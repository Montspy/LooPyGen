from copy import deepcopy
from PIL import Image
from base64 import b64encode
from dotenv import load_dotenv
import random
import time
import json
import os
import sys
import argparse
import shutil

import traits

# Paths generation
COLLECTION_LOWER = traits.COLLECTION_NAME.replace(" ", "_").lower()
COLLECTION_PATH = os.path.join("./generated", COLLECTION_LOWER)
DATA_PATH = os.path.join(COLLECTION_PATH, "metadata")
IMAGES_PATH = os.path.join(COLLECTION_PATH, "images")

METADATA_FILE_NAME = os.path.join(DATA_PATH, "all-traits.json")
STATS_FILENAME = os.path.join(DATA_PATH, "gen-stats.json")

# load .env file into memory
load_dotenv()

# set the SOURCE_FILES if it's not specified in .env
if os.getenv("SOURCE_FILES") is None:
    SOURCE_FILES = os.path.join("./images", COLLECTION_LOWER)
else:
    SOURCE_FILES = os.getenv("SOURCE_FILES")

# Image generation class
class ImageGenerator(object):
    seed: str               # Randomness seed
    prev_batches: list      # Pre-existing images
    this_batch: list        # New images
    dup_cnt_limit: int      # Maximum number of tries to create a unique image

    def __init__(self, seed: str, prev_batches: list, dup_cnt_limit: int):
        self.seed = seed
        # Remove IDs to make comparison to new image easier
        self.prev_batches = deepcopy(prev_batches)
        for img in self.prev_batches:
            img.pop("ID", None)
        self.this_batch = []
        self.dup_cnt_limit = dup_cnt_limit

    # A recursive function to generate unique image combinations
    def create_new_image(self, id: int, dup_cnt: int = 0):
        # New, empty dictionary
        new_image = {}

        # Seed each image based on randomness seed and ID
        image_seed = f"{self.seed}{id}{dup_cnt}"
        random.seed(image_seed)

        # For each trait category, select a random trait based on the weightings
        for l in traits.layers:
            new_image[l["layer_name"]] = random.choices(l["names"], l["weights"])[0]

        if new_image in self.this_batch or new_image in self.prev_batches:
            if dup_cnt > self.dup_cnt_limit:
                return new_image
            return self.create_new_image(id, dup_cnt + 1)
        else:
            return new_image

    def generate_images(self, starting_id: int, image_cnt: int):
        self.prev_batches.extend(self.this_batch)
        self.this_batch = []
        for i in range(image_cnt):
            unique_image = self.create_new_image(id=starting_id + i)
            self.this_batch.append(unique_image)
        # Add IDs
        batch_with_id = []
        for i, img in enumerate(self.this_batch):
            batch_with_id.append(img)
            batch_with_id[i]["ID"] = starting_id + i
        return batch_with_id


# Returns true if all images are unique
def all_images_unique(all_images):
    # Remove IDs to make comparison to new image easier
    images = deepcopy(all_images)
    for img in images:
        img.pop("ID", None)
    seen = list()
    return not any(i in seen or seen.append(i) for i in images)

# Combine and sort the lists
def sortID(e):
    return e["ID"]

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--count", help="Total number of images to generate", type=int, required=True)
    parser.add_argument("-e", "--empty", help="Empty the generated directory", action="store_true")
    parser.add_argument("--id", help="Specify starting ID for images", type=int, default = 1)
    parser.add_argument("--seed", help="Randomness seed", type=str, default=None)
    args = parser.parse_args()
    return args

def generate_paths(empty: bool):
    if empty:
        if os.path.exists(IMAGES_PATH):
            shutil.rmtree(IMAGES_PATH)
        if os.path.exists(METADATA_FILE_NAME):
            os.remove(METADATA_FILE_NAME)
        if os.path.exists(STATS_FILENAME):
            os.remove(STATS_FILENAME)

    # Make paths if they don't exist
    if not os.path.exists(IMAGES_PATH):
        os.makedirs(IMAGES_PATH)
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)


def main():
    # check for command line arguments
    args = parse_args()

    # Define amount of images to generate
    total_image = args.count

    if total_image > traits.get_variation_cnt():
        sys.exit(f"count ({total_image}) cannot be greater than the number of variations ({traits.get_variation_cnt()})")

    # Remove directories if asked to
    generate_paths(args.empty)

    # Set starting ID
    starting_id = args.id
    print("Starting at ID: " + str(starting_id))

    # Randomness seed
    if args.seed is not None:
        SEED = args.seed
    elif os.getenv("SEED") is not None:
        SEED = str(os.getenv("SEED"))
    else:
        timestamp = time.time_ns().to_bytes(16, byteorder='big')
        SEED = b64encode(timestamp).decode("utf-8") # Encode timestamp to a base64 string
    print(f"Using randomness seed: {SEED}")

    ## Generate Traits
    # Check if all-traits.json exists
    if os.path.exists(METADATA_FILE_NAME):
        print("Previous batches exist, pulling in their data.")
        with open(METADATA_FILE_NAME, 'r') as f:
            prev_batches = []
            seen = set(range(starting_id, starting_id + total_image))
            for img in json.load(f):    # Keep only IDs not being re-generated
                if img["ID"] not in seen:
                    seen.add(img["ID"])
                    prev_batches.append(img)

    else:
        prev_batches = []

    # Remove IDs that will get replaced


    ## Generate folders and names list from layers available in traits
    for i, l in enumerate(traits.layers):
        l["names"] = list(l["filenames"].keys())
        l["path"] = os.path.join(SOURCE_FILES, f"layer{i + 1:02}")

    # Generate the unique combinations based on layer weightings
    img_gen = ImageGenerator(seed=SEED, prev_batches=prev_batches, dup_cnt_limit=traits.get_variation_cnt())
    this_batch = img_gen.generate_images(starting_id=starting_id, image_cnt=total_image)

    all_images = prev_batches
    all_images.extend(this_batch)

    all_images.sort(key=sortID)

    # Couble check that all images are unique to the whole collection
    print("Are all images unique?", all_images_unique(all_images))

    # Get Trait Counts
    print("How many of each trait exist?")

    for l in traits.layers:
        l["count"] = {item: 0 for item in l["names"]}

    for image in all_images:
        n = 1
        for l in traits.layers:
            item = image[l["layer_name"]]
            l["count"][item] += 1

    for i, l in enumerate(traits.layers):
        print(f"Layer {i + 1:02}: {l['count']}")

    ## Store trait counts to json
    with open(STATS_FILENAME, 'w') as outfile:
        gen_stats = {l["layer_name"]: l["count"] for l in traits.layers}
        json.dump(gen_stats, outfile, indent=4)

    #### Generate Images
    for item in this_batch:
        # Open images as they are needed
        parts = []
        for l in traits.layers:
            layer_pretty_name = item[l["layer_name"]]
            layer_file = os.path.join(l["path"], l["filenames"][layer_pretty_name])

            try:
                part = l["image"][layer_pretty_name]
            except KeyError as e:   # Image needs to get loaded
                if not "image" in l:
                    l["image"] = {}
                l["image"][layer_pretty_name] = Image.open(layer_file).convert('RGBA')
                part = l["image"][layer_pretty_name]
            parts.append(part)

        # Composite all layers on top of each others
        composite = parts[0].copy()
        for p in parts:
            composite = Image.alpha_composite(composite, p)

        # # Convert to RGB (uncomment section)
        # background_color = (128, 128, 128)
        # background = Image.new(mode="RGB", size=composite.size, color=background_color)
        # background.paste(composite, mask=composite.split()[3])  # Drop the alpha channel
        # composite = background

        file_path = os.path.join(IMAGES_PATH, f"{COLLECTION_LOWER}_{item['ID']:03}.png")
        composite.save(file_path)
        print(f"Generated {file_path}")

    # Close images
    [img.close() for l in traits.layers if "image" in l for _,img in l["image"].items()]

    #### Generate Metadata for all Traits

    with open(METADATA_FILE_NAME, 'w') as outfile:
        json.dump(all_images, outfile, indent=4)

    print("Look in " + METADATA_FILE_NAME + " for an overview of all generated IDs and traits.")

if __name__ == "__main__":
    main()