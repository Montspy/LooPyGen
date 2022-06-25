#!/usr/bin/env bash

name="loopygen-cli"
tag="sk33z3r/$name"

update() {
cat <<EOF
+-------------------------------------------------+
|                                                 |
|   ░▒█░░░░▄▀▀▄░▄▀▀▄░▒█▀▀█░█░░█░▒█▀▀█░█▀▀░█▀▀▄    |
|   ░▒█░░░░█░░█░█░░█░▒█▄▄█░█▄▄█░▒█░▄▄░█▀▀░█░▒█    |
|   ░▒█▄▄█░░▀▀░░░▀▀░░▒█░░░░▄▄▄▀░▒█▄▄▀░▀▀▀░▀░░▀    |
|                                                 |
|           Created and Maintained By:            |
|                  sk33z3r.eth                    |
|                  itsmonty.eth                   |
|                                                 |
+-------------------------------------------------+
EOF
echo "Updating LooPyGen CLI..."
docker pull $tag
echo "...done!"
}

usage() {
cat <<EOF

    LooPyGen CLI Utility Script

    Usage: $0 [command]

    Commands:
    update                | Pull the latest image
    secrets               | Force remove the secrets Docker volume
    {command}             | Run a command inside the container

EOF
}

case $1 in
    update) update;;
    secrets) docker volume rm -f $name;;
    -h|-help|help) usage;;
    cid) # only mount local directory and set a new workdir inside the container
        docker run -it --rm --name $name \
            -w /scan \
            -v $PWD:/scan \
            $tag "$@"
    ;;
    *) # run a command inside a self-destructing container
        docker run -it --rm --name $name \
            -v $name:/loopygen/.secrets \
            -v $PWD/collections:/loopygen/collections:rw \
            $tag "$@"
    ;;
esac
