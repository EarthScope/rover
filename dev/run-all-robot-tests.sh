#!/bin/bash

dev/run-robot-tests-py3-on-py3.sh
mv output.xml output-3-3.xml
echo
echo "generating python 23"
dev/translate-py3-to-py23.sh > /dev/null 2>&1
dev/run-robot-tests-py2-on-py23.sh
mv ../rover23/output.xml output-2-23.xml
dev/run-robot-tests-py3-on-py23.sh
mv ../rover23/output.xml output-3-33.xml
echo
rebot output-3-3.xml output-2-23.xml output-3-33.xml
