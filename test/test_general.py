import os
import stat
import tarfile
import subprocess
import urllib.request

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
        fd = os.open(
            join(sub_done, 'dir', 'single_file_work'),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY
        )
        os.write(fd, b'WRONG\n')
        os.close(fd)


def test_create_existing_dir(sub_done):
    with pytest.raises(FileExistsError):
        mkdir(sub_done, 'dir')


def test_rename(mount_dir, sub_done, sub_open):
    assert isdir(sub_done, 'dir')
    assert not isdir(sub_done, 'dir33')
    files = set(ls(sub_done, 'dir'))

    assert isdir(sub_done, 'dir')
    assert not isdir(sub_done, 'dir33')
    mkdir(sub_done, 'dir33')
    mkdir(sub_done, 'dir', 'sub_dir')
    assert isdir(sub_done, 'dir33')
    with open(join(sub_done, 'dir33', 'new_file'), 'w') as f:
        f.write('bye\n')

    rename([sub_done, 'dir33'], [sub_done, 'dir', 'sub_dir', 'dir33'])
    with open(join(sub_done, 'dir', 'sub_dir', 'dir33', 'new_file'), 'r') as f:
        assert f.read() == 'bye\n'


def test_illegal_rename(mount_dir, sub_done, sub_open):
    assert isdir(sub_done, 'dir')
    assert not isdir(sub_done, 'dir33')
    mkdir(sub_done, 'dir33')
    assert isdir(sub_done, 'dir33')

    with pytest.raises(FileNotFoundError):
        rename([sub_done, 'dir33'], [sub_done, 'dir', 'non_existing', 'dir33'])

    with pytest.raises(FileExistsError):
        rename([sub_done, 'dir33'], [sub_done, 'dir'])


@pytest.mark.parametrize('fixed', [True, False], indirect=True)
def test_compiling_program(sub_done, mount, fixed):
    url = 'https://attach.libremail.nl/__test_codegra.fs__.tar.gz'
    fname = join(sub_done, '42.tar.gz')
    fdir = join(sub_done, '42sh/')
    urllib.request.urlretrieve(url, fname)
    tar = tarfile.open(fname, "r:gz")
    tar.extractall(sub_done)
    tar.close()
    print(subprocess.check_output(['make', '-C', fdir]))
    assert isdir(fdir)
    assert isfile(fname)
    assert subprocess.check_output(
        [join(fdir, '42sh'), '-c', 'echo hello from 42']
    ).decode('utf-8') == 'hello from 42\n'

    mount()

    if fixed:
        assert not isdir(fdir)
        assert not isfile(fname)
        return

    assert isfile(fname)
    assert isdir(fdir)
    assert subprocess.check_output(
        [join(fdir, '42sh'), '-c', 'echo hello from 42']
    ).decode('utf-8') == 'hello from 42\n'

    rm_rf(fdir)
    assert not isdir(fdir)

    mount()

    assert isfile(fname)
    assert not isdir(fdir)


@pytest.mark.parametrize('latest_only', [True, False], indirect=True)
def test_latest_only(assig_done, latest_only):
    amount = 0
    for item in ls(assig_done):
        amount += 1 if 'Stupid1' in item else 0
    if latest_only:
        assert amount == 1
    else:
        assert amount > 1


@pytest.mark.parametrize('fixed', [True, False], indirect=True)
def test_double_open(sub_done, mount, fixed):
    fname = join(sub_done, 'new_test_file')
    f = open(fname, 'wb')
    f.write(b'hello')

    ff = open(fname, 'r+b')
    fff = open(fname, 'r+b')

    f.flush()

    assert ff.read() == b'hello'

    f.close()

    assert fff.read() == b'hello'

    ff.close()
    fff.close()


@pytest.mark.parametrize('fixed', [False], indirect=True)
def test_deleting_file_in_fixed(sub_done, mount):
    fname = join(sub_done, 'new_test_file')
    fname2 = join(sub_done, 'new_test_file2')

    # Make sure we cannot delete existing files in fixed mode
    assert not isfile(fname)
    with open(fname, 'w') as f:
        f.write('Hello thomas\n')
    assert isfile(fname)

    mount(fixed=True)

    assert isfile(fname)
    with open(fname, 'r') as f:
        assert f.read() == 'Hello thomas\n'
    with pytest.raises(PermissionError):
        with open(fname, 'w') as f:
            f.write('Hello thomas\n')
    with pytest.raises(PermissionError):
        rm(fname)

    del fname

    # Now make sure we can delete files that did not exist
    assert not isfile(fname2)
    with open(fname2, 'w') as f:
        f.write('Hello thomas2\n')
    with open(fname2, 'r') as f:
        assert f.read() == 'Hello thomas2\n'
    assert isfile(fname2)

    rm(fname2)

    assert not isfile(fname2)

    # Make sure files created in fixed mode are not visible after a remount
    assert not isfile(fname2)
    with open(fname2, 'w') as f:
        f.write('Hello thomas2\n')
    with open(fname2, 'r') as f:
        assert f.read() == 'Hello thomas2\n'
    assert isfile(fname2)

    mount(fixed=True)
    assert not isfile(fname2)
    with open(fname2, 'w') as f:
        f.write('Hello thomas2\n')
    with open(fname2, 'r') as f:
        assert f.read() == 'Hello thomas2\n'
    assert isfile(fname2)

    mount(fixed=True)

    assert not isfile(fname2)


def test_renaming_file_in_fixed(sub_done, mount):
    fname = join(sub_done, 'new_test_file')
    fname2 = join(sub_done, 'new_test_file2')
    fname3 = join(sub_done, 'new_test_file3')

    # Make sure we cannot delete existing files in fixed mode
    assert not isfile(fname)
    with open(fname, 'w') as f:
        f.write('Hello thomas\n')
    assert isfile(fname)

    mount(fixed=True)

    assert isfile(fname)
    with pytest.raises(PermissionError):
        rename([fname], [fname2])

    del fname

    assert not isfile(fname2)
    with open(fname2, 'w') as f:
        f.write('Hello thomas\n')
    assert isfile(fname2)
    rename([fname2], [fname3])

    assert not isfile(fname2)
    assert isfile(fname3)
    with open(fname3, 'r') as f:
        assert f.read() == 'Hello thomas\n'

    mount(fixed=True)
    assert not isfile(fname3)


def test_deleting_directory_in_fixed(sub_done, mount):
    fdir = join(sub_done, 'new_test_file')
    fdir2 = join(sub_done, 'new_test_file2')
    fdir3 = join(sub_done, 'new_test_file3')

    # Make sure we cannot delete existing files in fixed mode
    assert not isdir(fdir)
    mkdir(fdir)
    assert isdir(fdir)

    mount(fixed=True)

    assert isdir(fdir)
    with pytest.raises(PermissionError):
        rmdir(fdir)
    assert isdir(fdir)

    del fdir

    assert not isdir(fdir2)
    mkdir(fdir2)
    assert isdir(fdir2)
    rename([fdir2], [fdir3])

    assert not isdir(fdir2)
    assert isdir(fdir3)

    mount(fixed=True)
    assert not isdir(fdir3)


def test_editing_file_in_fixed(sub_done, mount):
    fname = join(sub_done, 'new_test_file')
    fname2 = join(sub_done, 'new_test_file2')
    fname3 = join(sub_done, 'new_test_file3')

    # Make sure we cannot delete existing files in fixed mode
    assert not isfile(fname)
    with open(fname, 'w') as f:
        f.write('Hello thomas\n')
    assert isfile(fname)

    mount(fixed=True)

    assert isfile(fname)
    with pytest.raises(PermissionError):
        with open(fname, 'w') as f:
            f.write('hello\n')
