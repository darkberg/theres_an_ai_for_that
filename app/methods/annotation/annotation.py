from google.cloud import storage
from flask import render_template, url_for, flash, request, redirect, jsonify
import logging, re, sys, time, json

from methods import routes
from helpers import sessionMaker
from database_setup import User, Project, Version, Image, Box, Label
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_version, get_current_project, get_gcs_service_account
from settings import settings


@routes.route('/a')
def annotate():
    if LoggedIn() != True:
        return defaultRedirect()    
    return render_template('/annotation/annotation.html')


@routes.route('/test')
def test(): 
    if LoggedIn() != True:
        return defaultRedirect()
    
    return render_template('/annotation/test.html')


@routes.route('/version/current/json', methods=['GET'])
def versionView():
    def version_view_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()

        version = get_current_version(session)
        out = jsonify(version=version.serialize())

        return out, 200, {'ContentType':'application/json'}

    with sessionMaker.session_scope() as session:
        return version_view_scope(session)


# TODO Rename various "test" elements to "inference" to clarify
@routes.route('/images/test/out', methods=['GET'])
def testOut():
    def test_out_scope(session):    
        if LoggedIn() != True:
            return defaultRedirect()

        project = get_current_project(session)
        version = get_current_version(session)
        Images = session.query(Image).filter_by(version_id=version.id, is_test_image=True).order_by(Image.id.desc())

        gcs = storage.Client()
        gcs = get_gcs_service_account(gcs)
        bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)

        Public_urls = []
        expiration_time = int(time.time() + 300)

        file = str(project.id)+"/"+str(version.id)+"/"+ "test_inference_out/"+ "0_.jpg"
        blob = bucket.blob(file)
        public_url = blob.generate_signed_url(expiration=expiration_time)
        Public_urls.append(public_url)

        out = {}
        out['image_ids'] = [i.id for i in Images]
        out['width'] = [i.width for i in Images]
        out['height'] = [i.height for i in Images]
        out['public_url'] = [i for i in Public_urls]

        return json.dumps(out), 200, {'ContentType':'application/json'}

    with sessionMaker.session_scope() as session:
        return test_out_scope(session)


def rebuild_secure_urls(session, project, version, i):
    
    expiration_time = int(time.time() + 2592000)  # 1 month
    gcs = storage.Client()
    gcs = get_gcs_service_account(gcs)
    bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)

    file = str(project.id) + "/" + str(version.id) + "/" + "images/" + str(i.id)
    blob = bucket.blob(file)
    url_signed = blob.generate_signed_url(expiration=expiration_time)

    blob = bucket.blob(file + "_thumb")
    url_signed_thumb = blob.generate_signed_url(expiration=expiration_time)

    i.url_signed = url_signed
    i.url_signed_thumb = url_signed_thumb
    i.url_signed_expiry = expiration_time

    session.add(i)


@routes.route('/images/get', methods=['POST'])
def get_image_ids():
    def get_image_ids_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()  

        project = get_current_project(session)
        version = get_current_version(session)

        data = request.get_json(force=True)
        search_term = data.get("search_term", None)
        print(search_term, file=sys.stderr)
        if search_term is None:
            Images = session.query(Image).filter_by(version_id=version.id).order_by(Image.original_filename.desc()).limit(128)
        else: 
            search_term = "%" + search_term + "%"
            Images = session.query(Image).filter_by(version_id=version.id).filter(Image.original_filename.like(search_term)).order_by(Image.original_filename.desc()).limit(128)

        gcs = storage.Client()
        gcs = get_gcs_service_account(gcs)
        bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)

        Pre_condition_checked_images = []
        for i in Images:
            if i.soft_delete != True:
                if i.url_signed_expiry is None or i.url_signed_expiry <= time.time():
                    rebuild_secure_urls(session, project, version, i)                    

                Pre_condition_checked_images.append(i)
        
        out = jsonify(images=[i.serialize() for i in Pre_condition_checked_images])

        return out, 200, {'ContentType':'application/json'}

    with sessionMaker.session_scope() as session:
        return get_image_ids_scope(session)



@routes.route('/boxes/get/json', methods=['POST'])
def get_boxes():
    def get_boxes_scope(session):

        if LoggedIn() != True:
            return defaultRedirect()

        data = request.get_json(force=True)

        if data['image_id'] is not None:
            print("current_image.id", data['image_id'], file=sys.stderr)
            image_id = data['image_id']
            boxes = session.query(Box).filter_by(image_id=image_id).order_by(Box.id.desc())
        else:
            # This could be more sophisticated ie store last image we were working with
            version = get_current_version(session)
            image = session.query(Image).filter_by(version_id=version.id).order_by(Image.id.desc()).first()
            boxes = session.query(Box).filter_by(image_id=image.id).order_by(Box.id.desc())

        labels = []
        for b in boxes:
            label = session.query(Label).filter_by(id=b.label_id)
            labels.append(label[0].serialize())

        out = jsonify(boxes=[i.serialize() for i in boxes], labels=labels)
        

        return out, 200, {'ContentType':'application/json'}


    with sessionMaker.session_scope() as session:
        return get_boxes_scope(session)


@routes.route('/annotation/boxes/update', methods=['POST'])
def newBox():
    def new_box_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()

        data = request.get_json(force=True)   # Force = true if not set as application/json' 
        boxes = data['boxes']

        existing_boxes = session.query(Box).filter_by(image_id=data['image_id']).all()

        # TODO better way to do this
        for box_old in existing_boxes:
            for box_new in boxes:
                if box_old.id != box_new['id']:
                    session.delete(box_old)
            if len(boxes) == 0:   # Handle case of all boxes being deleted
                session.delete(box_old)

        for box in boxes:
            if box['width'] > 5 and box['height'] > 5:
                new_box = Box(x_min=box['x_min'], y_min=box['y_min'], x_max=box['x_max'], y_max=box['y_max'],
                                width=box['width'], height=box['height'], 
                                image_id = box['image_id'], 
                                label_id = box['label']['id'])
    
                session.add(new_box)
                session.commit()
                print(box['id'], file=sys.stderr)

        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

    with sessionMaker.session_scope() as session:
        return new_box_scope(session)


@routes.route('/images/delete', methods=['POST'])
def imageDelete():
    def image_delete_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()


        data = request.get_json(force=True)   # Force = true if not set as application/json' 
        image = data['image']

        version = get_current_version(session)

        Existing_images = session.query(Image).filter_by(version_id=version.id)

	    # Could delete multiple if get list of images to delete....
	    # Same issue as above otherwise, could do in query by checking id ie
	    # session.query(Employer).filter_by(id=employer_id).one()

        for i in Existing_images:
            if i.id == image['id']:
                i.soft_delete = True

                if i.is_test_image is True:
                    version.test_length -= 1
                else:
                    version.train_length -= 1
                # TODO Handle updating test / train length cache without db hit
               
                session.add(i)

        out = 'success'
        return json.dumps(out), 200, {'ContentType':'application/json'}

    with sessionMaker.session_scope() as session:
        return image_delete_scope(session)



@routes.route('/images/edit/toggle_test_image', methods=['POST'])
def toggleTestImage():
    def toggle_test_image_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()

        data = request.get_json(force=True)   # Force = true if not set as application/json' 
        image = data['image']

        version = get_current_version(session)
        image_db = session.query(Image).filter_by(version_id=version.id, id=image['id']).first()

        if image_db.is_test_image == True:
            version.train_length += 1
            version.test_length -= 1
        else:
            version.train_length -= 1
            version.test_length += 1
              
        image_db.is_test_image = not image_db.is_test_image
        session.add(image_db)
        out = 'success'
        return json.dumps(out), 200, {'ContentType':'application/json'}

    with sessionMaker.session_scope() as session:
        return toggle_test_image_scope(session)


# TODO rename , it's "all selected" not all in db
@routes.route('/images/edit/toggle_test_image/all', methods=['POST'])
def toggleTestImageAll():
    def toggle_test_image_all_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()

        data = request.get_json(force=True)   # Force = true if not set as application/json' 
        images = data['images']
        print("len(images)", len(images), file=sys.stderr)

        version = get_current_version(session)

        for i in images:
            image_db = session.query(Image).filter_by(version_id=version.id, id=i['id']).first()

            if image_db.is_test_image == True:
                version.train_length += 1
                version.test_length -= 1
            else:
                version.train_length -= 1
                version.test_length += 1
              
            image_db.is_test_image = not image_db.is_test_image
            session.add(image_db)
        
        session.add(version)
        out = 'success'
        return json.dumps(out), 200, {'ContentType':'application/json'}

    with sessionMaker.session_scope() as session:
        return toggle_test_image_all_scope(session)



@routes.route('/images/edit/toggle_done_labeling', methods=['POST'])
def toggle_done_labeling():
    def toggle_done_labeling_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()

        data = request.get_json(force=True)   # Force = true if not set as application/json' 
        image = data['image']

        version = get_current_version(session)
        Existing_images = session.query(Image).filter_by(version_id=version.id)

        for i in Existing_images:
            if i.id == image['id']:
                i.done_labeling = not i.done_labeling
                session.add(i)

        out = 'success'
        return json.dumps(out), 200, {'ContentType':'application/json'}

    with sessionMaker.session_scope() as session:
        return toggle_done_labeling_scope(session)


@routes.route('/images/edit/toggle_done_labeling_all', methods=['POST'])
def toggle_done_labeling_all():
    def toggle_done_labeling_all_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()

        data = request.get_json(force=True)
        images = data['images']

        version = get_current_version(session)
        Existing_images = session.query(Image).filter_by(version_id=version.id)

        for i in Existing_images:
            for j in images:
                if i.id == j['id']:
                    i.done_labeling = not i.done_labeling
                    session.add(i)

        out = 'success'
        return json.dumps(out), 200, {'ContentType':'application/json'}
    
    with sessionMaker.session_scope() as session:
        return toggle_done_labeling_all_scope(session)


@routes.route('/images/edit/remove_duplicate_filenames', methods=['POST'])
def remove_duplicate_filenames():
    def remove_duplicate_filenames_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()

        # May want to remove specific duplicates only
        data = request.get_json(force=True)   
        images = data['images']

        version = get_current_version(session)
        Existing_images = session.query(Image).filter_by(version_id=version.id)
    
        seen_file_once = []
        looked_at = 0
        soft_delete_marked = 0
        for i in Existing_images:
            looked_at += 1
            for j in images:
                if i.id == j['id']:
                    if i.original_filename not in seen_file_once:
                        seen_file_once.append(i.original_filename)
                    else:
                        i.soft_delete = True
                        session.add(i)
                        soft_delete_marked +=1

            if looked_at % 100 == 0:
                print("Looked at", looked_at, "Removed", soft_delete_marked)
    
        print("Removed", soft_delete_marked, "duplicates")             
        out = 'success'

        return json.dumps(out), 200, {'ContentType':'application/json'}

    with sessionMaker.session_scope() as session:
        return remove_duplicate_filenames_scope(session)


@routes.route('/images/edit/remove_duplicate_filenames/all', methods=['GET'])
def remove_duplicate_filenames_all():
    def remove_duplicate_filenames_all_scope(session):
        if LoggedIn() != True:
            return defaultRedirect()

        version = get_current_version(session)
        Existing_images = session.query(Image).filter_by(version_id=version.id)

        seen_file_once = []
        looked_at = 0
        soft_delete_marked = 0
        # basic greedy approach
        # If we have seen the filename mark future objects with same file name as soft delete, else add to list
        for i in Existing_images:   
            if i.original_filename in seen_file_once:
                i.soft_delete = True
                session.add(i)
                soft_delete_marked +=1
            else:
                seen_file_once.append(i.original_filename)
                looked_at += 1

            if looked_at % 100 == 0:
                print("Looked at", looked_at, "Removed", soft_delete_marked)
    
        print("Removed", soft_delete_marked, "duplicates")
        out = 'success'
        return json.dumps(out), 200, {'ContentType':'application/json'}

    with sessionMaker.session_scope() as session:
        return remove_duplicate_filenames_all_scope(session)
