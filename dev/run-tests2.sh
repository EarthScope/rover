#!/bin/bash

source env2/bin/activate
cd py2
nosetests tests/*
