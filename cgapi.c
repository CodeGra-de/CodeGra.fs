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

int cgapi_init(void)
{
        // Do global curl setup
        return 0;
}

int cgapi_deinit(void)
{
        // Do global curl cleanup
        return 0;
}

static size_t cgapi_read_data(char *ptr, size_t size, size_t nmemb, void *udata)
{
        struct buf *b = udata;
        if (b->pos >= b->len) {
                return 0;
        }

        size_t nbytes = MIN(size * nmemb, b->len - b->pos);
        memcpy(ptr, b->str + b->pos, nbytes);
        b->pos += nbytes;

        return nbytes;
}

static CURL *cgapi_init_request(const char *url)
{
        CURL *curl = curl_easy_init();
        if (!curl) {
                return NULL;
        }

        curl_easy_setopt(curl, CURLOPT_HEADER, 1L);
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
#ifndef NDEBUG
        curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);
#endif
        curl_easy_setopt(curl, CURLOPT_READFUNCTION, cgapi_read_data);
        // May be overridden, in which case it should be a pointer to
        // a `struct buf` whose `pos` is equal to `0`
        curl_easy_setopt(curl, CURLOPT_READDATA, NULL);

        // Set default headers & auth stuff

        return curl;
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
static char *cgapi_do_request(CURL *curl)
{
        struct buf res = {
                .len = 0,
                .pos = 0,
                .str = malloc(1 << 16),
        };

        if (res.str == NULL) {
                return NULL;
        }

        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, cgapi_write_response);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &res);

        CURLcode code = curl_easy_perform(curl);
        if (code != CURLE_OK) {
                // handle errors
                free(res.str);
                res.str = NULL;
        }

        return res.str;
}

cgapi_token cgapi_login(const char *email, const char *password)
{
        cgapi_token tok = NULL;

        CURL *curl = cgapi_init_request(api_routes[REQ_LOGIN]);
        if (curl == NULL)
                goto curl_init_failed;

        const char *user = serialize_user(email, password);
        if (user == NULL)
                goto serialize_failed;

        curl_easy_setopt(curl, CURLOPT_POST, 1);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, user);

        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        char *res = cgapi_do_request(curl);
        if (res == NULL)
                goto request_failed;

        curl_slist_free_all(headers);

        json_error_t err;
        json_t *j_res = json_loads(res, 0, &err);
        if (j_res == NULL)
                goto parse_res_failed;

        // validate j_res (is it an object, does it have correct keys etc.)
        json_t *token = json_object_get(j_res, "access_token");
        if (token == NULL || !json_is_string(token))
                goto invalid_json;
        const char *data = json_string_value(token);
        if (data == NULL)
                goto invalid_json;

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
        curl_easy_cleanup(curl);
curl_init_failed:
        return tok;
}

// TODO: Send mkdir request to server
int cgapi_mkdir(cgapi_token tok, int submission_id, const char *path)
{
        UNUSED(tok);
        UNUSED(submission_id);
        UNUSED(path);
        return 0;
}

// TODO: Send rmdir request to server
int cgapi_rmdir(cgapi_token tok, int submission_id, const char *path)
{
        UNUSED(tok);
        UNUSED(submission_id);
        UNUSED(path);
        return 0;
}

// TODO: Get assignments
int cgapi_get_assignments(cgapi_token tok, struct cgapi_assignment *ass)
{
        UNUSED(tok);
        UNUSED(ass);
        return 0;
}

// TODO: Get Submissions
int cgapi_get_submissions(cgapi_token tok, int assignment_id,
                          struct cgapi_submission *subs)
{
        UNUSED(tok);
        UNUSED(assignment_id);
        UNUSED(subs);
        return 0;
}

// TODO: Get submission files
int cgapi_get_submission_files(cgapi_token tok, int submission_id,
                               struct cgapi_file *files)
{
        UNUSED(tok);
        UNUSED(submission_id);
        UNUSED(files);
        return 0;
}

// TODO: Get other info from server
int cgapi_get_file_meta(cgapi_token tok, int file_id,
                        struct cgapi_file_meta *fm)
{
        UNUSED(tok);
        UNUSED(file_id);
        UNUSED(fm);
        return 0;
}

// TODO: Get data from server
int cgapi_get_file_buf(cgapi_token tok, int file_id, struct cgapi_file *f)
{
        UNUSED(tok);
        UNUSED(file_id);
        UNUSED(f);
        // f->buf = ...
        return 0;
}

// TODO: Send f->buf to server
int cgapi_put_file_buf(cgapi_token tok, struct cgapi_file *f)
{
        UNUSED(tok);
        UNUSED(f);
        return 0;
}

// TODO: Send unlink request to server
int cgapi_unlink_file(cgapi_token tok, struct cgapi_file *f)
{
        UNUSED(tok);
        UNUSED(f);
        return 0;
}
