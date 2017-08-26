export PYTHONPATH=$(CURDIR)

.PHONY: install_deps
install_deps:
	pip install -r requirements.txt
