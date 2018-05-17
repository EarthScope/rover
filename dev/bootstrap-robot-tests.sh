#!/bin/bash

find . -name "target" -print0 | while read -d $'\0' target; do
    echo "populating $target"
    dir=`dirname "$target"`
    run="$dir/run"
    cp "$run/"*.txt "$target/"
done

