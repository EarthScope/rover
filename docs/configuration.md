
# Rover Configuration

Rover can be configured via a file or using command line parameters.
The parameter names are the same in both cases.

## File Configuration

The default location for the configuration file is `~/rover/config`
(the file `config` in the `rover` directory located in the user's home
directory).  This file is generated when Rover is first used and can
be reset with `rover reset-config`.

Use a text editor to change parameter values in the file.  A line
starting with `#` is a comment.

## Command Line Configuration

The same parameters can also be specified on the command line.  So,
for example, th eparameter `temp-dir` in the configuration file could
be specified as:

    rover --temp-dir /tmp ...

Note that the syntax for boolean parameters on teh command line is
different to the file.  They are simply given as flags, which can be
negate dby prefixing with `no`::

    rover --compact ...
 
or

    rover --no-compact` ...

## Configuration Parameters

