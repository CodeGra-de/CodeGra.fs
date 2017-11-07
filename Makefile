export PYTHONPATH=$(CURDIR)
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
	coverage erase
	$(PYTEST) test/ -vvvvvvvvv $(TEST_FLAGS)
	coverage report -m cgfs.py

.PHONY: test_quick
test-quick: TEST_FLAGS += -x
test-quick: test
