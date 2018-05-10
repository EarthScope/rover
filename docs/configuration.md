
# Rover Configuration

Rover can be configured via a file or using command line parameters.
The parameter names are the same in both cases.

## File Configuration

The default location for the configuration file is `~/rover/config`
(the file `config` in the `rover` directory located in the user's home
directory).  This file is generated when Rover is first used and can
be reset with `rover reset-config`.

If a file in a different location is used, the location can begiven
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

## Configuration Parameters

### help

Default: ==SUPPRESS==

show this help message and exit

### file

Default: ~/rover/config

specify configuration file

### daemon

Default: False

use background processes?

### dev

Default: False

development mode (show exceptions)?

### delete-files

Default: True

delete temporary files?

### timespan-tol

Default: 0.1

tolerance for overlapping timespans

### download-workers

Default: 10

number of download instances to run

### multiprocess

Default: False

allow multiple processes (internal use only)?

### rover-cmd

Default: rover

command to run rover

### pre-index

Default: True

index before retrieval?

### post-compact

Default: True

call compact after retrieval?

### availability-url

Default: http://service.iris.edu/irisws/availability/1/query

availability service url

### dataselect-url

Default: http://service.iris.edu/fdsnws/dataselect/1/query

dataselect service url

### temp-dir

Default: ~/rover/tmp

temporary storage for downloads

### temp-expire

Default: 1

number of days before deleting temp files

### compact

Default: False

call compact after ingest?

### compact-list

Default: False

detect and list files with duplicate data?

### compact-mixed-types

Default: False

allow duplicate data in mixed data types?

### compact-mutate

Default: False

allow compact to mutate (replace) data?

### all

Default: False

process all files (not just modified)?

### recurse

Default: True

when given a directory, process children?

### log-dir

Default: ~/rover/logs

directory for logs

### log-name

Default: rover

base file name for logs

### log-unique

Default: False

unique log names (with PIDs)?

### log-unique-expire

Default: 7

number of days before deleting unique logs

### log-verbosity

Default: 5

log verbosity (0-5)

### log-size

Default: 6

maximum log size (1-10)

### log-count

Default: 10

maximum number of logs

### verbosity

Default: 4

stdout verbosity (0-5)

### mseed-cmd

Default: mseedindex

mseedindex command

### mseed-db

Default: ~/rover/index.sql

mseedindex database (also used by rover)

### mseed-dir

Default: ~/rover/mseed

root of mseed data dirs

### mseed-workers

Default: 10

number of mseedindex instances to run

### leap

Default: True

use leapseconds file?

### leap-expire

Default: 30

number of days before refreshing file

### leap-file

Default: ~/rover/leap-seconds.lst

file for leapsecond data

### leap-url

Default: http://www.ietf.org/timezones/data/leap-seconds.list

URL for leapsecond data

### command

use "help" for further information

### args

depends on the command - see above
