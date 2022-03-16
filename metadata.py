from copy import deepcopy
import json
import argparse
from os import path, getenv, makedirs
from pprint import pprint
from dotenv import load_dotenv
import traits
import shutil

# Paths generation
COLLECTION_LOWER = traits.COLLECTION_NAME.replace(" ", "_").lower()
COLLECTION_PATH = path.join("./generated", COLLECTION_LOWER)
DATA_PATH = path.join(COLLECTION_PATH, "metadata")
IMAGE_PATH = path.join(COLLECTION_PATH, "images")

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

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cid", nargs=1, help="Specify starting ID for images", type=str)
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

    # Set the CID and IPFS URL
    if args.cid:
        cid = args.cid[0]
    else:
        cid = getenv("IMAGES_CID")

    images_base_url = "ipfs://" + cid + "/"

    # Make paths if they don't exist
    if not path.exists(DATA_PATH):
        makedirs(DATA_PATH)

    #### Generate Metadata for each Image

    with open(METADATA_FILE_NAME) as f:
        all_images = json.load(f)

    # Changes this IMAGES_BASE_URL to yours
    for image in all_images:
        token_id = image['ID']

        if getenv("COLLECTION_DESCRIPTION") is None:
            DESCRIPTION = traits.COLLECTION_NAME + " #" + str(token_id)
        else:
            DESCRIPTION = getenv("COLLECTION_DESCRIPTION")

        image.pop("ID", None)   # Remove ID to get properties only

        token = {
            "name": f"{traits.COLLECTION_NAME} #{token_id:03}",
            "image": path.join(images_base_url, f"{COLLECTION_LOWER}_{token_id:03}.png"),
            "animation_url": path.join(images_base_url, f"{COLLECTION_LOWER}_{token_id:03}.png"),   # TODO: replace with pre-calc'd CID of file directly
            "description": DESCRIPTION,
            "royalty_percentage": getenv("ROYALTY_PERCENTAGE"),
            "tokenId": token_id,
            "artist": getenv("ARTIST_NAME"),
            "minter": getenv("MINTER"),
            "attributes": properties_to_attributes(image),
            "properties": image
        }

        with open(path.join(DATA_PATH, f"{COLLECTION_LOWER}_{token_id:03}.json"), 'w') as outfile:
            json.dump(token, outfile, indent=4)

if __name__ == "__main__":
    main()