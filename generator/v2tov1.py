#!/usr/bin/env python3

import os
from pprint import pprint
from shutil import copy2
import argparse
import json
from glob import glob

import utils

TO_VERSION = None
FROM_VERSION ="v2.0.0"

def parse_args():
    # check for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help=FROM_VERSION + ' JSON file to convert to v1.0.0', type=str, required=True)

    return parser.parse_args()

def main():
    # check for command line arguments
    args = parse_args()

    assert os.path.exists(args.file), f"File not found: {args.file}"

    with open(args.file, 'r') as f:
        in_json = utils.Struct(json.load(f))

    assert in_json.version == FROM_VERSION, f"Input file version {in_json.version or 'v1.0.0'} is not supported"

    in_collection = in_json.collection

    out_json = {
        "collection_name": in_collection["name"],
        "collection_lower": in_collection["lower"],
        "description": in_collection["description"],
        "artist_name": False,
        "thumbnails": "thumbnails" in in_collection["options"],
        "animation": "animation" in in_collection["options"],
        # "animation_format": ".gif",
        "royalty_percentage": in_collection["royalty"]["percentage"],
        "trait_count": len(in_collection["layers"]),
        "background_color": False,
        # "royalty_address": "0x0000000000000000000000000000000dead",
        # "seed": "cats",
        "image_layers": [
        ],
        # "thumbnail_size": [
        #     200,
        #     200
        # ]
    }

    # Options
    if len(in_collection["artists"]) > 0 and in_collection["artists"][0]:
        out_json["artist_name"] = in_collection["artists"][0]

    if "address" in in_collection["royalty"] and in_collection["royalty"]["address"]:
        out_json["royalty_address"] = in_collection["royalty"]["address"]

    if "seed" in in_collection["options"] and in_collection["options"]["seed"]:
        out_json["seed"] = in_collection["options"]["seed"]
    
    if out_json["thumbnails"]:
        out_json["thumbnails_size"] = [
            in_collection["options"]["thumbnails"]["width"]
        ]
        if "height" in in_collection["options"]["thumbnails"]: # Handle optional thumbnail height
            out_json["thumbnails_size"].append(in_collection["options"]["thumbnails"]["height"])
    
    if out_json["animation"]:
        out_json["animation_format"] = in_collection["options"]["animation"]["format"]

    # Image layers
    for layer_name, traits in in_collection["layers"].items():
        traits_cnt = len(traits)
        trait_names = []
        filenames = {}
        weights = []

        for trait in traits:
            trait_names.append(trait["name"])
            filenames[trait["name"]] = trait["filename"]
            weights.append(trait["weight"])

        out_json["image_layers"].append({
            "variations": traits_cnt,
            "layer_name": layer_name,
            "filenames": filenames,
            "weights": weights
        })
    
    out_json_name = args.file
    copy2(args.file, args.file + ".bak")
    # Uncomment to keep original file for debug
    out_json_name = os.path.splitext(args.file)[0] + "_" + (TO_VERSION or 'v1.0.0') + ".json"
    with open(out_json_name, 'w+') as f:
        json.dump(out_json, f, indent=4)
    print(f"JSON file converted to {TO_VERSION or 'v1.0.0'}: {out_json_name}")

if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print("ERROR:", e)
