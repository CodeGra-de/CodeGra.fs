CFLAGS = -std=c11 -Werror -Wall -Wextra -Wimplicit-fallthrough=2 -pedantic

CFLAGS += $(shell curl-config --cflags)
LDLIBS += $(shell curl-config --libs)

CFLAGS += $(shell pkg-config --cflags fuse)
LDLIBS += $(shell pkg-config --libs fuse)

all: cgfs

cgfs: dict.o cgapi.o

format:
	clang-format -i *.[ch]
