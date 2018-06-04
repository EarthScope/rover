#!/bin/bash

echo
echo "translating py3 to py23"
dev/translate-py3-to-py23.sh > /dev/null 2>&1
source env2/bin/activate
pushd ../rover23
echo
echo "unit tests of py23 code in env2"
nosetests tests/*.py
popd
