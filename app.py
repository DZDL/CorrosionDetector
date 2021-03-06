"""
Original code taken from https://github.com/anirbankonar123/CorrosionDetector
Adapted code in https://github.com/DZDL/CorrosionDetector
"""
from object_detection.utils import visualization_utils as vis_util
from object_detection.utils import label_map_util
import warnings
from object_detection.utils import ops as utils_ops
import streamlit as st
import numpy as np
import os
from os import listdir
from os.path import isfile, join
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile
import cv2 as cv

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image

sys.path.append("..")

warnings.filterwarnings('ignore')


# Weights path
# change this path as in your system
PATH_TO_CKPT = './checkpoints/weights/frozen_inference_graph.pb'
# check this path, and provide the image file names properly
PATH_TO_TEST_IMAGES_DIR = './datasetsplitted/test/'
# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = './checkpoints/weights/rust_label_map.pbtxt'


NUM_CLASSES = 1
# Size, in inches, of the output images.
IMAGE_SIZE = (12, 8)


def clean_temporal_files():
    """
    Remove all temporal files
    """
    paths_to_remove = ['datasetsplitted/test/',
                       'datasetsplitted/train']

    try:
        for path in paths_to_remove:
            for f in os.listdir(path):
                os.remove(os.path.join(path, f))
    except Exception as e:
        print(e)


def load_image_into_numpy_array(image):
    """
    Convert image to numpy array
    """
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
        (im_height, im_width, 3)).astype(np.uint8)


def run_inference_for_single_image(image, graph):
    """
    Inference one single image
    """
    with graph.as_default():
        with tf.Session() as sess:
            # Get handles to input and output tensors
            ops = tf.get_default_graph().get_operations()
            all_tensor_names = {
                output.name for op in ops for output in op.outputs}
            tensor_dict = {}
            for key in ['num_detections', 'detection_boxes', 'detection_scores',
                        'detection_classes', 'detection_masks']:
                tensor_name = key + ':0'
                if tensor_name in all_tensor_names:
                    tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                        tensor_name)
            if 'detection_masks' in tensor_dict:
                # The following processing is only for single image
                detection_boxes = tf.squeeze(
                    tensor_dict['detection_boxes'], [0])
                detection_masks = tf.squeeze(
                    tensor_dict['detection_masks'], [0])
                # Reframe is required to translate mask from box coordinates to image coordinates and fit the image size.
                real_num_detection = tf.cast(
                    tensor_dict['num_detections'][0], tf.int32)
                detection_boxes = tf.slice(detection_boxes, [0, 0], [
                                           real_num_detection, -1])
                detection_masks = tf.slice(detection_masks, [0, 0, 0], [
                                           real_num_detection, -1, -1])
                detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
                    detection_masks, detection_boxes, image.shape[0], image.shape[1])
                detection_masks_reframed = tf.cast(
                    tf.greater(detection_masks_reframed, 0.5), tf.uint8)
                # Follow the convention by adding back the batch dimension
                tensor_dict['detection_masks'] = tf.expand_dims(
                    detection_masks_reframed, 0)
            image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')

            # Run inference
            output_dict = sess.run(tensor_dict, feed_dict={
                                   image_tensor: np.expand_dims(image, 0)})

            # all outputs are float32 numpy arrays, so convert types as appropriate
            output_dict['num_detections'] = int(
                output_dict['num_detections'][0])
            output_dict['detection_classes'] = output_dict[
                'detection_classes'][0].astype(np.uint8)
            output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
            output_dict['detection_scores'] = output_dict['detection_scores'][0]
            if 'detection_masks' in output_dict:
                output_dict['detection_masks'] = output_dict['detection_masks'][0]
    return output_dict


def get_list_files_from_path(path):
    onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
    return onlyfiles


if __name__ == '__main__':

    clean_temporal_files()  # delete temporal files

    st.title("Corrosion detector")

    # Upload file
    st.subheader("- Choose a file (video or image)")
    uploaded_file = st.file_uploader("Elige una imagen compatible", type=[
        'png', 'jpg', 'bmp', 'jpeg', 'mp4'])

    if uploaded_file is not None:  # File > 0 bytes

        file_details = {"FileName": uploaded_file.name,
                        "FileType": uploaded_file.type,
                        "FileSize": uploaded_file.size}
        st.write(file_details)

        #######################
        # VIDEO UPLOADED FILE
        #######################
        if file_details['FileType'] == 'video/mp4':

            st.write("MP4 is not supported yet.")

        #######################
        # IMAGE UPLOADED FILE
        #######################
        elif (file_details['FileType'] == 'image/png' or
              file_details['FileType'] == 'image/jpg' or
              file_details['FileType'] == 'image/jpeg' or
              file_details['FileType'] == 'image/bmp'):

            file_bytes = np.asarray(
                bytearray(uploaded_file.read()), dtype=np.uint8)
            image = cv.imdecode(file_bytes, 1)
            cv.imwrite(PATH_TO_TEST_IMAGES_DIR+uploaded_file.name, image)

            st.write("This is your uploaded image:")
            st.image(image, caption='This is the uploaded image',
                     channels="BGR", use_column_width=True)

            detection_graph = tf.Graph()
            with detection_graph.as_default():
                od_graph_def = tf.GraphDef()
                with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
                    serialized_graph = fid.read()
                    od_graph_def.ParseFromString(serialized_graph)
                    tf.import_graph_def(od_graph_def, name='')

            label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
            categories = label_map_util.convert_label_map_to_categories(
                label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
            category_index = label_map_util.create_category_index(categories)

            #############
            # INFERENCE #
            #############

            TEST_IMAGE_PATHS = get_list_files_from_path(
                PATH_TO_TEST_IMAGES_DIR)

            for image_path in TEST_IMAGE_PATHS:

                # st.write(PATH_TO_TEST_IMAGES_DIR+image_path)

                image = Image.open(PATH_TO_TEST_IMAGES_DIR+image_path)
                # the array based representation of the image will be used later in order to prepare the
                # result image with boxes and labels on it.
                image_np = load_image_into_numpy_array(image)
                # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                image_np_expanded = np.expand_dims(image_np, axis=0)
                # Actual detection.
                output_dict = run_inference_for_single_image(
                    image_np, detection_graph)
                # Visualization of the results of a detection.
                vis_util.visualize_boxes_and_labels_on_image_array(
                    image_np,
                    output_dict['detection_boxes'],
                    output_dict['detection_classes'],
                    output_dict['detection_scores'],
                    category_index,
                    instance_masks=output_dict.get('detection_masks'),
                    use_normalized_coordinates=True,
                    line_thickness=2)
                
                
                st.image(image_np, caption='Output image',
                         channels="RGB", use_column_width=True)
