#!/bin/bash

source env3/bin/activate

cat <<EOF > docs/configuration.md

# Rover Configuration

Rover can be configured via a file or using command line parameters.
The parameter names are the same in both cases.

## File Configuration

The default location for the configuration file is \`~/rover/config\`
(the file \`config\` in the \`rover\` directory located in the user's home
directory).  This file is generated when Rover is first used and can
be reset with \`rover reset-config\`.

If a file in a different location is used, the location can be given
with \`-f\` or \`--file\` on the command line:

    rover -f /some/where/config ,,,

Use a text editor to change parameter values in the file.  A line
starting with \`#\` is a comment.

## Command Line Configuration

The same parameters can also be specified on the command line.  So,
for example, th eparameter \`temp-dir\` in the configuration file could
be specified as:

    rover --temp-dir /tmp ...

Note that the syntax for boolean parameters on teh command line is
different to the file.  They are simply given as flags, which can be
negated by prefixing with \`no\`:

    rover --index ...

or

    rover --no-index ...

Available parameters can be displayed using \`rover -h\`.

## Variables, Relative Paths, Default Configuration

The value \`\${CONFIGDIR}\` in any file value is replaced by the directory
in which the configuration file is located.

An escaped value \`\$\${...}\` is replaced by \`\${...}\`.

Relative paths for files and directories (bit not commands) are intepreted
as relative to \`\${CONFIGDIR}\`.  So, in the configuration file

    mseed_dir=mseed

is equivalent to

    mseed_dir=\${CONFIGDIR}/mseed

The default configuration uses relative paths only and assumes that the
configuration file is in \`~/rover\`.  This implies the following directory
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

The configuration file created automatically if not found, so **to use 
Rover with a completely new database, configuration, etc, it is only
necessary to sepecify a new path for the configuration file:**

    rover -f newdir/config

This will place all files in \`newdir\`.

## Parameters

EOF

python -c 'from rover.args import Arguments; Arguments().print_docs_table_md()' >> docs/configuration.md

cat <<EOF > docs/commands.md

# Rover Commands

* [Normal Usage](#normal-usage)
  * [Retrieve](#retrieve)
  * [List Retrieve](#list-retrieve)
  * [List Index](#list-index)
  * [List Summary](#list-summary)
  * [Write Config](#write-config)
* [Advanced Usage](#advanced-usage)
  * [Subscribe](#subscribe)
  * [Start](#start)
  * [Stop](#stop)
  * [Status](#status)
  * [Unsubscribe](#unsubscribe)
  * [Resubscribe](#resubscribe)
* [Low-Level Commands](#low-level-commands)
  * [Download](#download)
  * [Ingest](#ingest)
  * [Index](#index)
  * [Summary](#summary)
  * [Daemon](#daemon)
  * [Web](#web)

## Normal Usage

EOF

dev/rover help retrieve --md-format >> docs/commands.md
dev/rover help list-retrieve --md-format >> docs/commands.md
dev/rover help list-index --md-format >> docs/commands.md
dev/rover help list-summary --md-format >> docs/commands.md
dev/rover help write-config --md-format >> docs/commands.md

cat <<EOF >> docs/commands.md
## Advanced Usage (Daemon Mode)

EOF

dev/rover help subscribe --md-format >> docs/commands.md
dev/rover help start --md-format >> docs/commands.md
dev/rover help stop --md-format >> docs/commands.md
dev/rover help status --md-format >> docs/commands.md
dev/rover help unsubscribe --md-format >> docs/commands.md
dev/rover help resubscribe --md-format >> docs/commands.md

cat <<EOF >> docs/commands.md
## Low-Level Commands

The following commands are used internally, but are usually not useful
from the command line:

EOF

dev/rover help download --md-format >> docs/commands.md
dev/rover help ingest --md-format >> docs/commands.md
dev/rover help index --md-format >> docs/commands.md
dev/rover help summary --md-format >> docs/commands.md
dev/rover help daemon --md-format >> docs/commands.md
dev/rover help web --md-format >> docs/commands.md
