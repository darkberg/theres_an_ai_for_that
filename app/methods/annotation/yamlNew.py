from google.cloud import storage
from flask import render_template, url_for, flash, request, redirect, jsonify, copy_current_request_context
import logging, sys, re, json, time, threading, yaml

from helpers import sessionMaker
from methods import routes
from database_setup import User, Project, Version, Image, Box, Label
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_version, get_current_project, get_ml_settings, get_gcs_service_account
from methods.machine_learning import ml_settings
from settings import settings


def get_secure_link(blob):
    
    expiration_time = int(time.time() + 600) 
    return blob.generate_signed_url(expiration=expiration_time)


@routes.route('/yaml/new', methods=['GET'])
def yamlNew(hold_thread=False):

    if LoggedIn() != True:
        return defaultRedirect()

    @copy_current_request_context
    def task_manager():
        def task_manager_scope(session):
            project = get_current_project(session)
            version = get_current_version(session)
            machine_learning_settings = get_ml_settings(session=session, version=version)

            Images = session.query(Image).filter_by(version_id=version.id).order_by(Image.id.desc())
        
            annotations_list = []
            len_images = Images.count()
            counter = 0
            for image in Images:

                # TODO maybe better to do in database?
                if image.soft_delete != True and image.is_test_image != True and image.done_labeling == True:

                    boxes = session.query(Box).filter_by(image_id=image.id).order_by(Box.id.desc()).limit(100)

                    box_dict_list = []
                    for box in boxes:
                
                        label = session.query(Label).filter_by(id=box.label_id).one()
                        if label is None:
                            print("Label is none", file=sys.stderr)

                        box_dict_list.append({'label_id': label.id, 'label_name': label.name,
						                        'x_min': box.x_min, 'x_max': box.x_max,
						                        'y_min': box.y_min, 'y_max': box.y_max})

                    image_dict = {'image': {'image_id': image.id, 'image_width': image.width, 
				                    'image_height': image.height, 'original_filename': image.original_filename}}
                
                    boxes_dict = {'boxes': box_dict_list}
                    annotations_list.append({'annotations': [image_dict, boxes_dict]})

                if counter % 10 == 0:
                    print("Percent done", (counter/len_images)*100, file=sys.stderr)
                counter += 1

            print("annotations_list len", len(annotations_list), file=sys.stderr)
            yaml_data = yaml.dump(annotations_list, default_flow_style=False)

            gcs = storage.Client()
            gcs = get_gcs_service_account(gcs)
            bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)    
                
            project_str = str(project.id)+"/"+str(version.id)+"/ml/" + str(machine_learning_settings.ml_compute_engine_id) + "/annotations.yaml"

            blob = bucket.blob(project_str)
            blob.upload_from_string(yaml_data, content_type='text/yaml')

            print("Built YAML, link below", file=sys.stderr)

            link = get_secure_link(blob)
            print(link, file=sys.stderr)

            t.cancel()

        with sessionMaker.session_scope() as session:
            task_manager_scope(session)


    t = threading.Timer(0, task_manager)
    t.daemon = True
    t.start()

    print("[YAML processor] Started", file=sys.stderr)

    # Default to False for HTTP
    # Use 
    if hold_thread is True:
        t.join()
        
    out = "Started"
    return out, 200
    
