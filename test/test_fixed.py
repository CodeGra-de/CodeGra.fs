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
    yield 'student1'


@pytest.fixture(autouse=True)
def password():
    yield 'Student1'


@pytest.mark.parametrize('fixed', [False], indirect=True)
def test_deleting_file_in_fixed(sub_open, mount):
    fname = join(sub_open, 'new_test_file')
    fname2 = join(sub_open, 'new_test_file2')

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


def test_renaming_file_in_fixed(sub_open, mount):
    fname = join(sub_open, 'new_test_file')
    fname2 = join(sub_open, 'new_test_file2')
    fname3 = join(sub_open, 'new_test_file3')

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


def test_deleting_directory_in_fixed(sub_open, mount):
    fdir = join(sub_open, 'new_test_file')
    fdir2 = join(sub_open, 'new_test_file2')
    fdir3 = join(sub_open, 'new_test_file3')

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


def test_editing_file_in_fixed(sub_open, mount):
    fname = join(sub_open, 'new_test_file')

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


@pytest.mark.parametrize('fixed', [True], indirect=True)
def test_truncate_fixed(sub_open):
    fname = join(sub_open, 'new_file')

    f = open(fname, 'w')
    f.write('hello\n')
    f.flush()

    ff = open(fname, 'a')
    ff.truncate(1)

    ff.close()
    ff = open(fname, 'r')
    assert ff.read() == 'h'

    ff.close()

    f.close()

    os.truncate(fname, 0)
    f = open(fname, 'r')
    assert f.read() == ''
    f.close()
