---
title: Rover Commands
layout: default
---

* [Normal Usage](#normal-usage)
  * [Init Repository](#init-repository)
  * [Retrieve](#retrieve)
  * [List Retrieve](#list-retrieve)
  * [List Index](#list-index)
  * [List Summary](#list-summary)
* [Advanced Usage](#advanced-usage)
  * [Subscribe](#subscribe)
  * [Start](#start)
  * [Stop](#stop)
  * [Status](#status)
  * [Unsubscribe](#unsubscribe)
  * [Trigger](#trigger)
* [Low-Level Commands](#low-level-commands)
  * [Download](#download)
  * [Ingest](#ingest)
  * [Index](#index)
  * [Summary](#summary)
  * [Daemon](#daemon)
  * [Web](#web)

## Normal Usage


### Init Repository

    rover init-repository [directory]

    rover init-repo [directory]

    rover init [directory]

`init-repository` generates a rover.config file containing rover's default configuration parameters; a rover.config file, a data directory, and a logs directory to a target path.

To avoid over-writing data, `rover init-repository` returns an error if the command's target directory contains the file rover.config, or the directories data or logs.

##### Significant Parameters

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

    rover retrieve [net=N] [sta=S] [loc=L] [cha=C] [begin [end]]

    rover retrieve N_S_L_C [begin [end]]

`rover retrieve` post a URL request to the availability service defined in rover.config. Returned availability data is compared with a local repository's index using maximal timespans across quality and sample rates. Data not available in the local repository are downloaded, ingested, and the index is updated. Retrieve reindexes the local repository before comparing to account for modified data. 

File arguments must only contain a list of text strings following the pattern `net sta loc cha YYYY-MM-DDThh:mm:ss YYYY-MM-DDThh:mm:ss` where the first date-string occurs prior to the second date-string. Wild cards of `*` or `?` are accepted to partially or fully replace `net`, `sta`, `loc`, `cha` arguments. Starttime and endtime arguments cannot be assigned as a wildcard. For non-file arguments One or more `net`, `sta`, `loc`, `cha` input arguments must be provided; missing values are taken as wildcards.  

During the retrieve process, the command's status is available at `http://localhost:8000` (default configuration). Users can provide an email address that is notified upon completion of `rover retrieve`.

See `rover subscribe` for similar functionality, but with regular updates.
#### Errors, Retries and Consistency

Rover retrieve will repeat until no errors occur and no more data is downloaded or its configurable limit of download attempts returning 0 bytes of data, set by `download-retries`, is reached. Upon apparent process completion an additional retrieval is made, which should result in no data being downloaded. If data are downloaded during the additional retrieval phase then the data availability and web services servers are inconsistent.

Inconsistencies cause rover processes to exit with an error status and are reported in the logs directory and via the configurable email parameter.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| temp-dir            | tmp                  | Temporary storage for downloads |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url       |
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
| leap-expire         | 30                   | Number of days before refreshing file |
| leap-file           | leap-seconds.list    | File for leapsecond data       |
| leap-url            | http://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
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

Additional sub-command (download, ingest, index) parameters affect retrieve - see the subcommand's documentation for more details.

##### Examples

    rover retrieve N_S_L_C.txt

will process a request to download, ingest, and index data missing from rover's local repository.
    
    rover retrieve IU_ANMO_00_BH1 2017-01-01 2017-01-04


### List Retrieve

    rover list-retrieve file

    rover list-retrieve N_S_L_C [begin [end]]

Queries the availability service and compares these data with the local repository's index using maximal timespans across quality and sample rates. A list of requested data available at the server that are not present in the local repository is returned to the user. 

File arguments must only contain a list of text strings following the pattern `net sta loc cha YYYY-MM-DDThh:mm:ss YYYY-MM-DDThh:mm:ss` where the first date-string occurs prior to the second date-string. Wild cards of `*` or `?` are accepted to partially or fully replace `net`, `sta`, `loc`, `cha` arguments. Starttime and endtime arguments cannot be assigned as a wildcard. For non-file arguments one or more `net`, `sta`, `loc`, `cha` input arguments must be provided; missing values are taken as wildcards.  



##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url       |
| timespan-tol        | 0.5                  | Fractional tolerance for overlapping timespans (samples) |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover list-retrieve N_S_L_C.txt

displays data that are available in the host repository but are missing from the local repository.

    rover list-retrieve IU.ANMO.00.BH1 2017-01-01 2017-01-04

displays data that are available in the host repository but are missing from the local repository.


### List Index

    rover list-index [net=...|sta=...|loc=...|cha=..|qua=...|samp=...]* [begin=...] [end=...] \
    [count|join|join-qsr]

    rover list-index [N_S_L_C_Q]* [begin=...] [end=...] \
    [count|join|join-qsr]

`list_index` returns data available in the local repository (config parameter data-dir) that match given arguments. `list_index` accepts arguments of net=XX  sta=XXXX loc=XX cha=XXX qua=XX samp=XXX  begin=YYYY-MM-DDThh:mm:ss end=YYYY-MM-DDThh:mm:ss. Wild cards of `*` or `?` are accepted to partially or fully replace `net`, `sta`, `loc`, `cha`, `qua`, `samp` arguments. Starttime and endtime arguments cannot be assigned a wildcard. One or more `net`, `sta`, `loc`, `cha`,  `qua`, `samp`  input arguments must be provided; missing values are taken as wildcards.  
  Alternatively, a N_S_L_C begin=YYYY-MM-DDThh:mm:ss end=YYYY-MM-DDThh:mm:ss can be supplied as arguments. N_S_L_C  can be truncated to the station level. 


Flag parameters used to change the output format are optional arguments. Flags are mutually exclusive and take no value:

 ` count - displays the total number of matches.`

  `join - displays data available as continuous time ranges separated by data quality and sample rate. `

  `join-qsr - displays the maximal timespan across all quality and sample rates, similar to the process `retrieve`.`
  


#### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| timespan-tol        | 0.5                  | Fractional tolerance for overlapping timespans (samples) |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

#### Examples

    rover list-index IU_ANMO_00_BH? count

displays the total number of entries for all time, data quality, and sample rate.

    rover list-index net=* begin=2001-01-01

lists all available data in the local repository after the year 2000.

  Note that console logging is to stderr, while the command results are listed to stdout.


### List Summary

    rover list-summary [net=...|sta=...|loc=...|cha=..]* [begin=...] [end=...]

    rover list-summary [N_S_L_C_Q]* [begin=...] [end=...]

`list_summary` returns data available in the local repository (config parameter data-dir) that match given arguments. 
The summary entries are pre-calculated and record the whole time span, from the earliest to the latest data. `list-summary` is faster than `list-index` but shows less information.

Please note that console logging is to stderr, while the command results are listed to stdout.

#### Net_Sta_Loc_Chan

Query parameters can be named (network, station, location, channel) and unambiguous abbreviations are accepted.  Alternatively, a N_S_L_C can be supplied. N_S_L_C can be truncated on the right, but must contain at least one underscore.

Wildcards '*' and '?' can be used.

#### Time Range

The 'begin' and 'end' parameters can be provided only once per request.  They must be in the form YYYY-MM-DDTHH:MM:SS.SSSSSS, which may be truncated on the right. 'begin' and 'end' define a time range from which data are queried. 

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

#### Examples

    rover list-summary net=* begin=2001-01-01

list all entries in the summary after the year 2000.

## Advanced Usage (Daemon Mode)


### Subscribe

    rover subscribe file

    rover subscribe [net=N] [sta=S] [loc=L] [cha=C] [begin [end]]

    rover subscribe N_S_L_C [begin [end]]

`subscribe` generates a background service (daemon) that regularly compares data available at the configured server with the local repository. If there is a discrepancy, available data is downloaded, ingested and indexed. `subscribe` is similar to `rover retrieve` but uses a daemon to regularly update the local repository. `rover start` begins the subscription service.  See also `rover status` and `rover stop`.

The file argument should contain a list of Net_Sta_Loc_Chans and timespans, as appropriate for calling an Availability service (eg http://service.iris.edu/irisws/availability/1/).


File arguments must only contain a list of text strings following the pattern `net sta loc cha YYYY-MM-DDThh:mm:ss YYYY-MM-DDThh:mm:ss` where the first date-string occurs prior to the second date-string. Wild cards of `*` or `?` are accepted to partially or fully replace `net`, `sta`, `loc`, `cha` arguments. Starttime and endtime arguments cannot be assigned as a wildcard. For non-file arguments one or more `net`, `sta`, `loc`, `cha` input arguments must be provided; missing values are taken as wildcards.  

`subscribe` periodically retrieves a list of available data from a server's availability service and compares it with the local index.  Data not available locally are downloaded and ingested. Availability service data are compared with the local repository's index using maximal timespans across quality and sample rates. A list of requested data available at the server that are not present in the local repository is returned. The returned list determines the data that is downloaded and ingested for the server's data services. 

A user may have multiple subscriptions (see `rover list-subscribe`), but to avoid downloading duplicate data they must not describe overlapping data.  To enforce this, requests are checked on submission.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url       |
| dataselect-url      | http://service.iris.edu/fdsnws/dataselect/1/query | Dataselect service url         |
| force-request       | False                | Skip overlap checks (dangerous)? |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

Most of the download process is controlled by the parameters provided when starting the service (see `rover start`).

##### Examples

    rover subscribe N_S_L_C.txt

will instruct the daemon to periodically download, ingest, and index any data missing from the repository for NSLCs / timespans in the given file.

    rover subscribe IU_ANMO_00_BH1 2017-01-01 2075-01-04

will instruct the daemon to periodically download, ingest and index data for IU.ANMO.00.BH1. Rover subscribe can be set into the future to update a local repository in semi-real time.

    

### Start

Start the background (daemon) process to support `rover subscribe`.

See also `rover stop`, `rover status` and `rover daemon`.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| rover-cmd           | rover                | Command to run rover           |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| download-workers    | 5                    | Number of download instances to run |
| mseedindex-workers  | 10                   | Number of mseedindex instances to run |
| temp-dir            | tmp                  | Temporary storage for downloads |
| subscriptions-dir   | subscriptions        | Directory for subscriptions    |
| recheck-period      | 12                   | Time between availabilty checks (hours) |
| download-retries    | 3                    | Maximum number of attempts to download data |
| http-timeout        | 60                   | Timeout for HTTP requests (secs) |
| http-retries        | 3                    | Max retries for HTTP requests  |
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
| dev                 | False                | Development mode (show exceptions)? |

In addition, parameters relevant to the processing pipeline (see `rover retrieve`, or the individual commands for download, ingest and index) will apply.

Logging for individual processes in the pipeline will automatically be configured with `--unique-logs --log-verbosity 3`. For most worker tasks, that will give empty logs (no warnings or errors), which will be automatically deleted (see `rover download`).  To preserve logs, and to use the provided verbosity level, start the daemon with `--dev`,

When the daemon is running status should be visible at http://localhost:8000 (by default).  When a subscription is processed an email can be sent to the user (if `--email` is used).

#### Errors, Retries and Consistency

Similar to `rover retrieve`, `subscribe` will repeat until no errors occur and no more data is downloaded or its configurable limit of download attempts returning 0 bytes of data, set by `download-retries`, is reached. Upon apparent process completion an additional retrieval is made, which should result in no data being downloaded. If data are downloaded during the additional retrieval phase then the data availability and web services servers are inconsistent.

Errors and inconsistencies are reported in the logs and in the optional email (`email` parameter) sent to the user.

##### Examples

    rover start -f /path/to/rover.config

will start the daemon using the given configuration file.

    rover start --recheck-period 24

will start the daemon, processing subscriptions every 24 hours.

    

### Stop

Stop the background (daemon) process to support `rover subscribe`.

See also `rover start`, `rover status`.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover stop -f roverrc

will stop the daemon that was started using the given configuration file.

    

### Status

Displays if the daemon is operating. 

See also `rover start`, `rover stop`.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover status -f roverrc

will show whether the daemon using the given configuration file is running.

    

### Unsubscribe

    rover unsubscribe N[:M]+

Delete one or more subscriptions indentified by their indices. `rover list-subscribe` displays subscriptions indices. `unsubscribe` accepts integers or ranges of integers (N:M) as arguments.

To avoid conflicts with subscriptions that are currently being processed, `rover stop` must stop the daemon before using the `unsubscribe` command.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover unsubscribe 1:3

will delete subscriptions 1, 2 and 3.

    

### Trigger

    rover trigger N[:M]+

Ask the daemon to re-process a subscription(s) based on its index. `rover list-subscribe` displays subscriptions indices. `tirgger` accepts integers or ranges of integers (N:M) as arguments.

More exactly, this command resets the "last checked" date in the database, so when the daemon re-checks the database ,typically once per minute, it will process the subscription.

#### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover trigger 2

will ask the daemon to re-process subscription 2.

    
## Low-Level Commands

The following commands are used internally, but are usually not useful
from the command line:


### Download

    rover download url [path]

    rover download file [path]

`Rover download` downloads a single request, typically for a day, from a URL to a given path. The downloaded data is ingested and indexed into the local repository. If no path is given then a temporary file is created and deleted after use.  Rover treats the argument as a URL if it contains the characters "://". `rover retrieve` generates workers that call `rover download` in the terminal. 

The URL must be for a Data Select service, and can not request data that spans multiple calendar days.

File arguments are sent as POST to the URL set in the `dataselect-url` configuration parameter. Requested data are downloaded to the path argument, ingested and indexed.  If no path is given then a temporary file is created and deleted after use.

`download` is the main low-level task called in the processing pipeline. Each instances of download calls ingest and index as long as they are configured as true. To reduce the quantity of unhelpful logs generated when a pipeline is running, empty logs are automatically deleted on exit.

##### Significant Parameters

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

Parameters used to configure the sub-commands ingest, index are also applicable - see help for those commands for more details.

##### Examples

    rover download \
    'http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000'

will download, ingest and index data from the given URL.

    rover download myrequest.txt

will download, ingest and index data from `dataselect-url` after POSTing `myrequest.txt`.


### Ingest

    rover ingest file

Add the contents of the file (MSEED format) to the repository and index the new data.

The `mseedindex` command is used to index the different blocks of dta present in the file.  THe corresponding byte ranges are then appended to the appropriate files in the repository.

The file should not contain data that spans multiple calendar days.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| index               | True                 | Call index after ingest?       |
| leap                | True                 | Use leapseconds file?          |
| leap-expire         | 30                   | Number of days before refreshing file |
| leap-file           | leap-seconds.list    | File for leapsecond data       |
| leap-url            | http://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

In addition, parameters for sub-commands (index) will be used - see help for those commands for more details.

##### Examples

    rover ingest /tmp/IU.ANMO.00.*.mseed

will add all the data in the given file to the repository.


### Index

    rover index [--all]

    rover index (file|dir)+

Index the files (add or change entires in the tsindex table in the mseed database).

When no argument is give all modified files in the repository are processed.  To force all files, use `--all`.

When a directory is given, all files contained in that directory are processed, along with the contents of sub-directories, unless `--no-recurse` is specified.

The `mseedindex` command is used to index the data.  This optionally uses a file of leap-second data.  By default (unless `--no-leap`) a file is downloaded from `--leap-url` if the file currently at `--leap-file` is missing or older than `--leap-expire` days.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| all                 | False                | Process all files (not just modified)? |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| mseedindex-workers  | 10                   | Number of mseedindex instances to run |
| leap                | True                 | Use leapseconds file?          |
| leap-expire         | 30                   | Number of days before refreshing file |
| leap-file           | leap-seconds.list    | File for leapsecond data       |
| leap-url            | http://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover index --all

will index the entire repository.


### Summary

    rover summary

Create a summary of the index in the database.  This lists the overall span of data for each Net_Sta_Loc_Chan and can be queries using `rover list-summary`.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover summary

will create the summary.


    

### Daemon

The background (daemon) process that supports `rover subscribe`.

**Prefer using `rover start` to start this task in the background.**

See also `rover stop`, `rover status`.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| rover-cmd           | rover                | Command to run rover           |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| download-workers    | 5                    | Number of download instances to run |
| mseedindex-workers  | 10                   | Number of mseedindex instances to run |
| temp-dir            | tmp                  | Temporary storage for downloads |
| subscriptions-dir   | subscriptions        | Directory for subscriptions    |
| recheck-period      | 12                   | Time between availabilty checks (hours) |
| download-retries    | 3                    | Maximum number of attempts to download data |
| http-timeout        | 60                   | Timeout for HTTP requests (secs) |
| http-retries        | 3                    | Max retries for HTTP requests  |
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
| dev                 | False                | Development mode (show exceptions)? |

In addition, parameters relevant to the processing pipeline (see `rover retrieve`, or the individual commands for download, ingest and index) will apply,

Logging for individual processes in the pipeline will automatically configured with `--unique-logs --log-verbosity 3`. For most worker tasks, that will give empty logs (no warnings or errors), which will be automatically deleted (see `rover download`).  To preserve logs, and to use the provided verbosity level, start the daemon with `--dev`,

When the daemon is running status should be visible at http://localhost:8000 (by default).  When a subscription is processed an email can be sent to the user (if `--email` is used).

#### Errors, Retries and Consistency

If `download-retries` allows, subscriptions are re-processed until no errors occur and, once data appear to be complete, an additional retrieval is made which should result in no data being downloaded.  If this is not the case - if additional data are found - then the web services are inconsistent.

Errors and inconsistencies are reported in the logs and in the optional email (`email` parameter) sent to the user.

##### Examples

    rover daemon -f roverrc

will start the daemon (in the foreground - see `rover start`) using the given configuration file.

    rover start --recheck-period 24

will start the daemon (in the foreground - see `rover start`), processing subscriptions every 24 hours.

    

### Web

    rover web

    rover web --http-bind-address 0.0.0.0 --http-port 8080

    rover start --web ...   # the default

    rover retrieve --web ...   # the default

Start a web server that provides information on the progress of the download manager (the core of the `rover daemon` and `rover retrieve` commands).

With the default configuration this is started automatically, provided `--no-web` is not used with `rover retrieve` or `rover start`.

As with the `rover download` command, empty logs are removed on exit to avoid cluttering the log directory.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| web                 | True                 | Auto-start the download progress web server? |
| http-bind-address   | 127.0.0.1            | Bind address for HTTP server   |
| http-port           | 8000                 | Port for HTTP server           |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover start --no-web

will start the daemon without the web server.

    
