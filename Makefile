PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install install-web install-dev test build clean run-cli run-web precommit docker-build docker-up docker-down

install:
	$(PIP) install -e .

install-web:
	$(PIP) install -e ".[web]"

install-dev:
	$(PIP) install -e ".[dev,web]"

test:
	$(PYTHON) -m unittest discover -s tests -q

build:
	$(PIP) install --quiet build
	$(PYTHON) -m build

precommit:
	pre-commit run --all-files

run-cli:
	$(PYTHON) -m cli.daryl_memory_cli status

run-web:
	$(PYTHON) -m webui.app

docker-build:
	docker build -t dsm:latest .

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	rm -rf build dist .pytest_cache *.egg-info
