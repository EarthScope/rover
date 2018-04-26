#!/bin/bash

source env2/bin/activate
pushd ../py2
echo
echo "python 2 tests"
nosetests tests/*
popd
