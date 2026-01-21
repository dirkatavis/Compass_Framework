# Compass Framework – AI Coding Agent Guide

## Big picture
- Protocol-first core lives in src/compass_core: `@runtime_checkable` protocols define interfaces; concrete implementations sit alongside them (e.g., navigation/configuration/driver/logging protocols with Selenium/INI/JSON implementations).
- Public API is re-exported in src/compass_core/__init__.py with conditional imports for optional deps (Selenium) and Windows-only features (BrowserVersionChecker).
- Flows are protocol-driven: `Workflow` with `id()`, `plan()`, `run()`; concrete flows include `VehicleLookupFlow` and `PmWorkItemFlow`.

## Key workflows & data flow
- Vehicle lookup: read MVAs → normalize/track via `MvaCollection` → login via `LoginFlow`/`SmartLoginFlow` → navigate → `VehicleDataActions` → write CSV (see src/compass_core/vehicle_lookup_flow.py and csv_utils.py).
- Workitem creation: CSV specs → login → MVA entry → PM actions find/create (see src/compass_core/pm_work_item_flow.py and pm_actions_selenium.py).
- URL verification supports redirects: `Navigator.verify_page(..., match="domain|prefix|exact")` in src/compass_core/navigation.py.

## Configuration & optional deps
- webdriver.ini is the template; local overrides in webdriver.ini.local (gitignored). Drivers go in drivers.local/; paths resolved from INI or local folder.
- Selenium features require extras: `pip install -e .[selenium]` (alias `.[web]`).
- Windows-only version checks use winreg in src/compass_core/browser_version_checker.py and are conditionally exported.

## Testing & execution
- Preferred runner: `python run_tests.py unit|integration|e2e|all` (E2E is skipped unless `--enable-e2e`).
- E2E skip gate is `unittest._e2e_enabled`; tests also skip without credentials (see tests/e2e/README.md).
- Client scripts validate real workflows in clients/vehicle_lookup and clients/create_missing_workitems.

## Conventions that matter here
- Protocol-first: add/modify protocol file first, then implement; keep naming explicit (`JsonConfiguration`, `SeleniumNavigator`, `StandardDriverManager`).
- Conditional exports: add new optional components to src/compass_core/__init__.py behind try/except.
- Version bump requires syncing pyproject.toml and src/compass_core/engine.py (`CompassRunner.version`).
- Page Object Model lives only under tests/e2e/pages; production flows use protocols, not POMs.

## Example touchpoints
- Protocols: src/compass_core/configuration.py, navigation.py, driver_manager.py
- Implementations: src/compass_core/json_configuration.py, selenium_navigator.py, standard_driver_manager.py
- Flows: src/compass_core/vehicle_lookup_flow.py, pm_work_item_flow.py
- Clients: clients/vehicle_lookup/main.py, clients/create_missing_workitems/CreateMissingWorkItems.py