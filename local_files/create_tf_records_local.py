import tensorflow as tf
import yaml
import os
from object_detection.utils import dataset_util
import sys


# Settings

UNIT_NUMBER = 0
#  db_id : sequential_id
LABEL_DICT =  {     109 : 1 , 110 : 2, 111 : 3,  }

def create_tf_example(example):
    
    height = 660 # Image height
    width = 512 # Image width

    filename = example[0]['image']['original_filename'] # Filename of the image. Empty if image is not from file
    filename = filename.encode()

    with tf.gfile.GFile(example[0]['image']['original_filename'], 'rb') as fid:
        encoded_image = fid.read()

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
        classes.append(int(LABEL_DICT[box['label_id']]))


    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
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


def main(_):
    

    output_path = "C:/Users/" + str(UNIT_NUMBER) + "/tfrecords_0.record"
    writer = tf.python_io.TFRecordWriter(output_path)
    
    INPUT_YAML = "C:/Users/" + str(UNIT_NUMBER) + "/annotations.yaml"
    examples = yaml.load(open(INPUT_YAML, 'rb').read())

    len_examples = len(examples)
    print("Loaded ", len(examples), "examples")

    IMAGES_DIR = "C:/Users/images/"

    for i in range(len(examples)):
        examples[i]['annotations'][0]['image']['original_filename'] = os.path.abspath(os.path.join(os.path.dirname(IMAGES_DIR), 
                                                                              examples[i]['annotations'][0]['image']['original_filename']))
    counter = 0
    for example in examples:
        tf_example = create_tf_example(example['annotations'])
        writer.write(tf_example.SerializeToString())

        if counter % 10 == 0:
            sys.stdout.write("\nCompleted\t")
            sys.stdout.write(str((counter/len_examples)*100))
            sys.stdout.flush()
        counter += 1

    writer.close()



if __name__ == '__main__':
    tf.app.run()