#ifndef CGAPI_H
#define CGAPI_H

#include <stddef.h>

struct cgapi_token;
typedef struct cgapi_token *cgapi_token_t;

struct cgapi_assignment {
        int id;
        size_t namelen;
        char *name;
};

struct cgapi_submission {
        int id;
        size_t namelen;
        char *name;
};

struct cgapi_file {
        size_t buflen;
        char *buf;
};

struct cgapi_file_meta {
        int id;
};

cgapi_token_t cgapi_login(const char *email, const char *password);

int cgapi_get_assignments(cgapi_token_t tok,
                          struct cgapi_assignment **assignments);

int cgapi_get_submissions(cgapi_token_t tok, int assignment_id,
                          struct cgapi_submission **submissions);

int cgapi_get_submission_files(cgapi_token_t tok, int submission_id,
                               const char *path, struct cgapi_file **files);

int cgapi_get_file_meta(cgapi_token_t tok, unsigned submission_id,
                        const char *path, struct cgapi_file_meta *fm);

int cgapi_get_file_buf(cgapi_token_t tok, unsigned submission_id,
                       const char *path, struct cgapi_file *f);

int cgapi_put_file_buf(cgapi_token_t tok, unsigned submission_id,
                       const char *path, struct cgapi_file *f);

int cgapi_unlink_file(cgapi_token_t tok, struct cgapi_file *f);

#endif /* CGAPI_H */
