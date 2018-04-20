#!/bin/bash

rm -fr env2
virtualenv-2.7 env2
source env2/bin/activate
pip install nose
pip install future

echo "source env2/bin/activate"
