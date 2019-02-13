import os
import stat
import time
import uuid
import tarfile
import subprocess
import urllib.request

import pytest
import requests

from helpers import (
    ls, rm, join, chmod, chown, isdir, mkdir, rm_rf, rmdir, isfile, rename,
    symlink
)


@pytest.fixture(autouse=True, params=['thomas'])
def username(request):
    yield request.param


@pytest.fixture(autouse=True, params=['Thomas Schaper'])
def password(request):
    yield request.param


@pytest.fixture
def teacher_id():
    req = requests.post(
        'http://localhost:5000/api/v1/login',
        json={
            'username': 'robin',
            'password': 'Robin'
        }
    )
    return req.json()['user']['id']


@pytest.fixture
def ta_id(username, password):
    req = requests.post(
        'http://localhost:5000/api/v1/login',
        json={
            'username': username,
            'password': password
        }
    )
    return req.json()['user']['id']


@pytest.fixture
def admin_jwt():
    req = requests.post(
        'http://localhost:5000/api/v1/login',
        json={
            'username': 'admin',
            'password': 'admin'
        }
    )
    return req.json()['access_token']


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
        with open(
            join(
                mount_dir,
                [l for l in ls(mount_dir) if isdir(mount_dir, l)][0], 'file'
            ), 'w+'
        ) as f:
            f.write('hello\n')


def test_delete_invalid_file(mount_dir):
    with pytest.raises(PermissionError):
        top = [l for l in ls(mount_dir) if isdir(mount_dir, l)][0]
        rm_rf(mount_dir, top)

    with pytest.raises(PermissionError):
        top = [l for l in ls(mount_dir) if isdir(mount_dir, l)][0]
        f = [l for l in ls(mount_dir, top) if isdir(mount_dir, top, l)][0]
        rm_rf(mount_dir, top, f)


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
        amount += 1 if 'Student1' in item else 0
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


@pytest.mark.parametrize('fixed', [False, True], indirect=True)
def test_double_open_unlink(sub_done, mount, fixed):
    fname = join(sub_done, 'new_test_file')
    f = open(fname, 'wb')
    f.write(b'hello')

    f.flush()
    f.close()

    ff = open(fname, 'r+b')
    fff = open(fname, 'r+b')
    print(f, ff, fff)

    os.unlink(fname)

    assert ff.read() == b'hello'

    ff.close()

    assert fff.read() == b'hello'

    fff.close()

    with pytest.raises(FileNotFoundError):
        ff = open(fname, 'r+b')


def test_set_utime(sub_done, mount):
    fname = join(sub_done, 'new_test_file')
    fname2 = join(sub_done, 'new_test_file2')
    open(fname, 'w').close()

    old_st = os.lstat(fname)
    os.utime(fname, (10, 123.5))
    new_st = os.lstat(fname)

    assert new_st.st_atime == 10.0
    assert new_st.st_mtime == 123.5

    assert old_st.st_atime != 10.0
    assert old_st.st_mtime != 123.5

    mount(fixed=True)

    with pytest.raises(PermissionError):
        os.utime(join(sub_done, 'dir', 'single_file_work'), (100, 1235))

    open(fname2, 'w').close()

    old_st = os.lstat(fname2)
    os.utime(fname2, (10, 123.5))
    new_st = os.lstat(fname2)

    assert new_st.st_atime == 10.0
    assert new_st.st_mtime == 123.5

    assert old_st.st_atime != 10.0
    assert old_st.st_mtime != 123.5


def test_non_exising_submission(assig_done):
    with pytest.raises(FileNotFoundError):
        open(join(assig_done, 'NON EXISTING', 'file'), 'x').close()

    with pytest.raises(FileNotFoundError):
        mkdir(assig_done, 'NON EXISTING', 'file')

    with pytest.raises(FileNotFoundError):
        rename(
            [assig_done, 'NON EXISTING', 'file'],
            [assig_done, 'NON EXISTING', 'file2']
        )

    with pytest.raises(FileNotFoundError):
        ls(assig_done, 'NON EXISTING')


def test_renaming_submission(sub_done, sub_done2, assig_done):
    with pytest.raises(FileExistsError):
        rename([sub_done], [sub_done2])

    with pytest.raises(PermissionError):
        rename([sub_done], [assig_done, 'NEW AND WRONG'])

    open(join(sub_done, 'hello'), 'w').close()

    with pytest.raises(PermissionError):
        rename([sub_done, 'hello'], [sub_done2, 'hello'])


def test_removing_xattrs(sub_done):
    fname = join(sub_done, 'hello')
    open(fname, 'w').close()

    with pytest.raises(OSError):
        os.removexattr(fname, 'user.cool_attr')


def test_write_to_directory(sub_done):
    fdir = join(sub_done, 'new_dir')
    fname = join(fdir, 'new_file')

    mkdir(fdir)
    assert isdir(fdir)
    assert not isfile(fdir)

    with pytest.raises(IsADirectoryError):
        with open(fdir, 'w') as f:
            f.write('hello\n')

    open(fname, 'w').close()
    with pytest.raises(NotADirectoryError):
        ls(fname)
    with pytest.raises(FileExistsError):
        mkdir(fname)


def test_difficult_assigned_to(
    mount, teacher_jwt, student_jwt, teacher_id, ta_id, assig_open
):
    assig_id = open(join(assig_open, '.cg-assignment-id')).read().strip()

    old = requests.post(
        'http://localhost:5000/api/v1/assignments/{}/submission'.
        format(assig_id),
        headers={
            'Authorization': 'Bearer ' + student_jwt
        },
        files=dict(file=open('./test_data/multiple_dir_archive.zip', 'rb'))
    ).json()
    new = requests.post(
        'http://localhost:5000/api/v1/assignments/{}/submission'.
        format(assig_id),
        files=dict(file=open('./test_data/multiple_dir_archive.zip', 'rb')),
        headers={
            'Authorization': 'Bearer ' + student_jwt
        },
    ).json()
    print(old, new)

    requests.patch(
        'http://localhost:5000/api/v1/submissions/{}/grader'.format(old["id"]),
        json={'user_id': ta_id},
        headers={'Authorization': 'Bearer ' + teacher_jwt},
    )

    requests.patch(
        'http://localhost:5000/api/v1/submissions/{}/grader'.format(new["id"]),
        json={'user_id': teacher_id},
        headers={'Authorization': 'Bearer ' + teacher_jwt},
    )

    mount(assigned_to_me=True)
    assert all([l[0] == '.' for l in ls(assig_open)])
    mount(assigned_to_me=False)
    assert ls(assig_open)

    requests.patch(
        'http://localhost:5000/api/v1/submissions/{}/grader'.format(new["id"]),
        json={'user_id': ta_id},
        headers={'Authorization': 'Bearer ' + teacher_jwt},
    )
    mount(assigned_to_me=True)
    assert len([l for l in ls(assig_open) if l[0] != '.']) == 1


def test_double_assignment(mount, teacher_jwt, assig_open):
    n_id = str(uuid.uuid4())
    assig_name = 'New_Assig-{}'.format(n_id)
    print(n_id)
    assig_id = open(join(assig_open, '.cg-assignment-id')).read().strip()
    course_id = requests.get(
        'http://localhost:5000/api/v1/assignments/{}'.format(assig_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt
        },
    ).json()['course']['id']

    assert requests.post(
        'http://localhost:5000/api/v1/courses/{}/assignments/'.
        format(course_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt
        },
        json={
            'name': assig_name
        }
    ).status_code < 300
    # Make sure we have some time between the assignments
    time.sleep(1)
    assert requests.post(
        'http://localhost:5000/api/v1/courses/{}/assignments/'.
        format(course_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt
        },
        json={
            'name': assig_name
        }
    ).status_code < 300

    mount()

    assert len(
        [l for l in ls(assig_open, '..') if l.startswith(assig_name)]
    ) == 2


@pytest.mark.parametrize(
    'username,password', [['admin', 'admin']], indirect=True
)
def test_double_course(mount, admin_jwt, mount_dir):
    n_id = str(uuid.uuid4())
    course_name = 'New_Assig-{}'.format(n_id)
    print(n_id)

    assert requests.patch(
        'http://localhost:5000/api/v1/roles/4',
        headers={
            'Authorization': 'Bearer ' + admin_jwt
        },
        json={
            'value': True,
            'permission': 'can_create_courses'
        }
    ).status_code < 300

    assert requests.post(
        'http://localhost:5000/api/v1/courses/',
        headers={
            'Authorization': 'Bearer ' + admin_jwt
        },
        json={
            'name': course_name
        }
    ).status_code < 300
    time.sleep(1)
    assert requests.post(
        'http://localhost:5000/api/v1/courses/',
        headers={
            'Authorization': 'Bearer ' + admin_jwt
        },
        json={
            'name': course_name
        }
    ).status_code < 300

    mount()

    assert len([l for l in ls(mount_dir) if l.startswith(course_name)]) == 2
