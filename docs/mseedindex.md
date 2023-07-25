---
title: mseedindex install guidelines (for ROVER)
layout: default
---

ROVER is dependent upon the program [mseedindex](https://github.com/EarthScope/mseedindex) to maintain an index of downloaded miniSEED data.

To install mseedindex, a system must have a `C` (or `C++`) compiler and the `make` program. The instructions below outline mseedindex installation:

* Download the latest source code from the
  [mseedindex release page](https://github.com/EarthScope/mseedindex/releases).

* Unpack the source code, i.e. untar or unzip.

* On Unix-like computers, build/compile with `WITHOUTPOSTGRESQL=1 make`.

* Copy the `mseedindex` program to `/usr/bin` or similar location that is in your PATH.

If you do not want to install mseedindex in a location in your PATH then you will need to set the `mseedindex-cmd` option in your `rover.config` file(s) to the location of the mseedindex binary.
