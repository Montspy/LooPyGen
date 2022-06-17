#!/usr/bin/env bash

version=$(cat .version)

read -r -d '' startup_msg <<EOF
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

if [ -f .env ]; then
    . .env
fi

if [ -z $HUB_TAG ]; then
    if $(git --version 2>/dev/null); then
        branch=$(git rev-parse --abbrev-ref HEAD | sed 's,/,-,g')
    else
        branch=$(cat .version)
    fi
    if [ $branch == "main" ]; then
        branch="latest"
    fi
    if [ -f .env ]; then
        cat .env | sed "s/^HUB_TAG=.*$/HUB_TAG=$branch/g" > .temp
        mv .temp .env
    fi
else
    branch=$HUB_TAG
    if [ $branch == "main" ]; then
        branch="latest"
    fi
fi

tag="sk33z3r/loopygen:$branch"

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

ci() {
    docker login -u "$HUB_USER" -p "$HUB_KEY" &&
    echo "Building image with tag: $tag"
    docker build -t $tag . &&
    docker push $tag &&
    docker logout
}

update() {
    git fetch &&
    git pull &&
    git submodule update --init --recursive &&
    reload
}

reload() {
    docker-compose down --remove-orphans
    remove_start_menu_shortcuts
    #checkDotenv
    install_start_menu_shortcuts
    docker-compose up -d --build --force-recreate
}

migrate() {
    # if the user has the old setup, migrate files
    if ls images; then
        echo "Old collection structure found, migrating files..."
        for i in $(ls images); do
            mkdir -p collections/$i/{config,stats,ipfs}
            mv images/$i/*.json collections/$i/config/
            mv images/$i collections/$i/config/source_layers
            mv generated/$i/{gen-stats.json,all-traits.json} collections/$i/stats/
            mv generated/$i/metadata-cids.json collections/$i/config/
            mv generated/$i/{images,thumbnails,metadata} collections/$i/ipfs/
        done
        echo "...cleaning up..."
        rm -r images generated
        echo "...done!"
    else
        echo "Old collection structure not found, skipping file migration."
    fi
    # if the minter folder still exists, delete it
    if ls minter; then rm -r minter; fi
}

install_start_menu_shortcuts() {
    if [ ! -z ${WSL_DISTRO_NAME+x} ]; then
        start_menu_dir="`wslpath "$(wslvar USERPROFILE)"`/AppData/Roaming/Microsoft/Windows/Start Menu/Programs"    # Get Start Menu path for the current user
        [ -d "$start_menu_dir" ] && ([ -d "$start_menu_dir/LooPyGen" ] || mkdir "$start_menu_dir/LooPyGen")         # If Start Meny exists, create LooPyGen folder in it
        cp -a dockerfiles/assets/win_shortcuts/. "$start_menu_dir/LooPyGen"                                         # Copy our shortcuts in it
        (cd "$start_menu_dir/LooPyGen" && sed -i "s/DISTRO/${WSL_DISTRO_NAME}/g" "LooPyGen Folder.noturl" && sed -i "s/USERNAME/${USER}/g" "LooPyGen Folder.noturl")    # Update the LooPyGen folder URL based on distro name and user
        (cd "$start_menu_dir/LooPyGen" && find . -type f -name "*.noturl" -exec sh -c 'for pathname do mv -- "$pathname" "${pathname%.noturl}".url; done' sh {} + )     # Rename .noturl to .url (workaround Windows caching .url files at creation)
        grep -qxF 'cd ~/LooPyGen' ~/.bashrc || echo 'cd ~/LooPyGen' >> ~/.bashrc    # Default wsl bash to ~/LooPyGen
        echo "Shortcuts installed";
        [ ! -d "$start_menu_dir" ] && echo "Start menu directory not found";
    else
        echo "Not running inside WSL";
    fi
}

remove_start_menu_shortcuts() {
    if [ ! -z ${WSL_DISTRO_NAME+x} ]; then
        start_menu_dir="`wslpath "$(wslvar USERPROFILE)"`/AppData/Roaming/Microsoft/Windows/Start Menu/Programs"    # Get Start Menu path for the current user
        [ -d "$start_menu_dir" ] && ([ ! -d "$start_menu_dir/LooPyGen" ] || rm -rf "$start_menu_dir/LooPyGen")      # Delete Start Menu "LooPyGen folder"
        sed -i '/cd ~\/LooPyGen/d' ~/.bashrc
        echo "Shortcuts removed"
        [ ! -d "$start_menu_dir" ] && echo "Start menu directory not found"
    else
        echo "Not running inside WSL";
    fi
}

usage() {
cat <<EOF

    LooPyGen Docker Environment Utility Script

    Usage: $0 [command]

    Commands:
    build                 | Build the container locally
    reload                | Tear down and rebuild the container
    update                | Update and reload the repository
    up                    | Spin up container
    down                  | Tear down container
    install_start_menu    | Install Windows Start Menu
    remove_start_menu     | Remove Windows Start Menu
    migrate               | Migrate collection files
    container             | Runs commands for the container, meant for Docker
    ci                    | Build, tag, and push container to Docker Hub
    {command}             | Run a command inside the container

EOF
}

case $1 in
    build) docker-compose build;;
    reload) reload;;
    update) update;;
    up)
        #checkDotenv
        install_start_menu_shortcuts
        docker-compose up -d
    ;;
    install_start_menu) install_start_menu_shortcuts;;
    remove_start_menu) remove_start_menu_shortcuts;;
    down) docker-compose down;;
    migrate) migrate;;
    container)
        echo "[startup] Running startup job..."
        echo "[startup] Set permissions..."
        mkdir -p .secrets
        chmod -R 777 .secrets
        chmod 777 /loopygen
        list=""
        for f in $(ls); do
            if [ $f = 'python' ] || [ $f = 'ipfs-hash' ] || [ $f = '.git' ]; then
                echo "[startup] Skipping $f"
            else
                list="$list $f"
            fi
        done &&
        chmod -R 777 $list
        echo "[startup] Starting PHP FPM..."
        php-fpm &
        echo "$startup_msg"
        echo "[LooPyGen v$(cat .version)] Server Running..."

        nginx -g "daemon off;"
    ;;
    ci) ci;;
    -h|-help|help) usage;;
    *)
        if ! $(docker ps -q --filter "name=loopygen" | grep -q .); then
            #checkDotenv
            docker-compose up -d
        fi
        docker-compose exec loopygen "$@"
    ;;
esac
