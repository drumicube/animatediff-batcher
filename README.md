# animatediff-batcher

A small scripting tool to batch process simple animatediff clips generated under automatic1111:  
This script will process all AnimateDiff clips stored in a predefined input folder (animatediff_input_folder).  
All clips will be regenerated, adding to them a ADetailer pass, an ESRGAN pass, an img2img hires fix pass and a frame interpolation pass (60fps) using Rife or IFRNET.   
To prevent ADetailer crashing on the second movie generation, Auto1111 is rebooted before processing each animation.

The motivation behind this tool was pretty simple:  
Building AnimateDiff clips with high quality settings is very time consuming.  
Just batch lots of quick and minimal AnimateDiff clips (no frame interpolation, no Adetailer, low res) under Auto1111 as usual.  
Then, copy your favorite clip selection in a working folder, and let this tool automatically rebuild them in higher quality.  

## Requirements

* ffmpeg
* python3.10
* [RIFE ncnn Vulkan](https://github.com/nihui/rife-ncnn-vulkan) or [IFRNet ncnn Vulkan](https://github.com/nihui/ifrnet-ncnn-vulkan)
* [Real-ESRGAN ncnn Vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan)
* [4x-UltraSharp model for ESRGAN](https://openmodeldb.info/models/4x-UltraSharp) (copy all files in the 'models' subfolder next to the ERSCAN executable)
* Auto1111 configured to autostart with api support (--api)
* Auto1111 configured with 'Pad prompt/negative prompt to be same length'
* AnimateDiff extension configured with 'Save frames to stable-diffusion-webui/outputs/{ txt|img }2img-images/AnimateDiff/{gif filename}/'


## Limitations

* Linux only, no support for Windows. 
* Prompt travel is not supported.
* 16 frames support only (not tested with more, but it will surely fail).
* Required by Auto1111 API: You must tag your negative embeddings with the embedding keyword (```<embedding:bad-artist-anime>, <embedding:bad-picture-chill-75v>```)
 

## Disclaimer

Sorry, no support or bugfix, use this at your own risk.   
I have no intention to maintain this, it's just a dirty tool to automate my workflow.  
It did the job for me, I'm done with it.  

## Configuration

* Copy animatediff-batcher.cfg.sample to animatediff-batcher.cfg
* Edit animatediff-batcher.cfg and customize it according to your needs.

| Variable                 | Default value                | Description                                          |
|--------------------------|------------------------------|------------------------------------------------------|
| auto1111_folder          |                              | Absolute path to your Automatic1111 local install    |
| animatediff_input_folder |                              | Absolute path to the clip folder to be processed     |
| auto1111_timeout         | 10                           | Time in seconds to wait after rebooting auto1111     |
| hires_denoise            | 0.35                         | Denoise strength to be used by the hires pass        |
| real_esrgan_command      |                              | Absolute path to the ESRGAN executable               |
| real_esrgan_model        | 4x-UltraSharp-opt-fp16       | Model used by ESRGAN for upscaling                   |
| interpol_command         |                              | Absolute path to the Rife or IFRNet executable       |
| interpol_model           | rife-v4.6 or IFRNet_Vimeo90K | Model used by Rife or IFRNET for frame interpolation |
| interpol_folder          | ifrnet or rife               | Local folder name to store interpolated frames       |
| width                    | 512                          | Width in pixel of webm clips                         |
| height                   | 768                          | Height in pixel of webm clips                        |
| quality                  | 19                           | Encoding quality for ffmpeg                          |
| fps                      | 60                           | fps of webm clips                                    |


**Note regarding animatediff_input_folder**:  
Do not point this variable to the original AnimateDiff folder stored inside Auto1111 (_stable-diffusion-webui/outputs/txt2img-images/AnimateDiff/_)  
This variable must point to a folder where you have cherry-picked and copied AnimateDiff clips to be processed (.txt files + .gif files).  


## How to use

### Preparing files:

* Create a **animatediff_input_folder** folder (ex: /home/user/mybestclips).
* Create a subfolder inside your **animatediff_input_folder** for your current project (ex: /home/user/mybestclips/project1) 
* Batch generate simple AnimateDiff clips under Auto1111 as usual. (No highres fix, No Adetailer, 16 frames, Interpolation to Off)
* Copy all your favorite AnimateDiff clips (gif + txt files) into your project folder (ex: /home/user/mybestclips/project1)  
* Ensure your **animatediff-batcher.cfg** is correctly set, especially the needed paths.

### Processing files:

Run the following command to process all clips located into your project1 folder:
```commandline
./build_auto1111.sh project1
```

**Important:**   
As a reboot of Auto1111 is needed on each clip generation (ADetailer crash on second AnimateDiff clip), your current Auto1111 session will be terminated!  
Do not use Auto1111 while this script is running. Restart Auto1111 once it's finished.

### After processing:

Your 'project1' folder should now look like this:  

| folder                                                       | Content                                                                                |
|--------------------------------------------------------------|----------------------------------------------------------------------------------------|
| mybestclips/project1                                         | Empty if all clips processed successfully                                              |
| mybestclips/project1/output                                  | Contains generated hires 60fps webm animation files                                    |
| mybestclips/project1/archived                                | On each successful clip generation, the original clip is moved here                    |
| mybestclips/project1/processed                               | Contains Auto1111 rebuilt clips with a Adetailer pass                                  |
| mybestclips/project1/processed/frames/clipIdx-seed/          | Contains the 16 frames generated by the Auto1111 Adetailer pass for clip clipIdx-seed  |
| mybestclips/project1/processed/frames/clipIdx-seed/esrgan/   | Contains the 16 frames generated by the esrgan pass (4xUpscaled) for clip clipIdx-seed |
| mybestclips/project1/processed/frames/clipIdx-seed/hiresfix/ | Contains the 16 frames generated by the img2img hires pass for clip clipIdx-seed       |
| mybestclips/project1/processed/frames/clipIdx-seed/rife      | Contains the 128 frames generated by the rife pass for clip clipIdx-seed               |

'rife' being the final folder (128 frames) used by ffmpeg to generate the webm video.


### Building movies by merging several clips:

An additional helper script is also available to quickly merge several clips into final movies:  

* In the output folder containing all the webm of your project, create as many movie sub-folder as needed (movie1, movie2 etc.)
* Copy the needed webm clips from the parent folder in the needed movie subfolders to build your sequence.

Run this command to merge all clips by movie folder.
```commandline
./merge_clips.sh project1
```
A merged webm file should be present in each movie sub-folder.

**Note:** The merge being based on clip names, just add a number prefix to clip files for fine tuning the clip order.  
