#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
VERSION=$(cat VERSION)
work=/tmp/opencode/bookshelf-deb
rm -rf "$work"
mkdir -p "$work"
git archive HEAD | tar -x -C "$work"
rm -rf "$work/assets/screenshots"
mkdir -p "$work/debian/source"
cp packaging/deb/control "$work/debian/control"
cp packaging/deb/rules "$work/debian/rules"
cp packaging/deb/install "$work/debian/install"
cp packaging/deb/changelog "$work/debian/changelog"
cp packaging/deb/copyright "$work/debian/copyright"
echo "3.0 (native)" > "$work/debian/source/format"
cd "$work"
dpkg-buildpackage -us -uc -b -d
cd - >/dev/null
mv "$work/../bookshelf_${VERSION}-1_all.deb" .
echo "Built: bookshelf_${VERSION}-1_all.deb"
