#!/bin/bash

dev/run-robot-tests-py3-in-env3.sh
mv output.xml output-3-3.xml
dev/run-robot-tests-py23-in-env3.sh
mv output.xml output-3-23.xml
dev/run-robot-tests-py23-in-env2.sh
mv output.xml output-3-33.xml
echo
rebot output-3-3.xml output-2-23.xml output-3-33.xml
