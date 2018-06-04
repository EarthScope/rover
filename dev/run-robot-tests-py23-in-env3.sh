#!/bin/bash

dev/install-py23-in-env3.sh
source env3/bin/activate
pushd ../rover23
echo
echo "integration tests of py23 code in env3"
robot -F robot robot
popd
echo
echo "remaking env3 to remove install"
dev/make-env3.sh > /dev/null 2>&1
echo
pushd ../rover23
echo "file://`pwd`/log.html"
popd
