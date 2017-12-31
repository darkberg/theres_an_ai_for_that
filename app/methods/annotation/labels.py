from google.cloud import storage
from flask import render_template, url_for, flash, request, redirect, jsonify
import logging, sys, re, json, time, yaml

from helpers import sessionMaker
from database_setup import User, Project, Version, Image, Box, Label
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_version, get_current_project, get_ml_settings, get_gcs_service_account
from methods import routes
from methods.machine_learning import ml_settings
from settings import settings

session = sessionMaker.newSession()


def get_secure_link(blob):
    
    expiration_time = int(time.time() + 60) 
    return blob.generate_signed_url(expiration=expiration_time)


@routes.route('/labels/machine_learning/label_map/new', methods=['GET'])
def labelMapNew():

    if LoggedIn() == True:

        project = get_current_project(session)
        version = get_current_version(session)
        ml_settings = get_ml_settings(session=session, version=version)
        Images = session.query(Image).filter_by(version_id=version.id)
        
        Labels = []

        # TO DO Refactor ie maintain a cache all label ids used in a version
        # Would need to store that cache per version
        # And update / delete it as labels are changed  OR Collect at YAML stage

        labels = session.query(Label).filter_by(project_id=project.id)            
        for i in labels:
            if i.soft_delete != True:
                Labels.append(i)

        # Map db ids to id s staring with 123    
        Labels.sort(key= lambda x: x.id) 
        label_dict = {}
        start_at_1_label = 1
        lowest_label = 0
        for label in Labels:
            if label.id > lowest_label:
                label_dict[label.id] = start_at_1_label
                start_at_1_label += 1
                lowest_label = label.id

        print("label_dict length", len(label_dict), file=sys.stderr)

        project_str = str(project.id)+"/"+str(version.id)+"/ml/" + str(ml_settings.ml_compute_engine_id)
        project_str += "/label_map.pbtext"

        file = ""
        
        Labels_unique = set(Labels)

        len_labels = len(Labels_unique)

        version.labels_number = len_labels
        session.add(version)
        session.commit()

        for i, c in enumerate(Labels_unique):
            new = "\nitem {"
            id = "\nid: " + str(label_dict[c.id])
            name = "\nname: " + str(c.name) + "\n }\n"

            file += new + id + name

        gcs = storage.Client()
        gcs = get_gcs_service_account(gcs)
        bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)
        blob = bucket.blob(project_str)
        blob.upload_from_string(file, content_type='text/pbtext')

        print("Built label_map", file=sys.stderr)
        out = get_secure_link(blob)

        return out, 200, {'ContentType':'application/json'}

    else:
        flash("Please login")



@routes.route('/labels/new', methods=['POST'])
def labelNew():

	if LoggedIn() == True:

		data = request.get_json(force=True)   # Force = true if not set as application/json' 
		label = data['label']
		print(label, data.keys(), file=sys.stderr)

		have_error = False
		params = {}
		#existing_label = session.query(Label).filter_by(id=label['id']).first()
		existing_label = None  # Maybe do more with this later

		project = get_current_project(session)

		if label is None:
			params['error'] = "No Label"
			have_error = True

		if existing_label is not None:
			params['error'] = "Existing label"
			have_error = True
		
		if have_error:
			return json.dumps(params), 200, {'ContentType':'application/json'}
		else:
			label['colour'] = "blue" # since JS is being strange
			new_label = Label(
				name = label['name'],
				colour = label['colour'],
				project_id = project.id)
			session.add(new_label)
			session.commit()

			return json.dumps({'success':True}), 200, {'ContentType':'application/json'}
	
		# need an else statement here


@routes.route('/labels/json', methods=['GET'])
def labelRefresh():

	if LoggedIn() == True:

		project = get_current_project(session)
		Labels_db = session.query(Label).filter_by(project_id=project.id).order_by(Label.id.desc())
		# TODO can do soft_delete != "True" check in here???

		Labels = []
		for i in Labels_db:
			if i.soft_delete != True:
				Labels.append(i)

		out = {}
		out['ids'] = [i.id for i in Labels]
		out['names'] = [i.name for i in Labels]
		#Colour?

		return json.dumps(out), 200, {'ContentType':'application/json'}

	else:
		flash("Please login")



@routes.route('/labels/delete', methods=['POST'])
def labelDelete():

    if LoggedIn() == True:

        data = request.get_json(force=True)   # Force = true if not set as application/json' 
        label = data['label']

        project = get_current_project(session)
        existing_Labels = session.query(Label).filter_by(project_id=project.id).order_by(Label.id.desc())

        for i in existing_Labels:
            if i.id == label['id']:
                i.soft_delete = True
                session.add(i)

        out = 'success'
        session.commit()

        return json.dumps(out), 200, {'ContentType':'application/json'}

    else:
        flash("Please login")



def categoryMap():

    project = get_current_project(session=session)
    version = get_current_version(session=session)
    ml_settings = get_ml_settings(session=session, version=version)
    Labels_db = session.query(Label).filter_by(project_id=project.id).order_by(Label.id.desc())

    Images = session.query(Image).filter_by(version_id=version.id)
        
    Labels = []

    for i in Labels_db:
        if i.soft_delete != True:
            Labels.append(i)

    Labels_unique = set(Labels)

    Labels.sort(key= lambda x: x.id) 
    label_dict = {}
    start_at_1_label = 1
    lowest_label = 0
    for label in Labels:
        if label.id > lowest_label:
            label_dict[label.id] = start_at_1_label
            start_at_1_label += 1
            lowest_label = label.id

    project_str = str(project.id)+"/"+str(version.id) + "/ml/" + str(ml_settings.ml_compute_engine_id)
    project_str += "/label_map.pbtext"

    categoryMap = {}
    for i, c in enumerate(Labels_unique):
        name = str(c.name)
        id = int(label_dict[int(c.id)])
           
        dict = {'id': int(i + 1), 'name': name}
        categoryMap[id] = dict

    return categoryMap

