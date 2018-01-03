from google.cloud import storage, pubsub_v1
from flask import render_template, url_for, flash, request, redirect, jsonify, copy_current_request_context
import logging, sys, re, json, threading, yaml, time, os, tempfile
from io import BytesIO
import tensorflow as tf
from time import gmtime, strftime
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery, errors

from methods import routes
from methods.utils import dataset_util
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_version, get_current_project, get_ml_settings
from helpers import sessionMaker
from database_setup import User, Project, Version, Image, Box
from methods.annotation.yamlNew import yamlNew
from methods.annotation.labels import labelMapNew
from methods.machine_learning.tfrecordsNew import tfrecordsNew
from methods.machine_learning.configNew import fasterRcnnResnetNew
from methods.machine_learning.runInference import runInferenceSingle
from methods.machine_learning import configNew, ml_settings
from settings import settings


gcs = storage.Client()
bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)

credentials = GoogleCredentials.get_application_default()
ml = discovery.build('ml', 'v1', credentials=credentials)
projectID = 'projects/{}'.format(settings.GOOGLE_PROJECT_NAME)

# TODO
# With new more robust session handling need to implement 
# new scopped session if hitting directly from HTTP request


def training_pre_conditions(session):
    
    project = get_current_project(session)
    version = get_current_version(session)
    
    params = {}
    have_error = False
    if project.train_credits <= 0:
        params['train_credits'] = "Out of train credits"
        have_error = True
        session.close()
    else:
        project.train_credits -= 1
        session.add(project)
        session.commit()
        
    return have_error, params


@routes.route('/machine_learning/training/run', methods=['GET'])
def runTraining(session):
    if LoggedIn() != True:
        return defaultRedirect()

    have_error, params = training_pre_conditions(session)
    if have_error:
        print("have error", params, file=sys.stderr)
        return json.dumps(params), 200, {'ContentType':'application/json'}

    # TODO Thinking on reasonable way to "copy" a version and track changes

    project = get_current_project(session)
    version = get_current_version(session)
    machine_learning_settings = get_ml_settings(session=session, version=version)

    JOB_NAME = "train_" + machine_learning_settings.JOB_NAME
    print(JOB_NAME, file=sys.stderr)

    REGION="us-central1"
    RUNTIME_VERSION="1.2"

    root_dir = "gs://" + settings.CLOUD_STORAGE_BUCKET + "/" + str(project.id) + "/" + str(version.id) + "/ml/" + str(machine_learning_settings.ml_compute_engine_id) + "/"
    JOB_DIR = root_dir + "train"
    pipeline_config_path = root_dir + "faster_rcnn_resnet.config"

    MAIN_TRAINER_MODULE='object_detection.train'

    training_inputs = {'scaleTier': 'CUSTOM',
	    'masterType': 'standard_gpu',
	    'workerType': 'standard_gpu',
	    'parameterServerType': 'standard_gpu',
	    'workerCount': 2,
	    'parameterServerCount': 1,
	    'packageUris': ['gs://' + settings.CLOUD_STORAGE_BUCKET + '/' + settings.LIB_OBJECT_DETECTION_PYTHON,
					    'gs://' + settings.CLOUD_STORAGE_BUCKET + '/' + settings.LIB_SLIM_PYTHON ],
	    'pythonModule': MAIN_TRAINER_MODULE,
	    'args': ['--train_dir', JOB_DIR, 
				    '--pipeline_config_path', pipeline_config_path],
	    'region': REGION,
	    'jobDir': JOB_DIR,
	    'runtimeVersion': RUNTIME_VERSION }

    job_spec = {'jobId': JOB_NAME, 'trainingInput': training_inputs}

    request = ml.projects().jobs().create(body=job_spec, parent=projectID)

    try:
        response = request.execute()
        print(response, file=sys.stderr)
        out = 'success'
        return out, 200, {'ContentType':'application/json'}

    except errors.HttpError as EOFError:
        print('There was an error. Check the details:', file=sys.stderr)
        print(EOFError._get_reason(), file=sys.stderr)
        out = 'failed'
        return out, 500, {'ContentType':'application/json'}

    return "success", 200


@routes.route('/machine_learning/training/frozen/run', methods=['GET'])
def trainingFrozenRun(session):

    if LoggedIn() != True:
        return defaultRedirect()

    project = get_current_project(session)
    version = get_current_version(session)
    machine_learning_settings = get_ml_settings(session=session, version=version)

    #now=strftime("%Y_%m_%d_%H_%M_%S", gmtime())
    JOB_NAME = "frozen_user_" + machine_learning_settings.JOB_NAME
    print(JOB_NAME, file=sys.stderr)

    root_dir = "gs://" + settings.CLOUD_STORAGE_BUCKET + "/" + str(project.id) + "/" + str(version.id) + "/ml/" + str(machine_learning_settings.ml_compute_engine_id) + "/"
    JOB_DIR = root_dir + str(machine_learning_settings.re_train_id) + "/frozen"
    REGION ="us-central1"
    RUNTIME_VERSION ="1.2"
 
    # Should be updated during training and store in db?
    trained_checkpoint_prefix = configNew.check_actual_model_path_name(session=session)

    pipeline_config_path = root_dir + "faster_rcnn_resnet.config"
    MAIN_TRAINER_MODULE ="object_detection.export_inference_graph"

    training_inputs = {'scaleTier': 'CUSTOM',
	    'masterType': 'large_model',
	    'workerCount': 0,
	    'packageUris': ['gs://' + settings.CLOUD_STORAGE_BUCKET + '/' + settings.LIB_OBJECT_DETECTION_PYTHON,
					    'gs://' + settings.CLOUD_STORAGE_BUCKET + '/' + settings.LIB_SLIM_PYTHON ],
	    'pythonModule': MAIN_TRAINER_MODULE,
	    'args': ['--trained_checkpoint_prefix', trained_checkpoint_prefix, 
				    '--pipeline_config_path', pipeline_config_path,
				    '--input_type', 'encoded_image_string_tensor',
				    '--output_directory', JOB_DIR],
	    'region': REGION,
	    'jobDir': JOB_DIR,
	    'runtimeVersion': RUNTIME_VERSION }

    job_spec = {'jobId': JOB_NAME, 'trainingInput': training_inputs}

    request = ml.projects().jobs().create(body=job_spec, parent=projectID)

    try:
        response = request.execute()
        print(response, file=sys.stderr)
        out = 'success'
        return out, 200, {'ContentType':'application/json'}
    except errors.HttpError as EOFError:
        print('There was an error. Check the details:', file=sys.stderr)
        print(EOFError._get_reason(), file=sys.stderr)
        out = 'failed'
        return out, 200, {'ContentType':'application/json'}

    return "Success", 200


@routes.route('/machine_learning/training/new_model', methods=['GET'])
def runNewModel(session):

    if LoggedIn() != True:
        return defaultRedirect()

    project = get_current_project(session)
    JOB_NAME = "a_" + str(project.id)

    # Creating model
    requestDict = {'name': JOB_NAME,
				    'description': 'Built by runNewModel()'}
    request = ml.projects().models().create(parent=projectID, body=requestDict)

    try:
        response = request.execute()
        print(response, file=sys.stderr)
        operationID = response['name']
        out = 'success'
        return out, 200, {'ContentType':'application/json'}
    except errors.HttpError as EOFError:
        print('There was an error. Check the details:', file=sys.stderr)
        print(EOFError._get_reason(), file=sys.stderr)
        out = 'failed'
        return out, 200, {'ContentType':'application/json'}

    return "Success", 200


@routes.route('/machine_learning/training/new_version', methods=['GET'])
def runNewVersion(session):

    if LoggedIn() != True:
        return defaultRedirect()

    project = get_current_project(session)
    version = get_current_version(session)
    machine_learning_settings = get_ml_settings(session=session, version=version)
    project_root = "a_" + str(project.id)

    # Creating version
    modelID= '{}/models/{}'.format(projectID, project_root)
    versionName = "a_" + str(version.id) + "_" + str(machine_learning_settings.ml_compute_engine_id)
    versionName += "_" + str(machine_learning_settings.re_train_id)

    # Maybe could include more info like date time?
    versionDescription = 'created by runNewVersion()'
    root_dir = "gs://" + settings.CLOUD_STORAGE_BUCKET + "/" + str(project.id) + "/" + str(version.id)
    root_dir += "/ml/" + str(machine_learning_settings.ml_compute_engine_id) + "/" + str(machine_learning_settings.re_train_id) + "/"
    JOB_DIR = root_dir + "frozen/saved_model"

    requestDict = {'name': versionName,
                    'description': versionDescription,
                    'deploymentUri': JOB_DIR,
                    'runtimeVersion': '1.2'}

    request = ml.projects().models().versions().create(
        parent=modelID, body=requestDict)

    try:
        response = request.execute()
        print(response, file=sys.stderr)

        operationID = response['name']

        out = 'success'
        return out, 200, {'ContentType':'application/json'}
    except errors.HttpError as EOFError:
        # Something went wrong, print out some information.
        print('There was an error. Check the details:', file=sys.stderr)
        print(EOFError._get_reason(), file=sys.stderr)
        out = 'failed'
        return out, 200, {'ContentType':'application/json'}
    
    return out, 200, {'ContentType':'application/json'}



@routes.route('/machine_learning/training/run/all/<int:re_train>', methods=['GET'])
def runTrainingPipeline(re_train=0):

    """

    """

    # 1 == retrain
    # Can you pass a bool here? prefer that but just doing this for now

    if LoggedIn() != True:
        return defaultRedirect()
        
    @copy_current_request_context
    def task_manager():
        def task_manager_scope(session):
            print("[Training task manager] Started. Retrain_flag:", re_train,  file=sys.stderr)
            session = sessionMaker.scoppedSession() # Threadsafe

            # Maybe better to have this somewhere else
            version = get_current_version(session=session)
            if version.machine_learning_settings_id is None:
                ml_settings.machine_learning_settings_new(session=session)

            # Advance one for training if not retraining
            if re_train == 0:
                ml_settings.machine_learning_settings_edit(session=session, next_id=True)

            project = get_current_project(session=session)

            machine_learning_settings = get_ml_settings(session=session, version=version)

            JOB_NAME = "__projectID_" + str(project.id) + "__versionID_" + str(version.id) + "__ml_compute_id_" + str(machine_learning_settings.ml_compute_engine_id)

            if re_train == 1:
                machine_learning_settings.re_train_id += 1
                JOB_NAME += "__retrainID_" + str(machine_learning_settings.re_train_id)
        
            machine_learning_settings.JOB_NAME = JOB_NAME
            session.add(machine_learning_settings)
            session.commit()

            # Do YAML for retraining
            # TODO way to detect if this is needed or not...
            yamlNew(hold_thread=True)

            labelMapNew()
            fasterRcnnResnetNew(re_train=re_train)  # Config file

            tfrecordsNew(hold_thread=True)

            ### TRAINING
            runTraining(session)
            
            config = {}
            config['PUBSSUB_TOPIC'] = settings.PUB_SUB_TOPIC
            config['PROJECT'] = settings.GOOGLE_PROJECT_NAME
            publisher = pubsub_v1.PublisherClient()
            topic_path = publisher.topic_path(config['PROJECT'], config['PUBSSUB_TOPIC'])
            JOB_NAME = "train_" + machine_learning_settings.JOB_NAME
            JOB_NAME_FORMATTED = projectID + "/jobs/" + JOB_NAME

            training_flag = True
            while training_flag is True:
                
                request = ml.projects().jobs().get(name=JOB_NAME_FORMATTED)
                # TODO error handling
                response = request.execute()
                
                data = json.dumps(response)
                print(data, file=sys.stderr)
                data = data.encode()
                publisher.publish(topic_path, data=data)

                a = response['state']
                if a == "SUCCEEDED" or a == "FAILED" or a =="CANCELLED":
                    training_flag = False
                else:
                    time.sleep(30)
            
            #### END TRAINING

            # Now need to run new model on re training
            if re_train == 0:
                runNewModel(session)

            ##### FROZEN
            trainingFrozenRun(session)

            JOB_NAME = "frozen_user_" + machine_learning_settings.JOB_NAME
            JOB_NAME_FORMATTED = projectID + "/jobs/" + JOB_NAME

            frozen_flag = True
            while frozen_flag is True:
                
                request = ml.projects().jobs().get(name=JOB_NAME_FORMATTED)

                # TODO error handling
                response = request.execute()

                data = json.dumps(response)
                print(data, file=sys.stderr)
                data = data.encode()

                publisher.publish(topic_path, data=data)

                a = response['state']
                if a == "SUCCEEDED" or a == "FAILED" or a =="CANCELLED":
                    frozen_flag = False
                else:
                    time.sleep(30)

            
            #####
            runNewVersion(session)
            time.sleep(60*8)  # Sleep while long running operation
            runInferenceSingle()

            print("[Training task manager] SUCCESS", file=sys.stderr)
            t.cancel()

        with sessionMaker.session_scope() as session:
            task_manager_scope(session)


    t = threading.Timer(0, task_manager)
    t.daemon = True
    t.start()

    out = 'success'
    return out, 200, {'ContentType':'application/json'}
         