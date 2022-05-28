#!/bin/sh

# Do not use within loopygen
cd /loopyminty
python3 minter.py --json output/metadata-cids.json $@
