#!/bin/bash

source env3/bin/activate
echo
echo "robot python 3 tests on 3"
PYTHONPATH=../../.. robot -F robot robot
