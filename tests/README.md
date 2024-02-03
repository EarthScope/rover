
Some tests assume that mseedindex is available in the PATH.

Note that logging doesn't play well with tests.  The logging system is
stateful and, once started in the first test, persists across all.  So
later tests are, in fact, logged to the initial temp directory.  Since
this is deleted once the first test finishes we must be careful to
avoid log rollover.
