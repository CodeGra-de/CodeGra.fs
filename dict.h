#ifndef DICT_H
#define DICT_H

#include <stddef.h>

struct dict_node {
        struct dict_node *next;
        void *val;
        size_t keylen;
        char key[];
};

struct dict {
        size_t size;
        size_t count;
        struct dict_node *nodes[];
};

void dict_init(struct dict *dict, size_t size);

// dict_foreach & dict_destroy execute `block` with all
// items in the dict. In the `block` the variables
// `const char *key` and `void *val` are available.
#define dict_foreach(dict, block)                                              \
        do {                                                                   \
                for (size_t i = 0; i < (dict)->size; i++) {                    \
                        struct dict_node *n, *p;                               \
                        for (n = (dict)->nodes[i]; n; n = p) {                 \
                                p = n->next;                                   \
                                void *val = n->val;                            \
                                const char *key = n->key;                      \
                                (void)val, (void)key;                          \
                                (block);                                       \
                        }                                                      \
                }                                                              \
        } while (0)

#define dict_destroy(dict, block)                                              \
        do {                                                                   \
                dict_foreach((dict), {                                         \
                        (block);                                               \
                        free(n);                                               \
                });                                                            \
        } while (0)

//
void *dict_set(struct dict *dict, const char *key, void *val);
void *dict_get(struct dict *dict, const char *key);
void *dict_unset(struct dict *dict, const char *key);

#endif // DICT_H
