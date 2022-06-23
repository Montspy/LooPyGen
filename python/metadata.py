

import sys
import os

from minter import get_account_info, retry_async
from LoopringMintService import LoopringMintService
from utils import Struct

from shutil import copy2
import json
import argparse
import shutil
import asyncio
import glob

import utils

def properties_to_attributes(properties: dict):
    attributes = []
    for key, value in properties.items():
        attributes.append({
            "trait_type": key,
            "value": value
        })
    return attributes

# CID pre-calc helper functions
async def get_file_cid(filepath: str, version: int=0, id: int=None):
    # Find matching file
    matching_file = glob.glob(filepath)
    if len(matching_file) == 0:
        if id is None:
            return None
        return None, id
    matching_file = list(filter(lambda f: len(os.path.splitext(f)[-1]) <= 5, matching_file))  # Remove files with extensions longer than 5 (e.g. '.png:ZoneIdentifier')
    matching_file = sorted(matching_file, key=os.path.getmtime)[-1] # Sort by modified date, keep latest modified
    if not os.path.exists(matching_file):
        if id is None:
            return None
        return None, id

    proc = await asyncio.create_subprocess_shell(
        f"cid --cid-version={version} {matching_file}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode > 0:
        raise RuntimeError(f"Could not get CIDv{version} of file '{filepath}':\n\t{stderr.decode()}")

    if id is None:
        return stdout.decode().strip()
    return stdout.decode().strip(), id

def make_image_path(paths: utils.Struct, collection_lower: str, image: dict, thumbnail: bool):
    if thumbnail:
        return os.path.join(paths.thumbnails, f"{collection_lower}_{image['ID']:03}_thumb.*")
    else:
        return os.path.join(paths.images, f"{collection_lower}_{image['ID']:03}.*")

async def get_image_cids(paths: utils.Struct, collection_lower: str, images: list, thumbnail: bool=False):
    semaphore = asyncio.Semaphore(16)
    async def sem_task(task):
        async with semaphore:
            return await task

    task_completed_count = 0
    results = [None] * len(images)
    operation = "Calculating thumbnail CIDs" if thumbnail else "Calculating CIDs"

    tasks = [ sem_task(
        get_file_cid(
            make_image_path(paths, collection_lower, image, thumbnail),
            id=id
        )
    ) for id, image in enumerate(images) ]

    for task in asyncio.as_completed(tasks):
        result, id = await task
        results[id] = result
        task_completed_count += 1
        utils.set_progress_for_ui(operation, task_completed_count, len(images))

    return results

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", help="Overwrite the metadata file and all metadata fields", action="store_true")
    parser.add_argument("-e", "--empty", help="Empty the generated directory", action="store_true")
    parser.add_argument("--name", help="Collection name (lowercase, ascii only)", type=str)
    args = parser.parse_args()

    return args

def make_directories(paths: utils.Struct, empty: bool):
    # Remove directories if asked to
    if empty:
        if os.path.exists(paths.metadata):
            shutil.rmtree(paths.metadata)

    # Make paths if they don't exist
    if not os.path.exists(paths.metadata):
        os.makedirs(paths.metadata)

def main():
    # check for command line arguments
    args = parse_args()

    # Load traits.json
    traits = utils.load_traits(args.name)

    # Generate paths
    paths = utils.generate_paths(traits)

    # Make directories
    make_directories(paths, args.empty)

    # Resolve royalty address
    cfg = Struct()
    cfg.royalty = traits.royalty_address
    if cfg.royalty:
        cfg.royaltyAccount, cfg.royaltyAddress = asyncio.run(retry_async(get_account_info, cfg.royalty, retries=3))
        assert cfg.royaltyAddress and cfg.royaltyAccount, f"Invalid royalty account: {cfg.royalty} as {cfg.royaltyAddress} (account ID {cfg.royaltyAddress})"

    with open(paths.all_traits) as f:
        all_images = json.load(f)

    # Calculate image CIDs
    all_images_cids = asyncio.run(get_image_cids(paths, traits.collection_lower, all_images))
    all_metadata_cids = []

    # Calculate thumbnail CIDs (if they all exist)
    all_thumbs_cids = asyncio.run(get_image_cids(paths, traits.collection_lower, all_images, thumbnail=True))
    if any( [c is None for c in all_thumbs_cids] ):
        if all( [c is None for c in all_thumbs_cids] ):
            print("No thumbnail found, using full resolution image")
        else:
            print(f"Some thumbnail file(s) missing, using full resolution image")
        all_thumbs_cids = all_images_cids

    utils.set_progress_for_ui("Writing metadata", 0, len(all_images))
    for i, (cid, thumb_cid, image) in enumerate(zip(all_images_cids, all_thumbs_cids, all_images)):
        utils.set_progress_for_ui("Writing metadata", i + 1, len(all_images))
        token_id = image['ID']
        json_path = os.path.join(paths.metadata, f"{traits.collection_lower}_{token_id:03}.json")

        token = {}
        from_scratch = True    # Is true if 'overwrite' flag set or metadata json file is invalid
        if not args.overwrite and os.path.exists(json_path):
            try:
                # Read all the info from file
                with open(json_path, 'r') as infile:
                    token = json.load(infile)
                    from_scratch = False
                print(f"Updating CIDs for #{token_id:03} in {json_path}")
            except json.JSONDecodeError as err:
                print(f"Invalid metadata for #{token_id:03} in {json_path}: ")
                print("  " + str(err))

        if from_scratch:    # metadata json doesn't exist or 'overwrite' flag set
            print(f"Generating new metadata for #{token_id:03} to {json_path}")
            if os.path.exists(json_path):
                copy2(json_path, json_path + ".bak")
                print(f"  Saving backup as {json_path + '.bak'}: ")

            # Get trait properties only (remove ID, CID, etc...)
            layer_names = [l["layer_name"] for l in traits.image_layers]
            properties = {name: image[name] for name in layer_names}

            # Create all new info
            token = {
                "name": f"{traits.collection_name} #{token_id:03}",
                "description": traits.description,
                "royalty_percentage": int(traits.royalty_percentage),
                "id": token_id,
                "attributes": properties_to_attributes(properties),
                "properties": properties
            }
            if cfg.royaltyAddress is not None and cfg.royaltyAddress != "":
                token["royalty_address"] = cfg.royaltyAddress
            if traits.artist_name is not None and traits.artist_name != "":
                token["artist"] = traits.artist_name

        # Update CID fields
        token["image"] = os.path.join("ipfs://", thumb_cid)
        token["animation_url"] = os.path.join("ipfs://", cid)

        with open(json_path, 'w') as outfile:
            json.dump(token, outfile, indent=4)

        # Calculate metadata CIDs
        all_metadata_cids.append({"ID": token_id, "CID": asyncio.run(get_file_cid(json_path))})

    metadata_cids_path = paths.metadata_cids
    with open(metadata_cids_path, 'w') as outfile:
        json.dump(all_metadata_cids, outfile, indent=4)

if __name__ == "__main__":
    main()