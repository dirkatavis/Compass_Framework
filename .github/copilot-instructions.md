# Compass Framework – AI Coding Agent Guide

Goal: Equip agents to work productively in this repo by codifying the big-picture architecture, key workflows, and project-specific conventions.

## Architecture Overview
- **Source layout**: All code under [src/compass_core](src/compass_core) following a protocol-first design with `@runtime_checkable` interfaces.
- **Protocols → Implementations**: Interfaces in files like [navigation.py](src/compass_core/navigation.py), [configuration.py](src/compass_core/configuration.py), [version_checker.py](src/compass_core/version_checker.py), [logging.py](src/compass_core/logging.py), [driver_manager.py](src/compass_core/driver_manager.py). Implementations live alongside them (e.g., [json_configuration.py](src/compass_core/json_configuration.py), [ini_configuration.py](src/compass_core/ini_configuration.py), [selenium_navigator.py](src/compass_core/selenium_navigator.py), [standard_driver_manager.py](src/compass_core/standard_driver_manager.py), [browser_version_checker.py](src/compass_core/browser_version_checker.py)).
- **Public API**: Exported via [src/compass_core/__init__.py](src/compass_core/__init__.py) with conditional imports. Optional components (Selenium, Windows-only `BrowserVersionChecker`) are added when dependencies/platform are available.
- **Core engine**: [src/compass_core/engine.py](src/compass_core/engine.py) defines `CompassRunner.run()` for activation/status; used for simple sanity checks and version display.

## Version Synchronization (Critical)
- Update both: [pyproject.toml](pyproject.toml) and [src/compass_core/engine.py](src/compass_core/engine.py) when bumping versions.
  - pyproject: `version = "0.1.0"`
  - engine: `self.version = "0.1.0"`

## Testing & Workflows
- **Preferred runner**: [run_tests.py](run_tests.py) orchestrates categories with fast defaults.
  - Unit: `python run_tests.py unit`
  - Integration: `python run_tests.py integration`
  - E2E: `python run_tests.py --enable-e2e e2e`
  - All: `python run_tests.py all` (E2E skipped by default; enable with `--enable-e2e`)
- **Direct unittest**: `python -m unittest discover tests -v` or per folder under [tests](tests).
- **Test structure**: Protocol compliance in `tests/unit/test_*_interface.py`, implementations in `tests/unit/test_*.py`, cross-component in [tests/integration](tests/integration), browser automation in [tests/e2e](tests/e2e).

## Optional Dependencies & Platforms
- **Selenium features**: Install extras to enable navigator/driver manager.
  - Dev install: `pip install -e .[selenium]` (alias: `.[web]`)
- **Windows-only**: [browser_version_checker.py](src/compass_core/browser_version_checker.py) uses `winreg`; exported only on Windows.

## WebDriver Configuration (E2E)
- Use [webdriver.ini](webdriver.ini) as a template; create local overrides in [webdriver.ini.local](webdriver.ini.local).
- Place local drivers in [drivers.local](drivers.local) and reference paths in `webdriver.ini.local` (see [drivers.local/README.md](drivers.local/README.md)).
- E2E tests are skipped by default to avoid failing builds without drivers.

## Conventions & Patterns
- **Protocol-first**: Define `@runtime_checkable` Protocols (e.g., in [configuration.py](src/compass_core/configuration.py)); implement separately (e.g., [json_configuration.py](src/compass_core/json_configuration.py)).
- **Conditional imports**: Add implementations to public API in [__init__.py](src/compass_core/__init__.py) behind `try/except` for optional deps.
- **Graceful degradation**: Missing deps → features unavailable, tests skip when platform/deps absent.
- **Naming**: Implementations use explicit names (`JsonConfiguration`, `IniConfiguration`, `SeleniumNavigator`, `StandardDriverManager`, `StandardLoggerFactory`).

## Usage Examples
- Core engine: `from compass_core import CompassRunner; CompassRunner().run()`.
- Configuration: `from compass_core import JsonConfiguration; cfg = JsonConfiguration(); data = cfg.load("settings.json"); cfg.validate()`.
- Version check (Windows): `from compass_core import BrowserVersionChecker; BrowserVersionChecker().check_compatibility("chrome")`.
- Navigation (optional): `from compass_core import SeleniumNavigator; nav = SeleniumNavigator(webdriver); nav.navigate_to("https://example.com", verify=True)`.

## Build & Integration
- Dev install: `pip install -e .` then run tests via [run_tests.py](run_tests.py).
- Build: `python -m build` (artifacts ignored per .gitignore). 
- Client integration: install this repo into client projects via editable installs (see project docs) and validate client integration before pushing.

If any section is unclear or missing, tell me which workflows or files need elaboration and I’ll refine this guide.

## Coding Expectations
- **TDD-first**: Write failing tests before implementing protocols/implementations; use [tests/unit](tests/unit), [tests/integration](tests/integration), and gate E2E in [tests/e2e](tests/e2e).
- **DRY**: Extract shared logic into focused helpers or protocols; avoid duplication across implementations.
- **SOLID**: Keep single-responsibility modules; depend on abstractions (Protocols) not concretions; open for extension via new implementations.
- **POM**: When adding web flows, follow Page Object Model patterns inside navigator-related code; keep page semantics separate from flow orchestration.
- **Protocol-first**: Define `@runtime_checkable` Protocols (e.g., [configuration.py](src/compass_core/configuration.py)) before implementations; add conditional exports in [__init__.py](src/compass_core/__init__.py).
- **Type hints & docstrings**: Use explicit typing across public APIs; add concise docstrings describing intent and usage.
- **Graceful degradation**: Guard optional deps and platform specifics with `try/except` and `skipIf` in tests; see [browser_version_checker.py](src/compass_core/browser_version_checker.py).
- **Version sync**: Update both [pyproject.toml](pyproject.toml) and [engine.py](src/compass_core/engine.py) together.
- **Quality gates**: Before starting work and before merging, run `python run_tests.py all`; enable E2E when relevant with `--enable-e2e`.

## Development Workflow
- **Always branch first**: Create a new feature branch before coding; avoid direct commits to `main`.
- **PR via Copilot**: Open a pull request using GitHub Copilot; include rationale and links to tests.
- **Re-sync and retest**: After pulling latest `main` into your branch, re-run the full test suite (enable E2E when applicable).