#!/usr/bin/env python
import os
import json

BASE = os.path.join(os.path.dirname(__file__), '..')

TEMPLATE = """
#!/bin/bash
BASE_URL="https://codegradefs.s3-eu-west-1.amazonaws.com/v{{VERSION}}"

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
        err_echo "Failed to download file: ${url}, please check if a new version is available on https://codegrade.com/download-codegrade-filesystem"
        exit 10
    fi
}

_pip() {
    if hash pip3; then
        sudo pip3 "$@"
    else
        sudo pip "$@"
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

    printf "\\\\nInstalling dependencies\\\\n"
    if ! install_deps; then
        err_echo "Failed to install dependencies"
        exit 4
    fi
    tmpdir="$(mktemp -d)"
    trap '[[ -n $tmpdir ]] && rm -rf "$tmpdir"' 0 1 2 3 15

    printf "\\\\nDownloading all needed files\\\\n"
    download_file "${BASE_URL}/linux/python3-fusepy_NEWEST-1_all.deb" "$tmpdir/fusepy.deb"
    if is_distro "Debian"; then
        download_file "${BASE_URL}/debian/python3-codegrade-fs_all.deb" "$tmpdir/backend.deb"
    else
        download_file "${BASE_URL}/ubuntu/python3-codegrade-fs_all.deb" "$tmpdir/backend.deb"
    fi
    download_file "${BASE_URL}/linux/codegrade-fs_$(get_arch).deb" "$tmpdir/frontend.deb"

    if _pip list | grep -- 'CodeGra.fs'; then
        printf "\\\\nRemoving old versions\\\\n"
        _pip uninstall -y CodeGra.fs
    fi

    printf "\\\\nInstalling our version of fusepy\\\\n"
    sudo dpkg -i "$tmpdir/fusepy.deb"
    printf "\\\\nInstalling the backend of the CodeGrade Filesystem\\\\n"
    sudo dpkg -i "$tmpdir/backend.deb"
    printf "\\\\nInstalling the frontend of the CodeGrade Filesystem\\\\n"
    sudo dpkg -i "$tmpdir/frontend.deb"
    rm -rf "$tmpdir"
    tmpdir=""

    printf "\\\\nDone installing the file system\\\\n"
}

main
""".lstrip()


def main():
    with open(os.path.join(BASE, 'package.json'), 'r') as f:
        version = json.load(f)['version']

    dist_dir = os.path.join(BASE, 'dist')
    os.makedirs(dist_dir, exist_ok=True)
    with open(os.path.join(dist_dir, 'install_linux.bash'), 'w') as f:
        f.write(TEMPLATE.replace('{{VERSION}}', version))


if __name__ == '__main__':
    main()
