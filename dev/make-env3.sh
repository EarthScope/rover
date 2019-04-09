#!/bin/bash

if ! [ -x "$(command -v virtualenv)" ]; then
    echo "virtualenv not found"
    echo "you may need to modify this script to use virtualenv-3.5"
    exit 1
fi

rm -fr env3
virtualenv --python=python3 env3
source env3/bin/activate
pip install --upgrade pip
pip install requests
pip install nose
pip install future
pip install robotframework
pip install setuptools

 # Check python version in the vitualenv
 pyv="$(python -V 2>&1)"
 echo "$pyv"

 # Make a that checks for a range of python versions
 ver="Python 3\.[5-9]"
 if ! [[ $pyv =~ $ver ]]; then
     echo "Python 3 virtual enviroment was set up incorrectly."
     echo "Likely, the incorrect version of python is being utlized."
     echo "Please check that Python 3.5 or later is installed on this system."
     echo "Try again."
     exit 1
 fi

echo "source env3/bin/activate"
