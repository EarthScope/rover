---
title: ROVER Development
layout: default
---

## Python 2 and 3 support

ROVER is written in Python 3.

A combination of Python 2.7 and Python 3.5 and later are supported
by auto-generating portable code using the
[pasteurize](http://python-future.org/pasteurize.html) tool from the
[future](http://python-future.org/index.html) package.

One consequence of this is that the "installable" code (typically
available via `pip` from the [PyPI rover project](https://pypi.org/project/rover/) or a tarball) is not
identical to the development code (typically available from the
[rover repository](https://github.com/EarthScope/rover/)). Because of this disparity, instances of development ROVER should not be installed into system Python 2.7.

## Getting started

First, create a directory that will contain both the development and
auto-generated code:

    mkdir roverdev

Then change into this directory and clone github:

    cd roverdev
    git clone https://github.com/EarthScope/rover.git

Create a virtualenv for Python 3 development (you may need to alter
the script details slightly depending on your python version):

    cd rover
    dev/make-env3.sh
    source env3/bin/activate

You can now edit the source.  To test your changes:

    dev/run-nose-tests-py3-in-env3.sh 
    dev/run-robot-tests-py3-in-env3.sh

(nose tests are low-level code-based unit tests; robot tests are
high-level, command-based integration tests).

Tests assume that executable `/mseedindex/mseedindex` is installed in the parent directory of `rover`,
`rover/../mseedindex/mseedindex`.

You may need to edit tests or change configuration if this is not the
case.

You can also run tests on both the development and (auto-generated)
installable code.  These scripts automatically generate the `rover23`
code as described below; the robot script also installs `rover` in the
appropriate virtualenvs for testing, then create new virtualenvs
(without install) after the test.  The commands are:

    dev/run-all-nose-tests.sh
    dev/run-all-robot-tests.sh
    dev/run-all-tests.sh

## Generating installable code

To simply generate the tarball:

    dev/make-py23-tarball.sh

this creates `rover.tgz` in the `roverdev` directory.

To generate the code manually (this will create a `rover23` directory
in `roverdev`):

    dev/translate-py3-to-py23.sh

It is not recommended to install code directly on the development
machine (in the system python), but once you are using virtualenv you
can run `python setup.py install` from inside `rover23` to install.
To delete the install, remake the virtualenv.

When making a new release:

    dev/new-version.sh X.Y.Z

where X.Y.Z is the new version number.  This will set the version in
the source, tag the version in git, and build a suitably named tarball in the `roverdev` directory.

## Windows

* Install git and clone the project:

  * Install git.

  * Configure ssh keys (openssh is available in git bash).

  * Clone the repo.

* Install Python 3 and get virtualenv working:

  * Install Python (including options for PATH).

  * `pip install virtualenv` and update pip to latest version.

  * Run `dev\make-env3.bat` to create the environment.

  * Run `env3\Scripts\Activate.bat` to activate the environment.

  * The `rover` command is now installed and available.

* Install Python 2:

  * Install Python (no options for path - it's placed in C:\Python27)

  * Run `dev\make-env2.bat` to create the environment.

  * Run `env2\Scripts\Activate.bat` to activate the environment,

* Install mseedindex:

  * Install Visual Studio (community edition is free).

  * Clone mseedindex from github.

  * Compile mseedindex (no need for sqlite install - see mseedindex
    docs)

* You can now install and run ROVER:

  * See other batch scripts in dev. 

  * You will need to configure ROVER as normal to find mseedindex.

Note that on Windows we ignore the `ROVER-cmd` parameter because we
must use `pythonw` for sub-processes.

