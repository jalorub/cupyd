# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2024-10-14

### Added

- Documentation tentative using MKDocs (#29).
- CHANGELOG.md (#29).
- mypy (#27).
- Python 3.13 support (#27).
- Code coverage with Coveralls (#27).

### Changed

- Placed all flake8, black & mypy config inside `pyproject.toml` (#27).
- CI now run tests over ubuntu, macOS & windows (#27).

### Fixed

- Default maxsize (100k) for Queues in macOS caused an error. Now, if the specified maxsize is
  bigger than the OS bounded semaphore limit, maxsize will be set to that limit while logging a
  warning (#27).
- Ensure mypy passes for python3.9 (#27).

## [0.1.0] - 2024-10-08

- Initial release
