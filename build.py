#!/usr/bin/env python3

import os
import sys
import subprocess

if sys.platform.startswith('win32'):
    os.chdir(os.path.dirname(__file__))
    subprocess.check_call(
        [
            'pyinstaller',
            os.path.join('codegra_fs', 'gui.py'),
            '--onefile',
            '--icon',
            os.path.join('static', 'ms-icon.ico'),
            '--noconsole',
        ]
    )
    subprocess.check_call(
        [
            'pyinstaller',
            os.path.join('codegra_fs', 'api_consumer.py'),
            '--onedir',
            '--name',
            'cgapi-consumer',
        ]
    )
    subprocess.check_call(
        [
            os.path.join(
                'C:\\',
                'Program Files (x86)',
                'NSIS',
                'makensis.exe',
            ),
            'installer.nsi',
        ]
    )
elif sys.platform.startswith('linux'):
    subprocess.check_call(['python3', 'sdist', 'bdist_wheel'])
    print("""You can now upload this dist to pypi using:

    `twine upload dist/*`
    """)
else:
    print('Your platform cannot build cgfs yet')
