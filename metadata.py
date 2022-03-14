import json
import argparse
from os import path, getenv, makedirs
from dotenv import load_dotenv
from traits import names
import shutil

load_dotenv()

# check for command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--clear", help="Empty the generated directory", action="store_true")
parser.add_argument("--cid", nargs=1, help="Specify starting ID for images", type=int)
args = parser.parse_args()

dataPath = "./metadata"
genPath = dataPath + "/generated"

# Set starting ID
if args.cid:
    cid = args.cid[0]
else:
    cid = getenv("IMAGES_CID")

# Remove directories if asked to
if args.clear:
    if path.exists(genPath):
        shutil.rmtree(genPath)
    if path.exists(dataPath):
        shutil.rmtree(dataPath)

# Make paths if they don't exist
if not path.exists(genPath):
    makedirs(genPath)
if not path.exists(dataPath):
    makedirs(dataPath)


#### Generate Metadata for each Image

f = open(dataPath + '/all-traits.json',)
data = json.load(f)

# Changes this IMAGES_BASE_URL to yours
IMAGES_BASE_URL = "ipfs://" + cid + "/"
COLLECTION_LOWER = names["collection"].replace(" ", "_").lower()

def getAttribute(key, value):
    return {
        "trait_type": key,
        "value": value
    }

for i in data:
    token_id = i['tokenId']
    token = {
        "name": names["collection"] + ' #' + str(token_id),
        "image": IMAGES_BASE_URL + COLLECTION_LOWER + "_" + str(token_id) + '.png',
        "animation_url": IMAGES_BASE_URL + COLLECTION_LOWER + "_" + str(token_id) + '.png',
        "royalty_percentage": getenv("ROYALTY_PERCENTAGE"),
        "tokenId": token_id,
        "artist": getenv("ARTIST_NAME"),
        "minter": getenv("MINTER"),
        "attributes": [],
        "properties": {}
    }

    # set the attributes
    token["attributes"].append(getAttribute(names["trait01"], i[names["trait01"]]))
    token["attributes"].append(getAttribute(names["trait02"], i[names["trait02"]]))
    token["attributes"].append(getAttribute(names["trait03"], i[names["trait03"]]))
    token["attributes"].append(getAttribute(names["trait04"], i[names["trait04"]]))
    token["attributes"].append(getAttribute(names["trait05"], i[names["trait05"]]))
    token["attributes"].append(getAttribute(names["trait06"], i[names["trait06"]]))
    token["attributes"].append(getAttribute(names["trait07"], i[names["trait07"]]))

    # set the properties
    token["properties"][names["trait01"]] = i[names["trait01"]]
    token["properties"][names["trait02"]] = i[names["trait02"]]
    token["properties"][names["trait03"]] = i[names["trait03"]]
    token["properties"][names["trait04"]] = i[names["trait04"]]
    token["properties"][names["trait05"]] = i[names["trait05"]]
    token["properties"][names["trait06"]] = i[names["trait06"]]
    token["properties"][names["trait07"]] = i[names["trait07"]]

    with open(genPath + "/" + COLLECTION_LOWER + "_" + str(token_id) + ".json", 'w') as outfile:
        json.dump(token, outfile, indent=4)

f.close()