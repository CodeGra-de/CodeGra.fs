#ifndef CGAPI_H
#define CGAPI_H

#include <jansson.h>
#include <stddef.h>

struct cgapi_token;
typedef struct cgapi_token *cgapi_token_t;

cgapi_token_t cgapi_login(const char *email, const char *password);

int cgapi_get_courses(cgapi_token_t tok, json_t **courses);

int cgapi_get_submissions(cgapi_token_t tok, int assignment_id,
                          json_t **submissions);

int cgapi_get_submission_files(cgapi_token_t tok, int submission_id,
                               json_t **files);

int cgapi_get_file_meta(cgapi_token_t tok, unsigned submission_id,
                        const char *path, json_t *file);

int cgapi_get_file_buf(cgapi_token_t tok, unsigned submission_id,
                       const char *path, json_t *file);

int cgapi_patch_file_buf(cgapi_token_t tok, json_t *file);

int cgapi_post_file(cgapi_token_t tok, unsigned submission_id, const char *path,
                    int is_directory, const char *buf);

int cgapi_delete_file(cgapi_token_t tok, json_t *file);

#endif /* CGAPI_H */
