
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

* `rover compact --all` - will check for duplicate data (rasing an
  error on the first file found containing duplicates).

* `rover compact --all --compact-merge` - will try to merge (and so
  remove) duplicate data.

* `rover compact --all --compact-merge --compact-mutate` - will merge
  and remove duplicate data even if there are differences between the
  newer and older data (the newer data are preferred).

* `rover compact --all --compact-merge --compact-mixed-types` - will
   remove duplicate data without giving an eror if some duplicate data
   are of differnt types (duplicates of differeing types will not be
   merged).
