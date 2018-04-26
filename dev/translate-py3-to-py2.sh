#!/bin/bash

source env3/bin/activate

pushd ..
rm -fr py2
mkdir py2
cp -r rover/rover py2
cp -r rover/tests py2

pushd py2
pasteurize -w -n --no-diffs .
popd

for file in `egrep -lir --include=*.py TemporaryDirectory py2`; do
    echo "backports.tempfile for $file"
    sed -i 's/from tempfile import TemporaryDirectory/from backports.tempfile import TemporaryDirectory/' $file
done
popd
