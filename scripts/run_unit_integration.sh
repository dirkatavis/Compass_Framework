#!/usr/bin/env bash
# Run unit and integration tests sequentially using the existing test runner.
# Usage: ./scripts/run_unit_integration.sh
set -euo pipefail

echo "Running unit tests..."
python run_tests.py unit

echo "Running integration tests..."
python run_tests.py integration

echo "All unit and integration tests passed."
