# base imports
import numpy as np
import grpc
import tensorflow as tf
from tensorflow_serving.apis import predict_pb2
from tensorflow_serving.apis import prediction_service_pb2_grpc

import config_file as config

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
def grpc_request(stub, data_sample, model_name=config.MODEL_NAME, \
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


# Define and retrieve attributes of objects identified on a single image
def get_detections(frame_sequence, im_width, im_height, boxes, classes, scores, cat_index, min_score_thresh):
    detections = []
    for i in range(boxes.shape[0]):
        if scores is None or scores[i] > min_score_thresh:
            box = tuple(boxes[i].tolist())
            ymin, xmin, ymax, xmax = box
            (left, right, top, bottom) = (xmin * im_width,
                                          xmax * im_width,
                                          ymin * im_height,
                                          ymax * im_height)
            detections.append(
            {'frame_sequence': frame_sequence,
             'class': int(classes[i]), #cast numpy.int64 to python int
             'coordinates': {
                 'left': left,
                 'right': right,
                 'bottom': bottom,
                 'top': top},
             'score': scores[i]
            }
        )
    return detections
