#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division

import logging

from collections import defaultdict
from enum import IntEnum
from errno import EINVAL, EISDIR, ENOENT, ENOTDIR, ENOTEMPTY, ENOTSUP, EPERM
from getpass import getpass
from os import O_CREAT, O_EXCL, O_RDONLY, O_RDWR, O_TRUNC, O_WRONLY
from stat import S_IFDIR, S_IFREG
from sys import argv, exit
from time import time

from fuse import FUSE, FuseOSError, LoggingMixIn, Operations

from cgapi import CGAPI, CGAPIException, APICodes

class DirTypes(IntEnum):
    FSROOT = 0
    COURSE = 1
    ASSIGNMENT = 2
    SUBMISSION = 3
    REGDIR = 4


class BaseFile():
    def __init__(self, data, name=None):
        self.id = data['id']
        self.name = name if name is not None else data['name']
        self.stat = None

    def getattr(self, submission=None, path=None):
        if self.stat is None:
            self.stat = {
                'st_size': 0,
                'st_atime': time(),
                'st_mtime': time(),
                'st_ctime': time(),
            }

            if submission is not None and path is not None:
                stat = cgapi.get_file_meta(submission.id, path)
                self.stat['st_size'] = stat['size']
                self.stat['st_mtime'] = stat['modification_date']

        return self.stat


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

        self.stat['st_mtime'] = time()
        return self.stat

    def insert(self, file):
        self.children[file.name] = file
        self.stat['st_nlink'] += 1

    def get(self, filename):
        if filename not in self.children:
            raise FuseOSError(ENOENT)
        return self.children[filename]

    def pop(self, filename):
        try:
            file = self.children.pop(filename)
        except KeyError:
            raise FuseOSError(ENOENT)
        self.stat['st_nlink'] -= 1

        return file

    def read(self):
        return ['.', '..'] + [x for x in self.children]


class File(BaseFile):
    def __init__(self, data, name=None):
        super(File, self).__init__(data, name)

        self.data = None
        self.dirty = False

    def getattr(self, submission=None, path=None):
        if self.stat is None:
            super(File, self).getattr(submission, path)
            self.stat['st_mode'] = S_IFREG | 0o770
            self.stat['st_nlink'] = 1

        self.stat['st_mtime'] = time()
        return self.stat

    def open(self, buf):
        self.data = buf
        self.stat['st_size'] = len(buf)
        self.stat['st_atime'] = time()

    def flush(self):
        if not self.dirty:
            return

        try:
            cgapi.patch_file(self.id, self.data)
        except CGAPIException as e:
            if e['code'] == APICodes.OBJECT_ID_NOT_FOUND:
                raise FuseOSError(ENOENT)
            elif e['code'] == APICodes.INCORRECT_PERMISSION:
                raise FuseOSError(EPERM)

        self.dirty = False

    def read(self, offset, length):
        pass

    def release(self):
        self.data = None

    def truncate(self, length):
        data = self.data
        if length <= self.stat['st_size']:
            self.data = data[:length]
        else:
            self.data = data + bytes('\0' * (length - self.stat['st_size']), 'utf8')
        self.stat['st_size'] = length
        self.stat['st_atime'] = time()
        self.stat['st_mtime'] = time()
        self.dirty = True

    def write(self, data, offset):
        print(type(self.data), type(data))
        self.data = self.data[:offset] + data
        self.stat['st_size'] = len(self.data)
        self.stat['st_atime'] = time()
        self.stat['st_mtime'] = time()
        self.dirty = True
        return len(data)


class CGFS(LoggingMixIn, Operations):
    def __init__(self):
        self.files = {}
        self.fd = 0

        self.files = Directory({ 'id': None, 'name': 'root' }, type=DirTypes.FSROOT)
        self.files.getattr()
        self.load_courses()

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
        except CGAPIException:
            raise FuseOSError(ENOTDIR)

        for sub in submissions:
            sub_dir = Directory(sub, name=sub['user']['name'] + ' - ' + sub['created_at'], type=DirTypes.SUBMISSION, writable=True)
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
        except CGAPIException:
            raise FuseOSError(ENOTDIR)
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
        if start is None:
            start = self.files

        file = start
        parts = self.split_path(path) if isinstance(path, str) else path

        for part in parts:
            if part == '':
                continue

            if not isinstance(file, Directory):
                raise FuseOSError(ENOTDIR)

            if len(file.children) == 0:
                if file.type == DirTypes.ASSIGNMENT:
                    self.load_submissions(file)
                elif file.type == DirTypes.SUBMISSION:
                    self.load_submission_files(file)

            file = file.get(part)

        if expect_type is not None:
            if expect_type is File and not isinstance(file, File):
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
        parent = self.get_dir(parts[:-1])
        fname = parts[-1]

        if fname in parent.children:
            file = parent.get(fname)
        else:
            submission = self.get_submission(path)
            query_path = submission.tld + '/' + '/'.join(parts[3:])

            try:
                fdata = cgapi.create_file(submission.id, query_path)
            except CGAPIException:
                raise FuseOSError(EPERM)

            file = File(fdata, name=parts[-1])
            parent.insert(file)

        file.open(bytes('', 'utf8'))

        self.fd += 1
        return self.fd

    def flush(self, path, fh=None):
        file = self.get_file(path, expect_type=File)
        file.flush()

    def getattr(self, path, fh=None):
        parts = self.split_path(path)
        file = self.get_file(parts)

        if file.stat is None and len(parts) > 3:
            submission = self.get_submission(path)

            query_path = submission.tld + '/' + '/'.join(parts[3:])
            if isinstance(file, Directory):
                query_path += '/'
        else:
            submission = None
            query_path = None

        return file.getattr(submission, query_path)

    # TODO?: Add xattr support
    def getxattr(self, path, name, position=0):
        raise FuseOSError(ENOTSUP)

    # TODO?: Add xattr support
    def listxattr(self, path):
        raise FuseOSError(ENOTSUP)

    def mkdir(self, path, mode):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])
        dname = parts[-1]

        if dname in parent.children:
            raise FuseOSError(EEXIST)

        submission = self.get_submission(path)
        ddata = cgapi.create_file(submission.id, path, is_directory=True)

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
            if flags & (O_CREAT & O_EXCL):
                raise FuseOSError(EEXIST)

        if file.data is None:
            file.open(bytes(cgapi.get_file(file.id), 'utf8'))

        if flags & O_TRUNC:
            file.truncate(0)

        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        file = self.get_file(path, expect_type=File)
        return file.data[offset:offset + size]

    def readdir(self, path, fh):
        dir = self.get_dir(path)

        if len(dir.children) == 0:
            if dir.type == DirTypes.ASSIGNMENT:
                self.load_submissions(dir)
            elif dir.type == DirTypes.SUBMISSION:
                self.load_submission_files(dir)

        return dir.read()

    def readlink(self, path):
        raise FuseOSError(EINVAL)

    def release(self, path, fh=None):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])
        fname = parts[-1]

        if fname in parent.children:
            file = parent.get(fname)
            if isinstance(file, File):
                file.release()


    # TODO?: Add xattr support
    def removexattr(self, path, name):
        raise FuseOSError(ENOTSUP)

    def rename(self, old, new):
        parts = self.split_path(old)
        parent = self.get_dir(parts[:-1])
        file = parent.pop(parts[-1])

        parts = self.split_path(new)
        parent = self.get_dir(parts[:-1])
        parent.insert(file)

    def rmdir(self, path):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])

        if len(parent.children) != 0:
            raise FuseOSError(ENOTEMPTY)

        parent.pop(parts[-1])

    # TODO?: Add xattr support
    def setxattr(self, path, name, value, options, position=0):
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
        if length < 0:
            raise FuseOSError(EINVAL)

        file = self.get_file(path, expect_type=File)
        file.truncate(length)

    def unlink(self, path):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])
        fname = parts[-1]
        file = self.get_file(fname, start=parent, expect_type=File)

        try:
            cgapi.delete_file(file.id)
        except CGAPIException as e:
            if e.errno == APICodes.OBJECT_ID_NOT_FOUND:
                raise FuseOSError(ENOENT)
            elif e.errno == APICodes.INCORRECT_PERMISSION:
                raise FuseOSError(EPERM)

        parent.pop(fname)

    def utimens(self, path, times=None):
        file = self.get_file(path)

        atime, mtime = times if times else (time(), time())
        files[path]['st_atime'] = atime
        files[path]['st_mtime'] = mtime

    def write(self, path, data, offset, fh):
        file = self.get_file(path, expect_type=File)
        return file.write(data, offset)

if __name__ == '__main__':
    if len(argv) != 3:
        print('usage: %s MOUNTPOINT USER' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)

    # cgapi = CGAPI(argv[2], getpass())
    cgapi = CGAPI(argv[2], 'Thomas Schaper')

    fuse = FUSE(CGFS(), argv[1], foreground=True)
