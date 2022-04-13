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

import utils

# Image generation class
class ImageGenerator(object):
    seed: str               # Randomness seed
    prev_batches: list      # Pre-existing images
    this_batch: list        # New images
    dup_cnt_limit: int      # Maximum number of tries to create a unique image

    layers: list

    def __init__(self, layers: list, seed: str, prev_batches: list, dup_cnt_limit: int):
        self.layers = layers
        self.seed = seed
        # Keep trait properties only, to make comparison to new image easier
        self.prev_batches = []
        for image in prev_batches:
            layer_names = [l["layer_name"] for l in self.layers]
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
        for l in self.layers:
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
    
    # Sort the list by ID
    def sortID(e):
        return e["ID"]

# Returns true if all images are unique
def all_images_unique(all_images):
    # Remove IDs to make comparison to new image easier
    images = deepcopy(all_images)
    for img in images:
        img.pop("ID", None)
    seen = list()
    return not any(i in seen or seen.append(i) for i in images)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--count", help="Total number of images to generate", type=int, required=True)
    parser.add_argument("-e", "--empty", help="Empty the generated directory", action="store_true")
    parser.add_argument("--name", help="Collection name (lowercase, ascii only)", type=str)
    parser.add_argument("--id", help="Specify starting ID for images", type=int, default=1)
    parser.add_argument("--seed", help="Specify the randomness seed", type=str, default=None)
    parser.add_argument("-s", "--single", help="Only generate a single image at a time", action="store_true")
    args = parser.parse_args()
    return args

def make_directories(paths: utils.Struct, traits: utils.Struct, empty: bool):
    if empty:
        if os.path.exists(paths.images):
            shutil.rmtree(paths.images)
        if os.path.exists(paths.thumbnails):
            shutil.rmtree(paths.thumbnails)
        if os.path.exists(paths.all_traits):
            os.remove(paths.all_traits)
        if os.path.exists(paths.gen_stats):
            os.remove(paths.gen_stats)

    # Make paths if they don't exist
    if not os.path.exists(paths.images):
        os.makedirs(paths.images)
    if not os.path.exists(paths.metadata):
        os.makedirs(paths.metadata)
    if not os.path.exists(paths.thumbnails) and traits.thumbnails:
        os.makedirs(paths.thumbnails)

# Image builder functions
async def build_and_save_image(paths: utils.Struct, traits: utils.Struct, item: dict, task_id: int):
    with ImageBuilder(animated_format=traits.animated_format) as img_builder:
        for l in traits.image_layers:
            layer_pretty_name = item[l["layer_name"]]
        
            if l["type"] == "filenames":
                layer_file = os.path.join(l["path"], l["filenames"][layer_pretty_name])
                img_builder.overlay_image(layer_file)
            elif l["type"] == "rgba":
                if not "size" in l:
                    sys.exit(f"Missing image size for {l['layer_name']}")
                img_builder.overlay_image(tuple(l["rgba"][layer_pretty_name]), size=l["size"])

        # Composite all layers on top of each others
        composite = await img_builder.build()
        if traits.thumbnails:
            thumbnail = await img_builder.thumbnail(size=traits.thumbnail_size)

        if composite.type == ImageType.STATIC:
            file_path = os.path.join(paths.images, f"{traits.collection_lower}_{item['ID']:03}.png")
            composite.img.save(file_path)
            if traits.thumbnails:
                thumb_path = os.path.join(paths.thumbnails, f"{traits.collection_lower}_{item['ID']:03}_thumb.png")
                thumbnail.img.save(thumb_path)
        elif composite.type == ImageType.ANIMATED:
            ext = os.path.splitext(composite.fp)[1]
            file_path = os.path.join(paths.images, f"{traits.collection_lower}_{item['ID']:03}{ext}")
            shutil.copy2(composite.fp, file_path)
            if traits.thumbnails:
                ext = os.path.splitext(thumbnail.fp)[1]
                thumb_path = os.path.join(paths.thumbnails, f"{traits.collection_lower}_{item['ID']:03}_thumb{ext}")
                shutil.copy2(thumbnail.fp, thumb_path)

        # print(f"Generated #{item['ID']:03}: {file_path}")
    return task_id

async def generate(paths: utils.Struct, traits: utils.Struct, batch: list, single: bool): 
    if single:
        semaphore = asyncio.Semaphore(1)   # Limit to 16 images building at once
    else:
        semaphore = asyncio.Semaphore(16)   # Limit to 16 images building at once
    async def sem_task(task):
        async with semaphore:
            return await task

    task_ids = [item['ID'] for item in batch]
    results = []

    with yaspin.kbi_safe_yaspin().line as spinner:
        if len(task_ids) > 10:
            spinner.text = f"Generating {' '.join( [f'#{id:03}' for id in task_ids[:10]] )} (+ {len(task_ids) - 10} others)"
        else:
            spinner.text = f"Generating {' '.join( [f'#{id:03}' for id in task_ids] )}"
        for task in asyncio.as_completed( [sem_task(build_and_save_image(paths, traits, item, item['ID'])) for item in batch] ):
            result = await task
            results.append(result)
            task_ids.remove(result)
            if len(task_ids) > 10:
                spinner.text = f"Generating {' '.join( [f'#{id:03}' for id in task_ids[:10]] )} (+ {len(task_ids) - 10} others)"
            else:
                spinner.text = f"Generating {' '.join( [f'#{id:03}' for id in task_ids] )}"

    return results

def main():
    # load .env file into memory
    load_dotenv()

    # check for command line arguments
    args = parse_args()

    # Load traits.json
    traits = utils.load_traits(args.name)

    # Generate paths
    paths = utils.generate_paths(traits)

    # Remove directories if asked to
    make_directories(paths, traits, args.empty)

    # Define amount of images to generate
    total_image = args.count

    if total_image > utils.get_variation_cnt(traits.image_layers):
        sys.exit(f"count ({total_image}) cannot be greater than the number of variations ({utils.get_variation_cnt(traits.image_layers)})")

    # set the SOURCE_FILES if it's not specified in .env
    if os.getenv("SOURCE_FILES") is not None and os.getenv("SOURCE_FILES") != "":
        paths.source = os.getenv("SOURCE_FILES")

    # Set starting ID
    starting_id = args.id
    print("Starting at ID: " + str(starting_id))

    # Randomness seed in order of priority: traits.json, .env, random seed
    if args.seed is None and traits.seed is not None and traits.seed != "":
        args.seed = str(traits.seed)
    if args.seed is None and os.getenv("SEED") is not None and os.getenv("SEED") != "":
        args.seed = str(os.getenv("SEED"))
    if args.seed is None:
        timestamp = time.time_ns().to_bytes(16, byteorder='big')
        args.seed = b64encode(timestamp).decode("utf-8") # Encode timestamp to a base64 string
    print(f"Using randomness seed: {args.seed}")

    ## Generate Traits
    # Check if all-traits.json exists
    if os.path.exists(paths.all_traits):
        print("Previous batches exist, pulling in their data.")
        with open(paths.all_traits, 'r') as f:
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
    first_layer = 0 if traits.background_color else 1
    for i, l in enumerate(traits.image_layers):
        l["type"] = "filenames" if "filenames" in l else "rgba"
        l["names"] = list(l[l["type"]].keys())
        
        l["path"] = os.path.join(paths.source, f"layer{(first_layer + i):02}")

    # Generate the unique combinations based on layer weightings
    img_gen = ImageGenerator(layers=traits.image_layers, seed=args.seed, prev_batches=prev_batches, dup_cnt_limit=utils.get_variation_cnt(traits.image_layers))
    this_batch = img_gen.generate_images(starting_id=starting_id, image_cnt=total_image)

    all_images = prev_batches
    all_images.extend(this_batch)

    all_images.sort(key=ImageGenerator.sortID)

    # Double check that all images are unique to the whole collection
    if not all_images_unique(all_images):
        print(f"Some images are not unique, aborting")
        sys.exit(0)

    # Get Trait Counts
    print("How many of each trait exist?")

    for l in traits.image_layers:
        l["count"] = {item: 0 for item in l["names"]}

    for image in all_images:
        n = 1
        for l in traits.image_layers:
            item = image[l["layer_name"]]
            l["count"][item] += 1

    for i, l in enumerate(traits.image_layers):
        print(f"Layer {i:02}: {l['count']}")

    ## Store trait counts to json
    with open(paths.gen_stats, 'w') as outfile:
        gen_stats = {l["layer_name"]: l["count"] for l in traits.image_layers}
        gen_stats['seed'] = args.seed
        json.dump(gen_stats, outfile, indent=4)

    #### Generate Metadata for all Traits
    with open(paths.all_traits, 'w') as outfile:
        json.dump(all_images, outfile, indent=4)

    #### Generate Images
    composites = asyncio.run(generate(paths, traits, this_batch, args.single))
    print(f"Generated {len(this_batch)} images!")

    print("Look in " + paths.all_traits + " for an overview of all generated IDs and traits.")

if __name__ == "__main__":
    main()