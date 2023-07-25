
# ROVER Commands

* [Normal Usage](#normal-usage)
  * [Init Repository](#init-repository)
  * [Retrieve](#retrieve)
  * [List Retrieve](#list-retrieve)
  * [List Index](#list-index)
  * [List Summary](#list-summary)
* [Low-Level Commands](#low-level-commands)
  * [Download](#download)
  * [Ingest](#ingest)
  * [Index](#index)
  * [Summary](#summary)
  * [Web](#web)
  * [Retrieve-Metadata](#Retrieve-Metadata)

## Common ROVER Commands


### Init Repository

    rover init-repository [directory]

    rover init-repo [directory]

    rover init [directory]

Initializes a given directory, or the current directory if no argument is
provided, as a ROVER data repository. Init repository will create a
configuration file, rover.config, as well as log and data directories.

   The aliases `rover init-repo` and `rover int` also exist.

To avoid over-writing data, rover init-repo returns an error if
a rover.config file, data or log directory exist in the targeted directory.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover init-repository

will create the repository in the current directory.

    rover init-repository ~/rover

will create the repository in ~/rover

    

### Retrieve

    rover retrieve file

    rover retrieve [net=N] [sta=S] [loc=L] [cha=C] [start [end]]

    rover retrieve N_S_L_C [start [end]]

Compares ROVER's local index with remotely available data, then downloads and
ingest files missing from the local repository. The URL determining the
availability of remote data can be configured by the availability-url option,
and URL controlling data downloads is configured by the dataselect-url
option.

Use ROVER's list-index function to determine data available on a remote server
which is not in the local repository.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| temp-dir            | tmp                  | Temporary storage for downloads |
| availability-url    | http://service.iris.edu/fdsnws/availability/1/query | Availability service url       |
| dataselect-url      | http://service.iris.edu/fdsnws/dataselect/1/query | Dataselect service url         |
| timespan-tol        | 0.5                  | Fractional tolerance for overlapping timespans (samples) |
| pre-index           | True                 | Index before retrieval?        |
| ingest              | True                 | Call ingest after retrieval?   |
| index               | True                 | Call index after ingest?       |
| post-summary        | True                 | Call summary after retrieval?  |
| rover-cmd           | rover                | Command to run rover           |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| download-workers    | 5                    | Number of download instances to run |
| download-retries    | 3                    | Maximum number of attempts to download data |
| http-timeout        | 60                   | Timeout for HTTP requests (secs) |
| http-retries        | 3                    | Max retries for HTTP requests  |
| leap-expire         | 30                   | Number of days before refreshing leap seconds file |
| leap-file           | leap-seconds.list    | File for leap second data      |
| leap-url            | https://www.ietf.org/timezones/data/leap-seconds.list | URL for leap second data       |
| web                 | True                 | Auto-start the download progress web server? |
| http-bind-address   | 127.0.0.1            | Bind address for HTTP server   |
| http-port           | 8000                 | Port for HTTP server           |
| email               |                      | Address for completion status  |
| email-from          | noreply@rover        | From address for email         |
| smtp-address        | localhost            | Address of SMTP server         |
| smtp-port           | 25                   | Port for SMTP server           |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |
| temp-expire         | 1                    | Number of days before deleting temp files (days) |
| output-format       | mseed                | Output data format. Choose from "mseed" (miniSEED) or "asdf" (ASDF) |
| asdf-filename       | asdf.h5              | Name of ASDF file when ASDF output is specified |
| force-metadata-reload | False                | Force reload of metadata       |

In addition, options for sub-commands (download, ingest, index) will be used - see help for those
commands for more details.

##### Examples

    rover retrieve N_S_L_C.txt

processes a file containing a request to download, ingest, and index
data missing from ROVER's local repository.

    rover retrieve IU_ANMO_00_BH1 2017-01-01 2017-01-04

processes a command line request to download, ingest, and index
data missing from ROVER's local repository.


### List Retrieve

    rover list-retrieve file

    rover list-retrieve N_S_L_C [start [end]]

Compares the local index with the requested data remotely available, then
displays the difference. Note that the summary is printed to stdout, while
logging is to stderr.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| availability-url    | http://service.iris.edu/fdsnws/availability/1/query | Availability service url       |
| timespan-tol        | 0.5                  | Fractional tolerance for overlapping timespans (samples) |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover list-retrieve N_S_L_C.txt

will display the data missing form the repository to match what is available for the stations in the given file.

    rover list-retrieve IU.ANMO.00.BH1 2017-01-01 2017-01-04

will display the data missing from the repository to match what is available for IU.ANMO.00.BH1.


### List Index

    rover list-index [net=...|sta=...|loc=...|cha=..|qua=...|samp=...]* [start=...] [end=...] \
    [count|join|join-qsr]

    rover list-index [N_S_L_C_Q]* [start=...] [end=...] \
    [count|join|join-qsr]

List an index of entries for a ROVER repository, defined by the the data-dir
configuration options, that match given constraints. For more information,
run "rover list-index" with no arguments.

Flag options used to change the output format are optional arguments.
Flags are mutually exclusive and take no value:

  count - only the number of matches will be shown

  join - continguous time ranges will be joined

  join-qsr - the maximal timespan across all quality and samplerates is shown
  (as used by retrieve)

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| timespan-tol        | 0.5                  | Fractional tolerance for overlapping timespans (samples) |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

#### Examples

    rover list-index IU_ANMO_00_BH? count

will display the number of entries for all time, and any quality or smaplerate.

    rover list-index net=* start=2001-01-01

will list all entries in the index after the year 2000.


### List Summary

    rover list-summary [net=...|sta=...|loc=...|cha=..]* [start=...] [end=...]

    rover list-summary [N_S_L_C_Q]* [start=...] [end=...]

List a summary of entries for a ROVER repository, defined by the data-dir
configuration option, that match given constraints. List summary is faster
than `rover list-index` but gives less detail. For more information,
run "rover list-index" with no arguments.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

#### Examples

    rover list-summary net=* start=2001-01-01

list all entries in the summary after 2001-01-01.

## Low-Level Commands

The following commands are used internally, and are often less
useful from the command line:


### Download

    rover download url [path]

    rover download file [path]

Downloads a single request, typically for a day, from a URL or a given file.
File arguments are expected to contain FDSN web services requests and fetch
data from the URL set by the dataselect-url option. Data are downloaded to a
temporary directory, which is configured by the temp-dir option.
After downloaded, data are ingested into the data-dir repository and are
deleted from the temp directory. `rover download` is called by
`rover retrieve`.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| dataselect-url      | http://service.iris.edu/fdsnws/dataselect/1/query | Dataselect service url         |
| temp-dir            | tmp                  | Temporary storage for downloads |
| http-timeout        | 60                   | Timeout for HTTP requests (secs) |
| http-retries        | 3                    | Max retries for HTTP requests  |
| delete-files        | True                 | Delete temporary files?        |
| ingest              | True                 | Call ingest after retrieval?   |
| index               | True                 | Call index after ingest?       |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

Options used to configure the sub-commands ingest, index are also applicable
- see Ingest/Index help for more details.


##### Examples

    rover download
    'http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000'

will download, ingest and index data from the given URL.

    rover download myrequest.txt

will download, ingest and index data from `dataselect-url` after POSTing
`myrequest.txt`.


### Ingest

    rover ingest file

Adds contents from a miniSEED formatted file to ROVER's local repository and
indexes the new data.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| index               | True                 | Call index after ingest?       |
| leap                | True                 | Use leap seconds file?         |
| leap-expire         | 30                   | Number of days before refreshing leap seconds file |
| leap-file           | leap-seconds.list    | File for leap second data      |
| leap-url            | https://www.ietf.org/timezones/data/leap-seconds.list | URL for leap second data       |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

Options used to configure the sub-command index are also applicable -
see Index help for more details.

##### Examples

    rover ingest /tmp/IU.ANMO.00.*.mseed

will add all the data in the given file to the repository.


### Index

    rover index [--all]

    rover index (file|dir)+

Indexes files, adds or changes entries in the tsindex table stored in the
miniSEED database.

When no argument is given, all modified files in the repository are processed.
The `--all` flag forces all files to be processed. If a path argument
is provided, all files contained in the directory are processed, along with
the contents of sub-directories, unless `--no-recurse` is specified.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| all                 | False                | Process all files (not just modified)? |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| mseedindex-workers  | 10                   | Number of mseedindex instances to run |
| leap                | True                 | Use leap seconds file?         |
| leap-expire         | 30                   | Number of days before refreshing leap seconds file |
| leap-file           | leap-seconds.list    | File for leap second data      |
| leap-url            | https://www.ietf.org/timezones/data/leap-seconds.list | URL for leap second data       |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover index --all

will index the entire repository.


### Summary

    rover summary

Creates a summary of the index stored in a ROVER repository. This lists the
overall span of data for each Net_Sta_Loc_Chan and can be queried using
`rover list-summary`.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover summary

will create the summary of a local ROVER repository.


    

### Web

    rover web

    rover web --http-bind-address 0.0.0.0 --http-port 8080

    rover retrieve --web ...   # the default

Starts a web server that provides information on the progress of the download
manager. ROVER's default configuration starts `rover web` automatically.
The flag`--no-web` prevents ROVER's web server from launching in accordance
with `rover retrieve`.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| web                 | True                 | Auto-start the download progress web server? |
| http-bind-address   | 127.0.0.1            | Bind address for HTTP server   |
| http-port           | 8000                 | Port for HTTP server           |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover retrieve --no-web

will run retrieve without the web server.

    

### Retrieve-Metadata

    rover retrieve-metadata

Download missing metadata from the fdsnws-station web service and save to the
data archive. This feature is only supported for the ASDF output format.

##### Significant Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| temp-dir            | tmp                  | Temporary storage for downloads |
| station-url         | http://service.iris.edu/fdsnws/station/1/query | Station service url            |
| rover-cmd           | rover                | Command to run rover           |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| download-retries    | 3                    | Maximum number of attempts to download data |
| http-timeout        | 60                   | Timeout for HTTP requests (secs) |
| http-retries        | 3                    | Max retries for HTTP requests  |
| http-bind-address   | 127.0.0.1            | Bind address for HTTP server   |
| http-port           | 8000                 | Port for HTTP server           |
| email               |                      | Address for completion status  |
| email-from          | noreply@rover        | From address for email         |
| smtp-address        | localhost            | Address of SMTP server         |
| smtp-port           | 25                   | Port for SMTP server           |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |
| output-format       | mseed                | Output data format. Choose from "mseed" (miniSEED) or "asdf" (ASDF) |
| asdf-filename       | asdf.h5              | Name of ASDF file when ASDF output is specified |
| force-metadata-reload | False                | Force reload of metadata       |

##### Examples

If the "output-format" rover.config setting is set to "asdf" then

    rover retrieve-metadata

will download missing metadata from the asdf.h5 repository.
