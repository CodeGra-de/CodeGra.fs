#!/usr/bin/env python
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only

import os
import abc
import sys
import enum
import json
import uuid
import ctypes
import socket
import typing as t
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
from errno import (  # type: ignore
    EPERM, EEXIST, EINVAL, EISDIR, ENOENT, ENOTDIR, ENOTSUP, ENOTEMPTY
)
from getpass import getpass
from pathlib import Path
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import codegra_fs
import codegra_fs.constants as constants
from codegra_fs.cgapi import CGAPI, APICodes, CGAPIException

try:
    import fuse  # type: ignore
    from fuse import FUSE, Operations, FuseOSError, LoggingMixIn  # type: ignore
    if sys.platform.startswith('win32'):
        import cffi
        import winfspy
except:

    class Operations:  # type: ignore
        pass

    class LoggingMixIn:  # type: ignore
        pass


cgapi = None  # type: t.Optional[CGAPI]

fuse_ptr = None

CGFS_TESTING = bool(os.getenv('CGFS_TESTING', False))  # type: bool

T = t.TypeVar('T')

logger = logging.getLogger(__name__)

try:
    # Python 3.5 doesn't support the syntax below
    if sys.version_info >= (3, 6):
        from codegra_fs.cgfs_types import PartialStat, FullStat, APIHandlerResponse

except:
    # Make sure mypy isn't needed when running
    PartialStat = dict  # type: ignore
    FullStat = dict  # type: ignore
    APIHandlerResponse = dict  # type: ignore


@enum.unique
class FsyncLike(enum.Enum):
    fsync = enum.auto()
    flush = enum.auto()


def remove_permission(
    perm: int, read: bool=False, write: bool=False, execute: bool=False
) -> int:
    return perm & ~create_permission(read, write, execute)


def create_permission(read: bool, write: bool, execute: bool) -> int:
    base = 4 if read else 0
    base += 2 if write else 0
    base += 1 if execute else 0
    if sys.platform.startswith('win32'):
        return base + base * 8 + base * 8 ** 2
    else:
        return 0 + base * 8 + base * 8 ** 2


def getuid() -> int:
    if sys.platform.startswith('win32'):
        return 0
    return os.getuid()


def getegid() -> int:
    if sys.platform.startswith('win32'):
        return 0
    return os.getegid()


def handle_cgapi_exception(ex) -> t.NoReturn:
    if ex.code == APICodes.OBJECT_ID_NOT_FOUND.name:
        raise FuseOSError(ENOENT)
    elif ex.code == APICodes.INCORRECT_PERMISSION.name:
        raise FuseOSError(EPERM)
    else:
        raise ex


class ParseException(ValueError):
    def __init__(self, message: str, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.message = message


class DirTypes(IntEnum):
    FSROOT = 0
    COURSE = 1
    ASSIGNMENT = 2
    SUBMISSION = 3
    REGDIR = 4


class BaseFile():
    def __init__(self, data: t.Dict[str, t.Any],
                 name: t.Optional[str]=None) -> None:
        self.id = data.get('id', None)
        self.name = name if name is not None else data['name']
        self.stat = None  # type: t.Optional[PartialStat]

    def getattr(
        self, submission: t.Optional['Directory']=None, path: str=None
    ) -> PartialStat:
        if self.stat is None:
            self.stat = {
                'st_size': 0,
                'st_atime': time(),
                'st_mtime': time(),
                'st_ctime': time(),
                'st_uid': getuid(),
                'st_gid': getegid(),
            }

            if submission is not None and path is not None:
                assert cgapi is not None
                stat = cgapi.get_file_meta(submission.id, path)
                self.stat['st_size'] = stat['size']
                self.stat['st_mtime'] = stat['modification_date']

        return self.stat

    def setattr(self, key: str, value: t.Union[float, str]) -> None:
        if self.stat is None:
            self.stat = self.getattr()

        if CGFS_TESTING:
            assert key in ('st_size', 'st_mtime', 'st_atime', 'st_mtime')

        self.stat[key] = value  # type: ignore


NOT_PRESENT = object()


class Directory(BaseFile):
    def __init__(
        self,
        data: t.Dict[str, t.Any],
        name: t.Optional[str]=None,
        type: DirTypes=DirTypes.REGDIR,
        writable: bool=False
    ) -> None:
        super(Directory, self).__init__(data, name)

        self.type = type
        self.writable = writable
        self.children = {}  # type: t.Dict[str, BaseFile]
        self.children_loaded = False
        self.stat = None  # type: t.Optional[FullStat]

        self.tld = NOT_PRESENT  # type: t.Union[object, str]

    def getattr(
        self,
        submission: t.Optional['Directory']=None,
        path: t.Optional[str]=None
    ) -> FullStat:
        if self.stat is None:
            self.stat = t.cast(
                FullStat, {
                    'st_mode':
                        S_IFDIR | create_permission(
                            read=True, write=self.writable, execute=True
                        ),
                    **super(Directory, self).getattr(submission, path),
                }
            )
            self.stat['st_nlink'] = 2

        self.stat['st_atime'] = time()
        return self.stat

    def insert(self, file: BaseFile) -> None:
        if self.stat is None:
            self.stat = self.getattr()

        self.children[file.name] = file
        self.stat['st_nlink'] += 1

    def pop(self, filename: str) -> BaseFile:
        assert self.stat is not None

        try:
            file = self.children.pop(filename)
        except KeyError:
            raise FuseOSError(ENOENT)
        self.stat['st_nlink'] -= 1

        return file

    def read(self) -> t.List[str]:
        res = list(self.children)
        res.extend(['.', '..'])
        return res


class TempDirectory(Directory):
    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        super(TempDirectory, self).__init__(*args, **kwargs)
        self.stat = {
            'st_uid': getuid(),
            'st_gid': getegid(),
            'st_atime': time(),
            'st_ctime': time(),
            'st_size': 0,
            'st_mtime': time(),
            'st_mode': S_IFDIR | create_permission(True, True, True),
            'st_nlink': 2,
        }  # type: FullStat


class SingleFile(BaseFile):
    stat = None  # type: t.Optional[FullStat]

    def base_getattr(
        self, submission: t.Optional['Directory']=None, path: str=None
    ) -> PartialStat:
        return super().getattr(submission, path)

    @abc.abstractclassmethod
    def getattr(
        self, submission: t.Optional['Directory']=None, path: str=None
    ) -> FullStat:
        raise NotImplementedError

    @abc.abstractmethod
    def open(self, buf: bytes) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def read(self, offset: int, size: int) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def truncate(self, length: int) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def release(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def utimens(self, atime: float, mtime: float) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, data: bytes, offset: int) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def fsync(self) -> t.Optional[t.Dict[str, t.Any]]:
        ...

    @abc.abstractmethod
    def flush(self) -> t.Optional[t.Dict[str, t.Any]]:
        ...


class SpecialFile(SingleFile):
    NAME = 'default special file'

    def __init__(self, name: str, data: bytes=b'') -> None:
        self.mode = create_permission(read=True, write=False, execute=True)
        self.name = name
        self.data = data

    def get_data(self) -> bytes:
        return self.data

    def getattr(self, *_: object) -> FullStat:
        return {
            'st_size': len(self.get_data()),
            'st_atime': self.get_st_atime(),
            'st_mtime': self.get_st_mtime(),
            'st_ctime': self.get_st_ctime(),
            'st_uid': getuid(),
            'st_gid': getegid(),
            'st_mode': S_IFREG | self.mode,
            'st_nlink': 1,
        }

    def get_st_atime(self) -> float:
        return time()

    def get_st_mtime(self) -> float:
        return time()

    def get_st_ctime(self) -> float:
        return time()

    def read(self, offset: int, size: int) -> bytes:
        return self.get_data()[offset:offset + size]

    def release(self) -> None:
        return

    def open(self, data: bytes) -> None:
        return

    def truncate(self, length: int) -> None:
        raise FuseOSError(EPERM)

    def unlink(self) -> None:
        raise FuseOSError(EPERM)

    def utimens(self, atime: float, mtime: float) -> None:
        return

    def write(self, data: bytes, offset: int) -> int:
        raise FuseOSError(EPERM)

    def flush(self) -> None:
        return

    def fsync(self) -> None:  # pragma: no cover
        return self.flush()


class SocketFile(SpecialFile):
    def __init__(self, loc: bytes, name: str) -> None:
        super(SocketFile, self).__init__(name=name)
        self.loc = loc

    def get_data(self) -> bytes:
        return self.loc


class HelpFile(SpecialFile):
    def __init__(self, from_class: t.Type[SpecialFile]) -> None:
        name = os.path.splitext(from_class.NAME)[0] + '.help'
        super(HelpFile, self).__init__(name=name)
        self.mode = create_permission(read=True, write=False, execute=True)
        self.from_class = from_class

    def get_data(self) -> bytes:
        return bytes(
            '\n'.join(
                [
                    l[4:] if l[:4] == ' ' * 4 else l
                    for l in (self.from_class.__doc__ or '').splitlines()
                ]
            ), 'utf8'
        )

    def flush(self) -> None:
        pass


class CachedSpecialFile(SpecialFile, t.Generic[T]):
    DELTA = datetime.timedelta(minutes=5)

    def __init__(self, name: str) -> None:
        super(CachedSpecialFile, self).__init__(name=name)
        self.has_data = False
        self.data = b''
        self.time = datetime.datetime.utcnow() - self.DELTA
        self.mtime = time()
        self.mode = create_permission(True, True, True)
        self.overwrite = False
        self.show_exception = True

    def get_st_mtime(self) -> float:
        return self.mtime

    def get_data(self) -> bytes:
        if self.has_data and (datetime.datetime.utcnow() -
                              self.time) < self.DELTA:
            return self.data
        elif self.overwrite:
            assert self.has_data
            return self.data

        data = self.get_online_data()
        if data != self.data:
            self.mtime = time() + 1

        self.time = datetime.datetime.utcnow()
        self.data = data
        self.has_data = True

        return self.data

    @abc.abstractmethod
    def get_online_data(self) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def parse(self, data: bytes) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def send_back(self, data: T) -> None:
        raise NotImplementedError

    def write(self, data: bytes, offset: int) -> int:
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

        self.has_data = True
        return len(self.data)

    def fsync(self) -> None:
        return self.flush()

    def reset_data(self) -> None:
        self.overwrite = False
        self.has_data = False
        self.data = self.get_data()

    def flush(self) -> None:
        if not self.overwrite:
            return

        if self.data.strip() == b'__RESET__':
            self.reset_data()
            return

        try:
            parsed = self.parse(self.data)
        except ValueError:
            raise FuseOSError(EPERM)

        try:
            self.send_back(parsed)
        except CGAPIException as e:
            logger.error(
                'error from server: {} ({})'.format(e.message, e.description)
            )
            handle_cgapi_exception(e)
        except:
            if self.show_exception:
                logger.critical(traceback.format_exc())
            self.show_exception = True
            raise

        self.overwrite = False
        self.has_data = False
        self.data = self.get_data()

    def truncate(self, length: int) -> None:
        self.data = self.get_data()

        if length == 0:
            self.data = bytes('', 'utf8')
        elif length <= len(self.data):
            self.data = self.data[:length]
        else:
            assert self.stat is not None
            self.data = self.data + bytes(
                '\0' * (length - self.stat['st_size']), 'utf8'
            )

        self.overwrite = True


class FeedbackFile(CachedSpecialFile):
    NAME = '.cg-feedback'

    def __init__(self, api: CGAPI, submission_id: int) -> None:
        self.api = api
        super(FeedbackFile, self).__init__(name=self.NAME)
        self.submission_id = submission_id

    def get_online_data(self) -> bytes:
        feedback = self.api.get_submission(self.submission_id)['comment']
        if not feedback:
            return b''
        return bytes(feedback, 'utf8')

    def parse(self, data: bytes) -> str:
        return data.decode('utf8')

    def send_back(self, feedback: bytes) -> None:
        self.api.set_submission(self.submission_id, feedback=feedback)


class GradeFile(CachedSpecialFile[t.Union[str, float]]):
    NAME = '.cg-grade'

    def __init__(self, api: CGAPI, submission_id: int) -> None:
        self.api = api
        self.grade = None  # type: t.Optional[float]
        super(GradeFile, self).__init__(name=self.NAME)
        self.submission_id = submission_id

    def get_online_data(self) -> bytes:
        grade = self.api.get_submission(self.submission_id)['grade']

        if grade is None:
            return b''

        self.grade = round(float(grade), 2)
        return bytes(str(self.grade) + '\n', 'utf8')

    def parse(self, data: bytes) -> t.Union[float, str]:
        data_str = data.decode('utf8')
        if not data_str.strip():
            return 'delete'

        data_list = [d for d in data_str.split('\n') if d]

        if len(data_list) != 1:
            raise ValueError

        return float(data_list[0])

    def send_back(self, grade: t.Union[str, float]) -> None:
        if grade != 'delete':
            assert not isinstance(grade, str)
            if round(grade, 2) == self.grade:
                return

            if grade < 0 or grade > 10:
                raise FuseOSError(EPERM)

        self.api.set_submission(self.submission_id, grade=grade)


class RubricSelectFile(CachedSpecialFile[t.List[str]]):
    NAME = '.cg-rubric.md'

    def __init__(self, api: CGAPI, submission_id: int, user: t.Dict) -> None:
        super(RubricSelectFile, self).__init__(name=self.NAME)
        self.submission_id = submission_id
        self.user = user
        self.lookup = {}  # type: t.Dict[int, str]
        self.api = api

    def get_online_data(self) -> bytes:
        res = []
        self.lookup = {}
        d = self.api.get_submission_rubric(self.submission_id)
        sel = set(i['id'] for i in d['selected'])
        l_num = 0
        if d['rubrics']:
            res.append('# The rubric of {}\n\n'.format(self.user['name']))
            l_num += 2
        else:
            res.append('# This assignment does not have a rubric!\n')
            l_num += 1

        for rub in d['rubrics']:
            res.append('## ')
            res.append(rub['header'])
            res.append('\n')
            l_num += 1

            if rub['description']:
                res.append('  ')
                res.append(rub['description'].replace('\n', '\n  '))
                res.append('\n')
                l_num += rub['description'].count('\n') + 1

            res.append('-' * 79)
            res.append('\n')

            l_num += 1

            rub['items'].sort(key=lambda i: i['points'])
            for item in rub['items']:
                self.lookup[l_num] = item['id']
                res.append('- [{}] '.format('x' if item['id'] in sel else ' '))
                res.append(item['header'].replace('\n', '\n  '))
                res.append(' ({}) - '.format(item['points']))
                res.append(item['description'].replace('\n', '\n  '))
                res.append('\n')

                l_num += item['header'].count('\n') + item['description'
                                                           ].count('\n') + 1

            res.append('\n')
            l_num += 1

        return bytes(''.join(res[:-1]), 'utf8')

    def parse(self, data: bytes) -> t.List[str]:
        sel = []

        for i, line in enumerate(data.split(b'\n')):
            if line.startswith(b'- [x]') or line.startswith(b'- [X]'):
                try:
                    sel.append(self.lookup[i])
                except KeyError:
                    logger.warning(
                        'Item on line {} ({}) not found!'.format(i, line)
                    )
                    raise FuseOSError(EPERM)

        return sel

    def send_back(self, sel: t.List[str]) -> None:
        self.api.select_rubricitems(self.submission_id, sel)


RubricItems = t.List[t.Tuple[t.Optional[str], float, str, str]]
RubricRow = t.Tuple[str, t.Optional[str], str, RubricItems]


class RubricEditorFile(CachedSpecialFile[t.List[RubricRow]]):
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

    def __init__(
        self, api: CGAPI, assignment_id: int, append_only: bool=True
    ) -> None:
        super(RubricEditorFile, self).__init__(name=self.NAME)
        self.api = api
        self.assignment_id = assignment_id
        self.append_only = append_only
        self.lookup = {}  # type: t.Dict[str, int]

    def hash_id(self, id: int) -> str:
        h = hashlib.sha256(bytes(id)).hexdigest()[:16]  # type: str
        self.lookup[h] = id
        return h

    def get_online_data(self) -> bytes:
        res = []
        self.lookup = {}

        for rub in self.api.get_assignment_rubric(self.assignment_id):
            res.append('# ')
            res.append('[{}] '.format(self.hash_id(rub['id'])))
            res.append(rub['header'])
            res.append('\n')

            if rub['description']:
                res.append('  ')
                res.append(rub['description'].replace('\n', '\n  '))
                res.append('\n')

            res.append('-' * 79)
            res.append('\n')

            rub['items'].sort(key=lambda i: i['points'])
            for item in rub['items']:
                res.append('- [{}] '.format(self.hash_id(item['id'])))
                res.append('({}) '.format(item['points']))
                res.append(item['header'].replace('\n', '\n  '))
                res.append(' - ')
                res.append(item['description'].replace('\n', '\n  '))
                res.append('\n')
            res.append('\n')

        if not res:
            return b''

        res.pop()
        return bytes(''.join(res), 'utf8')

    def parse(self, data_b: bytes) -> t.List[RubricRow]:
        i = 0

        def strip_spaces(i: int) -> int:
            try:
                while data[i] == ' ':
                    i += 1
            except IndexError:
                pass

            return i

        def parse_line(i: int) -> t.Tuple[str, int]:
            res = []

            try:
                while data[i] != '\n':
                    res.append(data[i])
                    i += 1
            except IndexError:
                pass

            return ''.join(res), i + 1

        def parse_description(
            i: int,
            end: t.Optional[t.List[str]]=None,
            strip_leading: bool=True,
            strip_trailing: bool=False,
        ) -> t.Tuple[str, int]:
            if end is None:
                end = ['-']
            lines = []
            while True:
                if any(data[i:].startswith(e) for e in end):
                    break

                if strip_leading:
                    i = strip_spaces(i)

                if i >= len(data):
                    break

                item, i = parse_line(i)
                lines.append(item)

            if strip_trailing:
                while lines and lines[-1].strip() == '':
                    lines.pop()
            return '\n'.join(lines), i

        def parse_list(i: int) -> t.Tuple[RubricItems, int]:
            items = []
            while i < len(data) and data[i] != '#':
                i = strip_spaces(i + 1)
                item_id = None  # type: t.Optional[str]
                if data[i] == '[':
                    i += 1
                    item_id_lst = []
                    while data[i] != ']':
                        item_id_lst.append(data[i])
                        i += 1
                    i = strip_spaces(i + 1)
                    item_id = ''.join(item_id_lst)

                assert data[i] == '('
                i += 1
                points_lst = []
                while data[i] != ')':
                    points_lst.append(data[i])
                    i += 1
                i = strip_spaces(i + 1)
                points = float(''.join(points_lst))

                header_lst = []
                while data[i] != '-':
                    header_lst.append(data[i])
                    if data[i] == '\n':
                        raise ParseException(
                            'Item header cannot contain a newline, you '
                            'probably missed a "-" in your header'
                        )
                    else:
                        i += 1

                i = strip_spaces(i + 1)
                header = ''.join(header_lst).strip()

                desc, i = parse_description(
                    i, end=['-', '#'], strip_trailing=True
                )

                items.append((item_id, points, header, desc))

            return items, i

        def parse_item(i: int) -> t.Tuple[RubricRow, int]:
            i = strip_spaces(i)
            item_id = None  # type: t.Optional[str]

            if data[i] == '[':
                h = []
                i += 1
                while data[i] != ']':
                    h.append(data[i])
                    i += 1
                i = strip_spaces(i + 1)

                item_id = ''.join(h)

            name, i = parse_line(i)
            desc, i = parse_description(i, end=['---'])

            while data[i] != '\n':
                i += 1

            items, i = parse_list(i + 1)
            return (name, item_id, desc, items), i

        try:
            items = []  # type: t.List[RubricRow]
            data = data_b.decode('utf8')
            while i < len(data):
                assert data[i] == '#'
                item, i = parse_item(i + 1)
                items.append(item)
            return items

        except (IndexError, KeyError, AssertionError, ParseException) as e:
            logger.debug(traceback.format_exc())
            if isinstance(e, ParseException):
                logger.warning(e.message)
            else:
                logger.warning('The rubric could not parsed!')
            raise FuseOSError(EPERM)

    def send_back(self, parsed: t.List[RubricRow]) -> None:
        res = []
        new_lookup = {k: v for k, v in self.lookup.items()}

        def get_from_lookup(h: str) -> int:
            try:
                res = new_lookup[h]
                if self.append_only:
                    del new_lookup[h]
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

        if self.append_only and new_lookup:
            self.show_exception = False
            logging.critical(
                'You cannot delete rubric items using the file system.'
            )
            raise FuseOSError(EPERM)

        self.lookup = new_lookup
        self.api.set_assignment_rubric(self.assignment_id, {'rows': res})


class AssignmentSettingsFile(CachedSpecialFile[t.Dict[str, str]]):
    TO_USE = {'state', 'deadline', 'name'}

    def __init__(self, api: CGAPI, assignment_id: int) -> None:
        super(AssignmentSettingsFile,
              self).__init__(name='.cg-assignment-settings.ini')
        self.assignment_id = assignment_id
        self.api = api

    def send_back(self, data: t.Dict[str, str]) -> None:
        self.api.set_assignment(self.assignment_id, data)

    def get_online_data(self) -> bytes:
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

    def parse(self, settings: bytes) -> t.Dict[str, str]:
        res = {}
        for line in settings.split(b'\n'):
            if not line:
                continue

            key, val = [v.decode('utf8').strip() for v in line.split(b'=', 1)]
            if key not in self.TO_USE:
                raise ValueError
            res[key] = val

        if len(self.TO_USE) != len(res):
            raise ValueError

        return res


class TempFile(SingleFile):
    def __init__(self, name: str, tmpdir: str) -> None:
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
    def stat(self) -> FullStat:  # type: ignore
        st = os.lstat(self.full_path)
        stat = {
            key: getattr(st, key)
            for key in (
                'st_atime', 'st_ctime', 'st_gid', 'st_mtime', 'st_nlink',
                'st_size', 'st_uid'
            )
        }
        stat['st_mode'] = S_IFREG | create_permission(True, True, True)
        return t.cast(FullStat, stat)

    def getattr(
        self,
        submission: t.Optional[Directory]=None,
        path: t.Optional[str]=None
    ) -> FullStat:
        return self.stat

    def setattr(self, key: str,
                value: t.Union[float, str]) -> None:  # pragma: no cover
        raise ValueError

    def utimens(self, atime: float, mtime: float) -> None:
        os.utime(self.full_path, (atime, mtime))

    def open(self, buf: bytes) -> None:
        assert not self._unlink

        if self._cnt == 0:
            self._handle = open(self.full_path, 'r+b')

        self._cnt += 1

    def read(self, offset: int, size: int) -> bytes:
        self._handle.seek(offset)
        return self._handle.read(size)

    def write(self, data: bytes, offset: int) -> int:
        self._handle.seek(offset)
        res = self._handle.write(data)
        self._handle.flush()
        return res

    def release(self) -> None:
        self._cnt -= 1
        if self._cnt == 0:
            self._handle.close()
            self._handle = None  # type: ignore

    def flush(self) -> None:
        return

    def fsync(self) -> None:  # pragma: no cover
        return self.flush()

    def unlink(self) -> None:
        self._unlink = True
        if self._cnt == 0:
            os.unlink(self.full_path)

    def truncate(self, length: int) -> None:
        if self._handle is None:
            os.truncate(self.full_path, length)
        else:
            self._handle.seek(0)
            self._handle.truncate(length)
            self._handle.flush()


class File(SingleFile):
    def __init__(self, data: t.Dict[str, t.Any],
                 name: t.Optional[str]=None) -> None:
        super(File, self).__init__(data, name)

        self._data = None  # type: t.Optional[bytes]
        self.dirty = False
        self.stat = None  # type: t.Optional[FullStat]

    @property
    def data(self) -> bytes:
        if self._data is None:
            assert cgapi is not None
            self._data = cgapi.get_file(self.id)
            assert self.stat is not None
            self.stat['st_size'] = len(self._data)
        return self._data

    @data.setter
    def data(self, data: t.Optional[bytes]) -> None:
        if data is not None:
            assert self.stat is not None
            self.stat['st_size'] = len(data)
        self._data = data

    def getattr(
        self,
        submission: t.Optional[Directory]=None,
        path: t.Optional[str]=None
    ) -> FullStat:
        if self.stat is None:
            self.stat = t.cast(FullStat, self.base_getattr(submission, path))
            self.stat['st_mode'] = S_IFREG | create_permission(
                True, True, True
            )
            self.stat['st_nlink'] = 1

        if self.stat['st_size'] is None:
            self.stat['st_size'] = len(self.data)
        return self.stat

    def open(self, buf: bytes) -> None:
        self.data = buf
        assert self.stat is not None
        self.stat['st_atime'] = time()

    def read(self, offset: int, size: int) -> bytes:
        return self.data[offset:offset + size]

    def utimens(self, atime: float, mtime: float) -> None:
        self.setattr('st_atime', atime)
        self.setattr('st_mtime', mtime)

    def flush(self) -> t.Optional[t.Dict[str, t.Any]]:
        if not self.dirty:
            return None

        assert self._data is not None
        assert cgapi is not None

        try:
            res = cgapi.patch_file(self.id, self._data)
        except CGAPIException as e:
            # This is valid as we use a setter
            self.data = None  # type: ignore
            self.dirty = False
            handle_cgapi_exception(e)

        self.dirty = False
        return res

    def release(self) -> None:
        # This is valid as we use a setter
        self.data = None  # type: ignore

    def truncate(self, length: int) -> None:
        old_data = self.data

        if length == 0:
            self.data = bytes('', 'utf8')
        elif length <= len(old_data):
            self.data = self.data[:length]
        else:
            self.data = old_data + bytes(
                '\0' * (length - len(old_data)), 'utf8'
            )
        assert self.stat is not None

        self.stat['st_atime'] = time()
        self.stat['st_mtime'] = time()
        self.dirty = True

    def write(self, data: bytes, offset: int) -> int:
        old_data = self.data

        if offset > len(old_data):
            assert self._data is not None
            self._data += bytes(offset - len(old_data))

        if len(old_data) - offset - len(data) > 0:
            # Write in between
            second_offset = offset + len(data)
            self.data = old_data[:offset] + data + old_data[second_offset:]
        elif offset == 0:
            self.data = data
        else:
            self.data = self.data[:offset] + data

        assert self.stat is not None
        self.stat['st_atime'] = time()
        self.stat['st_mtime'] = time()
        self.dirty = True
        return len(data)

    def fsync(self) -> t.Optional[t.Dict[str, t.Any]]:
        return self.flush()


class APIHandler:
    ReceiveHandler = t.Callable[[t.Dict[str, t.Any]], APIHandlerResponse]

    def __init__(self, cgfs: 'CGFS') -> None:
        self.ops = {
            'set_feedback': self.set_feedback,
            'get_feedback': self.get_feedback,
            'delete_feedback': self.delete_feedback,
            'is_file': self.is_file,
        }  # type: t.Dict[str, APIHandler.ReceiveHandler]
        self.cgfs = cgfs
        self.stop = False

    def handle_conn(self, conn: socket.socket) -> None:
        data = b''
        while True:
            new_data = conn.recv(1024)
            data += new_data
            if len(new_data) < 1024:
                break

        if not data:
            return

        with self.cgfs._lock:
            data_dict = json.loads(data.decode())
            op = data_dict['op']
            if op not in self.ops:
                conn.send(b'{"ok": false, "error": "unkown op"}')
            del data_dict['op']
            payload = data_dict
            try:
                res = self.ops[op](payload)
                conn.send(bytes(json.dumps(res).encode('utf8')))
            except:
                logger.debug(traceback.format_exc())
                conn.send(b'{"ok": false, "error": "Unkown error"}')

    def run(self, sock: socket.socket) -> None:
        sock.settimeout(1.0)

        while not self.stop:
            try:
                conn, addr = sock.accept()
            except:
                continue

            try:
                conn.settimeout(1.0)
                self.handle_conn(conn)
            finally:
                conn.close()

    def _get_file(self,
                  f_name: str) -> t.Union[APIHandlerResponse, SingleFile]:
        f_name = self.cgfs.strippath(f_name)

        if sys.platform.startswith('win32'):
            ffi = cffi.FFI()
            in_str = ffi.new('wchar_t[]', f_name)
            out_str = ffi.new('char **')
            if winfspy.lib.FspPosixMapWindowsToPosixPathEx(
                in_str, out_str, True
            ) != 0:
                return {'ok': False, 'error': 'Winfspy returned an error'}
            f_name = ffi.string(out_str[0]).decode('utf-8')
            winfspy.lib.FspPosixDeletePath(out_str[0])
        try:
            return self.cgfs.get_file(f_name, expect_type=SingleFile)
        except:
            return {'ok': False, 'error': 'File ({}) not found'.format(f_name)}

    def delete_feedback(self,
                        payload: t.Dict[str, t.Any]) -> APIHandlerResponse:
        f_name = self.cgfs.strippath(payload['file'])
        line = payload['line']
        assert cgapi is not None

        with self.cgfs._lock:
            f = self._get_file(payload['file'])
            if not isinstance(f, SingleFile):
                return f

            try:
                cgapi.delete_feedback(f.id, line)
            except:
                return {'ok': False, 'error': 'The server returned an error'}

            return {'ok': True}

    def is_file(self, payload: t.Dict[str, t.Any]) -> APIHandlerResponse:
        f_name = self.cgfs.strippath(payload['file'])

        if sys.platform.startswith('win32'):
            file_parts = []  # type: t.List[str]
            while f_name:
                new_f_name, part = os.path.split(f_name)
                file_parts.append(part)
                if new_f_name == f_name:
                    break
                f_name = new_f_name
            file_parts.reverse()
        else:
            file_parts = self.cgfs.split_path(f_name)

        with self.cgfs._lock:
            f = self._get_file(payload['file'])
            if not isinstance(f, SingleFile):
                return f

            return {'ok': isinstance(f, File)}

    def get_feedback(self, payload: t.Dict[str, t.Any]) -> APIHandlerResponse:
        assert cgapi is not None

        with self.cgfs._lock:
            f = self._get_file(payload['file'])
            if not isinstance(f, SingleFile):
                return f

            if not isinstance(f, File):
                return {'ok': False, 'error': 'File not a sever file'}

            try:
                res = cgapi.get_feedback(f.id)
            except:
                return {'ok': False, 'error': 'The server returned an error'}

            return {'ok': True, 'data': res}

    def set_feedback(self, payload: t.Dict[str, t.Any]) -> APIHandlerResponse:
        line = payload['line']
        message = payload['message']

        with self.cgfs._lock:
            f = self._get_file(payload['file'])
            if not isinstance(f, SingleFile):
                return f

            if not isinstance(f, File):
                return {
                    'ok': False,
                    'error': 'File not found or not a server file'
                }

            assert cgapi is not None
            try:
                cgapi.add_feedback(f.id, line, message)
            except:
                return {'ok': False, 'error': 'The server returned an error'}

            return {'ok': True}


FileHandle = t.NewType('FileHandle', int)
OptFileHandle = t.Optional[FileHandle]


class CGFS(LoggingMixIn, Operations):
    API_FD = 0

    def init(self, path: str) -> None:
        global fuse_ptr
        fuse_ptr = ctypes.c_void_p(
            fuse._libfuse.fuse_get_context().contents.fuse
        )

    def __init__(
        self,
        latest_only: bool,
        socketfile: str,
        mountpoint: str,
        tmpdir: str,
        fixed: bool=False,
        rubric_append_only: bool=True,
        assigned_only: bool=False,
    ) -> None:
        self.latest_only = latest_only
        self.fixed = fixed
        self.fd = FileHandle(1)
        self.mountpoint = mountpoint
        self._lock = threading.RLock()
        self._open_files = {}  # type: t.Dict[FileHandle, SingleFile]
        self.assigned_only = assigned_only

        self._tmpdir = tmpdir

        if sys.platform.startswith('win32'):
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('localhost', 0))
            socketfile = str(self.socket.getsockname()[1])
        else:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.bind(socketfile)

        # Typeshed bug: https://github.com/python/typeshed/issues/2526
        self.socket.listen()  # type: ignore
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
        logger.info('Mounted')

    def strippath(self, path: str) -> str:
        path = os.path.abspath(path)
        return path[len(self.mountpoint):]

    def load_courses(self) -> None:
        assert cgapi is not None

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
            course_dir.children_loaded = True
        self.files.children_loaded = True

    def load_submissions(self, assignment: Directory) -> None:
        assert cgapi is not None

        try:
            submissions = cgapi.get_submissions(assignment.id)
        except CGAPIException as e:  # pragma: no cover
            handle_cgapi_exception(e)

        def get_assignee_id(sub):
            if isinstance(sub['assignee'], dict):
                return sub['assignee']['id']
            return None

        seen = set()  # type: t.Set[int]
        my_id = cgapi.user['id']
        user_assigned = self.assigned_only and any(
            get_assignee_id(s) == my_id for s in submissions
        )

        for sub in submissions:
            if sub['user']['id'] in seen:
                continue
            elif user_assigned and my_id not in {
                get_assignee_id(sub),
                sub['user']['id'],
            }:
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
            sub_dir.insert(RubricSelectFile(cgapi, sub['id'], sub['user']))
            sub_dir.insert(GradeFile(cgapi, sub['id']))
            sub_dir.insert(FeedbackFile(cgapi, sub['id']))
            assignment.insert(sub_dir)

        assignment.children_loaded = True

    def insert_tree(self, dir: Directory, tree: t.Dict[str, t.Any]):
        for item in tree['entries']:
            if 'entries' in item:
                new_dir = Directory(item, writable=True)
                new_dir.getattr()
                dir.insert(new_dir)
                self.insert_tree(new_dir, item)
            else:
                dir.insert(File(item))
        dir.children_loaded = True

    def load_submission_files(self, submission: Directory) -> None:
        assert cgapi is not None

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
        submission.children_loaded = True

    def split_path(self, path: str) -> t.List[str]:
        return [x for x in path.split('/') if x]

    def get_submission(self, path: str) -> Directory:
        parts = self.split_path(path)
        submission = self.get_file(parts[:3], expect_type=Directory)
        if submission.tld is NOT_PRESENT:
            self.load_submission_files(submission)

        return submission

    def get_file_with_fh(self, path: str, fh: OptFileHandle) -> SingleFile:
        if fh is None:
            return self.get_file(path, expect_type=SingleFile)
        else:
            return self._open_files[fh]

    def get_file(
        self,
        path: t.Union[str, t.List[str]],
        start: t.Optional[Directory]=None,
        expect_type: t.Type[T]=None
    ) -> T:
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
            file = file.children[part]  # type: ignore

        if expect_type is not None:
            if not isinstance(file, expect_type):
                raise FuseOSError(EISDIR)

        return t.cast(T, file)

    def get_dir(
        self,
        path: t.Union[str, t.List[str]],
        start: t.Optional[Directory]=None
    ) -> Directory:
        return self.get_file(path, start=start, expect_type=Directory)

    def chmod(self, path: str, mode: int) -> None:
        raise FuseOSError(EPERM)

    def chown(self, path: str, uid: int, gid: int) -> None:
        raise FuseOSError(EPERM)

    def create(self, path: str, mode: int) -> FileHandle:
        with self._lock:
            return self._create(path, mode)

    def _create(self, path: str, mode: int) -> FileHandle:
        parts = self.split_path(path)
        if len(parts) <= 3:
            raise FuseOSError(EPERM)

        parent = self.get_dir(parts[:-1])
        fname = parts[-1]

        assert fname not in parent.children

        submission = self.get_submission(path)
        assert isinstance(submission.tld, str)

        query_path = submission.tld + '/' + '/'.join(parts[3:])

        assert cgapi is not None

        if self.fixed:
            file = TempFile(fname, self._tmpdir)  # type: SingleFile
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

        self.fd = FileHandle(self.fd + 1)
        self._open_files[self.fd] = file

        return self.fd

    def fsync(self, path: str, _: object, fh: OptFileHandle) -> None:
        self._do_fsync_like(path, fh, FsyncLike.fsync)

    def flush(self, path: str, fh: OptFileHandle) -> None:
        self._do_fsync_like(path, fh, FsyncLike.flush)

    def _do_fsync_like(
        self, path: str, fh: OptFileHandle, todo: FsyncLike
    ) -> None:
        with self._lock:
            file = self.get_file_with_fh(path, fh)

            if todo == FsyncLike.fsync:
                res = file.fsync()
            elif todo == FsyncLike.flush:
                res = file.flush()
            else:
                assert False

            if res is not None:
                file.id = res['id']

    def getattr(self, path: str, fh: OptFileHandle=None) -> FullStat:
        with self._lock:
            return self._getattr(path, fh)

    def _getattr(self, path: str, fh: OptFileHandle) -> FullStat:
        if fh is None or fh not in self._open_files:
            parts = self.split_path(path)
            file = self.get_file(parts)  # type: t.Union[Directory, SingleFile]
        else:
            file = self._open_files[fh]

        if isinstance(file, (TempFile, SpecialFile)):
            return file.getattr()

        submission = None  # type: t.Optional[Directory]
        query_path = None  # type: t.Optional[str]

        if file.stat is None and len(parts) > 3:
            try:
                submission = self.get_submission(path)
            except CGAPIException as e:
                handle_cgapi_exception(e)

            assert isinstance(submission.tld, str)
            query_path = submission.tld + '/' + '/'.join(parts[3:])

            if isinstance(file, Directory):
                query_path += '/'
        else:
            submission = None
            query_path = None

        attrs = file.getattr(submission, query_path)  # type: FullStat
        if self.fixed and isinstance(file, File):
            attrs['st_mode'] = remove_permission(attrs['st_mode'], write=True)
        return attrs

    # TODO?: Add xattr support
    def getxattr(self, path: str, name: str, position: int=0) -> None:
        raise FuseOSError(ENOTSUP)

    # TODO?: Add xattr support
    def listxattr(self, path: str) -> None:  # pragma: no cover
        raise FuseOSError(ENOTSUP)

    def mkdir(self, path: str, mode: int) -> None:
        with self._lock:
            return self._mkdir(path, mode)

    def _mkdir(self, path: str, mode: int) -> None:
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])
        dname = parts[-1]

        # Fuse should handle this but better safe than sorry
        if dname in parent.children:  # pragma: no cover
            raise FuseOSError(EEXIST)

        if self.fixed:
            parent.insert(TempDirectory({}, name=dname, writable=True))
        else:
            assert cgapi is not None

            submission = self.get_submission(path)
            assert isinstance(submission.tld, str)

            query_path = submission.tld + '/' + '/'.join(parts[3:]) + '/'
            ddata = cgapi.create_file(submission.id, query_path)

            parent.insert(Directory(ddata, name=dname, writable=True))

    def open(self, path: str, flags: int) -> FileHandle:
        with self._lock:
            return self._open(path, flags)

    def _open(self, path: str, flags: int) -> FileHandle:
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])

        file = self.get_file(parts[-1], start=parent, expect_type=SingleFile)

        if isinstance(file, (TempFile, SpecialFile)):
            file.open(b'')

        # This is handled by fuse [0] but it can be disabled so it is better to
        # be safe than sorry as it can be enabled.
        # [0] https://sourceforge.net/p/fuse/mailman/message/29515577/
        if flags & O_TRUNC:  # pragma: no cover
            file.truncate(0)

        self.fd = FileHandle(self.fd + 1)
        self._open_files[self.fd] = file
        return self.fd

    def read(self, path: str, size: int, offset: int, fh: FileHandle) -> bytes:
        with self._lock:
            file = self._open_files[fh]
            return file.read(offset, size)

    def readdir(self, path: str, fh: OptFileHandle) -> t.List[str]:
        with self._lock:
            dir = self.get_dir(path)

            if not dir.children_loaded:
                if dir.type == DirTypes.ASSIGNMENT:
                    self.load_submissions(dir)
                elif dir.type == DirTypes.SUBMISSION:
                    self.load_submission_files(dir)

            return dir.read()

    def readlink(self, path: str) -> None:
        raise FuseOSError(EINVAL)

    def release(self, path: str, fh: FileHandle) -> None:
        with self._lock:
            file = self._open_files[fh]
            file.release()
            del self._open_files[fh]

    # TODO?: Add xattr support
    def removexattr(self, path: str, name: str) -> None:
        raise FuseOSError(ENOTSUP)

    def rename(self, old: str, new: str) -> None:
        with self._lock:
            return self._rename(old, new)

    def _rename(self, old: str, new: str) -> None:
        old_parts = self.split_path(old)
        old_parent = self.get_dir(old_parts[:-1])
        file = self.get_file(old_parts[-1], start=old_parent)  # type: BaseFile

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

        assert isinstance(submission.tld, str)
        new_query_path = submission.tld + '/' + '/'.join(new_parts[3:]) + '/'

        if not isinstance(file, (TempDirectory, TempFile)):
            if self.fixed:
                raise FuseOSError(EPERM)

            assert cgapi is not None
            try:
                res = cgapi.rename_file(file.id, new_query_path)
            except CGAPIException as e:
                handle_cgapi_exception(e)

            file.id = res['id']
        file.name = new_parts[-1]

        old_parent.pop(old_parts[-1])
        new_parent.insert(file)

    def rmdir(self, path: str) -> None:
        with self._lock:
            return self._rmdir(path)

    def _rmdir(self, path: str) -> None:
        parts = self.split_path(path)
        parent = self.get_dir(parts[:-1])
        dir = self.get_file(parts[-1], start=parent, expect_type=Directory)

        if dir.type != DirTypes.REGDIR:
            raise FuseOSError(EPERM)
        if dir.children:
            raise FuseOSError(ENOTEMPTY)

        if not isinstance(dir, TempDirectory):
            if self.fixed:
                raise FuseOSError(EPERM)

            assert cgapi is not None
            try:
                cgapi.delete_file(dir.id)
            except CGAPIException as e:
                handle_cgapi_exception(e)

        parent.pop(parts[-1])

    # TODO?: Add xattr support
    def setxattr(
        self,
        path: str,
        name: str,
        value: object,
        options: object,
        position: int=0
    ) -> None:  # pragma: no cover
        raise FuseOSError(ENOTSUP)

    def statfs(self, path: str) -> t.Dict[str, int]:
        return {
            'f_bsize': 512,
            'f_blocks': 4096,
            'f_bavail': 2048,
        }

    def symlink(self, target: str, source: str) -> None:
        raise FuseOSError(EPERM)

    def truncate(self, path: str, length: int, fh: OptFileHandle=None) -> None:
        with self._lock:
            if length < 0:  # pragma: no cover
                raise FuseOSError(EINVAL)

            file = self.get_file_with_fh(path, fh)

            if self.fixed and not isinstance(file, (TempFile, SpecialFile)):
                raise FuseOSError(EPERM)

            file.truncate(length)

    def unlink(self, path: str) -> None:
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

                assert cgapi is not None
                try:
                    cgapi.delete_file(file.id)
                except CGAPIException as e:
                    handle_cgapi_exception(e)

            parent.pop(fname)

    def utimens(self, path: str, times: t.Tuple[float, float]=None) -> None:
        with self._lock:
            file = self.get_file(path, expect_type=SingleFile)
            assert file is not None
            atime, mtime = times or (time(), time())

            if isinstance(file, File) and self.fixed:
                raise FuseOSError(EPERM)

            file.utimens(atime, mtime)

    def write(
        self, path: str, data: bytes, offset: int, fh: FileHandle
    ) -> int:
        with self._lock:
            file = self._open_files[fh]

            if self.fixed and not isinstance(file, (TempFile, SpecialFile)):
                raise FuseOSError(EPERM)

            return file.write(data, offset)


def create_and_mount_fs(
    username: str,
    password: str,
    url: t.Optional[str],
    fixed: bool,
    assigned_only: bool,
    latest_only: bool,
    mountpoint: str,
    rubric_append_only: bool,
) -> None:
    global cgapi
    logger.info('Mounting... ')

    try:
        cgapi = CGAPI(
            username,
            password,
            url,
            fixed=fixed,
        )
    except:
        logger.critical('Logging in failed:')
        logger.critical(traceback.format_exc())
        raise

    if not fixed:
        logger.warning('=====================================================')
        logger.warning('Mounting in non-fixed mode, all changes will be')
        logger.warning('visible and additions to students.')
        logger.warning('Watch out when uploading grading scripts!')
        logger.warning('=====================================================')

    with tempfile.TemporaryDirectory(dir=tempfile.gettempdir()) as tmpdir:
        sockfile = tempfile.NamedTemporaryFile().name
        kwargs = {}  # type: t.Dict[str, str]
        if sys.platform.startswith('win32'):
            # Force gid and uid to correct current user values:
            # https://github.com/billziss-gh/winfsp/issues/79#issuecomment-292806979
            kwargs = {
                'uid': '-1',
                'gid': '-1',
            }
        elif sys.platform.startswith('darwin'):
            # Fix OSX encoding issue as described here:
            # https://web.archive.org/web/20180920131107/https://github.com/osxfuse/osxfuse/issues/71
            kwargs = {
                'from_code': 'UTF-8',
                'to_code': 'UTF-8-MAC',
                'modules': 'iconv',
            }

        fs = None
        try:
            fs = CGFS(
                latest_only=latest_only,
                socketfile=sockfile,
                fixed=fixed,
                mountpoint=mountpoint,
                tmpdir=tmpdir,
                rubric_append_only=rubric_append_only,
                assigned_only=assigned_only,
            )
            FUSE(
                fs,
                mountpoint,
                nothreads=True,
                foreground=True,
                direct_io=True,
                **kwargs,
            )
        except RuntimeError:  # pragma: no cover
            logger.critical(traceback.format_exc())
        finally:
            if fs is not None and hasattr(fs, 'api_handler'):
                fs.api_handler.stop = True
            if os.path.isfile(sockfile):
                os.unlink(sockfile)


def check_version() -> None:
    if codegra_fs.utils.newer_version_available():
        msg = [
            (
                'You are running an outdated version of'
                ' CGFS, please consider upgrading.'
            ),
            'You can do this at https://codegra.de/codegra_fs/latest/',
        ]
        print('-' * (max(len(l) for l in msg) + 4), file=sys.stderr)
        for line in msg:
            print('| {} |'.format(line), file=sys.stderr)
        print('-' * (max(len(l) for l in msg) + 4), file=sys.stderr)


def main() -> None:
    global cgapi

    msg = codegra_fs.utils.get_fuse_install_message()
    if msg:
        err, url = msg
        print('ERROR!')
        print(msg, file=sys.stderr)
        if url:
            print('You can download it here: {}'.format(url))
        sys.exit(2)

    check_version()

    argparser = ArgumentParser(
        description='CodeGra.fs: The CodeGrade file system',
        epilog=constants.cgfs_epilog,
        formatter_class=RawDescriptionHelpFormatter,
    )
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
        help=constants.mountpoint_help,
    )
    argparser.add_argument(
        '-p',
        '--password',
        metavar='PASSWORD',
        type=str,
        dest='password',
        help=constants.password_help,
    )
    argparser.add_argument(
        '-u',
        '--url',
        metavar='URL',
        type=str,
        dest='url',
        help=constants.url_help
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
        '-a',
        '--all-submissions',
        dest='latest_only',
        action='store_false',
        default=True,
        help=constants.all_submissions_help,
    )
    argparser.add_argument(
        '-f',
        '--fixed',
        dest='fixed',
        action='store_true',
        default=False,
        help=constants.fixed_mode_help,
    )
    argparser.add_argument(
        '-q',
        '--quiet',
        dest='quiet',
        action='store_true',
        default=False,
        help="""Only output error messages.""",
    )
    argparser.add_argument(
        '-r',
        '--rubric-edit',
        dest='rubric_append_only',
        action='store_false',
        default=True,
        help=constants.rubric_edit_help,
    )
    argparser.add_argument(
        '-m',
        '--assigned-to-me',
        dest='assigned_only',
        default=False,
        action='store_true',
        help=constants.assigned_only_help,
    )
    argparser.add_argument(
        '--version',
        dest='version',
        action='version',
        version=(
            '%(prog)s {}'.format('.'.join(map(str, codegra_fs.__version__)))
        ),
        help='Display version.',
    )
    args = argparser.parse_args()

    mountpoint = os.path.abspath(args.mountpoint)
    username = args.username

    password = args.password
    if password is None and not sys.stdin.isatty():
        print('Password:', end=' ')
        password = sys.stdin.readline()
        if len(password) and password[-1] == '\n':
            password = password[:-1]
        if not password:
            password = None
    if password is None:
        password = getenv('CGFS_PASSWORD')
    if password is None:
        password = getpass('Password: ')

    latest_only = args.latest_only
    rubric_append_only = args.rubric_append_only
    fixed = args.fixed
    assigned_only = args.assigned_only

    if args.quiet:
        logging.basicConfig(level=logging.WARNING)
    elif args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    create_and_mount_fs(
        username=username,
        password=password,
        url=args.url or getenv('CGAPI_BASE_URL', None),
        fixed=fixed,
        assigned_only=assigned_only,
        latest_only=latest_only,
        mountpoint=mountpoint,
        rubric_append_only=rubric_append_only,
    )


if __name__ == '__main__':
    main()
