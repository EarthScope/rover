#!/bin/bash

source env3/bin/activate

cat <<EOF > docs/configuration.md

# ROVER Configuration

ROVER can be configured via a file, by using command line options,
or a combination of the two. Option names are the same in both cases.

## File Configuration

ROVER's configuration file, normally named rover.config, contains all
options for a ROVER repository. A default config is created when a
ROVER repository is initialized.

By default \`rover.config\` is searched for in the current working
directory, which allows for ROVER commands to be run without specifying
a config file.

To explicitly use a configuration file, the \`-f\` or \`--file\` option
followed by a path to the configuration file can be included when
calling ROVER, e.g.:

    rover -f /PATH/TO/rover.config

Use a text editor to change option values in the rover.config file.
Lines starting with \`#\` are comments.

## Command Line Configuration

Options can be directly specified on the command line.
For example, the \`verbosity\` option could be assigned
when running ROVER:

    rover --verbosity 6 ...

Boolean options follow different syntax when assigned through the
command prompt versus a config file. In the terminal,
boolean options are interperted as flags, which can be
negated by prefixing the option's name with \`no-\`:

    rover --web ...

or

    rover --no-web ...

Available options are displayed using \`rover -h\` or \`rover -H\`,
with the later syntax showing the full help with all options.

## Default Configuration

Upon initialization of a new repository, ROVER's default configuration
is written to a file named \`rover.config\`. ROVER repositories are
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

EOF

python -c 'from rover.args import Arguments; Arguments().print_docs_table_md()' >> docs/configuration.md

cat <<EOF > docs/commands.md

# ROVER Commands

* [Normal Usage](#normal-usage)
  * [Init Repository](#init-repository)
  * [Retrieve](#retrieve)
  * [List Retrieve](#list-retrieve)
  * [List Index](#list-index)
  * [List Summary](#list-summary)
* [Low-Level Commands](#low-level-commands)
  * [Download](#download)
  * [Ingest](#ingest)
  * [Index](#index)
  * [Summary](#summary)
  * [Web](#web)
  * [Retrieve-Metadata](#Retrieve-Metadata)

## Common ROVER Commands

EOF

dev/rover help init-repository --md-format >> docs/commands.md
dev/rover help retrieve --md-format >> docs/commands.md
dev/rover help list-retrieve --md-format >> docs/commands.md
dev/rover help list-index --md-format >> docs/commands.md
dev/rover help list-summary --md-format >> docs/commands.md

cat <<EOF >> docs/commands.md
## Low-Level Commands

The following commands are used internally, and are often less
useful from the command line:

EOF

dev/rover help download --md-format >> docs/commands.md
dev/rover help ingest --md-format >> docs/commands.md
dev/rover help index --md-format >> docs/commands.md
dev/rover help summary --md-format >> docs/commands.md
# dev/rover help daemon --md-format >> docs/commands.md
dev/rover help web --md-format >> docs/commands.md
dev/rover help retrieve-metadata --md-format >> docs/commands.md

# Make lines associated with daemon mode invisible for only help docs.
# To reinstates daemon mode documentation move lines below to line 92
# * [Advanced Usage](#advanced-usage)
#   * [Subscribe](#subscribe)
#   * [Daemon](#daemon)
#   * [Start](#start)
#   * [Stop](#stop)
#   * [Status](#status)
#   * [Unsubscribe](#unsubscribe)
#   * [Trigger](#trigger)

# To reinstates daemon mode documentation move lines below to line 110

#  ## Advanced ROVER Commands
#
#  EOF
#
#  dev/rover help subscribe --md-format >> docs/commands.md
#  dev/rover help start --md-format >> docs/commands.md
#  dev/rover help stop --md-format >> docs/commands.md
#  dev/rover help status --md-format >> docs/commands.md
#  dev/rover help unsubscribe --md-format >> docs/commands.md
#  dev/rover help trigger --md-format >> docs/commands.md
#
#  cat <<EOF >> docs/commands.md
