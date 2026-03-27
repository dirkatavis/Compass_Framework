"""Developer wrapper for the installable inventory exporter.

This keeps local repo usage (`python tools/export_inventory.py`) aligned with the
canonical implementation in `compass_core.tools.export_inventory`.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


# Ensure local /src is importable when running from the repository checkout.
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
CANONICAL_MODULE_PATH = SRC_DIR / "compass_core" / "tools" / "export_inventory.py"


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "compass_core.tools.export_inventory",
        str(CANONICAL_MODULE_PATH),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load exporter module from {CANONICAL_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


if __name__ == "__main__":
    main()
