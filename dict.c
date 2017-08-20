#include "dict.h"

#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void dict_init(struct dict *dict, size_t size)
{
        dict->size = size;
        dict->count = 0;
        for (size_t i = 0; i < size; i++) {
                dict->nodes[i] = 0;
        }
}

// Hash a string for a particular hash table using
// the Jenkins one-at-a-time hash function
// dicttps://en.wikipedia.org/wiki/Jenkins_hash_function
static size_t dict_hash(const char *key, size_t max)
{
        size_t hash = 0;

        for (size_t i = 0; i < strlen(key); i++) {
                hash += key[i];
                hash += hash << 10;
                hash ^= hash >> 6;
        }

        hash += hash << 3;
        hash ^= hash >> 11;
        hash += hash << 15;

        return hash % max;
}

// Create key-value pair.
static struct dict_node *dict_node_create(const char *key, void *val)
{
        size_t keylen = strlen(key);
        struct dict_node *n = malloc(sizeof(*n) + keylen + 1);

        if (!n) {
                return NULL;
        }

        n->val = val;
        n->next = 0;
        n->keylen = keylen;
        memcpy(n->key, key, keylen);
        n->key[keylen] = '\0';

        return n;
}

struct dict_node **dict_find(struct dict *dict, const char *key, int *cmpptr)
{
        assert(dict && key);

        size_t hash = dict_hash(key, dict->size);
        struct dict_node **n = &dict->nodes[hash];

        int cmp = -1;
        while (*n && (cmp = strcmp((*n)->key, key)) < 0) {
                n = &(*n)->next;
        }

        if (cmpptr) {
                *cmpptr = cmp;
        }

        return n;
}

// Insert or update a value in the hash table.
// Returns a pointer either equal to the new value
// if no old value existed at the given key, or equal
// to the old value if one existed at the key, or NULL
// if an error occurred.
void *dict_set(struct dict *dict, const char *key, void *val)
{
        assert(dict && key);

        int cmp;
        struct dict_node **n = dict_find(dict, key, &cmp);

        if (*n && !cmp) {
                void *oldval = (*n)->val;
                (*n)->val = val;
                return oldval;
        } else {
                struct dict_node *new = dict_node_create(key, val);
                if (!new) {
                        return NULL;
                }

                new->next = *n;
                *n = new;
                ++dict->count;

                return val;
        }
}

// Get the value for the given key.
void *dict_get(struct dict *dict, const char *key)
{
        assert(dict && key);

        int cmp;
        struct dict_node **n = dict_find(dict, key, &cmp);

        if (*n && !cmp) {
                return (*n)->val;
        } else {
                return NULL;
        }
}

// Remove the value for the given key from the hashtable
// and return it. Returns NULL if the key doesn't exist.
void *dict_unset(struct dict *dict, const char *key)
{
        assert(dict && key);

        int cmp;
        struct dict_node **n = dict_find(dict, key, &cmp);

        if (!*n || cmp) {
                return 0;
        }

        void *val = (*n)->val;

        struct dict_node *delete = *n;
        *n = (*n)->next;
        free(delete);

        return val;
}
