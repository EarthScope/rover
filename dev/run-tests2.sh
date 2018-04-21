#!/bin/bash

source env2/bin/activate
cd py2
echo
echo "python 2 tests"
nosetests tests/*
