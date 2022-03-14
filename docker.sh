#!/usr/bin/env bash

name="loopymint2"

docker build --tag $name .
docker run -it --rm --name $name -v $PWD:/$name:rw $name
