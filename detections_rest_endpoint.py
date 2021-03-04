import json
from PIL import Image
import numpy as np
import pandas as pd
import requests
import sys
import os

# The parent directory, "object-detection" is also needed because I suspect the utils 
#modules need other scripts in the parent directory "object_detection"

# Import the object detection module
#from utils import ops as utils_ops
from object_detection.utils import label_map_util
#from utils import visualization_utils as vis_util

image = Image.open(sys.argv[1])
image_np = np.array(image)

# this part of the code is very inefficient because 32bit floats are converted
#to 120bit strings in the json format. 
payload = json.dumps({"instances": [image_np.tolist()]})

headers = {"content-type": "application/json"}
url = 'http://localhost:8501/v1/models/faster_rcnn:predict'

json_response = requests.post(url, data=payload, headers=headers)
output_dict = json.loads(json_response.text)['predictions']

# maybe it's worthwhile to let just 2 decimal places in th arrays. See "hands-on ML book"
# here we are accessing the first image of output_dict above
# Take index [0] to remove the batch dimension.
output_dict = output_dict[0]

#------------------------------------------------------------------------------------
'''
Maybe it's worthwhile to encapsulate the code below to create a function to 
return a single output_dict for each image, like: def run_inference_for_single_image(output_dict[0]):
'''
# num_detections is an int
num_detections = int(output_dict.pop('num_detections'))

# Convert values from list to numpy arrays
output_dict = {key:np.array(value) for key,value in output_dict.items()}
output_dict['num_detections'] = num_detections

# detection_classes should be ints.
output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)
#------------------------------------------------------------------------------------

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = '/home/lserra/Work/tensorflow/models/research/object_detection/data/mscoco_label_map.pbtxt'

# Here we are using an utility from object detection but we can do it without using this utility
# and consequently without having to pip install these utilities and tf?
# don't think so because we still need to put the bounding boxes in the pictures
category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)

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
            {'image_id': image_name,
             'object': class_name,
             'coordinates': {
                 'left': left,
                 'right': right,
                 'bottom': bottom,
                 'top': top
                 },
             'score': scores[i]
            }
        )
    return detections

threshold = 0.3 # set minimun score threshold


image_name = os.path.basename(sys.argv[1])
image = image


detections = get_detections(
    image_name,
    image,
    output_dict['detection_boxes'],
    output_dict['detection_classes'],
    output_dict['detection_scores'],
    category_index,
    threshold)
#our final output should be something like detections, for single image or overall_detections if analysing a batch of images
print(pd.DataFrame(detections))
