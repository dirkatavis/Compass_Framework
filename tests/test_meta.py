"""
Meta-tests: Tests that validate our test suite itself
These catch issues in the test infrastructure
"""
import unittest
import importlib
import os
import sys
from pathlib import Path


class TestTestSuite(unittest.TestCase):
    """Meta-tests for validating test suite integrity"""
    
    def test_all_test_modules_can_be_imported(self):
        """Test that all test modules can be imported without errors"""
        tests_dir = Path(__file__).parent
        test_files = list(tests_dir.glob("test_*.py"))
        
        self.assertGreater(len(test_files), 0, "No test files found")
        
        for test_file in test_files:
            if test_file.name == Path(__file__).name:  # Skip self
                continue
                
            module_name = f"tests.{test_file.stem}"
            with self.subTest(module=module_name):
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_all_source_modules_can_be_imported(self):
        """Test that all source modules can be imported"""
        src_dir = Path(__file__).parent.parent / "src" / "compass_core"
        py_files = [f for f in src_dir.glob("*.py") if f.name != "__init__.py"]
        
        for py_file in py_files:
            module_name = f"compass_core.{py_file.stem}"
            with self.subTest(module=module_name):
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    self.fail(f"Failed to import {module_name}: {e}")
    
    def test_test_discovery_works(self):
        """Test that unittest discovery can find and load tests"""
        loader = unittest.TestLoader()
        tests_dir = str(Path(__file__).parent)
        
        try:
            suite = loader.discover(tests_dir, pattern="test_*.py")
            test_count = suite.countTestCases()
            self.assertGreater(test_count, 0, "No tests discovered")
        except Exception as e:
            self.fail(f"Test discovery failed: {e}")


if __name__ == '__main__':
    unittest.main()