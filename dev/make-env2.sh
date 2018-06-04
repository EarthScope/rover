#!/bin/bash

rm -fr env2
virtualenv-2.7 env2
source env2/bin/activate
pip install --upgrade pip
pip install requests
pip install nose
pip install future
pip install robotframework
pip install backports.tempfile

echo "source env2/bin/activate"
