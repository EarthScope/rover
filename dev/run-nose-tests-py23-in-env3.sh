#!/bin/bash

echo
echo "translating py3 to py23"
dev/translate-py3-to-py23.sh > /dev/null 2>&1
source env3/bin/activate
pushd ../rover23
echo
echo "unit tests of py23 code in env3"
nosetests tests/*.py
popd
