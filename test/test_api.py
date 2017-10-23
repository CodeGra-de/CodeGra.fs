import os
import re
import stat
import tarfile
import subprocess
import urllib.request

import pytest
import requests

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


@pytest.mark.parametrize(
    'data, res', [
        (
            b'# Header\nDescription\n----\n- (1.0) Item - Desc\n', (
                [('Header', 'Description', [(1.0, 'Item', 'Desc')])],
                '# \[{id}\] Header\n Description\n-+\n- '
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
                ], '# \[{id}\] Header\n Description\n-+\n- \[{id}\] \(1\.0\)'
                ' Item - Desc\n- \[{id}\] \(4\.0\) Item2 - Desc2\n'
            )
        ),
        (
            b'# Header\nDescription\n----\n- (1.0) Item - Desc\n- (4.0) Item2 '
            b'- Desc2\n\n# Header 2\nDescription 2\n------\n- (2.5) I - D\n   '
            b'C\n  \nA\n\n\nM\n', (
                [
                    (
                        'Header', 'Description',
                        [(1.0, 'Item', 'Desc'), (4.0, 'Item2', 'Desc2')]
                    ), (
                        'Header 2', 'Description 2', [
                            (2.5, 'I', 'D C\nA\n\nM'),
                        ]
                    )
                ], '# \[{id}\] Header\n Description\n-+\n- \[{id}\] \(1\.0\)'
                ' Item - Desc\n- \[{id}\] \(4\.0\) Item2 - Desc2\n\n#'
                ' \[{id}\] Header 2\n Description 2\n-+\n- \[{id}\] \(2\.5\) I'
                ' - D C\n\n  A\n\n\n  M\n'
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
    with open(r_file, 'r') as r:
        assert r.read() == ''

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

        rm(r_file)

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
                ], '# \[{id}\] Header\n Description\n-+\n- \[{id}\] \(1\.0\)'
                ' Item - Desc\n- \[{id}\] \(4\.0\) Item2 - Desc2\n'
            ), '- (5.0) Item4 - Desc4\n', (
                [
                    (
                        'Header', 'Description',
                        [(1.0, 'Item', 'Desc'), (5.0, 'Item4', 'Desc4')]
                    )
                ], '# \[{id}\] Header\n Description\n-+\n- \[{id}\] \(1\.0\)'
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
        rm(r_file)
        test_correct(res)
    else:
        with open(r_file, 'w') as f:
            f.write(read)
        test_correct(res_after)
