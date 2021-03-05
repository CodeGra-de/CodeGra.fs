#!/bin/bash

set -e

cd "$(dirname "$0")/../" || exit 1

tmp="$(mktemp -d)"

function rm_tmp() {
    if [[ -n "$tmp" ]]; then
        rm -r "$tmp"
    fi
}

trap "rm_tmp" 0 1 2 3 13 15 # EXIT HUP INT QUIT PIPE TERM

wget https://github.com/osxfuse/osxfuse/releases/download/macfuse-4.0.5/macfuse-4.0.5.dmg \
     -O "$tmp/fuse.dmg"
hdiutil attach -mountpoint "$tmp/mnt" "$tmp/fuse.dmg"
cp "$tmp"/mnt/*.pkg build/pkg-scripts/osxfuse.pkg
hdiutil detach "$tmp/mnt"
