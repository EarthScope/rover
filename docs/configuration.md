
# ROVER Configuration

ROVER can be configured via a file or by using command line parameters.
Parameter names are the same in both cases.

## File Configuration

ROVER's configuation file, rover.config, is written to a user specified
location upon the initialization of a rover data repository. ROVER
repositories are intilized by running the command
`rover init-repository /PATH/TO/DATAREPO`, a configuration file is
automatically generated in the directory DATAREPO. The command
`rover make-config` resets a rover.config.

To use a configuration file external to the data repository, the
`-f` or `--file` flag follwed by a path to the configuration
file must be included when calling ROVER:

    rover -f /PATH/TO/rover.config

Use a text editor to change parameter values in the rover.config file. Lines
starting with `#` are comments.

## Command Line Configuration

Parameters can be directly specified on the command line.
For example, the `temp-dir` parameter could be assigned
when running ROVER.

    rover --temp-dir /tmp ...

Boolean parameters follow different syntax when assigned through the
command prompt rather than a file. In the terminal,
boolean paramters are interperted as flags, which can be
negated by prefixing the parametrer's name with `no-`:

    rover --index ...

or

    rover --no-index ...

Available parameters can be displayed using `rover -h`.

## Variables, Relative Paths, Default Configuration

ROVER's default configuration uses relative paths and assumes that the
configuration file is in the `PATH/TO/DATAREPO` directory. Unless
otherwise configured, ROVER excpets the following directory structure:

    USERHOME/
    +- rover/
       +- config
       +- leap-seconds.lst
       +- logs/
       |  +- ...
       +- mseed/
       |  +- index.sql
       |  +- ...
       +- tmp/
          +- ...

A rover.config file is created automatically when initiating a ROVER
data repository. To create multiple ROVER data repositories using
one instance of ROVER, a user can either intiate a new repository using
`rover init-repository /PATH/TO/DATAREPO2` or specifiy a path to a
configuration using the -f/--file flag:

    rover -f newdir/config

Will place all files in `newdir`.

## Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| help / -h           | False                | Show the help message and exit |
| version             | ==SUPPRESS==         | Show program's version number and exit |
| full-help / -H      | False                | Show full help details         |
| file / -f           | rover.config         | Specify configuration file     |
| dev                 | False                | Development mode (show exceptions)? |
| delete-files        | True                 | Delete temporary files?        |
| md-format           | False                | Display help in markdown format? |
| force-cmd           | False                | Force cmd use (dangerous)      |
| data-dir            | data                 | The data directory - data, timeseries.sqlite |
| timespan-inc        | 0.5                  | Fractional increment for starting next timespan (samples) |
| timespan-tol        | 0.5                  | Fractional tolerance for overlapping timespans (samples) |
| download-retries    | 3                    | Maximum number of attempts to download data |
| download-workers    | 5                    | Number of download instances to run |
| rover-cmd           | rover                | Command to run rover           |
| pre-index           | True                 | Index before retrieval?        |
| ingest              | True                 | Call ingest after retrieval?   |
| index               | True                 | Call index after ingest?       |
| post-summary        | True                 | Call summary after retrieval?  |
| output-format       | mseed                | Output data format. Choose from "mseed" or "asdf" |
| asdf-filename       | asdf.h5              | Name of asdf file to create when OUTPUT_FORMAT=asdf |
| station-url         | http://service.iris.edu/fdsnws/station/1/query | Station service url            |
| force-metadata-reload | False                | Force reload of metadata       |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url       |
| dataselect-url      | http://service.iris.edu/fdsnws/dataselect/1/query | Dataselect service url         |
| temp-dir            | tmp                  | Temporary storage for downloads |
| temp-expire         | 1                    | Number of days before deleting temp files (days) |
| http-timeout        | 60                   | Timeout for HTTP requests (secs) |
| http-retries        | 3                    | Max retries for HTTP requests  |
| force-failures      | 0                    | Force failures for testing (dangerous) (percent) |
| sort-in-python      | False                | Avoid OS sort (slower)?        |
| all                 | False                | Process all files (not just modified)? |
| recurse             | True                 | When given a directory, process children? |
| subscriptions-dir   | subscriptions        | Directory for subscriptions    |
| recheck-period      | 12                   | Time between availabilty checks (hours) |
| force-request       | False                | Skip overlap checks (dangerous)? |
| log-dir             | logs                 | Directory for logs             |
| log-unique          | False                | Unique log names (with PIDs)?  |
| log-unique-expire   | 7                    | Number of days before deleting unique logs (days) |
| log-verbosity       | 4                    | Log verbosity (0-6)            |
| log-size            | 10M                  | Maximum log size (e.g. 10M)    |
| log-count           | 10                   | Maximum number of logs         |
| verbosity           | 4                    | Console verbosity (0-6)        |
| mseedindex-cmd      | mseedindex -sqlitebusyto 60000 | Mseedindex command             |
| mseedindex-workers  | 10                   | Number of mseedindex instances to run |
| leap                | True                 | Use leapseconds file?          |
| leap-expire         | 30                   | Number of days before reloading file |
| leap-file           | leap-seconds.list    | File for leapsecond data       |
| leap-url            | https://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
| web                 | True                 | Auto-start the download progress web server? |
| http-bind-address   | 127.0.0.1            | Bind address for HTTP server   |
| http-port           | 8000                 | Port for HTTP server           |
| email               |                      | Address for completion status  |
| email-from          | noreply@rover        | From address for email         |
| smtp-address        | localhost            | Address of SMTP server         |
| smtp-port           | 25                   | Port for SMTP server           |
