#!/bin/bash

source env3/bin/activate
echo
echo "nose python 3 tests on 3"
nosetests tests/*.py
