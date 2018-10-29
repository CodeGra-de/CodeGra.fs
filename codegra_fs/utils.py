# SPDX-License-Identifier: AGPL-3.0-only
import sys
import typing as t

import requests
import codegra_fs


def _get_fuse_version_info() -> t.Tuple[int, int]:
    if not sys.platform.startswith('win32'):
        return (-1, -1)

    import winfspy  # type: ignore
    import cffi  # type: ignore
    ffi = cffi.FFI()
    res = ffi.new('unsigned int *')
    if winfspy.lib.FspVersion(res) != 0:
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
                return 'You need at least WinFsp version 1.4 (currently in beta).', 'https://github.com/billziss-gh/winfsp/releases'
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
    req = requests.get('https://codegra.de/.cgfs.version', timeout=2)
    return req.status_code < 300 and tuple(
        int(p) for p in req.content.decode('utf8').strip().split('.')
    ) > codegra_fs.__version__
