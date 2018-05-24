#!/bin/bash

source env3/bin/activate
pushd ../rover23
echo
echo "nose python 3 tests on 23"
nosetests tests/*.py
popd
