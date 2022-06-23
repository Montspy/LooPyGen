#!/usr/bin/env python3

import os
from shutil import copy2
import argparse
import json
import sys
from glob import glob

from utils import generate_paths, save_config_json, print_exception_secret

def input_while(prompt: str, validate: callable, is_abort: callable, retry_msg: str, hidden: bool = False):
    from getpass import getpass
    while True:
        value, valid, result = None, False, None
        try:
            value = input(prompt) if not hidden else getpass(prompt)
            if is_abort(value):
                sys.exit("User aborted")
            valid, result = validate(value)
            if valid:
                return result
        except Exception as err:
            pass
        print(retry_msg.format(value))

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
            try:
                l2_pk = getpass("Layer 2 Private Key: ")
            except Exception as err:
                print_exception_secret()
                sys.exit(f"Unable to get Layer 2 Private Key")
            try:
                phrase = b64encode(getpass("Passphrase: ").encode("utf-8"))
            except Exception as err:
                print_exception_secret()
                sys.exit(f"Unable to encode passphrase")

            royalty = input_while("Default Royalty (0-10): ", lambda x:  (int(x) >= 0 and int(x) <= 10, int(x)), lambda x: x == "", "Invalid Royalty percentage: '{}'")
            nft_type = input_while("NFT Type [0 = ERC1155, 1 = ERC721]: ", lambda x:  (int(x) in [0,1], int(x)), lambda x: x == "", "Invalid NFT Type type: '{}'")
            token = input_while("Fee Token [0 = ETH, 1 = LRC]: ", lambda x:  (int(x) in [0,1], int(x)), lambda x: x == "", "Invalid Fee Token: '{}'")

            config_json = {
                "minter": address,
                "private_key": l2_pk,
                "royalty_percentage": royalty,
                "nft_type": nft_type,
                "fee_token": token
            }

        if args.transfer:
            address = input("From Address: ")
            try:
                l1_pk = getpass("Layer 1 Private Key: ")
                l2_pk = getpass("Layer 2 Private Key: ")
            except Exception as err:
                print_exception_secret()
                sys.exit(f"Unable to get Layer 1/2 Private Keys")
            try:
                phrase = b64encode(getpass("Passphrase: ").encode("utf-8"))
            except Exception as err:
                print_exception_secret()
                sys.exit(f"Unable to encode passphrase")

            token = input_while("Fee Token [0 = ETH, 1 = LRC]: ", lambda x:  (int(x) in [0,1], int(x)), lambda x: x == "", "Invalid Fee Token: '{}'")

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