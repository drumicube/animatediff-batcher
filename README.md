# animatediff-batcher

A small scripting tool to batch process animatediff clips generated under automatic1111:  
This script suite will take as input all animatediff clips from an input folder.  
It kills and reload Auto1111 on each animation, preventing ADetailer to crash after one rendering. 

* **build_auto1111.sh**: Rebuild all animatediff clips (gif, png, txt) located in your input folder using auto1111 api, adding to them FILM mode and a ADetailer pass.
* **build_clips.sh**: Upscale and interpolate all previously generated png frames, and merge them to rebuild a webm clip. 
* **merge_clips.sh**: Concatenate generated webm clips into final movies.

## Requirements

* ffmpeg
* python3.10
* [RIFE ncnn Vulkan](https://github.com/nihui/rife-ncnn-vulkan) or [IFRNet ncnn Vulkan](https://github.com/nihui/ifrnet-ncnn-vulkan)
* [Real-ESRGAN ncnn Vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan)
* Auto1111 configured to autostart with api support (--api)
* Auto1111 configured with 'Pad prompt/negative prompt to be same length'
* AnimateDiff extension configured with 'Save frames to stable-diffusion-webui/outputs/{ txt|img }2img-images/AnimateDiff/{gif filename}/'


## Limitations

* Swapping checkpoints is not supported, the last loaded checkpoint from Auto1111 will be used.
* Prompt travel is not supported.


## Configuration

* Copy animatediff-batcher.cfg.sample to animatediff-batcher.cfg
* Edit animatediff-batcher.cfg to update path and settings.
