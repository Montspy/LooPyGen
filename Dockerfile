FROM python:3.9-alpine3.15 AS python_modules
# add openssh and clean
RUN apk --no-cache --update add build-base jpeg-dev libffi-dev

# install python modules
ADD python/requirements.txt /generator.txt
ADD python/hello_loopring/requirements.txt /hello_loopring.txt
RUN pip install -r /generator.txt -r /hello_loopring.txt

FROM node:16-alpine3.15 as node_modules
# Set workdir initially just for npm to install
WORKDIR /usr/src/app
# Install modules
ADD ipfs-hash/package*.json ./
RUN npm install --omit=dev
RUN npm install --location=global pkg
# Install app files, compile to native binary
ADD ipfs-hash/* ./
RUN pkg ./cli.js -o ./ipfs-cid-linux

FROM php:fpm-alpine3.15 AS php
# define workdir
WORKDIR /loopygen
# install python3.9 and ffmpeg
RUN apk --no-cache --update add python3 ffmpeg bash nginx
# get compiled modules from previous stages
COPY --from=python_modules /usr/local/lib/python3.9 /usr/lib/python3.9
COPY --from=node_modules /usr/src/app/ipfs-cid-linux /usr/bin/cid
# setup composer
# COPY --from=composer /usr/bin/composer /usr/bin/composer
# RUN composer require web-token/jwt-encryption --ignore-platform-reqs --no-cache
# add scripts
ADD dockerfiles/scripts/* /usr/local/bin/
# add nginx conf
ADD dockerfiles/nginx.conf /etc/nginx/http.d/default.conf
# add app files
ADD ./python ./python
ADD ./php ./php
ADD ./css ./css
ADD ./js ./js
ADD ./index.php ./index.php
ADD ./docker.sh ./docker.sh
RUN ls -l
# run nginx
EXPOSE 80
STOPSIGNAL SIGKILL
CMD ["./docker.sh", "container"]