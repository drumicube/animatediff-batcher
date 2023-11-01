#!/bin/bash

clipfolder=$1
[ $# -eq 0 ] && { echo "No clip folder provided."; exit 1; }


auto1111folder="/home/yoyo2k1/stable-diffusion-webui"
animatediffprojectfolder="/home/yoyo2k1/Videos/AnimateDiff_Projects"

inputfolder=$animatediffprojectfolder/$clipfolder
[ ! -d $inputfolder ] && { echo "Directory /path/to/dir DOES NOT exists."; exit 1; }

while :
do
  pkill -f "python3 -u launch.py"
  echo "Sleeping for 15 seconds."
  sleep 15
  cd $auto1111folder || { echo "Failure: $auto1111folder does not exists"; exit 1; }
  ./webui.sh &
  sleep 15

  cd $animatediffprojectfolder || { echo "Failure: $animatediffprojectfolder does not exists"; exit 1; }
  if ! python build_auto1111_clip.py "$inputfolder" "$auto1111folder"; then
    echo "Done: Killing auto1111, then exiting."
    pkill -f "python3 -u launch.py"
    exit
  fi
done
