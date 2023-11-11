#!/bin/bash

shopt -s nullglob

bg_blue='\033[0;34m'
bg_end='\033[0m'

script_dir="$(dirname "$(readlink -f "$0")")"
source $script_dir/animatediff-batcher.cfg

clipfolder=$1
[ $# -eq 0 ] && { echo "No clip folder provided."; exit 1; }

inputfolder=$animatediff_input_folder/$clipfolder
[ ! -d $inputfolder ] && { echo "Directory $inputfolder does not exists."; exit 1; }
cd $auto1111_folder || { echo "Failure: $auto1111_folder does not exists"; exit 1; }


filesList=($inputfolder/*.txt)
for file in "${filesList[@]}"; do
    movie_name=$(basename ${file#"$inputfolder/"} .txt)
    # check if corresponding gif exists
    if [[ -f  $inputfolder/$movie_name.gif ]]; then

      printf "$bg_blue###############################################################################$bg_end\n"
      printf "$bg_blue#################### Rebooting Auto1111 for $movie_name $bg_end\n"
      printf "$bg_blue###############################################################################$bg_end\n"
      pkill -f "python3 -u launch.py"
      ./webui.sh &
      echo "Waiting $auto1111_timeout seconds to reboot Auto1111 before launching AnimateDiff queue."
      sleep $auto1111_timeout

      printf "$bg_blue###############################################################################################$bg_end\n"
      printf "$bg_blue############ Generating Adetailer frames for $movie_name using auto1111 txt2img API $bg_end\n"
      printf "$bg_blue###############################################################################################$bg_end\n"
      if ! python3 $script_dir/build_auto1111_adetailer.py "$inputfolder" "$auto1111_folder" "$movie_name"; then
        echo "Error: Auto1111 Adetailer pass failed. Killing Auto1111 and aborting."
        pkill -f "python3 -u launch.py"
        exit
      fi

      printf "$bg_blue###################################################################################$bg_end\n"
      printf "$bg_blue################# Generating esrgan upscaled frames for $movie_name $bg_end\n"
      printf "$bg_blue################################################################################### $bg_end\n"
      frame_esrgan_input_dir=$inputfolder"/processed/frames/"$movie_name
      frame_esrgan_dir=$frame_esrgan_input_dir"/esrgan"
      rm -fr $frame_esrgan_dir
      mkdir -p $frame_esrgan_dir
      if ! $real_esrgan_command -s 4 -i $frame_esrgan_input_dir -o $frame_esrgan_dir -n $real_esrgan_model; then
        echo "Error: ESRGAN pass failed. Aborting."
        pkill -f "python3 -u launch.py"
        exit
      fi

      printf "$bg_blue################################################################################################# $bg_end\n"
      printf "$bg_blue############# Generating Hires frames for $movie_name using auto1111 img2img api $bg_end\n"
      printf "$bg_blue################################################################################################# $bg_end\n"
      if ! python3 $script_dir/build_auto1111_hiresfix.py "$inputfolder" "$movie_name" $hires_denoise; then
        echo "Error: Auto1111 Hiresfix pass failed. Killing Auto1111 and aborting."
        pkill -f "python3 -u launch.py"
        exit
      fi

      printf "$bg_blue############################################################################################### $bg_end\n"
      printf "$bg_blue############## Generating Frame interpolation using rife for $movie_name $bg_end\n"
      printf "$bg_blue############################################################################################### $bg_end\n"
      frame_rife_input_dir=$inputfolder/processed/frames/$movie_name/hiresfix
      frame_rife_dir=$inputfolder/processed/frames/$movie_name/rife
      rm -fr $frame_rife_dir
      mkdir -p $frame_rife_dir
      if ! $interpol_command -m $interpol_model -x -n 128 -i $frame_rife_input_dir -o $frame_rife_dir; then
        echo "Error: Rife pass failed. Aborting."
        pkill -f "python3 -u launch.py"
        exit
      fi

      printf "$bg_blue######################################################################$bg_end\n"
      printf "$bg_blue################ Building final clip $movie_name $bg_end\n"
      printf "$bg_blue######################################################################$bg_end\n"
      mkdir -p $inputfolder/output
      ffmpeg -y -framerate $fps -i $inputfolder/processed/frames/$movie_name/rife/%08d.png -crf $quality -c:v libvpx-vp9 -vf scale="$width:$height" -pix_fmt yuv420p $inputfolder/output/$movie_name.webm

      printf "$bg_blue########################################################################$bg_end\n"
      printf "$bg_blue############# Archiving original clip $movie_name $bg_end\n"
      printf "$bg_blue########################################################################$bg_end\n"
      if [[ ! -d $inputfolder/archived ]]; then
        mkdir -p $inputfolder/archived
      fi
      mv $inputfolder/$movie_name.txt $inputfolder/archived
      mv $inputfolder/$movie_name.gif $inputfolder/archived

    fi
done

pkill -f "python3 -u launch.py"
