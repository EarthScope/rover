#!/bin/bash

# Check to see if vitural enviroment is set up correctly.
if ! [ -x "$(command -v virtualenv)" ]; then
    echo "Virtualenv not found."
    echo "You may need to install virtualenv or modify this script to use virtualenv-2.7."
    exit 1
fi

# set up virtiual env
rm -fr env2
virtualenv --python=python2.7 env2
source env2/bin/activate
pip install --upgrade pip
pip install requests
pip install nose
pip install future
pip install robotframework
pip install backports.tempfile
pip install setuptools

source env2/bin/activate

# Check python version in the vitualenv
pyv="$(python -V 2>&1)"
echo "$pyv"

# Make a that checks for a range of python versions
ver="Python 2\.7"
if ! [[ $pyv =~ $ver ]]; then
    echo "Python 2 virtual enviroment was set up incorrectly."
    echo "Likely, the incorrect version of python is being utlized."
    echo "Please check that Python 2.7 is installed on this system."
    echo "Try again."
    exit 1
fi

echo "source env2/bin/activate"

