#!/bin/bash

echo
echo "making clean env3 for install"
dev/make-env3.sh > /dev/null 2>&1
source env3/bin/activate
echo
echo "translating py3 to py23"
dev/translate-py3-to-py23.sh > /dev/null 2>&1
echo
echo "installing"
pushd ../rover23
python setup.py install > /dev/null 2>&1
rm -fr build
rm -fr dist
rm -fr rover.egg-info
popd
echo
echo "source env3/bin/activate"
