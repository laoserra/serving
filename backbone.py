import numpy as np
import matplotlib.pyplot as plt
from collections import deque
#from sklearn.utils.linear_assignment_ import linear_assignment
from scipy.optimize import linear_sum_assignment as linear_assignment
import collections
import detection_layer
import cv2
import json
import os
import sys


from utils.object_tracking_module import tracking_layer
from utils.object_tracking_module import tracking_utils
from trackableobject import TrackableObject
from output_directories import horizontal


max_detection = 15
min_detection =1
n_frame = 0

sum_unmatched_dets = 0
trackableObjects = {}
tracker_all = collections.defaultdict(dict)
tracker_dict = {}
tracker_list =[]
id_counter = 0
det = detection_layer.ObjectDetector()

totalDown = 0
totalUp = 0

#file name for tracks
video_name = os.path.basename(sys.argv[1])
video_base = os.path.splitext(video_name)[0]
output_tracks_name = video_base + '_tracks'




def iou(bb_test, bb_gt):
    """
  Computes IUO between two bboxes in the form [x1,y1,x2,y2]
  """
    xx1 = np.maximum(bb_test[0], bb_gt[0])
    yy1 = np.maximum(bb_test[1], bb_gt[1])
    xx2 = np.minimum(bb_test[2], bb_gt[2])
    yy2 = np.minimum(bb_test[3], bb_gt[3])
    w = np.maximum(0., xx2 - xx1)
    h = np.maximum(0., yy2 - yy1)
    wh = w * h
    res = ((bb_test[2] - bb_test[0]) * (bb_test[3] - bb_test[1]) + (bb_gt[2] - bb_gt[0]) * (
                bb_gt[3] - bb_gt[1]) - wh)
    if res != 0:      
        o = wh / res
    else:
        o = 0
    #print(o)
    return (o)


def convert_boxes_to_centroids(boxes):
    x1, y1, x2, y2 = boxes[1], boxes[0], boxes[3], boxes[2]
    x = x1 + int((x2 - x1) / 2)
    y = y1 + int((y2 - y1) / 2)
    return [x, y]


def assign_detections_to_trackers(trackers, detections, iou_thrd = 0.3):
    # if there is no trackers (start of the footage) return empty array
    if (len(trackers) == 0):
        return np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 5), dtype=int)
    # initiate empty matrix of len(det), len (trk)
    iou_matrix = np.zeros((len(detections), len(trackers)), dtype=np.float32)

    # extract the array of detections and trackers only
    for d, det in enumerate(detections):
        for t, trk in enumerate(trackers):
            # then write each detection and tracker IOU into the matrix (i.e. 0.1. 0.2, 03).
            # The loop compares each det with each trk
            iou_matrix[d, t] = iou(det, trk)
            
    # extract the indices of optimally matched dets and trks (Hungarian algorithm)
    # Algorithm selects the highest IOU for each det. Output is in the form [0,1,2], [1,0,2] (Selects the highest from each row)
    # This means that tracker[1] corresponds to det[0], 0->1, 2->2. Unmatched trackers are not saved to this array
    try:
        matched_indices = linear_assignment(-iou_matrix)
    except:
        print('matrix contains invalid numeric')
    # convert tuple to array (size is A x 2) where A is the number of matched pairs
    matched_indices = np.asarray(matched_indices)
    # initiate an empty array of unmatched detections
    unmatched_detections = []
    # loop over all detections and extract all unmatched detections (d is just an index)
    for d, det in enumerate(detections):
        # [0,:] corresponds to all matched detections indices
        if d not in matched_indices[0, :]:
            unmatched_detections.append(d)
    unmatched_trackers = []
    for t, trk in enumerate(trackers):
        # [1,:] corresponds to all matched trackers indices
        if t not in matched_indices[1, :]:
            unmatched_trackers.append(t)
    # initiate matches array
    matches = []
    # loop over all matched indices
    for m in np.transpose(matched_indices):
        # filter out matches with low IOU
        # Go inside each location (m[0],m[1] corresponds to one IOU value left after Hung algorithm)
        if (iou_matrix[m[0], m[1]] < iou_thrd):
            # add unmathced values to already existing ones
            unmatched_detections.append(m[0])
            unmatched_trackers.append(m[1])
        else:
            # append all the matches into separate array
            matches.append(m.reshape(1, 2))
    if len(matches) == 0:
        matches = np.empty((0, 2), dtype=int)
    else:
        matches = np.concatenate(matches, axis=0)
    # return all of the arrays
    return matches, np.array(unmatched_detections), np.array(unmatched_trackers)       


def processor(img, h, w):
    global tracker_list
    global max_detection
    global min_detection
    global track_id_list
    global sum_unmatched_dets
    global totalDown
    global totalUp
    global id_counter
    global n_frame
    global horizontal
    global tracker_dict
    
    
#declare either horizontal or vertical line for pedestrian countings    
    if horizontal == True:
        loi = h
        coord = 1
    else:
        loi = w
        coord = 0
    
    n_frame = n_frame+1
    # get the detections bounding boxes
    # get_localization function runs the tf detection
    z_box_raw = det.get_localization(img)
    z_box = z_box_raw[0]
    output_dict = z_box_raw[1]
    cat_index = z_box_raw[2]
    threshold = z_box_raw[3]
    # initiate the tracker list
    x_box =[]

    if len(tracker_list) > 0:
        for trk in tracker_list:
            # add tracking boxes from the previous frames
            # it updates constantly unmatched tracks eventually deleted
            x_box.append(trk.box)

    # call the function
    matched, unmatched_dets, unmatched_trks = assign_detections_to_trackers(x_box, z_box, iou_thrd = 0.3)
    # calculate the total number of objetcs appeared in the footage (roughly)
    # considering each unmatched_det is the new object appeared in the frame
         
    # matched detections
    # not entering this part from the beginning (matched size is 0 at first run)
    if matched.size >0:
        for det_idx, trk_idx in matched:
            # extract the boxes of matched detected objects only
            z = z_box[det_idx]
            z = np.expand_dims(z, axis=0).T
            # extract the boxes of matched tracked objects only
            tmp_trk= tracker_list[trk_idx]
            # Apply kalman filter with update part
            tmp_trk.kalman_filter(z)
            # extract bounding boxes XX
            xx = tmp_trk.x_state.T[0].tolist()
            # extract positions only (up, left, down, right)
            xx =[xx[0], xx[2], xx[4], xx[6]]
            # write KF output box to the tracked boxes array
            x_box[trk_idx] = xx
            tmp_trk.box =xx
            # number of detection matches
            tmp_trk.hits += 1
    
    # unmatched detections
    # the code enters this part first because first detections are unmatched by default (no tracking values)
    if len(unmatched_dets)>0:
        # loop over unmatched detections
        for idx in unmatched_dets:
            z = z_box[idx]
            z = np.expand_dims(z, axis=0).T
            # call the object "Tracker"
            tmp_trk = tracking_layer.Tracker() # new tracker
            # create array with the bounding boxes locations and the velocities
            # velocity is set to 0 if the detection is not matched
            x = np.array([[z[0], 0, z[1], 0, z[2], 0, z[3], 0]]).T

            # assign the state array for Kalman filter
            tmp_trk.x_state = x
            # predict thfe tracking boxes and velocities using predict_only
            # function different from KF (no update part)
            tmp_trk.predict_only()
            # write the predicted values into XX variable
            xx = tmp_trk.x_state
            # Transpose the array
            xx = xx.T[0].tolist()
            # extract the locations only (uo, left, down, right)
            xx =[xx[0], xx[2], xx[4], xx[6]]
            # list to store the coordinates for a bounding box
            tmp_trk.box = xx
            # assign the ID to the tracked box
            tmp_trk.id = id_counter 
            id_counter = id_counter + 1
            # add the tracking box into the tracker list (in the binary form for cv2 draw)
            tracker_list.append(tmp_trk)
            # add the tracking box into the tracker list (in the integer form)
            x_box.append(xx)


    # unmatched tracks
    # this tracks are not stored into tracker_list so not drawn on the image
    if len(unmatched_trks)>0:
        for trk_idx in unmatched_trks:
            tmp_trk = tracker_list[trk_idx]
            # add a number of unmatched tracks (track loss)
            tmp_trk.no_losses += 1
            # function different from KF (no update part)
            # these values are not using for the further computations so can bde deleted
            tmp_trk.predict_only()
            xx = tmp_trk.x_state
            xx = xx.T[0].tolist()
            xx =[xx[0], xx[2], xx[4], xx[6]]
            tmp_trk.box =xx
            x_box[trk_idx] = xx
                         
    good_tracker_list =[]


    # loop over all tracked list
    for trk in tracker_list:
        # if within a constraint
        if ((trk.hits >= min_detection) and (trk.no_losses <=max_detection)):
             good_tracker_list.append(trk)
             x_cv2 = trk.box
             #convert boxes to their centroid values
             center = convert_boxes_to_centroids(x_cv2)
			 #append object ID as keys and centers as values to the dictionary
             tracker_dict.setdefault(trk.id, []).append(center)
             #draw the box on frame
             img= tracking_utils.draw_box_label(trk.id,img, x_cv2)
             
    #update tracks every 100 frames          
    # if n_frame == 25:
        # with open(PATH_TO_SAVE_TRACKS+'/'+output_tracks_name + '.json', 'w') as fp:
	        # json.dump(tracker_dict, fp)
	        # n_frame = 0;
    
	#iterate through the dictionary	
    for (objectID, center) in tracker_dict.items():
		#check if ObjectID is in the trackableObjects class
        check = trackableObjects.get(objectID, None)

		# if there is no existing trackable object, create one
        if check is None:
            check = TrackableObject(objectID, center)

		# otherwise, there is a trackable object so we can utilize it
		# to determine direction
        else:
			# the difference between the y-coordinate of the *current*
			# centroid and the mean of *previous* 5 centroids will tell
			# us in which direction the object is moving (negative for
			# 'up' and positive for 'down') We need its length to be more than 5
            #x = [c[1] for c in check.center]
            
            if len(center)>5:		
                check.center.append(center)
                mean_value = (center[-5][coord] + center[-4][coord] + center[-3][coord] + center[-2][coord] + center[-1][coord]) / 5	
                direction = center[-1][coord] - mean_value
           
				# check to see if the object has been counted or not
                if not check.counted:
					# if the direction is negative (indicating the object
					# is moving up) AND the centroid is above the check
					# line AND the mean of the previous values is below the line, count the object
					# Mean of the previous values needs to be checked so prevent objects which are already below the line
					# and moving to the negative direction to be counted
                    if direction < 0 and center[-1][coord]  < loi/2 and mean_value > loi/2:
                        totalUp += 1
                        check.counted = True
                    # same logic but for the positive direction    
                    elif direction > 0 and center[-1][coord]  > loi/2 and mean_value < loi/2:
                        totalDown += 1
                        check.counted = True
		# store the trackable object in our dictionary
        trackableObjects[objectID] = check

		# draw the line and put text on the frame
        if horizontal == True:
            cv2.line(img, (0, int(loi/2)), (w, int(loi/2)), (0, 0xFF, 0), 5)
        else:
            cv2.line(img, (int(loi/2), 0), (int(loi/2), h), (0, 0xFF, 0), 5)

        cv2.putText(img, 'Up ' + str(totalUp) + '            Down ' + str(totalDown) + '             Total ' + str(totalUp+totalDown), (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.FONT_HERSHEY_SIMPLEX)

    print('Total number of people crossed ' + str(totalUp+totalDown))
    tracker_list = [x for x in tracker_list if x.no_losses<=max_detection]
    return img, output_dict, cat_index, threshold
