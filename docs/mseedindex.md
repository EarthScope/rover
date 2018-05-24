
# Mseedindex Install Guidelines

The [mseedindex](https://github.com/iris-edu/mseedindex) packaged is
used by Rover.

Only sqlite database support is required, so install may be as easy
as:

    * Downloading the latest source from
      [here](https://github.com/iris-edu/mseedindex/releases)

    * Unpacking the source

    * Building with `WITHOUTPOSTGRESQL=1 make`

    * Copying the `mseedindex` program to `/usr/bin` or similar.

If you do not want to install `mseedinindex` globally then you may
need to configure rover:

    * Install rover

    * Run `rover reset-config` to generate a configurration file
      (by default at `~/rover/config).

    * Edit the `mseed-cmd` value in that file appropriately, so that
      rover can execute mseedindex.
