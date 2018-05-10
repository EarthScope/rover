
# Known Bugs and Limitations

## Sampling Frequency and Timespans

MSEED files can contain data at multiple sampling frequencies.  When
`rover retrieve` uses the index to assess what data already exist it
uses the *maximal* range across all sampling frequencies.  So if
N.S.L.C.Q has 20Hz data from 06:00 to 10:00 hours, but 10Hz data only
from 08:00 to 09:00 then `rover retrieve` will assume all data exist
from 08:00 to 10:00 hours.  Any "missing" 10Hz data will never be
downloaded.

## Incomplete Handling Of Duplicate Data

See the discussion on [reliability](./reliability.md).  In short,
there are some occasions when `rover compact` should be used, and some
occasions where that is insufficient.

## Ingest Limited to Single Days

The `rover ingest` command rejects files that span multiple calendar
days.  This is because it works by blindly copying byte ranges based
on the mseedindex output, and the targets for this data (the files in
the local store) are per-day.

This is not a problem for normal use (because files are downloaded in
day-sized chunks), but is restrictive when ingesting local files.
