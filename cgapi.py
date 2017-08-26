from enum import Enum

import requests

CGFS_BASE_URL = getenv('CGFS_BASE_URL', 'https://codegra.de/api/v1')

class APIRoutes(Enum):
    LOGIN       = CGFS_BASE_URL + '/login'
    COURSES     = CGFS_BASE_URL + '/courses/?extended=true'
    SUBMISSIONS = CGFS_BASE_URL + '/assignments/%u/submissions/'
    FILES       = CGFS_BASE_URL + '/submissions/%u/files/?path=%s&is_directory=%s&owner=auto'
    FILE_META   = CGFS_BASE_URL + '/submissions/%u/files/?path=%s'
    FILE        = CGFS_BASE_URL + '/code/%u'


class CGAPIException(Exception):
    pass

class CGAPI():
    def __init__(self, user, password):
        r = requests.post(APIRoutes.LOGIN, json={
            'email': user,
            'password': password,
        })

        if r.status_code >= 400:
            raise CGAPIException(r.response.data.message)

        json = r.json()
        self.access_token = r.json()['access_token']

    def get_default_headers(self):
        return {
            'Authorization': 'Bearer ' + self.access_token,
        }

    def get_courses(self):
        r = requests.get(APIRoutes.COURSES, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r.response.data.message)

        return r.json()

    def get_submissions(self, assignment_id):
        url = APIRoutes.SUBMISSIONS % (assignment_id)
        r = requests.get(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r.response.data.message)

        return r.json()

    def get_submission_files(self, submission_id):
        url = APIRoutes.FILES % (submission_id)
        r = requests.get(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r.response.data.message)

        return r.json()

    def get_file_meta(self, submission_id, path):
        url = APIRoutes.FILE_META % (submission_id, path)
        r = requests.get(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r.response.data.message)

        return r.json()

    def create_file(self, submission_id, path, is_directory, buf):
        url = APIRoutes.FILES % (submission_id, path, is_directory)
        headers = self.get_default_headers()
        del headers['Content-Type']
        r = requests.post(url, headers=headers, data=buf)

        if r.status_code >= 400:
            raise CGAPIException(r.response.data.message)

        return r.json()

    def get_file(self, file_id):
        url = APIRoutes.FILE % (file_id)
        r = requests.get(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r.response.data.message)

        return r.text

    def patch_file(self, file_id):
        url = APIRoutes.FILE % (file_id)
        r = request.patch(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r.response.data.message)

    def delete_file(self, file_id):
        url = APIRoutes.FILE % (file_id)
        r = request.delete(url, headers=self.get_default_headers())

        if r.status_code >= 400:
            raise CGAPIException(r.response.data.message)
