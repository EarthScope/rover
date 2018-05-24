#!/bin/bash

source env2/bin/activate
pushd ../rover23
echo
echo "robot python 2 tests on 23"
PYTHONPATH=../../.. robot -F robot robot
popd
