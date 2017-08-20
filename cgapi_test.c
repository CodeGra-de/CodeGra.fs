#include "cgapi.c"
#include <stdio.h>

size_t failures = 0;

void test_serialize_user()
{
        const char *json = serialize_user("test", "test");
        const char *expect = "{\"email\":\"test\",\"password\":\"test\"}";

        if (!json || strcmp(json, expect)) {
                printf("Failed to serialize user\n");
                failures++;
        }
}

void test_login()
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        if (!tok) {
                printf("Failed to login\n");
                failures++;
        }

        free(tok);
}

int main(void)
{
        test_login();

        printf("%lu tests failed\n", failures);

        return failures != 0;
}
