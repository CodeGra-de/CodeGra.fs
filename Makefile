export PYTHONPATH=$(CURDIR)
TEST_FILE?=test/
TEST_FLAGS?=
PYTEST?=pytest

.PHONY: install_deps
install_deps:
	pip install -r requirements.txt

.PHONY: format
format:
	yapf -rip *.py

.PHONY: test
test:
	which cgfs
	coverage erase
	$(PYTEST) $(TEST_FILE) -vvvvvvvvv $(TEST_FLAGS)
	coverage report -m codegra_fs/cgfs.py

.PHONY: test_quick
test_quick: TEST_FLAGS += -x
test_quick: test

.PHONY: build
build:
	python ./build.py

.PHONY: gui
gui:
	npm run dev
