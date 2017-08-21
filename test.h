#include <stdio.h>

size_t numtests = 0;
size_t failures = 0;

#define EXPECT(expr)                                                           \
        do {                                                                   \
                numtests++;                                                    \
                if (!(expr)) {                                                 \
                        fprintf(stderr, "%s:%d: test failed: %s\n", __FILE__,  \
                                __LINE__, #expr);                              \
                        failures++;                                            \
                }                                                              \
        } while (0)

#define RESULTS()                                                              \
        do {                                                                   \
                fprintf(stderr, "total: %lu, succeed: %lu, failed: %lu\n",     \
                        numtests, numtests - failures, failures);              \
                return failures != 0;                                          \
        } while (0)
