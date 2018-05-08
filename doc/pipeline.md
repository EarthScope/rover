
# Rover's Processing Pipeline

When the `rover retrieve` command is used, the following steps are taken:

* **Availability** - The Availability service is contacted to see what
    data are available.  This is done by the `retrieve` command itself.

* **Comparison** - The available data re compared with the local index
    to see what timespans are missing.  Again, this work is done by
    the `retrieve` command.

* **Chunking** - Required timespans are split and arranged by SNCL and
    day.  This work is done by the Download Manager as part of the
    `retrieve` command.

* **Separate Processes** - All the following steps are done in a
    separate process for each download.  This reduces the damage that
    any error can have on the retieval as a whole.

  * **Download** - A day's data for a particular SNCL are downloaded
    from the Data Select service.  This is done by the `rover
    download` command.

  * **Indexing for Ingest** - The `mseedindex` command is used to
    index the downloaded data.  This is done by `rover ingest`.

  * **Ingest** - Each block of indexed data is added to the local data
    store.  This is done by `rover ingest`, which takes the byte
    offset and length of the block and appends that data to the
    existing data in the store.

  * **Compaction** - Optionally `rover compact` can be run.  This can
    check for and remove duplicate data.  See [Reliability,
    Repeatability and Idempotence](./reliability.md).

  * **Indexing** - Finally, `rover index` updates the 