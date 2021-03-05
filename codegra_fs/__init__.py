# SPDX-License-Identifier: AGPL-3.0-only

import sys
import typing as t

import pkg_resources
import packaging.version

if t.TYPE_CHECKING:
    from typing_extensions import Final, Literal

__version__ = 'UNKNOWN'  # type: t.Union['Literal["UNKNOWN"]', packaging.version.Version]
try:
    __version__ = packaging.version.Version(
        pkg_resources.get_distribution('codegrade-fs').version
    )
except:
    import traceback
    print('Could not read version:', file=sys.stderr)
    traceback.print_exc()
finally:
    del pkg_resources

__author__ = 'Olmo Kramer, Thomas Schaper'
__email__ = 'info@CodeGra.de'
__license__ = 'AGPL-3.0-only'
__maintainer__ = 'CodeGrade'

import codegra_fs.utils as utils
