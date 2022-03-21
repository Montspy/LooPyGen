# LooPyGen

This is the unofficial Loopring Python Image Generator and Minter on Layer 2.

The system utilizes a few parts:

1. Python to generate images and metadata according to the standards for the new Layer 2 marketplace.
2. NodeJS to pre-calculate CIDs on images and metadata files.
3. Python to run the batch minting process.
4. PHP to tie everything together.

Checkout the [Wiki pages](https://github.com/sk33z3r/loopymint2/wiki/Getting-Started) for up to date info on using the app!

Checkout the [issues section](https://github.com/sk33z3r/loopymint2/issues) to report any problems, make feature requests, or keep up with our progress!

## Basic Usage

### Building the Environment

```shell
./docker.sh up
```

### Image Generator Commands

**Basic run:**

```shell
./docker.sh generator --count XXX
```

**Delete previously generated images before generating a new set:**

```shell
./docker.sh generator --empty --count XXX
```

### Metadata JSON Generator Commands

**Basic run, after generating images:**

```shell
./docker.sh metadata
```

**Delete previously generated metadata before generating a new set:**

```shell
./docker.sh --empty metadata
```

### Minting Commands

**Batch mint a collection:**

```shell
./docker.sh mintcollection --amount 1
```

**Mint a specific set of IDs:**

```shell
./docker.sh mintcollection --start startID --end endID --amount 1
```

**Mint a single CID:**

```shell
./docker.sh mint --cid Qmau1Sx2hLTkLmXsu2dD28yMZtL3Pzs2uKqP2MeHZPm93V --amount 100
```

**Test run a mint (shows only what the script _would_ do, but doesn't actually do it):**

```shell
./docker.sh mintcollection --testmint --amount 100
```

### CID Calculator Commands

**CIDv0:**

```shell
./docker.sh cid ./path/to/file/in/repo
```

**CIDv1:**

```shell
./docker.sh cid --cid-version=1 ./path/to/file/in/repo
```

## dotenv

First you need to export your account to get the necessary details to fill in the dotenv file.

Go to loopring.io -> Security -> Export Account and copy the JSON provided into a safe space.

⚠️ **DO NOT SHARE THIS INFO WITH ANYONE** ⚠️

The output should look something like this:

```json
{
    "address": "0x000000000000000000000000000000000000000000000",
    "accountId": 12345,
    "level": "",
    "nonce": 1,
    "apiKey": "randomlettersandnumbersohmygod",
    "publicX": "0x000000000000000000000000000000000000000000000",
    "publicY": "0x000000000000000000000000000000000000000000000",
    "privateKey": "0x000000000000000000000000000000000000000000000"
}
```

Copy `.env.example` and rename it to `.env`, then edit the fields to match your exported data.

| Variable               | Description                                                                                                      | Accepted Values                     |
|------------------------|------------------------------------------------------------------------------------------------------------------|-------------------------------------|
| ARTIST_NAME            | Some name so people know who you are                                                                             | String of words, spaces, or numbers |
| MINTER                 | `address`                                                                                                        | See your account export             |
| ROYALTY_PERCENTAGE     | Percentage for royalty payouts to the minter                                                                     | 0 - 10                              |
| COLLECTION_DESCRIPTION | A description to put into metadata                                                                               | String of words, spaces, or numbers |
| SEED                   | A custom generation seed, generated for you if you leave it blank                                                | String of words, spaces, or numbers |
| SOURCE_FILES           | Custom folder where your source layers are. If blank, defaults to lowercase, no space version of COLLECTION_NAME | Path to a folder                    |
| LOOPRING_API_KEY       | `apiKey`                                                                                                         | See your account export             |
| LOOPRING_PRIVATE_KEY   | `privateKey`                                                                                                     | See your account export             |
| ACCT_ID                | `accountId`                                                                                                      | See your account export             |
| NFT_TYPE               | EIP1155 or EIP721                                                                                                | 0 (1155) or 1 (721)                 |
| FEE_TOKEN_ID           | ETH or LRC                                                                                                       | 0 (ETH) or 1 (LRC)                  |
