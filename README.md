# LooPyGen

This is the unofficial Loopring Python Image Generator and Minter on Layer 2.

⚠️ **NEVER SHARE YOUR PRIVATE KEY OR API KEY WITH ANYONE** ⚠️

## New Wiki

https://wiki.ezl2.app/en/quick-start

Checkout the [issues section](https://github.com/sk33z3r/LooPyGen/issues) to report any problems, make feature requests, or keep up with our progress!

## Basic Usage

### Building the Environment

```shell
./docker.sh up
```

### Setup your config and collection

Open a browser and go to: [http://localhost:8080](http://localhost:8080)

### Image Generator Commands

Basic run:

```shell
./docker.sh generate --count XXX
```

Delete previously generated images before generating a new set:

```shell
./docker.sh generate --empty --count XXX
```

Start generating from a specific ID number:

```shell
./docker.sh generate --count XXX --id YY
```

If you have a beefy computer, you can try to generate images simultaneously to speed up the process:

```shell
./docker.sh generate --count XXX --threaded
```

### Metadata JSON Generator Commands

Basic run, after generating images:

```shell
./docker.sh metadata
```

Delete previously generated metadata before generating a new set:

```shell
./docker.sh metadata --empty
```

### Minting Commands

Batch mint a collection:

```shell
./docker.sh mint --name <my_nft_collection> --amount 1
```

Mint a specific set of IDs:

```shell
./docker.sh mint --name <my_nft_collection> --start <startID> --end <endID> --amount 1
```

Mint a single CID:

```shell
./docker.sh mint --cid Qmau1Sx2hLTkLmXsu2dD28yMZtL3Pzs2uKqP2MeHZPm93V --amount 100
```

Test run a mint (shows only what the script _would_ do, but doesn't actually do it):

```shell
./docker.sh mint --name <my_nft_collection> --testmint --amount 100
```

### CID Calculator Commands

CIDv0:

```shell
./docker.sh cid ./path/to/file/in/repo
```

CIDv1:

```shell
./docker.sh cid --cid-version=1 ./path/to/file/in/repo
```
