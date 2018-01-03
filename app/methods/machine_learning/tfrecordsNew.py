from google.cloud import storage
import tensorflow as tf
from flask import render_template, url_for, flash, request, redirect, jsonify, copy_current_request_context
import sys, re, json, os, requests, time, logging, tempfile, threading, yaml
from io import BytesIO

from helpers import sessionMaker
from database_setup import User, Project, Version, Image, Box, Label
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_version, get_current_project, get_ml_settings, get_gcs_service_account
from methods import routes
from methods.machine_learning import ml_settings
from methods.utils import dataset_util
from settings import settings


def get_secure_link(blob):
    
    expiration_time = int(time.time() + 60) 
    return blob.generate_signed_url(expiration=expiration_time)


def create_tf_example(example, Labels_dict):
    
    height =  example[0]['image']['image_height']
    width =  example[0]['image']['image_width']
    image_id = example[0]['image']['image_id']

    gcs = storage.Client()
    bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)    
    blob_image = bucket.blob(example[0]['image']['image_id'])
    encoded_image = blob_image.download_as_string()

    image_id = image_id.encode()
    image_format = 'jpg'.encode() 

    xmins = [] # List of normalized left x coordinates in bounding box (1 per box)
    xmaxs = [] # List of normalized right x coordinates in bounding box
    ymins = [] # List of normalized top y coordinates in bounding box (1 per box)
    ymaxs = [] # List of normalized bottom y coordinates in bounding box
    classes_text = [] # List of string class name of bounding box (1 per box)
    classes = [] # List of integer class id of bounding box (1 per box)

    for box in example[1]['boxes']:
  
        xmins.append(float(box['x_min'] / width))
        xmaxs.append(float(box['x_max'] / width))
        ymins.append(float(box['y_min'] / height))
        ymaxs.append(float(box['y_max'] / height))

        classes_text.append(box['label_name'].encode())
        classes.append(int(Labels_dict[box['label_id']]))

    #print(classes, file=sys.stderr)
    #print(classes_text, file=sys.stderr)

    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/image_id': dataset_util.bytes_feature(image_id),
        'image/source_id': dataset_util.bytes_feature(image_id),
        'image/encoded': dataset_util.bytes_feature(encoded_image),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
    }))

    return tf_example


@routes.route('/tfrecords/new', methods=['GET'])
def tfrecordsNew(hold_thread=False):

    if LoggedIn() != True:
        return defaultRedirect()


    @copy_current_request_context
    def task_manager():
        def task_manager_scope(session):
            project = get_current_project(session)
            version = get_current_version(session)
            ml_settings = get_ml_settings(session=session, version=version)

            project_str = str(project.id)+"/"+str(version.id)+"/"

            gcs = storage.Client()
            gcs = get_gcs_service_account(gcs)
            bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)
            blob = bucket.blob(project_str + "ml/" + str(ml_settings.ml_compute_engine_id) + "/tfrecords_0.record")
            INPUT_YAML = project_str + "ml/" + str(ml_settings.ml_compute_engine_id) + "/annotations.yaml"
            yaml_blob = bucket.blob(INPUT_YAML)

            yaml_bytes = yaml_blob.download_as_string()
            examples = yaml.load(yaml_bytes)

            len_examples = len(examples)
            print("Loaded ", len(examples), "examples", file=sys.stderr)

            images_dir = project_str + "images/"
            for i in range(len(examples)):
                examples[i]['annotations'][0]['image']['image_id'] = images_dir + str(examples[i]['annotations'][0]['image']['image_id'])

            counter = 0
            all_examples = []

            # Reassign db ids to be 1 2 3  etc for tensorflow
            # TODO this is terrible surely better way to do this
            Labels = []
            labels = session.query(Label).filter_by(project_id=project.id)            
            for i in labels:
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

            print("label_dict length", len(label_dict), file=sys.stderr)

            temp = tempfile.NamedTemporaryFile()
            writer = tf.python_io.TFRecordWriter(str(temp.name))

            for example in examples:
            
                tf_example = create_tf_example(example['annotations'], label_dict)
                writer.write(tf_example.SerializeToString())
            
                if counter % 2 == 0:
                    print("Percent done", (counter/len_examples)*100)
                counter += 1

            writer.close()

            blob.upload_from_file(temp, content_type='text/record')
            temp.close()

            link = get_secure_link(blob)
            print(blob.name, file=sys.stderr)    
            print("Built TF records", file=sys.stderr)
            t.cancel()


        with sessionMaker.session_scope() as session:
            task_manager_scope(session)


    t = threading.Timer(0, task_manager)
    t.daemon = True
    t.start()
    
    print("[TF records processor] Started", file=sys.stderr)

    if hold_thread is True:
        t.join()

    return "Started tf_records", 200
