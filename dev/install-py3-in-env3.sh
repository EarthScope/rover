#!/bin/bash

echo
echo "making clean env3 for install"
dev/make-env3.sh > /dev/null 2>&1
source env3/bin/activate
echo
echo "installing"
python setup.py install > /dev/null 2>&1
rm -fr build
rm -fr dist
rm -fr rover.egg-info

echo
echo "WARNING"
echo "1 - you are using the devlopment (py3) code, not the installable (py23)"
echo "2 - this install will not update to reflect changes made to the source"
echo
echo "source env3/bin/activate"
