
# Known Bugs and Limitations

## Samping Frequency and Timespans

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
