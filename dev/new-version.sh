#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage:  $0 XX.YY.ZZ"
    exit 1
fi

echo
echo -n "previous version (python): "
egrep "^ROVER_VERSION.*" rover/args.py | sed -e 's/ROVER_VERSION = //' | sed -e "s/'//g"
echo -n "previous version (setup.py): "
egrep "version=.*" setup.py | sed -e 's/version=//' | sed -e 's/[" ,]//g'

VERSION="$1"
echo
echo "new version: $VERSION"

sed -i -e "s/^ROVER_VERSION.*/ROVER_VERSION = '$VERSION'/" rover/args.py
sed -i -e "s/version=.*/version=\"$VERSION\",/" setup.py

echo
echo -n "updated version (python): "
egrep "^ROVER_VERSION.*" rover/args.py | sed -e 's/ROVER_VERSION = //' | sed -e "s/'//g"
echo -n "updated version (setup.py): "
egrep "version=.*" setup.py | sed -e 's/version=//' | sed -e 's/[" ,]//g'

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
#git tag -a v$VERSION -m "version $VERSION"
echo
echo "to share the tag:"
echo "  git push origin --tags"
echo "to delete the tag (before pushing):"
echo "  git tag -d v$VERSION"
