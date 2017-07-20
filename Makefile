CFLAGS = -std=c11 -Werror -Wall -Wextra -pedantic $(shell pkg-config --cflags fuse)
LDLIBS = -lcurl $(shell pkg-config --libs fuse)

all: codegra-fs
