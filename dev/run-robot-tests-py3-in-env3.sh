#!/bin/bash

dev/install-py3-in-env3.sh
source env3/bin/activate
echo
echo "integration tests of py3 code in env3"
robot -F robot robot
echo
echo "remaking env3 to remove install"
dev/make-env-py3.sh > /dev/null 2>&1
