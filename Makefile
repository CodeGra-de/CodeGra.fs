CFLAGS = -std=c11 -Werror -Wall -Wextra -Wimplicit-fallthrough=2 -pedantic

CFLAGS += $(shell curl-config --cflags)
LDLIBS += $(shell curl-config --libs)

CFLAGS += $(shell pkg-config --cflags fuse)
LDLIBS += $(shell pkg-config --libs fuse)

CFLAGS += $(shell pkg-config --cflags jansson)
LDLIBS += $(shell pkg-config --libs jansson)

all: cgfs

cgfs: dict.o cgapi.o

test: cgapi_test
	valgrind ./cgapi_test

cgapi_test: CFLAGS += -O0 -g -DBASE_URL='"http://localhost:5000/api/v1"'

format:
	clang-format -i *.[ch]
