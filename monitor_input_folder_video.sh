#!/usr/bin/env bash

DIR_IN="/home/lserra/Work/Serving/input_folder/video"
DIR_ARCHIVE="/home/lserra/Work/Serving/archive_folder/video"
SCRIPT_VIDEO="/home/lserra/Work/Serving/object_tracking.py"

source /home/lserra/python-virtual-environments/serving/bin/activate

inotifywait -m -e create -e moved_to --format "%w%f" $DIR_IN | while read file

do
  if [ ${file: -4} == ".mp4" ]
  then
    echo Detected $file, running counts and detections
    python $SCRIPT_VIDEO $file
    mv $file $DIR_ARCHIVE
  fi
done
