#!/bin/bash

source env3/bin/activate
echo
echo "python 3 tests"
nosetests tests/*
