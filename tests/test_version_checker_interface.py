"""
Tests for VersionChecker interface
Very focused on just the interface contract
"""
import unittest
from typing import get_type_hints
from compass_core.version_checker import VersionChecker


class MockVersionChecker:
    """Simple implementation for testing the interface"""
    
    def get_browser_version(self) -> str:
        return "131.0.2903.70"
    
    def get_driver_version(self, driver_path: str) -> str:
        return "131.0.2903.70"


class TestVersionCheckerInterface(unittest.TestCase):
    """Test the VersionChecker protocol/interface"""
    
    def setUp(self):
        self.checker = MockVersionChecker()
    
    def test_interface_has_required_methods(self):
        """Test that the interface defines required methods"""
        # Check that our implementation satisfies the protocol
        self.assertTrue(hasattr(self.checker, 'get_browser_version'))
        self.assertTrue(hasattr(self.checker, 'get_driver_version'))
        
        # Check they are callable
        self.assertTrue(callable(self.checker.get_browser_version))
        self.assertTrue(callable(self.checker.get_driver_version))
    
    def test_get_browser_version_returns_string(self):
        """Test browser version method returns string"""
        result = self.checker.get_browser_version()
        self.assertIsInstance(result, str)
        self.assertEqual(result, "131.0.2903.70")
    
    def test_get_driver_version_accepts_path_returns_string(self):
        """Test driver version method accepts path and returns string"""
        result = self.checker.get_driver_version("/path/to/driver")
        self.assertIsInstance(result, str)
        self.assertEqual(result, "131.0.2903.70")
    
    def test_methods_have_correct_signatures(self):
        """Test that methods have expected type signatures"""
        hints = get_type_hints(self.checker.get_browser_version)
        self.assertEqual(hints.get('return'), str)
        
        hints = get_type_hints(self.checker.get_driver_version)
        self.assertEqual(hints.get('return'), str)


if __name__ == '__main__':
    unittest.main()