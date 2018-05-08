
# Reliability, Repeatability and Idempotence

## Introduction

There are two common approaches to making reliable software systems:
either make the system as robust as possible, capable of handing all
possible errors, or make it easy to run repeatedly until correct.

Rover takes the second approach.  It is designed ao that most errors
affect only a small part of any operation (by, for example, running
each download as a separate process), and for those errors to be
corrected by re-running the program.

To work reliably, then, it most be possible for Rover to run
repeatedly.  In particular, calling `rover retrieve` should not
download and append data that are already present in the store, or
store will expand in size.

This property - being able to repeat a command while preserving the
existing data - is called *idemptence*.  It is critical for reliable,
long-lived systems.

## Rover Is Generally Idempotent

Rover reuqests and ingests only data that it does not contain, so by
default it cannot have duplicate data.

Consider calling `rover retrieve` twice with the same parameters.  If
the first call is successful then the second call will download and
ingest no data.  If the first call fails so that some data are missing
then the second call will download and ingest only the missing data.

## Rover Cannot Guarantee Idempotency

But life is complicated.  Although Rover is generally idempotent we
can imagine cases where this is not the case:

  * If data are ingested from a local file multiple times then they
    will appear multiple times in the store.  This is because `rover
    ingest` simply appends data (see the [pipeline
    description](./pipeline.md)).

  * If `rover index` fails for some reason (perhaps a bug) then `rover
    retrieve` will download data that it does not "know about" (that
    have not been indexed).  On ingestion these will appear as
    dplicates.

This list is unlikely to be exhaustive.  So Rover may not always
behave inan indempotent manner.

## Compact: A Limited Solution

The most simple cases of duplicate data can be resolved by using the
command `rover compact`.  For example, this can be enabled during
retrieval with `rover retrieve --compact`.

The `rover compact` command attempts to merge duplicate data.  If it
succeeds then it removes the duplicated data and Rover again behaves
in a reliable, idempotent manner.

But the command has limitations.  These largely come from teh
complecityu of the MSSED format.  For example, it cannot merge data
with different types.

The `rover compact` command can also be used to update data.  If newer
data are ingested then `rover compact --compact-mutate` will replace
the old data with teh new (without the `--compact-mutate` it is an
error if merged data are not identical where they overlap).

Other uses for the command are described in the documentation on
[maintaining the store](./maintenance.md).

Note: *By default `rover compact` is not enabled.*


