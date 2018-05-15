#!/bin/bash

source env2/bin/activate
pushd ../py2
echo
echo "nose python 2 tests"
nosetests tests/*.py
popd
