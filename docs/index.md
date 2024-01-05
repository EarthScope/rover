---
title: The EarthScope ROVER user guide
layout: default
---
## Description

ROVER is a command line tool to robustly retrieve geophysical timeseries data from data centers such as [EarthScope](https://www.earthscope.org/data/). It builds an associated index for downloaded data to generate a local repository. ROVER compares a built local index to timeseries availability information provided by the datacenter. This enables a local archive to remain synchronized with a remote data center.

## Documentation

* [Installation](#installation)
* [Quick start](#quickstart)
* [ROVER commands](commands.md)
* [ROVER configuration](configuration.md)
* [Example commands to download data](download.md)
* [Example commands to manage and maintain the local store](maintenance.md)
* [ROVER's change log](changelog.md)
* [ROVER's processing pipeline](pipeline.md)
* [Known bugs and limitations](bugs.md)
* [ROVER development](development.md)

## Installation <a id="installation"></a>

ROVER is a command-line tool that requires Python 2.7, 3.6.2 or a later. Python 3.7 or above running on Linux or macOS are known to work best (pre-installed versions of Python available on some operating systems, such as macOS, may not support ROVER installation or operation without additional work). We suggest installing [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 3 (or the full [Anaconda](https://www.anaconda.com/distribution/#download-section) if you wish) for the best results.

### Option 1

ROVER requires the `C` language program [mseedindex](https://github.com/EarthScope/mseedindex) be available on the system's path. A `C` compiler and the `make` program are required to build mseedindex. ROVER and mseedindex may be downloaded and compiled simultaneously using pip:

    pip install rover[mseedindex]

### Option 2
Alternatively, ROVER and mseedindex may be installed independently.

[mseedindex](https://github.com/EarthScope/mseedindex) may be downloaded and compiled following the [mseedindex install guidelines](mseedindex.md). Similar to installation option 1, building mseedindex is dependent upon the `make` program and a `C` compiler.

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

ROVER is a [EarthScope](https://www.earthscope.org/) product.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Copyright (c) 2018 EarthScope Consortium

