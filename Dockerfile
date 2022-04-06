FROM python:3.9 AS python_modules
# add openssh and clean
RUN apt-get -y update; \
    apt-get -y upgrade
RUN apt-get -y install libjpeg-dev gcc libc-dev
# upgrade pip
RUN pip install --upgrade pip
# install python modules
ADD generator/requirements.txt /generator.txt
ADD minter/requirements.txt /minter.txt
ADD minter/hello_loopring/requirements.txt /hello_loopring.txt
RUN pip install -r /generator.txt -r /hello_loopring.txt -r /minter.txt

FROM node:16-alpine as node_modules
# Set workdir initially just for npm to install
WORKDIR /usr/src/app
# Install the app from npm directly
RUN npm i --only=production pure-ipfs-only-hash

FROM php:fpm-buster AS php
# install python3.9
RUN apt-get update; \
    apt-get -y upgrade
RUN apt-get install -y --fix-missing python3 npm ffmpeg git
# get compiled modules from previous stages
COPY --from=python_modules /usr/local/lib/python3.9 /usr/lib/python3.9
COPY --from=node_modules /usr/src/app/node_modules /usr/src/app/node_modules
# add the python files for the game
ADD dockerfiles/scripts/* /usr/local/bin/
# link cid calculator
RUN ln -s /usr/src/app/node_modules/pure-ipfs-only-hash/cli.js /usr/bin/cid
# finish up container
WORKDIR /var/www/html
