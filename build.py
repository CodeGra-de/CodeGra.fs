#!/usr/bin/env python3

import os
import sys
import subprocess

import requests

from codegra_fs import __version__

os.chdir(os.path.dirname(__file__))


def pyinstaller(module, name):
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
            os.path.join('static', 'icons', 'ms-icon.ico'),
            module,
        ],
    )


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
    pyinstaller(os.path.join('codegra_fs', 'cgfs.py'), 'cgfs')
    pyinstaller(os.path.join('codegra_fs', 'api_consumer.py'), 'cgapi-consumer')

    url = 'https://github.com/billziss-gh/winfsp/releases/download/v1.4.19049/winfsp-1.4.19049.msi'
    r = requests.get(url, allow_redirects=True)
    r.raise_for_status()
    open('dist/winfsp.msi', 'wb').write(r.content)

    npm('build:win')
elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
    # subprocess.check_call(['python3', 'sdist', 'bdist_wheel'])
    # print(
    #     """You can now upload this dist to pypi using:

    # `twine upload dist/*`
    # """
    # )
    print('Build cgfs with `make build`.')
else:
    print('Your platform cannot build cgfs yet')
