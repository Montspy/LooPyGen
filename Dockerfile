FROM python:3.9-alpine3.15 AS python_modules
# add openssh and clean
RUN apk --no-cache --update add build-base jpeg-dev libffi-dev

# install python modules
ADD generator/requirements.txt /generator.txt
ADD generator/hello_loopring/requirements.txt /hello_loopring.txt
RUN pip install -r /generator.txt -r /hello_loopring.txt

FROM node:16-alpine3.15 as node_modules
# Set workdir initially just for npm to install
WORKDIR /usr/src/app
# Install modules
ADD ipfs-hash/package*.json ./
RUN npm install --production
RUN npm install -g pkg
# Install app files, compile to native binary
ADD ipfs-hash/* ./
RUN pkg ./cli.js -o ./ipfs-cid-linux

FROM php:fpm-alpine3.15 AS php
# install python3.9 and ffmpeg
RUN apk --no-cache --update add python3 ffmpeg
# get compiled modules from previous stages
COPY --from=python_modules /usr/local/lib/python3.9 /usr/lib/python3.9
COPY --from=node_modules /usr/src/app/ipfs-cid-linux /usr/bin/cid
# get composer
COPY --from=composer /usr/bin/composer /usr/bin/composer
# add the python files for the game
ADD dockerfiles/scripts/* /usr/local/bin/
# finish up container
WORKDIR /var/www/html