#!/bin/bash

echo "creating virtualenvs"
dev/make-env2.sh > /dev/null
dev/make-env3.sh > /dev/null
dev/run-all-nose-tests.sh
dev/run-all-robot-tests.sh
