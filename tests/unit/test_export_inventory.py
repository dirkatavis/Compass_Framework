"""
Unit tests for tools/export_inventory.py helper functions.
"""
import ast
import sys
import textwrap
import unittest
from pathlib import Path

# Make the tools package importable from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import export_inventory as inv


# ---------------------------------------------------------------------------
# _layer_for_file
# ---------------------------------------------------------------------------

class TestLayerForFile(unittest.TestCase):

    def test_engine_is_entry_point(self):
        self.assertEqual(inv._layer_for_file("engine.py"), "Entry Point")

    def test_protocol_files(self):
        for f in ["configuration.py", "navigation.py", "login_flow.py"]:
            with self.subTest(f=f):
                self.assertEqual(inv._layer_for_file(f), "Protocol")

    def test_flow_files(self):
        for f in ["vehicle_lookup_flow.py", "pm_work_item_flow.py", "vin_to_mva_flow.py"]:
            with self.subTest(f=f):
                self.assertEqual(inv._layer_for_file(f), "Flow")

    def test_utility_files(self):
        for f in ["csv_utils.py", "mva_collection.py", "driver_factory.py"]:
            with self.subTest(f=f):
                self.assertEqual(inv._layer_for_file(f), "Utility")

    def test_implementation_fallback(self):
        self.assertEqual(inv._layer_for_file("selenium_navigator.py"), "Implementation")

    def test_engine_not_utility(self):
        # Regression: engine.py must never be classified as Utility
        self.assertNotEqual(inv._layer_for_file("engine.py"), "Utility")


# ---------------------------------------------------------------------------
# _class_is_protocol
# ---------------------------------------------------------------------------

class TestClassIsProtocol(unittest.TestCase):

    def _parse_class(self, src: str) -> ast.ClassDef:
        tree = ast.parse(textwrap.dedent(src))
        return next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef))

    def test_direct_protocol_base(self):
        node = self._parse_class("class Foo(Protocol): pass")
        self.assertTrue(inv._class_is_protocol(node))

    def test_attribute_protocol_base(self):
        node = self._parse_class("class Foo(typing.Protocol): pass")
        self.assertTrue(inv._class_is_protocol(node))

    def test_no_protocol_base(self):
        node = self._parse_class("class Foo(SomethingElse): pass")
        self.assertFalse(inv._class_is_protocol(node))

    def test_no_bases(self):
        node = self._parse_class("class Foo: pass")
        self.assertFalse(inv._class_is_protocol(node))


# ---------------------------------------------------------------------------
# _has_compass_public_decorator
# ---------------------------------------------------------------------------

class TestHasCompassPublicDecorator(unittest.TestCase):

    def _parse_func(self, src: str) -> ast.FunctionDef:
        tree = ast.parse(textwrap.dedent(src))
        return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))

    def test_bare_decorator(self):
        node = self._parse_func("@compass_public\ndef foo(): pass")
        self.assertTrue(inv._has_compass_public_decorator(node))

    def test_attribute_decorator(self):
        node = self._parse_func("@module.compass_public\ndef foo(): pass")
        self.assertTrue(inv._has_compass_public_decorator(node))

    def test_called_decorator(self):
        node = self._parse_func("@compass_public()\ndef foo(): pass")
        self.assertTrue(inv._has_compass_public_decorator(node))

    def test_no_decorator(self):
        node = self._parse_func("def foo(): pass")
        self.assertFalse(inv._has_compass_public_decorator(node))

    def test_unrelated_decorator(self):
        node = self._parse_func("@staticmethod\ndef foo(): pass")
        self.assertFalse(inv._has_compass_public_decorator(node))


# ---------------------------------------------------------------------------
# _review_recommendation
# ---------------------------------------------------------------------------

class TestReviewRecommendation(unittest.TestCase):

    def test_public_class_public_method_no_decorator_flagged(self):
        _, review, action = inv._review_recommendation("Public", "", "Public", "")
        self.assertEqual(review, "YES")
        self.assertIn("@compass_public", action)

    def test_public_class_private_method_not_flagged(self):
        _, review, _ = inv._review_recommendation("Public", "", "Private (Internal)", "")
        self.assertEqual(review, "")

    def test_private_class_public_method_not_flagged(self):
        # Methods in private classes are assumed intentionally internal
        _, review, _ = inv._review_recommendation("Private (Internal)", "", "Public", "")
        self.assertEqual(review, "")

    def test_public_class_public_method_with_decorator_certified(self):
        certified, review, _ = inv._review_recommendation("Public", "YES", "Public", "YES")
        self.assertEqual(certified, "YES")
        self.assertEqual(review, "")

    def test_public_class_private_method_with_decorator_mismatch(self):
        _, review, action = inv._review_recommendation("Public", "YES", "Private (Internal)", "YES")
        self.assertEqual(review, "YES")
        self.assertIn("Remove @compass_public", action)


# ---------------------------------------------------------------------------
# _class_review_status
# ---------------------------------------------------------------------------

class TestClassReviewStatus(unittest.TestCase):

    def test_public_class_no_decorator_flagged(self):
        review, action = inv._class_review_status("Public", "")
        self.assertEqual(review, "YES")
        self.assertIn("@compass_public", action)

    def test_public_class_with_decorator_clean(self):
        review, _ = inv._class_review_status("Public", "YES")
        self.assertEqual(review, "")

    def test_private_class_no_decorator_clean(self):
        review, _ = inv._class_review_status("Private (Internal)", "")
        self.assertEqual(review, "")

    def test_private_class_with_decorator_flagged(self):
        # Opposite mismatch: private name but decorated
        review, action = inv._class_review_status("Private (Internal)", "YES")
        self.assertEqual(review, "YES")
        self.assertIn("Remove @compass_public", action)


# ---------------------------------------------------------------------------
# _extract_all_exports
# ---------------------------------------------------------------------------

class TestExtractAllExports(unittest.TestCase):

    def _write_init(self, tmp_path: Path, src: str) -> Path:
        init = tmp_path / "__init__.py"
        init.write_text(textwrap.dedent(src), encoding="utf-8")
        return init

    def test_list_assignment(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            init = self._write_init(Path(d), """
                __all__ = ['Foo', 'Bar']
            """)
            exports = inv._extract_all_exports(init)
        self.assertIn("Foo", exports)
        self.assertIn("Bar", exports)

    def test_append(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            init = self._write_init(Path(d), """
                __all__ = ['Foo']
                __all__.append('Baz')
            """)
            exports = inv._extract_all_exports(init)
        self.assertIn("Baz", exports)

    def test_extend(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            init = self._write_init(Path(d), """
                __all__ = ['Foo']
                __all__.extend(['Bar', 'Qux'])
            """)
            exports = inv._extract_all_exports(init)
        self.assertIn("Bar", exports)
        self.assertIn("Qux", exports)

    def test_augmented_assign(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            init = self._write_init(Path(d), """
                __all__ = ['Foo']
                __all__ += ['Extra']
            """)
            exports = inv._extract_all_exports(init)
        self.assertIn("Extra", exports)

    def test_missing_file_returns_empty(self):
        exports = inv._extract_all_exports(Path("/nonexistent/__init__.py"))
        self.assertEqual(exports, set())


# ---------------------------------------------------------------------------
# _walk_source – class-only rows for no-method classes
# ---------------------------------------------------------------------------

class TestWalkSourceClassOnlyRows(unittest.TestCase):

    def test_enum_class_emits_row(self):
        """A class with no methods (e.g. Enum) should still produce a row."""
        import tempfile, os
        src = textwrap.dedent("""\
            from enum import Enum
            class MyStatus(Enum):
                PENDING = "pending"
                DONE = "done"
        """)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / "compass_core"
            root.mkdir()
            (root / "my_status.py").write_text(src, encoding="utf-8")
            rows = inv._walk_source(root, set())

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row[3], "MyStatus")   # Class
        self.assertEqual(row[10], "")          # Method – blank for class-only row


if __name__ == "__main__":
    unittest.main()
