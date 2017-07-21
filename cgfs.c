#include "dict.h"

#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sys/types.h>
#include <unistd.h>

#define FUSE_USE_VERSION 30
#include <fuse.h>

#include <curl/curl.h>

// Be careful! This macro RETURNs if malloc fails.
// Make sure this doesn't cause any leaks!
#define MALLOC(type, var, nitems) \
do { \
	var = malloc((nitems) * sizeof(type)); \
	if ((var) == NULL) { \
		perror("malloc"); \
		return ENOMEM; \
	} \
} while (0)

// Be careful! This macro RETURNs if realloc fails.
// Make sure this doesn't cause any leaks!
#define REALLOC(type, var, nitems) \
do { \
	type *tmp = realloc((var), (nitems) * sizeof(type)); \
	if (tmp == NULL) { \
		perror("realloc"); \
		return ENOMEM; \
	} \
	(var) = tmp; \
} while (0)

#define FREE(var) \
free(var); \
var = NULL;

struct file {
	int id;
	size_t nlinks;
	bool dirty;
	size_t buflen;
	char *buf;
};

struct dict open_files;

int cgfs_getattr(const char *path, struct stat *st)
{
	(void) path;
	struct fuse_context *fc = fuse_get_context();

	st->st_uid = fc->uid;
	st->st_gid = fc->gid;
	st->st_atime = time(NULL);
	st->st_mtime = time(NULL);

	// TODO: Get other info from server

	return 0;
}

int cgfs_access(const char *path, int mask)
{
	(void) path;

	char flags[5] = {
		mask & F_OK ? 'f' : '-',
		mask & R_OK ? 'r' : '-',
		mask & W_OK ? 'w' : '-',
		mask & X_OK ? 'x' : '-',
		0
	};

	(void) flags;

	// TODO: Send access request to server

	return 0;
}

int cgfs_mkdir(const char *path, mode_t mode)
{
	(void) path; (void) mode;

	// TODO: Send mkdir request to server

	return 0;
}

int cgfs_rmdir(const char *path)
{
	(void) path;

	// TODO: Send rmdir request to server

	return 0;
}

int cgfs_readdir(const char *path, void *buffer, fuse_fill_dir_t filler,
		 off_t offset, struct fuse_file_info *fi)
{
	(void) offset; (void) fi;

	filler(buffer, ".", NULL, 0);
	filler(buffer, "..", NULL, 0);

	// Determine type of directory. If path has:
	// - One '/': top level, get assignments
	// - Two '/': in assignment, get submissions for assignment
	// - Otherwise: in submission, get submission directory
	int nparts = 0;
	int path_parts[3] = { -1, -1, -1, };
	for (; nparts < 3; nparts++) {
		char *match = strchr(path, path_parts[nparts] + 1);
		if (match == NULL) {
			break;
		}
		path_parts[nparts] = match - path;
	}

	switch (nparts) {
	case 1:
		// TODO: Get assignments
		break;
	case 2:
		// TODO: Get assignment id
		// TODO: Get Submissions
		break;
	default:
		// TODO: Get submission id
		// TODO: Get submission files
		break;
	}

	return 0;
}

int cgfs_open(const char *path, struct fuse_file_info *fi)
{
	(void) fi;

	struct file *f = dict_get(&open_files, path);

	if (!f) {
		// TODO: Get data from server
		MALLOC(struct file, f, 1);
		dict_set(&open_files, path, f);
		memcpy(f->path, path, strlen(path));
		// TODO: Put data in file struct
	}

	return 0;
}

int cgfs_release(const char *path, struct fuse_file_info *fi)
{
	(void) fi;

	struct file *f = dict_get(&open_files, path);
	if (!f) return EBADF;

	f->nlinks--;
	if (f->nlinks == 0) {
		dict_unset(&open_files, path);
		FREE(f);
	}

	return 0;
}

int cgfs_read(const char *path, char *buf, size_t buflen,
		off_t offset, struct fuse_file_info *fi)
{
	(void) fi;

	struct file *f = dict_get(&open_files, path);
	if (!f) return EBADF;

	if ((size_t) offset > f->buflen) {
		return EFAULT;
	}

	if (buflen > f->buflen - offset) {
		buflen = f->buflen - offset;
	}

	memcpy(buf, f->buf + offset, buflen);

	return buflen;
}

int cgfs_write(const char *path, const char *buf, size_t buflen,
	       off_t offset, struct fuse_file_info *fi)
{
	(void) fi;

	struct file *f = dict_get(&open_files, path);
	if (!f) return EBADF;

	REALLOC(char, f->buf, f->buflen + buflen);
	memmove(f->buf + offset + buflen, f->buf + offset, f->buflen - offset);
	memcpy(f->buf + offset, buf, buflen);
	f->dirty = true;

	// flush?

	return buflen;
}

int cgfs_ftruncate(const char *path, off_t offset,
                   struct fuse_file_info *fi)
{
	(void) fi;

	struct file *f = dict_get(&open_files, path);
	if (!f) return EBADF;

	REALLOC(char, f->buf, offset);

	return 0;
}

int cgfs_flush(const char *path, struct fuse_file_info *fi)
{
	(void) fi;

	struct file *f = dict_get(&open_files, path);;
	if (!f) return EBADF;

	if (!f->dirty) {
		return 0;
	}

	// TODO: Send f->buf to server

	f->dirty = false;

	return 0;
}

int cgfs_unlink(const char *path)
{
	(void) path;

	// TODO: Send unlink request to server

	return 0;
}

static struct fuse_operations fuse_ops = {
	.getattr   = cgfs_getattr,
	.access    = cgfs_access,
	.mkdir     = cgfs_mkdir,
	.rmdir     = cgfs_rmdir,
	.readdir   = cgfs_readdir,
	.open      = cgfs_open,
	.release   = cgfs_release,
	.read      = cgfs_read,
	.write     = cgfs_write,
	.ftruncate = cgfs_ftruncate,
	.flush     = cgfs_flush,
	.unlink    = cgfs_unlink,
};

int main(int argc, char *argv[argc])
{
        dict_init(&open_files, 1 << 8);

	return fuse_main(argc, argv, &fuse_ops, NULL);
}
