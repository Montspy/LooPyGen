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

### Build the Environment

```plaintext
./docker.sh up
```

### Run the image generator

```plaintext
./docker.sh generator --count XXX
```

### Run the metadata generator

```plaintext
./docker.sh metadata
```

### Batch mint the generated collection

```plaintext
./docker.sh mintcollection --count 100
```

### Mint only one CID

```plaintext
./docker.sh mint --cid Qmau1Sx2hLTkLmXsu2dD28yMZtL3Pzs2uKqP2MeHZPm93V --amount 100
```

### Run the CID calculator

```plaintext
./docker.sh cid --cid-version=0 ./path/to/file/in/repo
```

or

```plaintext
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
