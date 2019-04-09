#!/bin/bash

echo
echo "translating py3 to py23"
dev/translate-py3-to-py23.sh > /dev/null 2>&1

# Determine the version of python
pyv="$(python -V 2>&1)"
#echo $pyv

# Check if system is already running python2
ver="Python 2\.7"
if [[ $pyv =~ $ver ]]; then
    echo "Did not activate virtual env."
    pushd ../rover23
    echo
    echo "Unit tests of py23 code in env2"
    nosetests tests/*.py
    popd
# If python 2 is not the system default set up virtual env
else

    # Determine if the env2 activate file exist if not exit.
    if ! [ -f env2/bin/activate ]; then
        echo "Python 2 virtual enviroment is not initialized."
        echo "Run /dev/make-env2.sh and try again."
        exit
    fi

    source env2/bin/activate
    # verfiy that the virtual env is running the correct python version
    pyv1="$(python -V 2>&1)"
    if ! [[ $pyv1 =~ $ver ]]; then
        echo "Python 2 virtual enviroment was set up incorrectly."
        echo "Likely, the incorrect version of Python is being utlized."
        echo "Please check that Python 2.7 is installed on this system."
        echo "Try again."
        exit
    fi

    # run commands if all checks pass
    pushd ../rover23
    echo
    echo "unit tests of py23 code in env2"
    nosetests tests/*.py
    popd
fi
