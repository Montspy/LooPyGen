from copy import deepcopy
import json
import argparse
from os import path, getenv, makedirs
from shutil import copy2
from pprint import pprint
from dotenv import load_dotenv
import traits
import shutil
import asyncio

# Paths generation
COLLECTION_LOWER = "".join(map(lambda c: c if c.isalnum() else '_', traits.COLLECTION_NAME)).lower()
COLLECTION_PATH = path.join("./generated", COLLECTION_LOWER)
DATA_PATH = path.join(COLLECTION_PATH, "metadata")
IMAGES_PATH = path.join(COLLECTION_PATH, "images")
IMAGES_BASE_URL = "ipfs://"

# specify all-traits.json file
METADATA_FILE_NAME = path.join(COLLECTION_PATH, "all-traits.json")

def properties_to_attributes(properties: dict):
    attributes = []
    for key, value in properties.items():
        attributes.append({
            "trait_type": key,
            "value": value
        })
    return attributes

# CID pre-calc helper functions
async def get_file_cid(path: str, version: int=0):
    proc = await asyncio.create_subprocess_shell(
        f"cid --cid-version={version} {path}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode > 0:
        raise RuntimeError(f"Could not get CIDv{version} of file '{path}':\n\t{stderr.decode()}")
    return stdout.decode().strip()

def make_image_path(image: dict):
    return path.join(IMAGES_PATH, f"{COLLECTION_LOWER}_{image['ID']:03}.png")

async def get_image_cids(images: list):
    return await asyncio.gather(*[get_file_cid(make_image_path(image)) for image in images])

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--empty", help="Empty the generated directory", action="store_true")
    args = parser.parse_args()

    return args

def main():
    load_dotenv()

    # check for command line arguments
    args = parse_args()

    # Remove directories if asked to
    if args.empty:
        if path.exists(DATA_PATH):
            shutil.rmtree(DATA_PATH)

    # Make paths if they don't exist
    if not path.exists(DATA_PATH):
        makedirs(DATA_PATH)

    #### Generate Metadata for each Image

    with open(METADATA_FILE_NAME) as f:
        all_images = json.load(f)

    # Calculate image CIDs
    all_images_cids = asyncio.run(get_image_cids(all_images))
    all_metadata_cids = []

    for cid, image in zip(all_images_cids, all_images):
        token_id = image['ID']
        json_path = path.join(DATA_PATH, f"{COLLECTION_LOWER}_{token_id:03}.json")

        if getenv("COLLECTION_DESCRIPTION") is None:
            DESCRIPTION = traits.COLLECTION_NAME + " #" + str(token_id)
        else:
            DESCRIPTION = getenv("COLLECTION_DESCRIPTION")

       # Get trait properties only (remove ID, CID, etc...)
        layer_names = [l["layer_name"] for l in traits.layers]
        properties = {name: image[name] for name in layer_names}

        token = {
            "name": f"{traits.COLLECTION_NAME} #{token_id:03}",
            "image": path.join(IMAGES_BASE_URL, cid),
            "animation_url": path.join(IMAGES_BASE_URL, cid),
            "description": DESCRIPTION,
            "royalty_percentage": getenv("ROYALTY_PERCENTAGE"),
            "tokenId": token_id,
            "artist": getenv("ARTIST_NAME"),
            "minter": getenv("MINTER"),
            "attributes": properties_to_attributes(properties),
            "properties": properties
        }

        print(f"Generating metadata for #{token_id:03} to {json_path}")

        with open(json_path, 'w') as outfile:
            json.dump(token, outfile, indent=4)

        # Calculate metadata CIDs
        all_metadata_cids.append({"ID": token_id, "CID": asyncio.run(get_file_cid(json_path))})

    metadata_cids_path = path.join(COLLECTION_PATH, "metadata-cids.json")
    minter_cids_path = path.join("./minter", "metadata-cids.json")
    with open(metadata_cids_path, 'w') as outfile:
        json.dump(all_metadata_cids, outfile, indent=4)
    copy2(metadata_cids_path, minter_cids_path)

if __name__ == "__main__":
    main()