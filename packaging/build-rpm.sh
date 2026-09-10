#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
VERSION=$(cat VERSION)
work=/tmp/opencode/bookshelf-rpm
rm -rf "$work"
mkdir -p "$work/SOURCES" "$work/RPMS/noarch" "$work/BUILD"
git archive --prefix="bookshelf-${VERSION}/" HEAD | tar -x -C "$work/BUILD"
tar -czf "$work/SOURCES/bookshelf-${VERSION}.tar.gz" -C "$work/BUILD" "bookshelf-${VERSION}"
rpmbuild -bb --define "_topdir $work" packaging/rpm/bookshelf.spec
cp "$work/RPMS/noarch/bookshelf-${VERSION}-1.noarch.rpm" .
echo "Built: bookshelf-${VERSION}-1.noarch.rpm"
