#include "cgapi.h"

#include <stdio.h>
#include <stdlib.h>
#include <curl/curl.h>

#ifndef BASE_URL
#define BASE_URL "https://codegra.de/api/v1"
#endif

enum req_type {
	REQ_ASSIGNMENTS,
	REQ_SUBMISSIONS,
	REQ_FILES,
};

static const char *api_routes[] = {
	[REQ_ASSIGNMENTS] = BASE_URL "/assignments/",
	[REQ_SUBMISSIONS] = BASE_URL "/assignments/%u/submissions/",
	[REQ_FILES]       = BASE_URL "/submissions/%u/files/%s",
};

void cgapi_init(void)
{
	// Do global curl setup
}

static CURL *cgapi_init_request(enum req_type type, const char *url)
{
	CURL *curl = curl_easy_init();
	if (!curl) return NULL;

	curl_easy_setopt(curl, CURLOPT_URL, url);
	curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);

	// Set headers & do auth stuff

	return curl;
}

// TODO: Send mkdir request to server
int cgapi_mkdir(int submission_id, const char *path)
{
	(void) submission_id, (void) path;
	return 0;
}
// TODO: Send rmdir request to server
int cgapi_rmdir(int submission_id, const char *path)
{
	(void) submission_id, (void) path;
	return 0;
}
// TODO: Get assignments
int cgapi_get_assignments(struct cgapi_assignment *ass)
{
	(void) ass;
	return 0;
}
// TODO: Get Submissions
int cgapi_get_submissions(int assignment_id, struct cgapi_submission *subs)
{
	(void) assignment_id, (void) subs;
	return 0;
}
// TODO: Get submission files
int cgapi_get_submission_files(int submission_id, struct cgapi_file *files)
{
	(void) submission_id, (void) files;
	return 0;
}
// TODO: Get other info from server
int cgapi_get_file_meta(int file_id, struct cgapi_file_meta *fm)
{
	(void) file_id, (void) fm;
	return 0;
}
// TODO: Get data from server
int cgapi_get_file_buf(int file_id, struct cgapi_file *f)
{
	(void) file_id, (void) f;
	// f->buf = ...
	return 0;
}
// TODO: Send f->buf to server
int cgapi_put_file_buf(struct cgapi_file *f)
{
	(void) f;
	return 0;
}
// TODO: Send unlink request to server
int cgapi_unlink_file(struct cgapi_file *f)
{
	(void) f;
	return 0;
}
