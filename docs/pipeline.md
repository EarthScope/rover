---
title: ROVER's processing pipeline
layout: default
---

**Expert use only** - the default configuration should "just work".
The options described here give precise control over the pipeline
workflow for special cases.

When the `rover retrieve` command is used, the following steps are taken:

* **Indexing** - Any modified files in the repository are indexed.
    This step can be omitted with `--no-pre-index`.

* **Availability** - The Availability service is contacted to see what
    data are available.  This is done by the `retrieve` command itself.

* **Comparison** - The available data re compared with the local index
    to see what timespans are missing.  Again, this work is done by
    the `retrieve` command.

* **Chunking** - Required timespans are split and arranged by N_S_L_C
    and day.  This work is done by the Download Manager as part of the
    `retrieve` command.

* **Separate Processes** - The following steps are done in a separate
    process for each download.  This reduces the damage that any error
    can have on the retieval as a whole.

  * **Download** - A day's data for a particular N_S_L_C are
    downloaded from the Data Select service.  This is done by the
    `rover download` command.

  * **Indexing for Ingest** - The `mseedindex` command is used to
    index the downloaded data.  This is done by `rover ingest`.  This
    and later steps can be omitted with `--no-ingest`.

  * **Ingest** - Each block of indexed data is added to the
    repository.  This is done by `rover ingest`, which takes the byte
    offset and length of the block and appends that data to the
    existing data in the repository.

  * **Indexing** - The command `rover index` updates the index for the
    repository.  This step can be omitted with `--no-index`.
    
* **Summary** - A summary table is generated.  This step can be ommitted
  with `--no-post-summary`.

The options `--no-ingest` and `--no-index` can be used to stop the
separate processes short.

Initial indexing can be omitted with `--no-pre-index` and final 
summarizing with `--no-post-summary`.

These options also affect low-level commands thare are used
individually.  So using `--no-index` with `rover ingest` would mean
that `rover index` was not called after ingesting data.
