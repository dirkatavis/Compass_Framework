"""
Compass Framework – API Inventory Exporter  (installable version)
==================================================================
Walks the compass_core source tree, parses every Python file with the AST, and
emits a CSV that classifies every class-level method by:

  File          – source filename
  Module        – dotted module name (compass_core.*)
  Layer         – Protocol | Implementation | Flow | Utility | Entry Point
  Class         – class name
    Is Protocol   – YES if the class itself inherits from Protocol
    In __all__    – YES if exported from compass_core/__init__.py
    Class Access  – Public | Private (Internal) by naming convention
    Class Public  – YES if class has @compass_public
  Method        – method name
    Method Access – Public | Private (Internal) by naming convention
    Method Public – YES if method has @compass_public
    Certified Public – YES only when public-by-name and @compass_public are both true
    Review Needed – YES when visibility/decorator intent mismatch is found
    Suggested Review Action – Suggested action to resolve mismatch
  Signature     – parameter list (self excluded)
  Summary       – first line of the method docstring (if present)

CLI Usage (after pip install compass-core)
------------------------------------------
  compass-inventory                       # auto-detects installed package
  compass-inventory --out my_report.csv   # custom output path
  compass-inventory --src path/to/src     # explicit source root
  compass-inventory --fail-on-drift       # exit non-zero on decorator drift

Developer Usage (from framework repo root)
------------------------------------------
  python tools/export_inventory.py        # same interface, same output
"""
import ast
import csv
import importlib.util
import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional, Set


# ---------------------------------------------------------------------------
# Layer classification
# ---------------------------------------------------------------------------

# Files whose primary purpose is defining Protocol contracts
_PROTOCOL_FILES: Set[str] = {
    "configuration.py",
    "navigation.py",
    "driver_manager.py",
    "workflow.py",
    "login_flow.py",
    "vehicle_data_actions.py",
    "pm_actions.py",
    "logging.py",
    "version_checker.py",
}

# Files that are pure utility / data-model modules (no Protocol, no selenium)
_UTILITY_FILES: Set[str] = {
    "csv_utils.py",
    "mva_collection.py",
    "page_detectors.py",
    "driver_factory.py",
    "browser_version_checker.py",
}


def _layer_for_file(filename: str) -> str:
    """Return the architectural layer label for a given source filename."""
    if filename == "engine.py":
        return "Entry Point"
    if filename in _PROTOCOL_FILES:
        return "Protocol"
    if filename.endswith("_flow.py"):
        return "Flow"
    if filename in _UTILITY_FILES:
        return "Utility"
    return "Implementation"


# ---------------------------------------------------------------------------
# AST helpers
# ---------------------------------------------------------------------------

def _class_is_protocol(node: ast.ClassDef) -> bool:
    """Return True if the class directly inherits from Protocol."""
    for base in node.bases:
        name = ""
        if isinstance(base, ast.Name):
            name = base.id
        elif isinstance(base, ast.Attribute):
            name = base.attr
        if name == "Protocol":
            return True
    return False


def _first_docstring(node: ast.AST) -> Optional[str]:
    """Extract the first line of a docstring from a function/class node."""
    if (
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        first_line = node.body[0].value.value.strip().splitlines()[0].strip()
        return first_line
    return ""


def _has_compass_public_decorator(node: ast.AST) -> bool:
    """Return True when a class/function has @compass_public decorator."""
    decorators = getattr(node, "decorator_list", [])
    for decorator in decorators:
        if isinstance(decorator, ast.Name) and decorator.id == "compass_public":
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == "compass_public":
            return True
        if isinstance(decorator, ast.Call):
            func = decorator.func
            if isinstance(func, ast.Name) and func.id == "compass_public":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "compass_public":
                return True
    return False


def _review_recommendation(
    class_access: str,
    class_public: str,
    method_access: str,
    method_public: str,
) -> Tuple[str, str, str]:
    """Return (certified_public, review_needed, recommendation)."""
    class_is_public = class_access == "Public"
    method_is_public = method_access == "Public"
    class_marked = class_public == "YES"
    method_marked = method_public == "YES"

    certified_public = (
        "YES" if class_is_public and class_marked and method_is_public and method_marked else ""
    )

    if class_is_public:
        if method_is_public and not method_marked:
            return certified_public, "YES", "Add @compass_public to method or rename with leading underscore"
        if not method_is_public and method_marked:
            return certified_public, "YES", "Remove @compass_public or rename without leading underscore"

    return certified_public, "", ""


def _class_review_status(class_access: str, class_public: str) -> Tuple[str, str]:
    """Return (class_review_needed, class_suggested_action)."""
    class_is_public = class_access == "Public"
    class_marked = class_public == "YES"

    if class_is_public and not class_marked:
        return "YES", "Add @compass_public to class or rename with leading underscore"
    if not class_is_public and class_marked:
        return "YES", "Remove @compass_public or rename without leading underscore"
    return "", ""


def _signature(func: ast.FunctionDef) -> str:
    """Return a readable parameter string, excluding 'self' / 'cls'."""
    func_args = func.args
    params: List[str] = []

    all_args = func_args.posonlyargs + func_args.args
    defaults_offset = len(all_args) - len(func_args.defaults)

    for idx, arg in enumerate(all_args):
        if arg.arg in ("self", "cls"):
            continue
        param = arg.arg
        if arg.annotation:
            try:
                param += f": {ast.unparse(arg.annotation)}"
            except Exception:
                pass
        default_idx = idx - defaults_offset
        if 0 <= default_idx < len(func_args.defaults):
            try:
                param += f" = {ast.unparse(func_args.defaults[default_idx])}"
            except Exception:
                pass
        params.append(param)

    if func_args.vararg:
        params.append(f"*{func_args.vararg.arg}")
    if func_args.kwarg:
        params.append(f"**{func_args.kwarg.arg}")

    return ", ".join(params)


# ---------------------------------------------------------------------------
# __all__ extraction from __init__.py
# ---------------------------------------------------------------------------

def _extract_all_exports(init_path: Path) -> Set[str]:
    """Parse __init__.py and collect every name appended to __all__."""
    exports: Set[str] = set()
    if not init_path.exists():
        return exports

    try:
        tree = ast.parse(init_path.read_text(encoding="utf-8-sig"))
    except SyntaxError:
        return exports

    for node in ast.walk(tree):
        # __all__ = [...]
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "__all__"
                for t in node.targets
            )
            and isinstance(node.value, ast.List)
        ):
            for elt in node.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    exports.add(elt.value)

        # __all__.append('Foo')
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "append"
            and isinstance(node.value.func.value, ast.Name)
            and node.value.func.value.id == "__all__"
        ):
            for arg in node.value.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    exports.add(arg.value)

        # __all__.extend([...])
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if (
                isinstance(call.func, ast.Attribute)
                and call.func.attr == "extend"
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "__all__"
                and call.args
                and isinstance(call.args[0], ast.List)
            ):
                for elt in call.args[0].elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        exports.add(elt.value)

        # __all__ += [...]
        if (
            isinstance(node, ast.AugAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__all__"
            and isinstance(node.value, ast.List)
        ):
            for elt in node.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    exports.add(elt.value)

    return exports


# ---------------------------------------------------------------------------
# Core walker
# ---------------------------------------------------------------------------

def _walk_source(src_root: Path, all_exports: Set[str]) -> List[Tuple]:
    rows: List[Tuple] = []

    for py_file in sorted(src_root.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue

        relative = py_file.relative_to(src_root.parent)
        module = str(relative.with_suffix("")).replace(os.sep, ".")
        filename = py_file.name
        layer = _layer_for_file(filename)

        try:
            source = py_file.read_text(encoding="utf-8-sig")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError) as exc:
            print(f"  [WARN] Could not parse {py_file}: {exc}", file=sys.stderr)
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            class_name = node.name
            is_protocol = "YES" if _class_is_protocol(node) else ""
            in_all = "YES" if class_name in all_exports else ""
            class_access = "Private (Internal)" if class_name.startswith("_") else "Public"
            class_public = "YES" if _has_compass_public_decorator(node) else ""
            class_review_needed, class_suggested_action = _class_review_status(class_access, class_public)

            method_nodes = [
                item for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]

            if not method_nodes:
                rows.append((
                    filename, module, layer, class_name, is_protocol, in_all,
                    class_access, class_public, class_review_needed, class_suggested_action,
                    "", "", "", "", "", "", "", _first_docstring(node),
                ))
                continue

            for item in method_nodes:
                method_name = item.name
                method_access = "Private (Internal)" if method_name.startswith("_") else "Public"
                method_public = "YES" if _has_compass_public_decorator(item) else ""
                certified_public, review_needed, recommendation = _review_recommendation(
                    class_access, class_public, method_access, method_public,
                )
                row_class_review_needed = class_review_needed if method_access == "Public" else ""
                row_class_suggested_action = class_suggested_action if method_access == "Public" else ""
                sig = _signature(item)
                summary = _first_docstring(item)

                rows.append((
                    filename, module, layer, class_name, is_protocol, in_all,
                    class_access, class_public, row_class_review_needed, row_class_suggested_action,
                    method_name, method_access, method_public, certified_public,
                    review_needed, recommendation, sig, summary,
                ))

    return rows


def _method_drift_rows(rows: List[Tuple]) -> List[Tuple]:
    """Return rows where a method is public-by-name but not @compass_public."""
    drift_rows: List[Tuple] = []
    for row in rows:
        class_access = row[6]
        method_name = row[10]
        method_access = row[11]
        method_public = row[12]

        if (
            class_access == "Public"
            and method_name
            and method_access == "Public"
            and method_public != "YES"
        ):
            drift_rows.append(row)

    return drift_rows


# ---------------------------------------------------------------------------
# Core export function
# ---------------------------------------------------------------------------

def export_inventory(
    src_dir: str,
    output_file: str = "framework_inventory.csv",
    fail_on_drift: bool = False,
) -> int:
    """Walk the compass_core source tree and emit a classified CSV inventory.

    Args:
        src_dir: Path to the directory that contains the ``compass_core`` package
            folder.  Pass ``"auto"`` to locate the installed package automatically.
        output_file: Destination CSV path.
        fail_on_drift: When *True* exit with code 2 if any public-by-name method
            lacks the ``@compass_public`` decorator.

    Returns:
        0 on success, 1 on missing source, 2 on drift when *fail_on_drift* is set.
    """
    if src_dir == "auto":
        spec = importlib.util.find_spec("compass_core")
        if spec is None or spec.origin is None:
            print("[ERROR] compass_core is not installed; cannot auto-detect source.", file=sys.stderr)
            return 1
        # origin = .../site-packages/compass_core/__init__.py  →  parent.parent = site-packages/
        src_dir = str(Path(spec.origin).parent.parent)

    src_root = Path(src_dir).resolve()
    if not src_root.exists():
        print(f"[ERROR] Source directory not found: {src_root}", file=sys.stderr)
        return 1

    init_path = src_root / "compass_core" / "__init__.py"
    all_exports = _extract_all_exports(init_path)

    compass_src = src_root / "compass_core"
    rows = _walk_source(compass_src, all_exports)

    headers = [
        "File",
        "Module",
        "Layer",
        "Class",
        "Is Protocol",
        "In __all__",
        "Class Access",
        "Class Public",
        "Class Review Needed",
        "Class Suggested Review Action",
        "Method",
        "Method Access",
        "Method Public",
        "Certified Public",
        "Review Needed",
        "Suggested Review Action",
        "Signature",
        "Summary",
    ]

    output_path = Path(output_file).resolve()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Inventory exported: {output_path}")
    print(f"  {len(rows)} methods across {len({r[3] for r in rows})} classes")
    print(f"  {len([r for r in rows if r[4] == 'YES'])} protocol methods")
    print(f"  {len([r for r in rows if r[5] == 'YES'])} exported via __all__")
    print(f"  {len([r for r in rows if r[11] == 'Public'])} public / "
          f"{len([r for r in rows if r[11] != 'Public'])} private methods")
    print(f"  {len([r for r in rows if r[13] == 'YES'])} certified public methods")
    print(f"  {len([r for r in rows if r[8] == 'YES'])} class rows flagged for review")
    print(f"  {len([r for r in rows if r[14] == 'YES'])} method rows flagged for review")

    if fail_on_drift:
        drift_rows = _method_drift_rows(rows)
        if drift_rows:
            print("[DRIFT] Public-by-name methods missing @compass_public:", file=sys.stderr)
            for row in drift_rows:
                print(f"  - {row[0]}::{row[3]}.{row[10]}", file=sys.stderr)
            print(
                f"[DRIFT] Found {len(drift_rows)} drift method(s). "
                "Use @compass_public or rename with leading underscore.",
                file=sys.stderr,
            )
            return 2

        print("[DRIFT] OK: no public-by-name methods are missing @compass_public")

    return 0


# ---------------------------------------------------------------------------
# CLI entry point  (registered via pyproject.toml [project.scripts])
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point for the ``compass-inventory`` command."""
    parser = argparse.ArgumentParser(
        prog="compass-inventory",
        description="Export Compass Framework API inventory to CSV.",
    )
    parser.add_argument(
        "--src",
        default="auto",
        help=(
            "Path to the directory containing the compass_core package folder "
            "(default: auto-detect from installed package location)."
        ),
    )
    parser.add_argument(
        "--out",
        default="framework_inventory.csv",
        help="Output CSV file path (default: framework_inventory.csv).",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Exit non-zero if any public-by-name method lacks @compass_public.",
    )
    args = parser.parse_args()
    sys.exit(export_inventory(args.src, args.out, args.fail_on_drift))


if __name__ == "__main__":
    main()
