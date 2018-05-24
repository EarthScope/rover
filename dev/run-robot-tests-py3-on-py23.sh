#!/bin/bash

source env3/bin/activate
pushd ../rover23
echo
echo "robot python 3 tests on 23"
PYTHONPATH=../../.. robot -F robot robot
popd
