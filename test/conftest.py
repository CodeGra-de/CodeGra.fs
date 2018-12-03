import os
import sys
import copy
import json
import time
import datetime
import tempfile
import contextlib
import subprocess

import pytest
import requests

password_pass = 0

@pytest.fixture(autouse=True)
def setup():
    pass


@pytest.fixture
def mount_dir():
    name = tempfile.mkdtemp()
    yield name + '/'
    os.removedirs(name)


@pytest.fixture(params=[False])
def fixed(request):
    return request.param


@pytest.fixture(params=[False])
def rubric_append_only(request):
    return request.param


@pytest.fixture(params=[True])
def latest_only(request):
    return request.param


@pytest.fixture(params=[False])
def assigned_to_me(request):
    return request.param


@pytest.fixture(autouse=True)
def mount(
    username, password, mount_dir, latest_only, fixed, rubric_append_only,
    assigned_to_me
):
    proc = None
    r_fixed = fixed
    del fixed
    r_assigned_to_me = assigned_to_me
    del assigned_to_me

    def do_mount(fixed=r_fixed, assigned_to_me=r_assigned_to_me):
        global password_pass
        nonlocal proc

        os.environ['CGAPI_BASE_URL'] = 'http://localhost:5000/api/v1'
        os.environ['CGFS_TESTING'] = 'True'
        args = [
            'coverage', 'run', '-a', './codegra_fs/cgfs.py', '--verbose',
            username, mount_dir
        ]
        stdin = None

        os.environ.pop('CGFS_PASSWORD', None)
        if password_pass == 0:
            args.extend(['--password', password])
        elif password_pass == 1:
            os.environ['CGFS_PASSWORD'] = password
        elif password_pass == 2:
            stdin = tempfile.TemporaryFile(mode='r+')
            stdin.write(password)
            stdin.seek(0)
        password_pass = (password_pass + 1) % 3

        if not latest_only:
            args.append('-a')
        if fixed:
            args.append('--fixed')
        if not rubric_append_only:
            args.append('--rubric-edit')
        if assigned_to_me:
            args.append('--assigned-to-me')

        proc = subprocess.Popen(args, stdin=stdin, stdout=sys.stdout, stderr=sys.stderr)
        check_dir = os.path.join(mount_dir, '.cg-mode')
        i = 0.001
        while not os.path.isfile(check_dir):
            time.sleep(i)
            i *= 2

    def do_umount():
        subprocess.check_call(['fusermount', '-u', mount_dir])
        try:
            proc.wait(1)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    def do_remount(fixed=r_fixed, assigned_to_me=r_assigned_to_me):
        do_umount()
        do_mount(fixed=fixed, assigned_to_me=assigned_to_me)

    do_mount()
    yield do_remount
    do_umount()


@pytest.fixture(autouse=True)
def assig_open(mount, python_id, mount_dir):
    return os.path.join(mount_dir, 'Programmeertalen', 'Python')


@pytest.fixture
def assig_done(mount, shell_id, mount_dir):
    return os.path.join(mount_dir, 'Programmeertalen', 'Shell')


@pytest.fixture
def sub_done2(assig_done):
    print(os.listdir(assig_done))
    for path in reversed(sorted(os.listdir(assig_done))):
        if 'Student2' in path:
            return os.path.join(assig_done, path)


@pytest.fixture
def sub_done(assig_done):
    print(os.listdir(assig_done))
    for path in reversed(sorted(os.listdir(assig_done))):
        if 'Student1' in path:
            return os.path.join(assig_done, path)


@pytest.fixture
def sub_open(assig_open):
    for path in reversed(sorted(os.listdir(assig_open))):
        if 'Student1' in path:
            return os.path.join(assig_open, path)


@pytest.fixture
def teacher_jwt():
    req = requests.post(
        'http://localhost:5000/api/v1/login',
        json={'username': 'robin',
              'password': 'Robin'}
    )
    return req.json()['access_token']


@pytest.fixture
def student_jwt():
    req = requests.post(
        'http://localhost:5000/api/v1/login',
        json={'username': 'student1',
              'password': 'Student1'}
    )
    return req.json()['access_token']


@pytest.fixture
def shell_id(student_jwt):
    r = requests.get(
        'http://localhost:5000/api/v1/assignments/',
        headers={
            'Authorization': 'Bearer ' + student_jwt,
        }
    )
    return [item for item in r.json() if item['name'] == 'Shell'][0]['id']


@pytest.fixture
def python_id(student_jwt):
    r = requests.get(
        'http://localhost:5000/api/v1/assignments/',
        headers={
            'Authorization': 'Bearer ' + student_jwt,
        }
    )
    return [item for item in r.json() if item['name'] == 'Python'][0]['id']


@pytest.fixture(autouse=True)
def sub1_id(student_jwt, python_id, teacher_jwt):
    r = requests.post(
        f'http://localhost:5000/api/v1/assignments/{python_id}/submission',
        headers={
            'Authorization': 'Bearer ' + student_jwt,
        },
        files=dict(file=open('./test_data/multiple_dir_archive.zip', 'rb'))
    )
    assert r.status_code == 201
    sub_id = r.json()['id']

    yield sub_id

    requests.delete(
        f'http://localhost:5000/api/v1/submissions/{sub_id}',
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    )


@pytest.fixture(autouse=True)
def sub2_id(student_jwt, shell_id, teacher_jwt):
    r = requests.patch(
        f'http://localhost:5000/api/v1/assignments/{shell_id}',
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        },
        json={
            'state':
                'open',
            'deadline':
                (datetime.datetime.utcnow() + datetime.timedelta(days=365))
                .isoformat()
        }
    )
    assert r.status_code == 200

    r = requests.post(
        f'http://localhost:5000/api/v1/assignments/{shell_id}/submission',
        headers={
            'Authorization': 'Bearer ' + student_jwt,
        },
        files=dict(file=open('./test_data/multiple_dir_archive.zip', 'rb'))
    )
    print(r.json())
    assert r.status_code == 201
    sub_id = r.json()['id']

    requests.patch(
        f'http://localhost:5000/api/v1/assignments/{shell_id}',
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        },
        json={
            'state': 'done',
            'deadline': datetime.datetime.utcnow().isoformat()
        }
    )

    yield sub_id

    requests.delete(
        f'http://localhost:5000/api/v1/submissions/{sub_id}',
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    )


@pytest.fixture(autouse=True)
def teardown():
    pass
