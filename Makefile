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
	coverage erase
	$(PYTEST) test/ -vvvvvvvvv
	coverage report -m cgfs.py
