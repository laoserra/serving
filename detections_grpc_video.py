# base imports
from PIL import Image
import numpy as np
import pandas as pd
import sys
import os
import time
import grpc
import tensorflow as tf
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc

# import script to insert records to the database
from manage_video_db import insert_multiple_detections

# Import utils from object detection module
from object_detection.utils import visualization_utils as vis_util

################################################################################
#                              Model preparation
################################################################################

# path to save tested images with bboxes and object counts
PATH_TO_SAVE_IMAGES_DIR = '/home/lserra/Work/Serving/output_folder/video'

category_index = {1: {'id': 1, 'name': 'pedestrian'}}

# Configuration parameters
# set minimum score threshold
THRESHOLD = 0.5
# host ip address
HOST = 'localhost'
# model to use
MODEL_NAME='faster_rcnn_video'

################################################################################
#                    Prepare to use gRPC endpoint from tf serving 
################################################################################

# gRPC API expects a serialized PredictRequest protocol buffer as input
# Establish a gRPC channel and a stub
def create_grpc_stub(host, port=8500):
    hostport = '{}:{}'.format(host, port)
    channel = grpc.insecure_channel(hostport)
    stub = prediction_service_pb2_grpc.PredictionServiceStub(channel)

    return stub


# Call model and signature to make predictions on the image
def grpc_request(stub, data_sample, model_name=MODEL_NAME, \
                 signature_name='serving_default'):
    request = predict_pb2.PredictRequest()
    request.model_spec.name = model_name
    request.model_spec.signature_name = signature_name
    shp = [dim for dim in data_sample.shape]
    request.inputs['input_tensor'].CopyFrom(tf.make_tensor_proto(data_sample,
                                                                 shape=shp))
    # I think I need to increase this waiting time to something like 20sec? done
    result = stub.Predict(request, 100.0)

    return result


################################################################################
#                                  Detection
################################################################################

# call previous functions and make inference
def run_inference_for_single_image(host, data_sample):
    stub = create_grpc_stub(host)
    rs_grpc = grpc_request(stub, data_sample)

    # outputs of interest
    outputs = ['num_detections',
               'detection_boxes',
               'detection_scores', 
               'detection_classes']

    # add outputs of interest to a dict as arrays according to their dimension
    shape = []
    output_dict = {}
    for output in outputs:
        shape = tf.TensorShape(rs_grpc.outputs[output].tensor_shape).as_list()
        shape = shape[1:]
        output_dict[output] = np.array(rs_grpc.outputs[output].float_val).reshape(shape)
        shape = []

    # num_detections is an int
    num_detections = int(output_dict.pop('num_detections'))
    output_dict['num_detections'] = num_detections

    # detection_classes should be ints.
    output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)

    return output_dict


# Define and retrieve attributes of objects identified in a single image
def get_detections(image_name, image, boxes, classes, scores, cat_index, min_score_thresh):
    im_width, im_height = image.size
    detections = []
    for i in range(boxes.shape[0]):
        if scores is None or scores[i] > min_score_thresh:
            box = tuple(boxes[i].tolist())
            ymin, xmin, ymax, xmax = box
            (left, right, top, bottom) = (xmin * im_width,
                                          xmax * im_width,
                                          ymin * im_height,
                                          ymax * im_height)
            if classes[i] in cat_index.keys():
                class_name = cat_index[classes[i]]['name']
            else:
                class_name='N/A'
            detections.append(
            {'image': image_name,
             'image_size': {
                 'im_width':im_width, 
                 'im_height':im_height},
             'object': class_name,
             'coordinates': {
                 'left': left,
                 'right': right,
                 'bottom': bottom,
                 'top': top},
             'score': scores[i]
            }
        )
    return detections

def show_inference(host, image_path):
    # read an image
    image = Image.open(image_path)
    image_np = np.array(image)
    image_np_expanded = np.expand_dims(image_np, axis=0)

    start = time.time()

    # Actual detection.
    output_dict = run_inference_for_single_image(host, image_np_expanded)

    end = time.time()
    time_diff = round((end - start), 3)
    print(f'Elapsed time to make prediction on the image: {time_diff} seconds')

    # put boxes and labels on image
    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np,
        output_dict['detection_boxes'],
        output_dict['detection_classes'],
        output_dict['detection_scores'],
        category_index,
        use_normalized_coordinates=True,
        max_boxes_to_draw=200,
        min_score_thresh=THRESHOLD,
        line_thickness=8)

    image_name = os.path.basename(image_path)

    detections = get_detections(
        image_name,
        image,
        output_dict['detection_boxes'],
        output_dict['detection_classes'],
        output_dict['detection_scores'],
        category_index,
        THRESHOLD)

    # write detections to the video db
    insert_multiple_detections(detections)
    #print(detections)

    # save image with bounding boxes
    im_save = Image.fromarray(image_np)
    image_base = os.path.splitext(image_name)[0]
    image_ext= os.path.splitext(image_name)[1]
    new_img_name = image_base + '_bbox' + image_ext
    im_save.save(PATH_TO_SAVE_IMAGES_DIR + '/' + new_img_name)


show_inference(HOST, sys.argv[1])
#our final output should be something like detections, for single image or overall_detections if analysing a batch of images
