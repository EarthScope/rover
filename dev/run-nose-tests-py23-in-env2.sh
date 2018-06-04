#!/bin/bash

source env2/bin/activate
pushd ../rover23
echo
echo "unit tests of py23 code in env2"
nosetests tests/*.py
popd
