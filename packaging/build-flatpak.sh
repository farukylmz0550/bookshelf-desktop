#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
VERSION=$(cat VERSION)
work=/tmp/opencode/bookshelf-flatpak
repo="$work/repo"
rm -rf "$repo" "$work/build"
mkdir -p "$work"
flatpak-builder --user --force-clean --repo="$repo" "$work/build" \
  packaging/flatpak/io.github.farukylmz0550.BookShelfLegacy.json
flatpak build-bundle --runtime "$repo" "BookShelf-${VERSION}.flatpak" \
  io.github.farukylmz0550.BookShelfLegacy "${VERSION}"
echo "Built: BookShelf-${VERSION}.flatpak"
