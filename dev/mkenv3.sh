#!/bin/bash

rm -fr env
virtualenv-3.4 env
source env/bin/activate
pip install nose

echo "source env/bin/activate"
