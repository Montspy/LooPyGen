#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "hello_loopring")))

from dotenv import load_dotenv
from pprint import pprint
import argparse
import asyncio
import json
import base58

from DataClasses import *
from LoopringMintService import LoopringMintService, NFTDataEddsaSignHelper, NFTEddsaSignHelper

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
        account = str(account).strip()
        if account[:2] == "0x":
            address = account
            id = await lms.getAccountId(address)
        elif account[-4:] == ".eth":
            address = await lms.resolveENS(account)
            id = await lms.getAccountId(address)
        else:
            id = int(account)
            address = await lms.getAccountAddress(id)
    return id, address

async def retry_async(coro, *args, timeout: float=3, retries: int=3, **kwds):
    for attempts in range(retries):
        try:
            return await asyncio.wait_for(coro(*args, **kwds), timeout=timeout)
        except asyncio.TimeoutError:
            print("Retrying... " + str(attempts))

async def eternity(s: float):
    await asyncio.sleep(s)

# Build config dictionnary
async def load_config(args, paths: Struct):
    cfg = Struct()
    secret = Struct()   # Split to avoid leaking keys to console or logs

    if args.loopygen and args.name: # Batch minting a generated collection of NFTs from LooPyGen
        with open(paths.traits) as f:
            traits_json = json.load(f)
        traits =  Struct(traits_json)
        with open(paths.config) as f:
            config_json = json.load(f)
        loopygen_cfg = Struct(config_json)
        secret.loopringPrivateKey = loopygen_cfg.private_key
        cfg.minter                = loopygen_cfg.minter
        cfg.royalty               = traits.royalty_address
        cfg.nftType               = int(loopygen_cfg.nft_type)
        cfg.royaltyPercentage     = int(traits.royalty_percentage)
        cfg.maxFeeTokenId         = int(loopygen_cfg.fee_token)
    elif args.loopygen and args.json: # Batch minting a folder of NFTs from LooPyGen
        with open(paths.config) as f:
            config_json = json.load(f)
        loopygen_cfg = Struct(config_json)
        secret.loopringPrivateKey = loopygen_cfg.private_key
        cfg.minter                = loopygen_cfg.minter
        cfg.royalty               = loopygen_cfg.minter
        cfg.nftType               = int(loopygen_cfg.nft_type)
        cfg.royaltyPercentage     = int(os.getenv("ROYALTY_PERCENTAGE"))
        cfg.maxFeeTokenId         = int(loopygen_cfg.fee_token)
    else:   # Minting from LooPyMinty
        secret.loopringPrivateKey = os.getenv("LOOPRING_PRIVATE_KEY")
        cfg.minter                = os.getenv("MINTER")
        cfg.royalty               = os.getenv("ROYALTY_ADDRESS")
        cfg.nftType               = int(os.getenv("NFT_TYPE"))
        cfg.royaltyPercentage     = int(os.getenv("ROYALTY_PERCENTAGE"))
        cfg.maxFeeTokenId         = int(os.getenv("FEE_TOKEN_ID"))

    cfg.validUntil            = 1700000000
    cfg.nftFactory            = "0xc852aC7aAe4b0f0a0Deb9e8A391ebA2047d80026"
    cfg.exchange              = "0x0BABA1Ad5bE3a5C0a66E7ac838a129Bf948f1eA4"
    
    # Resolve ENS, get account_id and ETH address
    cfg.minterAccount, cfg.minterAddress = await retry_async(get_account_info, cfg.minter, retries=3)
    assert cfg.minterAddress and cfg.minterAccount, f"Invalid minter: {cfg.minter} aka {cfg.minterAddress} (account ID {cfg.minterAccount})"
    if cfg.royalty:
        cfg.royaltyAccount, cfg.royaltyAddress = await retry_async(get_account_info, cfg.royalty, retries=3)
        assert cfg.royaltyAddress and cfg.royaltyAccount, f"Invalid royalty account: {cfg.royalty} aka {cfg.royaltyAddress} (account ID {cfg.royaltyAddress})"

    assert secret.loopringPrivateKey, "Missing private key (LOOPRING_PRIVATE_KEY)"
    assert cfg.nftType in [0, 1], f"Invalid NFT type (NFT_TYPE): {cfg.nftType}"
    assert cfg.royaltyPercentage in range(0, 11), f"Invalid royalty percentage [0-10] (ROYALTY_PERCENTAGE): {cfg.royaltyPercentage}"
    assert cfg.maxFeeTokenId in range(len(token_decimals)), f"Missing or invalid fee token ID (FEE_TOKEN_ID): {cfg.maxFeeTokenId}"

    if secret.loopringPrivateKey[:2] != "0x":
        secret.loopringPrivateKey = "0x{0:0{1}x}".format(int(secret.loopringPrivateKey), 64)
    
    return cfg, secret

# Parse CLI arguments
def parse_args():
    # check for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--amount", help="Specify the mint amount per NFT", type=int)
    parser.add_argument("--testmint", help="Skips the mint step", action='store_true')
    parser.add_argument("-V", "--verbose", help="Verbose output", action='store_true')
    parser.add_argument("--noprompt", help="Skip all user prompts", action='store_true')
    parser.add_argument("--loopygen", help=argparse.SUPPRESS, action='store_true')
    parser.add_argument("--name", help=argparse.SUPPRESS, type=str)

    single_group = parser.add_argument_group(title="Single mint", description="Use these options to mint a single NFT:")
    single_group.add_argument("-c", "--cid", help="Specify the CIDv0 hash for the metadata to mint", type=str)

    batch_group = parser.add_argument_group(title="Batch mint", description="Use these options to batch mint multiple NFTs:")
    batch_group.add_argument("-j", "--json", help="Specify a json file containing a list of CIDv0 hash to batch mint", type=str)
    batch_group.add_argument("-s", "--start", help="Specify the the starting ID to batch mint", type=int)
    batch_group.add_argument("-e", "--end", help="Specify the last ID to batch mint", type=int)
    args = parser.parse_args()

    # CID sources
    assert args.json or args.cid or (args.loopygen and args.name), "Missing --cid or --json argument, please provide one"

    # LooPyGen specifics
    if not args.json and not args.cid and (args.loopygen and args.name):
        args.json = os.path.join("./collections", args.name, "config", "metadata-cids.json")
        args.cid = None
    # END LooPyGen specifics

    if args.json:
        assert os.path.exists(args.json), f"JSON file not found: {args.json}"
    if args.cid:
        assert args.cid[:2] == "Qm", f"Invalid cid: {args.cid}" # Support CIDv0 only
    
    # Mint amount
    if not args.amount:
        args.amount = int(os.getenv("AMOUNT") or 1)
    
    # ID selection (start/end)
    if not args.start:
        args.start = 1
    if args.end:
        assert args.start <= args.end, f"start cannot be greater than end: {args.start} > {args.end}"

    if args.cid and (args.start or args.end):
        print("Ignoring start and end arguments with single CID minting")

    # Test mint mode
    if args.testmint:
        print('Test mint mode enabled: Minting will be skipped and no fees will incur.')

    global VERBOSE
    VERBOSE = args.verbose

    return args

# Estimate fees for a batch of NFTs from offchain fees
def estimate_batch_fees(cfg, off_chain_fee, count):
    fee = int(off_chain_fee['fees'][cfg.maxFeeTokenId]['fee'])
    token_symbol = off_chain_fee['fees'][cfg.maxFeeTokenId]['token']
    discount = off_chain_fee['fees'][cfg.maxFeeTokenId]['discount']
    decimals = token_decimals[token_symbol]

    return count * fee * discount / (10 ** decimals), token_symbol

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
        api_key_resp = await lms.getUserApiKey(accountId=cfg.minterAccount, privateKey=secret.loopringPrivateKey)
        # log(f"User API key: {json.dumps(api_key_resp, indent=2)}")   # DO NOT LOG
        if api_key_resp is None:
            sys.exit("Failed to obtain user api key")

    secret.loopringApiKey = api_key_resp['apiKey']

async def get_offchain_parameters(cfg, secret):
    async with LoopringMintService() as lms:
        parameters = {}
        # Getting the storage id
        storage_id = await lms.getNextStorageId(apiKey=secret.loopringApiKey, accountId=cfg.minterAccount, sellTokenId=cfg.maxFeeTokenId)
        log(f"Storage id: {json.dumps(storage_id, indent=2)}")
        if storage_id is None:
            sys.exit("Failed to obtain storage id")
        
        parameters['storage_id'] = storage_id

        # Getting the token address
        counterfactual_nft_info = CounterFactualNftInfo(nftOwner=cfg.minterAddress, nftFactory=cfg.nftFactory, nftBaseUri="")
        counterfactual_nft = await lms.computeTokenAddress(apiKey=secret.loopringApiKey, counterFactualNftInfo=counterfactual_nft_info)
        log(f"CounterFactualNFT Token Address: {json.dumps(counterfactual_nft, indent=2)}")
        if counterfactual_nft is None:
            sys.exit("Failed to obtain token address")
            
        parameters['counterfactual_nft_info'] = counterfactual_nft_info
        parameters['counterfactual_nft'] = counterfactual_nft

        # Getting the offchain fee
        off_chain_fee = await lms.getOffChainFee(apiKey=secret.loopringApiKey, accountId=cfg.minterAccount, requestType=9, tokenAddress=counterfactual_nft['tokenAddress'])
        log(f"Offchain fee:  {json.dumps(off_chain_fee['fees'][cfg.maxFeeTokenId], indent=2)}")
        if off_chain_fee is None:
            sys.exit("Failed to obtain offchain fee")
            
        parameters['off_chain_fee'] = off_chain_fee

    return parameters

async def get_hashes_and_sign(cfg, secret, cid: str, amount: int, offchain_parameters: dict, info: dict):
    # Generate the nft id here
    nft_id = "0x" + base58.b58decode(cid).hex()[4:]    # Base58 to hex and drop first 2 bytes
    log(f"Generated NFT ID: {nft_id}")
    info['nft_id'] = nft_id

    # Generate the poseidon hash for the nft data
    # https://github.com/Loopring/loopring_sdk/blob/692d372165b5ea0d760e33e177d9003cc0dfb0f7/src/api/sign/sign_tools.ts#L704
    ntf_id_hi = int(nft_id[2:34], 16)   # Skip "0x" prefix
    nft_id_lo = int(nft_id[34:66], 16)
    inputs = [
        int(cfg.minterAddress, 16),
        cfg.nftType,
        int(offchain_parameters['counterfactual_nft']['tokenAddress'], 16),
        nft_id_lo,
        ntf_id_hi,
        cfg.royaltyPercentage
    ]
    hasher = NFTDataEddsaSignHelper()
    nft_data_poseidon_hash = hasher.hash(inputs)
    # plog(inputs)
    log("Hashed NFT data: 0x{0:0{1}x}".format(nft_data_poseidon_hash, 64))
    info['nft_data_poseidon_hash'] = "0x{0:0{1}x}".format(nft_data_poseidon_hash, 64)

    # Generate the poseidon hash for the remaining data
    # https://github.com/Loopring/loopring_sdk/blob/692d372165b5ea0d760e33e177d9003cc0dfb0f7/src/api/sign/sign_tools.ts#L899
    inputs = [
        int(cfg.exchange, 16),
        cfg.minterAccount,   # minterId
        cfg.minterAccount,   # toAccountId
        nft_data_poseidon_hash,
        amount,
        cfg.maxFeeTokenId,
        int(offchain_parameters['off_chain_fee']['fees'][cfg.maxFeeTokenId]['fee']),
        cfg.validUntil,
        offchain_parameters['storage_id']['offchainId']
    ]
    hasher = NFTEddsaSignHelper(private_key=secret.loopringPrivateKey)
    nft_poseidon_hash = hasher.hash(inputs)
    # plog(inputs)
    log("Hashed NFT payload: 0x{0:0{1}x}".format(nft_poseidon_hash, 64))
    info['nft_poseidon_hash'] = "0x{0:0{1}x}".format(nft_poseidon_hash, 64)

    eddsa_signature = hasher.sign(inputs)
    log(f"Signed NFT payload hash: {eddsa_signature}")
    info['eddsa_signature'] = eddsa_signature

    return nft_id, nft_data_poseidon_hash, eddsa_signature

async def mint_nft(cfg, secret, nft_data_poseidon_hash: str, nft_id: str, amount: int,
                   eddsa_signature: str, offchain_parameters: dict, test_mode: bool, info: dict):
    async with LoopringMintService() as lms:
        # Check if NFT exists (get the token nft data)
        nft_data = await lms.getNftData(nftDatas="0x{0:0{1}x}".format(nft_data_poseidon_hash, 64))
        log(f"Nft data: {json.dumps(nft_data, indent=2)}")
        info['nft_data'] = nft_data
        nft_exists = (lms.last_status == 200) and (nft_data is not None) and (len(nft_data) > 0)

        if nft_exists:
            return MintResult.EXISTS

        if test_mode:
            return MintResult.TESTMODE
        
        nft_mint_response = await lms.mintNft(
            apiKey=secret.loopringApiKey,
            exchange=cfg.exchange,
            minterId=cfg.minterAccount,
            minterAddress=cfg.minterAddress,
            toAccountId=cfg.minterAccount,
            toAddress=cfg.minterAddress,
            royaltyAddress=cfg.royaltyAddress,
            nftType=cfg.nftType,
            tokenAddress=offchain_parameters['counterfactual_nft']['tokenAddress'],
            nftId=nft_id,
            amount=str(amount),
            validUntil=cfg.validUntil,
            royaltyPercentage=cfg.royaltyPercentage,
            storageId=offchain_parameters['storage_id']['offchainId'],
            maxFeeTokenId=cfg.maxFeeTokenId,
            maxFeeAmount=offchain_parameters['off_chain_fee']['fees'][cfg.maxFeeTokenId]['fee'],
            forceToMint=False,
            counterFactualNftInfo=offchain_parameters['counterfactual_nft_info'],
            eddsaSignature=eddsa_signature
        )
        log(f"Nft Mint reponse: {nft_mint_response}")
        info['nft_mint_response'] = nft_mint_response

        if nft_mint_response is not None and lms.last_status == 200:
            return MintResult.SUCCESS
        else:
            return MintResult.FAILED

async def main():
    load_dotenv()

    # check for command line arguments
    try:
        args = parse_args()
    except Exception as err:
        sys.exit(f"Failed to initialize the minter: {err}")
    
    # Generate paths
    paths = Struct()
    paths.mint_info = os.path.join(os.path.dirname(__file__), "mint-info.json")
    paths.config = "./config.json"
    if args.loopygen and args.name:
        paths.traits = os.path.join("./collections", args.name, "config", "traits.json")

    # Parse all cids from JSON or command line
    if args.json:
        with open(args.json, 'r') as f:
            all_cids = json.load(f)
    elif args.cid:
        all_cids = [{"ID": 1, "CID": args.cid}]

    if not os.path.exists(os.path.dirname(paths.mint_info)):
        os.makedirs(os.path.dirname(paths.mint_info))

    mint_info = []
    mint_info.append({'args': vars(args)})

    approved_fees_prompt = args.noprompt

    try:
        filtered_cids = []  # CIDs filtered based on start/end

        cfg, secret = await load_config(args, paths)
        log("config dump:")
        plog(cfg)
        mint_info.append({'cfg': cfg})

        # Filter NFT by IDs and get off chain parameters
        for cid in all_cids:
            id = cid['ID']
            cid_hash = cid['CID']

            info = {'id': id, 'cid': cid_hash, 'amount': args.amount, 'skipped': True}

            # Filter NFT based on IDs
            if id < args.start or (args.end is not None and id > args.end):
                mint_info.append(info)
                continue

            filtered_cids.append(cid)
            info['skipped'] = False

            mint_info.append(info)

        if len(filtered_cids) == 0:
            print(f"Collection does not contain NFT IDs within start/end arguments provided, nothing to mint ({args.start}/{args.end})")
            sys.exit(0)

        # Get user API key
        print("Getting user API key... ", end='')
        await get_user_api_key(cfg, secret)
        print("done!")

        # Get storage id, token address and offchain fee
        print("Getting offchain parameters... ", end='')
        offchain_parameters = await get_offchain_parameters(cfg, secret)
        info['offchain_parameters'] = offchain_parameters
        print("done!")

        # Estimate fees and get user approval
        if not approved_fees_prompt:
            batch_fees, fees_symbol = estimate_batch_fees(cfg, offchain_parameters['off_chain_fee'], len(filtered_cids))
            log("--------")
            approved_fees_prompt = prompt_yes_no(f"Estimated L2 fees for minting {args.amount} copies of {len(filtered_cids)} NFTs: {batch_fees}{fees_symbol}, continue?", default="no")
            mint_info.append({'fee_approval': approved_fees_prompt, 'fee': batch_fees, 'token': fees_symbol})
            if not approved_fees_prompt: 
                sys.exit("Aborted by user")
        
        # NFT Mint sequence
        for i, cid in enumerate(filtered_cids):
            id = cid['ID']
            cid_hash = cid['CID']

            info = {'id': id, 'cid': cid_hash, 'amount': args.amount}

            # Generate Eddsa Signature
            nft_id, nft_data_poseidon_hash, eddsa_signature = await get_hashes_and_sign(cfg, secret, cid=cid_hash, amount=args.amount, offchain_parameters=offchain_parameters, info=info)
            
            # Submit the nft mint
            mint_result = await mint_nft(cfg,
                                         secret,
                                         nft_data_poseidon_hash=nft_data_poseidon_hash,
                                         nft_id=nft_id,
                                         amount=args.amount,
                                         eddsa_signature=eddsa_signature,
                                         offchain_parameters=offchain_parameters,
                                         test_mode=args.testmint,
                                         info=info)
            
            if mint_result == MintResult.SUCCESS:
                print(f"{i+1}/{len(filtered_cids)} NFT {id}: Successful Mint! ({args.amount}x {cid_hash})")
                offchain_parameters['storage_id']['offchainId'] += 2
            elif mint_result ==  MintResult.FAILED:
                print(f"{i+1}/{len(filtered_cids)} NFT {id}: Mint FAILED... ({args.amount}x {cid_hash})")
            elif mint_result ==  MintResult.EXISTS:
                print(f"{i+1}/{len(filtered_cids)} NFT {id}: Skipping mint (nft already exists) ({args.amount}x {cid_hash})")
            elif mint_result ==  MintResult.TESTMODE:
                print(f"{i+1}/{len(filtered_cids)} NFT {id}: Skipping mint (test mint mode) ({args.amount}x {cid_hash})")

            mint_info.append(info)
    finally:
        with open(paths.mint_info, 'w+') as f:
            json.dump(mint_info, f, indent=4)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
