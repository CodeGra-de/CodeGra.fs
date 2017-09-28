#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import getenv

import uuid
from pathlib import Path

import logging
import os
from os import O_EXCL, O_CREAT, O_TRUNC, path
from enum import IntEnum
from stat import S_IFDIR, S_IFREG
from time import time
from errno import (
    EPERM, EEXIST, EINVAL, EISDIR, ENOENT, ENOTDIR, ENOTSUP, ENOTEMPTY
)
from getpass import getpass
from argparse import ArgumentParser

import tempfile
from fuse import FUSE, Operations, FuseOSError, LoggingMixIn
from cgapi import CGAPI, APICodes, CGAPIException


def handle_cgapi_exception(ex):
    if ex.code == APICodes.OBJECT_ID_NOT_FOUND:
        raise FuseOSError(ENOENT)
    elif ex.code == APICodes.INCORRECT_PERMISSION:
        raise FuseOSError(EPERM)
    else:
        raise ex


class DirTypes(IntEnum):
    FSROOT = 0
    COURSE = 1
    ASSIGNMENT = 2
    SUBMISSION = 3
    REGDIR = 4


class BaseFile():
    def __init__(self, data, name=None):
        self.id = data.get('id', None)
        self.name = name if name is not None else data['name']
        self.stat = None

    def getattr(self, submission=None, path=None):
        if self.stat is None:
            self.stat = {
                'st_size': 0,
                'st_atime': time(),
                'st_mtime': time(),
                'st_ctime': time(),
                'st_uid': os.getuid(),
                'st_gid': os.getegid(),
            }

            if submission is not None and path is not None:
                stat = cgapi.get_file_meta(submission.id, path)
                self.stat['st_size'] = stat['size']
                self.stat['st_mtime'] = stat['modification_date']

        return self.stat

    def setattr(self, key, value):
        if self.stat is None:
            self.getattr()

        self.stat[key] = value


class Directory(BaseFile):
    def __init__(self, data, name=None, type=DirTypes.REGDIR, writable=False):
        super(Directory, self).__init__(data, name)

        self.type = type
        self.writable = writable
        self.children = {}

    def getattr(self, submission=None, path=None):
        if self.stat is None:
            super(Directory, self).getattr(submission, path)
            mode = 0o770 if self.writable else 0o550
            self.stat['st_mode'] = S_IFDIR | mode
            self.stat['st_nlink'] = 2

        self.stat['st_atime'] = time()
        return self.stat

    def insert(self, file):
        if self.stat is None:
            self.getattr()

        self.children[file.name] = file
        self.stat['st_nlink'] += 1

    def pop(self, filename):
        try:
            file = self.children.pop(filename)
        except KeyError:
            raise FuseOSError(ENOENT)
        self.stat['st_nlink'] -= 1

        return file

    def read(self):
        res = list(self.children)
        res.extend(['.', '..'])
        return res


class TempDirectory(Directory):
    def __init__(self, *args, **kwargs):
        super(TempDirectory, self).__init__(*args, **kwargs)
        self.stat = {
            'st_size': 0,
            'st_atime': time(),
            'st_ctime': time(),
            'st_size': 0,
            'st_mtime': time(),
            'st_mode': S_IFDIR | 0o770,
            'st_nlink': 2,
        }


class TempFile:
    def __init__(self, name, tmpdir):
        self._tmpdir = tmpdir
        self.name = name

        self.__handle = None

        # Create a new temporary file
        self._filename = str(uuid.uuid4())

        while path.exists(
            path.join(path.join(self._tmpdir, self._filename)),
        ):  # pragma: no cover
            self._filename = str(uuid.uuid4())

        self.full_path = path.join(self._tmpdir, self._filename)
        Path(path.join(self.full_path)).touch()

    @property
    def stat(self):
        st = os.lstat(self.full_path)
        stat = {
            key: getattr(st, key)
            for key in (
                'st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime',
                'st_nlink', 'st_size', 'st_uid'
            )
        }
        stat['st_mode'] = S_IFREG | 0o770
        return stat

    @property
    def _handle(self):
        if self.__handle is None:
            self.__handle = open(self.full_path, 'r+b')
            self.__handle.seek(0)
        return self.__handle

    def getattr(self):
        return self.stat

    def setattr(self, key, value):  # pragma: no cover
        raise ValueError

    def utimens(self, atime, mtime):
        os.utime(self.full_path, (atime, mtime))

    def open(self, *args):
        # We open on demand so we never have problems with opening
        pass

    def read(self, offset, size):
        self._handle.seek(offset)
        return self._handle.read(size)

    def write(self, data, offset):
        handle = self._handle
        handle.seek(offset)
        res = handle.write(data)
        handle.flush()
        return res

    def release(self):
        if self.__handle is not None:
            self.__handle.flush()
            self.__handle.close()
        self.__handle = None

    def flush(self):
        self._handle.flush()

    def unlink(self):
        self.release()
        os.unlink(self.full_path)
        self._filename = None

    def truncate(self, length):
        self._handle.seek(0)
        self._handle.truncate(length)


class File(BaseFile):
    def __init__(self, data, name=None):
        super(File, self).__init__(data, name)

        self._data = None
        self.dirty = False

    @property
    def data(self):
        if self._data is None:
            self._data = cgapi.get_file(self.id)
            self.stat['st_size'] = len(self._data)
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def getattr(self, submission=None, path=None):
        if self.stat is None:
            super(File, self).getattr(submission, path)
            self.stat['st_mode'] = S_IFREG | 0o770
            self.stat['st_nlink'] = 1

        self.stat['st_atime'] = time()
        return self.stat

    def open(self, buf):
        self._data = buf
        self.stat['st_atime'] = time()

    def flush(self):
        if not self.dirty:
            return

        assert self._data is not None

        try:
            res = cgapi.patch_file(self.id, self._data)
        except CGAPIException as e:
            self.data = None
            self.dirty = False
            handle_cgapi_exception(e)

        self.dirty = False
        return res

    def release(self):
        self.data = None

    def truncate(self, length):
        if length == 0:
            self._data = bytes('', 'utf8')
        elif length <= self.stat['st_size']:
            self._data = self.data[:length]
        else:
            self._data = self.data + bytes(
                '\0' * (length - self.stat['st_size']), 'utf8'
            )
        self.stat['st_size'] = length
        self.stat['st_atime'] = time()
        self.stat['st_mtime'] = time()
        self.dirty = True

    def write(self, data, offset):
        if offset > self.stat['st_size']:
            self._data += bytes(offset - len(self.data))

        if self.stat['st_size'] - offset - len(data) > 0:
            # Write in between
            second_offset = offset + len(data)
            old_d = self.data
            self._data = old_d[:offset] + data + old_d[second_offset:]
        elif offset == 0:
            self._data = data
        else:
            self._data = self.data[:offset] + data

        self.stat['st_size'] = len(self._data)
        self.stat['st_atime'] = time()
        self.stat['st_mtime'] = time()
        self.dirty = True
        return len(data)


class CGFS(LoggingMixIn, Operations):
    def __init__(self, latest_only, fixed=False, tmpdir=None):
        self.latest_only = latest_only
        self.fixed = fixed
        self.files = {}
        self.fd = 0
        self._open_files = {}

        self._tmpdir = tmpdir

        self.files = Directory(
            {
                'id': None,
                'name': 'root'
            }, type=DirTypes.FSROOT
        )

        self.files.getattr()
        self.load_courses()
        print('Mounted')

    def load_courses(self):
        for course in cgapi.get_courses():
            assignments = course['assignments']

            course_dir = Directory(course, type=DirTypes.COURSE)
            course_dir.getattr()
            self.files.insert(course_dir)

            for assig in assignments:
                assig_dir = Directory(assig, type=DirTypes.ASSIGNMENT)
                assig_dir.getattr()
                course_dir.insert(assig_dir)

    def load_submissions(self, assignment):
        try:
            submissions = cgapi.get_submissions(assignment.id)
        except CGAPIException as e:  # pragma: no cover
            handle_cgapi_exception(e)

        seen = set()

        for sub in submissions:
            if sub['user']['id'] in seen:
                continue

            sub_dir = Directory(
                sub,
                name=sub['user']['name'] + ' - ' + sub['created_at'],
                type=DirTypes.SUBMISSION,
                writable=True
            )

            if self.latest_only:
                seen.add(sub['user']['id'])

            sub_dir.getattr()
            assignment.insert(sub_dir)

    def insert_tree(self, dir, tree):
        for item in tree['entries']:
            if 'entries' in item:
                new_dir = Directory(item, writable=True)
                new_dir.getattr()
                dir.insert(new_dir)
                self.insert_tree(new_dir, item)
            else:
                dir.insert(File(item))

    def load_submission_files(self, submission):
        try:
            files = cgapi.get_submission_files(submission.id)
        except CGAPIException as e:
            handle_cgapi_exception(e)
        self.insert_tree(submission, files)
        submission.tld = files['name']

    def split_path(self, path):
        return [x for x in path.split('/') if x]

    def get_submission(self, path):
        parts = self.split_path(path)
        submission = self.get_file(parts[:3])

        if submission is None:
            raise FuseOSError(ENOTDIR)

        return submission

    def get_file(self, path, start=None, expect_type=None):
        file = start if start is not None else self.files
        parts = self.split_path(path) if isinstance(path, str) else path

        for part in parts:
            if part == '':  # pragma: no cover
                continue

            try:
                if not file.children:
                    if file.type == DirTypes.ASSIGNMENT:
                        self.load_submissions(file)
                    elif file.type == DirTypes.SUBMISSION:
                        self.load_submission_files(file)
            except AttributeError:  # pragma: no cover
                if not isinstance(file, Directory):
                    raise FuseOSError(ENOTDIR)
                raise

            if part not in file.children:
                raise FuseOSError(ENOENT)
            file = file.children[part]

        if expect_type is not None:
            if expect_type is File and not isinstance(file, (File, TempFile)):
                raise FuseOSError(EISDIR)
            elif expect_type is Directory and not isinstance(file, Directory):
                raise FuseOSError(ENOTDIR)

        return file

    def get_dir(self, path, start=None):
        return self.get_file(path, start=start, expect_type=Directory)

    def chmod(self, path, mode):
        raise FuseOSError(EPERM)

    def chown(self, path, uid, gid):
        raise FuseOSError(EPERM)

    def create(self, path, mode):
        parts = self.split_path(path)
        if len(parts) <= 3:
            raise FuseOSError(EPERM)

        parent = self.get_dir(parts[:-1])
        fname = parts[-1]

        assert fname not in parent.children

        submission = self.get_submission(path)
        query_path = submission.tld + '/' + '/'.join(parts[3:])

        if self.fixed:
            file = TempFile(fname, self._tmpdir)
        else:
            try:
                fdata = cgapi.create_file(submission.id, query_path)
            except CGAPIException as e:
                handle_cgapi_exception(e)

            file = File(fdata, name=fname)
            file.setattr('st_size', fdata['size'])
            file.setattr('st_mtime', fdata['modification_date'])

        parent.insert(file)

        file.open(bytes('', 'utf8'))

        self.fd += 1
        self._open_files[self.fd] = file

        return self.fd

    def flush(self, path, fh=None):
        file = self.get_file(path, expect_type=File)
        res = file.flush()
        if res is not None:
            file.id = res['id']

    def getattr(self, path, fh=None):
        parts = self.split_path(path)
        file = self.get_file(parts)

        if isinstance(file, TempFile):
            return file.getattr()

        if file.stat is None and len(parts) > 3:
            try:
                submission = self.get_submission(path)
            except CGAPIException as e:
                handle_cgapi_exception(e)

            query_path = submission.tld + '/' + '/'.join(parts[3:])

            if isinstance(file, Directory):
                query_path += '/'
        else:
            submission = None
            query_path = None

        attrs = file.getattr(submission, query_path)
        if self.fixed and isinstance(file, File):
            attrs['st_mode'] &= ~0o222
        return attrs

    # TODO?: Add xattr support
    def getxattr(self, path, name, position=0):
        raise FuseOSError(ENOTSUP)

    # TODO?: Add xattr support
    def listxattr(self, path):  # pragma: no cover
        raise FuseOSError(ENOTSUP)

    def mkdir(self, path, mode):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])
        dname = parts[-1]

        # Fuse should handle this but better save than sorry
        if dname in parent.children:  # pragma: no cover
            raise FuseOSError(EEXIST)

        if self.fixed:
            parent.insert(TempDirectory({}, name=dname, writable=True))
        else:
            submission = self.get_submission(path)
            query_path = submission.tld + '/' + '/'.join(parts[3:]) + '/'
            ddata = cgapi.create_file(submission.id, query_path)

            parent.insert(Directory(ddata, name=dname, writable=True))

    def open(self, path, flags):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])

        try:
            file = self.get_file(parts[-1], start=parent, expect_type=File)
        except FuseOSError as e:
            if e.errno is not ENOENT:
                raise e
            if not flags & O_CREAT:
                raise FuseOSError(ENOENT)
            return self.create(path, 0o770)
        else:
            # This should be handled by FUSE.
            if flags & (O_CREAT & O_EXCL):  # pragma: no cover
                raise FuseOSError(EEXIST)

        if isinstance(file, TempFile):
            file.open()

        if flags & O_TRUNC:
            file.truncate(0)

        self.fd += 1
        self._open_files[self.fd] = file
        return self.fd

    def read(self, path, size, offset, fh):
        file = self._open_files[fh]

        if isinstance(file, TempFile):
            return file.read(offset, size)

        return file.data[offset:offset + size]

    def readdir(self, path, fh):
        dir = self.get_dir(path)

        if not dir.children:
            if dir.type == DirTypes.ASSIGNMENT:
                self.load_submissions(dir)
            elif dir.type == DirTypes.SUBMISSION:
                self.load_submission_files(dir)

        return dir.read()

    def readlink(self, path):
        raise FuseOSError(EINVAL)

    def release(self, path, fh):
        file = self._open_files[fh]
        file.release()
        del self._open_files[fh]

    # TODO?: Add xattr support
    def removexattr(self, path, name):
        raise FuseOSError(ENOTSUP)

    def rename(self, old, new):
        old_parts = self.split_path(old)
        old_parent = self.get_dir(old_parts[:-1])
        file = self.get_file(old_parts[-1], start=old_parent)

        new_parts = self.split_path(new)
        new_parent = self.get_dir(new_parts[:-1])
        if new_parts[-1] in new_parent.children:
            raise FuseOSError(EEXIST)

        submission = self.get_submission(old)
        if submission.id == self.get_submission(new):
            raise FuseOSError(EPERM)

        new_query_path = submission.tld + '/' + '/'.join(new_parts[3:]) + '/'

        if not isinstance(file, (TempDirectory, TempFile)):
            if self.fixed:
                raise FuseOSError(EPERM)

            try:
                res = cgapi.rename_file(file.id, new_query_path)
            except CGAPIException as e:
                handle_cgapi_exception(e)

            file.id = res['id']
        file.name = new_parts[-1]

        old_parent.pop(old_parts[-1])
        new_parent.insert(file)

    def rmdir(self, path):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])
        dir = self.get_file(parts[-1], start=parent)

        if dir.type != DirTypes.REGDIR:
            raise FuseOSError(EPERM)
        if dir.children:
            raise FuseOSError(ENOTEMPTY)

        if not isinstance(dir, TempDirectory):
            if self.fixed:
                raise FuseOSError(EPERM)

            try:
                cgapi.delete_file(dir.id)
            except CGAPIException as e:
                handle_cgapi_exception(e)

        parent.pop(parts[-1])

    # TODO?: Add xattr support
    def setxattr(
        self, path, name, value, options, position=0
    ):  # pragma: no cover
        raise FuseOSError(ENOTSUP)

    def statfs(self, path):
        return {
            'f_bsize': 512,
            'f_blocks': 4096,
            'f_bavail': 2048,
        }

    def symlink(self, target, source):
        raise FuseOSError(EPERM)

    def truncate(self, path, length, fh=None):
        if length < 0:  # pragma: no cover
            raise FuseOSError(EINVAL)

        if fh is not None and fh in self._open_files:  # pragma: no cover
            file = self._open_files[fh]
        else:
            file = self.get_file(path, expect_type=File)

        if self.fixed and not isinstance(file, TempFile):
            raise FuseOSError(EPERM)

        file.truncate(length)

    def unlink(self, path):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])
        fname = parts[-1]
        file = self.get_file(fname, start=parent, expect_type=File)

        if isinstance(file, TempFile):
            file.unlink()
        else:
            if self.fixed:
                raise FuseOSError(EPERM)

            try:
                cgapi.delete_file(file.id)
            except CGAPIException as e:
                handle_cgapi_exception(e)

        parent.pop(fname)

    def utimens(self, path, times=None):
        file = self.get_file(path)

        atime, mtime = times or (time(), time())
        if isinstance(file, TempFile):
            file.utimens(atime, mtime)
        else:
            file.setattr('st_atime', atime)
            file.setattr('st_mtime', mtime)

    def write(self, path, data, offset, fh):
        file = self._open_files[fh]

        if self.fixed and not isinstance(file, TempFile):
            raise FuseOSError(EPERM)

        return file.write(data, offset)


if __name__ == '__main__':
    print('Mounting... ')

    argparser = ArgumentParser(description='CodeGra.de file system')
    argparser.add_argument(
        'username',
        metavar='USERNAME',
        type=str,
        help='Your CodeGra.de username'
    )
    argparser.add_argument(
        'mountpoint',
        metavar='MOUNTPOINT',
        type=str,
        help='Mountpoint for the file system'
    )
    argparser.add_argument(
        '-p',
        '--password',
        metavar='PASSWORD',
        type=str,
        dest='password',
        help="""Your CodeGra.de password, don' pass this option if you want to
        pass your password over stdin."""
    )
    argparser.add_argument(
        '-u',
        '--url',
        metavar='URL',
        type=str,
        dest='url',
        help="""The url to find the api. This defaults to
        'https://codegra.de/api/v1/'. It can also be passed as a environment
        variable 'CGAPI_BASE_URL'"""
    )
    argparser.add_argument(
        '-v',
        '--verbose',
        dest='debug',
        action='store_true',
        default=False,
        help='Verbose mode: print all system calls (produces a LOT of output).'
    )
    argparser.add_argument(
        '-l',
        '--latest-only',
        dest='latest_only',
        action='store_true',
        default=False,
        help='Only see the latest submissions of students.'
    )
    argparser.add_argument(
        '-f',
        '--fixed',
        dest='fixed',
        action='store_true',
        default=False,
        help="""Mount the original files as read only. It is still possible to
        create new files, but it is not possible to alter existing files."""
    )
    args = argparser.parse_args()

    mountpoint = args.mountpoint
    username = args.username
    password = args.password if args.password is not None else getpass()
    latest_only = args.latest_only
    fixed = args.fixed

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    cgapi = CGAPI(
        username, password, args.url or getenv('CGAPI_BASE_URL', None)
    )

    with tempfile.TemporaryDirectory(dir=tempfile.gettempdir()) as tmpdir:
        fuse = FUSE(
            CGFS(latest_only, fixed=fixed, tmpdir=tmpdir),
            mountpoint,
            nothreads=True,
            foreground=True
        )
