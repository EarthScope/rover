#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage:  $0 XX.YY.ZZ"
    exit 1
fi

echo
echo -n "previous version: "
egrep "^__version__.*" rover/__init__.py | sed -e 's/__version__ = //' | sed -e "s/'//g"

VERSION="$1"
echo
echo "new version: $VERSION"

sed -i -e "s/^__version__.*/__version__ = '$VERSION'/" rover/__init__.py

echo
echo -n "updated version: "
egrep "^__version__.*" rover/__init__.py | sed -e 's/__version__ = //' | sed -e "s/'//g"

echo
echo "building tarball"
dev/make-py23-tarball.sh > /dev/null 2>&1
pushd .. > /dev/null
mv rover.tgz rover-$VERSION.tgz
echo
echo "rover-$VERSION.tgz in $PWD"
popd > /dev/null

echo
echo "tagging version in git"
git tag -a v$VERSION -m "version $VERSION"
echo
echo "to share the tag:"
echo "  git push origin --tags"
echo "to delete the tag (before pushing):"
echo "  git tag -d v$VERSION"
