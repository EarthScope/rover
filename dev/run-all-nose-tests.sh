#!/bin/bash

dev/run-nose-tests-py3-on-py3.sh
echo
echo "generating python 23"
dev/translate-py3-to-py23.sh > /dev/null 2>&1
dev/run-nose-tests-py2-on-py23.sh
dev/run-nose-tests-py3-on-py23.sh
