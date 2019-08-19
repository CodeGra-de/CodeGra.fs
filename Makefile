export PYTHONPATH = $(CURDIR)
MYPY_FLAGS += --package codegra_fs
PYLINT_FLAGS += --rcfile=setup.cfg codegra_fs
YAPF_FLAGS += --recursive --parallel codegra_fs
ISORT_FLAGS += --recursive codegra_fs
TEST_FILE ?= test/
TEST_FLAGS += -vvv

ENV = . env/bin/activate;

VERSION = $(shell node -e 'console.log(require("./package.json").version)')
UNAME = $(shell uname | tr A-Z a-z)

.PHONY: run
run: install
	$(ENV) npm run dev

env:
	virtualenv --python=python3 env

.PHONY: install-deps
install-deps: env/.install-deps env/.install-deps-$(UNAME) node_modules/.install-deps
env/.install-deps: requirements.txt | env
	$(ENV) pip3 install -r $^
	date >$@
env/.install-deps-$(UNAME): requirements-$(UNAME).txt | env
	$(ENV) pip3 install -r $^
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
	$(ENV) pylint $(PYLINT_FLAGS)
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
	npm run unit

.PHONY: test-quick
test-quick: TEST_FLAGS += -x
test-quick: test

.PHONY: check
check: check-format mypy lint test

.PHONY: build
build: install-deps check build-$(UNAME)

.PHONY: build-quick
build-quick: install-deps build-$(UNAME)

dist/cgfs: codegra_fs/*.py
	$(ENV) pyinstaller \
		--noconfirm \
		--onedir \
		--specpath dist \
		--name cgfs \
		codegra_fs/cgfs.py

dist/cgapi-consumer: codegra_fs/*.py
	$(ENV) pyinstaller \
		--noconfirm \
		--onedir \
		--specpath dist \
		--name cgapi-consumer \
		codegra_fs/api_consumer.py

.PHONY: build-darwin
build-darwin: dist/CodeGrade\ Filesystem\ $(VERSION).pkg

.PHONY: dist/CodeGrade Filesystem $(VERSION).pkg
dist/CodeGrade\ Filesystem\ $(VERSION).pkg: dist/mac | build/pkg-scripts/osxfuse.pkg
	pkgbuild --root dist/mac \
		--install-location /Applications \
		--component-plist build/com.codegrade.codegrade-fs.plist \
		--scripts build/pkg-scripts \
		"$@"

build/pkg-scripts/osxfuse.pkg:
	@printf 'Download the osxfuse dmg from https://osxfuse.github.io/\n' >&2
	@printf 'mount it and copy the .pkg file in it to\n' >&2
	@printf 'build/pkg-scripts/osxfuse.pkg\n' >&2
	exit 1

.PHONY: dist/mac
dist/mac: dist/cgfs dist/cgapi-consumer
	npm run build:mac

.PHONY: build-win
build-win:
	python .\build.py

.PHONY: build-linux
build-linux: build-linux-deb

.PHONY: build-linux-deb
build-linux-deb: build-linux-deb-frontend build-linux-deb-backend

.PHONY: build-linux-deb-frontend
build-linux-deb-frontend: dist/codegrade-fs_$(VERSION)_amd64.deb dist/codegrade-fs_$(VERSION)_i386.deb

.PHONY: dist/codegrade-fs_$(VERSION)_amd64.deb
dist/codegrade-fs_$(VERSION)_amd64.deb:
	npm run build:linux:x64

.PHONY: dist/codegrade-fs_$(VERSION)_i386.deb
dist/codegrade-fs_$(VERSION)_i386.deb:
	npm run build:linux:ia32

.PHONY: build-linux-deb-backend
build-linux-deb-backend: dist/python3-codegrade-fs_$(VERSION)-1_all.deb

.PHONY: dist/python3-codegrade-fs_$(VERSION)-1_all.deb
dist/python3-codegrade-fs_$(VERSION)-1_all.deb: dist/python3-fusepy_3.0.1-1_all.deb build/deb.patch
	dpkg -s python3-fusepy || sudo dpkg -i dist/python3-fusepy_3.0.1-1_all.deb
	git apply build/deb.patch
	trap 'rm -rf codegrade_fs.egg-info codegrade-fs-$(VERSION).tar.gz; \
		git apply --reverse build/deb.patch' 0 1 2 3 15; \
	$(ENV) python3 setup.py --command-packages=stdeb.command bdist_deb
	mkdir -p dist
	mv deb_dist/*.deb dist

build/deb.patch: codegra_fs/*.py
	build/make-deb-patch.sh

dist/python3-fusepy_3.0.1-1_all.deb:
	mkdir -p dist
	curl -L -o "$@" 'http://ftp.us.debian.org/debian/pool/main/p/python-fusepy/python3-fusepy_3.0.1-1_all.deb'

.PHONY: docs
docs: install-deps-docs
	$(ENV) $(MAKE) -C docs html

.PHONY: install-deps-docs
install-deps-docs: env/.install-deps-docs
env/.install-deps-docs: requirements-docs.txt | env
	$(ENV) pip3 install -r $^
	date >$@
