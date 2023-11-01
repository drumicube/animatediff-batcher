#!/bin/bash

script_dir="$(dirname "$(readlink -f "$0")")"
source $script_dir/animatediff-batcher.cfg

clipfolder=$1
[ $# -eq 0 ] && { echo "No clip folder provided."; exit 1; }

outputfolder=$animatediff_input_folder/$clipfolder"/output/*/"

for subclipdir in $outputfolder
do
  ### Rebuild cliplist txt file
  echo "#####################################################################"
  echo Rebuilding sub txt cliplist: $subclipdir"cliplist_webm.txt"
  rm -f $subclipdir"cliplist_webm.txt"
  for f in $subclipdir*.webm
  do
      if [[ ! $f == *merged* ]]
      then
          echo "file '$f'" >> $subclipdir"cliplist_webm.txt"
      fi
  done

  ### Merge all clips together
  echo Merging all sub clips into $subclipdir"merged.webm"
  ffmpeg -y -loglevel 0 -safe 0 -f concat -i $subclipdir"cliplist_webm.txt" -c copy $subclipdir"merged.webm"
  echo "#####################################################################"

done
