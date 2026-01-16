"""
Test optional dependency handling in __init__.py
"""
import unittest


class TestOptionalDependencies(unittest.TestCase):
    """Test that optional dependencies don't break core imports."""
    
    def test_core_import_always_works(self):
        """Test that CompassRunner can always be imported."""
        from compass_core import CompassRunner
        self.assertIsNotNone(CompassRunner)
    
    def test_selenium_navigator_available_when_selenium_installed(self):
        """Test that SeleniumNavigator is available when selenium is installed."""
        try:
            from compass_core import SeleniumNavigator
            # If selenium is installed, this should work
            self.assertIsNotNone(SeleniumNavigator)
        except ImportError:
            # If selenium not installed, this is expected
            self.skipTest("Selenium not installed - cannot test SeleniumNavigator availability")
    
    def test_direct_selenium_navigator_import_works(self):
        """Test that direct import of SeleniumNavigator works when selenium available."""
        try:
            from compass_core.selenium_navigator import SeleniumNavigator
            self.assertIsNotNone(SeleniumNavigator)
        except ImportError:
            self.skipTest("Selenium not installed - cannot test direct SeleniumNavigator import")


if __name__ == '__main__':
    unittest.main()