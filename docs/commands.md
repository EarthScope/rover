
# Rover Commands

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

`init-repository` Generates a rover.config file containing rover's default configuation parameters, a data directory, and a logs directory to a target path.

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

`rover retrieve` post a request to the availibilty service defined in rover.config. Returned availibilty data is compared with the local repository's index using maximal timespans across quality and sample rates. Data not available in the local repository are downloaded, ingested, and the index is updated. Retrieve reindexes the local repository before comparing to account for modified data. 

File arguments must only contain a list of text strings that follow the pattern `net sta loc cha YYYY-MM-DDThh:mm:ss YYYY-MM-DDThh:mm:ss` where the first date-string occurs prior to the second date-string. Wild cards of `*` or `?` are accepted to partially or fully replace `net`, `sta`, `loc`, `cha` arguments.

Input text arguments must contain one or more `net`, `sta`, `loc`, `cha` parameters; missing values, `*`, `?` are taken as wildcards. Wild cards are not accepted as starttime or endtime date strings in either file or input text arguments. 

During the retrieve process, the command's status is available at `http://localhost:8000` (default configuration). Users can provide an email address so they are notifed upon completion of `rover retrieve`.

See `rover subscribe` for similar functionality, but with regular updates.
#### Errors, Retries and Consistency

Rover retrieve will repeat until no errors occur or its configurable limit, set by `download-retries`, is reached. Upon apparent process completion an additional retrieval is made, which should result in no data being downloaded. If data are downloaded during the additional retrieval phase then the data availibilty and web services servers are inconsistent.

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

Queries the availibilty service and report a list of requested data availble at the server. 

File arguments must only contain a list of text strings following the pattern `net sta loc cha YYYY-MM-DDThh:mm:ss YYYY-MM-DDThh:mm:ss` where the first date-string occurs prior to the second date-string. Wild cards of `*` or `?` are accepted to partially or fully replace `net`, `sta`, `loc`, `cha` arguments.

Input text arguments must contain one or more `net`, `sta`, `loc`, `cha` parameters; missing values, `*`, `?` are taken as wildcards. Wild cards are not accepted as starttime or endtime date strings in either file or input text arguments. 



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

will display the data missing form the repository to match what is available for the stations in the given file.

    rover list-retrieve IU.ANMO.00.BH1 2017-01-01 2017-01-04

will display the data missing from the repository to match what is available for IU.ANMO.00.BH1.


### List Index

    rover list-index [net=...|sta=...|loc=...|cha=..|qua=...|samp=...]* [begin=...] [end=...] \
    [count|join|join-qsr]

    rover list-index [N_S_L_C_Q]* [begin=...] [end=...] \
    [count|join|join-qsr]

List index entries for the repository (config parameter data-dir) that match the given constraints.

Note that console logging is to stderr, while the command results are listed to stdout.

#### Net_Sta_Chan_Loc_Qual and Samplerate

Query parameters can be named (network, station, location, channel, quality, samplerate) and unambiguous abbreviations are accepted.  Alternatively, a N_S_L_C can be supplied (which can be truncated on the right, but must contain at least one underscore).

The wildcards '*' and '?' can be used.

#### Time Range

The 'begin' and 'end' parameters can be given only once.  They must be of the form YYYY-MM-DDTHH:MM:SS.SSSSSS (may be truncated on the right).  They define a range of times over which the data must appear (at least partially) to be included:

#### Flags

The following parameters are simple flags that change the output format.  They are mutually exclusive and take no value:

  count - only the number of matches will be shown

  join - continguous time ranges will be joined

  join-qsr - the maximal timespan across all quality and samplerates is shown (as used by retrieve)

##### Significant Parameters

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

    rover list-index net=* begin=2001-01-01

will list all entries in the index after the year 2000.


### List Summary

    rover list-summary [net=...|sta=...|loc=...|cha=..]* [begin=...] [end=...]

    rover list-summary [N_S_L_C_Q]* [begin=...] [end=...]

List summary entries for the repository (config parameter data-dir) that match the given constraints. The summary entries are pre-calculated and record the whole time span, from earliest to latest data. Because of this the `list-summary` command runs more quickly, but shows less information, than `list-index`.

Note that console logging is to stderr, while the command results are listed to stdout.

#### Net_Sta_Loc_Chan

Query parameters can be named (network, station, location, channel) and unambiguous abbreviations are accepted.  Alternatively, a N_S_L_C can be supplied (which can be truncated on the right, but must contain at least one underscore).

The wildcards '*' and '?' can be used.

#### Time Range

The 'begin' and 'end' parameters can be given only once.  They must be of the form YYYY-MM-DDTHH:MM:SS.SSSSSS (may be truncated on the right).  They define a range of times over which the data must appear (at least partially) to be included:

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

#### Examples

    rover list-summary net=* begin=2001-01-01

will list all entries in the summary after the year 2000.

## Advanced Usage (Daemon Mode)


### Subscribe

    rover subscribe file

    rover subscribe [net=N] [sta=S] [loc=L] [cha=C] [begin [end]]

    rover subscribe N_S_L_C [begin [end]]

Arrange for the background service (daemon) to regularly compare available data with the repository then download, ingest and index any new data.

This is similar to `rover retrieve`, but uses a background service to regularly update the repository.  To start the service use `rover start`.  See also `rover status` and `rover stop`.

The file argument should contain a list of Net_Sta_Loc_Chans and timespans, as appropriate for calling an Availability service (eg http://service.iris.edu/irisws/availability/1/).

In the second form above, at least one of `net`, `sta`, `loc`, `cha` should be given (missing values are taken as wildcards).  For this and the third form a (single-line) file will be automatically constructed containing that data.

The list of available data is retrieved from the service and compared with the local index.  Data not available locally are downloaded and ingested.

In the comparison of available data, maximal timespans across all quality and sample rates are used (so quality and samplerate information is "merged").

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

will instruct the daemon to regularly download, ingest, and index any data missing from the repository for NSLCs / timespans in the given file.

    rover subscribe IU_ANMO_00_BH1 2017-01-01 2017-01-04

will instruct the daemon to regularly download, ingest and index and data for IU.ANMO.00.BH1 between the given dates that are missing from the repository.

    

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

In addition, parameters relevant to the processing pipeline (see `rover retrieve`, or the individual commands for download, ingest and index) will apply,

Logging for individual processes in the pipeline will automatically configured with `--unique-logs --log-verbosity 3`. For most worker tasks, that will give empty logs (no warnings or errors), which will be automatically deleted (see `rover download`).  To preserve logs, and to use the provided verbosity level, start the daemon with `--dev`,

When the daemon is running status should be visible at http://localhost:8000 (by default).  When a subscription is processed an email can be sent to the user (if `--email` is used).

#### Errors, Retries and Consistency

If `download-retries` allows, subscriptions are re-processed until no errors occur and, once data appear to be complete, an additional retrieval is made which should result in no data being downloaded.  If this is not the case - if additional data are found - then the web services are inconsistent.

Errors and inconsistencies are reported in the logs and in the optional email (`email` parameter) sent to the user.

##### Examples

    rover start -f roverrc

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

Show whether the daemon is running or not..

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

Delete one or more subscriptions.  The arguments can be single numbers (identifying the subscriptions, as displayed by `rover list-subscrive`), or ranges (N:M).

Note: To avoid conflicts with subscriptions that are currently being processed, the daemon must be stopped (with `rover stop`) before using the `unsubscribe` command.

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

Ask the daemon to re-process the given subscriptions.  The arguments can be single numbers (identifying the subscriptions, as displayed by `rover list-subscribe`), or ranges (N:M).

More exactly, this command resets the "last checked" date in the database, so when the daemon re-checks the database (typically once per minute) it will process the subscription.

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

If given a URL, download a single request (typically for a day) to the given path, ingest and index it.  If no path is given then a temporary file is created and deleted after use.  Rover treats the argument as a URL if it contains the characters "://".


The url should be for a Data Select service, and should not request data that spans multiple calendar days.

If given a file name, POST that file to URL given by the `dataselect-url` configuration parameter, download the response to the given path,  ingest and index it.  If no path is given then a temporary file is created and deleted after use.

This task is the main low-level task called in the processing pipeline (it calls ingest and index as needed). Because of this, to reduce the quantity of unhelpful logs generated when a pipeline is running, empty logs are automatically deleted on exit.

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

In addition, parameters for sub-commands (ingest, index) will be used - see help for those commands for more details.

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

    
