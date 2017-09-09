export PYTHONPATH=$(CURDIR)
PYTEST?=pytest

.PHONY: install_deps
install_deps:
	pip install -r requirements.txt

.PHONY: format
format:
	yapf -rip *.py

.PHONY: test
test:
	$(PYTEST) test/ -vvvvvvvvv
