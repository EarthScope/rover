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
echo "Now is a chance to test the rover23 version, if all checks out:"
echo "  git commit rover/__init__.py -m 'version $VERSION'"
echo "  git tag -a v$VERSION -m 'version $VERSION'"
echo "push changes and tag:"
echo "  git push"
echo "  git push origin --tags"
echo
echo "Append 'plus' to version and push to master"
echo "  sed -i -e 's/^__version__.*/__version__ = ${VERSION}plus/' rover/__init__.py"
echo "  git commit rover/__init__.py -m 'version ${VERSION}plus'"
echo "  git push"

