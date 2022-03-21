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
    sed -i "s/^UID=.*$/UID=$uid/g" .env
    sed -i "s/^GID=.*$/GID=$gid/g" .env
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
