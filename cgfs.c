#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <linux/limits.h>
#include <sys/types.h>
#include <unistd.h>

#define FUSE_USE_VERSION 30
#include <fuse.h>

#include <curl/curl.h>

#ifndef MAX_OPEN_FILES
#define MAX_OPEN_FILES 1 << 10
#endif

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
	char path[PATH_MAX];
	size_t nlinks;
	size_t buflen;
	char *buf;
	bool dirty;
};

struct file *open_files[MAX_OPEN_FILES];

int cgfs_get_free_fh(void)
{
	int fh = 0;
	while (fh < MAX_OPEN_FILES && open_files[fh]) fh++;
	return fh < MAX_OPEN_FILES ? fh : ENFILE;
}

struct file *cgfs_get_open_file_by_path(const char *path)
{
	for (int i = 0; i < MAX_OPEN_FILES; i++) {
		if (!open_files[i]) {
			continue;
		}
		if (strncmp(open_files[i]->path, path, PATH_MAX) == 0) {
			return open_files[i];
		}
	}
	return NULL;
}

int cgfs_get_file(unsigned fh, struct file **f)
{
	if (fh >= MAX_OPEN_FILES || open_files[fh] == NULL) {
		return EBADF;
	}
	*f = open_files[fh];
	return 0;
}

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
        int fh = cgfs_get_free_fh();
	if (fh < 0) return fh;

	struct file *f = cgfs_get_open_file_by_path(path);;

	if (!f) {
		// TODO: Get data from server
		MALLOC(struct file, f, 1);
		// TODO: Put data in file struct
	}

	fi->fh = fh;
	open_files[fh] = f;

	return fh;
}

int cgfs_release(const char *path, struct fuse_file_info *fi)
{
	(void) path;

	struct file *f;
	int ret = cgfs_get_file(fi->fh, &f);
	if (ret < 0) return ret;

	f->nlinks--;
	if (f->nlinks == 0) {
		FREE(f->buf);
		FREE(f);
		open_files[fi->fh] = NULL;
	}

	return 0;
}

int cgfs_read(const char *path, char *buf, size_t buflen,
		off_t offset, struct fuse_file_info *fi)
{
	(void) path;

	struct file *f;
	int ret = cgfs_get_file(fi->fh, &f);
	if (ret < 0) return ret;

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
	(void) path;

	struct file *f;
	int ret = cgfs_get_file(fi->fh, &f);
	if (ret < 0) return ret;

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
	(void) path;

	struct file *f;
	int ret = cgfs_get_file(fi->fh, &f);
	if (ret < 0) return ret;

	REALLOC(char, f->buf, offset);

	return 0;
}

int cgfs_flush(const char *path, struct fuse_file_info *fi)
{
	(void) path;

	struct file *f;
	int ret = cgfs_get_file(fi->fh, &f);
	if (ret < 0) return ret;

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

int main(int argc, char *argv[argc])
{
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

	int fuse_argc = argc;
	for (char **arg = argv + 1; arg; arg++) {
		if (strcmp(*arg, "--")) {
			fuse_argc--;
			break;
		} else {
			break;
		}
		fuse_argc--;
	}

	return fuse_main(fuse_argc, argv + argc - fuse_argc, &fuse_ops, NULL);
}
