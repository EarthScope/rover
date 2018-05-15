
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

    rover --compact ...
 
or

    rover --no-compact ...

Available parameters can be displayed using `rover -h`.

## File Variables

The value `${CURDIR}` in any file value is replaced by the directory
in which the configuration file is located.  This is useful in tests.

An escaped value `$${...}` is replaced by `${...}`.

Any other variable (of the form `${...}`) raises an error.

## Configuration Parameters

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| help / -h           | False                | Show the help message and exit |
| file / -f           | ~/rover/config       | Specify configuration file     |
| daemon              | False                | Use background processes?      |
| dev                 | False                | Development mode (show exceptions)? |
| delete-files        | True                 | Delete temporary files?        |
| md-format           | False                | Display help in markdown format? |
| timespan-tol        | 0.1                  | Tolerance for overlapping timespans |
| download-workers    | 10                   | Number of download instances to run |
| multiprocess        | False                | Allow multiple processes (internal use only)? |
| rover-cmd           | rover                | Command to run rover           |
| pre-index           | True                 | Index before retrieval?        |
| post-compact        | True                 | Call compact after retrieval?  |
| ingest              | True                 | Call ingest after retrieval?   |
| compact             | False                | Call compact after ingest?     |
| index               | True                 | Call index after compaction/ingest? |
| availability-url    | http://service.iris.edu/irisws/availability/1/query | Availability service url       |
| dataselect-url      | http://service.iris.edu/fdsnws/dataselect/1/query | Dataselect service url         |
| temp-dir            | ~/rover/tmp          | Temporary storage for downloads |
| temp-expire         | 1                    | Number of days before deleting temp files |
| compact-list        | False                | Detect and list files with duplicate data? |
| compact-mixed-types | False                | Allow duplicate data in mixed data types? |
| compact-mutate      | False                | Allow compact to mutate (replace) data? |
| all                 | False                | Process all files (not just modified)? |
| recurse             | True                 | When given a directory, process children? |
| log-dir             | ~/rover/logs         | Directory for logs             |
| log-name            | rover                | Base file name for logs        |
| log-unique          | False                | Unique log names (with PIDs)?  |
| log-unique-expire   | 7                    | Number of days before deleting unique logs |
| log-verbosity       | 5                    | Log verbosity (0-5)            |
| log-size            | 6                    | Maximum log size (1-10)        |
| log-count           | 10                   | Maximum number of logs         |
| verbosity           | 4                    | Console verbosity (0-5)        |
| mseed-cmd           | mseedindex           | Mseedindex command             |
| mseed-db            | ~/rover/index.sql    | Mseedindex database (also used by rover) |
| mseed-dir           | ~/rover/mseed        | Root of mseed data dirs        |
| mseed-workers       | 10                   | Number of mseedindex instances to run |
| leap                | True                 | Use leapseconds file?          |
| leap-expire         | 30                   | Number of days before refreshing file |
| leap-file           | ~/rover/leap-seconds.lst | File for leapsecond data       |
| leap-url            | http://www.ietf.org/timezones/data/leap-seconds.list | URL for leapsecond data        |
