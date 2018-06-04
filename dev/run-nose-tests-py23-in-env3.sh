#!/bin/bash

source env3/bin/activate
pushd ../rover23
echo
echo "unit tests of py23 code in env3
nosetests tests/*.py
popd
