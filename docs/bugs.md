
# Known Bugs and Limitations

## Quality, Sampling Frequency and Timespans

MSEED files can contain data at multiple qualities and sampling
frequencies.  When `rover retrieve` uses the index to assess what data
already exist it uses the *maximal* range across all qualities and
sampling frequencies.  So if N.S.L.C has 20Hz data from 06:00 to 10:00
hours, but 10Hz data only from 08:00 to 09:00 then `rover retrieve`
will assume all data exist from 08:00 to 10:00 hours.  Any "missing"
10Hz data will never be downloaded.

Also, when calculating differences between timespans of available data
and local data for a particular SNCL, differences are only considered
significant if they exceed the minimum sample time (multiplied by
`--timespan-tol`, which by default is 1.5).  So if a SNCL contains
20Hz and 1Hz data a significant gap in the 20Hz data my go undetected.

## Handling Of Duplicate Data

If `rover ingest` is used manually it is possible for duplcaite data
to be added to the store (eg by ingesting the same file twice).  This
cannot (or should not) happen in normal use, because Rover does not
download duplicate data, so cannot ingest it.

Ideally either ingets should check and refuse to add duplicate data,
or we should have an additional command that compacts files.

## Ingest Limited to Single Days

The `rover ingest` command rejects files that span multiple calendar
days.  This is because it works by blindly copying byte ranges based
on the mseedindex output, and the targets for this data (the files in
the local store) are per-day.

This is not a problem for normal use (because files are downloaded in
day-sized chunks), but is restrictive when ingesting local files (see
duplicate data above).
