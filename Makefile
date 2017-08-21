CFLAGS = -std=c11 -Werror -Wall -Wextra -Wpedantic

CFLAGS += $(shell curl-config --cflags)
LDLIBS += $(shell curl-config --libs)

CFLAGS += $(shell pkg-config --cflags fuse)
LDLIBS += $(shell pkg-config --libs fuse)

CFLAGS += $(shell pkg-config --cflags jansson)
LDLIBS += $(shell pkg-config --libs jansson)

all: cgfs

cgfs: CFLAGS += -DNDEBUG
cgfs: dict.o cgapi.o

# FIXME: Temporarily disabled -fsanitize=address as it is broken on the latest
# version of Linux. A patch has been mergeerd in the Linux kernel but it hasn't
# been distributed yet.
# test: CFLAGS += -O0 -g -fsanitize=address -fsanitize=leak -fsanitize=undefined
test: CFLAGS += -O0 -g -fsanitize=leak -fsanitize=undefined
test: $(patsubst %.c, %, $(wildcard *_test.c))

%_test: test.h %.h %.c %_test.c
	$(CC) $(CFLAGS) $(LDLIBS) $@.c -o $@
	$@

cgapi_test: CFLAGS += -DBASE_URL='"http://localhost:5000/api/v1"'

analyze:
	clang-check -analyze *.[ch] -- $(CFLAGS)

format:
	clang-format -i *.[ch]

clean:
	rm -f cgfs *_test *.o *.plist

.PHONY: all test analyze format clean
