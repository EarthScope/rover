#!/bin/bash

dev/install-py23-in-env2.sh
echo

# Check if system is already running python2
ver="Python 2\.7"
# Determine if the env2 activate file exist if not exit.
if ! [ -f env2/bin/activate ]; then
    echo "Python 2 virtual enviroment is not initialized."
    echo "Run /dev/make-env2.sh and try again."
    exit 1
fi

source env2/bin/activate
# verfiy that the virtual env is running the correct python version
pyv="$(python -V 2>&1)"
if ! [[ $pyv =~ $ver ]]; then
    echo "Python 2 virtual enviroment was set up incorrectly."
    echo "Likely, the incorrect version of Python is being utlized."
    echo "Please check that Python 2.7 is installed on this system."
    echo "Try again."
    exit
fi
# we run in rover, not rover23, because robot tests are the same
echo "integration tests of py23 code in env2"
which rover
robot -F robot robot
echo
echo "remaking env2 to remove install"
dev/make-env2.sh > /dev/null 2>&1
echo
echo "file://`pwd`/log.html"
echo
