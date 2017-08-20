#include "cgapi.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <curl/curl.h>

#include <jansson.h>

#define UNUSED(x) (void)(x);

#define MAX(x, y) ((x) > (y) ? (x) : (y))
#define MIN(x, y) ((x) < (y) ? (x) : (y))

#define URL_MAX 1024

#ifndef BASE_URL
#define BASE_URL "https://codegra.de/api/v1"
#endif

enum req_type {
        REQ_LOGIN,
        REQ_ASSIGNMENTS,
        REQ_SUBMISSIONS,
        REQ_FILES,
        REQ_FILE,
        REQ_FILE_META,
};

static const char *api_routes[] = {
                [REQ_LOGIN] = BASE_URL "/login",
                [REQ_ASSIGNMENTS] = BASE_URL "/assignments/",
                [REQ_SUBMISSIONS] = BASE_URL "/assignments/%u/submissions/",
                [REQ_FILES] = BASE_URL "/submissions/%u/files/",
                [REQ_FILE] = BASE_URL "/submissions/%u/files/%s?revision=auto",
                [REQ_FILE_META] = BASE_URL "/submissions/%u/files/%s?type=stat",
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

        if ((j_email = json_string(email)) == NULL) goto email_failed;
        if ((j_password = json_string(password)) == NULL) goto password_failed;
        if ((j_user = json_object()) == NULL) goto user_failed;
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

static int deserialize_assignment(json_t *j_data, struct cgapi_assignment *assignment)
{
        if (!json_is_object(j_data)) return -1;

        json_t *j_id = json_object_get(j_data, "id");
        // ...

        assignment->id = json_integer_value(j_id);
        // ...

        return 0;
}

// Deserialize an assignments array as returned by the server and store in newly allocated
// memory in *assignments. Returns the size of the array, or a negative int when an error
// occurred.
static int deserialize_assignments(struct buf *data, struct cgapi_assignment **assignments)
{
        int ret = -1;
        *assignments = NULL;

        json_error_t err;
        json_t *j_data = json_loads(data->str + data->pos, 0, &err);
        if (j_data == NULL || !json_is_array(j_data)) goto parse_json_failed;

        size_t nass = json_array_size(j_data);
        if (nass == 0) goto array_empty;

        *assignments = malloc(nass * sizeof(**assignments));
        if (*assignments == NULL) goto malloc_failed;

        for (size_t i = 0; i < nass; i++) {
                deserialize_assignment(json_array_get(j_data, i), *assignments + i);
        }

array_empty:
        ret = nass;
malloc_failed:
        json_decref(j_data);
parse_json_failed:
        return ret;
}

static int deserialize_submissions(struct buf *data, struct cgapi_submission **submissions)
{
        UNUSED(data);
        UNUSED(submissions);
        return 0;
}

static int deserialize_files(struct buf *data, struct cgapi_file **files)
{
        UNUSED(data);
        UNUSED(files);
        return 0;
}

static void cgapi_cleanup_request(struct cgapi_handle h)
{
        curl_slist_free_all(h.headers);
        curl_easy_cleanup(h.curl);
        h.headers = h.curl = NULL;
}

static struct cgapi_handle cgapi_init_request(cgapi_token_t tok,
                                              const char *url)
{
        struct cgapi_handle h = {
                .curl = NULL, .headers = NULL,
        };

        h.curl = curl_easy_init();
        if (!h.curl) return h;

        curl_easy_setopt(h.curl, CURLOPT_HEADER, 1L);
        curl_easy_setopt(h.curl, CURLOPT_URL, url);
        curl_easy_setopt(h.curl, CURLOPT_FOLLOWLOCATION, 1L);
#ifndef NDEBUG
        curl_easy_setopt(h.curl, CURLOPT_VERBOSE, 0L);
#endif

#define ADD_DEFAULT_HEADER(handle, header)                                     \
        do {                                                                   \
                struct curl_slist *tmplist =                                   \
                        curl_slist_append((handle).headers, (header));         \
                if (tmplist == NULL) {                                         \
                        cgapi_cleanup_request((handle));                       \
                        return (handle);                                       \
                }                                                              \
                (handle).headers = tmplist;                                    \
        } while (0)

        ADD_DEFAULT_HEADER(h, "Content-Type: application/json");
        if (tok != NULL) ADD_DEFAULT_HEADER(h, tok->str);

#undef ADD_DEFAULT_HEADER

        return h;
}

static size_t cgapi_write_response(char *ptr, size_t size, size_t nmemb,
                                   void *udata)
{
        struct buf *b = udata;
        if (b->pos + size * nmemb + 1 > b->len) {
                char *rstr = realloc(
                        b->str, MAX(2 * b->len, b->pos + size * nmemb + 1));
                if (rstr == NULL) {
                        return 0;
                }
                b->str = rstr;
        }

        memcpy(b->str + b->pos, ptr, size * nmemb);
        b->pos += size * nmemb;
        b->str[b->pos] = '\0';
        return size * nmemb;
}

// Returns response string as a `struct buf` with `pos` set to the start of
// the response body.
int cgapi_do_request(struct cgapi_handle h, struct buf *res)
{
        *res = (struct buf){
                .len = 0, .pos = 0, .str = NULL,
        };

        curl_easy_setopt(h.curl, CURLOPT_HTTPHEADER, h.headers);
        curl_easy_setopt(h.curl, CURLOPT_WRITEFUNCTION, cgapi_write_response);
        curl_easy_setopt(h.curl, CURLOPT_WRITEDATA, res);

        CURLcode code = curl_easy_perform(h.curl);

        if (code != CURLE_OK) {
                // handle errors
                free(res->str);
                res->str = NULL;
                goto request_failed;
        }

        res->len = res->pos;

        // Find start of response body (i.e. two consecutive newlines).
        char *match = strstr(res->str, "\r\n\r\n");
        if (match) res->pos = match - res->str + 4;

request_failed:
        return -code;
}

cgapi_token_t cgapi_login(const char *email, const char *password)
{
        cgapi_token_t tok = NULL;

        struct cgapi_handle h = cgapi_init_request(NULL, api_routes[REQ_LOGIN]);
        if (h.curl == NULL) goto curl_init_failed;

        const char *user = serialize_user(email, password);
        if (user == NULL) goto serialize_failed;

        curl_easy_setopt(h.curl, CURLOPT_POST, 1L);
        curl_easy_setopt(h.curl, CURLOPT_POSTFIELDS, user);

        struct buf res;
        int code = cgapi_do_request(h, &res);
        if (code) goto request_failed;

        json_error_t err;
        json_t *j_res = json_loads(res.str + res.pos, 0, &err);
        if (j_res == NULL) goto parse_json_failed;

        json_t *token = json_object_get(j_res, "access_token");
        if (token == NULL) goto invalid_response;
        const char *data = json_string_value(token);
        if (data == NULL) goto invalid_response;

// Store as HTTP header: Jwt: <token>
#define JWT_HEADER "Jwt: "
        size_t toklen = strlen(JWT_HEADER) + json_string_length(token) + 1;
        tok = malloc(sizeof(*tok) + toklen);
        if (tok != NULL) {
                tok->len = snprintf(tok->str, toklen, JWT_HEADER "%s", data);
        }
#undef JWT_HEADER

invalid_response:
        json_decref(j_res);
parse_json_failed:
        free((char *)res.str);
request_failed:
        free((char *)user);
serialize_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
        return tok;
}

void cgapi_logout(cgapi_token_t tok) { free(tok); }

int cgapi_make_submission(cgapi_token_t tok, unsigned assignment_id)
{
        int ret = -1;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_SUBMISSIONS],
                                 assignment_id);
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        ret = 0;

        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

int cgapi_get_assignments(cgapi_token_t tok,
                          struct cgapi_assignment **assignments)
{
        int ret = -1;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_ASSIGNMENTS]);
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        // TODO: Parse response
        deserialize_assignments(&res, assignments);

        ret = 0;

        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

int cgapi_get_submissions(cgapi_token_t tok, int assignment_id,
                          struct cgapi_submission **submissions)
{
        int ret = -1;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_SUBMISSIONS],
                                 assignment_id);
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        // TODO: Parse response
        deserialize_submissions(&res, submissions);

        ret = 0;

        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

int cgapi_get_submission_files(cgapi_token_t tok, int submission_id,
                               const char *path, struct cgapi_file **files)
{
        int ret = -1;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_FILES],
                                 submission_id, path);
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        // TODO: Parse response
        deserialize_files(&res, files);

        ret = 0;

        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

int cgapi_get_file_meta(cgapi_token_t tok, unsigned submission_id,
                        const char *path, struct cgapi_file_meta *fm)
{
        int ret = -1;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_FILE_META],
                                 submission_id, path);
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        json_error_t err;
        json_t *j_res = json_loads(res.str + res.pos, 0, &err);
        if (j_res == NULL) goto parse_json_failed;

        json_t *j_id = json_object_get(j_res, "id");
        if (j_id == NULL) goto invalid_response;
        fm->id = json_integer_value(j_id);
        if (fm->id == 0) goto invalid_id;

        ret = 0;

invalid_id:
        json_decref(j_id);
invalid_response:
        json_decref(j_res);
parse_json_failed:
        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

int cgapi_get_file_buf(cgapi_token_t tok, unsigned submission_id,
                       const char *path, struct cgapi_file *f)
{
        int ret = -1;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_FILE],
                                 submission_id, path);
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        size_t buflen = res.len - res.pos;
        f->buf = malloc(buflen + 1);
        if (f->buf == NULL) goto malloc_failed;
        memcpy(f->buf, res.str + res.pos, buflen);
        f->buf[buflen] = '\0';

        ret = 0;

malloc_failed:
        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

int cgapi_put_file_buf(cgapi_token_t tok, unsigned submission_id,
                       const char *path, struct cgapi_file *f)
{
        int ret = -1;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_FILES],
                                 submission_id, path);
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        curl_easy_setopt(h.curl, CURLOPT_CUSTOMREQUEST, "PUT");
        curl_easy_setopt(h.curl, CURLOPT_POSTFIELDS, f->buf);

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        ret = 0;

        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

// TODO: Send unlink request to server
int cgapi_unlink_file(cgapi_token_t tok, struct cgapi_file *f)
{
        UNUSED(tok);
        UNUSED(f);
        return 0;
}
