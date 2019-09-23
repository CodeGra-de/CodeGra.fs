#!/bin/bash
# SPDX-License-Identifier: AGPL-3.0-only
VERSION="1.1.0"

err_echo() {
    (>&2 echo "$@")
}

is_linux() {
    [[ "$(uname)" = 'Linux' ]]
}

get_arch() {
    dpkg --print-architecture
}

is_distro() {
    local to_check="$1"
    grep "$to_check" /etc/issue >/dev/null 2>&1
}

install_deps() {
    sudo apt-get install -qy wget python3 fuse python3-requests libnotify4 gconf2 gconf-service libappindicator1 libxtst6 libnss3
}

download_file() {
    local url="$1" dst="$2"
    if ! wget --quiet "$url" -O "$dst"; then
        err_echo "Failed to download file $url"
        exit 10
    fi
}

main() {
    local tmpdir

    if ! is_linux; then
        err_echo "This script only supports linux"
        exit 1
    fi

    if ! is_distro "Debian" && ! is_distro "Ubuntu" && ! is_distro 'Linux Mint'; then
        err_echo "For now only Ubuntu, Linux Mint, and Debian are supported"
        err_echo "Please check our github repository at https://github.com/CodeGra-de/CodeGra.fs to install it manually"
        exit 2
    fi

    case "$(get_arch)" in
        "amd64") ;;
        "i386") ;;
        *) err_echo "We only support amd64 and i386 as architectures"
           exit 3
    esac

    echo "Updating package list"
    sudo apt update -q

    printf "\\nInstalling dependencies\\n"
    if ! install_deps; then
        err_echo "Failed to install dependencies"
        exit 4
    fi
    tmpdir="$(mktemp -d)"
    trap '[[ -n $tmpdir ]] && rm -rf "$tmpdir"' 0 1 2 3 15

    printf "\\nDownloading all needed files\\n"
    download_file "https://codegra.de/static/fs/linux/python3-fusepy_NEWEST-1_all.deb" "$tmpdir/fusepy.deb"
    if is_distro "Debian"; then
        download_file "https://codegra.de/static/fs/debian/python3-codegrade-fs_${VERSION}-1_all.deb" "$tmpdir/backend.deb"
    else
        download_file "https://codegra.de/static/fs/ubuntu/python3-codegrade-fs_${VERSION}-1_all.deb" "$tmpdir/backend.deb"
    fi
    download_file "https://codegra.de/static/fs/linux/codegrade-fs_${VERSION}_$(get_arch).deb" "$tmpdir/frontend.deb"

    printf "\\nInstalling our version of fusepy\\n"
    sudo dpkg -i "$tmpdir/fusepy.deb"
    printf "\\nInstalling the backend of the CodeGrade Filesystem\\n"
    sudo dpkg -i "$tmpdir/backend.deb"
    printf "\\nInstalling the frontend of the CodeGrade Filesystem\\n"
    sudo dpkg -i "$tmpdir/frontend.deb"
    rm -rf "$tmpdir"
    tmpdir=""

    printf "\\nDone installing the file system\\n"
}

main
