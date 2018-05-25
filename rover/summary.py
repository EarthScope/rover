
from .args import SUMMARY
from .sqlite import SqliteSupport


"""
Commands related to the index:

The 'rover summary' command - creates a summary of the tsindex table.
The 'rover list-summary' command - displays entries from the summary table.
"""


class Summarizer(SqliteSupport):
    """
### Summary

    rover summary

Create a summary of the index in the database.  This lists the overall span of data for each SNCL and can
be queries using `rover list-summary`.

##### Significant Parameters

@mseed-db
@verbosity
@log-dir
@log-name
@log-verbosity

##### Examples

    rover summary

will create the summary.


    """

    def __init__(self, config):
        super().__init__(config)

    def run(self, args):
        if len(args):
            raise Exception('Usage: rover %s' % SUMMARY)
        self.execute('drop table if exists tsindex_summary')
        self.execute('''create table tsindex_summary as
                            select network, station, location, channel, 
                            min(starttime) AS earliest, max(endtime) AS latest, 
                            datetime('now') as updt
                        from tsindex
                        group by 1,2,3,4''')

