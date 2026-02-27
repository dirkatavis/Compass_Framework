Running Tests — Compass_Framework

This repository provides a unified test runner and simple scripts to make running tests consistent across projects.

Quick steps (recommended):

- Create and activate a virtual environment, install dev requirements:

  PowerShell:

  ```powershell
  python -m venv .venv
  . .venv\Scripts\Activate.ps1
  pip install -r requirements-dev.txt
  ```

  Bash / macOS / Linux:

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements-dev.txt
  ```

- Run the unified test runner (preferred):

  ```bash
  python run_tests.py unit
  ```

- Or use the provided quick-run scripts in scripts/:

  - PowerShell: ./scripts/run_unit.ps1
  - Bash: ./scripts/run_unit.sh

- To run only pytest-style tests directly:

  ```bash
  python -m pytest -q tests/unit
  python -m pytest -q tests/unit -m new_slice   # run only the new slice
  ```

Notes & conventions
- End-to-end (`e2e`) tests are excluded by default. Marker `new_slice` is available for running the new tests slice.
- `run_tests.py` will run legacy `unittest` discovery first and then, if `pytest` is installed, run `pytest` on the same test directory.
- If you prefer a tool-managed environment, install dependencies from `requirements-dev.txt` above.

If you'd like, I can add this repository to CI with a matching matrix and a reproducible dev environment.
