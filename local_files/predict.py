import numpy as np
import os, operator, time, sys, base64, pprint
import tensorflow as tf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
from collections import defaultdict
from io import StringIO
from utils import label_map_util
from utils import visualization_utils as vis_util
from glob import glob
from scipy.misc import imsave
import scipy.misc


class Image():
    def __init__(self):
        self.boxes = []
        self.classes = []
        self.scores = []          


class Network():
    def __init__(self):
        self.CKPT = None
        self.PATH_TO_LABELS = None
        self.angle_id = None
        self.boxes = None
        self.scores = None
        self.classes = None
        self.min_score_thresh = None
        self.num_classes = None
        self.name = None
        self.image_np = None
         
    def load_label_map(self):
        path = self.PATH_TO_LABELS
        label_map = label_map_util.load_labelmap(path)
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=self.num_classes, use_display_name=True)
        self.category_index = label_map_util.create_category_index(categories)
    
    def build(self):
        self.graph = tf.Graph()
        with self.graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(self.CKPT, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
            self.sess = tf.Session(graph=self.graph)
        self.image_tensor = self.graph.get_tensor_by_name('image_tensor:0')
        self.detection_boxes = self.graph.get_tensor_by_name('detection_boxes:0')
        self.detection_scores = self.graph.get_tensor_by_name('detection_scores:0')
        self.detection_classes = self.graph.get_tensor_by_name('detection_classes:0')
        self.num_detections = self.graph.get_tensor_by_name('num_detections:0')


    def run(self):
        with self.graph.as_default():
        
            self.image_np_expanded = np.expand_dims(self.image_np, axis=0)
            (boxes, scores, classes, num) = self.sess.run(
                            [self.detection_boxes, self.detection_scores, 
                            self.detection_classes, self.num_detections],
                            feed_dict={self.image_tensor: self.image_np_expanded})
            self.boxes = np.squeeze(boxes)
            self.scores = np.squeeze(scores)
            self.classes = np.squeeze(classes).astype(np.int32)

    def visual(self, image_path):
        for i in range(self.boxes.shape[0]):
            vis_util.visualize_boxes_and_labels_on_image_array(
                self.image_np, self.boxes, self.classes, self.scores,
                self.category_index,
                use_normalized_coordinates=True,
                line_thickness=3,
                min_score_thresh=self.min_score_thresh)
            file_name = os.path.split(image_path)[1]
            directory = OUTPUT_DIR
            if not os.path.exists(directory):
                os.makedirs(directory)
            imsave(directory + str(self.name) + "_" + str(file_name), self.image_np)

    def cache_results(self):      
        self.image = Image()
        for i in range(self.boxes.shape[0]):
            if self.scores[i] is None:
                pass            
            if self.scores[i] > self.min_score_thresh:
                self.image.boxes.append(self.boxes[i])
                self.image.classes.append(self.classes[i])
                self.image.scores.append(self.scores[i]) 

    def run_image(self):
        self.run()
        self.cache_results()


def load_test_images():
    
    TEST_IMAGE_PATHS = glob(os.path.join(PATH_TO_TEST_IMAGES_DIR, '*.jpg'))
    print("Length of test images:", len(TEST_IMAGE_PATHS))
    return TEST_IMAGE_PATHS



## Settings
UNIT_NUMBER = str(1)
BASE_PATH = 'C:/Users/'

PATH_TO_TEST_IMAGES_DIR = BASE_PATH + 'data/silly_walks/raw'
OUTPUT_DIR = BASE_PATH +  'data/silly_walks/out/' + UNIT_NUMBER + '/'

TEST_IMAGE_PATHS = load_test_images()

silly_walks = Network()
silly_walks.CKPT = BASE_PATH + 'silly_walks/model/out/frozen_inference_graph.pb'
silly_walks.PATH_TO_LABELS = BASE_PATH +  'data/silly_walks/model/label_map.pbtext'
silly_walks.num_classes = 1
silly_walks.load_label_map()
silly_walks.min_score_thresh = .50
silly_walks.name = "silly_walks"
silly_walks.build()

start_time = 0
units_done_counter = 0
def update_counter():
    global units_done_counter
    units_done_counter += 1
start_time = time.time()


for i, image_path in enumerate(TEST_IMAGE_PATHS):

    image = scipy.misc.imread(image_path)
        
    silly_walks.image_np = np.copy(image)  # Useful if using multiple networks here
    silly_walks.run_image()
    silly_walks.visual(image_path)

    update_counter()
    
end_time = time.time()

print("\n\nTime (minutes)", (end_time - start_time) / 60)
