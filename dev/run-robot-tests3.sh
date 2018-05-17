#!/bin/bash

bootstrap=0
if [[ $# -eq 1 && "$1" = "--bootstrap" ]]; then
    bootstrap=1
elif [[ $# -ne 0 ]]; then
    echo
    echo "  usage:"
    echo "    dev/run-robot-test3.sh [--bootstrap]"
    echo
    exit 1
fi

source env3/bin/activate
echo
echo "robot python 3 tests"
robot -F robot robot

if [[ $bootstrap ]]; then
    find . -name "target" -print0 | while read -d $'\0' target; do
        echo "populating $target"
        dir=`dirname "$target"`
        run="$dir/run"
        cp "$run/"*.txt "$target/"
    done
fi
