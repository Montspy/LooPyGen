from typing import TypedDict
from dataclasses import dataclass

class MintResponseData(TypedDict):
    hash: str
    nftTokenId: int
    nftData: str
    status: str
    isIdempotent: bool
    accountId: int
    storageId: int

class TransferResponseData(TypedDict):
    hash: str
    status: str
    isIdempotent: bool

class ApiKeyResponse(TypedDict):
    apiKey: str

class CounterFactualNft(TypedDict):
    tokenAddress: str

class CounterFactualNftInfo(TypedDict):
    nftOwner: str
    nftFactory: str
    nftBaseUri: str

class Fee(TypedDict):
    token: str
    fee: str
    discount: float

class OffchainFee(TypedDict):
    gasPrice: str
    fees: 'list[Fee]'

class StorageId(TypedDict):
    orderId: int
    offchainId: int

class NftInfo(TypedDict):
    id: int
    accountId: int
    tokenId: int
    nftData: str
    tokenAddress: str
    nftId: str
    nftType: str
    total: int
    locked: int

class NftBalance(TypedDict):
    totalNum: int
    data: 'list[NftInfo]'

class NftData(TypedDict):
    nftData: str
    minter: str
    nftType: str
    tokenAddress: str
    nftId: str
    creatorFeeBips: int
    royaltyPercentage: int
    status: bool
    nftFactory: str
    nftOwner: str
    nftBaseUri: str
    royaltyAddress: str
    originalMinter: str

class MintResult:
    FAILED = -1
    SUCCESS = 0
    EXISTS = 1
    FEE_INVALID = 2
    TESTMODE = 99

class TransferResult:
    FAILED = -1
    SUCCESS = 0
    FEE_INVALID = 2
    TESTMODE = 99

class TransferMode:
    SINGLE=1
    RANDOM=2
    ORDERED=3

token_decimals = {'ETH': 18, 'LRC': 18, 'USDT': 6, 'DAI': 18, 'USDC': 6}