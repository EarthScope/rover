
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

### Compare
      
    rover compare (file|sncl start [end])

Compare the local index (config parameter mseed-db) with the data
availabe remotely (config parameter availability-url), then display
the difference.  Note that the summary is printed to stdout, while
logging is to stderr.

##### Examples

    rover compare targets.list

will list the downloads needed to retrieve everything in the given
file (that is not already present in the local store).

    rover compare IU.ANMO.00.BH1 2017-01-01

will list the downloads needed to retrieve missing data for
IU.ANMO.00.BH1 from Jan 1 2017 onwards.

### List Index

    rover list-index [network=...|station=...|location=...|channel=..|quality=...|samplerate=...]*
      [S.N.C.L.Q]* [begin=...] [end=...] [count|join\join-samplerates]
    
List index entries for the local store (config parameter mseed-dir)
that match the given constraints.  For more information, run "rover
list-index" (with no arguments).

The list_store command prints entries from the index that match 
the query parameters.  Parameters generally have the form 
name=value (no spaces).

#### SNCLQ and Samplerate

The following parameters take '*' and '?' as wildcards, can be
repeated for multiple matches (combined with 'OR"), and the name only
has to match unambiguously (so cha=HHZ is OK): station, network,
channel, location, quality, samplerate.

The short form N.S.L.C.Q can also be used (at a minimum N.S must be
supplied).

#### Time Range

The following parameters can be given only once, must be of
the form YYYY-MM-DDTHH:MM:SS.SSSSSS (may be truncated on the
right), and define a range of times over which the block must 
appear (at least partially) to be included:

  begin, end

#### Flags

The following parameters are simple flags that change the
output format.  They are mutually exclusive and take no
value:

  count - only the number of matches will be shown
  join - continguous time ranges will be joined
  join-samplerates - the maximal timespan across all
    samplerates is shown (as used by retrieve) 

#### Examples

    rover list-index IU.ANMO.00.BH? count

will display the number of entries for all time, any quality or
smaplerate.

    rover list-index net=* begin=2001-01-01

will list all entries in the index after the year 2000.

Note that console logging is to stderr, while results are
printed to stdout.

## Advanced Usage

### Subscribe

## Low-level Commands

The following commands are used internally, but are usually not useful
from the command line:

### Download
  
    rover download url

Download data from the given URL to the temporary store (config
parameter temp-dir).  When downloaded, ingest into the local store
(config parameter mseed-dir) and delete.  Called by subscribe when
needed.

### Ingest
  
    rover ingest (file|dir) ...

Add the specified files to the local store (config parameter
mseed-dir), compact the contents, and update the database index
(config parameter mseed-db).  Called by retrieve when needed.
      
TODO: Document day restriction (online help too).

### Compact

    rover compact [(file|dir)...]

Rewrite mseed files, removing duplicates and joining contiguous data,
then (for files in the local store) update the database index (config
parameter mseed-db).  Called by ingest when needed.
      
If no arguments are given then files in the local store (config
parameter mseed-dir) that have been modified since the store was last
indexed are processed.  The config parameter all can be used (eg --all
on the command line) to force processing of all files in the store.
      
The config parameter compact can be used (eg --no-compact on the
command line) to avoid calling this command when ingesting data.

### Index
            
    rover index [(file|dir) ...]

Scan files and update the database index (config parameter mseed-db)
using the mseedindex command (config parameter mseed-cmd). Called by
compact or ingest when needed.
      
If no arguments are given then files in the local store (config
parameter mseed-dir) that have been modified since the store was last
indexed are processed.  The config parameter all can be used (eg --all
on the command line) to force processing of all files in the store.
