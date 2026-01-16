"""
Tests for BrowserVersionChecker compatibility checking method.
"""
import unittest
from unittest.mock import patch, MagicMock
from compass_core.browser_version_checker import BrowserVersionChecker


class TestCompatibilityChecking(unittest.TestCase):
    """Test browser/driver version compatibility checking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = BrowserVersionChecker()
    
    def test_perfect_chrome_compatibility(self):
        """Test perfect Chrome browser/driver version match."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            version = "131.0.6778.85"
            mock_browser.return_value = version
            mock_driver.return_value = version
            
            result = self.checker.check_compatibility("chrome", "chromedriver.exe")
            
            self.assertEqual(result["browser_version"], version)
            self.assertEqual(result["driver_version"], version)
            self.assertTrue(result["compatible"])
            self.assertTrue(result["major_match"])
            self.assertTrue(result["exact_match"])
            self.assertIn("Perfect version match", result["recommendation"])
    
    def test_chrome_major_version_match(self):
        """Test Chrome with matching major version but different minor."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "131.0.6778.193"
            mock_driver.return_value = "131.0.6778.85"
            
            result = self.checker.check_compatibility("chrome")
            
            self.assertEqual(result["browser_version"], "131.0.6778.193")
            self.assertEqual(result["driver_version"], "131.0.6778.85")
            self.assertTrue(result["compatible"])
            self.assertTrue(result["major_match"])
            self.assertFalse(result["exact_match"])
            self.assertIn("Major versions match", result["recommendation"])
    
    def test_chrome_major_version_mismatch_driver_old(self):
        """Test Chrome with driver too old (major version mismatch)."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "143.0.7499.193"
            mock_driver.return_value = "131.0.6778.85"
            
            result = self.checker.check_compatibility("chrome", "chromedriver.exe")
            
            self.assertFalse(result["compatible"])
            self.assertFalse(result["major_match"])
            self.assertFalse(result["exact_match"])
            self.assertIn("Driver too old", result["recommendation"])
            self.assertIn("gap: 12 versions", result["recommendation"])
            self.assertIn("Update WebDriver to v143", result["recommendation"])
    
    def test_chrome_major_version_mismatch_driver_new(self):
        """Test Chrome with driver too new (major version mismatch)."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "130.0.6723.58"
            mock_driver.return_value = "143.0.7499.185"
            
            result = self.checker.check_compatibility("chrome", "chromedriver.exe")
            
            self.assertFalse(result["compatible"])
            self.assertFalse(result["major_match"])
            self.assertFalse(result["exact_match"])
            self.assertIn("Driver too new", result["recommendation"])
            self.assertIn("gap: 13 versions", result["recommendation"])
    
    def test_edge_compatibility_check(self):
        """Test Edge browser/driver compatibility checking."""
        with patch.object(self.checker, 'get_edge_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "131.0.2903.70"
            mock_driver.return_value = "131.0.2903.70"
            
            result = self.checker.check_compatibility("edge", "msedgedriver.exe")
            
            self.assertEqual(result["browser_version"], "131.0.2903.70")
            self.assertEqual(result["driver_version"], "131.0.2903.70")
            self.assertTrue(result["compatible"])
            self.assertTrue(result["exact_match"])
    
    def test_browser_not_found(self):
        """Test when browser is not found."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "unknown"
            mock_driver.return_value = "131.0.6778.85"
            
            result = self.checker.check_compatibility("chrome")
            
            self.assertFalse(result["compatible"])
            self.assertIn("Chrome browser not found", result["recommendation"])
    
    def test_driver_not_found(self):
        """Test when driver is not found."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "143.0.7499.193"
            mock_driver.return_value = "unknown"
            
            result = self.checker.check_compatibility("chrome", "chromedriver.exe")
            
            self.assertFalse(result["compatible"])
            self.assertIn("Driver not found at chromedriver.exe", result["recommendation"])
    
    def test_both_not_found(self):
        """Test when both browser and driver not found."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "unknown"
            mock_driver.return_value = "unknown"
            
            result = self.checker.check_compatibility("chrome")
            
            self.assertFalse(result["compatible"])
            self.assertIn("Both chrome browser and driver not found", result["recommendation"])
    
    def test_default_driver_path_chrome(self):
        """Test default driver path for Chrome."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "131.0.6778.85"
            mock_driver.return_value = "131.0.6778.85"
            
            result = self.checker.check_compatibility("chrome")  # No driver_path specified
            
            # Should call get_driver_version with default "chromedriver.exe"
            mock_driver.assert_called_with("chromedriver.exe")
    
    def test_default_driver_path_edge(self):
        """Test default driver path for Edge."""
        with patch.object(self.checker, 'get_edge_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "131.0.2903.70"
            mock_driver.return_value = "131.0.2903.70"
            
            result = self.checker.check_compatibility("edge")  # No driver_path specified
            
            # Should call get_driver_version with default "msedgedriver.exe"
            mock_driver.assert_called_with("msedgedriver.exe")
    
    def test_invalid_version_format(self):
        """Test handling of invalid version formats."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_browser.return_value = "invalid.version"
            mock_driver.return_value = "also.invalid"
            
            result = self.checker.check_compatibility("chrome")
            
            self.assertFalse(result["compatible"])
            self.assertIn("Invalid version format", result["recommendation"])
    
    def test_realistic_auto_update_scenario_compatibility(self):
        """Test realistic auto-update scenario using compatibility checker."""
        with patch.object(self.checker, 'get_browser_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            # Browser auto-updated to version 143, driver still at 131
            mock_browser.return_value = "143.0.7499.193"
            mock_driver.return_value = "131.0.6778.85"
            
            result = self.checker.check_compatibility("chrome", "chromedriver.exe")
            
            self.assertFalse(result["compatible"])
            self.assertFalse(result["major_match"])
            self.assertIn("Driver too old", result["recommendation"])
            self.assertIn("Update WebDriver to v143", result["recommendation"])
            
            # This is exactly the failure case that happens most often in CI/CD


if __name__ == '__main__':
    unittest.main()