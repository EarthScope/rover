
# ROVER Commands

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

## Common ROVER Commands


### Init Repository

    rover init-repository [directory]

    rover init-repo [directory]

    rover init [directory]

Initializes a given directory, or the current directory if no argument is provided, as a ROVER data repository. Init repository will create a configuration file, rover.config, as well as log and data directories.
 
   The aliases `rover init-repo` and `rover int` also exist.

To avoid over-writing data, rover init-repo returns an error if a rover.config file, data or log directory exist in the targeted directory.

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

Compares ROVER's local index with remotely available data, then downloads and ingest files missing from the local repository. The URL determining the availability of remote data can be configured by the availability-url parameter, and URL controlling data downloads is configured by the dataselect-url parameter.

Use ROVER's list-index function to determine data available on a remote server which is not in the local repository.
   
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
| leap-expire         | 30                   | Number of days before reloading file |
| leap-file           | leap-seconds.list    | File for leapsecond data       |
| leap-url            | https://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
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
| output-format       | mseed                | Output data format. Choose from "mseed" or "asdf" |
| asdf-filename       | asdf.h5              | Name of asdf file to create when OUTPUT_FORMAT=asdf |
| force-metadata-reload | False                | Force reload of metadata       |

In addition, parameters for sub-commands (download, ingest, index) will be used - see help for those commands for more details.

##### Examples

    rover retrieve N_S_L_C.txt

processes a file containing a request to download, ingest, and index data missing from rover’s local repository.
    
    rover retrieve IU_ANMO_00_BH1 2017-01-01 2017-01-04

processes a command line request to download, ingest, and index data missing from rover’s local repository.


### List Retrieve

    rover list-retrieve file

    rover list-retrieve N_S_L_C [begin [end]]

Compares the local index with the requested data remotely available, then displays the difference. Note that the summary is printed to stdout, while logging is to stderr.

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

List an index of entries for a ROVER repository, defined by the the data-dir configuration parameter, that match given constraints. For more information, run "rover list-index" with no arguments.

Flag parameters used to change the output format are optional arguments. Flags are mutually exclusive and take no value:

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

List a summary of entries for a ROVER repository, defined by the data-dir configuration parameter, that match given constraints. List summary is faster than `rover list-index` but gives less detail.  For more information, run "rover %s" with no arguments.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

#### Examples

    rover list-summary net=* begin=2001-01-01

list all entries in the summary after 2001-01-01.

## Advanced ROVER Commands


### Subscribe

    rover subscribe file

    rover subscribe [net=N] [sta=S] [loc=L] [cha=C] [begin [end]]

    rover subscribe N_S_L_C [begin [end]]

Subscribe generates a background service, daemon, that regularly compares data available at the configured server with the local repository. If there is a discrepancy, available data is downloaded, ingested and indexed. ROVER subscribe is similar to `rover retrieve` but uses a daemon to regularly update a local repository.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url       |
| dataselect-url      | http://service.iris.edu/fdsnws/dataselect/1/query | Dataselect service url         |
| force-request       | False                | Skip overlap checks (dangerous)? |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |
| temp-dir            | tmp                  | Temporary storage for downloads |

Most of the download process is controlled by the parameters provided when starting the service (see `rover start`).

##### Examples

    rover subscribe N_S_L_C.txt

will instruct the daemon to regularly download, ingest, and index any data missing from the repository for NSLCs / timespans in the given file.

    rover subscribe IU_ANMO_00_BH1 2017-01-01 2017-01-04

will instruct the daemon to regularly download, ingest and index and data for IU.ANMO.00.BH1 between the given dates that are missing from the repository.

    

### Start

Starts the background, daemon, process to support `rover subscribe`. The parameter, --recheck-period, sets the time interval in hours for the daemon to reprocess. ROVER start is the preferred method to begin a ROVER subscription.

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

In addition, parameters relevant to the processing pipeline (see `rover retrieve` , or the individual commands for download, ingest and index) apply.

##### Examples

    rover start -f roverrc

will start the daemon using the given configuration file.

    rover start --recheck-period 24

will start the daemon, processing subscriptions every 24 hours.

    

### Stop

Stop the background, daemon, process to support `rover subscribe`.

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

will show whether a daemon, using a given configuration file, is running.

    

### Unsubscribe

    rover unsubscribe N[:M]+

Deletes one or more subscriptions identified by their indices. ROVER list-subscribe displays subscription indices. Unsubscribe accepts integers or ranges of integers (N:M) as arguments. Data associated with a subscription(s) are not deleted.

To avoid conflicts with subscriptions that are currently being processed, `rover stop` must stop the daemon before using the unsubscribe command.

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

Ask the daemon to immediately re-process a subscription(s) based on its index. List-subscribe displays subscriptions indices. Trigger accepts integers or ranges of integers (N:M) as arguments.

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

The following commands are used internally, and are often less
useful from the command line:


### Download

    rover download url [path]

    rover download file [path]

Downloads a single request, typically for a day, from a URL or a given file. File arguments are expected to contain FDSN web services requests and fetch data from the URL set by the dataselect-url parameter. Data are downloaded to a temporary directory, which is configured by the temp-dir parameter. After downloaded, data are ingested into the data-dir repository and are deleted from the temp directory. `rover download` is called by `rover retrieve`, 'rover subscribe` and `rover daemon`.

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

Parameters used to configure the sub-commands ingest, index are also applicable - see Ingest/Index help for more details.


##### Examples

    rover download 'http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000'

will download, ingest and index data from the given URL.

    rover download myrequest.txt

will download, ingest and index data from `dataselect-url` after POSTing `myrequest.txt`.


### Ingest

    rover ingest file

Adds contents from a miniSEED formatted file to ROVER's local repository and indexes the new data.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| index               | True                 | Call index after ingest?       |
| leap                | True                 | Use leapseconds file?          |
| leap-expire         | 30                   | Number of days before reloading file |
| leap-file           | leap-seconds.list    | File for leapsecond data       |
| leap-url            | https://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

Parameters used to configure the sub-command index are also applicable - see Index help for more details.

##### Examples

    rover ingest /tmp/IU.ANMO.00.*.mseed

will add all the data in the given file to the repository.


### Index

    rover index [--all]

    rover index (file|dir)+

Indexes files, adds or changes entries in the tsindex table stored in the miniSEED database.
 
When no argument is given, all modified files in the repository are processed. The `--all` flag forces all files to be processed. If a path argument is provided, all files contained in the directory are processed, along with the contents of sub-directories, unless `--no-recurse` is specified.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| all                 | False                | Process all files (not just modified)? |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| mseedindex-workers  | 10                   | Number of mseedindex instances to run |
| leap                | True                 | Use leapseconds file?          |
| leap-expire         | 30                   | Number of days before reloading file |
| leap-file           | leap-seconds.list    | File for leapsecond data       |
| leap-url            | https://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover index --all

will index the entire repository.


### Summary

    rover summary

Creates a summary of the index stored in a ROVER repository. This lists the overall span of data for each Net_Sta_Loc_Chan and can be queried using `rover list-summary`.

##### Significant Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| verbosity           | 4                    | Console verbosity (0-6)        |
| log-dir             | logs                 | Directory for logs             |
| log-verbosity       | 4                    | Log verbosity (0-6)            |

##### Examples

    rover summary

will create the summary of a local ROVER repository.


    

### Daemon

The background, daemon, process that supports `rover subscribe`. ROVER's start command is the preferred method to launch the subscription service.

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

##### Examples

    rover daemon -f roverrc

will start the daemon in the foreground using the given configuration file.
  
    rover start --recheck-period 24

will start the daemon in the foreground, processing subscriptions every 24 hours.

REMINDER: ROVER start is the preferred method to launch the subscription service. 

    

### Web

    rover web

    rover web --http-bind-address 0.0.0.0 --http-port 8080

    rover start --web ...   # the default

    rover retrieve --web ...   # the default

Starts a web server that provides information on the progress of the download manager, the core of the `rover daemon` and `rover retrieve` commands. ROVER's default configuration starts `rover web` automatically. The flag`--no-web` prevents ROVER's web server from launching in accordance with `rover retrieve` or `rover start`.

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

    

### Retrieve

    rover retrieve-metadata

Download missing metadata from the fdsnws-station web service and save to the data archive. This feature is only supported for the ASDF output format.

##### Significant Parameters

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
| output-format       | mseed                | Output data format. Choose from "mseed" or "asdf" |
| asdf-filename       | asdf.h5              | Name of asdf file to create when OUTPUT_FORMAT=asdf |
| force-metadata-reload | False                | Force reload of metadata       |

##### Examples

If the "output-format" rover.config setting is set to "asdf" then

    rover retrieve-metadata

will download missing metadata from the asdf.h5 repository.
