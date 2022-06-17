#!/usr/bin/env python3
import os
import sys

from pprint import pprint
import argparse
import asyncio
import random
import base58
import json
import re

from utils import Struct, generate_paths, load_config_json, load_traits, sanitize, set_progress_for_ui
from minter import get_account_info

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


async def retry_async(coro, *args, timeout: float = 3, retries: int = 3, **kwds):
    for attempts in range(retries):
        try:
            return await asyncio.wait_for(coro(*args, **kwds), timeout=timeout)
        except asyncio.TimeoutError:
            print("Retrying... " + str(attempts))


# Parse CLI arguments
def parse_args() -> argparse.Namespace:
    # check for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nfts",
        metavar='<NFTID, CID, CONTRACT, "COLLECTION" or LIST>',
        dest="source",
        help="Specify which NFT(s) to send. COLLECTION is a LooPyGen collection name (surround with quotes for special characters and spaces). LIST is a text file with one NFTID or CID per line, or a metadata-cids.json file",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--to",
        metavar="<ADDRESS, ENS, ACCOUNTID or LIST>",
        dest="to",
        help="Wallets to send NFTs to. LIST is a text file with one ADDRESS, ENS or ACCOUNTID per line",
        type=str,
        required=True,
    )
    mode_group_title = parser.add_argument_group(title="Transfer mode")
    mode_group = mode_group_title.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--single",
        dest="single",
        help="Send an NFT to each address provided (set how many copies are sent to each address with --amount)",
        action="store_true",
    )
    mode_group.add_argument(
        "--random",
        dest="random",
        help="Send one random NFT to each address provided (the randomness is weighted by the amount of each NFT in the sender wallet). Only use with --nfts CONTRACT or LIST. The sender wallet should have at least as many NFTs (including copies) as there are addresses in --to",
        action="store_true",
    )
    mode_group.add_argument(
        "--ordered",
        dest="ordered",
        help="Send one NFT to each address provided, in order (1st NFT to 1st address, 2nd NFT to 2nd address, ...). Only use with --nfts LIST. Does *NOT* support --nfts CONTRACT as a source. --nfts LIST should have at least as many lines of NFTs as there are addresses in --to",
        action="store_true",
    )
    parser.add_argument(
        "--memo",
        metavar='"MEMO"',
        help="A note attached to your transfers (must be surrounded with quotes)",
        type=str,
        default="",
    )
    parser.add_argument(
        "--amount",
        help="Amount of NFTs to send to each address (only valid with --single mode)",
        type=int,
        default=1,
    )
    parser.add_argument("--test", help="Skips the transfer step", action="store_true")

    advanced_group = parser.add_argument_group(title="Advanced options")
    advanced_group.add_argument(
        "--noprompt", help="Skip all user prompts", action="store_true"
    )
    advanced_group.add_argument(
        "-V", "--verbose", help="Verbose output", action="store_true"
    )
    advanced_group.add_argument(
        "--fees", help="Estimates the fees and exits", action="store_true"
    )
    advanced_group.add_argument(
        "--php", help=argparse.SUPPRESS, action="store_true"
    )  # Unused. Prevents errors if flag is provided
    advanced_group.add_argument(
        "--configpass", help=argparse.SUPPRESS, type=str
    )  # Should be base64 encoded

    args = parser.parse_args()

    # Test mode
    if args.test:
        print("Test mode enabled: Transfers will be skipped and no fees will incur.")

    global VERBOSE
    VERBOSE = args.verbose

    return args


# Build config dictionnary
async def load_config(args, paths: Struct):

    cfg = Struct()
    secret = Struct()  # Split to avoid leaking keys to console or logs
    loopygen_cfg = load_config_json(
        paths.transfer_config, args.configpass, args.noprompt
    )
    secret.loopringPrivateKey = loopygen_cfg.private_key
    secret.metamaskPrivateKey = loopygen_cfg.private_key_mm
    cfg.fromAddress = loopygen_cfg.sender
    cfg.maxFeeTokenId = int(loopygen_cfg.fee_token)
    cfg.memo = str(args.memo).strip()

    # Fee limit is estimatedFee * ( 1 + feeSlippage ), default: +50%
    cfg.feeSlippage = 0.5
    cfg.validUntil = 1700000000
    cfg.nftFactory = "0xc852aC7aAe4b0f0a0Deb9e8A391ebA2047d80026"
    cfg.exchange = "0x0BABA1Ad5bE3a5C0a66E7ac838a129Bf948f1eA4"

    # Resolve ENS, get account_id and ETH address
    cfg.fromAccount, cfg.fromAddress = await retry_async(
        get_account_info, cfg.fromAddress, retries=3
    )
    assert (
        cfg.fromAddress and cfg.fromAccount
    ), f"Invalid from address: {cfg.fromAddress} (account ID {cfg.fromAccount})"

    assert (
        secret.loopringPrivateKey
    ), "Missing Loopring private key (LOOPRING_PRIVATE_KEY)"
    assert secret.metamaskPrivateKey, "Missing MetaMask private key (L1_PRIVATE_KEY)"
    assert cfg.maxFeeTokenId in range(
        len(token_decimals)
    ), f"Missing or invalid fee token ID (FEE_TOKEN_ID): {cfg.maxFeeTokenId}"

    if secret.loopringPrivateKey[:2] != "0x":
        secret.loopringPrivateKey = "0x{0:0{1}x}".format(
            int(secret.loopringPrivateKey), 64
        )
    secret.loopringPrivateKey = secret.loopringPrivateKey.lower()
    if len(secret.metamaskPrivateKey) == 64 and secret.metamaskPrivateKey[:2] != "0x":
        secret.metamaskPrivateKey = "0x" + secret.metamaskPrivateKey
    secret.metamaskPrivateKey = secret.metamaskPrivateKey.lower()

    # Get user API key
    print("Getting user API key... ", end="")
    await get_user_api_key(cfg, secret)
    print("done!")

    # Prepare NFT IDs from source and filter based on sender balance
    print("Retrieving sender's NFT balance... ", end="")
    nft_balance = await get_nft_balance(cfg, secret)
    print("done!")

    ## CLI args validation
    # --nfts
    args.source = str(args.source).strip()
    if os.path.exists(args.source) or os.path.exists(
        os.path.join(".", "collections", sanitize(args.source), "config", "traits.json")
    ):  # LIST or COLLECTION
        # Determine the source file name
        if os.path.exists(args.source):
            fn = args.source
        else:
            traits = load_traits(sanitize(args.source))
            paths = generate_paths(traits)
            assert os.path.exists(
                paths.metadata_cids
            ), f'Collection "{traits.collection_name}" is missing metadata-cids.json file'
            fn = paths.metadata_cids
        # Open source file and load nft ids from it
        with open(fn, "r") as f:
            if os.path.split(fn)[-1] == "metadata-cids.json":
                # Handle metadata-cids.json format
                metadata_cids = json.load(f)
                lines = [element["CID"] for element in metadata_cids]
            else:
                # Handle simple text files (newline delimited)
                lines = [line.strip() for line in f.readlines()]
        # Convert each line to NFT ID hex-string if it was a CID: base58 to hex and drop first 2 bytes (always 1220h)
        nft_ids = [
            "0x" + base58.b58decode(line).hex()[4:] if line[:2] == "Qm" else line
            for line in lines
        ]
        cfg.nfts = filter_nft_balance_by(nft_balance, "nftId", nft_ids)
        # Treat --ordered as a special case. cfg.nfts should be a list of nft info based on the --nfts LIST file
        if args.ordered:
            nfts_data = []
            # For each line in the --nfts LIST file, get the nft_info (from the nft_balance) and add it to the new cfg.nfts
            for nft_id in nft_ids:
                nft_data = filter_nft_balance_by(cfg.nfts, "nftId", nft_id)["data"]
                nfts_data.extend(nft_data)
            cfg.nfts = NftBalance(totalNum=len(nfts_data), data=nfts_data)
    elif re.match(r"^Qm[a-zA-Z0-9]{44}$", args.source):  # CID
        nft_id = "0x" + base58.b58decode(args.source).hex()[4:]
        cfg.nfts = filter_nft_balance_by(nft_balance, "nftId", nft_id)
        assert (
            not args.ordered
        ), f"Unsupported --nfts CID with transfer mode --ordered or --random. Did you mean to use --single transfer mode?"
    elif re.match(r"^0x[a-fA-F0-9]{41,64}$", args.source):  # NFTID
        nft_id = "0x" + args.source.replace("0x", "").rjust(64, "0")
        cfg.nfts = filter_nft_balance_by(nft_balance, "nftId", nft_id)
        assert (
            not args.ordered
        ), f"Unsupported --nfts NFTID with transfer mode --ordered or --random. Did you mean to use --single transfer mode?"
    elif re.match(r"^0x[a-fA-F0-9]{40}$", args.source):  # CONTRACT
        contract = "0x" + args.source.replace("0x", "").rjust(40, "0")
        cfg.nfts = filter_nft_balance_by(nft_balance, "tokenAddress", contract)
        assert (
            not args.ordered
        ), f"Unsupported --nfts CONTRACT with transfer mode --ordered. Please use --nfts NFTID, CID or LIST with --ordered"
    plog(cfg.nfts)

    cfg.nftsCount = cfg.nfts["totalNum"]
    assert (
        cfg.nftsCount > 0
    ), f"No NFT matching \"{args.source}\" was found in the sender's wallet. Make sure --nfts is a valid NFTID, CID, CONTRACT, COLLECTION or LIST."

    # Weights based off the amount of each NFT
    cfg.weights = [int(t["total"]) for t in cfg.nfts["data"]]
    cfg.totalAmount = sum(cfg.weights)
    log(cfg.weights, cfg.totalAmount)

    # --to
    args.to = str(args.to).strip()
    if os.path.exists(args.to):  # LIST
        with open(args.to, "r") as f:
            cfg.tosRaw = [line.strip() for line in f.readlines()]
    else:  # ADDRESS, ENS or ACCOUNTID
        cfg.tosRaw = [args.to]

    # All valid (account, address) tuples
    cfg.tos = []
    # True/False representing validity of each cfg.tosRaw element
    cfg.tosRawValid = []
    # Validate each entry by getting Loopring account ID and address
    for to in cfg.tosRaw:
        valid = False
        try:
            to_account, to_address = await retry_async(get_account_info, to, retries=3)
            if to_account and to_address:
                valid = True
        except:
            pass
        cfg.tosRawValid.append(valid)
        if valid:
            cfg.tos.append((to_account, to_address))
        else:
            print(f"Skipping invalid to address: {to}")
    plog(cfg.tos)

    cfg.tosCount = len(cfg.tos)
    assert (
        cfg.tosCount > 0
    ), f"Could not parse --to argument {args.to}. Make sure it is an ADDRESS, ENS, ACCOUNTID or LIST."

    # Transfer mode (--single, --ordered or --random)
    if args.single:
        args.amount = int(args.amount)
        assert (
            cfg.nftsCount == 1
        ), f"Expected only 1 NFT in --nfts for --single transfer mode, got {cfg.nftsCount}"
        # Make sure they have at least as many NFT copies as to addresses
        assert (
            cfg.totalAmount >= cfg.tosCount * args.amount
        ), f"Not enough copies of the NFT found in balance of account {cfg.fromAccount} (expected {cfg.tosCount * args.amount} or more, but got {cfg.totalAmount} matching)."
    elif args.random:
        # --amount should be the default of 1
        assert (
            args.amount == 1
        ), f"Unsupported --amount argument with --ordered transfer mode."
        # Make sure they have at least as many total NFT copies as to addresses
        assert (
            cfg.totalAmount >= cfg.tosCount * args.amount
        ), f"Not enough NFTs (including copies) found in balance of account {cfg.fromAccount} (expected {cfg.tosCount} or more, but got {cfg.totalAmount} matching)."
    elif args.ordered:
        # --amount should be the default of 1
        assert (
            args.amount == 1
        ), f"Unsupported --amount argument with --ordered transfer mode."
        # At least as many NFTs should be provided in --nfts as addresses in --to
        assert (
            cfg.nftsCount >= cfg.tosCount
        ), f"Not enough NFTs provided for --ordered transfer mode. At least as many NFTs should be provided in --nfts as addresses in --to (got {cfg.tosCount} addresses, but got {cfg.nftsCount} NFTs)."
        nft_ids = [nft["nftId"] for nft in cfg.nfts["data"]]
        unique_nft_ids = list(set(nft_ids))
        # How many copies of each NFT is needed
        count_per_nft_id = [nft_ids.count(nft_id) for nft_id in unique_nft_ids]
        # How many copies of each NFT is in balance
        balance_per_nft_id = [
            int(filter_nft_balance_by(nft_balance, "nftId", nft_id)["data"][0]["total"])
            for nft_id in unique_nft_ids
        ]
        enough_copies_per_nft_id = [
            (balance >= count)
            for (count, balance) in zip(count_per_nft_id, balance_per_nft_id)
        ]
        if not all(enough_copies_per_nft_id):
            missing_copies_strings = [
                f"NFT ID {nft_id}: Expected {count} copies but found {balance} in wallet"
                for (nft_id, count, balance, enough) in zip(
                    unique_nft_ids,
                    count_per_nft_id,
                    balance_per_nft_id,
                    enough_copies_per_nft_id,
                )
                if not enough
            ]
            sys.exit(
                f"Not enought copies of some NFTs found in balance of account {cfg.fromAccount}\n"
                + "\n".join(missing_copies_strings)
            )

    return cfg, secret


def sanitize_args(args) -> dict:
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
        "php",
    ]
    sanitized_args = dict(filter(lambda item: item[0] in safe_args, vars(args).items()))
    return sanitized_args


def get_token_value(amount: int, symbol: str) -> float:
    if symbol not in token_decimals.keys():
        return None
    return amount / (10 ** token_decimals[symbol])


# Estimate fees for a batch of NFTs from offchain fees
def estimate_batch_fees(
    cfg: Struct, off_chain_fee: OffchainFee, count: int
) -> "Tuple[int, int, str]":
    fee = int(off_chain_fee["fees"][cfg.maxFeeTokenId]["fee"])
    token_symbol = off_chain_fee["fees"][cfg.maxFeeTokenId]["token"]
    discount = off_chain_fee["fees"][cfg.maxFeeTokenId]["discount"]

    estimated_fee = int(count * discount * fee)
    limit_fee = int(estimated_fee * (1 + cfg.feeSlippage))

    return estimated_fee, limit_fee, token_symbol


# Prompts the user to answer by yes or no
def prompt_yes_no(prompt: str, default: str = None) -> bool:
    if default is None:
        indicator = "[y/n]"
    elif default == "yes":
        indicator = "[Y/n]"
    elif default == "no":
        indicator = "[y/N]"
    else:
        raise ValueError(f"Invalid default string yes/no/None but is {default}")

    while True:
        print(f"{prompt} {indicator}: ", end="")
        s = input().lower()
        if s[:1] == "y":
            return True
        elif s[:1] == "n":
            return False
        elif s == "" and default is not None:
            if default == "yes":
                return True
            elif default == "no":
                return False


async def get_user_api_key(cfg, secret) -> None:
    async with LoopringMintService() as lms:
        # Getting the user api key
        api_key_resp = await lms.getUserApiKey(
            accountId=cfg.fromAccount, privateKey=secret.loopringPrivateKey
        )
        # log(f"User API key: {json.dumps(api_key_resp, indent=2)}")   # DO NOT LOG
        if api_key_resp is None:
            sys.exit("Failed to obtain user api key")

    secret.loopringApiKey = api_key_resp["apiKey"]


async def get_offchain_parameters(cfg, secret, nftTokenId) -> dict:
    async with LoopringMintService() as lms:
        parameters = {}
        # Getting the storage id
        storage_id = await lms.getNextStorageId(
            apiKey=secret.loopringApiKey,
            accountId=cfg.fromAccount,
            sellTokenId=nftTokenId,
        )
        log(f"Storage id: {json.dumps(storage_id, indent=2)}")
        if storage_id is None:
            sys.exit("Failed to obtain storage id")

        parameters["storage_id"] = storage_id

        # Getting the token address
        counterfactual_nft_info = CounterFactualNftInfo(
            nftOwner=cfg.fromAddress, nftFactory=cfg.nftFactory, nftBaseUri=""
        )
        counterfactual_nft = await lms.computeTokenAddress(
            apiKey=secret.loopringApiKey, counterFactualNftInfo=counterfactual_nft_info
        )
        log(
            f"CounterFactualNFT Token Address: {json.dumps(counterfactual_nft, indent=2)}"
        )
        if counterfactual_nft is None:
            sys.exit("Failed to obtain token address")

        parameters["counterfactual_nft_info"] = counterfactual_nft_info
        parameters["counterfactual_nft"] = counterfactual_nft

        # Getting the offchain fee (requestType=11 is NFT_TRANSFER)
        off_chain_fee = await lms.getOffChainFee(
            apiKey=secret.loopringApiKey,
            accountId=cfg.fromAccount,
            requestType=11,
            tokenAddress=counterfactual_nft["tokenAddress"],
        )
        log(
            f"Offchain fee:  {json.dumps(off_chain_fee['fees'][cfg.maxFeeTokenId], indent=2)}"
        )
        if off_chain_fee is None:
            sys.exit("Failed to obtain offchain fee")

        parameters["off_chain_fee"] = off_chain_fee

    return parameters


async def get_nft_balance(cfg, secret) -> NftBalance:
    async with LoopringMintService() as lms:
        info = {}
        # Getting the NFT balance
        nft_balance = await lms.getUserNftBalance(
            apiKey=secret.loopringApiKey, accountId=cfg.fromAccount
        )
        log(f"NFT balance: {json.dumps(nft_balance, indent=2)}")
        if nft_balance is None:
            sys.exit("Failed to obtain nft balance")

    return nft_balance


def filter_nft_balance_by(balance: NftBalance, key: str, values: any) -> NftBalance:
    # Check inputs
    if len(balance["data"]) == 0:
        return NftBalance(totalNum=0, data=[])
    assert (
        key in balance["data"][0].keys()
    ), f"Error filtering NFT balance: Invalid key {key}"

    # Convert single elements to list
    if type(values) != type(list()):
        values = [values]

    # Define filter and sorting lambdas
    if key in [
        "tokenAddress",
        "nftId",
        "nftData",
    ]:  # For hex strings, compare the underlying integer
        values = [int(v, 16) for v in values]
        filter_func = (
            lambda t: int(t[key], 16) in values
        )  # Filter out the values of `key` that are not in `values`
        sorting_func = lambda t: values.index(
            int(t[key], 16)
        )  # Sort by the order in `values`
    else:  # For other types (str, int), compare directly
        filter_func = lambda t: t[key] in values
        sorting_func = lambda t: values.index(t[key])

    filtered_data = list(filter(filter_func, balance["data"]))
    sorted_data = sorted(filtered_data, key=sorting_func)
    return NftBalance(totalNum=len(sorted_data), data=sorted_data)


# https://github.com/Loopring/loopring_sdk/blob/692d372165b5ea0d760e33e177d9003cc0dfb0f7/src/api/sign/sign_tools.ts#L1020
async def get_hashes_and_sign(
    cfg,
    secret,
    tokenId: int,
    amount: int,
    toAddress: str,
    toAccount: int,
    offchain_parameters: dict,
    info: dict,
):
    # Generate the poseidon hash for the remaining data
    # https://github.com/Loopring/loopring_sdk/blob/692d372165b5ea0d760e33e177d9003cc0dfb0f7/src/api/sign/sign_tools.ts#L899
    inputs = [
        int(cfg.exchange, 16),
        cfg.fromAccount,  # fromAccountId
        toAccount,  # toAccountId
        tokenId,
        amount,
        cfg.maxFeeTokenId,
        int(
            (1 + cfg.feeSlippage)
            * int(
                offchain_parameters["off_chain_fee"]["fees"][cfg.maxFeeTokenId]["fee"]
            )
        ),  # Apply max fee slippage
        # int(offchain_parameters['off_chain_fee']['fees'][cfg.maxFeeTokenId]['fee']),
        int(toAddress, 16),
        0,
        0,
        cfg.validUntil,
        offchain_parameters["storage_id"]["offchainId"],
    ]
    hasher = NFTTransferEddsaSignHelper(private_key=secret.loopringPrivateKey)
    nft_poseidon_hash = hasher.hash(inputs)
    log("NFT transfer payload hash inputs:")
    plog(inputs)
    log("Hashed NFT transfer payload: 0x{0:0{1}x}".format(nft_poseidon_hash, 64))
    info["nft_poseidon_hash"] = "0x{0:0{1}x}".format(nft_poseidon_hash, 64)

    eddsa_signature = hasher.sign(inputs)
    log(f"Signed NFT payload hash: {eddsa_signature}")
    info["eddsa_signature"] = eddsa_signature

    # Generate the ECDSA signature
    EIP712.init_env(
        name="Loopring Protocol",
        version="3.6.0",
        chainId=1,
        verifyingContract="0x0BABA1Ad5bE3a5C0a66E7ac838a129Bf948f1eA4",
    )

    message = generateTransferEIP712Hash(
        req={
            "payerAddr": cfg.fromAddress,
            "payeeAddr": toAddress,
            "token": {"volume": str(amount), "tokenId": tokenId},
            "maxFee": {
                "tokenId": cfg.maxFeeTokenId,
                "volume": int(
                    (1 + cfg.feeSlippage)
                    * int(
                        offchain_parameters["off_chain_fee"]["fees"][cfg.maxFeeTokenId][
                            "fee"
                        ]
                    )
                ),  # Apply max fee slippage
            },
            "validUntil": cfg.validUntil,
            "storageId": offchain_parameters["storage_id"]["offchainId"],
        }
    )

    # print(f"{message=}")
    eth_pkey = int(secret.metamaskPrivateKey, 16).to_bytes(32, byteorder="big")
    v, r, s = sig_utils.ecsign(message, eth_pkey)
    ecdsa_signature = "0x" + bytes.hex(v_r_s_to_signature(v, r, s)) + "02"
    # print(f"{ecdsa_signature=}")

    return eddsa_signature, ecdsa_signature


async def transfer_nft(
    cfg,
    secret,
    amount: int,
    toAccount: int,
    toAddress: str,
    nftInfo: NftInfo,
    eddsa_signature: str,
    ecdsa_signature: str,
    offchain_parameters: dict,
    test_mode: bool,
    info: dict,
) -> TransferResult:
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
            storageId=offchain_parameters["storage_id"]["offchainId"],
            maxFeeTokenId=cfg.maxFeeTokenId,
            maxFeeAmount=int(
                (1 + cfg.feeSlippage)
                * int(
                    offchain_parameters["off_chain_fee"]["fees"][cfg.maxFeeTokenId][
                        "fee"
                    ]
                )
            ),
            memo=cfg.memo,
            nftInfo=nftInfo,
            counterFactualNftInfo=offchain_parameters["counterfactual_nft_info"],
            eddsaSignature=eddsa_signature,
            ecdsaSignature=ecdsa_signature,
        )
        log(f"Nft Transfer reponse: {nft_transfer_response}")
        info["nft_transfer_response"] = nft_transfer_response

    if nft_transfer_response is None:  # Something failed
        mint_code = lms.last_error["resultInfo"]["code"]
        if mint_code == 114002:  # Invalid fee amount
            return TransferResult.FEE_INVALID, nft_transfer_response
    elif lms.last_status == 200:  # Transfer succeeded
        return TransferResult.SUCCESS, nft_transfer_response

    return TransferResult.FAILED, nft_transfer_response


async def main() -> None:
    # check for command line arguments
    try:
        args = parse_args()
    except Exception as err:
        sys.exit(f"Failed to initialize the transfers: {err}")

    # Generate paths
    paths = generate_paths()

    # Load transfer config and configure the tool based on the CLI args
    cfg, secret = await load_config(args, paths)

    if not os.path.exists(os.path.dirname(paths.transfer_info)):
        os.makedirs(os.path.dirname(paths.transfer_info))

    transfer_info = []
    transfer_info.append({"args": sanitize_args(args)})

    try:
        log("config dump:")
        plog(cfg)
        transfer_info.append({"cfg": cfg})

        # Get storage id, token address and offchain fee
        print("Getting offchain parameters... ", end="")
        offchain_parameters = await get_offchain_parameters(
            cfg, secret, cfg.nfts["data"][0]["tokenId"]
        )
        transfer_info.append({"offchain_parameters": offchain_parameters})
        print("done!")

        # Estimate fees and get user approval
        log("--------")
        cfg.feeEstimate, cfg.feeLimit, cfg.feeSymbol = estimate_batch_fees(
            cfg, offchain_parameters["off_chain_fee"], cfg.tosCount
        )
        fee_range_string = f"{get_token_value(cfg.feeEstimate, cfg.feeSymbol)}-{get_token_value(cfg.feeLimit, cfg.feeSymbol)}{cfg.feeSymbol}"
        print(
            f"Estimated L2 fees for transfering NFTs to {cfg.tosCount} addresses: {fee_range_string}",
            end="",
        )
        if args.fees:  # Exit if --fees
            print()
            sys.exit()
        if not args.noprompt:  # Skip approval if --noprompt
            approved_fees_prompt = prompt_yes_no(", continue?", default="no")
            transfer_info.append(
                {
                    "fee_approval": approved_fees_prompt,
                    "feeEstimate": cfg.feeEstimate,
                    "feeLimit": cfg.feeLimit,
                    "feeSymbol": cfg.feeSymbol,
                }
            )
            if not approved_fees_prompt:
                sys.exit("Fees not approved by user")
        else:
            print()
        approved_off_chain_fees = offchain_parameters["off_chain_fee"]

        # NFT transfer sequence
        for i, (to_account, to_address) in enumerate(cfg.tos):
            info = {"to_account": to_account, "to_address": to_address}

            if args.single:
                index = 0
            elif args.random:
                # Pick random NFT ID by index
                index = random.choices(range(cfg.nfts["totalNum"]), cfg.weights)[0]
                # Amount of that NFT is one less for subsequent random choice
                cfg.weights[index] -= 1
            elif args.ordered:
                # Pick NFT ID sequentially
                index = i

            nft_info = cfg.nfts["data"][index]

            log("Picked:", index)
            plog(nft_info)

            info["index"] = index
            info["nftId"] = nft_info["nftId"]

            # Get storage id, token address, and keep originally approved off chain fees
            offchain_parameters = await get_offchain_parameters(
                cfg, secret, nft_info["tokenId"]
            )
            offchain_parameters["off_chain_fee"] = approved_off_chain_fees

            # Generate Eddsa Signature
            eddsa_signature, ecdsa_signature = await get_hashes_and_sign(
                cfg,
                secret,
                nft_info["tokenId"],
                args.amount,
                to_address,
                to_account,
                offchain_parameters=offchain_parameters,
                info=info,
            )

            # Submit the nft transfer
            transfer_result, response = await transfer_nft(
                cfg,
                secret,
                amount=args.amount,
                toAccount=to_account,
                toAddress=to_address,
                nftInfo=nft_info,
                eddsa_signature=eddsa_signature,
                ecdsa_signature=ecdsa_signature,
                offchain_parameters=offchain_parameters,
                test_mode=args.test,
                info=info,
            )

            if transfer_result == TransferResult.SUCCESS:
                print(
                    f"{i+1}/{cfg.tosCount} {i+1}: Successful Transfer! (tx hash: {response['hash']}, to: {to_address}, nftId: {nft_info['nftId']})"
                )
                offchain_parameters["storage_id"]["offchainId"] += 2
            elif transfer_result == TransferResult.FAILED:
                print(
                    f"{i+1}/{cfg.tosCount} {i+1}: Transfer FAILED... (to: {to_address}, nftId: {nft_info['nftId']})"
                )
            elif (
                transfer_result == TransferResult.FEE_INVALID
            ):  # Invalid fees, exit cleanly
                print(
                    f"{i+1}/{cfg.tosCount} {i+1}: Transfer FAILED due to invalid fee. Was there a gas spike? (to: {to_address}, nftId: {nft_info['nftId']})"
                )
                print(
                    f"Fees increased above the limit of {get_token_value(cfg.feeLimit, cfg.feeSymbol)}{cfg.feeSymbol}, aborting..."
                )
                sys.exit(transfer_result)
            elif transfer_result == TransferResult.TESTMODE:
                print(
                    f"{i+1}/{cfg.tosCount} {i+1}: Skipping transfer (test mode) (to: {to_address}, nftId: {nft_info['nftId']})"
                )

            transfer_info.append(info)
        
            set_progress_for_ui("transfer", i + 1, cfg.tosCount)

        if not all(cfg.tosRawValid):
            invalid_to_addresses = [
                to for (to, valid) in zip(cfg.tosRaw, cfg.tosRawValid) if not valid
            ]
            print(f"Skipped {len(invalid_to_addresses)} invalid to addresses:")
            print("\n".join(invalid_to_addresses))
    finally:
        with open(paths.transfer_info, "w+") as f:
            json.dump(transfer_info, f, indent=4)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
