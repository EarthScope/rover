
# Example commands to download data

## Immedidate download

The `retrieve` group of commands are used to download data on-demand.  Full help for the retrive command is available from the command-line using `rover help retrieve`.

To download data for all sites matching `IU_ANMO_3?_*`, i.e. network IU, station ANMO, location starting with 3 and all channeks, during the first day of 2016:

    rover retrieve IU_ANMO_3?_* 2016-01-01T00:00:00 2016-01-02T00:00:00
    
Alternatively, a list of one or more data selections may be provided in a file.  For example, if the file named `request.txt` contains:

    IU ANMO * LHZ 2012-01-01T00:00:00 2012-02-01T00:00:00
    TA MSTX -- BH? 2012-01-01T00:00:00 2012-02-01T00:00:00

it can be requested with the following command:

    rover retrieve request.txt

While the command is running the status can be seen at http://localhost:8000 (if using the default settings).

When the command finishes an email is optionally sent to the user (`rover retrieve --email ....`).

### Checking what would be downloaded before downloading

To see what data would be downloaded without downloading it use the `list-retrive` command, for exammple:

    rover list-retrieve IU_ANMO_3?_* 2016-01-01T00:00:00 2016-01-02T00:00:00

## Background mode

In background mode the system will repeatedly (see `--recheck-period`)
check whether more data need to be downloaded based on subscriptions.

To support this, a background "daemon" must be running.  This can be
started with:

    rover start

and stopped with:

    rover stop

While the daemon is running the status can be seen at http://localhost:8000 (if using the default settings).

The `subscribe` command to request data has the same format as described above for the `retrieve` command.  For example:

    rover subscribe IU_ANMO_3?_* 2016-01-01T00:00:00 2016-01-02T00:00:00

When processing of a subscription is complete an email is optionally sent 
to the user (`rover start --email ....`).  The daemon will automatically
re-process the subscription regularly, to check for new data.  Processing
can also be triggered by hand using

    rover trigger N
    
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

