"""
Test __all__ declaration and public API control.
"""
import unittest
import compass_core


class TestPublicAPI(unittest.TestCase):
    """Test that public API is properly controlled via __all__."""
    
    def test_all_declaration_exists(self):
        """Test that __all__ is properly declared."""
        self.assertTrue(hasattr(compass_core, '__all__'))
        self.assertIsInstance(compass_core.__all__, list)
        
    def test_compass_runner_in_all(self):
        """Test that CompassRunner is always in __all__."""
        self.assertIn('CompassRunner', compass_core.__all__)
    
    def test_json_configuration_in_all(self):
        """Test that JsonConfiguration is always in __all__."""
        self.assertIn('JsonConfiguration', compass_core.__all__)
    
    def test_browser_version_checker_conditional_in_all(self):
        """Test BrowserVersionChecker in __all__ when on Windows."""
        try:
            # Try to access BrowserVersionChecker through module
            getattr(compass_core, 'BrowserVersionChecker')
            # If access works, should be in __all__
            self.assertIn('BrowserVersionChecker', compass_core.__all__)
        except AttributeError:
            # If attribute doesn't exist, should not be in __all__
            self.assertNotIn('BrowserVersionChecker', compass_core.__all__)
        
    def test_selenium_navigator_conditional_in_all(self):
        """Test SeleniumNavigator in __all__ when selenium available."""
        try:
            from compass_core import SeleniumNavigator
            # If import works, should be in __all__
            self.assertIn('SeleniumNavigator', compass_core.__all__)
        except ImportError:
            # If import fails, should not be in __all__
            self.assertNotIn('SeleniumNavigator', compass_core.__all__)
            
    def test_star_import_respects_all(self):
        """Test that star import only gets items from __all__."""
        # This is more of a documentation test since we can't easily
        # test star import isolation in unit tests
        expected_public_api = compass_core.__all__
        
        # All items in __all__ should be accessible
        for item in expected_public_api:
            self.assertTrue(hasattr(compass_core, item))
            
    def test_private_modules_not_in_all(self):
        """Test that internal modules are not exposed in __all__."""
        private_items = ['engine', 'navigation', 'selenium_navigator', 'configuration', 'json_configuration', 'version_checker', 'browser_version_checker']
        
        for item in private_items:
            self.assertNotIn(item, compass_core.__all__)


if __name__ == '__main__':
    unittest.main()