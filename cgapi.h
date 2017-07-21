#ifndef CGAPI_H
#define CGAPI_H

#include <stddef.h>

struct cgapi_assignment {
};

struct cgapi_submission {
};

struct cgapi_file {
	size_t buflen;
	char *buf;
};

struct cgapi_file_meta {
};

int cgapi_login(char *username, char *password);

int cgapi_mkdir(int submission_id, const char *path);

int cgapi_rmdir(int submission_id, const char *path);

int cgapi_get_assignments(struct cgapi_assignment *ass);

int cgapi_get_submissions(int assignment_id, struct cgapi_submission *subs);

int cgapi_get_submission_files(int submission_id, struct cgapi_file *files);

int cgapi_get_file_meta(int file_id, struct cgapi_file_meta *fm);

int cgapi_get_file_buf(int file_id, struct cgapi_file *f);

int cgapi_put_file_buf(struct cgapi_file *f);

int cgapi_unlink_file(struct cgapi_file *f);

#endif /* CGAPI_H */
