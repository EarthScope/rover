#!/bin/bash

source env3/bin/activate
rm -fr py2
mkdir py2
cp -r rover py2
cp -r tests py2

pushd py2
pasteurize -w -n --no-diffs .
popd

for file in `egrep -lir --include=*.py TemporaryDirectory py2`; do
    echo "backports.tempfile for $file"
    sed -i 's/from tempfile import/from backports.tempfile import/' $file
done
