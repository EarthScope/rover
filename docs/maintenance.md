---
title: Example commands to manage and maintain a repository
layout: default
---

## Indexing

* `rover index` - will re-index any files that have been modified
  since they were last indexed.

* `rover index --all` - will re-index all files.

* `rover summary` - will generate a summary of the index.

(all these commands should be called automatically by `rover retrieve`)

## Ingest of Local Data

* `rover ingest file.mseed` - will include a file from the local
  filesystem into the repository.

  **WARNING**: Repeated use of this command with the same file will
  result in duplicated data in the repository.

## Inspection

* `rover list-index count` - will give the number of entries in the 
  index.

* `rover list-index net=XX join` - will show the timespan coverage for
  all data belonging to the given network.

* `rover list-summary net=XX` - will show the overall (earliest to
  latest) voerage for all data belonging to the given network (in
  general, `rover list-summary` will run much more quickly that `rover
  list-index` because it uses a pre-computed summary table).
