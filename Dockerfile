FROM python:3.9 AS python_modules
# add openssh and clean
RUN apt-get -y update &&\
    apt-get -y install --no-install-recommends libjpeg-dev gcc libc-dev &&\
    apt-get clean &&\
    rm -rf /var/lib/apt/lists/*

# install python modules
ADD generator/requirements.txt /generator.txt
ADD generator/hello_loopring/requirements.txt /hello_loopring.txt
RUN pip install -r /generator.txt -r /hello_loopring.txt

FROM node:16 as node_modules
# Set workdir initially just for npm to install
WORKDIR /usr/src/app
# Install modules
ADD ipfs-hash/package*.json ./
RUN npm install --production
# Install app files
ADD ipfs-hash/* ./

FROM php:fpm AS php
# install python3.9
RUN apt-get update &&\
    apt-get -y install --no-install-recommends npm git unzip wget &&\
    apt-get -y clean &&\
    apt-get -y autoremove &&\
    rm -rf /var/lib/apt/lists/*
# install ffmpeg
RUN wget --no-check-certificate https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v4.4.1/ffmpeg-4.4.1-linux-64.zip &&\
    wget --no-check-certificate https://github.com/ffbinaries/ffbinaries-prebuilt/releases/download/v4.4.1/ffprobe-4.4.1-linux-64.zip
RUN unzip ffmpeg-4.4.1-linux-64.zip &&\
    unzip ffprobe-4.4.1-linux-64.zip &&\
    chmod +x ffmpeg ffprobe &&\
    mv ffmpeg ffprobe /usr/local/bin/ &&\
    rm ffmpeg-4.4.1-linux-64.zip ffprobe-4.4.1-linux-64.zip
# get compiled modules from previous stages
COPY --from=python_modules /usr/local/lib/python3.9 /usr/lib/python3.9
COPY --from=node_modules /usr/src/app /usr/src/app
# get composer
COPY --from=composer /usr/bin/composer /usr/bin/composer
# add the python files for the game
ADD dockerfiles/scripts/* /usr/local/bin/
# link cid calculator
RUN ln -s /usr/src/app/cli.js /usr/bin/cid
# finish up container
WORKDIR /var/www/html
