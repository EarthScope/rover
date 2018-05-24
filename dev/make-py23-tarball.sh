#!/bin/bash

dev/translate-py3-to-py23.sh

pushd ../rover23

rm -fr tests
rm -fr robot
pushd ..
tar cvfz rover.tgz --transform s/rover23/rover/ rover23
popd

popd
