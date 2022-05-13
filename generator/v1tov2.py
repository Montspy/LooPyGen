#!/usr/bin/env python3

import os
from pprint import pprint
from shutil import copy2
import argparse
import json
from glob import glob

import utils

TO_VERSION = "v2.0.0"
FROM_VERSION = None # aka v1.0.0

def parse_args():
    # check for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help='v1.0.0 JSON file to convert to ' + TO_VERSION, type=str, required=True)

    return parser.parse_args()

def main():
    # check for command line arguments
    args = parse_args()

    assert os.path.exists(args.file), f"File not found: {args.file}"

    with open(args.file, 'r') as f:
        in_json = utils.Struct(json.load(f))

    assert in_json.version == FROM_VERSION, f"Input file version {in_json.version or 'v1.0.0'} is not supported"

    out_collection = {
        "name": in_json.collection_name,
        "lower": in_json.collection_lower,
        "description": in_json.description,
        "artists": [
            in_json.artist_name or ""
        ],
        "royalty": {
            "address": in_json.royalty_address or "",
            "percentage": in_json.royalty_percentage
        },
        "options": {
            # seed
            # thumbnails
            # animation
        },
        "layers": {}
    }

    pprint(out_collection)

    # Options
    if in_json.seed:
        out_collection["options"]["seed"] = in_json.seed
    
    if in_json.thumbnails:
        out_collection["options"]["thumbnails"] = {
            "width": in_json.thumbnail_size[0]
        }
        if len(in_json.thumbnail_size) > 1: # Handle optional thumbnail height
            out_collection["options"]["thumbnails"]["height"] = in_json.thumbnail_size[1]
    
    if in_json.animation:
        out_collection["options"]["animation"] = {}
        out_collection["options"]["animation"]["format"] = in_json.animation_format

    if in_json.background_color:
        print("Support for background color has been dropped")

    # Image layers
    for layer in in_json.image_layers:
        layer_name = layer["layer_name"]
        traits = layer["filenames"].keys()
        filenames = layer["filenames"].values()
        weights = layer["weights"]

        out_collection["layers"][layer_name] = [] # Initialize trait list for layer
        for name, filename, weight in zip(traits, filenames, weights):  # Add each trait to the list
            out_collection["layers"][layer_name].append({
                "name": name,
                "filename": filename,
                "weight": weight
            })

    out_json = {
        "version": TO_VERSION,
        "collection": out_collection
    }
    
    out_json_name = args.file
    copy2(args.file, args.file + ".bak")
    # Uncomment to keep original file for debug
    out_json_name = os.path.splitext(args.file)[0] + "_" + TO_VERSION + ".json"
    with open(out_json_name, 'w+') as f:
        json.dump(out_json, f, indent=4)
    print(f"JSON file converted to {TO_VERSION}: {out_json_name}")

if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print("ERROR:", e)
