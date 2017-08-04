#include "cgapi.c"

size_t failures = 0;

void test_login()
{
        cgapi_token tok = cgapi_login("thomas_schaper@example.com", "Thomas Schaper");

        if (tok) {
                printf("Token: %s\n", tok->str);
        } else {
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
