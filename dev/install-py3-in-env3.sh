#!/bin/bash

dev/make-env-py3.sh
source env3/bin/activate
python setup.py install
rm -fr build
rm -fr dist
rm -fr rover.egg-info

echo
echo "WARNING"
echo "1 - you are using the devlopment (py3) code, not the installable (py23)"
echo "2 - this install will not update to reflct changes made to the source"
echo
