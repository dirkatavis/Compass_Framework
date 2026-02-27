Summary of changes in feature/new-tests

This branch adds a unified test slice, improves test ergonomics, and fixes a
small integration bug uncovered by the new tests.

What I changed
- Tests and infra
  - Added pytest-based unit tests under `tests/unit` (new slice marked with
    `@pytest.mark.new_slice`) and integration tests under `tests/integration`.
  - Added `tests/unit/run_unit_tests.py` and `tests/integration/run_integration_tests.py`
    so contributors can find a single, discoverable entrypoint inside each
    test folder.
  - Added `TESTING.md` with quick setup and run instructions.
  - Added `pytest.ini` to register markers and exclude `e2e` tests by default.
  - Added `requirements-dev.txt` listing `pytest` and `pytest-mock` for dev
    installs.

- Runner
  - Updated `run_tests.py` to run legacy `unittest` discovery and then invoke
    `pytest` programmatically when available for a single unified command.

- Production fixes (tests revealed brittle behavior)
  - `src/compass_core/smart_login_flow.py`
    - Added `_detect_login_page()` compatibility helper so existing tests that
      patch that attribute do not error.
    - Replaced inline detection code with a call to `_detect_login_page()` so
      test patches control behavior.
    - Made handling of `driver.window_handles` robust to mocks that don't
      implement `len()` or indexing.

Why these changes
- Make the testing workflow discoverable and consistent across projects by
  providing per-folder entrypoints (`run_unit_tests.py` and
  `run_integration_tests.py`) and a `TESTING.md` doc.
- Keep the unified runner as the single command for local dev and CI.
- Fix brittle behavior found by integration tests so the test suite is
  stable across environments and mock objects.

Test status
- Local runs executed via `python run_tests.py unit` and
  `python run_tests.py integration` — all unit and integration tests pass
  locally (unit: 384/384; pytest: 417/417; integration: 11/11).

Suggested PR body actions
- Copy this file into the GitHub PR description, then add reviewers.
- Optional: add a small GitHub Actions workflow that runs `python run_tests.py
  unit` and `python run_tests.py integration` on PRs. I can add that as a
  follow-up.

Notes
- I intentionally added `requirements-dev.txt` rather than modifying
  `pyproject.toml` so dev deps are explicit and easy to install; happy to
  add `pytest` to `pyproject.toml` instead if you prefer.
