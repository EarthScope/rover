
# Example Commands to Download Data

## Immedidate Download

To download data for all sites matching `IU_ANMO_3?_*` during the
first day of 2016:

    rover retrieve  IU_ANMO_3?_*  2016-01-01T00:00:00  2016-01-02T00:00:00

To see how much data would be retrieved:

    rover list-retrieve  IU_ANMO_3?_*  2016-01-01T00:00:00  2016-01-02T00:00:00

## Background Mode

In background mode the system will repeatedly (see `--recheck-period`)
check whether more data need to be downloaded.

To support this, a background "daemon" must be running.  This can be
started with:

    rover start

and stopped with:

    rover stop

The command to request data has the same format as `rover retrieve`
above:

    rover subscribe  IU_ANMO_3?_*  2016-01-01T00:00:00  2016-01-02T00:00:00

Existing subscriptions can be shown with:

    rover list-subscribe

and the data to be downloaded for a particular description displayed
with:

    rover list-subscribe N

where N is the subscription number displayed by `rover list-subscribe`
(no arguments).

