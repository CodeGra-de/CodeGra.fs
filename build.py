#!/usr/bin/env python3

import os
import sys
import subprocess

import requests

from codegra_fs import __version__

os.chdir(os.path.dirname(__file__))


def pyinstaller(module, name):
    if sys.platform == 'darwin':
        icon = os.path.join('static', 'icons', 'icon.icns')
    else:
        icon = os.path.join('static', 'icons', 'ms-icon.ico')

    subprocess.check_call(
        [
            'pyinstaller',
            '--noconfirm',
            '--onedir',
            '--specpath',
            'dist',
            '--name',
            name,
            '--icon',
            icon,
            module,
        ],
    )


def run_pyinstaller():
    pyinstaller(os.path.join('codegra_fs', 'cgfs.py'), 'cgfs')
    pyinstaller(os.path.join('codegra_fs', 'api_consumer.py'), 'cgapi-consumer')


def npm(job):
    subprocess.check_call(
        [
            'npm',
            'run',
            job,
        ],
        shell=True,
    )


if sys.platform.startswith('win32'):
    run_pyinstaller()

    url = 'https://github.com/billziss-gh/winfsp/releases/download/v1.4.19049/winfsp-1.4.19049.msi'
    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()
    open('dist/winfsp.msi', 'wb').write(r.content)


    npm('build:win')
elif sys.platform.startswith('linux'):
    subprocess.check_call(['python3', 'sdist', 'bdist_wheel'])

    print(
        """You can now upload this dist to pypi using:

    `twine upload dist/*`
    """
    )
elif sys.platform.startswith('darwin'):
    run_pyinstaller()

    npm('build:mac')

    subprocess.check_call(
        [
            'pkgbuild',
            '--root',
            'dist/mac',
            '--install-location',
            '/Applications',
            '--component-plist',
            'build/com.codegrade.codegrade-fs.plist',
            '--scripts',
            'build/pkg-scripts',
            'dist/CodeGrade Filesystem {}.pkg'.format('.'.join(map(str, __version__))),
        ],
        stdout=sys.stdout.fileno(),
        stderr=sys.stderr.fileno(),
    )
else:
    print('Your platform cannot build cgfs yet')
