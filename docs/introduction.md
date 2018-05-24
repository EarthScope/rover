
# An Introduction to Rover

The `rover` command helps build, index and maintain a local store of
data.  The data are retrieved from a [dataselect
service](http://service.iris.edu/fdsnws/dataselect/1/); details of
available data re retrieved from an [availability
service](http://service.iris.edu/irisws/availability/1/).

For install instructions see the [README](../README.md).

## Exploring Rover

There may be no need to read all this documentation.  Rover has some
help built-in.  Simply typing

    rover

will give you an introductory screen.  While

    rover -h

displays all the configuration parameters.

## Further Documentation

* [Commands](./commands.md) and [configuration](./configuration.md).

* Examples of commands for [downloading data](./download.md) and
  [maintaining the store](./maintenance.md).

* An explanation of the [processing pipeline](./pipeline.md) used
  during retrieval of data.

* Notes on [Rover development](./development.md).
