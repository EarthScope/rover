#!/bin/bash

source env3/bin/activate
rm -fr py2
mkdir py2
cp -r rover py2
cp -r tests py2
cd py2
pasteurize -w -n .
