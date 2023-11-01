import json
import requests
import io
import os
import sys
import glob
import shutil
import base64
from PIL import Image
import re

url = "http://127.0.0.1:7860"

re_param_code = r'\s*([\w ]+):\s*("(?:\\.|[^\\"])+"|[^,]*)(?:,|$)'
re_param = re.compile(re_param_code)
re_imagesize = re.compile(r"^(\d+)x(\d+)$")
re_hypernet_hash = re.compile("\(([0-9a-f]+)\)$")


def parse_generation_parameters(x: str):
    """parses generation parameters string, the one you see in text field under the picture in UI:
```
girl with an artist's beret, determined, blue eyes, desert scene, computer monitors, heavy makeup, by Alphonse Mucha and Charlie Bowater, ((eyeshadow)), (coquettish), detailed, intricate
Negative prompt: ugly, fat, obese, chubby, (((deformed))), [blurry], bad anatomy, disfigured, poorly drawn face, mutation, mutated, (extra_limb), (ugly), (poorly drawn hands), messy drawing
Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 965400086, Size: 512x512, Model hash: 45dee52b
```

    returns a dict with field values
    """

    res = {}

    prompt = ""
    negative_prompt = ""

    done_with_prompt = False

    *lines, lastline = x.strip().split("\n")
    if len(re_param.findall(lastline)) < 3:
        lines.append(lastline)
        lastline = ''

    for line in lines:
        line = line.strip()
        if line.startswith("Negative prompt:"):
            done_with_prompt = True
            line = line[16:].strip()
        if done_with_prompt:
            negative_prompt += ("" if negative_prompt == "" else "\n") + line
        else:
            prompt += ("" if prompt == "" else "\n") + line

    res["Prompt"] = prompt
    res["Negative prompt"] = negative_prompt

    for k, v in re_param.findall(lastline):
        try:
            if v[0] == '"' and v[-1] == '"':
                v = unquote(v)

            m = re_imagesize.match(v)
            if m is not None:
                res[f"{k}-1"] = m.group(1)
                res[f"{k}-2"] = m.group(2)
            else:
                res[k] = v
        except Exception:
            print(f"Error parsing \"{k}: {v}\"")

    # Missing CLIP skip means it was set to 1 (the default)
    if "Clip skip" not in res:
        res["Clip skip"] = "1"

    hypernet = res.get("Hypernet", None)
    if hypernet is not None:
        res["Prompt"] += f"""<hypernet:{hypernet}:{res.get("Hypernet strength", "1.0")}>"""

    if "Hires resize-1" not in res:
        res["Hires resize-1"] = 0
        res["Hires resize-2"] = 0

    if "Hires sampler" not in res:
        res["Hires sampler"] = "Use same sampler"

    if "Hires checkpoint" not in res:
        res["Hires checkpoint"] = "Use same checkpoint"

    if "Hires prompt" not in res:
        res["Hires prompt"] = ""

    if "Hires negative prompt" not in res:
        res["Hires negative prompt"] = ""

    # Missing RNG means the default was set, which is GPU RNG
    if "RNG" not in res:
        res["RNG"] = "GPU"

    if "Schedule type" not in res:
        res["Schedule type"] = "Automatic"

    if "Schedule max sigma" not in res:
        res["Schedule max sigma"] = 0

    if "Schedule min sigma" not in res:
        res["Schedule min sigma"] = 0

    if "Schedule rho" not in res:
        res["Schedule rho"] = 0

    if "VAE Encoder" not in res:
        res["VAE Encoder"] = "Full"

    if "VAE Decoder" not in res:
        res["VAE Decoder"] = "Full"

    return res


# ########################### script starts here ###############################

if len(sys.argv) != 3:
    print("Aborting: invalid number or input arguments for " + sys.argv[0] + " script.")
    exit(1)

clipFolder = sys.argv[1]
auto1111Folder = sys.argv[2]
animatediff_path = auto1111Folder + "/outputs/txt2img-images/AnimateDiff"
if not os.path.isdir(clipFolder):
    print("Aborting clipFolder: " + clipFolder + " does not exist.")
    exit(1)
if not os.path.isdir(animatediff_path):
    print("Aborting animatediff_path: " + animatediff_path + " does not exist.")
    exit(1)

inputFolder = clipFolder
processedFolder = inputFolder + "/processed"
interpFolder = processedFolder + "/interp"
archivedFolder = inputFolder + "/archived"

if not os.path.isdir(inputFolder):
    print("Aborting: " + inputFolder + " does not exist. ")
    exit(1)
if not os.path.exists(processedFolder):
    os.makedirs(processedFolder)
if not os.path.exists(interpFolder):
    os.makedirs(interpFolder)
if not os.path.exists(archivedFolder):
    os.makedirs(archivedFolder)


alwayson_scripts = {
    "ADetailer": {
        "args": [
            {
                "ad_model": "face_yolov8n.pt",
                "ad_mask_k_largest": 4,
            }
        ]
    },
    'AnimateDiff': {
        'args': [{
            'model': 'mm_sd_v15_v2.safetensors',  # Motion module
            'format': ['GIF', 'PNG', 'TXT'],  # Save format, 'GIF' | 'MP4' | 'PNG' | 'WEBP' | 'TXT'
            'enable': True,  # Enable AnimateDiff
            'video_length': 16,  # Number of frames
            'fps': 8,  # FPS
            'loop_number': 0,  # Display loop number
            'closed_loop': 'N',  # Closed loop, 'N' | 'R-P' | 'R+P' | 'A'
            'batch_size': 16,  # Context batch size
            'stride': 1,  # Stride
            'overlap': -1,  # Overlap
            'interp': 'FILM',  # Frame interpolation, 'Off' | 'FILM'
            'interp_x': 4,  # Interp X
            'video_source': '',  # Video source
            'video_path': '',  # Video path
            'latent_power': 1,  # Latent power
            'latent_scale': 32,  # Latent scale
            'last_frame': None,  # Optional last frame
            'latent_power_last': 1,  # Optional latent power for last frame
            'latent_scale_last': 32  # Optional latent scale for last frame
        }
        ]
    }
}

# scan of txt files in input folder
for file in os.listdir(inputFolder):
    if file.endswith(".txt"):
        metadata_file = open(os.path.join(inputFolder, file), "r")
        metadata_txt = metadata_file.read()
        print(metadata_txt)
        metadata_file.close()
        metadata = parse_generation_parameters(metadata_txt)

        metadata["width"] = metadata["Size-1"]
        metadata["height"] = metadata["Size-2"]
        metadata["cfg_scale"] = metadata["CFG scale"]
        metadata["denoising_strength"] = 0
        metadata["seed"] = metadata["Seed"]
        metadata["steps"] = metadata["Steps"]
        metadata["prompt"] = metadata["Prompt"]
        metadata["negative_prompt"] = metadata["Negative prompt"]
        metadata["sampler_index"] = metadata["Sampler"]
        metadata["alwayson_scripts"] = alwayson_scripts

        response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=metadata)
        if response.status_code == 200:
            list_of_txt_files = glob.glob(animatediff_path + '/*.txt')
            latest_txt_file = max(list_of_txt_files, key=os.path.getctime)
            generated_filename = os.path.basename(os.path.splitext(latest_txt_file)[0])

            # copy generated files
            shutil.copyfile(animatediff_path + "/" + generated_filename + ".txt",
                            processedFolder + "/" + generated_filename + ".txt")
            shutil.copyfile(animatediff_path + "/" + generated_filename + ".gif",
                            processedFolder + "/" + generated_filename + ".gif")
            shutil.copytree(animatediff_path + "/interp/" + generated_filename, interpFolder + "/" + generated_filename)
            # backup original files
            fileNoExtension = os.path.splitext(file)[0]
            shutil.move(inputFolder + "/" + fileNoExtension + ".txt", archivedFolder + "/" + fileNoExtension + ".txt")
            shutil.move(inputFolder + "/" + fileNoExtension + ".gif", archivedFolder + "/" + fileNoExtension + ".gif")
            # first clip processed, we exit as Adetailer will fail on the next clip iteration
            exit(0)

print("Aborting: No clip was found in " + inputFolder)
exit(1)
