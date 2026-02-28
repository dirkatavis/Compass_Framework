#!/usr/bin/env python3
"""Run unit tests for this repository.

This script invokes the repository's unified test runner to run the unit tests
so contributors can find a clear entrypoint in the `tests/unit` folder.
"""
import os
import subprocess
import sys


def main() -> int:
    here = os.path.dirname(__file__)
    runner = os.path.abspath(os.path.join(here, "..", "..", "run_tests.py"))
    return subprocess.call([sys.executable, runner, "unit"])


if __name__ == "__main__":
    sys.exit(main())
