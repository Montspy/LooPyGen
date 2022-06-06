#!/usr/bin/env bash

name="loopygen"

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

update() {
    git fetch &&
    git pull &&
    git submodule update --init --recursive &&
    reload
}

reload() {
    docker-compose down --remove-orphans
    remove_start_menu_shortcuts
    checkDotenv
    install_start_menu_shortcuts
    docker builder prune -f
    docker-compose up -d --build --force-recreate
}

migrate() {
    for i in $(ls images); do
        mkdir -p collections/$i/{config,stats,ipfs}
        mv images/$i/*.json collections/$i/config/
        mv images/$i collections/$i/config/source_layers
        mv generated/$i/{gen-stats.json,all-traits.json} collections/$i/stats/
        mv generated/$i/metadata-cids.json collections/$i/config/
        mv generated/$i/{images,thumbnails,metadata} collections/$i/ipfs/
    done
    rm -r images generated
}

install_start_menu_shortcuts() {
    if [ ! -z ${WSL_DISTRO_NAME+x} ]; then
        start_menu_dir="`wslpath "$(wslvar USERPROFILE)"`/AppData/Roaming/Microsoft/Windows/Start Menu/Programs"    # Get Start Menu path for the current user
        [ -d "$start_menu_dir" ] && ([ -d "$start_menu_dir/LooPyGen" ] || mkdir "$start_menu_dir/LooPyGen")         # If Start Meny exists, create LooPyGen folder in it
        cp -a dockerfiles/assets/win_shortcuts/. "$start_menu_dir/LooPyGen"                                         # Copy our shortcuts in it
        (cd "$start_menu_dir/LooPyGen" && sed -i "s/DISTRO/${WSL_DISTRO_NAME}/g" "LooPyGen Folder.noturl" && sed -i "s/USERNAME/${USER}/g" "LooPyGen Folder.noturl")    # Update the LooPyGen folder URL based on distro name and user
        (cd "$start_menu_dir/LooPyGen" && find . -type f -name "*.noturl" -exec sh -c 'for pathname do mv -- "$pathname" "${pathname%.noturl}".url; done' sh {} + )     # Rename .noturl to .url (workaround Windows caching .url files at creation)
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
        echo "Shortcuts removed"
        [ ! -d "$start_menu_dir" ] && echo "Start menu directory not found"
    else
        echo "Not running inside WSL";
    fi
}

case $1 in
    build) docker-compose build;;
    reload) reload;;
    update) update;;
    up)
        checkDotenv
        install_start_menu_shortcuts
        docker-compose up -d
    ;;
    install_start_menu) install_start_menu_shortcuts;;
    remove_start_menu) remove_start_menu_shortcuts;;
    down) docker-compose down;;
    migrate) migrate;;
    *)
        if ! $(docker ps -q --filter "name=loopygen.php" | grep -q .); then
            checkDotenv
            docker-compose up -d
        fi
        docker-compose exec php "$@"
    ;;
esac
