import numpy as np
import tensorflow as tf
from PIL import Image
import os
from matplotlib import pyplot as plt
import time
from glob import glob
cwd = os.path.dirname(os.path.realpath(__file__))
from utils import label_map_util

from utils import visualization_utils
import detections_grpc_video as dgv


#category_index = {1: {'id': 1, 'name': 'pedestrian'}}
category_index = {1: {'id': 1, 'name': 'pedestrian'},
                  2: {'id': 2, 'name': 'bycicle'},
                  3: {'id': 3, 'name': 'partially-visible person'},
                  4: {'id': 4, 'name': 'ignore region'},
                  5: {'id': 5, 'name': 'crowd'}}

# minimum threshold for detections
THRESHOLD = 0.2


class ObjectDetector(object):



    def __init__(self):

        self.object_boxes = []
        # self.boxes = boxes
        # self.scores = scores
        # self.classes = classes
        # self.num_detections = num_detections

    def load_image_into_numpy_array(self, image):
         (im_width, im_height) = image.size
         return np.array(image.getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)       

    def box_normal_to_pixel(self, box, dim):    
        height, width = dim[0], dim[1]
        box_pixel = [int(box[0]*height), int(box[1]*width), int(box[2]*height), int(box[3]*width)]
        return np.array(box_pixel)       
        
    def get_localization(self, image, visual=False):
        global category_index
        global THRESHOLD

        input_image = np.asarray(image)
        image_np_expanded = np.expand_dims(input_image, axis = 0)
        
        
        output_dict = dgv.run_inference_for_single_image('localhost', image_np_expanded)
        
        # Run inference
        detection_boxes = output_dict['detection_boxes']
        detection_scores = output_dict['detection_scores']
        detection_classes = output_dict['detection_classes']
        num_detections = output_dict['num_detections']

        # Actual detection.
        (boxes, scores, classes, num) = detection_boxes, detection_scores, detection_classes, num_detections
        if visual == True:
            visualization_utils.visualize_boxes_and_labels_on_image_array_tracker(
                image,
                np.squeeze(boxes),
                np.squeeze(classes).astype(np.int32),
                np.squeeze(scores),
                category_index,
                use_normalized_coordinates=True,min_score_thresh=THRESHOLD,
                line_thickness=3)
            plt.figure(figsize=(9,6))
            plt.imshow(image)
            plt.show()
        boxes=np.squeeze(boxes)
        classes =np.squeeze(classes)
        scores = np.squeeze(scores)
        cls = classes.tolist()
        idx_vec = [i for i, v in enumerate(cls) if ((scores[i]>THRESHOLD))]
        if len(idx_vec) ==0:
            print('there are not any detections, passing to the next frame...')
        else:
            tmp_object_boxes=[]
            for idx in idx_vec:
                dim = image.shape[0:2]
                box = self.box_normal_to_pixel(boxes[idx], dim)
                box_h = box[2] - box[0]
                box_w = box[3] - box[1]
                ratio = box_h/(box_w + 0.01)

                #if ((ratio < 0.8) and (box_h>20) and (box_w>20)):
                tmp_object_boxes.append(box)
                #print(box, ', confidence: ', scores[idx], 'ratio:', ratio)

            self.object_boxes = tmp_object_boxes
        return self.object_boxes, output_dict, category_index, THRESHOLD
