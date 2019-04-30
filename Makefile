export PYTHONPATH = $(CURDIR)
MYPY_FLAGS += --package codegra_fs
PYLINT_FLAGS += --rcfile=setup.cfg codegra_fs
YAPF_FLAGS += --recursive --parallel codegra_fs
ISORT_FLAGS += --recursive codegra_fs
TEST_FILE ?= test/
TEST_FLAGS += -vvv

ENV = . env/bin/activate;

UNAME = $(shell uname | tr A-Z a-z)

.PHONY: run
run: install
	$(ENV) npm run dev

env:
	virtualenv --python=python3 env

.PHONY: install-deps
install-deps: env/.install-deps node_modules/.install-deps
env/.install-deps: requirements.txt requirements-mac.txt | env
	$(ENV) pip3 install -r requirements.txt
	if [ "$(UNAME)" -eq 'darwin' ]; then \
		$(ENV) pip3 install -r requirements-mac.txt; \
	fi
	date >$@
node_modules/.install-deps: package.json
	npm install
	date >$@

.PHONY: install
install: install-deps env/bin/cgfs env/bin/cgapi-consumer
env/bin/%: setup.py codegra_fs/*.py
	$(ENV) pip3 install .

.PHONY: mypy
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
build: check build-$(UNAME)
	$(ENV) python3 ./build.py

dist/cgfs: codegra_fs/*.py
	$(ENV) pyinstaller \
		--noconfirm \
		--onedir \
		--specpath dist \
		--name cgfs \
		--icon static/icons/icon.icns \
		codegra_fs/cgfs.py

dist/cgapi-consumer: codegra_fs/*.py
	$(ENV) pyinstaller \
		--noconfirm \
		--onedir \
		--specpath dist \
		--name cgapi-consumer \
		--icon static/icons/icon.icns \
		codegra_fs/api_consumer.py

.PHONY: build-darwin
build-darwin: dist/CodeGrade\ Filesystem.pkg
dist/CodeGrade\ Filesystem.pkg: dist/cgfs dist/cgapi-consumer | build/pkg-scripts/osxfuse.pkg
	npm run build:mac
	pkgbuild --root dist/mac \
		--install-location /Applications \
		--component-plist build/com.codegrade.codegrade-fs.plist \
		--scripts build/pkg-scripts \
		"$@"

.PHONY: build-win
build-win: dist/CodeGrade\ Filesystem.exe
dist/CodeGrade\ Filesystem.exe: dist/cgfs dist/cgapi-consumer | dist/winfsp.msi
	npm run build:win

dist/winfsp.msi:
	curl -L -o "$@" 'https://github.com/billziss-gh/winfsp/releases/download/v1.4.19049/winfsp-1.4.19049.msi'

.PHONY: build-linux
build-linux:
	npm run build:linux
