#!/bin/bash

echo
echo "making clean env3 for install"
dev/make-env-py3.sh > /dev/null 2>&1
source env3/bin/activate
echo
echo "installing"
pushd ../rover23
python setup.py install > /dev/null 2>&1
echo
echo "robot python 3 tests on 23"
robot -F robot robot
popd
echo
echo "remaking env3 to remove install"
dev/make-env-py3.sh > /dev/null 2>&1

rm -fr build
rm -fr dist
rm -fr rover.egg-info
