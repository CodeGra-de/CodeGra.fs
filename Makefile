export PYTHONPATH = $(CURDIR)
MYPY_FLAGS += --package codegra_fs
PYLINT_FLAGS += --rcfile=setup.cfg codegra_fs
YAPF_FLAGS += --recursive --parallel codegra_fs
ISORT_FLAGS += --recursive codegra_fs
TEST_FILE ?= test/
TEST_FLAGS += -vvv

VERSION = $(shell node -e 'console.log(require("./package.json").version)')
UNAME = $(shell python ./.scripts/get_os.py)

.PHONY: run
run: install
	npm run dev

.PHONY: install-deps
install-deps: node_modules/.install-deps
	pip install -r requirements.txt
	pip install -r requirements-$(UNAME).txt

node_modules/.install-deps: package.json
	npm ci
	date >$@

.PHONY: install
install: install-deps env/bin/cgfs env/bin/cgapi-consumer
env/bin/%: setup.py codegra_fs/*.py
	pip install .

.PHONY: mypy
mypy: install-deps
	mypy $(MYPY_FLAGS)

.PHONY: lint
lint: install-deps
	pylint $(PYLINT_FLAGS)
	npm run lint

.PHONY: format
format: install-deps
	yapf --in-place $(YAPF_FLAGS)
	isort $(ISORT_FLAGS)
	npm run format

.PHONY: check-format
check-format: install-deps
	yapf --diff $(YAPF_FLAGS)
	isort --check-only $(ISORT_FLAGS)
	npm run check-format

.PHONY: test
test: install
	coverage erase
	pytest $(TEST_FILE) $(TEST_FLAGS)
	coverage report -m codegra_fs/cgfs.py
	npm run unit

.PHONY: travis_test
travis_test:
	npm run unit
	coverage erase
	pytest $(TEST_FILE) $(TEST_FLAGS)
	coverage report -m codegra_fs/cgfs.py

.PHONY: test-quick
test-quick: TEST_FLAGS += -x
test-quick: test

.PHONY: check
check: check-format mypy lint test

.PHONY: build
build: install check build-$(UNAME)

.PHONY: build-quick
build-quick: install build-$(UNAME)

dist/cgfs: codegra_fs/*.py
	pyinstaller \
		--noconfirm \
		--onedir \
		--specpath dist \
		--additional-hooks-dir=./pyinstaller_hooks \
		--name cgfs \
		codegra_fs/cgfs.py

dist/cgapi-consumer: codegra_fs/*.py
	pyinstaller \
		--noconfirm \
		--onedir \
		--specpath dist \
		--additional-hooks-dir=./pyinstaller_hooks \
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
	bash ./.scripts/get_macfuse.bash

.PHONY: dist/mac
dist/mac: dist/cgfs dist/cgapi-consumer
	npm run build:mac

.PHONY: build-win
build-win:
	python .\build.py

.PHONY: build-linux
build-linux: build-linux-deb
	python .scripts/make_install_linux_script.py

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
	trap 'rm -rf codegrade_fs.egg-info codegrade-fs-$(VERSION).tar.gz;' 0 1 2 3 15; \
	python setup.py --command-packages=stdeb.command bdist_deb
	mkdir -p dist
	mv deb_dist/*.deb dist

build/deb.patch: codegra_fs/*.py
	build/make-deb-patch.sh

dist/python3-fusepy_3.0.1-1_all.deb:
	mkdir -p dist
	curl -L -o "$@" 'http://ftp.us.debian.org/debian/pool/main/p/python-fusepy/python3-fusepy_3.0.1-1_all.deb'

.PHONY: docs
docs: install-deps-docs
	$(MAKE) -C docs html

.PHONY: install-deps-docs
install-deps-docs: env/.install-deps-docs
env/.install-deps-docs: requirements-docs.txt | env
	pip install -r $^
	date >$@
