
# IRIS Rover

## Description

Rover is a utility to download MSEED data from web services, building
a local store of data with an associated index (database).

## Documentation

* [An Introduction to Rover](docs/introduction.md)

* [Rover Commands](docs/commands.md)

* [Rover Configuration](docs/configuration.md)

* [Example Commands to Download Data](docs/download.md)

* [Example Commands to Manage and Maintain the Local Store](docs/maintenance.md)

* [Rover's Processing Pipeline](docs/pipeline.md)

* [Known Bugs and Limitations](docs/bugs.md)

* [Rover Development](docs/development.md)

## Installation

Rover requires [mseedindex](https://github.com/iris-edu/mseedindex) -
see [Mseedindex Install Guidelines](docs/mseedindex.md).

If you have a `rover.tgz` tarball:

    tar xvfz rover.tgz
    cd rover
    python setup.py install

If you are working with the development code see
[here](./docs/development.md).

## Copyright and License

This software Copyright (c) 2018 IRIS (Incorporated Research
Institutions for Seismology).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses/.


