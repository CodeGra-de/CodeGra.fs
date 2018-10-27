# -*- coding: utf-8 -*-
# SPDX-License-Identifier: AGPL-3.0-only

import typing as t
import logging
from enum import IntEnum
from functools import partial
from urllib.parse import quote

import requests

DEFAULT_CGAPI_BASE_URL = 'https://codegra.de/api/v1'

logger = logging.getLogger(__name__)


class APIRoutes():
    def __init__(self, base, owner='auto'):
        while base and base[-1] == '/':  # pragma: no cover
            base = base[:-1]

        self.owner = owner
        self.base = base

    def get_login(self):
        return '{base}/login'.format(base=self.base)

    def get_courses(self):
        return '{base}/courses/?extended=true'.format(base=self.base)

    def get_submissions(self, assignment_id):
        return '{base}/assignments/{assignment_id}/submissions/'.format(
            base=self.base, assignment_id=assignment_id
        )

    def get_files(self, submission_id: int) -> str:
        return ('{base}/submissions/{submission_id}'
                '/files/?owner={owner}').format(
                    base=self.base,
                    submission_id=submission_id,
                    owner=self.owner,
                )

    def get_file(self, submission_id: int, path: str) -> str:
        return (
            '{base}/submissions/{submission_id}/'
            'files/?path={path}&owner={owner}'
        ).format(
            base=self.base,
            submission_id=submission_id,
            path=quote(path),
            owner=self.owner
        )

    def get_file_buf(self, file_id):
        return '{base}/code/{file_id}'.format(base=self.base, file_id=file_id)

    def select_rubricitems(self, submission_id):
        return '{base}/submissions/{submission_id}/rubricitems/'.format(
            base=self.base, submission_id=submission_id
        )

    def get_submission_rubric(self, submission_id):
        return '{base}/submissions/{submission_id}/rubrics/'.format(
            base=self.base, submission_id=submission_id
        )

    def get_submission(self, submission_id):
        return '{base}/submissions/{submission_id}'.format(
            base=self.base, submission_id=submission_id
        )

    set_submission = get_submission

    def get_assignment_rubric(self, assignment_id):
        return '{base}/assignments/{assignment_id}/rubrics/'.format(
            base=self.base, assignment_id=assignment_id
        )

    def get_file_rename(self, file_id, new_path):
        return (
            '{base}/code/{file_id}?operation='
            'rename&new_path={new_path}'
        ).format(
            base=self.base, file_id=file_id, new_path=quote(new_path)
        )

    def get_feedbacks(self, assignment_id):
        return '{base}/assignments/{assignment_id}/feedbacks/'.format(
            base=self.base, assignment_id=assignment_id
        )

    def get_feedback(self, file_id):
        return ('{base}/code/{file_id}?type=feedback').format(
            base=self.base, file_id=file_id
        )

    def add_feedback(self, file_id, line):
        return ('{base}/code/{file_id}/comments/{line}').format(
            base=self.base, file_id=file_id, line=line
        )

    delete_feedback = add_feedback

    def get_assignment(self, assignment_id):
        return ('{base}/assignments/{assignment_id}').format(
            base=self.base, assignment_id=assignment_id
        )


class APICodes(IntEnum):
    """Internal API codes that are used by :class:`APIException` objects.
    """
    INCORRECT_PERMISSION = 0
    NOT_LOGGED_IN = 1
    OBJECT_ID_NOT_FOUND = 2
    OBJECT_WRONG_TYPE = 3
    MISSING_REQUIRED_PARAM = 4
    INVALID_PARAM = 5
    REQUEST_TOO_LARGE = 6
    LOGIN_FAILURE = 7
    INACTIVE_USER = 8
    INVALID_URL = 9
    OBJECT_NOT_FOUND = 10
    BLOCKED_ASSIGNMENT = 11
    INVALID_CREDENTIALS = 12
    INVALID_STATE = 13
    INVALID_OAUTH_REQUEST = 14
    DISABLED_FEATURE = 15


class CGAPIException(Exception):
    def __init__(self, response):
        data = response.json()
        super().__init__(data['message'])

        self.status_code = response.status_code
        self.description = data['description']
        self.message = data['message']
        self.code = data['code']

    def __str__(self):  # pragma: no cover
        return 'codegra_fs.cgapi.CGAPIException: {} - {} [{}]'.format(
            self.message, self.description, self.code
        )


class CGAPI():
    def __init__(
        self,
        username: str,
        password: str,
        base: t.Optional[str]=None,
        fixed: bool=False
    ) -> None:
        owner = 'student' if fixed else 'auto'
        self.routes = APIRoutes(base or DEFAULT_CGAPI_BASE_URL, owner)

        r = requests.post(
            self.routes.get_login(),
            json={
                'username': username,
                'password': password,
            }
        )

        self._handle_response_error(r)
        json = r.json()

        self.user = json['user']
        self.access_token = json['access_token']
        self.s = requests.Session()
        self.fixed = fixed

        self.s.headers = {
            'Authorization': 'Bearer ' + self.access_token,
        }
        self.s.get = partial(self.s.get, timeout=3)  # type: ignore
        self.s.patch = partial(self.s.patch, timeout=3)  # type: ignore
        self.s.post = partial(self.s.post, timeout=3)  # type: ignore
        self.s.delete = partial(self.s.delete, timeout=3)  # type: ignore
        self.s.put = partial(self.s.put, timeout=3)  # type: ignore

    def _handle_response_error(self, request):
        if request.status_code >= 400:
            raise CGAPIException(request)

    def get_courses(self):
        r = self.s.get(self.routes.get_courses())

        self._handle_response_error(r)

        return r.json()

    def get_submissions(self, assignment_id):
        url = self.routes.get_submissions(assignment_id=assignment_id)
        r = self.s.get(url)

        self._handle_response_error(r)

        return r.json()

    def get_submission_files(self, submission_id):
        url = self.routes.get_files(submission_id=submission_id)
        r = self.s.get(url)

        self._handle_response_error(r)

        return r.json()

    def get_file_meta(self, submission_id, path):
        url = self.routes.get_file(submission_id=submission_id, path=path)
        r = self.s.get(url)

        self._handle_response_error(r)

        return r.json()

    def create_file(self, submission_id, path, buf=None):
        url = self.routes.get_file(submission_id=submission_id, path=path)
        r = self.s.post(url, data=buf)

        self._handle_response_error(r)

        return r.json()

    def rename_file(self, file_id, new_path):
        url = self.routes.get_file_rename(file_id=file_id, new_path=new_path)
        r = self.s.patch(url)

        self._handle_response_error(r)

        return r.json()

    def get_file(self, file_id: int) -> bytes:
        url = self.routes.get_file_buf(file_id=file_id)
        r = self.s.get(url)

        self._handle_response_error(r)

        return r.content

    def patch_file(self, file_id: int, buf: bytes) -> t.Dict[str, t.Any]:
        url = self.routes.get_file_buf(file_id=file_id)
        r = self.s.patch(url, data=buf)

        self._handle_response_error(r)

        return r.json()

    def delete_file(self, file_id):
        url = self.routes.get_file_buf(file_id=file_id)
        r = self.s.delete(url)

        self._handle_response_error(r)

    def get_assignment_rubric(self, assignment_id):
        url = self.routes.get_assignment_rubric(assignment_id)
        r = self.s.get(url)
        if r.status_code == 404:
            return []

        self._handle_response_error(r)

        return r.json()

    def set_assignment_rubric(self, assignment_id, rub):
        url = self.routes.get_assignment_rubric(assignment_id)
        r = self.s.put(url, json=rub)
        self._handle_response_error(r)

    def get_submission_rubric(self, submission_id):
        url = self.routes.get_submission_rubric(submission_id)
        r = self.s.get(url)

        if r.status_code == 404:
            return {'rubrics': [], 'selected': []}

        self._handle_response_error(r)

        return r.json()

    def select_rubricitems(self, submission_id, items):
        url = self.routes.select_rubricitems(submission_id)
        r = self.s.patch(url, json={'items': items})
        self._handle_response_error(r)

    def get_feedbacks(self, assignment_id):
        url = self.routes.get_feedbacks(assignment_id)
        r = self.s.get(url)

        self._handle_response_error(r)

        return r.json()

    def add_feedback(self, file_id, line, message):
        url = self.routes.add_feedback(file_id, line)
        r = self.s.put(url, json={'comment': message})

        self._handle_response_error(r)

    def delete_feedback(self, file_id, line):
        url = self.routes.delete_feedback(file_id=file_id, line=line)
        r = self.s.delete(url)

        self._handle_response_error(r)

    def get_feedback(self, file_id):
        url = self.routes.get_feedback(file_id)
        r = self.s.get(url)

        self._handle_response_error(r)

        return r.json()

    def get_assignment(self, assignment_id):
        url = self.routes.get_assignment(assignment_id=assignment_id)
        r = self.s.get(url)

        self._handle_response_error(r)

        return r.json()

    def set_assignment(self, assignment_id, settings):
        url = self.routes.get_assignment(assignment_id=assignment_id)
        r = self.s.patch(url, json=settings)

        self._handle_response_error(r)

    def get_submission(self, submission_id):
        url = self.routes.get_submission(submission_id)
        r = self.s.get(url)

        self._handle_response_error(r)

        return r.json()

    def set_submission(
        self,
        submission_id: int,
        grade: t.Union[None, float, str]=None,
        feedback: t.Optional[bytes]=None
    ):
        url = self.routes.set_submission(submission_id)
        d = {}  # type: t.Dict[str, t.Union[bytes, float, None]]
        if grade is not None:
            if grade == 'delete':
                d['grade'] = None
            else:
                assert not isinstance(grade, str)
                d['grade'] = grade

        if feedback is not None:
            d['feedback'] = feedback
        r = self.s.patch(url, json=d)

        self._handle_response_error(r)
