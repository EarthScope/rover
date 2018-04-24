
from contextlib import closing

from os import listdir, stat
from os.path import join, basename, expanduser, abspath, isfile, isdir, dirname

from .sqlite import Sqlite, NoResult


class Workers():

    pass


class Mseedindex(Sqlite):
    '''
    Wrap mseedindex, extending functionality to:
    * Work with a standard directory layout on disk
    * Run multiple instances in parallel.
    * Skip files aalready processed (using size and last modified date)
    * Remove files from the index that have gone from disk

    To do this we manage parallel database tabeles containing file
    directory, size and last modified data.
    '''

    def __init__(self, dbpath, root, log):
        super().__init__(dbpath, log)
        self._load_tables()
        self._check_root(abspath(expanduser(root)))

    def _load_tables(self):
        self._execute('''create table if not exists rover_mseeddirs (
                           id integer primary key autoincrement,
                           parent integer,
                           path text unique,
                           foreign key (parent) references rover_mseeddirs(id) on delete cascade
                     )''')
        self._execute('''create table if not exists rover_mseedfiles (
                            id integer primary key autoincrement,
                            dir integer not null,
                            name text not null,
                            size integer not null,
                            last_modified integer not null,
                            foreign key (dir) references rover_mseeddirs(id) on delete cascade,
                            constraint dir_name unique on rover_mseedfiles(dir, name)
                     )''')

    def _check_root(self, root):
        c = self._db.cursor()
        try:
            path = self._root()
            if root != path:
                self._log.warn('Index root has changed ("%s" != "%s")' % (root, path))
                self._remove_all_dirs()
                self._add_dir(None, root)
        except NoResult:
            self._add_dir(None, root)

    def _root(self):
        return self._fetchsingle('select path from rover_mseeddirs where parent is null')

    def scan(self):
        self._scan_dir(self._root(), 0)

    def _scan_dir(self, dir, level):
        self._log.debug('Scanning directory "%s" (level %d / 4)' % (dir, level))
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
                    self._add_dir(dir, join(dir, fs_dirs[-1]))
                    db_dirs.append(fs_dirs[-1])

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

    def _id_for_dir(self, dir):
        return self._fetchsingle('select id from rover_mseeddirs where path like ?', (dir,))

    def _db_dirs(self, dir):
        parent = self._id_for_dir(dir)
        paths = self._fetchall('select path from rover_mseeddirs where parent = ?', (parent,))
        dirs = [basename(path) for path in paths]
        return sorted(dirs)

    def _fs_dirs(self, dir):
        return sorted([name for name in listdir(dir) if isdir(join(dir, name))])

    def _remove_dir(self, dir):
        id = self._id_for_dir(dir)
        # this uses cascade to delete files and child dirs
        self._execute('delete from rover_mseeddirs  where id = ?' (id,))
        # todo - delete mseedindex too

    def _remove_all_dirs(self):
        self._log.warn('Deleting all entries from index')
        # this uses cascade to delete files
        self._execute('delete from rover_mseeddirs')
        # todo - delete mseedindex too

    def _add_dir(self, parent, dir):
        if parent:
            id = self._id_for_dir(parent)
        else:
            id = None
        self._execute('insert into rover_mseeddirs (parent, path) values (?, ?)', (id, dir))

    def _db_files(self, dir):
        id = self._id_for_dir(dir)
        results = self._fetchall('select name from rover_mseedfiles where dir = ?', (id,))
        return sorted([result[0] for result in results])

    def _fs_files(self, dir):
        return sorted([name for name in listdir(dir) if isfile(join(dir, name))])

    def _modified(self, file):
        statinfo = stat(file)
        id = self._id_for_dir(dirname(file))
        lastmod, size = self._fetchone('select last_modified, size from rover_mseedfiles where dir = ? and name = ?',
                                       (id, basename(file)))
        self._log.debug('%s lastmod %d / %d; size %d / %d' % (lastmod, statinfo.st_atime, size, statinfo.st_size))
        return lastmod != statinfo.st_atime or size != statinfo.st_size

    def _scan_and_record_file(self, file):
        pass

    def _remove_file(self, file):
        id = self._id_for_dir(dirname(file))
        self._execute('delete from rover_mseedfiles where dir = ? and name = ?', (id, basename(file)))
        # todo - delete mseedindex too

    def close(self):
        # todo - wait for workers
        self._db.close()


def index(args, log):
    with closing(Mseedindex(args.db_file, args.mseed_dir, log)) as indexer:
        indexer.scan()
