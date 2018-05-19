
# Compact

## Introduction

The `rover compact` command is optional and only used if obspy is
installed (installing obspy on OSX can be tricky).

In normal use (see [Reliability](#reliability) below) this command is
not needed, so you may not need to read any further.

What `rover compact` does is detect and / or remove duplicate data in
an mssed file.  It cannot remove data in all cases (the types of the
duplicate blocks must be identical), but when it can it can also check
that the duplicate data are identical.

The two use cases where this may be important are:

* When dealing with data files that have duplicate data.  This should
  not happen with `rover retrieve`, but may, for example, be a result
  of calling `rover ingest` manually more than once on the same data.

* Future extensions of Rover may have the ability to download data
  that was already present in the local store, but which has changed.
  The `rover compact` command, when removing duplicate data, keeps the
  latest version, so allows new data to be merged.

Unless dealing with those two cases, you probably do not need `rover
compact`.

## Reliability

There are two common approaches to making reliable software systems:
either make the system as robust as possible, capable of handing all
possible errors, or make it easy to run repeatedly until correct.

Rover takes the second approach.  It is designed so that most errors
affect only a small part of any operation (by, for example, running
each download as a separate process), and for those errors to be
corrected by re-running the program.

To work reliably, then, it most be possible for Rover to run
repeatedly.  In particular, calling `rover retrieve` should not
download and append data that are already present in the store, or the
store will expand in size.

This property - being able to repeat a command while preserving the
existing data - is called *idempotence*.  It is critical for reliable,
long-lived systems.

### Rover Is Generally Idempotent

Rover requests and ingests only data that it does not contain, so by
default it cannot have duplicate data.

Consider calling `rover retrieve` twice with the same parameters.  If
the first call is successful then the second call will download and
ingest no data.  If the first call fails so that some data are missing
then the second call will download and ingest only the missing data.

### But Rover Cannot Guarantee Idempotency

Life is complicated.  Although Rover is generally idempotent we can
imagine cases where this is not the case:

  * If data are ingested from a local file multiple times then they
    will appear multiple times in the store.  This is because `rover
    ingest` simply appends data (see the [pipeline
    description](./pipeline.md)).

  * If `rover index` fails for some reason (perhaps a bug) then `rover
    retrieve` will download data that it does not "know about" (that
    have not been indexed).  On ingestion these will appear as
    duplicates.

This list is unlikely to be exhaustive.  So Rover may not always
behave in an idempotent manner.

### Compact And Idempotency

Running `rover compact` removes duplicate data in common cases and so
increases the chnace that rover is idempotent even on unexpected
failure.
