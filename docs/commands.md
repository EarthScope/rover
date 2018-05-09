
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

    rover list-index ...
    
List index entries for the local store (config parameter mseed-dir)
that match the given constraints.  For more information, run "rover
list-index" (with no arguments).

## Advanced Usage

### Subscribe

## Low-level Commands

The following commands are used internally, but are usually not useful
from the command line:

### Download
  
    download url

Download data from the given URL to the temporary store (config
parameter temp-dir).  When downloaded, ingest into the local store
(config parameter mseed-dir) and delete.  Called by subscribe when
needed.

### Ingest
  
    ingest (file|dir) ...

Add the specified files to the local store (config parameter
mseed-dir), compact the contents, and update the database index
(config parameter mseed-db).  Called by retrieve when needed.
      
### Compact

    compact [(file|dir)...]

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
            
    index [(file|dir) ...]

Scan files and update the database index (config parameter mseed-db)
using the mseedindex command (config parameter mseed-cmd). Called by
compact or ingest when needed.
      
If no arguments are given then files in the local store (config
parameter mseed-dir) that have been modified since the store was last
indexed are processed.  The config parameter all can be used (eg --all
on the command line) to force processing of all files in the store.
