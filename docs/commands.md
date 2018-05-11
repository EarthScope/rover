
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
| pre-index           | True                 | Index before retrieval?         |
| post-compact        | True                 | Call compact after retrieval?   |
| rover-cmd           | rover                | Command to run rover            |
| mseed-cmd           | mseedindex           | Mseedindex command              |

In addition, parameters for sub-commands (download, ingest, index, compact) will be used - see help for those commands for more details.

##### Examples

    rover retrieve sncls.txt

    rover retrieve 'U.ANMO.00.BH1 2017-01-01 2017-01-04


### List Index

    rover list-index [network=...|station=...|location=...|channel=..|quality=...|samplerate=...]*       [S.N.C.L.Q]* [begin=...] [end=...] [count|join\join-samplerates]

List index entries for the local store (config parameter mseed-dir) that match the given constraints.  For more information, run "rover list-index" (with no arguments).

The list_store command prints entries from the index that match the query parameters.  Parameters generally have the form name=value (no spaces).

#### SNCLQ and Samplerate

The following parameters take '*' and '?' as wildcards, can be repeated for multiple matches (combined with 'OR"), and the name only has to match unambiguously (so cha=HHZ is OK): station, network, channel, location, quality, samplerate.

The short form N.S.L.C.Q can also be used (at a minimum N.S must be supplied).

#### Time Range

The following parameters can be given only once, must be of the form YYYY-MM-DDTHH:MM:SS.SSSSSS (may be truncated on the right), and define a range of times over which the block must appear (at least partially) to be included:

  begin, end

#### Flags

The following parameters are simple flags that change the output format.  They are mutually exclusive and take no value:

  count - only the number of matches will be shown   join - continguous time ranges will be joined   join-samplerates - the maximal timespan across all     samplerates is shown (as used by retrieve)

#### Examples

    rover list-index IU.ANMO.00.BH? count

will display the number of entries for all time, any quality or smaplerate.

    rover list-index net=* begin=2001-01-01

will list all entries in the index after the year 2000.

Note that console logging is to stderr, while results are printed to stdout.
    
## Advanced Usage (Daemon Mode)

## Low-Level Commands

The following commands are used internally, but are usually not useful
from the command line:

