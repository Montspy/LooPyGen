import json
import argparse
from os import path, getenv, makedirs
from dotenv import load_dotenv
import traits
import shutil

load_dotenv()

# check for command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--cid", nargs=1, help="Specify starting ID for images", type=int)
parser.add_argument("-e", "--empty", help="Empty the generated directory", action="store_true")
args = parser.parse_args()

COLLECTION_LOWER = traits.COLLECTION_NAME.replace(" ", "_").lower()
IMAGES_BASE_URL = "ipfs://" + cid + "/"

dataPath = "./metadata"
genPath = dataPath + "/" + COLLECTION_LOWER + "/generated"

# Remove directories if asked to
if args.empty:
    if os.path.exists(genPath):
        shutil.rmtree(genPath)

# Set starting ID
if args.cid:
    cid = args.cid[0]
else:
    cid = getenv("IMAGES_CID")

# Make paths if they don't exist
if not path.exists(genPath):
    makedirs(genPath)
if not path.exists(dataPath):
    makedirs(dataPath)

#### Generate Metadata for each Image

f = open(dataPath + '/all-traits.json')
data = json.load(f)

# Changes this IMAGES_BASE_URL to yours

def getAttribute(key, value):
    return {
        "trait_type": key,
        "value": value
    }

for i in data:
    token_id = i['ID']

    if getenv("COLLECTION_DESCRIPTION") is None:
        DESCRIPTION = traits.COLLECTION_NAME + " #" + str(token_id)
    else:
        DESCRIPTION = getenv("COLLECTION_DESCRIPTION")

    token = {
        "name": traits.COLLECTION_NAME + ' #' + str(token_id),
        "image": IMAGES_BASE_URL + COLLECTION_LOWER + "_" + str(token_id) + '.png',
        "animation_url": IMAGES_BASE_URL + COLLECTION_LOWER + "_" + str(token_id) + '.png',
        "description": DESCRIPTION,
        "royalty_percentage": getenv("ROYALTY_PERCENTAGE"),
        "tokenId": token_id,
        "artist": getenv("ARTIST_NAME"),
        "minter": getenv("MINTER"),
        "attributes": [],
        "properties": {}
    }

    # set the attributes
    n = 1
    for l in traits.layers:
        token["attributes"].append(getAttribute(traits.layers[n]["layer_name"], i[traits.layers[n]["layer_name"]]))
        n = n + 1

    # set the properties
    n = 1
    for l in traits.layers:
        token["properties"][traits.layers[n]["layer_name"]] = i[traits.layers[n]["layer_name"]]
        n = n + 1

    with open(genPath + "/" + COLLECTION_LOWER + "_" + str(token_id) + ".json", 'w') as outfile:
        json.dump(token, outfile, indent=4)

f.close()