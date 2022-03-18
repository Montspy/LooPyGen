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
./docker.sh mint --cid Qmau1Sx2hLTkLmXsu2dD28yMZtL3Pzs2uKqP2MeHZPm93V --count 100
```

### Run the CID calculator

```plaintext
./docker.sh cid --cid-version=0 ./path/to/file/in/repo
```

or

```plaintext
./docker.sh cid --cid-version=1 ./path/to/file/in/repo
```
