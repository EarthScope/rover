#!/bin/bash

dev/make-env-py3.sh
source env3/bin/activate
python setup.py install
