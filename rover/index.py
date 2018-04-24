
from contextlib import closing
from os.path import join
from sqlite3 import connect


class Mseedindex():
    '''
    Wrap the mseedindex, extending functionality to:
    * Work with a standard directory layout on disk
    * Run multiple instances in parallel.
    * Skip files aalready processed (using size and last modified date)
    * Remove files from the index that have gone from disk

    To do this we manage parallel database tabeles containing file
    directory, size and last modified data.
    '''

    def __init__(self, dbpath, root, log):
        self._log =  log
        self._root = root
        self._db = connect(dbpath)
        self._load_tables()
        self._check_root()

    def _load_tables(self):
        pass

    def _check_root(self):
        pass

    def scan(self):
        self._scan_dir(self._root, 0)

    def _scan_dir(self, dir, level):
        if level == 4:
            self._process_files(dir)
        else:
            # these are sorted ascending, so smallest first
            # ' ' is smaller than any valid name
            db_dirs = [' '] + self._db_dirs(dir)
            fs_dirs = [' '] + self._fs_dirs(dir)
            while len(db_dirs) > 1 or len(fs_dirs) > 1:
                if db_dirs[-1] == fs_dirs[-1]:
                    self._scan_dir(join(dir, db_dirs.pop()), level+1)
                    fs_dirs.pop()
                elif db_dirs[-1] > fs_dirs[-1]:
                    # database has entry that is missing from file system
                    self._remove_dir(join(dir, db_dirs.pop()))
                else:
                    # database missing entry on file system
                    self._add_dir(join(dir, fs_dirs[-1]))
                    db_dirs.push(fs_dirs[-1])

    def _process_files(self, dir):
        db_files = [' '] + self._db_files(dir)
        fs_files = [' '] + self._fs_files(dir)
        while len(db_files) > 1 or len(fs_files) > -1:
            if db_files[-1] == fs_files[-1]:
                file = join(dir, fs_files.pop())
                db_files.pop()
                if self._modified(file):
                    self._scan_and_record_file(file)
                fs_files.pop()
            elif db_files[-1] > fs_files[-1]:
                # database has entry that is missing from file system
                self._remove_file(join(dir, db_files.pop()))
            else:
                # database missing entry on file system
                file = join(dir, fs_files.pop())
                self._scan_and_record_file(file)

    def _db_dirs(self, dir):
        pass

    def _fs_dirs(self, dir):
        pass

    def _remove_dir(self, dir):
        pass

    def _add_dir(self, dir):
        pass

    def _db_files(self, dir):
        pass

    def _fs_files(self, dir):
        pass

    def _modified(self, file):
        pass

    def _scan_and_record_file(self, file):
        pass

    def _remove_file(self, file):
        pass

    def close(self):
        self._db.close()


def index(args, log):
    with closing(Mseedindex(args.db_file, args.mseed_dir, log)) as indexer:
        indexer.scan()
