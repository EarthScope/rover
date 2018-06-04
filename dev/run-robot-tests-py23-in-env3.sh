#!/bin/bash

dev/install-py23-in-env3.sh
source env3/bin/activate
# we run in rover, not rover23, because robot tests are the same
echo
echo "integration tests of py23 code in env3"
robot -F robot robot
echo
echo "remaking env3 to remove install"
dev/make-env3.sh > /dev/null 2>&1
echo
echo "file://`pwd`/log.html"
echo
