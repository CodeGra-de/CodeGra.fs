#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

#include <fuse.h>
#include <curl/curl.h>

#ifndef MAX_OPEN_FILES
#define MAX_OPEN_FILES 1 << 8
#endif

#define MALLOC(type, var, nitems) \
(type) *(var) = malloc(nitems * sizeof(type)); \
if ((var) == NULL) { \
	perror("malloc"); \
	exit(ENOMEM); \
}

#define FREE(var) \
free(var); \
var = NULL;

struct file {
	int id;
	bool synced;
	size_t numfds;
	size_t buflen;
	char *buf;
};

static struct file open_files[MAX_OPEN_FILES];

#define VALIDATE_FD(fd) \
do \
	if (fd < 0 || fd >= MAX_OPEN_FILES || fd < 0 || \
	    open_files[fd].id < 0) \
		return EBADF; \
while (0)

int find_free_fd(void)
{
	int i = 0;
	while (i < MAX_OPEN_FILES && open_files[i].id >= 0) i++;
	return i < MAX_OPEN_FILES ? i : -1;
}

int close_fd(int fd)
{
	VALIDATE_FD(fd);

	open_files[fd].numfds--;
	if (open_files[fd].numfds == 0) {
		open_files[fd].id = -1;
		FREE(open_files[fd].buf);
	}
}

int main(int argc, const char *argv[argc])
{
	(void) argv;
	return EXIT_SUCCESS;
}
