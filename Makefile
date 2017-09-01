export PYTHONPATH=$(CURDIR)

.PHONY: install_deps
install_deps:
	pip install -r requirements.txt

.PHONY: format
format:
	yapf -rip *.py

.PHONY: test
test:
	bats/bin/bats cgfs.bats
