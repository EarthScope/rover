#!/bin/bash

echo
echo "unit tests of py3 code in env3"

# Determine the version of python
pyv="$(python -V 2>&1)"

# Check if system is already running python3
ver="Python 3\.[5-9]"
if [[ $pyv =~ $ver ]]; then
    nosetests tests/*.py
# If python 2 is not the system default set up virtual env
else

    # Determine if the env3 activate file exist if not exit.
    if ! [ -f env3/bin/activate ]; then
        echo "Python 3 virtual enviroment is not initialized."
        echo "Run /dev/make-env3.sh and try again."
        exit 1
    fi

    source env3/bin/activate

    # verfiy that the virtual env is running the correct python version
    pyv1="$(python -V 2>&1)"
    if ! [[ $pyv1 =~ $ver ]]; then
        echo "Python 3 virtual enviroment was set up incorrectly."
        echo "Likely, the incorrect version of python is being utlized."
        echo "Please check that Python 3.5 or later is installed on this system."
        echo "Try again."
        exit 1
    fi

    # run commands if all checks pass
    nosetests tests/*.py
fi
