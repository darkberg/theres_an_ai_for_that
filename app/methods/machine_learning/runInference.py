from google.cloud import storage
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery, errors
import numpy as np
from flask import render_template, url_for, flash, request, redirect, jsonify, copy_current_request_context
import logging, sys, re, json, time, os, yaml, requests, base64, tempfile, threading
from io import BytesIO
import tensorflow as tf
from time import gmtime, strftime
import scipy

from helpers import sessionMaker
from database_setup import User, Project, Version, Image, Box
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_version, get_current_project, get_ml_settings
from methods.utils import dataset_util, visualization_utils, label_map_util
from methods import routes
from settings import settings
from methods.annotation.labels import categoryMap
from methods.machine_learning import ml_settings


@routes.route('/machine_learning/inference/run', methods=['GET'])
def runInferenceSingle():

    if LoggedIn() != True:
        return defaultRedirect()

    @copy_current_request_context
    def task_manager():
        credentials = GoogleCredentials.get_application_default()
        ml = discovery.build('ml', 'v1', credentials=credentials)
        projectID = 'projects/{}'.format(settings.GOOGLE_PROJECT_NAME)
        
        project = get_current_project(session=session)
        version = get_current_version(session=session)
        machine_learning_settings = get_ml_settings(session=session, version=version)

        Images_db = session.query(Image).filter_by(version_id=version.id, is_test_image=True)

        REGION ="us-central1"
        RUNTIME_VERSION ="1.2"

        modelName = "a_" + str(project.id)
        versionName = "a_" + str(version.id) + "_" + str(machine_learning_settings.ml_compute_engine_id)
        versionName += "_" + str(machine_learning_settings.re_train_id)
        modelVersionName = '{}/models/{}/versions/{}'.format(
            projectID, modelName, versionName)

        gcs = storage.Client()
        bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)
        filenames = []

        root_dir = str(project.id)+"/"+str(version.id)+"/"
        for image in Images_db:
            #print(image.is_test_image, file=sys.stderr)
            if image.soft_delete != True:
                filenames.append(root_dir + "images/"+  str(image.id))
                break

        Rows = []
        Images = []
        print("len(filenames):",len(filenames), file=sys.stderr)

        for file in filenames:
            blob = bucket.blob(file)
            image = blob.download_as_string()

            # Resize
            image = scipy.misc.imread(BytesIO(image))
            if image is None:
                raise IOError("Could not open")

            # TODO BETTER WAY
            #image = scipy.misc.imresize(image, (640, 960))
            temp = tempfile.mkdtemp()
            new_temp_filename = temp+"/resized.jpg"
            scipy.misc.imsave(new_temp_filename, image)
            
            # Otherwise have strange byte issues
            blob = bucket.blob(file + "_test_resized")
            blob.upload_from_filename(new_temp_filename, content_type="image/jpg")
            image = blob.download_as_string()

            encoded_contents = base64.b64encode(image).decode('UTF-8')
            row = {'b64': encoded_contents}
            Rows.append(row)
            Images.append(image)
        
        output = {'instances': Rows}
       
        ml_request = ml.projects().predict(
            name = modelVersionName,
            body = output)

        PATH_TO_LABELS = root_dir + "ml/" + str(machine_learning_settings.ml_compute_engine_id) + "/label_map.pbtext"

        label_map_blob = bucket.blob(PATH_TO_LABELS)
        label_map_data = label_map_blob.download_as_string()
        
        category_index = categoryMap()
            


        try:
            time0 = time.time()
            response = ml_request.execute()
            time1 = time.time()
            print("Time in seconds", (time1 - time0), file=sys.stderr)
           
            print(response, file=sys.stderr)


            for i in range(len(Images)):
                response = response['predictions'][i]  # First one

                boxes = response['detection_boxes']
                scores = response['detection_scores']
                classes = response['detection_classes']

                boxes = np.array(boxes)
                scores = np.array(scores)
                classes = np.array(classes, dtype=int)
                print(classes, file=sys.stderr)

                image_np = scipy.misc.imread(BytesIO(Images[i]))

                # Handle gray scale
                if len(image_np.shape) == 2:
                    image_np = np.stack((image_np,) * 3, axis=2)

                print(image_np.shape)

                visualization_utils.visualize_boxes_and_labels_on_image_array(
                    image_np, boxes, classes, scores,
                    category_index,
                    use_normalized_coordinates=True,
                    min_score_thresh = .3,
                    line_thickness=2)
            
                
                blob = bucket.blob(root_dir + "test_inference_out/" + str(i) + "_.jpg")

                temp = tempfile.mkdtemp()
                new_temp_filename = temp+"/inference_" + str(i) + "_.jpg"
                scipy.misc.imsave(new_temp_filename, image_np)
                blob.upload_from_filename(new_temp_filename, content_type="image/jpg")
            
            min_score_thresh = .05
            for i in range(len(boxes)):
                if scores[i] > min_score_thresh:

                    class_name = category_index[classes[i]]['name']
                    print(class_name, scores[i],  file=sys.stderr)
            
            # TODO add pub sub messaging
            out = 'success'

        except errors.HttpError as EOFError:
            print('There was an error. Check the details:', file=sys.stderr)
            print(EOFError._get_reason(), file=sys.stderr)
            out = 'failed'
            
            
        session.close()
        t.cancel()

    session = sessionMaker.newSession()
    t = threading.Timer(0, task_manager)
    t.daemon = True
    t.start()

    out = 'success'
    return out, 200, 





