CFLAGS = -std=c11 -Werror -Wall -Wextra -pedantic

CFLAGS += $(shell curl-config --cflags)
LDLIBS += $(shell curl-config --libs)

CFLAGS += $(shell pkg-config --cflags fuse)
LDLIBS += $(shell pkg-config --libs fuse)

CFLAGS += $(shell pkg-config --cflags jansson)
LDLIBS += $(shell pkg-config --libs jansson)

all: cgfs

cgfs: dict.o cgapi.o

test: CFLAGS += -O0 -g -fsanitize=address -fsanitize=leak -fsanitize=undefined
test: $(patsubst %_test.c,%_test,$(wildcard *_test.c))
	@for tester in *_test; do $$tester; done

cgapi_test: CFLAGS += -DBASE_URL='"http://localhost:5000/api/v1"'

format:
	clang-format -i *.[ch]

clean:
	rm -f *_test *.o cgfs

.PHONY: all test format clean
