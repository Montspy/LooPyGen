from copy import deepcopy
from PIL import Image
from base64 import b64encode
from dotenv import load_dotenv
import yaspin
from ImageBuilder import ImageBuilder, ImageDescriptor, ImageType
import random
import time
import json
import os
import sys
import argparse
import asyncio
import shutil

import traits

# Paths generation
COLLECTION_LOWER =  "".join(map(lambda c: c if c.isalnum() else '_', traits.COLLECTION_NAME)).lower()
COLLECTION_PATH = os.path.join("./generated", COLLECTION_LOWER)
DATA_PATH = os.path.join(COLLECTION_PATH, "metadata")
IMAGES_PATH = os.path.join(COLLECTION_PATH, "images")

METADATA_FILE_NAME = os.path.join(COLLECTION_PATH, "all-traits.json")
STATS_FILENAME = os.path.join(COLLECTION_PATH, "gen-stats.json")

# Image generation class
class ImageGenerator(object):
    seed: str               # Randomness seed
    prev_batches: list      # Pre-existing images
    this_batch: list        # New images
    dup_cnt_limit: int      # Maximum number of tries to create a unique image

    def __init__(self, seed: str, prev_batches: list, dup_cnt_limit: int):
        self.seed = seed
        # Keep trait properties only, to make comparison to new image easier
        self.prev_batches = []
        for image in prev_batches:
            layer_names = [l["layer_name"] for l in traits.layers]
            self.prev_batches.append({name: image[name] for name in layer_names})

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
    parser.add_argument("--id", help="Specify starting ID for images", type=int, default=1)
    parser.add_argument("--seed", help="Specify the randomness seed", type=str, default=None)
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

# Image builder functions
async def build_and_save_image(item: dict, task_id: int):
    with ImageBuilder() as img_builder:
        for l in traits.layers:
            layer_pretty_name = item[l["layer_name"]]
        
            if l["type"] == "filenames":
                layer_file = os.path.join(l["path"], l["filenames"][layer_pretty_name])
                img_builder.overlay_image(layer_file)
            elif l["type"] == "rgba":
                if not "size" in l:
                    sys.exit(f"Missing image size for {l['layer_name']}")
                img_builder.overlay_image(l["rgba"][layer_pretty_name], size=l["size"])

        # Composite all layers on top of each others
        composite = await img_builder.build()

        if composite.type == ImageType.STATIC:
            file_path = os.path.join(IMAGES_PATH, f"{COLLECTION_LOWER}_{item['ID']:03}.png")
            composite.img.save(file_path)
        elif composite.type == ImageType.DYNAMIC:
            ext = os.path.splitext(composite.fp)[1]
            file_path = os.path.join(IMAGES_PATH, f"{COLLECTION_LOWER}_{item['ID']:03}{ext}")
            shutil.copy2(composite.fp, file_path)
        
        # print(f"Generated #{item['ID']:03}: {file_path}")
    return task_id

async def generate(batch: list): 
    # return await asyncio.gather(*[build_and_save_image(item) for item in batch])
    task_ids = [item['ID'] for item in batch]
    results = []

    with yaspin.kbi_safe_yaspin().line as spinner:
        spinner.text = f"Generating {len(task_ids)} images..."
        for task in asyncio.as_completed( [build_and_save_image(item, item['ID']) for item in batch] ):
            result = await task
            results.append(result)
            task_ids.remove(result)
            if len(task_ids) > 10:
                spinner.text = f"Generating {len(task_ids)} images..."
            else:
                spinner.text = f"Generating {' '.join( [f'#{id:03}' for id in task_ids] )}"

    return results

def main():
    # load .env file into memory
    load_dotenv()

    # check for command line arguments
    args = parse_args()

    # Define amount of images to generate
    total_image = args.count

    if total_image > traits.get_variation_cnt():
        sys.exit(f"count ({total_image}) cannot be greater than the number of variations ({traits.get_variation_cnt()})")

    # Remove directories if asked to
    generate_paths(args.empty)

    # set the SOURCE_FILES if it's not specified in .env
    if os.getenv("SOURCE_FILES") is not None and os.getenv("SOURCE_FILES") != "":
        SOURCE_FILES = os.getenv("SOURCE_FILES")
    else:
        SOURCE_FILES = os.path.join("./images", COLLECTION_LOWER)

    # Set starting ID
    starting_id = args.id
    print("Starting at ID: " + str(starting_id))

    # Randomness seed
    if args.seed is not None:
        SEED = args.seed
    elif os.getenv("SEED") is not None and os.getenv("SEED") != "":
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
            # Remove IDs that will get replaced
            seen = set(range(starting_id, starting_id + total_image))
            for img in json.load(f):    # Keep only IDs not being re-generated
                if img["ID"] not in seen:
                    seen.add(img["ID"])
                    prev_batches.append(img)

    else:
        prev_batches = []

    ## Generate folders and names list from layers available in traits
    for i, l in enumerate(traits.layers):
        l["type"] = "filenames" if "filenames" in l else "rgba"
        l["names"] = list(l[l["type"]].keys())
        if traits.layers[0]["layer_name"].lower() != "background color":
            n = i + 1
        else:
            n = i
        l["path"] = os.path.join(SOURCE_FILES, f"layer{n:02}")

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
        print(f"Layer {i:02}: {l['count']}")

    ## Store trait counts to json
    with open(STATS_FILENAME, 'w') as outfile:
        gen_stats = {l["layer_name"]: l["count"] for l in traits.layers}
        gen_stats['seed'] = SEED
        json.dump(gen_stats, outfile, indent=4)

    #### Generate Images
    composites = asyncio.run(generate(this_batch))
    print(f"Generated {len(this_batch)} images!")

    #### Generate Metadata for all Traits

    with open(METADATA_FILE_NAME, 'w') as outfile:
        json.dump(all_images, outfile, indent=4)

    print("Look in " + METADATA_FILE_NAME + " for an overview of all generated IDs and traits.")

if __name__ == "__main__":
    main()