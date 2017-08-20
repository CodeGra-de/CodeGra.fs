#include "dict.c"
#include <stdio.h>

size_t failures = 0;

#define EXPECT(expr)                                                           \
        do {                                                                   \
                if (!(expr)) {                                                 \
                        failures++;                                            \
                }                                                              \
        } while (0)

void test_dict_create(void)
{
        size_t size = 100;
        struct dict *dict = dict_create(size);

        EXPECT(dict != NULL);
        EXPECT(dict->size == size);
        EXPECT(dict->count == 0);
        EXPECT(dict->nodes != NULL);
        for (size_t i = 0; i < size; i++) {
                EXPECT(dict->nodes[i] == NULL);
        }

        dict_destroy(dict, {});
}

void test_dict_foreach(void)
{
        char *strings[] = {
                "abc",
                "bcd",
                "cde",
                "def",
                "efg",
                "fgh",
                "ghi",
                "hij",
                "ijk",
                "jkl",
        };
        size_t nstrings = sizeof(strings) / sizeof(*strings);

        struct dict *dict = dict_create(100);

        for (size_t i = 0; i < nstrings; i++) {
                dict_set(dict, strings[i], strings[i]);
        }

        size_t count = 0;
        dict_foreach(dict, {
                count++;
        });
        EXPECT(count == nstrings);

        dict_destroy(dict, {});
}

void test_dict_destroy(void)
{
        size_t nstrings = 10;
        char *strings[nstrings];
        for (size_t i = 0; i < nstrings; i++) {
                strings[i] = malloc(4);
                if (strings[i] == NULL) {
                        for (size_t j = 0; j < i; j++) {
                                free(strings[j]);
                        }
                        return;
                }

                strncpy(strings[i],
                        "abcdefghijklmnopqrstuvwxyz" + (i % nstrings), 3);
                strings[i][3] = '\0';
        }

        struct dict *dict = dict_create(100);

        for (size_t i = 0; i < nstrings; i++) {
                dict_set(dict, strings[i], strings[(i + 1) % nstrings]);
        }

        dict_destroy(dict, {
                free(val);
        });

        for (size_t i = 0; i < nstrings; i++) {
                EXPECT(strings[i] == NULL);
        }
}

void test_dict_set(void)
{
        char *strings[] = {
                "abc",
                "bcd",
                "cde",
                "def",
                "efg",
                "fgh",
                "ghi",
                "hij",
                "ijk",
                "jkl",
        };
        size_t nstrings = sizeof(strings) / sizeof(*strings);

        struct dict *dict = dict_create(100);

        // Check that return value is equal to set value
        for (size_t i = 0; i < nstrings; i++) {
                char *val = dict_set(dict, strings[i], strings[i]);
                EXPECT(val == strings[i]);
        }

        // Check that each key is equal to its value
        dict_foreach(dict, {
                EXPECT(strcmp(key, val) == 0);
                EXPECT(strings[key[0] - 'a'] == val);
        });

        // Check that dict_set returns the old value when key already exists
        for (size_t i = 0; i < nstrings; i++) {
                char *val = dict_set(dict, strings[i], strings[(i + 1) % nstrings]);
                EXPECT(val == strings[i]);
        }

        dict_destroy(dict, {});
}

void test_dict_get(void)
{
        char *strings[] = {
                "abc",
                "bcd",
                "cde",
                "def",
                "efg",
                "fgh",
                "ghi",
                "hij",
                "ijk",
                "jkl",
        };
        size_t nstrings = sizeof(strings) / sizeof(*strings);

        struct dict *dict = dict_create(100);

        for (size_t i = 0; i < nstrings; i++) {
                dict_set(dict, strings[i], strings[i]);
                char *val = dict_get(dict, strings[i]);
                EXPECT(val == strings[i]);
        }

        dict_destroy(dict, {});
}

void test_dict_unset(void)
{
        char *strings[] = {
                "abc",
                "bcd",
                "cde",
                "def",
                "efg",
                "fgh",
                "ghi",
                "hij",
                "ijk",
                "jkl",
        };
        size_t nstrings = sizeof(strings) / sizeof(*strings);

        struct dict *dict = dict_create(100);

        for (size_t i = 0; i < nstrings; i++) {
                dict_set(dict, strings[i], strings[i]);
                char *val = dict_unset(dict, strings[i]);
                EXPECT(val == strings[i]);
        }

        dict_destroy(dict, {});
}

int main(void)
{
        test_dict_create();
        test_dict_foreach();
        test_dict_destroy();
        test_dict_set();
        test_dict_get();
        test_dict_unset();

        return EXIT_SUCCESS;
}
