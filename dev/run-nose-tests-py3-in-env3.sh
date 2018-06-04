#!/bin/bash

source env3/bin/activate
echo
echo "unit tests of py3 code in env3"
nosetests tests/*.py
