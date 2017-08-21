#include "cgapi.c"
#include "test.h"

void test_cgapi_serialize_user()
{
        const char *json = cgapi_serialize_user("test", "test");
        const char *expected = "{\"email\":\"test\",\"password\":\"test\"}";

        EXPECT(json != NULL);
        EXPECT(strcmp(json, expected) == 0);

        free((char *)json);
}

void test_cgapi_login()
{
        cgapi_token_t tok =
                cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        EXPECT(tok != NULL);

        free(tok);
}

int main(void)
{
        test_cgapi_serialize_user();
        test_cgapi_login();

        RESULTS();
}
