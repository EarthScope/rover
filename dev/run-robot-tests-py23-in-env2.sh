#!/bin/bash

dev/install-py23-in-env2.sh
source env2/bin/activate
pushd ../rover23
echo
echo "integration tests of py23 code in env2"
robot -F robot robot
popd
echo
echo "remaking env2 to remove install"
dev/make-env2.sh > /dev/null 2>&1
echo
pushd ../rover23
echo "file://`pwd`/log.html"
popd
