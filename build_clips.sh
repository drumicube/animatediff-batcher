#!/bin/bash

clipfolder=$1
[ $# -eq 0 ] && { echo "No clip folder provided."; exit 1; }

animatediffprojectfolder="/home/yoyo2k1/Videos/AnimateDiff_Projects"
realesrgan="/home/yoyo2k1/projects/realesrgan-ncnn-vulkan-v0.2.0-ubuntu/realesrgan-ncnn-vulkan"

#interpolcommand="/home/yoyo2k1/projects/rife-ncnn-vulkan-20221029-ubuntu/rife-ncnn-vulkan"
#interpolmodel="rife-v4"
#interpolfolder="rife"

interpolcommand="/home/yoyo2k1/projects/ifrnet-ncnn-vulkan-20220720-ubuntu/ifrnet-ncnn-vulkan"
interpolmodel="IFRNet_Vimeo90K"
interpolfolder="ifrnet"

inputfolder=$animatediffprojectfolder/$clipfolder
img2imgfolder=$inputfolder"/input_clips/interp/"
outputfolder=$inputfolder"/output/"

width=1024
height=1536
model=4x-UltraSharp-opt-fp16
quality=19  # The range of the CRF scale is 0–51 (23 is the default,  17 or 18 to be visually lossless , and 51 is worst quality possible.)
fps=60

#################### building mp4 (stable-diffusion-webui/outputs/txt2img-images/AnimateDiff/interp/)

shopt -s nullglob
mkdir -p $outputfolder

### Generate single video clips
for subdir in $img2imgfolder*/
do
    # generate esrgan upscaled frames
    img2imgupscaleddir=$subdir"up/"

    if [[ ! -d $img2imgupscaleddir ]]; then
      mkdir -p $img2imgupscaleddir
      $realesrgan -s 4 -i $subdir -o $img2imgupscaleddir -n $model
    fi

    if [[ -d $img2imgupscaleddir ]]
    then
        pngfiles=($img2imgupscaleddir/*.png)
        nbpngfiles=${#pngfiles[@]}
        echo "img2img upscaled folder (up) located in: "$img2imgupscaleddir

        mp4name=${subdir#"$img2imgfolder"}
        mp4name=${mp4name%"/"}
        echo "processing: "$mp4name" (number of pngs files: "$nbpngfiles")"

        interpolatedpath=$subdir$interpolfolder
        if [[ ! -d $interpolatedpath ]]; then
          mkdir -p $interpolatedpath
          $interpolcommand -m $interpolmodel -x -i $img2imgupscaleddir -o $interpolatedpath
        fi
        echo "###############################################################################"
        echo Building clip: $outputfolder$mp4name.$model.webm
        echo "###############################################################################"
        ffmpeg -y -framerate $fps -i $interpolatedpath/%08d.png -crf $quality -c:v libvpx-vp9 -vf scale="$width:$height" -pix_fmt yuv420p $outputfolder$mp4name.$model.webm
    fi
done
