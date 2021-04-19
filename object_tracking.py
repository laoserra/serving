import numpy as np
import cv2
import backbone
import time
import tensorflow as tf
import sys
import os


from utils.object_tracking_module import tracking_layer
from utils import label_map_util
from output_directories import PATH_TO_SAVE_VIDEOS
from manage_video_db import insert_video_data
from manage_video_db import insert_multiple_tracks


#Uncomment the next line if you want CPU execution
#os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

#grab the video file
cap = cv2.VideoCapture(sys.argv[1])
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
fps = int(cap.get(cv2.CAP_PROP_FPS))
fourcc = cv2.VideoWriter_fourcc(*'XVID')
#save the output video with bounding boxes
video_name = os.path.basename(sys.argv[1])
video_base = os.path.splitext(video_name)[0]
video_ext= os.path.splitext(video_name)[1]
output_video_name = video_base + '_bbox' + video_ext
out = cv2.VideoWriter(PATH_TO_SAVE_VIDEOS + '/' + output_video_name, fourcc, fps, (width, height))


#initialize the frame counting variable
frame_number = 0
#initialize the time
init_time = time.time()
while(True):     
    #extract frame from the video       
    ret, img = cap.read()    
    if ret:
        np.asarray(img)
        #count the frames
        frame_number += 1
        start_time = time.time()
        #process the image
        processed_img = backbone.processor(img, height, width)
        #print(return_tracks_data())
        print ("per-frame time: " + str(time.time() - start_time) + " seconds")
        print ("overall time: " + str(time.time() - init_time) + " seconds")     
        out.write(processed_img)
        print("writing frame " + str(frame_number))
    #break the while loop if there is no frames to process    
    else:
        break 
print("end of the video!")

# insert data to the video table
insert_video_data(video_name, height, width, backbone.totalUp, backbone.totalDown)

# insert tracks to the tracks table
insert_multiple_tracks(backbone.tracker_dict, video_name)
