#ifndef CGAPI_H
#define CGAPI_H

#include <stddef.h>

struct cgapi_token;
typedef struct cgapi_token *cgapi_token;

struct cgapi_user {
        char *email;
        char *password;
};

struct cgapi_assignment {
        int id;
};

struct cgapi_submission {
        int id;
};

struct cgapi_file {
        size_t buflen;
        char *buf;
};

struct cgapi_file_meta {
        int id;
};

int cgapi_init(void);

cgapi_token cgapi_login(const char *email, const char *password);

int cgapi_mkdir(cgapi_token tok, int submission_id, const char *path);

int cgapi_rmdir(cgapi_token tok, int submission_id, const char *path);

int cgapi_get_assignments(cgapi_token tok, struct cgapi_assignment *ass);

int cgapi_get_submissions(cgapi_token tok, int assignment_id, struct cgapi_submission *subs);

int cgapi_get_submission_files(cgapi_token tok, int submission_id, struct cgapi_file *files);

int cgapi_get_file_meta(cgapi_token tok, int file_id, struct cgapi_file_meta *fm);

int cgapi_get_file_buf(cgapi_token tok, int file_id, struct cgapi_file *f);

int cgapi_put_file_buf(cgapi_token tok, struct cgapi_file *f);

int cgapi_unlink_file(cgapi_token tok, struct cgapi_file *f);

#endif /* CGAPI_H */
