#!/usr/bin/env bash

name="loopygen"

checkDotenv() {
    if [ ! -f .env ]; then
        cp .env.example .env
    fi
}

getIDs() {
    uid=$(id -u)
    gid=$(id -g)
    cat .env | sed "s/^UID=.*$/UID=$uid/g" > .temp1
    cat .temp1 | sed "s/^GID=.*$/GID=$gid/g" > .env
    rm .temp1
}

checkDotenv
getIDs

case $1 in
    build) docker-compose build;;
    reload) docker-compose up -d --build --force-recreate;;
    up) docker-compose up -d;;
    down) docker-compose down;;
    *) docker-compose exec php $@;;
esac
