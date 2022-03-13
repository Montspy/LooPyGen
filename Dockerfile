FROM python:3 AS build
# add openssh and clean
RUN apt-get -y update; \
    apt-get -y upgrade
RUN apt-get -y install libjpeg-dev gcc libc-dev
# upgrade pip
RUN pip install --upgrade pip
# install python modules
ADD dockerfiles/requirements.txt /
RUN pip install -r /requirements.txt

FROM python:3 AS run
# get compiled modules from pervious stage
COPY --from=build /usr/local/lib/python3.10 /usr/local/lib/python3.10
# add the python files for the game
ADD dockerfiles/generate.sh /usr/local/bin/generate
ADD dockerfiles/metadata.sh /usr/local/bin/metadata
# finish up container
WORKDIR /lrc-batch
CMD ["bash"]
