export PYTHONPATH = $(CURDIR)
MYPY_FLAGS += --package codegra_fs
PYLINT_FLAGS += --rcfile=setup.cfg codegra_fs
YAPF_FLAGS += --recursive --parallel codegra_fs
ISORT_FLAGS += --recursive codegra_fs
TEST_FILE ?= test/
TEST_FLAGS += -vvv

ENV = . env/bin/activate;

.PHONY: run
run: install
	$(ENV) npm run dev

env:
	virtualenv env

.PHONY: install-deps
install-deps: env/.install-deps node_modules/.install-deps
env/.install-deps: requirements.txt requirements-mac.txt | env
	$(ENV) pip install -r requirements.txt
	if [ "$$(uname)" == 'Darwin' ]; then \
		$(ENV) pip install -r requirements-mac.txt; \
	fi
	date >$@
node_modules/.install-deps: package.json
	npm install
	date >$@

.PHONY: install
install: install-deps env/bin/cgfs env/bin/cgapi-consumer
env/bin/%: setup.py codegra_fs/*.py
	$(ENV) pip install .

.PHONY: myypy
mypy: install-deps
	$(ENV) mypy $(MYPY_FLAGS)

.PHONY: lint
lint: install-deps
	# Remove the "|| true" when pylint succeeds
	$(ENV) pylint $(PYLINT_FLAGS) || true
	npm run lint

.PHONY: format
format: install-deps
	$(ENV) yapf --in-place $(YAPF_FLAGS)
	$(ENV) isort $(ISORT_FLAGS)
	npm run format

.PHONY: check-format
check-format: install-deps
	$(ENV) yapf --diff $(YAPF_FLAGS)
	$(ENV) isort --check-only $(ISORT_FLAGS)
	npm run check-format

.PHONY: test
test: install
	$(ENV) coverage erase
	$(ENV) pytest $(TEST_FILE) $(TEST_FLAGS)
	$(ENV) coverage report -m codegra_fs/cgfs.py

.PHONY: test_quick
test_quick: TEST_FLAGS += -x
test_quick: test

.PHONY: check
check: check-format mypy lint test

.PHONY: build
build: check
	$(ENV) python ./build.py
