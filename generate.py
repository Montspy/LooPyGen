from PIL import Image, ImageDraw, ImageFont
from IPython.display import display
import random
import json
import os
import torch
import torchvision
import torchvision.transforms as T
import re
import argparse
import shutil
import traits

# check for command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("total", help="Total number of images to generate", type=int)
parser.add_argument("-c", "--clear", help="Empty the generated directory", action="store_true")
parser.add_argument("--id", nargs=1, help="Specify starting ID for images", type=int)
args = parser.parse_args()

# Define amount of images to generate
TOTAL_IMAGES = args.total

genPath = "./images/generated"
dataPath = "./metadata"

# Remove directories if asked to
if args.clear:
    if os.path.exists(genPath):
        shutil.rmtree(genPath)
    if os.path.exists(dataPath):
        shutil.rmtree(dataPath)

# Make paths if they don't exist
if not os.path.exists(genPath):
    os.makedirs(genPath)
if not os.path.exists(dataPath):
    os.makedirs(dataPath)

# Set starting ID
if args.id:
    startingId = args.id[0]
else:
    startingId = 0

## Generate Traits

all_images = []

# A recursive function to generate unique image combinations
def create_new_image():

    # New, empty dictionary
    new_image = {}

    # For each trait category, select a random trait based on the weightings
    new_image [traits.names["layer01"]] = random.choices(traits.layer01_names, traits.layer01_weights)[0]
    new_image [traits.names["layer02"]] = random.choices(traits.layer02_names, traits.layer02_weights)[0]
    new_image [traits.names["layer03"]] = random.choices(traits.layer03_names, traits.layer03_weights)[0]
    new_image [traits.names["layer04"]] = random.choices(traits.layer04_names, traits.layer04_weights)[0]

    if new_image in all_images:
        return create_new_image()
    else:
        return new_image

# Generate the unique combinations based on layer weightings
for i in range(TOTAL_IMAGES):

    new_layer_image = create_new_image()

    all_images.append(new_layer_image)

# Returns true if all images are unique
def all_images_unique(all_images):
    seen = list()
    return not any(i in seen or seen.append(i) for i in all_images)

print("Are all images unique?", all_images_unique(all_images))
# Add token Id to each image
for item in all_images:
    item["ID"] = startingId
    startingId = startingId + 1

print(all_images)

# Get Trait Counts
print("How many of each trait exist?")

trait01_count = {}
for item in traits.layer01_names:
    trait01_count[item] = 0

trait02_count = {}
for item in traits.layer02_names:
    trait02_count[item] = 0

trait03_count = {}
for item in traits.layer03_names:
    trait03_count[item] = 0

trait04_count = {}
for item in traits.layer04_names:
    trait04_count[item] = 0

for image in all_images:
    trait01_count[image[traits.names["layer01"]]] += 1
    trait02_count[image[traits.names["layer02"]]] += 1
    trait03_count[image[traits.names["layer03"]]] += 1
    trait04_count[image[traits.names["layer04"]]] += 1

print(trait01_count)
print(trait02_count)
print(trait03_count)
print(trait04_count)

STATS_FILENAME = dataPath + '/gen-stats.json'
with open(STATS_FILENAME, 'w') as outfile:
    json.dump(trait01_count, outfile, indent=4)
    json.dump(trait02_count, outfile, indent=4)
    json.dump(trait03_count, outfile, indent=4)
    json.dump(trait04_count, outfile, indent=4)

#### Generate Images

for item in all_images:

    # Define and convert images
    trait01_file = Image.open(f'{traits.layer01dir}{traits.layer01_filenames[item[traits.names["layer01"]]]}').convert('RGBA')
    trait02_file = Image.open(f'{traits.layer02dir}{traits.layer02_filenames[item[traits.names["layer02"]]]}').convert('RGBA')
    trait03_file = Image.open(f'{traits.layer03dir}{traits.layer03_filenames[item[traits.names["layer03"]]]}').convert('RGBA')
    trait04_file = Image.open(f'{traits.layer04dir}{traits.layer04_filenames[item[traits.names["layer04"]]]}').convert('RGBA')

    # Create the composite image
    composite = Image.alpha_composite(trait01_file, trait02_file)
    composite = Image.alpha_composite(composite, trait03_file)
    composite = Image.alpha_composite(composite, trait04_file)

    #Convert to RGB
    rgb_im = composite.convert('RGB')
    file_name = traits.names["collection"] + "_" + str(item["ID"]) + ".png"
    rgb_im.save(genPath + "/" + file_name)
    print("Generated " + genPath + "/" + file_name)

#### Generate Metadata for all Traits

METADATA_FILE_NAME = dataPath + '/all-traits.json'
with open(METADATA_FILE_NAME, 'w') as outfile:
    json.dump(all_images, outfile, indent=4)
