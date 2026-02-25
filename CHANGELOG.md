# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project follows [Semantic Versioning](https://semver.org/).

## [0.4.0] - 2026-02-25

### Added

- Packaging with `pyproject.toml`.
- Console scripts: `daryl-memory` and `dsm-webui`.
- CI workflow (`.github/workflows/ci.yml`) with tests + build.
- Release workflow (`.github/workflows/release-pypi.yml`) for PyPI.
- Deployment assets: `Dockerfile`, `docker-compose.yml`, `.dockerignore`.
- Contribution and security docs: `CONTRIBUTING.md`, `SECURITY.md`.
- Developer tooling: `Makefile`, `.pre-commit-config.yaml`.

### Changed

- Runtime logs are quiet by default, with `--verbose` in CLI.
- Warnings/errors redirected to stderr.
- Runtime portability improvements around `DSM_MEMORY_DIR`.
