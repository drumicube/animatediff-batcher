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

if len(sys.argv) != 4:
    print("Aborting: invalid number or input arguments for " + sys.argv[0] + " script.")
    exit(1)
clipFolder = sys.argv[1]
clipName = sys.argv[2]
hiresDenoise = sys.argv[3]

if not os.path.isdir(clipFolder):
    print("Aborting clipFolder: " + clipFolder + " does not exist.")
    exit(1)
esrganFramesFolder = clipFolder + "/processed/frames/" + clipName + "/esrgan"
if not os.path.exists(esrganFramesFolder):
    print("Aborting processed folder: " + esrganFramesFolder + " does not exist.")
    exit(1)
hiresFixFramesFolder = clipFolder + "/processed/frames/" + clipName + "/hiresfix"
if not os.path.exists(hiresFixFramesFolder):
    os.makedirs(hiresFixFramesFolder)


# HiresFix pass using the original prompt and the esrgan upscaled frames
alwayson_scripts = {
    "ADetailer": {
        "args": [
            {
                "ad_model": "face_yolov8n.pt",
                "ad_mask_k_largest": 4,
            }
        ]
    }
}

# Check original files
originalMetadataFileName = clipFolder + "/" + clipName + ".txt"
if not os.path.isfile(originalMetadataFileName):
    print("Metadata file " + originalMetadataFileName + " not found.")
    exit(1)
originalGifFileName = clipFolder + "/" + clipName + ".gif"
if not os.path.isfile(originalGifFileName):
    print("Gif file " + originalGifFileName + " not found.")
    exit(1)

# Read metadata file
metadata_file = open(os.path.join(originalMetadataFileName), "r")
metadata_txt = metadata_file.read()
metadata_file.close()

# Rebuild metadata for Auto1111 API
metadata = parse_generation_parameters(metadata_txt)
metadata["width"] = metadata["Size-1"]
metadata["height"] = metadata["Size-2"]
metadata["cfg_scale"] = metadata["CFG scale"]

metadata["seed"] = metadata["Seed"]
metadata["steps"] = metadata["Steps"]
metadata["prompt"] = metadata["Prompt"]
metadata["negative_prompt"] = metadata["Negative prompt"]
metadata["sampler_index"] = metadata["Sampler"]
metadata["alwayson_scripts"] = alwayson_scripts

filelist=os.listdir(esrganFramesFolder)
for imageName in filelist[:]:
    if not(imageName.endswith(".png")):
        continue

    f = open(esrganFramesFolder + "/" + imageName, "rb")
    encoded_image = base64.b64encode(f.read()).decode('utf-8')
    f.close()

    img2img_payload = {
            "init_images": [encoded_image],
            "prompt": metadata["Prompt"],
            "negative_prompt": metadata["Negative prompt"],
            "seed": metadata["Seed"],
            "denoising_strength": hiresDenoise,
            "width": int(metadata["Size-1"])*2,
            "height": int(metadata["Size-2"])*2,
            "cfg_scale": metadata["CFG scale"],
            "sampler_name": metadata["Sampler"],
            "restore_faces": False,
            "steps": metadata["Steps"],
            "send_images": True,
            "save_images": False,
            "alwayson_scripts": alwayson_scripts
        }

    # Call Auto1111 API
    response = requests.post(url=f'{url}/sdapi/v1/img2img', json=img2img_payload)
    if response.status_code == 200:
        response_data = response.json()
        encoded_result = response_data["images"][0]
        result_data = base64.b64decode(encoded_result)
        with open(hiresFixFramesFolder + "/" + imageName, 'wb') as file:
            file.write(result_data)
            file.close()
    else:
        print("Error Auto1111 Hiresfix:", response.text)
        exit(1)

exit(0)




