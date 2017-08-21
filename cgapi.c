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
        REQ_COURSES,
        REQ_ASSIGNMENTS,
        REQ_SUBMISSIONS,
        REQ_FILES,
        REQ_FILE,
        REQ_FILE_META,
};

static const char *api_routes[] = {
                [REQ_LOGIN] = BASE_URL "/login",
                [REQ_COURSES] = BASE_URL "/courses/?extended=true",
                [REQ_SUBMISSIONS] = BASE_URL "/assignments/%u/submissions/",
                [REQ_FILES] = BASE_URL
                "/submissions/%u/files/?path=%s&is_directory=%s&owner=auto",
                [REQ_FILE_META] = BASE_URL "/submissions/%u/files/?path=%s",
                [REQ_FILE] = BASE_URL "/code/%u",
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

static const char *cgapi_serialize_user(const char *email, const char *password)
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

static int cgapi_is_array(json_t *j) { return !!json_is_array(j); }

static int cgapi_is_object(json_t *j) { return !!json_is_object(j); }

static int cgapi_deserialize_json(const char *json, json_t **dest,
                                  int is_type(json_t *))
{
        json_error_t err;
        *dest = json_loads(json, 0, &err);

        if (*dest == NULL) return -1;

        if (!is_type(*dest)) {
                json_decref(*dest);
                *dest = NULL;
                return -1;
        }

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

        if (res != NULL) {
                curl_easy_setopt(h.curl, CURLOPT_WRITEFUNCTION,
                                 cgapi_write_response);
                curl_easy_setopt(h.curl, CURLOPT_WRITEDATA, res);
        }

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

        const char *user = cgapi_serialize_user(email, password);
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

// Store as HTTP header: "Authorization: Bearer <token>"
#define JWT_HEADER "Authorization: Bearer "
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

int cgapi_get_courses(cgapi_token_t tok, json_t **courses)
{
        int ret = -1;

        struct cgapi_handle h =
                cgapi_init_request(tok, api_routes[REQ_COURSES]);
        if (h.curl == NULL) goto curl_init_failed;

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        cgapi_deserialize_json(res.str + res.pos, courses, cgapi_is_array);

        ret = 0;

        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
        return ret;
}

int cgapi_get_submissions(cgapi_token_t tok, int assignment_id,
                          json_t **submissions)
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

        cgapi_deserialize_json(res.str + res.pos, submissions, cgapi_is_array);

        ret = 0;

        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

int cgapi_get_submission_files(cgapi_token_t tok, int submission_id,
                               json_t **files)
{
        int ret = -1;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_FILES],
                                 submission_id, "", "");
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        cgapi_deserialize_json(res.str + res.pos, files, cgapi_is_object);

        ret = 0;

        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

int cgapi_get_file_meta(cgapi_token_t tok, unsigned submission_id,
                        const char *path, json_t *f)
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
        if (j_id == NULL || !json_is_integer(j_id)) goto invalid_response;
        json_object_set(f, "id", j_id);

        ret = 0;

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
                       const char *path, json_t *f)
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

        json_t *j_buf = json_stringn(res.str + res.pos, res.len - res.pos + 1);
        if (j_buf == NULL) goto json_stringify_failed;
        if (json_object_set(f, "buf", j_buf) < 0) {
                json_decref(j_buf);
                goto json_stringify_failed;
        }

        ret = 0;

json_stringify_failed:
        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
        return ret;
}

int cgapi_patch_file_buf(cgapi_token_t tok, json_t *f)
{
        int ret = -1;

        json_t *j_id = json_object_get(f, "id");
        json_t *j_buf = json_object_get(f, "buf");
        if (!json_is_integer(j_id) || !json_is_string(j_buf)) goto invalid_file;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_FILE],
                                 json_integer_value(j_id));
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        curl_easy_setopt(h.curl, CURLOPT_CUSTOMREQUEST, "PATCH");
        curl_easy_setopt(h.curl, CURLOPT_POSTFIELDS, json_string_value(j_buf));

        struct buf res;
        ret = cgapi_do_request(h, &res);
        if (ret) goto request_failed;

        json_error_t err;
        json_t *j_res = json_loads(res.str + res.pos, 0, &err);
        if (j_res == NULL) goto parse_json_failed;

        json_t *j_new_id = json_object_get(j_res, "id");
        if (j_new_id == NULL || !json_is_integer(j_new_id)) goto invalid_json;
        json_object_set(f, "id", j_new_id);

        ret = 0;

invalid_json:
        json_decref(j_res);
parse_json_failed:
        free(res.str);
request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
invalid_file:
        return ret;
}

int cgapi_post_file(cgapi_token_t tok, unsigned submission_id, const char *path,
                    int is_directory, const char *buf)
{
        int ret = -1;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_FILES],
                                 submission_id, path, is_directory);
        if (urllen > URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        curl_easy_setopt(h.curl, CURLOPT_POST, 1l);
        curl_easy_setopt(h.curl, CURLOPT_POSTFIELDS, buf);

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

int cgapi_unlink_file(cgapi_token_t tok, json_t *f)
{
        int ret = -1;

        json_t *j_id = json_object_get(f, "id");
        if (!json_is_integer(j_id)) goto invalid_file;

        char url[URL_MAX];
        size_t urllen = snprintf(url, URL_MAX, api_routes[REQ_FILE],
                                 json_integer_value(j_id));
        if (urllen >= URL_MAX) goto print_url_failed;

        struct cgapi_handle h = cgapi_init_request(tok, url);
        if (h.curl == NULL) goto curl_init_failed;

        curl_easy_setopt(h.curl, CURLOPT_CUSTOMREQUEST, "DELETE");

        ret = cgapi_do_request(h, NULL);
        if (ret) goto request_failed;

        ret = 0;

request_failed:
        cgapi_cleanup_request(h);
curl_init_failed:
print_url_failed:
invalid_file:
        return ret;
}
