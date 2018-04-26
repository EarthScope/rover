
Some tests assume that mssedindex is cloned and compiled in the directory
mseedindex parallel to the root rover directory.

Some tests access the tests/data directory via rover.__file__ (and so won't
work from an egg install, presumably).
