#!/bin/sh

set -eu

git stash

for f in codegra_fs/cgfs.py codegra_fs/utils.py; do
	cp "$f" "$f.2"
	sed -e 's/import fuse/import fusepy/' -e 's/from fuse import/from fusepy import/' <"$f.2" >"$f"
	rm "$f.2"
done

if python3 --version | grep '3\.5'; then
	rm codegra_fs/cgfs_types.py
fi

git diff --patch >build/deb.patch

git checkout codegra_fs/cgfs.py codegra_fs/utils.py codegra_fs/cgfs_types.py

git stash pop
