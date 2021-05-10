#!/usr/bin/env bash

DIR_IN="/home/lserra/Work/Serving/input_folder/video/cam2"
DIR_ARCHIVE="/home/lserra/Work/Serving/archive_folder/video"
SCRIPT_VIDEO="/home/lserra/Work/Serving/object_tracking.py"
LOG_FILE="/home/lserra/Work/Serving/cam2.log"
FLUSH_TRIGGER=12

source /home/lserra/python-virtual-environments/serving/bin/activate

inotifywait -m -e create -e moved_to --format "%w%f" $DIR_IN | while read file

do
  if [ ${file: -4} == ".mp4" ]
  then
    echo Detected $file, running counts and detections
    echo $LOG_FILE
    echo "$LOG_FILE"
    python $SCRIPT_VIDEO $file $FLUSH_TRIGGER 2>&1 | tee -a "$LOG_FILE"
    #python $SCRIPT_VIDEO $file $FLUSH_TRIGGER >> "$LOG_FILE" 2>&1
    mv $file $DIR_ARCHIVE
  fi
done
