#!/bin/bash

dev/install-py23-in-env2.sh
source env2/bin/activate
# we run in rover, not rover23, because robot tests are the same
echo
echo "integration tests of py23 code in env2"
robot -F robot robot
echo
echo "remaking env2 to remove install"
dev/make-env2.sh > /dev/null 2>&1
echo
echo "file://`pwd`/log.html"
echo

