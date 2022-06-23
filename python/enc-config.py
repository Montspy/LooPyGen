#!/usr/bin/env python3

import os
from shutil import copy2
import argparse
import json
from glob import glob

from utils import Struct, generate_paths, save_config_json

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
    args = parse_args()

    # Generate paths and make directories
    paths = generate_paths()

    # set correct path for the type of config
    if args.mint:
        enc_path = paths.config
    elif args.transfer:
        enc_path = paths.transfer_config

    # check if a json path is provided
    if not args.json:
        dec_path = enc_path
    else:
        dec_path = args.json

    # check if a secret is provided
    if args.secret:
        phrase = args.secret

    else:
        from getpass import getpass
        from base64 import b64encode

        if args.mint:
            address = input("Minter Address: ")
            l2_pk = getpass("Layer 2 Private Key: ")
            phrase = b64encode(getpass("Passphrase: ").encode("utf-8"))
            royalty = input("Default Royalty (0-10): ")
            nft_type = input("NFT Type [0 = ERC1155, 1 = ERC721]: ")
            token = input("Fee Token [0 = ETH, 1 = LRC]: ")

            config_json = {
                "minter": address,
                "private_key": l2_pk,
                "royalty_percentage": royalty,
                "nft_type": nft_type,
                "fee_token": token
            }

        if args.transfer:
            address = input("From Address: ")
            l1_pk = getpass("Layer 1 Private Key: ")
            l2_pk = getpass("Layer 2 Private Key: ")
            phrase = b64encode(getpass("Passphrase: ").encode("utf-8"))
            token = input("Fee Token [0 = ETH, 1 = LRC]: ")

            config_json = {
                "sender": address,
                "private_key": l2_pk,
                "private_key_mm": l1_pk,
                "fee_token": token
            }

        # save config to file
        with open(dec_path, 'w') as outfile:
            json.dump(config_json, outfile, indent=4)

    # encrypt the json and save the file
    save_config_json(dec_path, enc_path, phrase)

if __name__ == '__main__':
    main()