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
    new_image [traits.names["trait01"]] = random.choices(traits.trait01, traits.trait01_weights)[0]
    new_image [traits.names["trait02"]] = random.choices(traits.trait02, traits.trait02_weights)[0]
    new_image [traits.names["trait03"]] = random.choices(traits.trait03, traits.trait03_weights)[0]
    new_image [traits.names["trait04"]] = random.choices(traits.trait04, traits.trait04_weights)[0]
    new_image [traits.names["trait05"]] = random.choices(traits.trait05, traits.trait05_weights)[0]
    new_image [traits.names["trait06"]] = random.choices(traits.trait06, traits.trait06_weights)[0]
    new_image [traits.names["trait07"]] = random.choices(traits.trait07, traits.trait07_weights)[0]

    if new_image in all_images:
        return create_new_image()
    else:
        return new_image

# Generate the unique combinations based on trait weightings
for i in range(TOTAL_IMAGES):

    new_trait_image = create_new_image()

    all_images.append(new_trait_image)

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
for item in traits.trait01:
    trait01_count[item] = 0

trait02_count = {}
for item in traits.trait02:
    trait02_count[item] = 0

trait03_count = {}
for item in traits.trait03:
    trait03_count[item] = 0

trait04_count = {}
for item in traits.trait04:
    trait04_count[item] = 0

trait05_count = {}
for item in traits.trait05:
    trait05_count[item] = 0

trait06_count = {}
for item in traits.trait06:
    trait06_count[item] = 0

trait07_count = {}
for item in traits.trait07:
    trait07_count[item] = 0

for image in all_images:
    trait01_count[image[traits.names["trait01"]]] += 1
    trait02_count[image[traits.names["trait02"]]] += 1
    trait03_count[image[traits.names["trait03"]]] += 1
    trait04_count[image[traits.names["trait04"]]] += 1
    trait05_count[image[traits.names["trait05"]]] += 1
    trait06_count[image[traits.names["trait06"]]] += 1
    trait07_count[image[traits.names["trait07"]]] += 1

print(trait01_count)
print(trait02_count)
print(trait03_count)
print(trait04_count)
print(trait05_count)
print(trait06_count)
print(trait07_count)

#### Generate Images

for item in all_images:

    # Define and convert images
    trait01_file = Image.open(f'{traits.trait01dir}{traits.trait01_paths[item[traits.names["trait01"]]]}').convert('RGBA')
    trait02_file = Image.open(f'{traits.trait02dir}{traits.trait02_paths[item[traits.names["trait02"]]]}').convert('RGBA')
    trait03_file = Image.open(f'{traits.trait03dir}{traits.trait03_paths[item[traits.names["trait03"]]]}').convert('RGBA')
    trait04_file = Image.open(f'{traits.trait04dir}{traits.trait04_paths[item[traits.names["trait04"]]]}').convert('RGBA')
    trait05_file = Image.open(f'{traits.trait05dir}{traits.trait05_paths[item[traits.names["trait05"]]]}').convert('RGBA')
    trait06_file = Image.open(f'{traits.trait06dir}{traits.trait06_paths[item[traits.names["trait06"]]]}').convert('RGBA')
    trait07_file = Image.open(f'{traits.trait07dir}{traits.trait07_paths[item[traits.names["trait07"]]]}').convert('RGBA')

    # Create the composite image
    composite = Image.alpha_composite(trait01_file, trait02_file)
    composite = Image.alpha_composite(composite, trait03_file)
    composite = Image.alpha_composite(composite, trait04_file)
    composite = Image.alpha_composite(composite, trait05_file)
    composite = Image.alpha_composite(composite, trait06_file)
    composite = Image.alpha_composite(composite, trait07_file)

    #Convert to RGB
    rgb_im = composite.convert('RGB')
    file_name = traits.names["collection"] + "_" + str(item["ID"]) + ".png"
    rgb_im.save(genPath + "/" + file_name)
    print("Generated " + genPath + "/" + file_name)

#### Generate Metadata for all Traits

METADATA_FILE_NAME = dataPath + '/all-traits.json';
with open(METADATA_FILE_NAME, 'w') as outfile:
    json.dump(all_images, outfile, indent=4)
