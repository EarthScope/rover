
# Rover Configuration

Rover can be configured via a file or using command line parameters.
The parameter names are the same in both cases.

## File Configuration

The default location for the configuration file is `~/rover/config`
(the file `config` in the `rover` directory located in the user's home
directory).  This file is generated when Rover is first used and can
be reset with `rover reset-config`.

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

    rover --daemon ...

or

    rover --no-daemon ...

Available parameters can be displayed using `rover -h`.

## Variables, Relative Paths, Default Configuration

The value `${CONFIGDIR}` in any file value is replaced by the directory
in which the configuration file is located.

An escaped value `$${...}` is replaced by `${...}`.

Relative paths for files and directories (bit not commands) are intepreted
as relative to `${CONFIGDIR}`.  So, in the configuration file

    mseed_db=index.sql

is equivalent to

    mseed_db=${CONFIGDIR}/index.sql

The default configuration uses relative paths only and assumes that the
configuration file is in `~/rover`.  This implies the following directory
structure:

    USERHOME/
    +- rover/
       +- index.sql
       +- leap-seconds.lst
       +- logs/
       |  +- ...
       +- mseed/
       |  +- ...
       +- tmp/
          +- ...
|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| help / -h           | False                | Show the help message and exit |
| file / -f           | ~/rover/config       | Specify configuration file     |
| daemon              | False                | Use background processes?      |
| dev                 | False                | Development mode (show exceptions)? |
| delete-files        | True                 | Delete temporary files?        |
| md-format           | False                | Display help in markdown format? |
| subscriptions-dir   | subscriptions        | Directory for subscriptions    |
| timespan-tol        | 1.5                  | Fractional tolerance for overlapping timespans |
| download-workers    | 10                   | Number of download instances to run |
| multiprocess        | False                | Allow multiple processes (internal use only)? |
| rover-cmd           | rover                | Command to run rover           |
| pre-index           | True                 | Index before retrieval?        |
| ingest              | True                 | Call ingest after retrieval?   |
| index               | True                 | Call index after ingest?       |
| post-summary        | True                 | Call summary after retrieval?  |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url       |
| dataselect-url      | http://service.iris.edu/fdsnws/dataselect/1/query | Dataselect service url         |
| temp-dir            | tmp                  | Temporary storage for downloads |
| temp-expire         | 1                    | Number of days before deleting temp files |
| all                 | False                | Process all files (not just modified)? |
| recurse             | True                 | When given a directory, process children? |
| log-dir             | logs                 | Directory for logs             |
| log-name            | rover                | Base file name for logs        |
| log-unique          | False                | Unique log names (with PIDs)?  |
| log-unique-expire   | 7                    | Number of days before deleting unique logs |
| log-verbosity       | 5                    | Log verbosity (0-5)            |
| log-size            | 6                    | Maximum log size (1-10)        |
| log-count           | 10                   | Maximum number of logs         |
| verbosity           | 4                    | Console verbosity (0-5)        |
| mseed-cmd           | mseedindex           | Mseedindex command             |
| mseed-db            | index.sql            | Mseedindex database (also used by rover) |
| mseed-dir           | mseed                | Root of mseed data dirs        |
| mseed-workers       | 10                   | Number of mseedindex instances to run |
| leap                | True                 | Use leapseconds file?          |
| leap-expire         | 30                   | Number of days before refreshing file |
| leap-file           | leap-seconds.lst     | File for leapsecond data       |
| leap-url            | http://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
