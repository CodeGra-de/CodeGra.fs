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

enum cgfs_file_type {
        CGFS_COURSE,
        CGFS_ASSIGNMENT,
        CGFS_SUBMISSION,
        CGFS_FILE,
};

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

static int cgfs_is_directory(json_t *dir)
{
        if (!json_is_object(dir)) return 0;

        json_t *entries = json_object_get(dir, "entries");

        return entries != NULL && json_is_array(entries);
}

static int cgfs_is_empty_path(const char *path)
{
        return path[0] == '\0' || (path[0] == '/' && path[1] == '\0');
}

static int cgfs_mark_dir_entries(json_t *dir, enum cgfs_file_type type, int recursive)
{
        if (!cgfs_is_directory(dir)) return -1;

        json_t *entries = json_object_get(dir, "entries");

        size_t idx;
        json_t *entry;

        json_array_foreach(dir, idx, entry) {
                json_object_set(entry, "type", json_integer(type));

                if (recursive && cgfs_is_directory(entry)) {
                        int err = cgfs_mark_dir_entries(entry, type, recursive);
                        if (err) return err;
                }
        }

        return 0;
}

static int cgfs_get_assignment_submissions(json_t *assignment)
{
        if (!json_is_object(assignment)) return -1;

        json_t *j_id = json_object_get(assignment, "id");
        if (!json_is_integer(j_id)) return -1;

        unsigned id = json_integer_value(j_id);

        json_t *submissions;
        int err = cgapi_get_submissions(CGFS_CONTEXT->login_token, id, &submissions);
        if (err) return err;

        if (json_object_set(assignment, "entries", submissions) < 0) {
                json_decref(submissions);
                return -1;
        }

        return cgfs_mark_dir_entries(assignment, CGFS_SUBMISSION, 0);
}

static int cgfs_get_submission_files(json_t *submission)
{
        if (!json_is_object(submission)) return -1;

        json_t *j_id = json_object_get(submission, "id");
        if (!json_is_integer(j_id)) return -1;

        unsigned id = json_integer_value(j_id);

        json_t *files;
        int err = cgapi_get_submission_files(CGFS_CONTEXT->login_token, id, &files);
        if (err) return err;

        if (json_object_set(submission, "entries", files) < 0) {
                json_decref(files);
                return -1;
        }

        return cgfs_mark_dir_entries(submission, CGFS_FILE, 1);
}

static int cgfs_get_file_in_dir(json_t *dir, const char *name, json_t **dest)
{
        *dest = NULL;

        if (!cgfs_is_directory(dir)) return ENOTDIR;

        size_t idx;
        json_t *entry;

        json_array_foreach(entries, idx, entry) {
                if (!json_is_object(entry)) continue;

                json_t *j_name = json_object_get(entry, "name");
                if (j_name == NULL || !json_is_string(j_name)) continue;

                if (strcmp(json_string_value(j_name), name) == 0) {
                        *dest = entry;
                        return 0;
                }
        }

        return ENOENT;
}

static int cgfs_next_part_in_path(json_t *dir, const char **path, json_t **dest)
{
        *dest = NULL;

        if (path[0] == '/') (*path)++;

        const char *sep = strchr(*path, '/');
        if (sep == NULL) {
                sep = strchr(*path, '\0');
                if (sep == NULL) return ENOENT;
        }

        size_t len = sep - *path;
        char name[len];
        memcpy(name, *path, len);
        part[len] = '\0';

        int status = cgfs_get_file_in_dir(dir, course_name, dest);

        if (status == 0) *path = sep;

        return status;
}

static int cgfs_get_file_by_path(const char *path, json_t **dest)
{
        *dest = CGFS_CONTEXT->file_tree;

        if (cgfs_is_empty_path(path)) return 0;

        int err;

        err = cgfs_next_part_in_path(*dest, &path, dest);
        if (err) return err;
        if (cgfs_is_empty_path(path)) return 0;

        err = cgfs_next_part_in_path(*dest, &path, dest);
        if (err) return err;
        if (cgfs_is_empty_path(path)) return 0;

        json_t *submission;
        err = cgfs_next_part_in_path(*dest, &path, &submission);
        if (err) {
                cgfs_get_assignment_submissions(*dest);
                err = cgfs_next_part_in_path(*dest, &path, &submission);
                if (err) return err;
        }
        *dest = submission;

        if (cgfs_is_empty_path(path)) return 0;
        if (!cgfs_is_directory(*dest)) return ENOTDIR;

        json_t *entry;
        err = cgfs_next_part_in_path(*dest, &path, &entry);
        if (err) {
                cgfs_get_submission_files(*dest);
                err = cgfs_next_part_in_path(*dest, &path, &entry);
                if (err) return err;
        }
        *dest = entry;

        if (cgfs_is_empty_path(path)) return 0;

        while ((err = cgfs_next_part_in_path(*dest, &path, dest)) == 0 && path[0] != '\0');

        return 0;
}

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

        static struct cgfs_context context;

        // Pop email from argv
        char *email = argv[argc - 1];

        size_t pass_max = 128;
        char password[pass_max];
        get_password(pass_max, password);

        context.login_token = cgapi_login(email, password);
        if (context.login_token == NULL) {
                fprintf(stderr, "%s: login failed\n", argv[0]);
                exit(EXIT_FAILURE);
        }

        // Clear memory
        memset(password, 0, pass_max);

        if (cgapi_get_courses(context.login_token, &context.file_tree) < 0) {
                fprintf(stderr, "%s: couldn't load courses", argv[0]);
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

        // Disable multithreaded FUSE, overriding the email address in argv.
        argv[argc - 1] = argv[argc - 2];
        argv[argc - 2] = "-s";

        return fuse_main(argc, argv, &fuse_ops, &context);
}
