#!/usr/bin/env bash
# Run unit tests using the project's unified test runner (run_tests.py)
# Usage: ./scripts/run_unit.sh
set -euo pipefail

echo "Running unit tests via run_tests.py..."
python run_tests.py unit
