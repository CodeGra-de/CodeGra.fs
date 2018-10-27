#!/usr/bin/env python3

import sys

import codegra_fs
from setuptools import setup

version = '.'.join(map(str, codegra_fs.__version__))

if sys.version_info < (3, 5):
    print('Sorry only python 3.5 and up is supported', file=sys.stderr)
    sys.exit(1)

requires = [
    'requests>=2.18.4', 'fusepy>3.0.0,<4.0.0', 'PyQt5==5.11.3,<6.0.0',
    'appdirs>=1.4.3,<2.0.0'
]
if sys.platform.startswith('win32'):
    requires += [
        'winfspy >= 0.2.0',
        'cffi >= 1.0.0',
    ]

setup(
    name='CodeGra.fs',
    author='The CodeGrade team',
    author_email='info@codegra.de',
    version=version,
    description='File-system for CodeGrade instances',
    install_requires=requires,
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    packages=['codegra_fs'],
    entry_points={
        'console_scripts':
            [
                'cgfs = codegra_fs.cgfs:main',
                'cgapi-consumer = codegra_fs.api_consumer:main',
                'cgfs-qt = codegra_fs.gui:main',
            ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
    ],
)
