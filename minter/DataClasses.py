from typing import TypedDict
from dataclasses import dataclass

@dataclass
class Struct(dict):
    def __init__(self, d: dict = None):
        if d:
            for k,v in d.items():
                super().__setitem__(k,v)
    def __getattr__(self, name):
        if super().__contains__(name):
            return super().__getitem__(name)
        else:
            return None
    def __setattr__(self, name, value):
        return super().__setitem__(name, value)
    def __delattr__(self, name):
        return super().__delitem__(name)
    def __str__(self):
        return super().__str__()
    def __repr__(self):
        return super().__repr__()

class MintResponseData(TypedDict):
    hash: str
    nftTokenId: int
    nftData: str
    status: str
    isIdempotent: bool
    accountId: int
    storageId: int

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
    TESTMODE = 2

token_decimals = {'ETH': 18, 'LRC': 18, 'USDT': 6, 'DAI': 18, 'USDC': 6}