#!/usr/bin/env bash

name="lrc-batch"

docker build --tag $name .
docker run -it --rm --name $name -v $PWD:/$name:rw $name
