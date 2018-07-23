#!/bin/bash

echo "WARNING: this will delete any build directory in roverdev"
echo "(as well as replacing rover23)"

dev/translate-py3-to-py23.sh

pushd ..
rm -fr build
mkdir build
cp -r rover23 build/rover

pushd build/rover
rm -fr tests

pushd ..
tar cvfz rover.tgz rover
popd

popd
mv build/rover.tgz .
rm -fr build

popd
