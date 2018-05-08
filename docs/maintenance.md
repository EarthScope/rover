
# Commands to Manage and Maintain the Local Store

## Configuration

* `rover reset-config` - will reset the configuration to the default.

## Indexing

* `rover index` - will re-index any files that have been modified
  since they were last indexed.

* `rover index --all` - will re-index all files.

## Compaction

For background see [Reliability, Repeatability and
Idempotence](./reliability.md).

* `rover compact --all --compact-list` - will check for duplicate data
  (listing them to stdout and raising an error on completion).

* `rover compact --all` - will try to merge (and so remove) duplicate
  data.

* `rover compact --all --compact-mutate` - will merge and remove
  duplicate data even if there are differences between the newer and
  older data (the newer data are preferred).

* `rover compact --all --compact-mixed-types` - will merge and remove
   duplicate data without giving an eror if some duplicates are of
   differnt types (duplicates of differing types will not be merged).

## Ingest of Local Data

* `rover ingest file.mseed` - will include a file from the local
  filesystem into the store.

  Note that repeated use of this command with the same file will give
  [duplicated data](./reliability.md).
