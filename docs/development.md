
# Rover Development

## Python 2

Rover is developed using "pure" Python 3.  **This gives the most
maintainable, future-proof source.**

However, we must also support Python 2.7.  To do this we auto-generate
code that can run on Python 2.7 *and* Python 3 using the
[pasteurize](http://python-future.org/pasteurize.html) tool from the
[future](http://python-future.org/index.html) package.

One consequence of this is that the "installable" code (typically
available from [PyPI](https://pypi.org/) or a tarball) is not
identical to the development code (typically available from
[github](https://github.com/iris-edu/rover/)).

## Getting Started

First, create a directory that will contain both the development and
auto-generated code:

    mkdir roverdev

Then change into this directory and clone github:

    cd roverdev
    git clone git@github.com:iris-edu/rover.git

Create a virtualenv for Python 3 development (you may need to alter
the script details slightly depending on your python version):

    cd rover
    dev/make-env-py3.sh
    source env3/bin/activate

You can now edit the source.  To test your changes:

    dev/run-nose-tests-py3-on-py3.sh
    dev/run-robot-tests-py3-on-py3.sh

(nose tests are low-level code-based unit tests; robot tests are
high-level, command-based integration tests).

You can also run tests on both the development and (auto-generated)
installable code (these scripts automatically generate the `rover23`
code as described below):

    dev/run-all-nose-tests.sh
    dev/run-all-robot-tests.sh

## Generating Installable Code

To simply generate the tarball:

    dev/make-py23-tarball.sh

this creates `rover.tgz` in the `roverdev` directory.

To generate the code manually (this will create a `rover23` directory
in `roverdev`):

    dev/translate-py3-to-py23.sh

It is not recommended to install code directly on the development
machine (in the system python), but once you are using virtualenv you
can run `python setup.py install` from inside `rover23` to install.
