#include "test.h"
#include "cgapi.c"

void test_serialize_user()
{
        const char *json = serialize_user("test", "test");
        const char *expected = "{\"email\":\"test\",\"password\":\"test\"}";

        EXPECT(json != NULL);
        EXPECT(strcmp(json, expected) == 0);

        free((char *)json);
}

void test_login()
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        EXPECT(tok != NULL);

        free(tok);
}

int main(void)
{
        test_serialize_user();
        test_login();

        RESULTS();
}
