#!/usr/bin/env python3

import sys
from distutils.core import setup

version = '0.1.0'

if sys.version_info < (3, 5):
    print('Sorry only python 3.5 and up is supported', file=sys.stderr)
    sys.exit(1)

setup(
    name='CodeGra.fs',
    author='The CodeGra.de team',
    author_email='info@codegra.de',
    version=version,
    description='File-system for CodeGra.de instances',
    long_description=open('README.md').read(),
    install_requires=['requests>=2.18.4', 'fusepy>=2.0.4'],
    packages=['codegra_fs'],
    entry_points={
        'console_scripts':
            [
                'cgfs = codegra_fs.cgfs:main',
                'cgapi-consumer = codegra_fs.api_consumer:main'
            ]
    }
)
