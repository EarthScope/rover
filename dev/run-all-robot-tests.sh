#!/bin/bash

dev/run-robot-tests-py3-on-py3.sh
mv log.html log-3-3.html
echo
echo "generating python 23"
dev/translate-py3-to-py23.sh > /dev/null 2>&1
dev/run-robot-tests-py2-on-py23.sh
mv log.html log-2-23.html
dev/run-robot-tests-py3-on-py23.sh
mv log.html log-3-23.html
