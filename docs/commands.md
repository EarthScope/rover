
# Rover Commands

## Normal Usage


### Retrieve

    rover retrieve file

    rover retrieve N.S.L.C begin [end]

Compare available data with the local store, then download, ingest and index data.

The file argument should contain a list of SNCLs and timespans, as appropriate for calling an Availability service (eg http://service.iris.edu/irisws/availability/1/).  Otherwise, if a SNCL and timespan are given, a (single-line) file will be automatically constructed containing that data.

The list of available data is retrieved from the service and compared with the local index.  Data not available locally are downloaded and ingested.

This command also indexes modified data in the store before processing and runs `rover compact --compact-list1 afterwards to check for duplicate data.

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| temp-dir            | ~/rover/tmp          | Temporary storage for downloads |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url        |
| dataselect-url      | http://service.iris.edu/fdsnws/dataselect/1/query | Dataselect service url          |
| timespan-tol        | 0.1                  | Tolerance for overlapping timespans |
| pre-index           | True                 | Index before retrieval?         |
| post-compact        | True                 | Call compact after retrieval?   |
| rover-cmd           | rover                | Command to run rover            |
| mseed-cmd           | mseedindex           | Mseedindex command              |
| mseed-db            | ~/rover/index.sql    | Mseedindex database (also used by rover) |
| verbosity           | 4                    | Console verbosity (0-5)         |
| log-dir             | ~/rover/logs         | Directory for logs              |
| log-name            | rover                | Base file name for logs         |
| log-verbosity       | 5                    | Log verbosity (0-5)             |

In addition, parameters for sub-commands (download, ingest, index, compact) will be used - see help for those commands for more details.

##### Examples

    rover retrieve sncls.txt

    rover retrieve 'U.ANMO.00.BH1 2017-01-01 2017-01-04


### Compare

    rover compare file

    rover compare N.S.L.C begin [end]

Compare available data with the local store, then display what data would be downloaded.  So this command whows what `rover retrieve` would actually retrieve.

The file argument should contain a list of SNCLs and timespans, as appropriate for calling an Availability service (eg http://service.iris.edu/irisws/availability/1/).  Otherwise, if a SNCL and timespan are given, a (single-line) file will be automatically constructed containing that data.

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url        |
| timespan-tol        | 0.1                  | Tolerance for overlapping timespans |
| mseed-db            | ~/rover/index.sql    | Mseedindex database (also used by rover) |
| verbosity           | 4                    | Console verbosity (0-5)         |
| log-dir             | ~/rover/logs         | Directory for logs              |
| log-name            | rover                | Base file name for logs         |
| log-verbosity       | 5                    | Log verbosity (0-5)             |

##### Examples

    rover compare sncls.txt

    rover compare 'U.ANMO.00.BH1 2017-01-01 2017-01-04


### List Index

    rover list-index [net=...|sta=...|loc=...|cha=..|qua=...|samp=...]* \
    [count|join|join-samplerates]

    rover list-index [S.N.C.L.Q]* [begin=...] [end=...] \
    [count|join|join-samplerates]

List index entries for the local store (config parameter mseed-dir) that match the given constraints.

Note that console logging is to stderr, while the command results are listed to stdout.

#### SNCLQ and Samplerate

Query parameters can be named (network, station, location, channel, qualit, samplerate) and unambiguous abbreviations are accepted.  Alternative SNCLQ can be supplied (which can be truncated on the right, but must contain at least one period).

The wildcards '*' and '?' can be used.

#### Time Range

The 'begin' and 'end' parameters can be given only once.  They must be of the form YYYY-MM-DDTHH:MM:SS.SSSSSS (may be truncated on the right).  They define a range of times over which the data must appear (at least partially) to be included:

#### Flags

The following parameters are simple flags that change the output format.  They are mutually exclusive and take no value:

  count - only the number of matches will be shown

  join - continguous time ranges will be joined

  join-samplerates - the maximal timespan across all samplerates is shown (as used by retrieve)

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| timespan-tol        | 0.1                  | Tolerance for overlapping timespans |
| mseed-db            | ~/rover/index.sql    | Mseedindex database (also used by rover) |
| verbosity           | 4                    | Console verbosity (0-5)         |
| log-dir             | ~/rover/logs         | Directory for logs              |
| log-name            | rover                | Base file name for logs         |
| log-verbosity       | 5                    | Log verbosity (0-5)             |

#### Examples

    rover list-index IU.ANMO.00.BH? count

will display the number of entries for all time, and any quality or smaplerate.

    rover list-index net=* begin=2001-01-01

will list all entries in the index after the year 2000.
    

### Reset Config

    rover reset-config

Write default values to the config file.

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| file / -f           | ~/rover/config       | Specify configuration file      |
| verbosity           | 4                    | Console verbosity (0-5)         |
| log-dir             | ~/rover/logs         | Directory for logs              |
| log-name            | rover                | Base file name for logs         |
| log-verbosity       | 5                    | Log verbosity (0-5)             |

##### Examples

    rover reset-config

    rover reset-config --f .roverrc

    
## Advanced Usage (Daemon Mode)


### Subscribe

    rover subscribe

    
## Low-Level Commands

The following commands are used internally, but are usually not useful
from the command line:


### Download

    rover download url

Download a single request (typically for a day), ingest and index it.  After processing, the downloaded data file is deleted.

The url should be for a Data Select service, and should not request data that spans multiple calendar days.

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| temp-dir            | ~/rover/tmp          | Temporary storage for downloads |
| delete-files        | True                 | Delete temporary files?         |
| verbosity           | 4                    | Console verbosity (0-5)         |
| log-dir             | ~/rover/logs         | Directory for logs              |
| log-name            | rover                | Base file name for logs         |
| log-verbosity       | 5                    | Log verbosity (0-5)             |

In addition, parameters for sub-commands (ingest, index, and possibly compact) will be used - see help for those commands for more details.

##### Examples

    rover download \
    http://service.iris.edu/fdsnws/dataselect/1/query?net=IU&sta=ANMO&loc=00&cha=BHZ&start=2010-02-27T06:30:00.000&end=2010-02-27T10:30:00.000

    

### Ingest

    rover ingest file

Add the contents of the file (MSEED format) to the local store and index the new data.

The `mseedindex` command is used to index the different blocks of dta present in the file.  THe corresponding byte ranges are then appended to the appropriate files in the local store.

Optionally, `rover compact` can be called to remove duplicate data (use `--compact`).

The file should not contain data that spans multiple calendar days.

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| mseed-cmd           | mseedindex           | Mseedindex command              |
| mseed-db            | ~/rover/index.sql    | Mseedindex database (also used by rover) |
| mseed-dir           | ~/rover/mseed        | Root of mseed data dirs         |
| compact             | False                | Call compact after ingest?      |
| leap                | True                 | Use leapseconds file?           |
| leap-expire         | 30                   | Number of days before refreshing file |
| leap-file           | ~/rover/leap-seconds.lst | File for leapsecond data        |
| leap-url            | http://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data         |
| verbosity           | 4                    | Console verbosity (0-5)         |
| log-dir             | ~/rover/logs         | Directory for logs              |
| log-name            | rover                | Base file name for logs         |
| log-verbosity       | 5                    | Log verbosity (0-5)             |

In addition, parameters for sub-commands (index, and possibly compact) will be used - see help for those commands for more details.

##### Examples

    rover ingest /tmp/IU.ANMO.00.*.mseed

    rover ingest /tmp/IU.ANMO.00.*.mseed --compact

    

### Compact

    rover compact [--compact-list]

    rover compact (file|dir)+ [--no-recurse] [--compact-list]

Remove (or simply log) duplicate data and then index the file.

When no argument is give all files in the local store are processed.  When a directory is given, all files contained in that directory are processed, along with the contents of sub-directories, unless `--no-recurse` is specified.

If `--compact-list` is given then details of duplicate data are printed to stdou, but no action is taken.

if `--compact-mutate` is given then duplicate data do not have to agree; th emore recent data (appearing later in the file) are preserved.

If `--compact-mixed-types` is given then it is not a fatal error for the duplicate data to have different types (but still, such data will not be de-duplicated).

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| mseed-dir           | ~/rover/mseed        | Root of mseed data dirs         |
| temp-dir            | ~/rover/tmp          | Temporary storage for downloads |
| compact-list        | False                | Detect and list files with duplicate data? |
| compact-mutate      | False                | Allow compact to mutate (replace) data? |
| compact-mixed-types | False                | Allow duplicate data in mixed data types? |
| timespan-tol        | 0.1                  | Tolerance for overlapping timespans |
| verbosity           | 4                    | Console verbosity (0-5)         |
| log-dir             | ~/rover/logs         | Directory for logs              |
| log-name            | rover                | Base file name for logs         |
| log-verbosity       | 5                    | Log verbosity (0-5)             |

In addition, parameters for the sub-command index will be used - see help for that command for more details.

##### Examples

    rover compact --compact-list

will check the entire store for duplicate data.

    

    Run mssedindex on appropriate files (and delete entries for missing files).

    Most of the work is done in the scanner superclasses which find the files     to modify, and in the worker that runs mseedindex.
    
