FROM python:3.9 AS python_modules
RUN apt-get -y update; \
    apt-get -y upgrade
RUN apt-get -y install libjpeg-dev gcc libc-dev
# upgrade pip
RUN pip install --upgrade pip
# install python modules
ADD requirements.txt /
ADD hello_loopring/requirements.txt /loopring.txt
RUN pip install -r /requirements.txt -r /loopring.txt

FROM alpine:3.14 AS run
# Set workdir initially just for npm to install
WORKDIR /usr/src/app

# Install openssl and npm
RUN apk add --update --no-cache openssl npm

# Install python3.9
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools

# Install the app from npm directly
RUN npm i --only=production pure-ipfs-only-hash
RUN ln -s /usr/src/app/node_modules/pure-ipfs-only-hash/cli.js /usr/bin/cid

# get compiled modules from previous stages
COPY --from=python_modules /usr/local/lib/python3.9 /usr/lib/python3.9

# Add the cli files
ADD dockerfiles/prepare.sh /usr/local/bin/prepare
ADD dockerfiles/mint.sh /usr/local/bin/mint
ADD dockerfiles/mintcollection.sh /usr/local/bin/mintcollection

CMD ["sh"]