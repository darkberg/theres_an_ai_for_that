from google.cloud import storage
from flask import render_template, url_for, flash, request, redirect, jsonify
import logging, sys, re, json, time
import yaml

from methods import routes
from methods.machine_learning import ml_settings
from helpers import sessionMaker
from database_setup import User, Project, Version, Image, Box
from helpers.permissions import LoggedIn, defaultRedirect, getUserID, get_current_version, get_current_project, get_ml_settings
from settings import settings

session = sessionMaker.newSession()
gcs = storage.Client()
bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)


def check_actual_model_path_name(session=session):
    project = get_current_project(session)
    version = get_current_version(session)
    machine_learning_settings = get_ml_settings(session=session, version=version)
    
    root_dir = "gs://" + settings.CLOUD_STORAGE_BUCKET + "/" + str(project.id) + "/" + str(version.id) + "/ml/" + str(machine_learning_settings.ml_compute_engine_id) + "/"
    previous_goal_iterations = machine_learning_settings.previous_goal_iterations
    model_name_ranges = [i for i in range(previous_goal_iterations-1,previous_goal_iterations+5)]
    for i in model_name_ranges:
        MODEL_NAME = 'model.ckpt-' + str(i) + '.index'
        trained_checkpoint_prefix = str(project.id) + "/" + str(version.id) + "/ml/" + str(machine_learning_settings.ml_compute_engine_id) + "/train/" + MODEL_NAME
        blob = bucket.blob(trained_checkpoint_prefix)
        if blob.exists() == True:
            MODEL_NAME = 'model.ckpt-' + str(i)
            trained_checkpoint_prefix = root_dir + "train/" + MODEL_NAME
            
            # Store in DB for other functions that need it
            machine_learning_settings.trained_checkpoint_prefix = trained_checkpoint_prefix     
            session.add(machine_learning_settings)
            session.commit()

            print(trained_checkpoint_prefix, file=sys.stderr)
            return trained_checkpoint_prefix


@routes.route('/machine_learning/config/a/new', methods=['GET'])
def fasterRcnnResnetNew(re_train=0):

    if LoggedIn() != True:
        return defaultRedirect()

    project = get_current_project(session)
    version = get_current_version(session)
    machine_learning_settings = get_ml_settings(session=session, version=version)

    project_str = str(project.id)+"/"+str(version.id)+"/ml/" + str(machine_learning_settings.ml_compute_engine_id)
    project_str += "/faster_rcnn_resnet.config"
    # Faster R-CNN with Resnet-101 (v1)

    root_dir = "gs://" + settings.CLOUD_STORAGE_BUCKET + "/" + str(project.id) + "/" + str(version.id) + "/ml/" + str(machine_learning_settings.ml_compute_engine_id) + "/"
    num_classes_var = version.labels_number   # TODO get this automatically
    print("version.labels_number", version.labels_number, file=sys.stderr)
    min_dimension_var = 720
    max_dimension_var = 1280  # TODO get this automaticaly within limit
    first_stage_max_proposals_var = 100

    label_map_path_var = root_dir + "label_map.pbtxt"

    # Testing for multiple records?
    input_path_var = root_dir + "tfrecords_*.record"
    num_steps_var = machine_learning_settings.iterations

    # This is the shared generic starting point
    fine_tune_checkpoint_var = "gs://" + settings.CLOUD_STORAGE_BUCKET + "/" + settings.RESNET_PRE_TRAINED_MODEL
    if re_train == 1:
            
        machine_learning_settings.previous_goal_iterations = machine_learning_settings.iterations
        num_steps_var = machine_learning_settings.iterations + 1500
        fine_tune_checkpoint_var = check_actual_model_path_name(session=session)

    model = "model {"
    faster_rcnn = "\nfaster_rcnn {"
    num_classes = "\nnum_classes: " + str(num_classes_var)
    image_resizer = "\nimage_resizer { \nkeep_aspect_ratio_resizer {"
    min_dimension = "\nmin_dimension: " + str(min_dimension_var)
    max_dimension = "\nmax_dimension: " + str(max_dimension_var) + "\n} \n}"

    feature_extractor = "\nfeature_extractor { \n type: 'faster_rcnn_resnet101' "
    first_stage_features_stride = "\nfirst_stage_features_stride: 16 \n } "
    first_stage_anchor_generator = """first_stage_anchor_generator \n{ \ngrid_anchor_generator 
    { \nscales: [0.25, 0.5, 1.0, 2.0] \naspect_ratios: [0.5, 1.0, 2.0] \nheight_stride: 16 \n
    width_stride: 16 \n } \n } \n"""

        
    first_stage_box_predictor_conv_hyperparams = """
    first_stage_box_predictor_conv_hyperparams {
    op: CONV
    regularizer {
    l2_regularizer {
    weight: 0.0
    }
    }
    initializer {
    truncated_normal_initializer {
    stddev: 0.01
    }
    }
    }
    first_stage_nms_score_threshold: 0.0
    first_stage_nms_iou_threshold: 0.7
    first_stage_localization_loss_weight: 2.0
    first_stage_objectness_loss_weight: 1.0
    initial_crop_size: 14
    maxpool_kernel_size: 2
    maxpool_stride: 2
    """

    first_stage_max_proposals = "\nfirst_stage_max_proposals:" + str(first_stage_max_proposals_var)
        
    second_stage_box_predictor = """
    second_stage_box_predictor {
    mask_rcnn_box_predictor {
    use_dropout: false
    dropout_keep_probability: 1.0
    fc_hyperparams {
    op: FC
    regularizer {
    l2_regularizer {
    weight: 0.0
    }
    }
    initializer {
    variance_scaling_initializer {
    factor: 1.0
    uniform: true
    mode: FAN_AVG
    }
    }
    }
    }
    }
    """
    second_stage_post_processing = """
    second_stage_post_processing {
    batch_non_max_suppression {
    score_threshold: 0.0
    iou_threshold: 0.6
    max_detections_per_class: 100
    """
    max_total_detections = "max_total_detections:" + str(first_stage_max_proposals_var) + "\n}"

    score_converter = """
    score_converter: SOFTMAX
    }
    second_stage_localization_loss_weight: 2.0
    second_stage_classification_loss_weight: 1.0
    """
    second_stage_batch_size = "\nsecond_stage_batch_size: " + str(first_stage_max_proposals_var) + "\n }\n }\n"

    train_config = """
    train_config: {
    batch_size: 1
    optimizer {
    momentum_optimizer: {
    learning_rate: {
    manual_step_learning_rate {
    initial_learning_rate: 0.0003
    schedule {
    step: 0
    learning_rate: .0003
    }
    schedule {
    step: 900000
    learning_rate: .00003
    }
    schedule {
    step: 1200000
    learning_rate: .000003
    }
    }
    }
    momentum_optimizer_value: 0.9
    }
    use_moving_average: false
    }
    gradient_clipping_by_norm: 10.0
    """
    fine_tune_checkpoint = "\nfine_tune_checkpoint: '" + str(fine_tune_checkpoint_var) + "'"
        
    from_detection_checkpoint = "\nfrom_detection_checkpoint: true"

    num_steps = "\nnum_steps: " + str(num_steps_var)

    data_augmentation_options = """
    data_augmentation_options {
    random_horizontal_flip {
    }
    }
    }
    """

    train_input_reader = """
    train_input_reader: {
    tf_record_input_reader {
    """

    input_path = "\ninput_path: '" + str(input_path_var) + "' \n}"
    label_map_path = "\nlabel_map_path: '" + str(label_map_path_var) + "'\n}"

    config_file_a = model + faster_rcnn + num_classes + image_resizer + min_dimension + max_dimension + feature_extractor + first_stage_features_stride + first_stage_anchor_generator
    config_file_b = first_stage_box_predictor_conv_hyperparams + first_stage_max_proposals + second_stage_box_predictor + second_stage_post_processing + max_total_detections
    config_file_c = score_converter + second_stage_batch_size + train_config + fine_tune_checkpoint + from_detection_checkpoint + num_steps + data_augmentation_options + train_input_reader + input_path + label_map_path

    config_file = config_file_a + config_file_b + config_file_c

    gcs = storage.Client()
    bucket = gcs.get_bucket(settings.CLOUD_STORAGE_BUCKET)
    blob = bucket.blob(project_str)
    blob.upload_from_string(config_file, content_type='text/config')

    print("Built Config", file=sys.stderr)
    out = 'success'
    
    return out, 200, {'ContentType':'application/json'}
