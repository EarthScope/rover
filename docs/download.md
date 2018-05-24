
# Example Commands to Download Data

## Immedidate Download

To download data for all sites matching `IU.ANMO.3?.*` during the
first day of 2016:

    rover retrieve  IU.ANMO.3?.*  2016-01-01T00:00:00  2016-01-02T00:00:00

To see how much data would be retrieved:

    rover compare  IU.ANMO.3?.*  2016-01-01T20:00:00  2016-01-02T04:00:00

## Background Mode

(More here once daemon mode complete).
