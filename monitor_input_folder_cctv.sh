#!/usr/bin/env bash

DIR_IN="/home/lserra/Work/Serving/input_folder/cctv"
DIR_ARCHIVE="/home/lserra/Work/Serving/archive_folder/cctv"
SCRIPT="/home/lserra/Work/Serving/detections_grpc_cctv.py"

source /home/lserra/python-virtual-environments/serving/bin/activate

inotifywait -m -e create -e moved_to --format "%w%f" $DIR_IN | while read file

do
  if [ ${file: -4} == ".jpg" ] || [ ${file: -4} == ".JPG" ]
  then
      # update script from video bash script
    echo Detected $file, executing detections script
    python $SCRIPT $file
    mv $file $DIR_ARCHIVE
  fi
done
