#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage:  $0 XX.YY.ZZ"
    exit 1
fi

OLDVERSION=$(<rover/VERSION)
echo
echo "previous version: $OLDVERSION"

VERSION="$1"
echo
echo "new version: $VERSION"

# Replace version
echo $VERSION > rover/VERSION

NEWVERSION=$(<rover/VERSION)
echo
echo "updated version: $NEWVERSION"

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
echo "  git commit rover/VERSION -m 'version $VERSION'"
echo "  git tag -a v$VERSION -m 'version $VERSION'"
echo "push changes and tag:"
echo "  git push"
echo "  git push origin --tags"
echo
echo "Append 'plus' to version and push to master"
echo "  echo '${VERSION}plus' > rover/VERSION"
echo "  git commit  rover/VERSION -m 'version ${VERSION}plus'"
echo "  git push"

