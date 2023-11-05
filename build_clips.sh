#!/bin/bash

# test rife not upscaled from auto1111
# /home/yoyo2k1/projects/rife-ncnn-vulkan-20221029-ubuntu/rife-ncnn-vulkan -m rife-v4.6 -x -n 128 -i /home/yoyo2k1/Videos/test/input/ -o /home/yoyo2k1/Videos/test/output/
# test IFRNet not upscaled from auto1111
# /home/yoyo2k1/projects/ifrnet-ncnn-vulkan-20220720-ubuntu/ifrnet-ncnn-vulkan -m IFRNet_GoPro -x -n 128 -i /home/yoyo2k1/Videos/test/input/ -o /home/yoyo2k1/Videos/test/output2/
# rebuild movie
# ffmpeg -y -framerate 60 -i /home/yoyo2k1/Videos/test/output/%08d.png -crf 19 -c:v libvpx-vp9 -vf scale="1024:1536" -pix_fmt yuv420p /home/yoyo2k1/Videos/test/output/movie.webm


script_dir="$(dirname "$(readlink -f "$0")")"
source $script_dir/animatediff-batcher.cfg

clipfolder=$1
[ $# -eq 0 ] && { echo "No clip folder provided."; exit 1; }

inputfolder=$animatediff_input_folder/$clipfolder
img2imgfolder=$inputfolder"/processed/interp/"
outputfolder=$inputfolder"/output/"

#################### building mp4

shopt -s nullglob
mkdir -p $outputfolder

### Generate single video clips
for subdir in $img2imgfolder*/
do
    # generate esrgan upscaled frames
    img2imgupscaleddir=$subdir"upscaled/"

    if [[ ! -d $img2imgupscaleddir ]]; then
      mkdir -p $img2imgupscaleddir
      $real_esrgan_command -s 4 -i $subdir -o $img2imgupscaleddir -n $real_esrgan_model
    fi

    if [[ -d $img2imgupscaleddir ]]
    then
        pngfiles=($img2imgupscaleddir/*.png)
        mp4name=${subdir#"$img2imgfolder"}
        mp4name=${mp4name%"/"}
        nbpngfiles=${#pngfiles[@]}
        echo "processing: "$mp4name" (number of pngs files: "$nbpngfiles")"

        # generate interpolated frames
        interpolatedpath=$subdir$interpol_folder
        if [[ ! -d $interpolatedpath ]]; then
          mkdir -p $interpolatedpath
          $interpol_command -m $interpol_model -x -i $img2imgupscaleddir -o $interpolatedpath
        fi

        # building webm clip from generated frames
        if [[ ! -f $outputfolder$mp4name.$real_esrgan_model.webm ]]; then
          echo "###############################################################################"
          echo Building clip: $outputfolder$mp4name.$real_esrgan_model.webm
          echo "###############################################################################"
          ffmpeg -y -framerate $fps -i $interpolatedpath/%08d.png -crf $quality -c:v libvpx-vp9 -vf scale="$width:$height" -pix_fmt yuv420p $outputfolder$mp4name.$real_esrgan_model.webm
        fi
    fi
done
