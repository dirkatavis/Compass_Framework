# Compass Framework – AI Coding Agent Guide

## Big picture
- **Protocol-first architecture**: All interfaces are `@runtime_checkable` Protocol classes in src/compass_core. Each protocol file contains both the protocol definition and concrete implementations (e.g., `Navigator` protocol + `SeleniumNavigator` class in navigation.py, `Configuration` + `IniConfiguration`/`JsonConfiguration` in separate files).
- **Public API**: Re-exported through src/compass_core/__init__.py with conditional imports for optional dependencies (Selenium) and Windows-only features (`BrowserVersionChecker`). Missing dependencies result in components not being exported, not import errors.
- **Workflow orchestration**: `Workflow` protocol defines `id()`, `plan()`, `run()` interface. Concrete implementations: `VehicleLookupFlow` (batch MVA processing), `PmWorkItemFlow` (work item creation). Steps use `FlowContext` (dataclass with mva, params, logger, actions).

## Key workflows & data flow
- **Vehicle lookup**: CSV → `read_mva_list()` normalizes to 8 digits → `MvaCollection` tracks status (PENDING/PROCESSING/COMPLETED/FAILED) → `SmartLoginFlow` detects SSO cache hit/miss → `SeleniumVehicleDataActions` retrieves VIN/Desc → `write_results_csv()`. See vehicle_lookup_flow.py, csv_utils.py, mva_collection.py.
- **Workitem creation**: CSV with MVA/DamageType/CorrectionAction → login → `SeleniumPmActions.has_open_workitem()/complete_open_workitem()/associate_pm_complaint()` → PM flow step execution. See pm_work_item_flow.py, pm_actions_selenium.py.
- **Smart authentication**: `SmartLoginFlow` wraps `SeleniumLoginFlow`, navigates to app_url first, detects if redirected to login page (cache miss) vs. already authenticated (cache hit), only performs login when needed. SSO cache behavior: incognito=True forces login every time.
- **Page verification**: `Navigator.verify_page()` checks document.readyState, optional URL prefix match (startswith), optional element presence check via Tuple[str, str] locator.

## Configuration & optional deps
- **Config files**: webdriver.ini is template (committed), webdriver.ini.local for local overrides (gitignored). Required sections: [credentials] (username/password/login_id), [app] (login_url/app_url), [webdriver] (driver paths), [options] (headless/window_size).
- **Driver paths**: Resolved from INI [webdriver] section or drivers.local/ folder. StandardDriverManager supports incognito=True kwarg for fresh sessions.
- **Optional install**: Base framework has no Selenium dependency. `pip install -e .[selenium]` or `.[web]` adds Selenium support, enables all Navigator/LoginFlow/VehicleDataActions implementations.
- **Windows-only**: `BrowserVersionChecker` uses winreg to check installed browser versions, only exported on Windows (conditional import in __init__.py).
- **Environment variables**: COMPASS_USERNAME, COMPASS_PASSWORD, COMPASS_LOGIN_ID override INI credentials.

## Testing & execution
- **Preferred runner**: `python run_tests.py unit|integration|e2e|all` with optional `--enable-e2e` flag. E2E tests skip unless flag set or category=e2e, controlled by `unittest._e2e_enabled` global.
- **E2E prerequisites**: Requires credentials in webdriver.ini.local or environment variables; tests check config validity and skip if missing. See tests/e2e/README.md.
- **Client execution**: Navigate to client directory first (clients/vehicle_lookup/ or clients/create_missing_workitems/), then run main.py or CreateMissingWorkItems.py. Clients add src/ to sys.path as fallback for editable install.
- **Test structure**: tests/unit/ (component isolation), tests/integration/ (multi-component), tests/e2e/ (browser automation). Page Object Model classes only in tests/e2e/pages/ (e.g., login_page.py), never in production code.

## Conventions that matter here
- **Protocol-first development**: Always define or update protocol file first, then implement. Naming: protocol name + implementation descriptor (`Configuration` → `IniConfiguration`, `JsonConfiguration`; `Navigator` → `SeleniumNavigator`; `DriverManager` → `StandardDriverManager`).
- **Conditional exports**: New optional components must be added to src/compass_core/__init__.py within try/except block, append to `__all__` if import succeeds. ImportError means dependency missing, not code error.
- **Version sync**: Bumping version requires updating both pyproject.toml [project].version and src/compass_core/engine.py `CompassRunner.version` field.
- **MVA normalization**: `read_mva_list()` auto-normalizes to 8 digits via regex (prefers leading 8 digits, fallback to first 8 chars), set normalize=False to disable. CSV rows starting with '#' or 'MVA' treated as headers/comments.
- **Return dictionaries**: Protocol methods return Dict[str, Any] with 'status' key ('success'/'failure'/'ok'/'error'), optional 'error' message, relevant data fields. Enables consistent error handling without exceptions.

## Example touchpoints
- **Protocols**: src/compass_core/configuration.py, navigation.py, driver_manager.py, workflow.py, login_flow.py, vehicle_data_actions.py, pm_actions.py, logging.py
- **Implementations**: src/compass_core/ini_configuration.py, json_configuration.py, selenium_navigator.py, standard_driver_manager.py, selenium_login_flow.py, smart_login_flow.py, selenium_vehicle_data_actions.py, pm_actions_selenium.py
- **Flows**: src/compass_core/vehicle_lookup_flow.py, pm_work_item_flow.py
- **Utilities**: src/compass_core/csv_utils.py (read_mva_list, write_results_csv, read_workitem_list), mva_collection.py (MvaCollection, MvaItem, MvaStatus enum)
- **Clients**: clients/vehicle_lookup/main.py, clients/create_missing_workitems/CreateMissingWorkItems.py
- **Entry point**: src/compass_core/engine.py (CompassRunner)