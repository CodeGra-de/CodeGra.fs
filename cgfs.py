#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import uuid
import socket
import hashlib
import logging
import datetime
import tempfile
import threading
import traceback
from os import O_EXCL, O_CREAT, O_TRUNC, path, getenv
from enum import IntEnum
from stat import S_IFDIR, S_IFREG
from time import time
from errno import (
    EPERM, EEXIST, EINVAL, EISDIR, ENOENT, ENOTDIR, ENOTSUP, ENOTEMPTY
)
from getpass import getpass
from pathlib import Path
from argparse import ArgumentParser

from fuse import FUSE, Operations, FuseOSError, LoggingMixIn

from cgapi import CGAPI, APICodes, CGAPIException


def handle_cgapi_exception(ex):
    if ex.code == APICodes.OBJECT_ID_NOT_FOUND.name:
        raise FuseOSError(ENOENT)
    elif ex.code == APICodes.INCORRECT_PERMISSION.name:
        raise FuseOSError(EPERM)
    else:
        raise ex


def wrap_string(string, prefix, max_len):
    res = []
    first = True
    _prefix = ''
    while string:
        last_word = 0
        if len(string) <= max_len and '\n' not in string:
            last_word = max_len
        else:
            for i in range(min(max_len, len(string))):
                if string[i] == ' ':
                    last_word = i
                elif string[i] == '\n':
                    res.append((_prefix + string[:i]) if i else '')
                    res.append('')
                    string = string[i + 1:]
                    while string.strip(' ')[0] == '\n':
                        res.append('')
                        string = string.strip(' ')[1:]
                    last_word = None
                    break

        if last_word is not None:
            res.append(_prefix + string[:last_word or max_len])
            string = string[last_word + 1 if last_word else max_len:]
        if first:
            _prefix = prefix
            max_len -= len(prefix)
            first = False
    return ('\n').join(res), len(res) - 1


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


class SingleFile:
    pass


class SpecialFile(SingleFile):
    def __init__(self, name, data=b''):
        self.mode = 0o550
        self.name = name
        self.data = data

    def get_data(self):
        return self.data

    def getattr(self):
        return {
            'st_size': len(self.get_data()),
            'st_atime': self.get_st_atime(),
            'st_mtime': self.get_st_mtime(),
            'st_ctime': self.get_st_ctime(),
            'st_uid': os.getuid(),
            'st_gid': os.getegid(),
            'st_mode': S_IFREG | self.mode,
            'st_nlink': 1,
        }

    def get_st_atime(self):
        return time()

    def get_st_mtime(self):
        return time()

    def get_st_ctime(self):
        return time()

    def read(self, offset, size):
        return self.get_data()[offset:offset + size]

    def release(self):
        return

    def open(self):
        return

    def truncate(self, length):
        raise FuseOSError(EPERM)

    def unlink(self):
        raise FuseOSError(EPERM)

    def utimens(self, atime, mtime):
        return

    def write(self, data, offset):
        raise FuseOSError(EPERM)

    def flush(self):
        return

    def fsync(self):  # pragma: no cover
        return self.flush()


class SocketFile(SpecialFile):
    def __init__(self, loc, name):
        super(SocketFile, self).__init__(name=name)
        self.loc = loc

    def get_data(self):
        return self.loc


class HelpFile(SpecialFile):
    def __init__(self, from_class):
        name = os.path.splitext(from_class.NAME)[0] + '.help'
        super(HelpFile, self).__init__(name=name)
        self.mode = 0o550
        self.from_class = from_class

    def get_data(self):
        return bytes(
            '\n'.join(
                [
                    l[4:] if l[:4] == ' ' * 4 else l
                    for l in self.from_class.__doc__.splitlines()
                ]
            ), 'utf8'
        )

    def flush(self):
        pass


class CachedSpecialFile(SpecialFile):
    DELTA = datetime.timedelta(seconds=60)

    def __init__(self, name):
        super(CachedSpecialFile, self).__init__(name=name)
        self.data = None
        self.time = None
        self.mtime = time()
        self.mode = 0o770
        self.overwrite = False

    def get_st_mtime(self):
        return self.mtime

    def get_data(self):
        if self.data and (datetime.datetime.utcnow() - self.time) < self.DELTA:
            return self.data
        elif self.overwrite:
            return self.data

        data = self.get_online_data()
        if data != self.data:
            self.mtime = time() + 1

        self.time = datetime.datetime.utcnow()
        self.data = data

        return self.data

    def write(self, data, offset):
        self.overwrite = True
        self.data = self.get_data()

        if offset > len(self.data):
            self.data += bytes(offset - len(self.data))

        if len(self.data) - offset - len(data) > 0:
            # Write in between
            second_offset = offset + len(data)
            self.data = self.data[:offset] + data + self.data[second_offset:]
        elif offset == 0:
            self.data = data
        else:
            self.data = self.data[:offset] + data

        self.data = self.data
        return len(data)

    def fsync(self):
        return self.flush()

    def unlink(self):
        self.overwrite = False
        self.data = None
        raise ValueError

    def flush(self):
        if not self.overwrite:
            return

        try:
            parsed = self.parse(self.data)
        except ValueError:
            raise FuseOSError(EPERM)

        try:
            self.send_back(parsed)
        except CGAPIException as e:
            print('error from server:', e.message)
            handle_cgapi_exception(e)
        except:
            traceback.print_exc()
            raise

        self.overwrite = False
        self.data = None
        self.data = self.get_data()

    def truncate(self, length):
        self.data = self.get_data()

        if length == 0:
            self.data = bytes('', 'utf8')
        elif length <= len(self.data):
            self.data = self.data[:length]
        else:
            self.data = self.data + bytes(
                '\0' * (length - self.stat['st_size']), 'utf8'
            )

        self.overwrite = True


class RubricSelectFile(CachedSpecialFile):
    NAME = '.cg-rubric.md'

    def __init__(self, api, submission_id):
        super(RubricSelectFile, self).__init__(name=self.NAME)
        self.submission_id = submission_id
        self.lookup = {}
        self.api = api

    def get_online_data(self):
        res = []
        self.lookup = {}
        d = self.api.get_submission_rubric(self.submission_id)
        sel = set(i['id'] for i in d['selected'])
        l_num = 0
        for rub in d['rubrics']:
            res.append('# ')
            res.append(rub['header'])
            res.append('\n')

            new, num = wrap_string(' ' + rub['description'], ' ', 80)
            res.append(new)
            res.append('\n')
            res.append('-' * 79)
            res.append('\n')

            l_num += num + 3

            rub['items'].sort(key=lambda i: i['points'])
            for item in rub['items']:
                self.lookup[l_num] = item['id']
                new, num = wrap_string(
                    '- [{}] {} ({}) - {}'.format(
                        'x' if item['id'] in sel else ' ',
                        item['header'],
                        item['points'],
                        item['description'],
                    ),
                    '  ',
                    80,
                )
                res.append(new)
                res.append('\n')
                l_num += num + 1

            res.append('\n')
            l_num += 1

        return bytes(''.join(res[:-1]), 'utf8')

    def parse(self, data):
        sel = []

        for i, line in enumerate(data.split(b'\n')):
            if line.startswith(b'- [x]') or line.startswith(b'- [X]'):
                try:
                    sel.append(self.lookup[i])
                except KeyError:
                    raise FuseOSError(EPERM)

        return sel

    def send_back(self, sel):
        self.api.select_rubricitems(self.submission_id, sel)


class RubricEditorFile(CachedSpecialFile):
    """This file lets users edit rubrics.

    The format is as follows:

    file:
      rubric file | ε
    newline:
      '\\n'
    rubric:
      header newline description sep newline items
    id_hash:
      '[' (ANY_NON_SPACE_CHAR * 16) '] ' | ε
    header:
      '# ' id_hash ' ANY_NON_NEWLINE_CHAR
    description:
      description_line description?
    description?:
      description_line description? | ε
    description_line:
      '  ' ANY_NON_NEWLINE_CHAR newline
    sep?:
      '-' | ε
    sep:
      '-' sep?
    items:
      item items?
    items?:
      item items? | ε
    float:
      ALPHANUM_CHARS | ALPHANUM_CHARS '.' ALPHANUM_CHARS
    title:
      ANY_NOT_-_CHAR
    description:
      SINGLE_NOT_-_CHAR ANY_NON_NEWLINE_CHAR newline description | SINGLE_NOT_-_CHAR ANY_NON_NEWLINE_CHAR
    item:
      '- ' id_hash '('  float ') ' '-' description newline

    Please note that the ids are hashes, so they should not be edited. Removing
    items is only supported when editing rubrics is enabled. The file will
    change after saving, make sure your editor reloads a file after saving.

    An example file could be like this:
    # My header
    My description
    of multiple
    lines
    --------------
    - (5.0) First item - Description
    - (1.0) Second item - Multiline
      description

      is here.
    """
    NAME = '.cg-edit-rubric.md'

    def __init__(self, api, assignment_id, append_only=True):
        super(RubricEditorFile, self).__init__(name=self.NAME)
        self.api = api
        self.assignment_id = assignment_id
        self.append_only = append_only
        self.lookup = {}

    def hash_id(self, id):
        h = hashlib.sha256(bytes(id)).hexdigest()[:16]
        self.lookup[h] = id
        return h

    def get_online_data(self):
        res = []
        self.lookup = {}

        for rub in self.api.get_assignment_rubric(self.assignment_id):
            res.append('# ')
            res.append('[{}] '.format(self.hash_id(rub['id'])))
            res.append(rub['header'])
            res.append('\n')

            new, _ = wrap_string(' ' + rub['description'], ' ', 80)
            res.append(new)
            res.append('\n')
            res.append('-' * 79)
            res.append('\n')

            rub['items'].sort(key=lambda i: i['points'])
            for item in rub['items']:
                new, _ = wrap_string(
                    '- [{}] ({}) {} - {}'.format(
                        self.hash_id(item['id']),
                        item['points'],
                        item['header'],
                        item['description'],
                    ),
                    '  ',
                    80,
                )
                res.append(new)
                res.append('\n')

            res.append('\n')

        if not res:
            return b''

        res.pop()
        return bytes(''.join(res), 'utf8')

    def parse(self, data):
        i = 0

        def strip_spaces(i):
            while data[i] == ' ':
                i += 1

            return i

        def parse_line(i):
            res = []

            while data[i] != '\n':
                res.append(data[i])
                i += 1

            return ''.join(res), i + 1

        def parse_description(i, end=None):
            if end is None:
                end = ['-']
            lines = []
            while True:
                if i == len(data) or data[i] in end:
                    while lines and lines[-1] in ['\n', ' ']:
                        lines.pop()
                    return ''.join(lines), i

                stripped_i = strip_spaces(i)

                if data[stripped_i] == '\n':
                    if lines and lines[-1] == ' ':
                        lines[-1] = '\n'
                    else:
                        lines.append('\n')
                    i = stripped_i + 1
                else:
                    line, i = parse_line(i)
                    lines.append(line.strip())
                    lines.append(' ')

        def parse_list(i):
            items = []
            while i < len(data) and data[i] != '#':
                i = strip_spaces(i + 1)
                if data[i] == '[':
                    i += 1
                    item_id = []
                    while data[i] != ']':
                        item_id.append(data[i])
                        i += 1
                    i = strip_spaces(i + 1)
                    item_id = ''.join(item_id)
                else:
                    item_id = None

                assert data[i] == '('
                i += 1
                points = []
                while data[i] != ')':
                    points.append(data[i])
                    i += 1
                i = strip_spaces(i + 1)
                points = float(''.join(points))

                header = []
                while data[i] != '-':
                    header.append(data[i])
                    i += 1
                i = strip_spaces(i + 1)
                header = ''.join(header).strip()
                desc, i = parse_description(i, end=['-', '#'])
                items.append((item_id, points, header, desc))

            return items, i

        def parse_item(i):
            i = strip_spaces(i)

            if data[i] == '[':
                h = []
                i += 1
                while data[i] != ']':
                    h.append(data[i])
                    i += 1
                i = strip_spaces(i + 1)

                item_id = ''.join(h)
            else:
                item_id = None
            name, i = parse_line(i)
            desc, i = parse_description(i)
            while data[i] != '\n':
                i += 1
            items, i = parse_list(i + 1)
            return (name, item_id, desc, items), i

        try:
            items = []
            data = data.decode('utf8')
            while i < len(data):
                assert data[i] == '#'
                item, i = parse_item(i + 1)
                items.append(item)
            return items

        except (IndexError, KeyError, AssertionError) as _:
            traceback.print_exc()
            raise FuseOSError(EPERM)

    def send_back(self, parsed):
        res = []

        def get_from_lookup(h):
            try:
                res = self.lookup[h]
                if self.append_only:
                    del self.lookup[h]
                return res
            except KeyError:
                raise FuseOSError(EPERM)

        for header, row_id, desc, items in parsed:
            items_res = []
            for item_id_hash, points, i_head, i_desc in items:
                items_res.append(
                    {
                        'description': i_desc,
                        'header': i_head,
                        'points': points,
                    }
                )
                if item_id_hash is not None:
                    items_res[-1]['id'] = get_from_lookup(item_id_hash)

            res.append(
                {
                    'description': desc,
                    'header': header,
                    'items': items_res
                }
            )
            if row_id is None:
                assert not any('id' in i for i in items_res)
            else:
                res[-1]['id'] = get_from_lookup(row_id)

        if self.append_only and self.lookup:
            raise FuseOSError(EPERM)

        self.api.set_assignment_rubric(self.assignment_id, {'rows': res})


class AssignmentSettingsFile(CachedSpecialFile):
    TO_USE = {'state', 'deadline', 'name'}

    def __init__(self, api, assignment_id):
        super(AssignmentSettingsFile,
              self).__init__(name='.cg-assignment-settings.ini')
        self.assignment_id = assignment_id
        self.api = api

    def send_back(self, data):
        self.api.set_assignment(self.assignment_id, data)

    def get_online_data(self):
        lines = []
        for k, v in self.api.get_assignment(self.assignment_id).items():
            if k not in self.TO_USE:
                continue

            if k == 'state' and v in {'grading', 'submitting'}:
                lines.append('{} = {}'.format(k, 'open'))
            else:
                lines.append('{} = {}'.format(k, v))

        lines.sort(key=lambda i: i[0])
        lines.append('')
        return bytes('\n'.join(lines), 'utf8')

    def parse(self, settings):
        res = {}
        for line in settings.split(b'\n'):
            if not line:
                continue

            key, val = line.split(b'=', 1)
            key = key.decode('utf8').strip()
            if key not in self.TO_USE:
                raise ValueError
            res[key] = val.decode('utf8').strip()

        if len(self.TO_USE) != len(res):
            raise ValueError

        return res


class TempFile(SingleFile):
    def __init__(self, name, tmpdir):
        self._tmpdir = tmpdir
        self.name = name
        self._cnt = 0
        self._unlink = False

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
                'st_atime', 'st_ctime', 'st_gid', 'st_mtime', 'st_nlink',
                'st_size', 'st_uid'
            )
        }
        stat['st_mode'] = S_IFREG | 0o770
        return stat

    def getattr(self):
        return self.stat

    def setattr(self, key, value):  # pragma: no cover
        raise ValueError

    def utimens(self, atime, mtime):
        os.utime(self.full_path, (atime, mtime))

    def open(self, *args):
        assert not self._unlink

        if self._cnt == 0:
            self._handle = open(self.full_path, 'r+b')

        self._cnt += 1

    def read(self, offset, size):
        self._handle.seek(offset)
        return self._handle.read(size)

    def write(self, data, offset):
        self._handle.seek(offset)
        res = self._handle.write(data)
        self._handle.flush()
        return res

    def release(self):
        self._cnt -= 1
        if self._cnt == 0:
            self._handle.close()
            self._handle = None

    def flush(self):
        return

    def fsync(self):  # pragma: no cover
        return self.flush()

    def unlink(self):
        self._unlink = True
        if self._cnt == 0:
            os.unlink(self.full_path)

    def truncate(self, length):
        if self._handle is None:
            os.truncate(self.full_path, length)
        else:
            self._handle.seek(0)
            self._handle.truncate(length)
            self._handle.flush()


class File(BaseFile, SingleFile):
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
        self.stat['st_size'] = len(data) if data is not None else 0
        self._data = data

    def getattr(self, submission=None, path=None):
        if self.stat is None:
            super(File, self).getattr(submission, path)
            self.stat['st_mode'] = S_IFREG | 0o770
            self.stat['st_nlink'] = 1

        return self.stat

    def open(self, buf):
        self.data = buf
        self.stat['st_atime'] = time()

    def read(self, offset, size):
        return self.data[offset:offset + size]

    def utimens(self, atime, mtime):
        self.setattr('st_atime', atime)
        self.setattr('st_mtime', mtime)

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
            self.data = bytes('', 'utf8')
        elif length <= self.stat['st_size']:
            self.data = self.data[:length]
        else:
            self.data = self.data + bytes(
                '\0' * (length - self.stat['st_size']), 'utf8'
            )
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


class APIHandler:
    OPS = {'add_feedback', 'get_feedback', 'delete_feedback', 'is_file'}

    def __init__(self, cgfs):
        self.cgfs = cgfs
        self.stop = False

    def handle_conn(self, conn):
        data = b''
        while True:
            new_data = conn.recv(1024)
            data += new_data
            if len(new_data) < 1024:
                break

        if not data:
            return

        with self.cgfs._lock:
            data = json.loads(data)
            op = data['op']
            if op not in self.OPS:
                conn.send(b'{"ok": false, "error": "unkown op"}')
            del data['op']
            payload = data
            try:
                res = getattr(self, op)(payload)
                conn.send(bytes(json.dumps(res).encode('utf8')))
            except:
                traceback.print_exc()
                conn.send(b'{"ok": false, "error": "Unkown error"}')

    def run(self, sock):
        sock.settimeout(1.0)

        while not self.stop:
            try:
                conn, addr = sock.accept()
            except socket.timeout:
                continue
            except OSError:
                traceback.print_exc()
                print('Closing socket')
                return
            except:
                continue

            try:
                conn.settimeout(1.0)
                self.handle_conn(conn)
            finally:
                conn.close()

    def delete_feedback(self, payload):
        f_name = self.cgfs.strippath(payload['file'])
        line = payload['line']

        with self.cgfs._lock:
            try:
                f = self.cgfs.get_file(f_name, expect_type=SingleFile)
            except:
                return {'ok': False, 'error': 'File not found'}

            try:
                res = cgapi.delete_feedback(f.id, line)
            except:
                return {'ok': False, 'error': 'The server returned an error'}

            return {'ok': True}

    def is_file(self, payload):
        f_name = self.cgfs.strippath(payload['file'])

        with self.cgfs._lock:
            try:
                f = self.cgfs.get_file(f_name, expect_type=SingleFile)
            except:
                return {'ok': False, 'error': 'File not found'}

            return {'ok': isinstance(f, File)}

    def get_feedback(self, payload):
        f_name = self.cgfs.strippath(payload['file'])

        with self.cgfs._lock:
            try:
                f = self.cgfs.get_file(f_name, expect_type=SingleFile)
            except:
                return {'ok': False, 'error': 'File not found', 'f': f_name}

            if isinstance(f, TempFile):
                return {'ok': False, 'error': 'File not a sever file'}

            try:
                res = cgapi.get_feedback(f.id)
            except:
                return {'ok': False, 'error': 'The server returned an error'}

            return {'ok': True, 'data': res}

    def add_feedback(self, payload):
        f_name = self.cgfs.strippath(payload['file'])
        line = payload['line']
        message = payload['message']

        with self.cgfs._lock:
            try:
                f = self.cgfs.get_file(f_name, expect_type=SingleFile)
            except:
                return {'ok': False, 'error': 'File not found'}

            if isinstance(f, TempFile):
                return {'ok': False, 'error': 'File not a sever file'}

            try:
                cgapi.add_feedback(f.id, line, message)
            except:
                return {'ok': False, 'error': 'The server returned an error'}

            return {'ok': True}


class CGFS(LoggingMixIn, Operations):
    API_FD = 0

    def __init__(
        self,
        latest_only,
        socketfile,
        mountpoint,
        fixed=False,
        tmpdir=None,
            rubric_append_only=True,
            quiet=False,
    ):
        self.latest_only = latest_only
        self.fixed = fixed
        self.files = {}
        self.fd = 1
        self.mountpoint = mountpoint
        self._lock = threading.RLock()
        self._open_files = {}
        self.quiet = quiet

        self._tmpdir = tmpdir

        self._socketfile = socketfile
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(self._socketfile)
        self.socket.listen()
        self.api_handler = APIHandler(self)
        threading.Thread(
            target=self.api_handler.run, args=(self.socket, )
        ).start()
        self.special_socketfile = SocketFile(
            bytes(socketfile, 'utf8'), '.api.socket'
        )

        self.rubric_append_only = rubric_append_only

        self.files = Directory(
            {
                'id': None,
                'name': 'root'
            }, type=DirTypes.FSROOT
        )

        with self._lock:
            self.files.getattr()
            self.files.insert(self.special_socketfile)
            self.files.insert(
                SpecialFile(
                    '.cg-mode', b'FIXED\n' if self.fixed else b'NOT_FIXED\n'
                )
            )
            self.load_courses()
        if not self.quiet:
            print('Mounted')

    def strippath(self, path):
        path = os.path.abspath(path)
        return path[len(self.mountpoint):]

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
                assig_dir.insert(AssignmentSettingsFile(cgapi, assig['id']))
                assig_dir.insert(
                    RubricEditorFile(
                        cgapi, assig['id'], self.rubric_append_only
                    )
                )
                assig_dir.insert(HelpFile(RubricEditorFile))
                assig_dir.insert(
                    SpecialFile(
                        '.cg-assignment-id',
                        data=str(assig['id']).encode() + b'\n'
                    )
                )

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
            sub_dir.insert(RubricSelectFile(cgapi, sub['id']))
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
        submission.insert(
            SpecialFile(
                '.cg-submission-id', data=str(submission.id).encode() + b'\n'
            )
        )
        submission.tld = files['name']

    def split_path(self, path):
        return [x for x in path.split('/') if x]

    def get_submission(self, path):
        parts = self.split_path(path)
        submission = self.get_file(parts[:3])
        try:
            submission.tld
        except AttributeError:
            self.load_submission_files(submission)

        return submission

    def get_file(self, path, start=None, expect_type=None):
        file = start if start is not None else self.files
        parts = self.split_path(path) if isinstance(path, str) else path

        for part in parts:
            if part == '':  # pragma: no cover
                continue

            try:
                if not any(
                    not isinstance(f, SpecialFile)
                    for f in file.children.values()
                ):
                    if file.type == DirTypes.ASSIGNMENT:
                        self.load_submissions(file)
                    elif file.type == DirTypes.SUBMISSION:
                        self.load_submission_files(file)
            except AttributeError:  # pragma: no cover
                if not isinstance(file, Directory):
                    raise FuseOSError(ENOTDIR)
                raise

            if part not in file.children or file.children[part] is None:
                raise FuseOSError(ENOENT)
            file = file.children[part]

        if expect_type is not None:
            if not isinstance(file, expect_type):
                raise FuseOSError(EISDIR)

        return file

    def get_dir(self, path, start=None):
        return self.get_file(path, start=start, expect_type=Directory)

    def chmod(self, path, mode):
        raise FuseOSError(EPERM)

    def chown(self, path, uid, gid):
        raise FuseOSError(EPERM)

    def create(self, path, mode):
        with self._lock:
            return self._create(path, mode)

    def _create(self, path, mode):
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

    def fsync(self, path, _, fh):
        self._flush_or_fsync(path, fh, 'fsync')

    def flush(self, path, fh):
        self._flush_or_fsync(path, fh, 'flush')

    def _flush_or_fsync(self, path, fh, todo):
        with self._lock:
            if fh is None:  # pragma: no cover
                file = self.get_file(path, expect_type=SingleFile)
            else:
                file = self._open_files[fh]
            res = getattr(file, todo)()
            if res is not None:
                file.id = res['id']

    def getattr(self, path, fh=None):
        with self._lock:
            return self._getattr(path, fh)

    def _getattr(self, path, fh):
        parts = self.split_path(path)
        file = self.get_file(parts)

        if isinstance(file, (TempFile, SpecialFile)):
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
        with self._lock:
            return self._mkdir(path, mode)

    def _mkdir(self, path, mode):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])
        dname = parts[-1]

        # Fuse should handle this but better safe than sorry
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
        with self._lock:
            return self._open(path, flags)

    def _open(self, path, flags):
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])

        file = self.get_file(parts[-1], start=parent, expect_type=SingleFile)

        if isinstance(file, (TempFile, SpecialFile)):
            file.open()

        # This is handled by fuse [0] but it can be disabled so it is better to
        # be safe than sorry as it can be enabled.
        # [0] https://sourceforge.net/p/fuse/mailman/message/29515577/
        if flags & O_TRUNC:  # pragma: no cover
            file.truncate(0)

        self.fd += 1
        self._open_files[self.fd] = file
        return self.fd

    def read(self, path, size, offset, fh):
        with self._lock:
            file = self._open_files[fh]
            return file.read(offset, size)

    def readdir(self, path, fh):
        with self._lock:
            dir = self.get_dir(path)

            if not dir.children or all(
                isinstance(f, SpecialFile) for f in dir.children.values()
            ):
                if dir.type == DirTypes.ASSIGNMENT:
                    self.load_submissions(dir)
                elif dir.type == DirTypes.SUBMISSION:
                    self.load_submission_files(dir)

            return dir.read()

    def readlink(self, path):
        raise FuseOSError(EINVAL)

    def release(self, path, fh):
        with self._lock:
            file = self._open_files[fh]
            file.release()
            del self._open_files[fh]

    # TODO?: Add xattr support
    def removexattr(self, path, name):
        raise FuseOSError(ENOTSUP)

    def rename(self, old, new):
        with self._lock:
            self._rename(old, new)

    def _rename(self, old, new):
        old_parts = self.split_path(old)
        old_parent = self.get_dir(old_parts[:-1])
        file = self.get_file(old_parts[-1], start=old_parent)

        if isinstance(file, SpecialFile):
            raise FuseOSError(EPERM)

        new_parts = self.split_path(new)
        new_parent = self.get_dir(new_parts[:-1])

        if new_parts[-1] in new_parent.children:
            raise FuseOSError(EEXIST)

        if len(new_parts) < 4 or len(old_parts) < 4:
            raise FuseOSError(EPERM)

        submission = self.get_submission(old)
        if submission.id != self.get_submission(new).id:
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
        with self._lock:
            self._rmdir(path)

    def _rmdir(self, path):
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
        with self._lock:
            if length < 0:  # pragma: no cover
                raise FuseOSError(EINVAL)

            if fh is not None and fh in self._open_files:  # pragma: no cover
                file = self._open_files[fh]
            else:
                file = self.get_file(path, expect_type=SingleFile)

            if self.fixed and not isinstance(file, (TempFile, SpecialFile)):
                raise FuseOSError(EPERM)

            file.truncate(length)

    def unlink(self, path):
        with self._lock:
            parts = self.split_path(path)
            parent = self.get_dir(parts[:-1])
            fname = parts[-1]
            file = self.get_file(fname, start=parent, expect_type=SingleFile)

            if isinstance(file, (TempFile, SpecialFile)):
                try:
                    file.unlink()
                except ValueError:
                    return
            else:
                if self.fixed:
                    raise FuseOSError(EPERM)

                try:
                    cgapi.delete_file(file.id)
                except CGAPIException as e:
                    handle_cgapi_exception(e)

            parent.pop(fname)

    def utimens(self, path, times=None):
        with self._lock:
            file = self.get_file(path)
            assert file is not None
            atime, mtime = times or (time(), time())

            if isinstance(file, File) and self.fixed:
                raise FuseOSError(EPERM)

            file.utimens(atime, mtime)

    def write(self, path, data, offset, fh):
        with self._lock:
            file = self._open_files[fh]

            if self.fixed and not isinstance(file, (TempFile, SpecialFile)):
                raise FuseOSError(EPERM)

            return file.write(data, offset)


if __name__ == '__main__':
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
    argparser.add_argument(
        '-q',
        '--quiet',
        dest='quiet',
        action='store_true',
        default=True,
        help="""Only output error messages.""",
    )
    argparser.add_argument(
        '-r',
        '--rubric-edit',
        dest='rubric_append_only',
        action='store_false',
        default=True,
        help="""Make it possible to delete rubric items or categories using the
        `.cg-edit-rubric.md` files. Note: this feature is experimental and can
        lead to data loss!"""
    )
    args = argparser.parse_args()

    mountpoint = os.path.abspath(args.mountpoint)
    username = args.username
    password = args.password if args.password is not None else getpass()
    latest_only = args.latest_only
    rubric_append_only = args.rubric_append_only
    fixed = args.fixed
    quiet = args.quiet

    if not quiet:
        print('Mounting... ')

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    cgapi = CGAPI(
        username, password, args.url or getenv('CGAPI_BASE_URL', None)
    )

    with tempfile.TemporaryDirectory(dir=tempfile.gettempdir()) as tmpdir:
        sockfile = tempfile.NamedTemporaryFile().name
        try:
            fs = CGFS(
                latest_only,
                socketfile=sockfile,
                fixed=fixed,
                mountpoint=mountpoint,
                tmpdir=tmpdir,
                rubric_append_only=rubric_append_only,
                quiet=quiet,
            )
            fuse = FUSE(
                fs,
                mountpoint,
                nothreads=True,
                foreground=True,
                direct_io=True
            )
        except RuntimeError:  # pragma: no cover
            traceback.print_exc()
        finally:
            fs.api_handler.stop = True
            os.unlink(sockfile)
