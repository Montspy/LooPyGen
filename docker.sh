#!/usr/bin/env bash

name="loopymint2"

case $1 in
    build) docker build --tag $name .;;
    *) docker run -it --rm --name $name -v $PWD:/$name:rw $name $@;;
esac