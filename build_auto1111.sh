#!/bin/bash

script_dir="$(dirname "$(readlink -f "$0")")"
source $script_dir/animatediff-batcher.cfg

clipfolder=$1
[ $# -eq 0 ] && { echo "No clip folder provided."; exit 1; }

inputfolder=$animatediff_input_folder/$clipfolder
[ ! -d $inputfolder ] && { echo "Directory $inputfolder does not exists."; exit 1; }
cd $auto1111_folder || { echo "Failure: $auto1111_folder does not exists"; exit 1; }

while :
do
  # kill last instance of Auto1111 and relaunch it (prevent ADetailer crash)
  pkill -f "python3 -u launch.py"
  echo "Sleeping for 15 seconds."
  sleep 15
  ./webui.sh &
  sleep 15

  # Call python script to process remaining clips with Auto1111 api
  if ! python3 $script_dir/build_auto1111_clip.py "$inputfolder" "$auto1111_folder"; then
    echo "Done: Killing auto1111, then exiting."
    pkill -f "python3 -u launch.py"
    exit
  fi
done
