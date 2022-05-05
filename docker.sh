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

reload() {
    docker-compose down
    checkDotenv
    docker builder prune -f
    docker-compose up -d --build --force-recreate
}

migrate() {
    for i in $(ls images); do
        mkdir -p collections/$i/{config,stats}
        mv images/$i/*.json collections/$i/config/
        mv images/$i collections/$i/config/source_layers
        mv generated/$i/{gen-stats.json,all-traits.json} collections/$i/stats/
        mv generated/$i/metadata-cids.json collections/$i/config/
        mv generated/$i/{images,metadata} collections/$i/
    done
    rm -r images generated
}

case $1 in
    build) docker-compose build;;
    reload) reload;;
    update) git pull --recurse-submodules && reload;;
    up)
        checkDotenv
        if [ $2 = "prod" ]; then
            docker-compose up -d react
        else
            docker-compose up -d
        fi
    ;;
    down) docker-compose down;;
    migrate) migrate;;
    *) docker-compose exec python $@;;
esac
