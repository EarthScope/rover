#!/bin/bash

rm -fr env3
virtualenv-3.5 env3
source env3/bin/activate
pip install --upgrade pip
pip install requests
pip install numpy
pip install obspy
pip install nose
pip install future
pip install robotframework

echo "source env3/bin/activate"
