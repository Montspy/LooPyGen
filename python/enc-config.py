#!/usr/bin/env python3

import os
from shutil import copy2
import argparse
import json
import sys
from glob import glob

from utils import generate_paths, save_config_json, print_exception_secret

# Parse CLI arguments
def parse_args():
    # check for command line arguments
    parser = argparse.ArgumentParser()
    input_grp = parser.add_mutually_exclusive_group(required=True)
    input_grp.add_argument('--mint', help='Encrypt minting config', action='store_true')
    input_grp.add_argument('--transfer', help='Encrypt transfer config', action='store_true')
    parser.add_argument('--json', help='Path to JSON config to encrypt', type=str)
    parser.add_argument('--secret', help='Base64 encoded secret to encrypt with', type=str)

    return parser.parse_args()

def main():
    # check for command line arguments
    try:
        args = parse_args()
    except Exception as err:
        print_exception_secret()
        sys.exit(f"Unable to parse arguments")

    # Generate paths and make directories
    paths = generate_paths()

    # set correct path for the type of config
    if args.mint:
        enc_path = paths.config
    elif args.transfer:
        enc_path = paths.transfer_config

    # check if a secret is provided
    if not args.secret:
        sys.exit("Error: secret not provided")

    # check if a json path is provided
    if not args.json:
        dec_path = enc_path
    else:
        dec_path = args.json

    # encrypt the json and save the file
    save_config_json(dec_path, enc_path, args.secret)

if __name__ == '__main__':
    main()