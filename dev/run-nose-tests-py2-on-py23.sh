#!/bin/bash

source env2/bin/activate
pushd ../rover23
echo
echo "nose python 2 tests on 23"
nosetests tests/*.py
popd
