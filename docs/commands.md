
# Rover Commands

## Normal Usage

### Retrieve

    rover retrieve (file|sncl start [end])

Compare the local index (config parameter mseed-db) with the data
availabe remotely (config parameter availability-url), then download
(config parameter dataselect-url) and ingest the missing files.  Use
compare (below) to see what data would be downloaded (without doing
the work).

### Compare
      
    rover compare (file|sncl start [end])

Compare the local index (config parameter mseed-db) with the data
availabe remotely (config parameter availability-url), then display
the difference.  Note that the summary is printed to stdout, while
logging is to stderr.

### List Index

    rover list-index [network=...|station=...|location=...|channel=..|quality=...|samplerate=...]*
      [S.N.C.L.q]* [begin=...] [end=...] [count|join\join-samplerates]
    
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
