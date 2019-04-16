#!/bin/bash

VERSION=$(<rover/VERSION)
echo
echo "Building release for version: $VERSION"

echo
echo "Translating Python 3 to portable 2-3 version and building tarball"
dev/make-py23-tarball.sh > /dev/null 2>&1
pushd .. > /dev/null
mv rover.tgz rover-$VERSION.tgz
echo
echo "rover-$VERSION.tgz in $PWD"
popd > /dev/null

echo
echo "Now is a chance to test the rover23 version,"
echo "  if all checks out, you can upload the 2-3 version to PyPI"
echo
