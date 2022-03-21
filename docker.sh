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
    cat .env | sed "s/^UID=.*$/UID=$uid/g" > .temp
    cat .temp | sed "s/^GID=.*$/GID=$gid/g" > .env
    rm .temp
}

case $1 in
    build) docker-compose build;;
    reload)
        checkDotenv
        getIDs
        docker-compose up -d --build --force-recreate
    ;;
    up)
        checkDotenv
        getIDs
        docker-compose up -d
    ;;
    down) docker-compose down;;
    *) docker-compose exec php $@;;
esac
