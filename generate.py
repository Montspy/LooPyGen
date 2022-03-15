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
parser.add_argument("-n", "--number", nargs=1, help="Total number of images to generate", type=int)
parser.add_argument("-c", "--clear", help="Empty the generated directory", action="store_true")
parser.add_argument("--id", nargs=1, help="Specify starting ID for images", type=int)
args = parser.parse_args()

# Define amount of images to generate
TOTAL_IMAGES = args.number[0]

genPath = "./images/generated"
dataPath = "./metadata"
METADATA_FILE_NAME = dataPath + '/all-traits.json'
STATS_FILENAME = dataPath + '/gen-stats.json'
COLLECTION_LOWER = traits.COLLECTION_NAME.replace(" ", "_").lower()

# Remove directories if asked to
if args.clear:
    if os.path.exists(genPath):
        shutil.rmtree(genPath)
    if os.path.exists(METADATA_FILE_NAME):
        os.remove(METADATA_FILE_NAME)
    if os.path.exists(STATS_FILENAME):
        os.remove(STATS_FILENAME)

# Make paths if they don't exist
if not os.path.exists(genPath):
    os.makedirs(genPath)
if not os.path.exists(dataPath):
    os.makedirs(dataPath)

# Set starting ID
if args.id:
    startingId = args.id[0]
    print("Starting at ID: " + str(startingId))
else:
    startingId = 1

## Generate Traits

this_batch = []
all_images = []

# Check if all-traits.json exists
if os.path.exists(METADATA_FILE_NAME):
    print("Previous batches exist, pulling in their data.")
    f = open(METADATA_FILE_NAME)
    prev_batches = json.load(f)
    f.close()
else:
    prev_batches = []

## Top level image directory
topLevel = "./images/source_layers"

## Generate folders and names list from layers available in traits
n = 1
for l in traits.layers:
    traits.layers[n]["names"] = list(traits.layers[n]["filenames"].keys())
    traits.layers[n]["path"] = topLevel + "/layer0" + str(n) + "/"
    n = n + 1

# A recursive function to generate unique image combinations
def create_new_image():

    # New, empty dictionary
    new_image = {}
    n = 1

    # For each trait category, select a random trait based on the weightings
    for l in traits.layers:
        new_image[traits.layers[n]["layer_name"]] = random.choices(traits.layers[n]["names"], traits.layers[n]["weights"])[0]
        new_image["ID"] = startingId
        n = n + 1

    if new_image in this_batch or new_image in prev_batches:
        return create_new_image()
    else:
        return new_image

# Generate the unique combinations based on layer weightings
for i in range(TOTAL_IMAGES):

    new_layer_image = create_new_image()

    this_batch.append(new_layer_image)

    startingId = startingId + 1

# Returns true if all images are unique
def all_images_unique(all_images):
    seen = list()
    return not any(i in seen or seen.append(i) for i in all_images)

# Combine and sort the lists
def sortID(e):
    return e["ID"]

for i in prev_batches:
    all_images.append(i)

for i in this_batch:
    all_images.append(i)

all_images.sort(key=sortID)

# Couble check that all images are unique to the whole collection
print("Are all images unique?", all_images_unique(all_images))

# Get Trait Counts
print("How many of each trait exist?")

n = 1
for l in traits.layers:
    traits.layers[n]["count"] = {}
    for item in traits.layers[n]["names"]:
        traits.layers[n]["count"][item] = 0
    n = n + 1

for image in all_images:
    n = 1
    for l in traits.layers:
        traits.layers[n]["count"][image[traits.layers[n]["layer_name"]]] += 1
        n = n + 1

n = 1
for c in traits.layers:
    print(traits.layers[n]["count"])
    n = n + 1

## Store trait counts to json
n = 1
with open(STATS_FILENAME, 'w') as outfile:
    gen_stats = {}
    for l in traits.layers:
        gen_stats[traits.layers[n]["layer_name"]] = traits.layers[n]["count"]
        n = n + 1
    json.dump(gen_stats, outfile, indent=4)

#### Generate Images

for item in this_batch:

    n = 1
    for l in traits.layers:
        traits.layers[n]["file"] = Image.open(f'{traits.layers[n]["path"]}{traits.layers[n]["filenames"][item[traits.layers[n]["layer_name"]]]}').convert('RGBA')
        n = n + 1

    composite = Image.alpha_composite(traits.layers[1]["file"], traits.layers[2]["file"])

    if len(traits.layers) > 2:
        n = 1
        for l in traits.layers:
            if n < 3:
                n = n + 1
            else:
                composite = Image.alpha_composite(composite, traits.layers[n]["file"])
                n = n + 1

    #Convert to RGB
    rgb_im = composite.convert('RGB')
    file_name = traits.COLLECTION_LOWER + "_" + str(item["ID"]) + ".png"
    rgb_im.save(genPath + "/" + file_name)
    print("Generated " + genPath + "/" + file_name)

#### Generate Metadata for all Traits

with open(METADATA_FILE_NAME, 'w') as outfile:
    json.dump(all_images, outfile, indent=4)

print("Look in " + METADATA_FILE_NAME + " for an overview of all generated IDs and traits.")
