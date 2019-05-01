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
install-deps: env/.install-deps node_modules/.install-deps
env/.install-deps: requirements.txt requirements-darwin.txt requirements-linux.txt | env
	$(ENV) pip3 install -r requirements.txt
	if [ -f requirements-$(UNAME).txt ]; then \
		$(ENV) pip3 install -r requirements-$(UNAME).txt; \
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
build-darwin: dist/mac | build/pkg-scripts/osxfuse.pkg
	pkgbuild --root dist/mac \
		--install-location /Applications \
		--component-plist build/com.codegrade.codegrade-fs.plist \
		--scripts build/pkg-scripts \
		"dist/CodeGrade\ Filesystem\ $(VERSION).pkg "

dist/mac: dist/cgfs dist/cgapi-consumer
	npm run build:mac

.PHONY: build-win
build-win: | dist/winfsp.msi
	npm run build:win

dist/winfsp.msi:
	curl -L -o "$@" 'https://github.com/billziss-gh/winfsp/releases/download/v1.4.19049/winfsp-1.4.19049.msi'

.PHONY: build-linux
build-linux: build-linux-deb

.PHONY: build-linux-deb
build-linux-deb: build-linux-deb-frontend build-linux-deb-backend

.PHONY: build-linux-deb-frontend
build-linux-deb-frontend:
	npm run build:linux

.PHONY: build-linux-deb-backend
build-linux-deb-backend:
	git apply build/ubuntu-deb.patch
	$(ENV) python3 setup.py --command-packages=stdeb.command bdist_deb
	git apply --reverse build/ubuntu-deb.patch
	mv deb_dist/*.deb dist
	rm -rf deb_dist
	rm -rf codegrade_fs.egg-info
	rm -f codegrade-fs-1.0.0.tar.gz
