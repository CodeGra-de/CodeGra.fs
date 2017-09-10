# -*- coding: utf-8 -*-

from os import getenv
from enum import IntEnum

import requests

CGAPI_BASE_URL = getenv('CGAPI_BASE_URL', 'https://codegra.de/api/v1')


class APIRoutes():
    LOGIN = CGAPI_BASE_URL + '/login'
    COURSES = CGAPI_BASE_URL + '/courses/?extended=true'
    SUBMISSIONS = CGAPI_BASE_URL + '/assignments/{assignment_id}/submissions/'
    FILES = CGAPI_BASE_URL + '/submissions/{submission_id}/files/?owner=auto'
    FILE = CGAPI_BASE_URL + '/submissions/{submission_id}/files/?path={path}&owner=auto'
    FILE_BUF = CGAPI_BASE_URL + '/code/{file_id}'


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
        super(CGAPIException, self).__init__(data['message'])

        self.description = data['description']
        self.message = data['message']
        self.code = data['code']


class CGAPI():
    def __init__(self, username, password):
        r = requests.post(
            APIRoutes.LOGIN,
            json={
                'username': username,
                'password': password,
            }
        )

        if r.status_code >= 400:
            raise CGAPIException(r)

        self.access_token = r.json()['access_token']

    def get_default_headers(self):
        return {
            'Authorization': 'Bearer ' + self.access_token,
        }

    def get_courses(self):
        r = requests.get(APIRoutes.COURSES, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r)

        return r.json()

    def get_submissions(self, assignment_id):
        url = APIRoutes.SUBMISSIONS.format(assignment_id=assignment_id)
        r = requests.get(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r)

        return r.json()

    def get_submission_files(self, submission_id):
        url = APIRoutes.FILES.format(submission_id=submission_id)
        r = requests.get(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r)

        return r.json()

    def get_file_meta(self, submission_id, path):
        url = APIRoutes.FILE.format(submission_id=submission_id, path=path)
        r = requests.get(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r)

        return r.json()

    def create_file(self, submission_id, path, buf=None):
        url = APIRoutes.FILE.format(submission_id=submission_id, path=path)
        r = requests.post(url, headers=self.get_default_headers(), data=buf)

        if r.status_code >= 400:
            raise CGAPIException(r)

        return r.json()

    def get_file(self, file_id):
        url = APIRoutes.FILE_BUF.format(file_id=file_id)
        r = requests.get(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r)

        return r.text

    def patch_file(self, file_id, buf):
        url = APIRoutes.FILE_BUF.format(file_id=file_id)
        r = requests.patch(url, headers=self.get_default_headers(), data=buf)

        if r.status_code >= 400:
            raise CGAPIException(r)

        return r.json()

    def delete_file(self, file_id):
        url = APIRoutes.FILE_BUF.format(file_id=file_id)
        r = requests.delete(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r)
