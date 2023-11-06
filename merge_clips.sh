#!/bin/bash

script_dir="$(dirname "$(readlink -f "$0")")"
source $script_dir/animatediff-batcher.cfg

clipfolder=$1
[ $# -eq 0 ] && { echo "No clip folder provided."; exit 1; }

outputfolder=$animatediff_input_folder/$clipfolder"/output/*/"

for subclipdir in $outputfolder
do

  movie_name=${subclipdir#"$animatediff_input_folder/$clipfolder/output/"}
  movie_name=${movie_name%"/"}

  ### Rebuild cliplist txt file
  echo "#####################################################################"
  echo Rebuilding sub txt cliplist: $subclipdir"cliplist_$movie_name.txt"
  rm -f $subclipdir"cliplist_$movie_name.txt"
  for f in $subclipdir*.webm
  do
      if [[ ! $f == *merged* ]]
      then
          echo "file '$f'" >> $subclipdir"cliplist_$movie_name.txt"
      fi
  done

  ### Merge all clips together
  echo Merging all sub clips into $subclipdir"merged_$movie_name.webm"
  ffmpeg -y -loglevel 0 -safe 0 -f concat -i $subclipdir"cliplist_$movie_name.txt" -c copy $subclipdir"merged_$movie_name.webm"
  echo "#####################################################################"

done
