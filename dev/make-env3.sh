#!/bin/bash

python3 -c $'import sys;\nv = sys.version_info\nif v.major != 3 or v.minor < 5:\n exit(1)'
if [ $? -eq 1 ]; then
    echo "python3 must be 3.5 or above"
    exit
fi

if ! [ -x "$(command -v virtualenv)" ]; then
    echo "virtualenv not found"
    echo "you may need to modify this script to use virtualenv-3.5"
    exit
fi

rm -fr env3
virtualenv --python=python3 env3
source env3/bin/activate
pip install --upgrade pip
pip install requests
pip install nose
pip install future
pip install robotframework

echo "source env3/bin/activate"
