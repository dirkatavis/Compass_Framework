"""
apply_compass_public.py - First-pass application of @compass_public decorator.

This script adds `@compass_public` to classes and methods in the
Compass Framework source that are clearly part of the public API contract.
Run once; afterwards the decorator is maintained manually.

Usage:
    python tools/apply_compass_public.py [--src ./src/compass_core] [--dry-run]
"""
import ast
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Target map
# ---------------------------------------------------------------------------
# Format: { filename: { ClassName: [method_names] | True } }
# True means "all non-private methods defined in the class"
TARGETS: dict = {
    # --- Protocols (entire public contract) ---
    "configuration.py": {
        "Configuration": True,
    },
    "navigation.py": {
        "Navigator": True,
    },
    "driver_manager.py": {
        "DriverManager": True,
    },
    "login_flow.py": {
        "LoginFlow": True,
    },
    "vehicle_data_actions.py": {
        "VehicleDataActions": True,
    },
    "pm_actions.py": {
        "PmActions": True,
    },
    "version_checker.py": {
        "VersionChecker": True,
    },
    "logging.py": {
        "Logger": True,
        "LoggerFactory": True,
        "StandardLogger": ["debug", "info", "warning", "error", "critical"],
        "StandardLoggerFactory": ["create_logger"],
    },
    "workflow.py": {
        "WorkflowStep": True,
        "Workflow": True,
        "WorkflowManager": True,
        "StandardWorkflowManager": ["run"],
    },
    # --- Entry point ---
    "engine.py": {
        "CompassRunner": ["run"],
    },
    # --- Implementations (protocol-matching methods only) ---
    "ini_configuration.py": {
        "IniConfiguration": ["load", "save", "get", "set", "validate"],
    },
    "json_configuration.py": {
        "JsonConfiguration": ["load", "save", "get", "set", "validate"],
    },
    "selenium_navigator.py": {
        "SeleniumNavigator": ["navigate_to", "verify_page", "scroll_into_view_center"],
    },
    "standard_driver_manager.py": {
        "StandardDriverManager": True,
    },
    "selenium_login_flow.py": {
        "SeleniumLoginFlow": ["authenticate"],
    },
    "smart_login_flow.py": {
        "SmartLoginFlow": ["authenticate"],
    },
    "pm_actions_selenium.py": {
        "SeleniumPmActions": [
            "get_lighthouse_status",
            "has_open_workitem",
            "complete_open_workitem",
            "has_pm_complaint",
            "associate_pm_complaint",
            "navigate_back_home",
            "find_workitem",
            "create_workitem",
        ],
    },
    "selenium_vehicle_data_actions.py": {
        "SeleniumVehicleDataActions": [
            "enter_mva",
            "enter_vin",
            "get_vehicle_property",
            "get_vehicle_properties",
            "verify_mva_echo",
        ],
    },
    # --- Flows (Workflow protocol: id / plan / run) ---
    "vehicle_lookup_flow.py": {
        "VehicleLookupFlow": ["id", "plan", "run"],
    },
    "pm_work_item_flow.py": {
        "PmWorkItemFlow": ["id", "plan", "run"],
    },
    "vin_to_mva_flow.py": {
        "Vin2MvaFlow": ["id", "plan", "run"],
    },
}

IMPORT_LINE = "from .decorators import compass_public\n"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _insert_line_before(lines: list[str], lineno_1based: int, new_line: str) -> list[str]:
    """Return a new list with *new_line* inserted before *lineno_1based*."""
    idx = lineno_1based - 1
    return lines[:idx] + [new_line] + lines[idx:]


def _detect_encoding(path: Path) -> str:
    raw = path.read_bytes()
    return "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"


def _insert_import(lines: list[str]) -> list[str]:
    """Add the compass_public import if not already present.

    Inserts after the last existing `from .` or `from compass_core` import block,
    or after module docstring / __future__ import, whichever is latest.
    """
    if any(IMPORT_LINE.strip() in l for l in lines):
        return lines  # already imported

    # Find insertion point: after the leading import block only.
    insert_after = -1
    in_docstring = False
    docstring_done = False
    started_code = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Skip docstring block
        if not docstring_done:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if in_docstring:
                    in_docstring = False
                    docstring_done = True
                else:
                    in_docstring = True
                    if stripped.count('"""') >= 2 or stripped.count("'''") >= 2:
                        # Single-line docstring
                        in_docstring = False
                        docstring_done = True
                continue
            if in_docstring:
                continue
        if not stripped:
            if started_code and insert_after != -1:
                break
            continue

        if stripped.startswith('#'):
            continue

        if stripped.startswith("from ") or stripped.startswith("import "):
            insert_after = i
            started_code = True
            continue

        if insert_after != -1:
            break

    if insert_after == -1:
        # No import found; insert at the very start (before any code)
        return [IMPORT_LINE] + lines

    pos = insert_after + 1
    return lines[:pos] + [IMPORT_LINE] + lines[pos:]


def _collect_insertions(
    source: str,
    class_targets: dict,
) -> list[tuple[int, str]]:
    """Return (lineno_1based, text) pairs for every decorator line to insert.

    The returned list is in *ascending* lineno order.
    """
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    insertions: list[tuple[int, int, str]] = []  # (lineno, col_offset, text)

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        cls_name = node.name
        if cls_name not in class_targets:
            continue

        method_targets = class_targets[cls_name]

        # Decorator for the class itself
        cls_decorator_line = (
            node.decorator_list[0].lineno
            if node.decorator_list
            else node.lineno
        )
        # Check if @compass_public already on this class
        if not _already_decorated(node):
            indent = _leading_spaces(lines, node.lineno)
            insertions.append((cls_decorator_line, node.col_offset, f"{indent}@compass_public\n"))

        # Walk immediate method children
        for child in ast.walk(node):
            if child is node:
                continue
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # Only direct children (methods of this class, not nested)
            if not _is_direct_child(node, child):
                continue
            method_name = child.name
            if method_targets is True:
                include = not method_name.startswith("_")
            else:
                include = method_name in method_targets
            if not include:
                continue
            if _already_decorated(child):
                continue
            deco_line = (
                child.decorator_list[0].lineno
                if child.decorator_list
                else child.lineno
            )
            indent = _leading_spaces(lines, child.lineno)
            insertions.append((deco_line, child.col_offset, f"{indent}@compass_public\n"))

    # Deduplicate by lineno
    seen: set[int] = set()
    unique: list[tuple[int, str]] = []
    for lineno, col, text in sorted(insertions, key=lambda t: (t[0], t[1])):
        if lineno not in seen:
            seen.add(lineno)
            unique.append((lineno, text))
    return unique


def _is_direct_child(cls_node: ast.ClassDef, func_node: ast.FunctionDef) -> bool:
    """Return True if func_node is an immediate method of cls_node (not nested)."""
    for child in ast.iter_child_nodes(cls_node):
        if child is func_node:
            return True
    return False


def _already_decorated(node) -> bool:
    """Return True if @compass_public is already applied."""
    for deco in node.decorator_list:
        if isinstance(deco, ast.Name) and deco.id == "compass_public":
            return True
        if isinstance(deco, ast.Attribute) and deco.attr == "compass_public":
            return True
    return False


def _leading_spaces(lines: list[str], lineno_1based: int) -> str:
    line = lines[lineno_1based - 1]
    return line[: len(line) - len(line.lstrip())]


# ---------------------------------------------------------------------------
# Core processor
# ---------------------------------------------------------------------------

def process_file(path: Path, class_targets: dict, dry_run: bool = False) -> dict:
    """Apply @compass_public to *path* according to *class_targets*.

    Returns a dict with 'classes_decorated', 'methods_decorated', 'skipped'.
    """
    enc = _detect_encoding(path)
    source = path.read_text(encoding=enc)
    lines = source.splitlines(keepends=True)

    try:
        insertions = _collect_insertions(source, class_targets)
    except SyntaxError as exc:
        return {"error": str(exc), "classes_decorated": 0, "methods_decorated": 0}

    if not insertions:
        return {"classes_decorated": 0, "methods_decorated": 0, "skipped": True}

    # Count class vs method insertions (heuristic: col_offset == 0 → module-level / class)
    # Actually we track them by indentation depth
    classes = sum(1 for _, t in insertions if not t.startswith("    "))
    methods = len(insertions) - classes

    # Apply insertions in *reverse* order so line numbers remain valid
    for lineno, text in reversed(insertions):
        idx = lineno - 1
        lines = lines[:idx] + [text] + lines[idx:]

    # Inject import
    lines = _insert_import(lines)

    new_source = "".join(lines)

    if not dry_run:
        path.write_text(new_source, encoding=enc)

    return {"classes_decorated": classes, "methods_decorated": methods}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Apply @compass_public decorators")
    parser.add_argument("--src", default="src/compass_core",
                        help="Path to compass_core source directory")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview changes without writing files")
    args = parser.parse_args()

    src = Path(args.src)
    if not src.exists():
        print(f"ERROR: source directory not found: {src}")
        return

    total_classes = 0
    total_methods = 0
    errors = []

    for filename, class_targets in sorted(TARGETS.items()):
        path = src / filename
        if not path.exists():
            print(f"  SKIP  {filename} (file not found)")
            continue
        result = process_file(path, class_targets, dry_run=args.dry_run)
        if "error" in result:
            errors.append((filename, result["error"]))
            print(f"  ERROR {filename}: {result['error']}")
        elif result.get("skipped"):
            print(f"  OK    {filename} (no changes needed)")
        else:
            c = result["classes_decorated"]
            m = result["methods_decorated"]
            total_classes += c
            total_methods += m
            tag = "[DRY RUN] " if args.dry_run else ""
            print(f"  {tag}PATCH {filename}: {c} class(es), {m} method(s) decorated")

    print()
    print(f"Done. {total_classes} class decorators + {total_methods} method decorators applied"
          + (" (dry run – no files written)" if args.dry_run else "."))
    if errors:
        print(f"Errors in {len(errors)} file(s):")
        for f, e in errors:
            print(f"  {f}: {e}")


if __name__ == "__main__":
    main()
