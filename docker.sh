#!/usr/bin/env bash

name="loopygen"

checkDotenv() {
    uid=$(id -u)
    gid=$(id -g)
    if [ ! -f .env ]; then
        touch .env
        echo "# AUTOMATICALLY SET, DO NOT EDIT" >> .env
        echo "UID=$uid" >> .env
        echo "GID=$gid" >> .env
    else
        cat .env | sed "s/^UID=.*$/UID=$uid/g" > .temp
        cat .temp | sed "s/^GID=.*$/GID=$gid/g" > .env
        rm .temp
    fi
}

case $1 in
    build) docker-compose build;;
    reload)
        checkDotenv
        docker-compose up -d --build --force-recreate
    ;;
    up)
        checkDotenv
        docker-compose up -d
    ;;
    down) docker-compose down;;
    *) docker-compose exec php $@;;
esac
