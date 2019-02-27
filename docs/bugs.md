---
title: Known bugs and limitations

layout: default
---

## Quality, sampling frequency and timespans

miniSEED files can contain data at multiple qualities and sampling
frequencies.  When `rover retrieve` uses the index to assess what data
already exist it uses the *maximal* range across all qualities and
sampling frequencies.  So if a given **N\_S\_L\_C** has 20 samples/second data from 06:00 to 10:00
hours, but 10 samples/second data only from 08:00 to 09:00 then `rover retrieve`
will assume all data exist from 08:00 to 10:00 hours.  Any "missing"
10 samples/second data will never be downloaded.

Also, when calculating differences between timespans of available data
and local data for a particular **N\_S\_L\_C**, differences are only
considered significant if they exceed the minimum sample time
(multiplied by `--timespan-tol`, which by default is 1.5).  So if a
**N\_S\_L\_C** contains 20 samples/sec and 1 samples/sec data a significant gap in the 20 samples/sec data
my go undetected.



## Handling of duplicate data


If `rover ingest` is used manually it is possible for duplicate data
to be added to the repository (e.g. by ingesting the same file twice).
This cannot (or should not) happen in normal use, because ROVER does
not download duplicate data, so cannot ingest it.

Ideally either ingest should check and refuse to add duplicate data,
or we should have an additional command that compacts files.


## Ingest limited to single days



The `rover ingest` command rejects files that span multiple calendar
days.  This is because it works by blindly copying byte ranges based
on the mseedindex output, and the targets for this data (the files in
the repository) are per-day.

This is not a problem for normal use (because files are downloaded in
day-sized chunks), but is restrictive when ingesting local files (see
duplicate data above).

## Availability request format


To avoid duplicate data (see above) `rover subscribe` checks the
subscription against existing subscriptions.  This comparison only
supports the basic request format:

    net sta loc cha [start [end]]

The actual format supported by the availability command is more
complex (e.g. start and end times using parameters), but this will
trigger an exception during the check for duplicate data.

If necessary, the user can use `--force-request` to avoid the check
for duplicate data.
