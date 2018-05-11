
# Rover Commands

## Normal Usage


### Retrieve

    rover retrieve file

    rover retrieve N.S.L.C begin [end]

Compare available data with the local store, then download, ingest and index data.

The file argument should contain a list of SNCLs and timespans, as appropriate for calling an Availability service (eg http://service.iris.edu/irisws/availability/1/).  Otherwise, if a SNCL and timespan are given, a (single-line) file will be automatically constructed containing that data.

The list of available data is retrieved from the service and compared with the local index.  Data not available locally are downloaded and ingested.

This command also indexes modified data in the store before processing and runs \`rover compact --compact-list1 afterwards to check for duplicate data.

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| temp-dir            | ~/rover/tmp          | Temporary storage for downloads |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url        |
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

Compare available data with the local store, then display what data would be downloaded.  So this command whows what \`rover retrieve\` would actually retrieve.

The file argument should contain a list of SNCLs and timespans, as appropriate for calling an Availability service (eg http://service.iris.edu/irisws/availability/1/).  Otherwise, if a SNCL and timespan are given, a (single-line) file will be automatically constructed containing that data.

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url        |
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
    
## Advanced Usage (Daemon Mode)


### Retrieve

    rover retrieve file

    rover retrieve N.S.L.C begin [end]

Compare available data with the local store, then download, ingest and index data.

The file argument should contain a list of SNCLs and timespans, as appropriate for calling an Availability service (eg http://service.iris.edu/irisws/availability/1/).  Otherwise, if a SNCL and timespan are given, a (single-line) file will be automatically constructed containing that data.

The list of available data is retrieved from the service and compared with the local index.  Data not available locally are downloaded and ingested.

This command also indexes modified data in the store before processing and runs \`rover compact --compact-list1 afterwards to check for duplicate data.

##### Significant Parameters

|  Name               | Default              | Description                     |
| ------------------- | -------------------- | ------------------------------- |
| temp-dir            | ~/rover/tmp          | Temporary storage for downloads |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url        |
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

## Low-Level Commands

The following commands are used internally, but are usually not useful
from the command line:


    Download a single request (typically for a day), ingest and index it (ingest calls     index, so we just call ingest).

    The only complex thing here is that these may run in parallel.  That means that     multiple ingest instances can be running in parallel, all using  mseedindex.     To avoid conflict over sqlite access we use a different database file for each,     so we need to track and delete those.

    To do this we have a table that lists ingesters, along with URLs, PIDs,     database paths and epochs.

    This isn't a problem for the main ingest command because only a single instance     of the command line command runs at any one time.
    

    The simplest possible ingester:     * Uses mseedindx to parse the file.     * For each section, appends to any existing file using byte offsets     * Refuses to handle blocks that cross day boundaries     * Does not check for overlap, differences in sample rate, etc. (see compact)
    

    Compact modified files (remove redundant mseed data and tidy).

    We do this by bubble-sorting the data blocks, merging data when     appropriate.  This allows us to replace data with the latest (later     in the file) values.

    We also check whether duplicate data are mutated and raise an error     if so (unless --compact-mutate is set).

    If --compact-list then simply list prooblems, don't fic them.

    Note that sorting seems to have no effect - the obspy code doesn't respect the     changed order on writing (in fact the order appears to be already sorted and     doesn't reflect the actual ordering in the file).
    

    Run mssedindex on appropriate files (and delete entries for missing files).

    Most of the work is done in the scanner superclasses which find the files     to modify, and in the worker that runs mseedindex.
    
