
# Example Commands to Download Data

## Immedidate Download

To download data for all sites matching `IU_ANMO_3?_*` during the
first day of 2016:

    rover retrieve IU_ANMO_3?_* 2016-01-01T00:00:00 2016-01-02T00:00:00
    
While the command is running the status can be seen at http://localhost:8000.
When the command finishes an email is optionally sent to the user 
(`rover retrieve --email ....`).

To see how much data would be retrieved:

    rover list-retrieve IU_ANMO_3?_* 2016-01-01T00:00:00 2016-01-02T00:00:00

## Background Mode

In background mode the system will repeatedly (see `--recheck-period`)
check whether more data need to be downloaded.

To support this, a background "daemon" must be running.  This can be
started with:

    rover start

and stopped with:

    rover stop

While the daemon is running the status can be seen at http://localhost:8000.

The command to request data has the same format as `rover retrieve`
above:

    rover subscribe IU_ANMO_3?_* 2016-01-01T00:00:00 2016-01-02T00:00:00

When processing of a subscription is complete an email is optionally sent 
to the user (`rover start --email ....`).  The daemon will automatically
re-process the subscription regularly, to check for new data.  Processing
can also be triggered by hand using

    rover resubscribe N
    
where N is the subscription index, as listed below.
    
Existing subscriptions can be shown with:

    rover list-subscribe

and the data to be downloaded for a particular description displayed
with:

    rover list-subscribe N

where N is the subscription number displayed by `rover list-subscribe`
(no arguments).

Finally, subscriptions can be deleted with

    rover unsubscribe N

