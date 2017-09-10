import os
import stat

import pytest

from helpers import (
    ls, rm, join, chmod, chown, isdir, mkdir, rm_rf, rmdir, isfile, rename,
    symlink
)


@pytest.fixture(autouse=True)
def username():
    yield 'thomas'


@pytest.fixture(autouse=True)
def password():
    yield 'Thomas Schaper'


def test_create_symlink(sub_done):
    with pytest.raises(PermissionError):
        symlink([sub_done, 'dir'], [sub_done, 'wowsers'])

    assert isdir(sub_done, 'dir')
    assert not isdir(sub_done, 'wowsers')

    mkdir(sub_done, 'wowsers')
    assert isdir(sub_done, 'wowsers')


def test_create_invalid_file(mount_dir):
    with pytest.raises(PermissionError):
        with open(join(mount_dir, 'file'), 'w+') as f:
            f.write('hello\n')

    with pytest.raises(PermissionError):
        with open(join(mount_dir, ls(mount_dir)[0], 'file'), 'w+') as f:
            f.write('hello\n')


def test_delete_invalid_file(mount_dir):
    with pytest.raises(PermissionError):
        rm_rf(mount_dir, ls(mount_dir)[0])

    with pytest.raises(PermissionError):
        top = ls(mount_dir)[0]
        rm_rf(mount_dir, top, ls(mount_dir, top)[0])


def test_invalid_perm_setting(sub_done):
    assert isfile(sub_done, 'dir', 'single_file_work')

    with pytest.raises(PermissionError):
        chown([sub_done, 'dir', 'single_file_work'], 7, 7)
    assert isfile(sub_done, 'dir', 'single_file_work')

    with pytest.raises(PermissionError):
        chmod([sub_done, 'dir', 'single_file_work'], stat.S_IRGRP)
    assert isfile(sub_done, 'dir', 'single_file_work')


def test_truncate_file(sub_done):
    with open(join(sub_done, 'dir', 'single_file_work'), 'r') as f:
        old = f.read()
    with open(join(sub_done, 'dir', 'single_file_work'), 'a') as f:
        f.write('wow\n')
    with open(join(sub_done, 'dir', 'single_file_work'), 'r') as f:
        assert f.read() == old + 'wow\n'
    with open(join(sub_done, 'dir', 'single_file_work'), 'a') as f:
        assert f.truncate(len(old))
    with open(join(sub_done, 'dir', 'single_file_work'), 'r') as f:
        assert f.read() == old
    with open(join(sub_done, 'dir', 'single_file_work'), 'a') as f:
        assert f.truncate(len(old) * 3)
    with open(join(sub_done, 'dir', 'single_file_work'), 'r') as f:
        new = f.read()
        assert len(new) == len(old) * 3
        new.startswith(old)
        all(n == '\0' for n in new[len(old):])

    fd = os.open(
        join(sub_done, 'dir', 'single_file_work'), os.O_TRUNC | os.O_WRONLY
    )
    os.write(fd, b'hello\n')
    os.close(fd)
    with open(join(sub_done, 'dir', 'single_file_work'), 'r') as f:
        assert f.read() == 'hello\n'


def test_open_directory(sub_done):
    with pytest.raises(IsADirectoryError):
        with open(join(sub_done, 'dir/'), 'w') as f:
            f.write('ERROR\n')


def test_force_create_file(sub_done):
    with pytest.raises(FileExistsError):
        fd = os.open(join(sub_done, 'dir', 'single_file_work'), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, b'WRONG\n')
        os.close(fd)


def test_create_existing_dir(sub_done):
    with pytest.raises(FileExistsError):
        mkdir(sub_done, 'dir')


def test_rename(mount_dir, sub_done, sub_open):
    assert isdir(mount_dir, sub_done, 'dir')
    assert not isdir(mount_dir, sub_done, 'dir33')
    files = set(ls(mount_dir, sub_done, 'dir'))

    rename([mount_dir, sub_done, 'dir'], [mount_dir, sub_done, 'dir33'])

    assert isdir(mount_dir, sub_done, 'dir33')
    assert not isdir(mount_dir, sub_done, 'dir')
    assert files == set(ls(mount_dir, sub_done, 'dir33'))

    with open(join(mount_dir, sub_done, 'dir33', 'single_file_work'),
              'w') as f:
        f.write('hello\n')

    rename(
        [mount_dir, sub_done, 'dir33', 'single_file_work'],
        [mount_dir, sub_done, 'dir33', 'single_file_work!']
    )

    with open(join(mount_dir, sub_done, 'dir33', 'single_file_work!'),
              'r') as f:
        assert f.read() == 'hello\n'
