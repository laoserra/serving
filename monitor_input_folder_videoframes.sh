#!/usr/bin/env bash

DIR_IN="/home/lserra/Work/Serving/input_folder/video"
DIR_ARCHIVE="/home/lserra/Work/Serving/archive_folder/video"
SCRIPT_DETECTIONS="/home/lserra/Work/Serving/detections_grpc_videoframes.py"

source /home/lserra/python-virtual-environments/serving/bin/activate

inotifywait -m -e create -e moved_to --format "%w%f" $DIR_IN | while read file

do
  if [ ${file: -4} == ".mp4" ]
  then
    for video in $DIR_IN/*.mp4
      do
        echo Converting $video to jpeg frames
        ffmpeg -i $video $DIR_IN/"$(basename "$video" .mp4)"_%06d.jpg
        mv $video $DIR_ARCHIVE
        start=`date +%s`
        for frame in $DIR_IN/*.jpg
          do
            echo Detected $frame, executing detections script
            python $SCRIPT_DETECTIONS $frame
            mv $frame $DIR_ARCHIVE
          done
        end=`date +%s`
        runtime=$( echo "$end - $start" | bc )
        echo 'Elapsed time to process all images: '$runtime' sec'
      done
  fi
done
