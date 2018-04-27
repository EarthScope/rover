
Some tests assume that mssedindex is cloned and compiled in the directory
mseedindex parallel to the root rover directory.

Some tests access the tests/data directory via rover\.\__file\_\_ (and
so won't work from an egg install, presumably).

Note that logging doesn't play well with tests.  The logging system is
stateful and, once started in the first test, persists across all.  So
later tests are, in fact, logged to the initial temp directory.  Since
this is deleted once the first test finishes we must be carefulto
avoid log rollover.
