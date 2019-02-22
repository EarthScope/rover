#!/bin/bash

source env3/bin/activate

cat <<EOF > docs/configuration.md

# ROVER Configuration

ROVER can be configured via a file or by using command line parameters.
Parameter names are the same in both cases.

## File Configuration

ROVER's configuation file, rover.config, is written to a user specified
location upon the initialization of a rover data repository. ROVER
repositories are intilized by running the command
\`rover init-repository /PATH/TO/DATAREPO\`, a configuration file is
automatically generated in the directory DATAREPO. The command
\`rover make-config\` resets a rover.config.

To use a configuration file external to the data repository, the
\`-f\` or \`--file\` flag follwed by a path to the configuration
file must be included when calling ROVER:

    rover -f /PATH/TO/rover.config

Use a text editor to change parameter values in the rover.config file. Lines
starting with \`#\` are comments.

## Command Line Configuration

Parameters can be directly specified on the command line.
For example, the \`temp-dir\` parameter could be assigned
when running ROVER.

    rover --temp-dir /tmp ...

Boolean parameters follow different syntax when assigned through the
command prompt rather than a file. In the terminal,
boolean paramters are interperted as flags, which can be
negated by prefixing the parametrer's name with \`no-\`:

    rover --index ...

or

    rover --no-index ...

Available parameters can be displayed using \`rover -h\`.

## Variables, Relative Paths, Default Configuration

ROVER's default configuration uses relative paths and assumes that the
configuration file is in the \`PATH/TO/DATAREPO\` directory. Unless
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
\`rover init-repository /PATH/TO/DATAREPO2\` or specifiy a path to a
configuration using the -f/--file flag:

    rover -f newdir/config

Will place all files in \`newdir\`.

## Parameters

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
* [Advanced Usage](#advanced-usage)
  * [Subscribe](#subscribe)
  * [Start](#start)
  * [Stop](#stop)
  * [Status](#status)
  * [Unsubscribe](#unsubscribe)
  * [Trigger](#trigger)
* [Low-Level Commands](#low-level-commands)
  * [Download](#download)
  * [Ingest](#ingest)
  * [Index](#index)
  * [Summary](#summary)
  * [Daemon](#daemon)
  * [Web](#web)

## Common ROVER Commands

EOF

dev/rover help init-repository --md-format >> docs/commands.md
dev/rover help retrieve --md-format >> docs/commands.md
dev/rover help list-retrieve --md-format >> docs/commands.md
dev/rover help list-index --md-format >> docs/commands.md
dev/rover help list-summary --md-format >> docs/commands.md

cat <<EOF >> docs/commands.md
## Advanced ROVER Commands

EOF

dev/rover help subscribe --md-format >> docs/commands.md
dev/rover help start --md-format >> docs/commands.md
dev/rover help stop --md-format >> docs/commands.md
dev/rover help status --md-format >> docs/commands.md
dev/rover help unsubscribe --md-format >> docs/commands.md
dev/rover help trigger --md-format >> docs/commands.md

cat <<EOF >> docs/commands.md
## Low-Level Commands

The following commands are used internally, and are often less
useful from the command line:

EOF

dev/rover help download --md-format >> docs/commands.md
dev/rover help ingest --md-format >> docs/commands.md
dev/rover help index --md-format >> docs/commands.md
dev/rover help summary --md-format >> docs/commands.md
dev/rover help daemon --md-format >> docs/commands.md
dev/rover help web --md-format >> docs/commands.md
dev/rover help retrieve-metadata --md-format >> docs/commands.md
