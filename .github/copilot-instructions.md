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
- **Test structure**: 
  - Protocol compliance in `tests/unit/test_*_interface.py` (verify protocol adherence using mock implementations)
  - Implementation tests in `tests/unit/test_*.py` (test concrete classes)
  - Cross-component in [tests/integration](tests/integration) (verify protocol interactions)
  - Browser automation in [tests/e2e](tests/e2e) (full workflows with real WebDriver)
- **E2E skip mechanism**: Tests check `hasattr(unittest, '_e2e_enabled')` and skip if false. Enabled via `unittest._e2e_enabled = True` or `--enable-e2e` flag.
- **Test counts**: 361 unit tests (360 passing, 1 known failure), ~7 integration, ~4 E2E (as of Jan 20, 2026).

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

## URL Verification Strategies (SSO & Redirects)
- **Domain matching**: Use `verify_page(url="https://host.com/...", match="domain")` to tolerate SSO/multipass redirects while checking scheme+netloc.
- **Prefix matching** (default): `match="prefix"` for strict path prefix verification.
- **Exact matching**: `match="exact"` for absolute URL equality.
- Example: `navigator.verify_page(url="https://login.microsoftonline.com", match="domain")` succeeds even if redirected to `/common/oauth2/...`.

## PM Workflows & Business Flows
- **Protocol-first flows**: Define `Workflow` protocol with `id()`, `plan()`, `run()` methods; implement in concrete classes (e.g., [pm_work_item_flow.py](src/compass_core/pm_work_item_flow.py), [vehicle_lookup_flow.py](src/compass_core/vehicle_lookup_flow.py)).
- **PmActions protocol**: Abstract PM-specific actions (lighthouse status, workitem handling); implement in [pm_actions_selenium.py](src/compass_core/pm_actions_selenium.py).
- **VehicleLookupFlow**: Batch vehicle property lookup workflow implementing `Workflow` protocol; orchestrates login, MVA iteration, property retrieval, CSV output.
- **Flow context**: Flows receive `params: Dict[str, Any]` with runtime configuration (URLs, credentials, file paths, timeouts).
- **WorkflowStep**: Discrete action abstraction with `name` and `description` in `plan()` return value; used for visibility and tracking.
- **Graceful skips**: Flows return `{"status": "skipped", "reason": "..."}` for early exits (e.g., lighthouse rentable, no data).

## Page Object Model (POM) Patterns
- **Location**: E2E POMs in [tests/e2e/pages](tests/e2e/pages) (e.g., [login_page.py](tests/e2e/pages/login_page.py)).
- **Structure**: Locators as class constants (tuples), action methods, verification methods.
- **Example**: `MicrosoftLoginPage` encapsulates email/password fields, next/signin buttons, error messages.
- **Usage in flows**: Instantiate POM with driver, call action methods (e.g., `login_page.login(username, password)`).
- **Keep POM in tests**: Page objects belong in test folders; business logic uses protocol abstractions, not POMs directly.

## Driver Configuration & Incognito
- **Config priority**: `webdriver.ini.local` > `webdriver.ini` (template). Local file gitignored.
- **Driver paths**: Set in INI (`edge_path = drivers.local/msedgedriver.exe`) or use default fallback (`drivers.local/` then project root).
- **Incognito mode**: `StandardDriverManager.get_or_create_driver(incognito=True)` adds `--inprivate` for Edge.
- **Headless**: Combine `headless=True` and `incognito=True` as needed; note headless may alter auth flows.

## Usage Examples
- Core engine: `from compass_core import CompassRunner; CompassRunner().run()`.
- Configuration: `from compass_core import JsonConfiguration; cfg = JsonConfiguration(); data = cfg.load("settings.json"); cfg.validate()`.
- Version check (Windows): `from compass_core import BrowserVersionChecker; BrowserVersionChecker().check_compatibility("chrome")`.
- Navigation with SSO: `nav = SeleniumNavigator(driver); nav.navigate_to("https://app.com", verify=False); nav.verify_page(url="https://app.com", match="domain")`.
- Driver with incognito: `dm = StandardDriverManager(); driver = dm.get_or_create_driver(incognito=True, headless=False)`.
- PM flow: `flow = PmWorkItemFlow(); result = flow.run(FlowContext(mva="MVA123", logger=logger, params={...}))`.

## UI Flow Samples
- **Sample script**: [scripts/ui_flow_sample.py](scripts/ui_flow_sample.py) demonstrates login + optional MVA entry.
- **Credentials**: Pass via CLI args (`--username`, `--password`) or env vars (`UI_SAMPLE_USERNAME`, `UI_SAMPLE_PASSWORD`).
- **Locator syntax**: Use `css=.selector` or `xpath=//input[@name='field']` for `--mva-locator`.
- **Run example**: `python scripts/ui_flow_sample.py --url https://login.microsoftonline.com/ --incognito --username user@example.com`.

## Build & Integration
- Dev install: `pip install -e .` then run tests via [run_tests.py](run_tests.py).
- Selenium support: `pip install -e .[selenium]` (alias: `.[web]`) enables Navigator, DriverManager, LoginFlow, VehicleLookupFlow.
- Build: `python -m build` (artifacts ignored per .gitignore). 
- Client integration: See [clients/](clients/) for real-world usage examples; install framework in client projects via editable installs.

## Client Integration Pattern
- **Structure**: Clients in [clients/](clients/) demonstrate framework usage with real workflows.
- **vehicle_lookup**: Batch MVA processing client using `VehicleLookupFlow` to retrieve glass data (MVA, VIN, Description) from CSV lists.
- **create_missing_workitems**: Workitem creation/verification client that finds existing workitems or creates new ones based on CSV specifications (MVA, DamageType, CorrectionAction).
- **Shared config**: Clients use framework's `webdriver.ini.local` for credentials and sample data files in `data/` for test input.
- **Development flow**: Framework-first (add protocol/implementation) → Test → Client validation → Iterate.
- **Client execution**: From repo root, activate venv (`.\.venv-1\Scripts\Activate.ps1`), then `cd clients/<client_name>; python main.py` or `python CreateMissingWorkItems.py`.

## Vehicle Lookup & Batch Processing
- **VehicleLookupFlow**: Orchestrates complete MVA→property workflow: authenticate, read MVA list, iterate lookups, write CSV results.
- **MvaCollection**: State tracking for batch MVA processing with `MvaItem` (status: pending/processing/completed/failed) and progress methods (`pending_count()`, `completed_count()`, `progress_percentage()`).
- **CSV utilities**: `read_mva_list(csv_path)` normalizes 8-digit MVAs, skips headers/comments; `write_results_csv(csv_path, results)` writes structured output; `read_workitem_list(csv_path)` reads workitem specifications.
- **MVA normalization**: Leading 8 digits preferred; if <8 digits, left-pad with zeros; preserves raw in comments if normalized differs.
- **VehicleDataActions protocol**: `enter_mva()`, `get_vehicle_property()`, `get_vehicle_properties()`, `verify_mva_echo()`, `wait_for_property_loaded()`.

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