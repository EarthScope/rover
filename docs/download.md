## Immediate download

The `retrieve` group of commands are used to download, ingest, and index data.  

To download data for all sites matching `IU_ANMO_3?_*`, i.e. network IU, station ANMO, location starting with 3 and all channels, during the first day of 2016:

    rover retrieve IU_ANMO_3?_* 2016-01-01T00:00:00 2016-01-02T00:00:00
    
Alternatively, a list of one or more data selections may be provided in a file.  For example, if the file named `request.txt` contains:

    IU ANMO * LHZ 2012-01-01T00:00:00 2012-02-01T00:00:00
    TA MSTX -- BH? 2012-01-01T00:00:00 2012-02-01T00:00:00

it can be requested with the following command:

    rover retrieve request.txt

The download status can be seen at http://localhost:8000 (if using the default settings).

When `rover retrieve` finishes an email can be optionally sent to the user (`rover retrieve --email ....`).

### Checking what would be downloaded before downloading

To see what data would be downloaded without downloading it use the `list-retrive` command, for exammple:

    rover list-retrieve IU_ANMO_3?_* 2016-01-01T00:00:00 2016-01-02T00:00:00

