#!/bin/bash

dev/run-nose-tests3.sh
echo
echo "generating python 2"
dev/translate-py3-to-py2.sh > /dev/null 2>&1
dev/run-nose-tests2.sh
