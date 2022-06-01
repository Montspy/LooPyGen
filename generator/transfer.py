#!/usr/bin/env python3
import os
import sys

from pprint import pprint
import argparse
import asyncio
import random
import base58
import json

from utils import generate_paths, load_config_json, Struct

from DataClasses import *
from LoopringMintService import LoopringMintService, NFTTransferEddsaSignHelper
from hello_loopring.sdk.sig_utils.ecdsa_utils import EIP712, generateTransferEIP712Hash
from py_eth_sig_utils import utils as sig_utils
from py_eth_sig_utils.signing import v_r_s_to_signature

# Verbose output
VERBOSE = False
def log(*objects, **kwds):
    if VERBOSE:
        print(*objects, **kwds)
def plog(object, **kwds):
    if VERBOSE:
        pprint(object, **kwds)

async def get_account_info(account: str):
    async with LoopringMintService() as lms:
        account = str(account).strip().lower()
        if account[:2] == "0x": # Assuming it's an address formatted as L2 hex-string 
            address = account
            id = await lms.getAccountId(address)
        elif account[-4:] == ".eth":    # Assuming it's an ENS
            address = await lms.resolveENS(account)
            id = await lms.getAccountId(address)
        else:   # Assuming it's an account ID
            id = int(account)
            address = await lms.getAccountAddress(id)
    return id, address

async def retry_async(coro, *args, timeout: float=3, retries: int=3, **kwds):
    for attempts in range(retries):
        try:
            return await asyncio.wait_for(coro(*args, **kwds), timeout=timeout)
        except asyncio.TimeoutError:
            print("Retrying... " + str(attempts))

# Build config dictionnary
async def load_config(args, paths: Struct):
    cfg = Struct()
    secret = Struct()   # Split to avoid leaking keys to console or logs
    loopygen_cfg = load_config_json(paths.transfer_config, args.configpass)
    secret.loopringPrivateKey = loopygen_cfg.private_key
    secret.metamaskPrivateKey = loopygen_cfg.private_key_mm
    cfg.fromAddress           = loopygen_cfg.sender
    cfg.maxFeeTokenId         = int(loopygen_cfg.fee_token)

    cfg.feeSlippage           = 0.5 # Fee limit is estimatedFee * ( 1 + feeSlippage ), default: +50%
    cfg.validUntil            = 1700000000
    cfg.nftFactory            = "0xc852aC7aAe4b0f0a0Deb9e8A391ebA2047d80026"
    cfg.exchange              = "0x0BABA1Ad5bE3a5C0a66E7ac838a129Bf948f1eA4"
    
    # Resolve ENS, get account_id and ETH address
    cfg.fromAccount, cfg.fromAddress = await retry_async(get_account_info, cfg.fromAddress, retries=3)
    assert cfg.fromAddress and cfg.fromAccount, f"Invalid from address: {cfg.fromAddress} (account ID {cfg.fromAccount})"

    assert secret.loopringPrivateKey, "Missing Loopring private key (LOOPRING_PRIVATE_KEY)"
    assert secret.metamaskPrivateKey, "Missing MetaMask private key (L1_PRIVATE_KEY)"
    assert cfg.maxFeeTokenId in range(len(token_decimals)), f"Missing or invalid fee token ID (FEE_TOKEN_ID): {cfg.maxFeeTokenId}"

    if secret.loopringPrivateKey[:2] != "0x":
        secret.loopringPrivateKey = "0x{0:0{1}x}".format(int(secret.loopringPrivateKey), 64)
    secret.loopringPrivateKey = secret.loopringPrivateKey.lower()
    if len(secret.metamaskPrivateKey) == 64 and secret.metamaskPrivateKey[:2] != "0x":
        secret.metamaskPrivateKey = "0x" + secret.metamaskPrivateKey
    secret.metamaskPrivateKey = secret.metamaskPrivateKey.lower()
    
    return cfg, secret

# Parse CLI arguments
def parse_args():
    # check for command line arguments
    parser = argparse.ArgumentParser()
    mode_group_title = parser.add_argument_group(title="Transfer mode")
    mode_group = mode_group_title.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--single", metavar="NFT ID", dest="nftid", help="Provide an NFT ID for one-to-many transfers", type=str)
    mode_group.add_argument("--random", metavar="CONTRACT", dest="random_contract", help="Provide a contract address for many-to-many random transfers", type=str)
    mode_group.add_argument("--randomlist", metavar="LIST", dest="random_list", help="Path to a file of NFT IDs or CIDs for many-to-many random transfers", type=str)
    mode_group.add_argument("--list", metavar="LIST", dest="ordered_list", help="Path to a file of NFT IDs or CIDs for many-to-many ordered transfers", type=str)
    
    to_group_title = parser.add_argument_group(title="Recipients")
    to_group = to_group_title.add_mutually_exclusive_group(required=True)
    to_group.add_argument("--to", help="L2 address (hex string) to transfer to", type=str)
    to_group.add_argument("--tolist", metavar="LIST", help="Path to a file of L2 address (hex string) to transfer to", type=str)

    parser.add_argument("--amount", help="Amount of NFTs to send to each address (only valid with --single)", type=int, default=1)
    parser.add_argument("--test", help="Skips the transfer step", action='store_true')
    parser.add_argument("--noprompt", help="Skip all user prompts", action='store_true')
    parser.add_argument("-V", "--verbose", help="Verbose output", action='store_true')
    parser.add_argument("--fees", help="Estimates the fees and exits", action='store_true')
    parser.add_argument("--php", help=argparse.SUPPRESS, action='store_true')   # Unused. Prevents errors if flag is provided
    parser.add_argument("--configpass", help=argparse.SUPPRESS, type=str)       # Should be base64 encoded

    args = parser.parse_args()

    # Argument validation
    # NFT ID
    if args.nftid:
        assert args.nftid[:2] == "0x" and len(args.nftid) == 66, f"Invalid NFT ID provided for --single ({args.nftid})"
        assert args.amount > 0, f"Invalid argument --amount ({args.amount}), should be > 0"
        args.mode = TransferMode.SINGLE

    # Random contract
    if args.random_contract:
        assert args.random_contract[:2] == "0x" and len(args.random_contract) == 42, f"Invalid Contract address provided for --random ({args.random_contract})"
        assert args.amount == 1, f"Invalid argument --amount ({args.amount}), should be 1 with --random"
        args.mode = TransferMode.RANDOM

    # Random CID list
    if args.random_list:
        assert os.path.exists(args.random_list), f"Invalid path to list of CIDs provided for --randomlist ({args.random_list})"
        assert args.amount == 1, f"Invalid argument --amount ({args.amount}), should be 1 with --randomlist"
        args.mode = TransferMode.RANDOM

    # Ordered CID list
    if args.ordered_list:
        assert os.path.exists(args.ordered_list), f"Invalid path to list of CIDs provided for --list ({args.ordered_list})"
        assert args.amount == 1, f"Invalid argument --amount ({args.amount}), should be 1 with --list"
        args.mode = TransferMode.ORDERED

    # To address
    if args.to:
        assert (args.to[-4:] == ".eth") or ((args.to[:2] == "0x") and (len(args.to) == 42)), f"Invalid To address provided for --to ({args.to})"

    # To address list
    if args.tolist:
        assert os.path.exists(args.tolist), f"Invalid path to list of To addresses provided for --tolist ({args.tolist})"

    # Test mode
    if args.test:
        print('Test mode enabled: Transfers will be skipped and no fees will incur.')
    
    args.memo = ''

    global VERBOSE
    VERBOSE = args.verbose

    return args

def sanitize_args(args):
    safe_args = [
        "single",
        "random",
        "randomlist",
        "list",
        "to",
        "tolist",
        "amount",
        "test",
        "noprompt",
        "verbose",
        "php"
    ]
    sanitized_args = dict(filter(lambda item: item[0] in safe_args, vars(args).items()))
    return sanitized_args

def get_token_value(amount: int, symbol: str) -> float:
    if symbol not in token_decimals.keys():
        return None
    return amount / (10 ** token_decimals[symbol])

# Estimate fees for a batch of NFTs from offchain fees
def estimate_batch_fees(cfg: Struct, off_chain_fee: OffchainFee, count: int) -> "Tuple[int, int, str]":
    fee = int(off_chain_fee['fees'][cfg.maxFeeTokenId]['fee'])
    token_symbol = off_chain_fee['fees'][cfg.maxFeeTokenId]['token']
    discount = off_chain_fee['fees'][cfg.maxFeeTokenId]['discount']

    estimated_fee = int(count * discount * fee)
    limit_fee = int(estimated_fee * (1 + cfg.feeSlippage))

    return estimated_fee, limit_fee, token_symbol

# Prompts the user to answer by yes or no
def prompt_yes_no(prompt: str, default: str=None):
    if default is None:
        indicator = "[y/n]"
    elif default == "yes":
        indicator = "[Y/n]"
    elif default == "no":
        indicator = "[y/N]"
    else:
        raise ValueError(f"Invalid default string yes/no/None but is {default}")
    
    while True:
        print(f"{prompt} {indicator}: ", end='')
        s = input().lower()
        if s[:1] == 'y':
            return True
        elif s[:1] == 'n':
            return False
        elif s == "" and default is not None:
            if default == "yes":
                return True
            elif default == "no":
                return False

async def get_user_api_key(cfg, secret):
    async with LoopringMintService() as lms:
        # Getting the user api key
        api_key_resp = await lms.getUserApiKey(accountId=cfg.fromAccount, privateKey=secret.loopringPrivateKey)
        # log(f"User API key: {json.dumps(api_key_resp, indent=2)}")   # DO NOT LOG
        if api_key_resp is None:
            sys.exit("Failed to obtain user api key")

    secret.loopringApiKey = api_key_resp['apiKey']

async def get_offchain_parameters(cfg, secret, nftTokenId):
    async with LoopringMintService() as lms:
        parameters = {}
        # Getting the storage id
        storage_id = await lms.getNextStorageId(apiKey=secret.loopringApiKey, accountId=cfg.fromAccount, sellTokenId=nftTokenId)
        log(f"Storage id: {json.dumps(storage_id, indent=2)}")
        if storage_id is None:
            sys.exit("Failed to obtain storage id")
        
        parameters['storage_id'] = storage_id

        # Getting the token address
        counterfactual_nft_info = CounterFactualNftInfo(nftOwner=cfg.fromAddress, nftFactory=cfg.nftFactory, nftBaseUri="")
        counterfactual_nft = await lms.computeTokenAddress(apiKey=secret.loopringApiKey, counterFactualNftInfo=counterfactual_nft_info)
        log(f"CounterFactualNFT Token Address: {json.dumps(counterfactual_nft, indent=2)}")
        if counterfactual_nft is None:
            sys.exit("Failed to obtain token address")
            
        parameters['counterfactual_nft_info'] = counterfactual_nft_info
        parameters['counterfactual_nft'] = counterfactual_nft

        # Getting the offchain fee (requestType=11 is NFT_TRANSFER)
        off_chain_fee = await lms.getOffChainFee(apiKey=secret.loopringApiKey, accountId=cfg.fromAccount, requestType=11, tokenAddress=counterfactual_nft['tokenAddress'])
        log(f"Offchain fee:  {json.dumps(off_chain_fee['fees'][cfg.maxFeeTokenId], indent=2)}")
        if off_chain_fee is None:
            sys.exit("Failed to obtain offchain fee")
            
        parameters['off_chain_fee'] = off_chain_fee

    return parameters

async def get_nft_balance(cfg, secret) -> NftBalance:
    async with LoopringMintService() as lms:
        info = {}
        # Getting the NFT balance
        nft_balance = await lms.getUserNftBalance(apiKey=secret.loopringApiKey, accountId=cfg.fromAccount)
        log(f"NFT balance: {json.dumps(nft_balance, indent=2)}")
        if nft_balance is None:
            sys.exit("Failed to obtain nft balance")
    
    return nft_balance

def filter_nft_balance_by(balance: NftBalance, key: str, values: any) -> NftBalance:
    # Check inputs
    if len(balance['data']) == 0:
        return NftBalance(totalNum=0, data=[])
    assert key in balance['data'][0].keys(), f"Error filtering NFT balance: Invalid key {key}"

    # Convert single elements to list
    if type(values) != type(list()):
        values = [values]

    # Define filter and sorting lambdas
    if key in ['tokenAddress', 'nftId', 'nftData']: # For hex strings, compare the underlying integer
        values = [int(v, 16) for v in values]
        filter_func = lambda t: int(t[key], 16) in values           # Filter out the values of `key` that are not in `values`
        sorting_func = lambda t: values.index(int(t[key], 16))      # Sort by the order in `values`
    else:   # For other types (str, int), compare directly
        filter_func = lambda t: t[key] in values
        sorting_func = lambda t: values.index(t[key])

    filtered_data = list(filter(filter_func, balance['data']))
    sorted_data = sorted(filtered_data, key=sorting_func)
    return NftBalance(totalNum=len(sorted_data), data=sorted_data)

# https://github.com/Loopring/loopring_sdk/blob/692d372165b5ea0d760e33e177d9003cc0dfb0f7/src/api/sign/sign_tools.ts#L1020
async def get_hashes_and_sign(cfg, secret, tokenId: int, amount: int, toAddress: str, toAccount: int, offchain_parameters: dict, info: dict):
    # Generate the poseidon hash for the remaining data
    # https://github.com/Loopring/loopring_sdk/blob/692d372165b5ea0d760e33e177d9003cc0dfb0f7/src/api/sign/sign_tools.ts#L899
    inputs = [
        int(cfg.exchange, 16),
        cfg.fromAccount,  # fromAccountId
        toAccount,        # toAccountId
        tokenId,
        amount,
        cfg.maxFeeTokenId,
        int( (1 + cfg.feeSlippage) * int(offchain_parameters['off_chain_fee']['fees'][cfg.maxFeeTokenId]['fee']) ), # Apply max fee slippage
        # int(offchain_parameters['off_chain_fee']['fees'][cfg.maxFeeTokenId]['fee']),
        int(toAddress, 16),
        0,
        0,
        cfg.validUntil,
        offchain_parameters['storage_id']['offchainId']
    ]
    hasher = NFTTransferEddsaSignHelper(private_key=secret.loopringPrivateKey)
    nft_poseidon_hash = hasher.hash(inputs)
    plog(inputs)
    log("Hashed NFT transfer payload: 0x{0:0{1}x}".format(nft_poseidon_hash, 64))
    info['nft_poseidon_hash'] = "0x{0:0{1}x}".format(nft_poseidon_hash, 64)

    eddsa_signature = hasher.sign(inputs)
    log(f"Signed NFT payload hash: {eddsa_signature}")
    info['eddsa_signature'] = eddsa_signature

    # Generate the ECDSA signature
    EIP712.init_env(name="Loopring Protocol",
                    version="3.6.0",
                    chainId=1,
                    verifyingContract="0x0BABA1Ad5bE3a5C0a66E7ac838a129Bf948f1eA4")

    message = generateTransferEIP712Hash(req={
        'payerAddr': cfg.fromAddress,
        'payeeAddr': toAddress,
        'token': {
            'volume': str(amount),
            'tokenId': tokenId
        },
        'maxFee': {
            'tokenId': cfg.maxFeeTokenId,
            'volume': int( (1 + cfg.feeSlippage) * int(offchain_parameters['off_chain_fee']['fees'][cfg.maxFeeTokenId]['fee']) ) # Apply max fee slippage
        },
        'validUntil': cfg.validUntil,
        'storageId': offchain_parameters['storage_id']['offchainId']
    })

    # print(f"{message=}")
    eth_pkey = int(secret.metamaskPrivateKey, 16).to_bytes(32, byteorder='big')
    v, r, s = sig_utils.ecsign(message, eth_pkey)
    ecdsa_signature = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + "02"
    # print(f"{ecdsa_signature=}")

    return eddsa_signature, ecdsa_signature

async def transfer_nft(cfg, secret,  amount: int, toAccount: int, toAddress: str, nftInfo: NftInfo, eddsa_signature: str, ecdsa_signature: str, offchain_parameters: dict, test_mode: bool, info: dict):
    async with LoopringMintService() as lms:
        if test_mode:
            return TransferResult.TESTMODE, None
        
        nft_transfer_response = await lms.transferNft(
            apiKey=secret.loopringApiKey,
            exchange=cfg.exchange,
            fromAccountId=cfg.fromAccount,
            fromAddress=cfg.fromAddress,
            toAccountId=toAccount,
            toAddress=toAddress,
            amount=amount,
            validUntil=cfg.validUntil,
            storageId=offchain_parameters['storage_id']['offchainId'],
            maxFeeTokenId=cfg.maxFeeTokenId,
            maxFeeAmount=int( (1 + cfg.feeSlippage) * int(offchain_parameters['off_chain_fee']['fees'][cfg.maxFeeTokenId]['fee']) ),
            memo=cfg.memo,
            nftInfo=nftInfo,
            counterFactualNftInfo=offchain_parameters['counterfactual_nft_info'],
            eddsaSignature=eddsa_signature,
            ecdsaSignature=ecdsa_signature
        )
        log(f"Nft Transfer reponse: {nft_transfer_response}")
        info['nft_transfer_response'] = nft_transfer_response

    if nft_transfer_response is None:   # Something failed
        mint_code = lms.last_error['resultInfo']['code']
        if mint_code == 114002: # Invalid fee amount
            return TransferResult.FEE_INVALID, nft_transfer_response
    elif lms.last_status == 200:    # Transfer succeeded
        return TransferResult.SUCCESS, nft_transfer_response

    return TransferResult.FAILED, nft_transfer_response

async def main():
    # check for command line arguments
    try:
        args = parse_args()
    except Exception as err:
        sys.exit(f"Failed to initialize the transfers: {err}")
    
    # Generate paths
    paths = generate_paths()

    if not os.path.exists(os.path.dirname(paths.transfer_info)):
        os.makedirs(os.path.dirname(paths.transfer_info))

    transfer_info = []
    transfer_info.append({'args': vars(args)})

    approved_fees_prompt = args.noprompt

    try:
        cfg, secret = await load_config(args, paths)
        log("config dump:")
        plog(cfg)
        transfer_info.append({'cfg': cfg})

        # Get user API key
        print("Getting user API key... ", end='')
        await get_user_api_key(cfg, secret)
        print("done!")

        # Prepare to addresses
        if args.tolist:
            with open(args.tolist, 'r') as f:
                tos = [line.strip() for line in f]
        elif args.to:
            tos = [args.to]

        # Prepare NFT IDs from source and filter based on sender balance
        print("Retrieving sender's NFT balance... ", end='')
        nft_balance = await get_nft_balance(cfg, secret)
        print("done!")
        if args.mode == TransferMode.SINGLE:
            # Verify that single NFT ID is in the sender balance
            nfts = filter_nft_balance_by(nft_balance, 'nftId', args.nftid)
        else:   # RANDOM or ORDERED
            if args.random_contract:
                # Filter those not from that contract address/collection
                nfts = filter_nft_balance_by(nft_balance, 'tokenAddress', args.random_contract)
            elif args.random_list or args.ordered_list:
                # Get list of CIDs or NFT IDs from file, verify they are in the sender balance    
                with open(args.random_list or args.ordered_list, 'r') as f:
                    cids = [line.strip() for line in f.readlines()]
                    cids = list(set(cids))  # Remove duplicate lines
                nft_ids = ["0x" + base58.b58decode(cid).hex()[4:] if cid[:2] == "Qm" else cid for cid in cids]  # CID to NFT ID hex-string: base58 to hex and drop first 2 bytes (always 1220h)
                nfts = filter_nft_balance_by(nft_balance, 'nftId', nft_ids)

        log(nfts['totalNum'])
        plog(nfts)
        transfer_info.append({'nfts': nfts})

        # Weights based off the amount of each NFT
        weights = [int(t['total']) for t in nfts['data']]
        total_amount = sum(weights)
        log(weights, total_amount)
        transfer_info.append({'weights': weights})
        transfer_info.append({'total_amount': total_amount})

        # Make sure they have at least as many NFTs as to addresses
        if total_amount < (len(tos) * args.amount):
            sys.exit(f"Not enough matching NFTs found in balance of account {cfg.fromAccount} ({total_amount} matching, but expected {(len(tos) * args.amount)} or more)")

        # Filter tos
        skipped_tos = []
        filtered_tos = []
        for to in tos:
            info = {'to': to, 'invalid': True}

            valid_to = True

            try: 
                to_account, to_address = await retry_async(get_account_info, to, retries=3)
                if not to_account or not to_address:
                    valid_to = False
            except:
                valid_to = False
            
            if not valid_to:
                transfer_info.append(info)
                print(f"Skipping invalid to address: {to}")
                skipped_tos.append(to)
                continue

            filtered_tos.append((to_account, to_address))
            info['invalid'] = False
            info['to_account'] = to_account
            info['to_address'] = to_address

            transfer_info.append(info)

        if len(filtered_tos) == 0:
            sys.exit(f"No valid to address found, no one to transfer to...")

        # Get storage id, token address and offchain fee
        print("Getting offchain parameters... ", end='')
        offchain_parameters = await get_offchain_parameters(cfg, secret, nfts['data'][0]['tokenId'])
        transfer_info.append({'offchain_parameters': offchain_parameters})
        print("done!")

        # Estimate fees and get user approval
        log("--------")
        cfg.feeEstimate, cfg.feeLimit, cfg.feeSymbol = estimate_batch_fees(cfg, offchain_parameters['off_chain_fee'], len(filtered_tos))
        print(f"Estimated L2 fees for transfering NFTs to {len(filtered_tos)} addresses: {get_token_value(cfg.feeEstimate, cfg.feeSymbol)}-{get_token_value(cfg.feeLimit, cfg.feeSymbol)}{cfg.feeSymbol}", end='')
        if args.fees:   # Exit if --fees
            print()
            sys.exit()
        if not args.noprompt:   # Skip approval if --noprompt
            approved_fees_prompt = prompt_yes_no(", continue?", default="no")
            transfer_info.append({'fee_approval': approved_fees_prompt, 'feeEstimate': cfg.feeEstimate, 'feeLimit': cfg.feeLimit, 'feeSymbol': cfg.feeSymbol})
            if not approved_fees_prompt: 
                sys.exit("Fees not approved by user")
        else:
            print()
        approved_off_chain_fees = offchain_parameters['off_chain_fee']
        
        # NFT transfer sequence
        for i, (to_account, to_address) in enumerate(filtered_tos):
            info = {'to_account': to_account, 'to_address': to_address}

            log("Picking from weights:", weights)

            if args.mode == TransferMode.SINGLE:
                nft_info = nfts['data'][0]
                index = 0
            elif args.mode == TransferMode.RANDOM:
                # Pick random NFT ID by index
                index = random.choices(range(nfts['totalNum']), weights)[0]
                weights[index] -= 1  # Amount of that NFT is one less for subsequent random choice
                nft_info = nfts['data'][index]
            elif args.mode == TransferMode.ORDERED: # Using `weights` list as the quantity remaining of each NFT
                # Pick NFT ID sequentially (next NFT ID with weight > 0)
                index = next(i for i,w in enumerate(weights) if w > 0)
                weights[index] -= 1  # Amount of that NFT is one less for subsequent transfer
                nft_info = nfts['data'][index]

            log("Picked:", index)
            plog(nft_info)

            info['index'] = index
            info['nftId'] = nft_info['nftId']

            # Get storage id, token address, and keep originally approved off chain fees
            offchain_parameters = await get_offchain_parameters(cfg, secret, nft_info['tokenId'])
            offchain_parameters['off_chain_fee'] = approved_off_chain_fees

            # Generate Eddsa Signature
            eddsa_signature, ecdsa_signature = await get_hashes_and_sign(cfg, secret, nft_info['tokenId'], args.amount, to_address, to_account, offchain_parameters=offchain_parameters, info=info)

            # Submit the nft transfer
            transfer_result, response = await transfer_nft(cfg,
                                                           secret,
                                                           amount=args.amount,
                                                           toAccount=to_account,
                                                           toAddress=to_address,
                                                           nftInfo=nft_info,
                                                           eddsa_signature=eddsa_signature,
                                                           ecdsa_signature=ecdsa_signature,
                                                           offchain_parameters=offchain_parameters,
                                                           test_mode=args.test,
                                                           info=info)
            
            if transfer_result == TransferResult.SUCCESS:
                print(f"{i+1}/{len(filtered_tos)} {i+1}: Successful Transfer! (tx hash: {response['hash']}, to: {to_address}, nftId: {nft_info['nftId']})")
                offchain_parameters['storage_id']['offchainId'] += 2
            elif transfer_result == TransferResult.FAILED:
                print(f"{i+1}/{len(filtered_tos)} {i+1}: Transfer FAILED... (to: {to_address}, nftId: {nft_info['nftId']})")
            elif transfer_result == TransferResult.FEE_INVALID: # Invalid fees, exit cleanly
                print(f"{i+1}/{len(filtered_tos)} {i+1}: Transfer FAILED due to invalid fee. Was there a gas spike? (to: {to_address}, nftId: {nft_info['nftId']})")
                print(f"Fees increased above the limit of {get_token_value(cfg.feeLimit, cfg.feeSymbol)}{cfg.feeSymbol}, aborting...")
                sys.exit(transfer_result)
            elif transfer_result == TransferResult.TESTMODE:
                print(f"{i+1}/{len(filtered_tos)} {i+1}: Skipping transfer (test mode) (to: {to_address}, nftId: {nft_info['nftId']})")

            transfer_info.append(info)

        if len(skipped_tos) > 0:
            print(f"Skipped {len(skipped_tos)} invalid to addresses:")
            print('\n'.join(skipped_tos))
    finally:
        with open(paths.transfer_info, 'w+') as f:
            json.dump(transfer_info, f, indent=4)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
