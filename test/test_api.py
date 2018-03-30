import os
import re
import json
import stat
import tarfile
import subprocess
import urllib.request

import requests

import pytest
from helpers import (
    ls, rm, join, chmod, chown, isdir, mkdir, rm_rf, rmdir, isfile, rename,
    symlink
)


def run_shell(prog, **kwargs):
    return subprocess.run(
        prog, stderr=subprocess.PIPE, stdout=subprocess.PIPE, **kwargs
    )


@pytest.fixture(autouse=True)
def username():
    yield 'robin'


@pytest.fixture(autouse=True)
def password():
    yield 'Robin'


@pytest.mark.parametrize(
    'data, res', [
        (
            b'# Header\nDescription\n----\n- (1.0) Item - Desc\n', (
                [('Header', 'Description', [(1.0, 'Item', 'Desc')])],
                '# \[{id}\] Header\n  Description\n-+\n- '
                '\[{id}\] \(1\.0\) Item - Desc\n'
            )
        ),
        (
            b'# Header\nDescription\n----\n- (1.0) Item - Desc\n- (4.0) Item2'
            b' - Desc2\n', (
                [
                    (
                        'Header', 'Description',
                        [(1.0, 'Item', 'Desc'), (4.0, 'Item2', 'Desc2')]
                    )
                ], '# \[{id}\] Header\n  Description\n-+\n- \[{id}\] \(1\.0\)'
                ' Item - Desc\n- \[{id}\] \(4\.0\) Item2 - Desc2\n'
            )
        ),
        (
            b'# Header\nDescription\n----\n- (1.0) Item - Desc\n- (4.0) Item2 '
            b'- Desc2\n\n# Header 2\nDescription 2\n------\n- (2.5) I - D\n   '
            b'C\n  \nA\n\n  \nM\n', (
                [
                    (
                        'Header', 'Description',
                        [(1.0, 'Item', 'Desc'), (4.0, 'Item2', 'Desc2')]
                    ), (
                        'Header 2', 'Description 2', [
                            (2.5, 'I', 'D\nC\n\nA\n\n\nM'),
                        ]
                    )
                ], '# \[{id}\] Header\n  Description\n-+\n- \[{id}\] \(1\.0\)'
                ' Item - Desc\n- \[{id}\] \(4\.0\) Item2 - Desc2\n\n#'
                ' \[{id}\] Header 2\n  Description 2\n-+\n- \[{id}\] \(2\.5\) I'
                ' - D\n  C\n  \n  A\n  \n  \n  M\n'
            )
        ),
        (b'hello', False),
        (b'# Header', False),
        (b'# Header\n', False),
        (b'# Header\nDescription', False),
        (b'# Header\nDescription\n', False),
        (b'# Header\nDescription\n----\nItem', False),
        (b'# Header\nDescription\n----\n(1.0) Item - Desc', False),
        (b'# Header\nDescription\n----\n- (1.0) Item - Desc\n# C', False),
        (b'# Header\nDescription\n----\n- [noid] (1.0) Item - Desc\n', False),
        (b'# Header\nDescription\n----\n- (1.0) Item\n', False),
    ]
)
def test_get_set_rubric(
    sub_done, assig_done, data, res, shell_id, teacher_jwt
):
    r = requests.delete(
        'http://localhost:5000/api/v1/assignments/{}/rubrics/'.
        format(shell_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    )
    assert r.status_code < 400 or r.status_code == 404
    r_file = join(assig_done, '.cg-edit-rubric.md')
    r_help_file = join(assig_done, '.cg-edit-rubric.help')
    with open(r_file, 'r') as r:
        assert r.read() == ''

    with open(r_help_file) as r:
        assert r.read()

    f = open(r_file, 'wb', 0)
    f.write(data)

    f.flush()

    if res:
        f.close()

        with open(r_file, 'r') as r:
            read = r.read()
            print(read)
            print(res[1].format(id='[a-z0-9]{16}'))
            assert re.compile(res[1].format(id='[a-z0-9]{16}')).match(read)

        with open(r_file, 'w') as r:
            r.write(read)

        with open(r_file, 'r') as r:
            assert r.read() == read

        r = requests.get(
            'http://localhost:5000/api/v1/assignments/{}/rubrics/'.
            format(shell_id),
            headers={
                'Authorization': 'Bearer ' + teacher_jwt,
            }
        )
        assert r.status_code == 200
        for res, exp in zip(r.json(), res[0]):
            assert res['header'] == exp[0]
            assert res['description'] == exp[1]
            for exp_i, res_i in zip(res['items'], exp[2]):
                assert exp_i['points'] == res_i[0]
                assert exp_i['header'] == res_i[1]
                assert exp_i['description'] == res_i[2]
    else:
        with pytest.raises(OSError):
            os.fsync(f.fileno())

        with pytest.raises(PermissionError):
            f.close()

        open(r_file, 'w').write('__RESET__\n')

        with open(r_file, 'r') as r:
            assert r.read() == ''


@pytest.mark.parametrize(
    'data, res, to_add, res_after', [
        (
            b'# Header\nDescription\n----\n- (1.0) Item - Desc\n- (4.0) Item2'
            b' - Desc2\n', (
                [
                    (
                        'Header', 'Description',
                        [(1.0, 'Item', 'Desc'), (4.0, 'Item2', 'Desc2')]
                    )
                ], '# \[{id}\] Header\n  Description\n-+\n- \[{id}\] \(1\.0\)'
                ' Item - Desc\n- \[{id}\] \(4\.0\) Item2 - Desc2\n'
            ), '- (5.0) Item4 - Desc4\n', (
                [
                    (
                        'Header', 'Description',
                        [(1.0, 'Item', 'Desc'), (5.0, 'Item4', 'Desc4')]
                    )
                ], '# \[{id}\] Header\n  Description\n-+\n- \[{id}\] \(1\.0\)'
                ' Item - Desc\n- \[{id}\] \(5\.0\) Item4 - Desc4\n'
            )
        ),
    ]
)
@pytest.mark.parametrize('rubric_append_only', [True, False], indirect=True)
def test_remove_add_rubric_item(
    sub_done,
    assig_done,
    data,
    res,
    shell_id,
    teacher_jwt,
    to_add,
    res_after,
    rubric_append_only,
):
    r = requests.delete(
        'http://localhost:5000/api/v1/assignments/{}/rubrics/'.
        format(shell_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    )
    assert r.status_code < 400 or r.status_code == 404
    r_file = join(assig_done, '.cg-edit-rubric.md')
    with open(r_file, 'r') as r:
        assert r.read() == ''

    f = open(r_file, 'wb', 0)
    f.write(data)

    f.flush()

    f.close()

    def test_correct(res):
        with open(r_file, 'r') as r:
            read = r.read()
            print(read)
            print(res[1].format(id='[a-z0-9]{16}'))
            assert re.compile(res[1].format(id='[a-z0-9]{16}')).match(read)

        with open(r_file, 'w') as r:
            r.write(read)

        with open(r_file, 'r') as r:
            assert r.read() == read

        r = requests.get(
            'http://localhost:5000/api/v1/assignments/{}/rubrics/'.
            format(shell_id),
            headers={
                'Authorization': 'Bearer ' + teacher_jwt,
            }
        )
        assert r.status_code == 200
        for res, exp in zip(r.json(), res[0]):
            assert res['header'] == exp[0]
            assert res['description'] == exp[1]
            for exp_i, res_i in zip(res['items'], exp[2]):
                assert exp_i['points'] == res_i[0]
                assert exp_i['header'] == res_i[1]
                assert exp_i['description'] == res_i[2]

    test_correct(res)

    read = open(r_file, 'r').read().split('\n')
    read = read[:-2]
    read.append(to_add)
    read = '\n'.join(read)

    if rubric_append_only:
        with pytest.raises(PermissionError):
            with open(r_file, 'w') as f:
                f.write(read)
        open(r_file, 'w').write('__RESET__\n\n')
        test_correct(res)
    else:
        with open(r_file, 'w') as f:
            f.write(read)
        test_correct(res_after)


def test_selecting_rubric(
    sub_done,
    assig_done,
    shell_id,
    teacher_jwt,
):
    r = requests.delete(
        'http://localhost:5000/api/v1/assignments/{}/rubrics/'.
        format(shell_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    )
    assert r.status_code < 400 or r.status_code == 404
    r_file = join(assig_done, '.cg-edit-rubric.md')
    ru_file = join(sub_done, '.cg-rubric.md')
    with open(r_file, 'r') as r:
        assert r.read() == ''

    f = open(r_file, 'wb', 0)
    f.write(
        b'# Header\nDescription\n----\n- (1.0) Item - Desc\n- (4.0) Item2 '
        b'- Desc2\n\n# Header 2\nDescription 2\n------\n- (2.5) I - D\n   '
        b'C\n  \nA\n\n\nM\n'
    )

    f.flush()

    f.close()

    with open(join(sub_done, '.cg-submission-id'), 'r') as f:
        sub_id = f.read().strip()

    with open(ru_file, 'r') as f:
        data = f.read()

    print(sub_id)
    r = requests.get(
        'http://localhost:5000/api/v1/submissions/{}/rubrics/'.format(sub_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    )
    assert not r.json()['selected']

    with pytest.raises(PermissionError):
        with open(ru_file, 'w') as f:
            f.write('\n' + data.replace('[ ] I (2.5)', '[x] I (2.5)'))

    with open(ru_file, 'w') as f:
        f.write(data)

    r = requests.get(
        'http://localhost:5000/api/v1/submissions/{}/rubrics/'.format(sub_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    )
    assert not r.json()['selected']

    with open(ru_file, 'w') as f:
        f.write(data.replace('[ ] I (2.5)', '[x] I (2.5)'))

    r = requests.get(
        'http://localhost:5000/api/v1/submissions/{}/rubrics/'.format(sub_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    )
    sel = r.json()['selected']
    assert len(sel) == 1
    assert sel[0]['header'] == 'I'
    assert sel[0]['points'] == 2.5


def test_assig_settings(
    sub_done,
    assig_done,
    shell_id,
    teacher_jwt,
):
    a_file = join(assig_done, '.cg-assignment-settings.ini')

    with open(a_file, 'r') as r:
        data = r.read()

    with pytest.raises(PermissionError):
        with open(a_file, 'w') as r:
            r.write('')

    with pytest.raises(PermissionError):
        with open(a_file, 'w') as r:
            r.write('bla = die')

    with open(a_file, 'w') as r:
        d = data.replace('done', 'open')
        r.write(d)

    assert requests.get(
        'http://localhost:5000/api/v1/assignments/{}'.format(shell_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    ).json()['state'] == 'grading'

    with open(a_file, 'w') as r:
        r.write(data.replace('hidden', 'done'))

    assert requests.get(
        'http://localhost:5000/api/v1/assignments/{}'.format(shell_id),
        headers={
            'Authorization': 'Bearer ' + teacher_jwt,
        }
    ).json()['state'] == 'done'


def test_socket_api(sub_done, assig_done, shell_id, teacher_jwt):
    for root, _, files in os.walk(sub_done):
        for name in files:
            if name[0] != '.':
                f = join(root, name)
                break

    print(f)
    assert run_shell([
        'cgapi-consumer',
        'get-comment',
    ]).returncode == 1
    s = run_shell([
        'cgapi-consumer',
        'get-comment',
        '/etc',
    ])
    assert s.returncode == 3

    print(run_shell(['cgapi-consumer', 'get-comment', f]).stdout)
    res = subprocess.check_output(['cgapi-consumer', 'get-comment', f])
    assert res == b'[]\n'

    assert run_shell([
        'cgapi-consumer',
        'set-comment',
        '/etc',
    ]).returncode == 3
    assert run_shell(['cgapi-consumer', 'set-comment', '/etc', '5',
                      'hello']).returncode == 3

    s = run_shell(['cgapi-consumer', 'set-comment', f, '5'])
    print(s.stderr, s.stdout)
    assert s.returncode == 1

    assert subprocess.check_output(
        ['cgapi-consumer', 'set-comment', f, '5', 'Feedback message']
    ) == b''

    res = subprocess.check_output(['cgapi-consumer', 'get-comment', f])
    assert b'\n' not in res[:-1]
    assert json.loads(res) == [
        {
            'line': 5,
            'col': 0,
            'content': 'Feedback message'
        }
    ]

    assert subprocess.check_output(
        ['cgapi-consumer', 'set-comment', f, '1', 'Message']
    ) == b''
    res = subprocess.check_output(['cgapi-consumer', 'get-comment', f])
    assert b'\n' not in res[:-1]
    assert json.loads(res) == [
        {
            'line': 1,
            'col': 0,
            'content': 'Message'
        }, {
            'line': 5,
            'col': 0,
            'content': 'Feedback message'
        }
    ]

    assert subprocess.check_output(
        ['cgapi-consumer', 'set-comment', f, '5', '']
    ) == b''
    res = subprocess.check_output(['cgapi-consumer', 'get-comment', f])
    assert b'\n' not in res[:-1]
    assert json.loads(res) == [
        {
            'line': 1,
            'col': 0,
            'content': 'Message'
        }, {
            'line': 5,
            'col': 0,
            'content': ''
        }
    ]

    assert run_shell([
        'cgapi-consumer',
        'delete-comment',
        f,
        '4',
    ]).returncode == 2

    # Don't change after a wrong delete
    assert res == subprocess.check_output(['cgapi-consumer', 'get-comment', f])

    assert subprocess.check_output(
        [
            'cgapi-consumer',
            'delete-comment',
            f,
            '5',
        ]
    ) == b''

    res = subprocess.check_output(['cgapi-consumer', 'get-comment', f])
    assert b'\n' not in res[:-1]
    assert json.loads(res) == [
        {
            'line': 1,
            'col': 0,
            'content': 'Message'
        },
    ]

    assert subprocess.check_output([
        'cgapi-consumer',
        'is-file',
        f,
    ]) == b''
    assert run_shell(['cgapi-consumer', 'is-file', '/etc']).returncode == 3
    assert run_shell(
        [
            'cgapi-consumer',
            'is-file',
            join(sub_done, '.cg-rubric.md'),
        ]
    ).returncode == 2


@pytest.mark.parametrize('fixed', [True, False], indirect=True)
def test_cg_mode_file(mount_dir, fixed):
    assert (open(join(mount_dir, '.cg-mode'),
                 'r').read() == 'FIXED\n') == fixed


def test_grade_file(sub_done):
    g_file = join(sub_done, '.cg-grade')
    with open(g_file, 'r') as f:
        assert f.read() == ''

    with open(g_file, 'w') as f:
        f.write('5.5')

    with pytest.raises(PermissionError):
        with open(g_file, 'w') as f:
            f.write('hallo')

    with pytest.raises(PermissionError):
        with open(g_file, 'w') as f:
            f.write('5.5\n5.3')

    open(g_file, 'w').write('\n__RESET__\n\n')

    with open(g_file, 'r') as f:
        assert f.read() == '5.5\n'

    with open(g_file, 'w') as f:
        assert f.write('5.5\n')

    with open(g_file, 'r') as f:
        assert f.read() == '5.5\n'

    with open(g_file, 'w') as f:
        pass

    with open(g_file, 'r') as f:
        assert f.read() == ''

    with pytest.raises(PermissionError):
        with open(g_file, 'w') as f:
            f.write('11.0\n')

    with open(g_file, 'w') as f:
        pass


@pytest.mark.parametrize(
    'data', ['hello\nThomas\n\nBye we', '', 'ss' * 80 + '\nsds']
)
def test_feedback_file(sub_done, data):
    f_file = join(sub_done, '.cg-feedback')
    with open(f_file, 'r') as f:
        assert f.read() == ''

    with open(f_file, 'w') as f:
        f.write(data)

    with open(f_file, 'r') as f:
        assert f.read() == data

    with open(f_file, 'w') as f:
        pass

    with open(f_file, 'r') as f:
        assert f.read() == ''

@pytest.mark.parametrize(
    'path', ['c++', 'c++/file.cpp'],
)
def test_quote_paths(sub_done, path):
    dirs = path.split('/')[:-1]
    if len(dirs):
        mkdir(join(sub_done, *dirs))

    f_path = join(sub_done, path)
    with open(join(sub_done, f_path), 'w') as f:
        assert f.write('abc') == 3

    tmp_path = join(sub_done, 'abc')
    rename([f_path], [tmp_path])
    assert not isfile(f_path)
    assert isfile(tmp_path)

    rename([tmp_path], [f_path])
    assert isfile(f_path)
    assert not isfile(tmp_path)

    rm(f_path)
    if len(dirs):
        rmdir(join(sub_done, *dirs))
