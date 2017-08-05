#include "cgapi.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <curl/curl.h>

#include <jansson.h>

#define UNUSED(x) (void)(x);

#define MAX(x, y) ((x) > (y) ? (x) : (y))
#define MIN(x, y) ((x) < (y) ? (x) : (y))

#ifndef BASE_URL
#define BASE_URL "https://codegra.de/api/v1"
#endif

enum req_type {
        REQ_LOGIN,
        REQ_ASSIGNMENTS,
        REQ_SUBMISSIONS,
        REQ_FILES,
};

static const char *api_routes[] = {
                [REQ_LOGIN] = BASE_URL "/login",
                [REQ_ASSIGNMENTS] = BASE_URL "/assignments/",
                [REQ_SUBMISSIONS] = BASE_URL "/assignments/%u/submissions/",
                [REQ_FILES] = BASE_URL "/submissions/%u/files/%s?revision=auto",
};

struct cgapi_token {
        size_t len;
        char str[];
};

struct buf {
        size_t len;
        size_t pos;
        char *str;
};

struct cgapi_handle {
        CURL *curl;
        struct curl_slist *headers;
};

/*
 * Serialization functions to serialize common data
 */

static const char *serialize_user(const char *email, const char *password)
{
        const char *json = NULL;
        json_t *j_user;
        json_t *j_email;
        json_t *j_password;

        if ((j_email = json_string(email)) == NULL)
                goto email_failed;
        if ((j_password = json_string(password)) == NULL)
                goto password_failed;
        if ((j_user = json_object()) == NULL)
                goto user_failed;
        if (json_object_set(j_user, "email", j_email) < 0)
                goto serialize_failed;
        if (json_object_set(j_user, "password", j_password) < 0)
                goto serialize_failed;

        json = json_dumps(j_user, JSON_COMPACT);

serialize_failed:
        json_decref(j_user);
user_failed:
        json_decref(j_password);
password_failed:
        json_decref(j_email);
email_failed:
        return json;
}

static void cgapi_cleanup_request(struct cgapi_handle h)
{
        curl_slist_free_all(h.headers);
        curl_easy_cleanup(h.curl);
        h.headers = h.curl = NULL;
}

static struct cgapi_handle cgapi_init_request(const char *url)
{
        struct cgapi_handle h = {
                .curl = NULL,
                .headers = NULL,
        };

        h.curl = curl_easy_init();
        if (!h.curl)
                return h;

        curl_easy_setopt(h.curl, CURLOPT_HEADER, 1L);
        curl_easy_setopt(h.curl, CURLOPT_URL, url);
        curl_easy_setopt(h.curl, CURLOPT_FOLLOWLOCATION, 1L);
#ifndef NDEBUG
        curl_easy_setopt(h.curl, CURLOPT_VERBOSE, 1L);
#endif

#define ADD_DEFAULT_HEADER(handle, header) \
        do { \
                struct curl_slist *tmplist = curl_slist_append(handle.headers, header); \
                if (tmplist == NULL) { \
                        cgapi_cleanup_request(handle); \
                        return handle; \
                } \
                handle.headers = tmplist; \
        } while (0)

        ADD_DEFAULT_HEADER(h, "Content-Type: application/json");

#undef ADD_HEADER

        return h;
}

static size_t cgapi_write_response(char *ptr, size_t size, size_t nmemb, void *udata)
{
        struct buf *b = udata;
        if (b->pos + size * nmemb > b->len) {
                char *rstr = realloc(b->str, MAX(2 * b->len, b->pos + size * nmemb));
                if (rstr == NULL) {
                        return 0;
                }
                b->str = rstr;
        }

        memcpy(b->str, ptr, size * nmemb);
        b->pos += size * nmemb;
        return size * nmemb;
}

// Returns response string.
static char *cgapi_do_request(struct cgapi_handle h)
{
        struct buf res = {
                .len = 0,
                .pos = 0,
                .str = NULL,
        };

        curl_easy_setopt(h.curl, CURLOPT_HTTPHEADER, h.headers);
        curl_easy_setopt(h.curl, CURLOPT_WRITEFUNCTION, cgapi_write_response);
        curl_easy_setopt(h.curl, CURLOPT_WRITEDATA, &res);

        CURLcode code = curl_easy_perform(h.curl);

        if (code != CURLE_OK) {
                // handle errors
                free(res.str);
                res.str = NULL;
        }

        return res.str;
}

cgapi_token_t cgapi_login(const char *email, const char *password)
{
        cgapi_token_t tok = NULL;

        struct cgapi_handle h = cgapi_init_request(api_routes[REQ_LOGIN]);
        if (h.curl == NULL) goto curl_init_failed;

        const char *user = serialize_user(email, password);
        if (user == NULL) goto serialize_failed;

        curl_easy_setopt(h.curl, CURLOPT_POST, 1);
        curl_easy_setopt(h.curl, CURLOPT_POSTFIELDS, user);

        char *res = cgapi_do_request(h);
        if (res == NULL) goto request_failed;

        json_error_t err;
        json_t *j_res = json_loads(res, 0, &err);
        if (j_res == NULL) goto parse_res_failed;

        // validate j_res (is it an object, does it have correct keys etc.)
        json_t *token = json_object_get(j_res, "access_token");
        if (token == NULL || !json_is_string(token)) goto invalid_json;
        const char *data = json_string_value(token);
        if (data == NULL) goto invalid_json;

        size_t toklen = json_string_length(token);
        tok = malloc(sizeof(*tok) + toklen + 1);
        if (tok != NULL) {
                memcpy(tok->str, data, toklen);
                tok->str[toklen] = '\0';
                tok->len = toklen;
        }

invalid_json:
        json_decref(j_res);
parse_res_failed:
        free(res);
request_failed:
        free((char *) user);
serialize_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
        return tok;
}

// TODO: Send mkdir request to server
int cgapi_mkdir(cgapi_token_t tok, int submission_id, const char *path)
{
        UNUSED(tok);
        UNUSED(submission_id);
        UNUSED(path);
        return 0;
}

// TODO: Send rmdir request to server
int cgapi_rmdir(cgapi_token_t tok, int submission_id, const char *path)
{
        UNUSED(tok);
        UNUSED(submission_id);
        UNUSED(path);
        return 0;
}

// TODO: Get assignments
int cgapi_get_assignments(cgapi_token_t tok, struct cgapi_assignment *ass)
{
        UNUSED(tok);
        UNUSED(ass);
        return 0;
}

// TODO: Get Submissions
int cgapi_get_submissions(cgapi_token_t tok, int assignment_id,
                          struct cgapi_submission *subs)
{
        UNUSED(tok);
        UNUSED(assignment_id);
        UNUSED(subs);
        return 0;
}

// TODO: Get submission files
int cgapi_get_submission_files(cgapi_token_t tok, int submission_id,
                               struct cgapi_file *files)
{
        UNUSED(tok);
        UNUSED(submission_id);
        UNUSED(files);
        return 0;
}

// TODO: Get other info from server
int cgapi_get_file_meta(cgapi_token_t tok, int file_id,
                        struct cgapi_file_meta *fm)
{
        UNUSED(tok);
        UNUSED(file_id);
        UNUSED(fm);
        return 0;
}

// TODO: Get data from server
int cgapi_get_file_buf(cgapi_token_t tok, int file_id, struct cgapi_file *f)
{
        UNUSED(tok);
        UNUSED(file_id);
        UNUSED(f);
        // f->buf = ...
        return 0;
}

// TODO: Send f->buf to server
int cgapi_put_file_buf(cgapi_token_t tok, struct cgapi_file *f)
{
        UNUSED(tok);
        UNUSED(f);
        return 0;
}

// TODO: Send unlink request to server
int cgapi_unlink_file(cgapi_token_t tok, struct cgapi_file *f)
{
        UNUSED(tok);
        UNUSED(f);
        return 0;
}
