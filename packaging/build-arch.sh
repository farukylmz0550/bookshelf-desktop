#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
VERSION=$(cat VERSION)
work=/tmp/opencode/bookshelf-arch
rm -rf "$work"
mkdir -p "$work"
git archive HEAD | tar -x -C "$work"
rm -rf "$work/assets/screenshots"
cp packaging/arch/PKGBUILD "$work/PKGBUILD"
cd "$work"
makepkg -f --noconfirm
cd - >/dev/null
mv "$work/bookshelf-${VERSION}-1-any.pkg.tar.zst" .
echo "Built: bookshelf-${VERSION}-1-any.pkg.tar.zst"
