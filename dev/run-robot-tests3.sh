#!/bin/bash

source env3/bin/activate
echo
echo "robot python 3 tests"
robot -F robot robot
