#include "cgapi.h"

#include <errno.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sys/types.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>

#define FUSE_USE_VERSION 30
#include <fuse.h>
#include <jansson.h>

// Be careful! This macro RETURNs if malloc fails.
// Make sure this doesn't cause any leaks!
#define MALLOC(type, var, nitems)                                              \
        do {                                                                   \
                var = malloc((nitems) * sizeof(type));                         \
                if ((var) == NULL) {                                           \
                        perror("malloc");                                      \
                        return ENOMEM;                                         \
                }                                                              \
        } while (0)

// Be careful! This macro RETURNs if realloc fails.
// Make sure this doesn't cause any leaks!
#define REALLOC(type, var, nitems)                                             \
        do {                                                                   \
                type *tmp = realloc((var), (nitems) * sizeof(type));           \
                if (tmp == NULL) {                                             \
                        perror("realloc");                                     \
                        return ENOMEM;                                         \
                }                                                              \
                (var) = tmp;                                                   \
        } while (0)

#define FREE(var)                                                              \
        do {                                                                   \
                free(var);                                                     \
                var = NULL;                                                    \
        } while (0)

#define UNUSED(x) (void)(x);

struct cgfs_context {
        cgapi_token_t login_token;
        json_t *file_tree;
};

#define CGFS_CONTEXT ((struct cgfs_context *) fuse_get_context()->private_data)

struct file {
        int id;
        size_t nlinks;
        bool dirty;

        // Stat data
        struct timespec mtime;
        struct timespec deadline;
        bool is_writable;

        // Buffer data
        size_t buflen;
        char *buf;
};

int cgfs_getattr(const char *path, struct stat *st)
{
        UNUSED(path);

        struct fuse_context *fc = fuse_get_context();

        st->st_uid = fc->uid;
        st->st_gid = fc->gid;
        st->st_atime = time(NULL);

        // TODO: Get other info from server

        struct file *f = dict_get(CGFS_CONTEXT->open_files, path);
        if (f) {
                // st->st_mtime = f->mtime;
        } else {
                // st->st_mtime = api_data->mtime;
        }

        return 0;
}

int cgfs_access(const char *path, int mask)
{
        struct file *f = dict_get(CGFS_CONTEXT->open_files, path);
        if (!f) {
                // Get file from server
                if (!f) {
                        return EACCES;
                }
        }

        if (mask == F_OK) {
                return 0;
        }

        if (mask & W_OK) {
                return f->is_writable ? 0 : EACCES;
        }

        return 0;
}

int cgfs_mkdir(const char *path, mode_t mode)
{
        UNUSED(path);
        UNUSED(mode);

        // TODO: Send mkdir request to server

        return 0;
}

int cgfs_rmdir(const char *path)
{
        UNUSED(path);

        // TODO: Send rmdir request to server

        return 0;
}

int cgfs_readdir(const char *path, void *buffer, fuse_fill_dir_t filler,
                 off_t offset, struct fuse_file_info *fi)
{
        UNUSED(offset);
        UNUSED(fi);

        filler(buffer, ".", NULL, 0);
        filler(buffer, "..", NULL, 0);

        // Determine type of directory. If path has:
        // - One '/': top level, get assignments
        // - Two '/': in assignment, get submissions for assignment
        // - Otherwise: in submission, get submission directory
        int nparts = 0;
        int path_parts[3] = {
                -1, -1, -1,
        };
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
        UNUSED(fi);

        struct file *f = dict_get(CGFS_CONTEXT->open_files, path);

        if (!f) {
                MALLOC(struct file, f, 1);
                // TODO: Get data from server
                dict_set(CGFS_CONTEXT->open_files, path, f);
        }

        f->nlinks++;

        return 0;
}

int cgfs_release(const char *path, struct fuse_file_info *fi)
{
        UNUSED(fi);

        struct file *f = dict_get(CGFS_CONTEXT->open_files, path);
        if (!f) return EBADF;

        f->nlinks--;
        if (f->nlinks == 0) {
                dict_unset(CGFS_CONTEXT->open_files, path);
                FREE(f);
        }

        return 0;
}

int cgfs_read(const char *path, char *buf, size_t buflen, off_t offset,
              struct fuse_file_info *fi)
{
        UNUSED(fi);

        struct file *f = dict_get(CGFS_CONTEXT->open_files, path);
        if (!f) return EBADF;

        if ((size_t)offset > f->buflen) {
                return EFAULT;
        }

        if (buflen > f->buflen - offset) {
                buflen = f->buflen - offset;
        }

        memcpy(buf, f->buf + offset, buflen);

        return buflen;
}

int cgfs_write(const char *path, const char *buf, size_t buflen, off_t offset,
               struct fuse_file_info *fi)
{
        UNUSED(fi);

        struct file *f = dict_get(CGFS_CONTEXT->open_files, path);
        if (!f) return EBADF;

        REALLOC(char, f->buf, f->buflen + buflen);
        memmove(f->buf + offset + buflen, f->buf + offset, f->buflen - offset);
        memcpy(f->buf + offset, buf, buflen);
        f->dirty = true;

        return buflen;
}

int cgfs_ftruncate(const char *path, off_t offset, struct fuse_file_info *fi)
{
        UNUSED(fi);

        struct file *f = dict_get(CGFS_CONTEXT->open_files, path);
        if (!f) return EBADF;

        REALLOC(char, f->buf, offset);

        return 0;
}

int cgfs_flush(const char *path, struct fuse_file_info *fi)
{
        UNUSED(fi);

        struct file *f = dict_get(CGFS_CONTEXT->open_files, path);
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
        UNUSED(path);

        // TODO: Send unlink request to server

        return 0;
}

// Read a nul-terminated password into the buffer
void get_password(size_t len, char pass[len])
{
        printf("Enter password: ");

	struct termios oflags, nflags;
	tcgetattr(fileno(stdin), &oflags);
	nflags = oflags;
	nflags.c_lflag &= ~ECHO;
	nflags.c_lflag |= ECHONL;

	if (tcsetattr(fileno(stdin), TCSANOW, &nflags) != 0) {
		perror("tcsetattr");
		exit(EXIT_FAILURE);
	}

	size_t i = 0;
	int c;
	while ((c = getchar()) != EOF && c != '\n' && i < len - 1)
		pass[i++] = c;

	pass[i] = '\0';

	if (tcsetattr(fileno(stdin), TCSANOW, &oflags) != 0) {
		perror("tcsetattr");
		exit(EXIT_FAILURE);
	}
}

int main(int argc, char *argv[argc])
{
        if (argc < 3 || argv[argc - 2][0] == '-' || argv[argc - 1][0] == '-') {
                fprintf(stderr, "%s: last 2 arguments must be mountpoint and email, respectively\n", argv[0]);
                exit(EXIT_FAILURE);
        } 

        char *email = argv[--argc];
        argv[argc] = NULL;

        char password[128];
        get_password(128, password);

        static struct cgfs_context context;

        context.login_token = cgapi_login(email, password);
        if (context.login_token == NULL) {
                fprintf(stderr, "%s: login failed\n", argv[0]);
                exit(EXIT_FAILURE);
        }

        context.open_files = dict_create(1 << 8);
        if (context.open_files == NULL) {
                printf("%s: ", argv[0]);
                perror("dict_create");
                exit(EXIT_FAILURE);
        }

        static struct fuse_operations fuse_ops = {
                .getattr = cgfs_getattr,
                .access = cgfs_access,
                .mkdir = cgfs_mkdir,
                .rmdir = cgfs_rmdir,
                .readdir = cgfs_readdir,
                .open = cgfs_open,
                .release = cgfs_release,
                .read = cgfs_read,
                .write = cgfs_write,
                .ftruncate = cgfs_ftruncate,
                .flush = cgfs_flush,
                .unlink = cgfs_unlink,
        };

        return fuse_main(argc, argv, &fuse_ops, &context);
}
