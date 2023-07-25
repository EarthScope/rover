
# ROVER Configuration

ROVER can be configured via a file, by using command line options,
or a combination of the two. Option names are the same in both cases.

## File Configuration

ROVER's configuration file, normally named rover.config, contains all
options for a ROVER repository. A default config is created when a
ROVER repository is initialized.

By default `rover.config` is searched for in the current working
directory, which allows for ROVER commands to be run without specifying
a config file.

To explicitly use a configuration file, the `-f` or `--file` option
followed by a path to the configuration file can be included when
calling ROVER, e.g.:

    rover -f /PATH/TO/rover.config

Use a text editor to change option values in the rover.config file.
Lines starting with `#` are comments.

## Command Line Configuration

Options can be directly specified on the command line.
For example, the `verbosity` option could be assigned
when running ROVER:

    rover --verbosity 6 ...

Boolean options follow different syntax when assigned through the
command prompt versus a config file. In the terminal,
boolean options are interperted as flags, which can be
negated by prefixing the option's name with `no-`:

    rover --web ...

or

    rover --no-web ...

Available options are displayed using `rover -h` or `rover -H`,
with the later syntax showing the full help with all options.

## Default Configuration

Upon initialization of a new repository, ROVER's default configuration
is written to a file named `rover.config`. ROVER repositories are
initialized by running the command:

    rover init-repository /PATH/TO/DATAREPO

By default, a repository is arranged in the following structure:

    DATAREPO/
       +- rover.config
       +- leap-seconds.list
       +- logs/
       |  +- ...
       +- data/
       |  +- timeseries.sqlite
       |  +- ...
       +- tmp/
          +- ...

All of these base directory and file locations can be specified
using ROVER options.

## Options

|  Name               | Default              | Description                    |
| ------------------- | -------------------- | ------------------------------ |
| help / -h           | False                | Show the help message and exit |
| full-help / -H      | False                | Show full help details         |
| version             | ==SUPPRESS==         | Show program's version number and exit |
| full-config         | False                | Initialize with full configuration file |
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
| output-format       | mseed                | Output data format. Choose from "mseed" (miniSEED) or "asdf" (ASDF) |
| asdf-filename       | asdf.h5              | Name of ASDF file when ASDF output is specified |
| station-url         | http://service.iris.edu/fdsnws/station/1/query | Station service url            |
| force-metadata-reload | False                | Force reload of metadata       |
| availability-url    | http://service.iris.edu/fdsnws/availability/1/query | Availability service url       |
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
| leap                | True                 | Use leap seconds file?         |
| leap-expire         | 30                   | Number of days before refreshing leap seconds file |
| leap-file           | leap-seconds.list    | File for leap second data      |
| leap-url            | https://www.ietf.org/timezones/data/leap-seconds.list | URL for leap second data       |
| web                 | True                 | Auto-start the download progress web server? |
| http-bind-address   | 127.0.0.1            | Bind address for HTTP server   |
| http-port           | 8000                 | Port for HTTP server           |
| email               |                      | Address for completion status  |
| email-from          | noreply@rover        | From address for email         |
| smtp-address        | localhost            | Address of SMTP server         |
| smtp-port           | 25                   | Port for SMTP server           |
