#!/bin/bash

python2 -c $'import sys;\nv = sys.version_info\nif v.major != 2 or v.minor < 7:\n exit(1)'
if [ $? -eq 1 ]; then
    echo "python2 must be 2.7 or above"
    exit
fi

if ! [ -x "$(command -v virtualenv)" ]; then
    echo "virtualenv not found"
    echo "you may need to modify this script to use virtualenv-2.7"
    exit
fi

rm -fr env2
virtualenv --python=python2 env2
source env2/bin/activate
pip install --upgrade pip
pip install requests
pip install nose
pip install future
pip install robotframework
pip install backports.tempfile
pip install setuptools

echo "source env2/bin/activate"
