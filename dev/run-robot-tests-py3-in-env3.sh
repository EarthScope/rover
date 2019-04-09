#!/bin/bash

dev/install-py3-in-env3.sh
echo

# Check if system is already running python3
ver="Python 3\.[5-9]"
# Determine if the env2 activate file exist if not exit.
if ! [ -f env3/bin/activate ]; then
    echo "Python 3 virtual enviroment is not initialized."
    echo "Run /dev/make-env3.sh and try again."
    exit 1
fi

source env3/bin/activate
# verfiy that the virtual env is running the correct python version
pyv="$(python -V 2>&1)"
if ! [[ $pyv =~ $ver ]]; then
    echo "Python 3 virtual enviroment was set up incorrectly."
    echo "Likely, the incorrect version of python is being utlized."
    echo "Please check that Python 3.5 or later is installed on this system."
    echo "Try again."
    exit 1
fi

echo "integration tests of py3 code in env3"
robot -F robot robot
echo
echo "remaking env3 to remove install"
dev/make-env3.sh > /dev/null 2>&1
echo
echo "file://`pwd`/log.html"
echo

