---
title: The IRIS ROVER user guide
layout: default
---
## Description

ROVER is a command line tool to robustly retrieve geophysical timeseries data from data centers such as [IRIS DMC](http://ds.iris.edu). It builds an associated index for downloaded data to generate a local repository. ROVER compares a built local index to timeseries availability information provided by the datacenter. This enables a local archive to remain synchronized with a remote data center.

## Documentation

* [Installation](#installation)
* [Quick start](#quickstart)
* [ROVER commands](commands.md)
* [ROVER configuration](configuration.md)
* [Example commands to download data](download.md)
* [Example commands to manage and maintain the local store](maintenance.md)
* [ROVER's processing pipeline](pipeline.md)
* [Known bugs and limitations](bugs.md)
* [ROVER development](development.md)

## Installation <a id="installation"></a>

ROVER is a command-line tool dependent on Python 2.7, 3.5 or a newer version. Python 3.7 or above is preferred. Pre-installed versions of Python available on some operating systems, such as macOS, may not support ROVER installation or operation. We suggest installing [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 3 (or [Anaconda](https://www.anaconda.com/distribution/#download-section) if you wish) for the best results.

### Option 1

ROVER requires the `C` language program [mseedindex](https://github.com/iris-edu/mseedindex) be available on the system's path. A `C` compiler and the `make` program are required to build mseedindex. ROVER and mseedindex may be downloaded and compiled simultaneously using pip:

    pip install rover --install-option="--mseedindex"

### Option 2
Alternatively, ROVER and mseedindex may be installed independently.

[Mseedindex](https://github.com/iris-edu/mseedindex) may be downloaded and compiled following the [mseedindex install guidelines](mseedindex.md). Similar to installation option 1, building mseedindex is dependent upon the `make` program and a `C` compiler.

Once mseedindex is configured and availble on the system's path, use `pip` to install ROVER and its other Python requirements:

    pip install rover

You should now be able to type `rover --version` to see if it was successfully installed.

## Quick start <a id="quickstart"></a>

Initialize a data repository, which creates the `datarepo` directory, and change into the new directory:

    rover init-repository datarepo
    cd datarepo

Create a request file named `request.txt` containing:

    IU ANMO * LHZ 2012-01-01T00:00:00 2012-02-01T00:00:00
    TA MSTX -- BH? 2012-01-01T00:00:00 2012-02-01T00:00:00

Run the process `rover retrieve` to fetch these data:

   ```
   rover retrieve request.txt
   ```

`list-summary` prints the retrieved data from the earliest to the latest timespans:

   ```
   rover list-summary

      IU_ANMO_00_LHZ 2012-01-01T00:00:00.069500 2012-01-31T23:59:59.069500
      IU_ANMO_10_LHZ 2012-01-01T00:00:00.069500 2012-01-31T23:59:59.069500
      TA_MSTX__BHE 2012-01-01T00:00:00.000000 2012-01-31T23:59:59.975000
      TA_MSTX__BHN 2012-01-01T00:00:00.000000 2012-01-31T23:59:59.975000
      TA_MSTX__BHZ 2012-01-01T00:00:00.000000 2012-01-31T23:59:59.975000
   ```

Retrieved files are miniSEED format containing day lengths of station data. The files are saved with the path structure:

   ```
   <datarepo>/data/<network>/<year>/<day>/<station>.<network>.<year>.<day>
   ```
## Exploring ROVER

ROVER has built-in help. The command `rover help` prints a ROVER introduction to the terminal.

There are many more options available in ROVER including; the ability to send emails that monitor
ROVER request and subscriptions (see the `--email` option), view listings of contiguous traces (via the `rover list-index join` command), or view the status of a long-running download using a web browser (by default at [http://localhost:8000/](http://localhost:8000/)).`rover help help` prints a list of [commands](commands.md) available in the ROVER code suite.

ROVER is configurable via the rover.config file or by using the command line. Type `rover -h` to see the configuration parameters that are adjustable using the command line.

For more detailed examples, see more [example commands to download data](download.md) and [example commands to manage and maintain the local repository](maintenance.md).

## Copyright and License

ROVER is a [IRIS Data Management Center](http://ds.iris.edu/ds/nodes/dmc/) product.

It is free software and can be redistributed and/or modified
under the terms of the GNU General Public License, version 3 or later, as published by
the Free Software Foundation.

ROVER is distributed without any warranty including the
implied warranty of merchantability or fitness for a
particular purpose.  See the GNU General Public License
for more details.

A copy of the GNU General Public License should be included
with the ROVER package. If not, see http://www.gnu.org/licenses/.

Copyright (c) 2018 Incorporated Research
Institutions for Seismology (IRIS).

<!-- GitHub corner from https://github.com/tholman/github-corners -->
<a href="https://github.com/iris-edu/rover" class="github-corner" aria-label="View source on GitHub"><svg width="80" height="80" viewBox="0 0 250 250" style="fill:#70B7FD; color:#fff; position: absolute; top: 0; border: 0; right: 0;" aria-hidden="true"><path d="M0,0 L115,115 L130,115 L142,142 L250,250 L250,0 Z"></path><path d="M128.3,109.0 C113.8,99.7 119.0,89.6 119.0,89.6 C122.0,82.7 120.5,78.6 120.5,78.6 C119.2,72.0 123.4,76.3 123.4,76.3 C127.3,80.9 125.5,87.3 125.5,87.3 C122.9,97.6 130.6,101.9 134.4,103.2" fill="currentColor" style="transform-origin: 130px 106px;" class="octo-arm"></path><path d="M115.0,115.0 C114.9,115.1 118.7,116.5 119.8,115.4 L133.7,101.6 C136.9,99.2 139.9,98.4 142.2,98.6 C133.8,88.0 127.5,74.4 143.8,58.0 C148.5,53.4 154.0,51.2 159.7,51.0 C160.3,49.4 163.2,43.6 171.4,40.1 C171.4,40.1 176.1,42.5 178.8,56.2 C183.1,58.6 187.2,61.8 190.9,65.4 C194.5,69.0 197.7,73.2 200.1,77.6 C213.8,80.2 216.3,84.9 216.3,84.9 C212.7,93.1 206.9,96.0 205.4,96.6 C205.1,102.4 203.0,107.8 198.3,112.5 C181.9,128.9 168.3,122.5 157.7,114.1 C157.9,116.9 156.7,120.9 152.7,124.9 L141.0,136.5 C139.8,137.7 141.6,141.9 141.8,141.8 Z" fill="currentColor" class="octo-body"></path></svg></a><style>.github-corner:hover .octo-arm{animation:octocat-wave 560ms ease-in-out}@keyframes octocat-wave{0%,100%{transform:rotate(0)}20%,60%{transform:rotate(-25deg)}40%,80%{transform:rotate(10deg)}}@media (max-width:500px){.github-corner:hover .octo-arm{animation:none}.github-corner .octo-arm{animation:octocat-wave 560ms ease-in-out}}</style>
