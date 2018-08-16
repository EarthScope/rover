
# Rover Configuration

Rover can be configured via a file or using command line parameters.
The parameter names are the same in both cases.

## File Configuration

The default location for the configuration file is `~/rover/config`
(the file `config` in the `rover` directory located in the user's home
directory).  This file is generated when Rover is first used and can
be reset with `rover make-config`.

If a file in a different location is used, the location can be given
with `-f` or `--file` on the command line:

    rover -f /some/where/config ,,,

Use a text editor to change parameter values in the file.  A line
starting with `#` is a comment.

## Command Line Configuration

The same parameters can also be specified on the command line.  So,
for example, th eparameter `temp-dir` in the configuration file could
be specified as:

    rover --temp-dir /tmp ...

Note that the syntax for boolean parameters on teh command line is
different to the file.  They are simply given as flags, which can be
negated by prefixing with `no`:

    rover --index ...

or

    rover --no-index ...

Available parameters can be displayed using `rover -h`.

## Variables, Relative Paths, Default Configuration

The value `${CONFIGDIR}` in any file value is replaced by the directory
in which the configuration file is located.

An escaped value `$${...}` is replaced by `${...}`.

Relative paths for files and directories (bit not commands) are intepreted
as relative to `${CONFIGDIR}`.  So, in the configuration file

    data_dir=mseed

is equivalent to

    data_dir=${CONFIGDIR}/mseed

The default configuration uses relative paths only and assumes that the
configuration file is in `~/rover`.  This implies the following directory
structure:

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

The configuration file is created automatically if not found, so **to
use Rover with a completely new database, configuration, etc, it is
only necessary to sepecify a new path for the configuration file:**

    rover -f newdir/config

This will place all files in `newdir`.

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
| timespan-tol        | 1.5                  | Fractional tolerance for overlapping timespans (samples) |
| download-retries    | 3                    | Maximum number of attempts to download data |
| download-workers    | 5                    | Number of download instances to run |
| rover-cmd           | rover                | Command to run rover           |
| pre-index           | True                 | Index before retrieval?        |
| ingest              | True                 | Call ingest after retrieval?   |
| index               | True                 | Call index after ingest?       |
| post-summary        | True                 | Call summary after retrieval?  |
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
| leap-expire         | 30                   | Number of days before refreshing file |
| leap-file           | leap-seconds.list    | File for leapsecond data       |
| leap-url            | http://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
| web                 | True                 | Auto-start the download progress web server? |
| http-bind-address   | 127.0.0.1            | Bind address for HTTP server   |
| http-port           | 8000                 | Port for HTTP server           |
| email               |                      | Address for completion status  |
| email-from          | noreply@rover        | From address for email         |
| smtp-address        | localhost            | Address of SMTP server         |
| smtp-port           | 25                   | Port for SMTP server           |
