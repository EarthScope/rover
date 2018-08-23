
# An Introduction to rover

The `rover` command helps build, index and maintain a repository of
data.  The data are retrieved from a [fdsnws-dataselect
service](http://service.iris.edu/fdsnws/dataselect/1/); details of
available data are retrieved from an [irisws-availability
service](http://service.iris.edu/irisws/availability/1/).

For install instructions see the [Installation](index.md#installation) section.

## Exploring rover

There may be no need to read all this documentation.  Rover has some
help built-in.  Simply typing

    rover help

will give you an introductory screen.  While

    rover -h

displays all the configuration parameters.

## Further documentation

* [Commands](commands.md) and [configuration](configuration.md).

* Examples of commands for [downloading data](download.md) and
  [maintaining the repository](maintenance.md).

* An explanation of the [processing pipeline](pipeline.md) used
  during retrieval of data.

* Notes on [rover development](development.md) and [mseedindex
  install guidelines](mseedindex.md).
