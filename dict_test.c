#include "test.h"
#include "dict.c"

void test_dict_create(void)
{
        size_t size = 100;
        struct dict *dict = dict_create(size);

        EXPECT(dict != NULL);
        EXPECT(dict->size == size);
        EXPECT(dict->count == 0);
        for (size_t i = 0; i < size; i++) {
                EXPECT(dict->nodes[i] == NULL);
        }

        dict_destroy(dict, {});
}

void test_dict_foreach(void)
{
        char *strings[] = {
                "abc", "bcd", "cde", "def", "efg",
                "fgh", "ghi", "hij", "ijk", "jkl",
        };
        size_t nstrings = sizeof(strings) / sizeof(*strings);
        int found[nstrings];

        struct dict *dict = dict_create(100);

        for (size_t i = 0; i < nstrings; i++) {
                dict_set(dict, strings[i], strings[i]);
                found[i] = 0;
        }

        dict_foreach(dict, { found[key[0] - 'a']++; });

        for (size_t i = 0; i < nstrings; i++) {
                EXPECT(found[i] == 1);
        }

        dict_destroy(dict, {});
}

void test_dict_destroy(void)
{
        char *strings[] = {
                "abc", "bcd", "cde", "def", "efg",
                "fgh", "ghi", "hij", "ijk", "jkl",
        };
        size_t nstrings = sizeof(strings) / sizeof(*strings);
        int found[nstrings];

        struct dict *dict = dict_create(100);

        for (size_t i = 0; i < nstrings; i++) {
                dict_set(dict, strings[i], strings[i]);
                found[i] = 0;
        }

        dict_destroy(dict, { found[key[0] - 'a']++; });

        for (size_t i = 0; i < nstrings; i++) {
                EXPECT(found[i] == 1);
        }
}

void test_dict_set(void)
{
        char *strings[] = {
                "abc", "bcd", "cde", "def", "efg",
                "fgh", "ghi", "hij", "ijk", "jkl",
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
                char *val =
                        dict_set(dict, strings[i], strings[(i + 1) % nstrings]);
                EXPECT(val == strings[i]);
        }

        dict_destroy(dict, {});
}

void test_dict_get(void)
{
        char *strings[] = {
                "abc", "bcd", "cde", "def", "efg",
                "fgh", "ghi", "hij", "ijk", "jkl",
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
                "abc", "bcd", "cde", "def", "efg",
                "fgh", "ghi", "hij", "ijk", "jkl",
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

        RESULTS();
}
