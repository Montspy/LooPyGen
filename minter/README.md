# LoopMintPy

This is a **Python3** adaptation of fudgey's [LoopMintSharp](https://github.com/fudgebucket27/LoopMintSharp).
Now with batch minting!

## Install

Using Docker:

```shell
git clone --recurse-submodules https://github.com/Montspy/LooPyMinty.git
./docker.sh build
```

## dotenv

First you need to export your account to get the necessary details to fill in the dotenv file.

Go to loopring.io -> Security -> Export Account and copy the JSON provided into a safe space.

**⚠️ DO NOT SHARE THIS INFO WITH ANYONE ⚠️**

The output should look something like this:

```json
{
    "address": "0x000000000000000000000000000000000000000000000",
    "accountId": 12345,
    "level": "",
    "nonce": 1,
    "apiKey": "jKGjglkSlkdglksjdglkjsdgLHlhGksldjhgalHGLghlgg9dgHLGHSDgh",
    "publicX": "0x000000000000000000000000000000000000000000000",
    "publicY": "0x000000000000000000000000000000000000000000000",
    "privateKey": "0x000000000000000000000000000000000000000000000"
}
```

Copy `.env.example` and rename it to `.env`, then edit the fields to match your exported data.

| Variable               | Required for | Description                                  | Accepted Values         |
|------------------------|--------------|----------------------------------------------|-------------------------|
| LOOPRING_PRIVATE_KEY   | Mint      | `privateKey`                                 | See your account export !DO NOT SHARE WITH ANYONE! |
| NFT_TYPE               | Mint      | EIP1155 or EIP721                            | 0 (1155) or 1 (721)     |
| FEE_TOKEN_ID           | Mint      | ETH or LRC                                   | 0 (ETH) or 1 (LRC)      |
| MINTER                 | Mint + Prepare | `address`                                    | L2 address, account ID or ENS |
| ROYALTY_PERCENTAGE     | Mint + Prepare | Percentage for royalty payouts to the minter | 0 - 10                  |
| COLLECTION_NAME        | No           | The pretty name of your NFT collection       | Text                    |
| COLLECTION_DESCRIPTION | No           | A description of the NFT collection          | Text                    |
| ARTIST                 | No           | The name of the NFT artist                   | Text                    |

## Usage

### Preparing metadata and CIDs
```shell
> ./docker.sh prepare -h
usage: prepare.py [-h] (--file FILE | --idir IDIR) [--metadata] [--overwrite]

optional arguments:
  -h, --help   show this help message and exit
  --file FILE  Specify an input file
  --idir IDIR  Specify an input directory
  --metadata   Generate metadata templates instead of the CIDs list
  --overwrite  Overwrite the metadata files and all metadata fields
```

### Minting
```shell
> ./docker.sh mint -h
usage: minter.py [-h] [-n AMOUNT] [--testmint] [-V] [--noprompt] [-c CID] [-j JSON] [-s START] [-e END]

optional arguments:
  -h, --help            show this help message and exit
  -n AMOUNT, --amount AMOUNT
                        Specify the mint amount per NFT
  --testmint            Skips the mint step
  -V, --verbose         Verbose output
  --noprompt            Skip all user prompts

Single mint:
  Use these options to mint a single NFT:

  -c CID, --cid CID     Specify the CIDv0 hash for the metadata to mint

Batch mint:
  Use these options to batch mint multiple NFTs:

  -j JSON, --json JSON  Specify a json file containing a list of CIDv0 hash to batch mint
  -s START, --start START
                        Specify the the starting ID to batch mint
  -e END, --end END     Specify the last ID to batch mint
```

## Examples
### Generate metadata templates for an NFT collection

```shell
./docker.sh prepare --idir ./images/ --metadata --overwrite
```
`./images/` should contain only the images to prepare metadata templates for.
The `output/metadata` directory will be created with metadata JSON files for each image.

Once edited with all required information, we can generate the list of CIDs for those metadata files:
```shell
./docker.sh prepare --idir ./output/metadata/
```
The `output/metadata-cids.json` file will be created with a list of CIDs, one for each metadata file.
**Every time** the metadata files in `output/metadata` are modified, you need to re-run this command to update the CID!

Once you are ready to mint your collection, you can follow the following commands.

### Batch mint NFTs

Mint your whole collection with: 

```shell
./docker.sh mint --json ./output/metadata-cids.json --count 1
```
Or mint only part of the collection with --start and --end to specify IDs
```shell
./docker.sh mint --json ./output/metadata-cids.json --count 1 --start 1 --end 10
```

### Mint a single NFT

To mint a single NFT, you can still use:

```shell
./docker.sh mint --cid QmdmRoWVU4PV9ZCi1khprtX2YdAzV9UEFN5igZZGxPVAa4 --count 100
```

### Content of `metadata-cids.json`
`metadata-cids.json` should be an array of dict with ID and CID:
```json
[
    {
        "ID": 1,
        "CID": "Qmau1Sx2hLTkLmXsu2dD28yMZtL3Pzs2uKqP2MeHZPm93V"
    },
    {
        "ID": 2,
        "CID": "QmSyhgNxWWEQSVTjgxzd4F6xHJ2LLDFzaTdX6wV5qFzenX"
    },
    {
        "ID": 3,
        "CID": "QmYETprnpLtVXxydrzgCSrz6uC1swmS31rqupazdPWenE6"
    }
]
```