# The IRIS rover user guide

## Description

Rover is tool to robustly retrieve seismic (and other) data from data
centers like the [IRIS DMC](http://ds.iris.edu).  An associated index is
built for all of the data downloaded to a local repository.

Rover is a command-line tool and requires Python 2.7 or (preferrably)
Python 3.5 or later.

## Documentation

* [Installation](#installation)
* [Quick start](#quickstart)
* [An introduction to rover](introduction.md)
* [Rover commands](commands.md)
* [Rover configuration](configuration.md)
* [Example commands to download data](download.md)
* [Example commands to manage and maintain the local store](maintenance.md)
* [Rover's processing pipeline](pipeline.md)
* [Known bugs and limitations](bugs.md)
* [Rover development](development.md)

## Installation <a id="installation"></a>

1. Rover requires [mseedindex](https://github.com/iris-edu/mseedindex) -
see [mseedindex install guidelines](mseedindex.md).  This is a `C` language program
that must be compiled.

2. Install rover, and other Python requirements, with `pip`:

    ```
    pip install rover
    ```

You should now be able to type `rover --version` to see if it was successfully installed.

## Quick start <a id="quickstart"></a>

1. Initialize a data repository (creates the `datarepo` directory), and change into the new directory:

    ```
    rover init-repository datarepo
    cd datarepo
    ```

1. Create a request file, e.g. named `request.txt` that contains:

    ```
    IU ANMO * LHZ 2012-01-01T00:00:00 2012-02-01T00:00:00
    TA MSTX -- BH? 2012-01-01T00:00:00 2012-02-01T00:00:00
    ```

1. Run rover in retrieve move to fetch these data:

   ```
   rover retrieve request.txt
   ```

1. List a summary of the data, earliest and latest times, retrieved:

   ```
   rover list-summary

      IU_ANMO_00_LHZ 2012-01-01T00:00:00.069500 2012-01-31T23:59:59.069500
      IU_ANMO_10_LHZ 2012-01-01T00:00:00.069500 2012-01-31T23:59:59.069500
      TA_MSTX__BHE 2012-01-01T00:00:00.000000 2012-01-31T23:59:59.975000
      TA_MSTX__BHN 2012-01-01T00:00:00.000000 2012-01-31T23:59:59.975000
      TA_MSTX__BHZ 2012-01-01T00:00:00.000000 2012-01-31T23:59:59.975000
   ```

The data, in miniSEED format, are now available in the `datareport/data/` directory.  All data for a station or a day are stored in a single file, with the following general file organization:

   ```
   <datarepo>/data/<network>/<year>/<day>/<station>.<network>.<year>.<day>
   ```

There are many more options available in rover, such as the ability send an email
when the request is finished (see the `--email` option), view a listing of contiguous traces (via the `rover list-index join` command), view the status of a long-running download using a web browser (by default at [http://localhost:8000/](http://localhost:8000/)).

There are more options in the rover.config file and on the command line, use the `-h` option to see the command line options.

For more detailed exampmles, see more [example commands to download data](download.md) and [example commands to manage and maintain the local store](maintenance.md).

## Copyright and License

This a product of the [IRIS Data Management Center](http://ds.iris.edu/ds/nodes/dmc/).

This software Copyright (c) 2018 Incorporated Research
Institutions for Seismology (IRIS).

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

<!-- GitHub corner from https://github.com/tholman/github-corners -->
<a href="https://github.com/iris-edu/rover" class="github-corner" aria-label="View source on GitHub"><svg width="80" height="80" viewBox="0 0 250 250" style="fill:#70B7FD; color:#fff; position: absolute; top: 0; border: 0; right: 0;" aria-hidden="true"><path d="M0,0 L115,115 L130,115 L142,142 L250,250 L250,0 Z"></path><path d="M128.3,109.0 C113.8,99.7 119.0,89.6 119.0,89.6 C122.0,82.7 120.5,78.6 120.5,78.6 C119.2,72.0 123.4,76.3 123.4,76.3 C127.3,80.9 125.5,87.3 125.5,87.3 C122.9,97.6 130.6,101.9 134.4,103.2" fill="currentColor" style="transform-origin: 130px 106px;" class="octo-arm"></path><path d="M115.0,115.0 C114.9,115.1 118.7,116.5 119.8,115.4 L133.7,101.6 C136.9,99.2 139.9,98.4 142.2,98.6 C133.8,88.0 127.5,74.4 143.8,58.0 C148.5,53.4 154.0,51.2 159.7,51.0 C160.3,49.4 163.2,43.6 171.4,40.1 C171.4,40.1 176.1,42.5 178.8,56.2 C183.1,58.6 187.2,61.8 190.9,65.4 C194.5,69.0 197.7,73.2 200.1,77.6 C213.8,80.2 216.3,84.9 216.3,84.9 C212.7,93.1 206.9,96.0 205.4,96.6 C205.1,102.4 203.0,107.8 198.3,112.5 C181.9,128.9 168.3,122.5 157.7,114.1 C157.9,116.9 156.7,120.9 152.7,124.9 L141.0,136.5 C139.8,137.7 141.6,141.9 141.8,141.8 Z" fill="currentColor" class="octo-body"></path></svg></a><style>.github-corner:hover .octo-arm{animation:octocat-wave 560ms ease-in-out}@keyframes octocat-wave{0%,100%{transform:rotate(0)}20%,60%{transform:rotate(-25deg)}40%,80%{transform:rotate(10deg)}}@media (max-width:500px){.github-corner:hover .octo-arm{animation:none}.github-corner .octo-arm{animation:octocat-wave 560ms ease-in-out}}</style>