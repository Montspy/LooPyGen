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

FROM node:16 as node_modules
# Set workdir initially just for npm to install
WORKDIR /usr/src/app
# Install container pre-requisites
RUN apt-get -y update; \
    apt-get -y upgrade
RUN apt-get -y install python3
# Install modules
ADD ipfs-hash/package*.json ./
RUN npm install
# Install app files
ADD ipfs-hash/* ./

FROM php:fpm AS php
# install python3.9
RUN dpkg --configure -a
RUN apt-get update; \
    apt-get -y upgrade
RUN apt-get install -y python3 npm ffmpeg
# get compiled modules from previous stages
COPY --from=python_modules /usr/local/lib/python3.9 /usr/lib/python3.9
COPY --from=node_modules /usr/src/app /usr/src/app
# add the python files for the game
ADD dockerfiles/scripts/* /usr/local/bin/
# link cid calculator
RUN ln -s /usr/src/app/cli.js /usr/bin/cid
# finish up container
WORKDIR /var/www/html
