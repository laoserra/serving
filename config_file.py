################################################################################
#                              Configuration parameters
################################################################################

# class labels
CATEGORY_INDEX = {1: {'id': 1, 'name': 'pedestrian'},
                  2: {'id': 2, 'name': 'cyclist'},
                  3: {'id': 3, 'name': 'partially-visible person'},
                  4: {'id': 4, 'name': 'ignore region'},
                  5: {'id': 5, 'name': 'crowd'}}

#PATH_TO_SAVE_VIDEOS = '/home/lserra/Work/Serving/output_folder/video/'
OUTPUT_FOLDER = '/home/lserra/Work/Serving/output_folder/video/'

# PATH to existent database
PATH_DB = OUTPUT_FOLDER + 'video.db'
#PATH_TO_SAVE_TRACKS = '/home/lserra/Work/Serving/output_folder/video/'

# disposition of crossing line
HORIZONTAL = True

# detection threshold
THRESHOLD = 0.5

# object detection model to make use of
MODEL_NAME = 'widerperson'

#IP address of the model server
HOST = 'localhost'
################################################################################
