# LRC Batch Mint System

This system utilizes a few parts.

1. Python to generate images and metadata according to the standards for the new Layer 2 marketplace.
2. Python to run the batch minting process

# Setting up the generator

Edit the `traits.py` file to include the number of traits you wish to have, mapping the same information you see there.

# Running the engine

For now this is based in Docker, so [install that first.](https://docs.docker.com/engine/install/)

Now run `./docker.sh` to setup a python environment with the scripts ready to go:

```shell
$ ./docker.sh
Sending build context to Docker daemon  4.455MB
Step 1/8 : FROM python:3.8-slim-buster
 ---> 5cc8cb0c433a
Step 2/8 : RUN pip install --upgrade pip
 ---> Using cache
 ---> c41a43e68ccf
Step 3/8 : RUN apt-get -y update;     apt-get -y upgrade
 ---> Running in b0de1ea0fcb2
Get:1 http://security.debian.org/debian-security buster/updates InRelease [65.4 kB]
Get:2 http://deb.debian.org/debian buster InRelease [122 kB]
Get:3 http://security.debian.org/debian-security buster/updates/main amd64 Packages [316 kB]
...
Removing intermediate container 5a635f977c14
 ---> 29f50c57b0c1
Step 12/12 : CMD ["bash"]
 ---> Running in d0b767026eb4
Removing intermediate container d0b767026eb4
 ---> 5e6e99aaa565
Successfully built 5e6e99aaa565
Successfully tagged lrc-batch:latest
root@43c30d60526a:/lrc-batch#
```

Once at this shell prompt, you can run the image generator and specify how many unique items you want to create.

```shell
$ generate 100
```

After you generate the images and upload to IPFS, you can then generate the metadata JSON files.

```shell
$ metadata
```
