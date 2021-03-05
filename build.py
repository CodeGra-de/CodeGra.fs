#!/usr/bin/env python3
import os
import sys
import platform
import subprocess

import requests

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
os.chdir(BASE_DIR)

WINFSP_VERSION = '1.8.20304'


def pyinstaller(module, name):
    subprocess.check_call(
        [
            'pyinstaller',
            '--noconfirm',
            '--onedir',
            '--additional-hooks-dir=./pyinstaller_hooks',
            '--specpath',
            'dist',
            '--name',
            name,
            '--icon',
            os.path.join(BASE_DIR, 'static', 'icons', 'ms-icon.ico'),
            module,
        ],
    )


def download_file(url, dest):
    if not os.path.exists(dest):
        r = requests.get(url, allow_redirects=True)
        r.raise_for_status()
        with open(dest, 'wb') as f:
            f.write(r.content)


def npm(job):
    subprocess.check_call(['npm', 'run', job], shell=True)


def make(*recipe):
    subprocess.check_call(['make', *recipe])


if sys.platform.startswith('win32'):
    subprocess.check_call(['pip', 'install', '.'])
    pyinstaller(os.path.join(BASE_DIR, 'codegra_fs', 'cgfs.py'), 'cgfs')
    pyinstaller(
        os.path.join(BASE_DIR, 'codegra_fs', 'api_consumer.py'),
        'cgapi-consumer'
    )

    download_file(
        (
            'https://github.com/billziss-gh/winfsp/releases/download/'
            'v{version_short}/winfsp-{version_long}.msi'
        ).format(
            version_long=WINFSP_VERSION,
            version_short='.'.join(WINFSP_VERSION.split('.')[:2]),
        ),
        os.path.join(BASE_DIR, 'dist', 'winfsp.msi'),
    )

    npm('build:win')
elif platform.system() in ('Linux', 'Darwin'):
    make('build-quick')
else:
    print('Your platform cannot build cgfs yet.')
