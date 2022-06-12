#!/usr/bin/env python3

from utils import Router, SemVerFilter, FromToFilter, Struct
from typing import Callable
from shutil import copy2
import argparse
import json
import os


# Modify 'TRAITS_VERSION' to match the latest traits.json version. Conversions will default to 'TRAITS_VERSION' unless specified with --version
TRAITS_VERSION = 'v2.0.0'

def parse_args():
    # check for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', help=f"traits JSON file to convert to {TRAITS_VERSION}", type=str, required=True)
    parser.add_argument('--version', help=f"Version to convert to (semver), default: {TRAITS_VERSION}", type=str, default=TRAITS_VERSION)
    parser.add_argument('--output', help=f"Output file location of converted traits JSON", type=str)

    args = parser.parse_args()

    # Check input file exists
    assert os.path.exists(args.file), f"File not found: {args.file}"

    # Check valid version provided
    assert SemVerFilter(args.version).get_priority() == 0, f"Invalid semver version provided {args.version}"
    
    return args

def v1tov2(in_json: dict) -> dict:
    FROM_VERSION = 'v1.0.0'
    TO_VERSION = 'v2.0.0'

    in_json = Struct(in_json)

    assert in_json.version is None or in_json.version == FROM_VERSION, f"Input file version {in_json.version} is not supported by this converter"

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
    
    return out_json

def v2tov1(in_json: dict) -> dict:
    FROM_VERSION = 'v2.0.0'
    TO_VERSION = None   # v1.0.0 did not have a "version" field

    assert (in_json['version'] is None) or (in_json['version']) == FROM_VERSION, f"Input file version {in_json['version']} is not supported by this converter"

    in_collection = in_json['collection']

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
    
    return out_json

# Add converters below as they are created, use 'x' as a wildcard for major, minor or patch elements
def load_converters() -> Router:
    # The Router maps a pair of semvers (from, to) to a converter
    # Each converter is a function that takes a dict as input (input json), and outputs a dict (converted output json)
    router = Router[FromToFilter, Callable[[dict], dict]]()
    router.add_map(
        FromToFilter(
            SemVerFilter('x.x.x'),
            SemVerFilter('x.x.x')
        ),
        None
    )
    router.add_map(
        FromToFilter(
            SemVerFilter('1.x.x'),
            SemVerFilter('2.0.0')
        ),
        v1tov2
    )
    router.add_map(
        FromToFilter(
            SemVerFilter('2.0.0'),
            SemVerFilter('1.0.0')
        ),
        v2tov1
    )

    return router

def main():
    # check for command line arguments
    args = parse_args()

    router = load_converters()

    # Load input json and read version
    with open(args.file, 'r') as f:
        in_json = json.load(f)
    if 'version' in in_json:
        file_version = in_json['version']
    else:
        file_version = 'v1.0.0' # Assume v1.0.0 if no version found in file
    
    # Find a converter and convert
    converter = router.match_route(
        FromToFilter(
            SemVerFilter(file_version),
            SemVerFilter(args.version)
        )
    )
    assert converter is not None, f"Could not find a converter to convert from {file_version} to {args.version}"

    out_json = converter(in_json)

    # Save the converted file
    if args.output is not None:
        out_json_name = args.output
    else:
        out_json_name = args.file
        # Uncomment to keep original file for debug
        # out_json_name = os.path.splitext(args.file)[0] + "_" + args.version + ".json"
    if os.path.exists(out_json_name):
        copy2(out_json_name, out_json_name + ".bak")
    with open(out_json_name, 'w+') as f:
        json.dump(out_json, f, indent=4)
    print(f"JSON file converted from {file_version} to {args.version}: {out_json_name}")

if __name__ == '__main__':
    try:
        main()
    except AssertionError as e:
        print("ERROR:", e)