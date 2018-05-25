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

    rover --daemon ...
 
or

    rover --no-daemon ...

Available parameters can be displayed using \`rover -h\`.

## File Variables

The value \`\${CURDIR}\` in any file value is replaced by the directory
in which the configuration file is located.  This is useful in tests.

An escaped value \`\$\${...}\` is replaced by \`\${...}\`.

Any other variable (of the form \`\${...}\`) raises an error.

## Configuration Parameters

EOF

python -c 'from rover.args import Arguments; Arguments().print_docs_table_md()' >> docs/configuration.md

cat <<EOF > docs/commands.md

# Rover Commands

* [Normal Usage](#normal-usage)
  * [Retrieve](#retrieve)
  * [List Retrieve](#list-retrieve)
  * [List Index](#list-index)
  * [Reset Config](#reset-config)
* [Advanced Usage](#advanced-usage)
  * [Subscribe](#subscribe)
* [Low-Level Commands](#low-level-commands)
  * [Download](#download)
  * [Ingest](#ingest)
  * [Index](#index)
  * [Summary](#summary)

## Normal Usage

EOF

dev/rover help retrieve --md-format >> docs/commands.md
dev/rover help list-retrieve --md-format >> docs/commands.md
dev/rover help list-index --md-format >> docs/commands.md
dev/rover help reset-config --md-format >> docs/commands.md

cat <<EOF >> docs/commands.md
## Advanced Usage (Daemon Mode)

EOF

dev/rover help subscribe --md-format >> docs/commands.md

cat <<EOF >> docs/commands.md
## Low-Level Commands

The following commands are used internally, but are usually not useful
from the command line:

EOF

dev/rover help download --md-format >> docs/commands.md
dev/rover help ingest --md-format >> docs/commands.md
dev/rover help index --md-format >> docs/commands.md
dev/rover help summary --md-format >> docs/commands.md
