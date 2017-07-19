CFLAGS = -std=c11 -Werror -Wall -Wextra -Wimplicit-fallthrough=2 -pedantic $(shell pkg-config --cflags fuse)
LDLIBS = -lcurl $(shell pkg-config --libs fuse)

all: codegra-fs
