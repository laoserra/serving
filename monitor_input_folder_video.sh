#!/usr/bin/env bash

DIR_IN="/home/lserra/Work/Serving/input_folder/video"
DIR_ARCHIVE="/home/lserra/Work/Serving/archive_folder/video"
SCRIPT="/home/lserra/Work/Serving/detections_grpc_video.py"

source /home/lserra/python-virtual-environments/serving/bin/activate

inotifywait -m -e create -e moved_to --format "%w%f" $DIR_IN | while read file

do
  if [ ${file: -4} == ".avi" ]
  then
    echo Detected $file, converting to jpeg frames
    ffmpeg -i $file $DIR_IN/"$(basename "$file" .avi)"_%06d.jpg
    mv $file $DIR_ARCHIVE
    for frame in $DIR_IN/*.jpg
      do
        echo Detected $frame, executing detections script
        python $SCRIPT $frame
        mv $frame $DIR_ARCHIVE
      done
  fi
done
