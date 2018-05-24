
# Example Commands to Manage and Maintain the Local Store

## Configuration

* `rover reset-config` - will reset the configuration to the default.

## Indexing

* `rover index` - will re-index any files that have been modified
  since they were last indexed.

* `rover index --all` - will re-index all files.

## Ingest of Local Data

* `rover ingest file.mseed` - will include a file from the local
  filesystem into the store.

  **WARNING**: Repeated use of this command with the same file will
  give duplicated data.

## Inspection

* `rover list-index count` - will give the number of entries in the 
  index.

* `rover list-index net=XX join` - will show the timespan coverage for
  all data belonging to the given network.
