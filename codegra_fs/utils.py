# SPDX-License-Identifier: AGPL-3.0-only
import re
import sys
import typing as t
import datetime
from collections import defaultdict

import requests
import codegra_fs

T = t.TypeVar('T')
Y = t.TypeVar('Y')


def _get_fuse_version_info() -> t.Tuple[int, int]:
    if not sys.platform.startswith('win32'):
        return (-1, -1)

    import cffi  # type: ignore
    import winfspy.plumbing  # type: ignore
    ffi = cffi.FFI()
    res = ffi.new('unsigned int *')
    if winfspy.plumbing.lib.FspVersion(res) != 0:
        return (0, 0)
    return ((res[0] >> 16) & 0xffff, res[0] & 0xffff)


def get_fuse_install_message() -> t.Optional[t.Tuple[str, t.Optional[str]]]:
    try:
        import fuse  # type: ignore
    except:
        pass
    else:
        if sys.platform.startswith('win32'):
            winfsp_version = _get_fuse_version_info()
            if winfsp_version < (1, 4):
                return (
                    'You need at least WinFsp version 1.4.',
                    'https://github.com/billziss-gh/winfsp/releases'
                )
        return None

    if sys.platform.startswith('darwin'):
        return (
            'Fuse is not installed, this can be done by installing OSXFuse',
            'https://osxfuse.github.io/'
        )
    elif sys.platform.startswith('linux'):
        return (
            'Fuse is not installed, this can be done by doing `sudo apt install fuse` on ubuntu',
            None
        )
    elif sys.platform.startswith('win32'):
        return (
            'WinFsp not installed, please download version 1.4 (currently in beta) or later.',
            'https://github.com/billziss-gh/winfsp/releases'
        )
    else:
        return (
            'Unsupported platform, only GNU/Linux, Mac and Windows are supported',
            None
        )


def newer_version_available() -> bool:
    try:
        req = requests.get('https://fs.codegrade.com/.cgfs.json', timeout=2)
        req.raise_for_status()
        latest = tuple(map(int, req.json()['version']))
    except:
        return False
    return latest > codegra_fs.__version__


def find_all_dups(
    seq: t.Sequence[T],
    key: t.Callable[[T], Y],
) -> t.List[t.Tuple[T, ...]]:
    dct = defaultdict(list)  # type: t.MutableMapping[Y, t.List[T]]
    for el in seq:
        dct[key(el)].append(el)
    return [tuple(v) for v in dct.values() if len(v) > 1]


def name_of_user(user: t.Dict[str, t.Any]) -> str:
    if user.get('group') is None:
        return user['name']
    else:
        return 'Group "{}"'.format(user['group']['name'])


def get_members_of_user(user: t.Dict[str, t.Any]) -> t.List[str]:
    if user.get('group') is None:
        return [user['name']]
    return [member['name'] for member in user['group']['members']]


def format_datestring(datestring: str, use_colons: bool) -> str:
    datestring = datestring.replace('T', ' ').split('.')[0]
    if use_colons:
        return datestring
    d = datetime.datetime.strptime(datestring, '%Y-%m-%d %H:%M:%S')
    return '{0:%Y}-{0:%m}-{0:%d} {0:%H}h {0:%M}m {0:%S}s'.format(d)


def maybe_strip_trailing_newline(s: str) -> str:
    if s and s[-1] == '\n':
        s = s[:-1]
    return s


_WINDOWS_ILLEGAL_CHARS_RE = re.compile(r'[<>:"/\\|\?\*]')


def remove_special_chars(s: str) -> str:
    """Remove special characters from ...
    """
    s = s.encode('ascii', 'replace').decode('ascii')
    if re.search(_WINDOWS_ILLEGAL_CHARS_RE, s):
        return re.sub(_WINDOWS_ILLEGAL_CHARS_RE, '-', s)
    return s
