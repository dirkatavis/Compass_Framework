"""
Tests for version compatibility scenarios - the most common real-world failures.
"""
import unittest
from unittest.mock import patch, MagicMock
from compass_core.browser_version_checker import BrowserVersionChecker


class TestVersionCompatibility(unittest.TestCase):
    """Test browser/driver version compatibility scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = BrowserVersionChecker()
    
    def test_chrome_browser_driver_version_mismatch_major(self):
        """Test Chrome browser and driver with major version mismatch."""
        with patch.object(self.checker, '_get_chrome_version') as mock_browser, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Browser is newer major version
            mock_browser.return_value = "143.0.7499.193"
            
            # Driver is older major version
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "ChromeDriver 131.0.6778.85"
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_browser_version()
            driver_version = self.checker.get_driver_version("chromedriver.exe")
            
            self.assertEqual(browser_version, "143.0.7499.193")
            self.assertEqual(driver_version, "131.0.6778.85")
            
            # Verify they don't match (major version compatibility)
            browser_major = browser_version.split('.')[0]
            driver_major = driver_version.split('.')[0]
            self.assertNotEqual(browser_major, driver_major)
    
    def test_chrome_browser_driver_version_mismatch_minor(self):
        """Test Chrome browser and driver with minor version mismatch."""
        with patch.object(self.checker, '_get_chrome_version') as mock_browser, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Same major, different minor versions
            mock_browser.return_value = "131.0.6778.193"
            
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "ChromeDriver 131.0.6778.85"  # Older patch
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_browser_version()
            driver_version = self.checker.get_driver_version("chromedriver.exe")
            
            self.assertEqual(browser_version, "131.0.6778.193")
            self.assertEqual(driver_version, "131.0.6778.85")
            
            # Same major version (compatible) but different patch
            self.assertEqual(browser_version.split('.')[0], driver_version.split('.')[0])
            self.assertNotEqual(browser_version, driver_version)
    
    def test_edge_browser_driver_version_mismatch(self):
        """Test Edge browser and driver with version mismatch."""
        with patch.object(self.checker, '_get_edge_version') as mock_browser, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Edge browser version
            mock_browser.return_value = "143.0.3650.139"
            
            # Edge driver is much older
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Microsoft Edge WebDriver 130.0.2849.68"
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_edge_version()
            driver_version = self.checker.get_driver_version("msedgedriver.exe")
            
            self.assertEqual(browser_version, "143.0.3650.139")
            self.assertEqual(driver_version, "130.0.2849.68")
            
            # Major versions don't match
            browser_major = browser_version.split('.')[0]
            driver_major = driver_version.split('.')[0]
            self.assertNotEqual(browser_major, driver_major)
    
    def test_browser_detected_driver_unknown(self):
        """Test browser detected but driver version unknown."""
        with patch.object(self.checker, '_get_chrome_version') as mock_browser, \
             patch('os.path.exists') as mock_exists:
            
            # Browser version available
            mock_browser.return_value = "143.0.7499.193"
            
            # Driver file missing
            mock_exists.return_value = False
            
            browser_version = self.checker.get_browser_version()
            driver_version = self.checker.get_driver_version("chromedriver.exe")
            
            self.assertEqual(browser_version, "143.0.7499.193")
            self.assertEqual(driver_version, "unknown")
            
            # This scenario means automation will fail
            self.assertNotEqual(browser_version, "unknown")
            self.assertEqual(driver_version, "unknown")
    
    def test_driver_detected_browser_unknown(self):
        """Test driver detected but browser version unknown."""
        with patch.object(self.checker, '_get_chrome_version') as mock_browser, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Browser version unknown (not installed?)
            mock_browser.return_value = "unknown"
            
            # Driver available 
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "ChromeDriver 131.0.6778.85"
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_browser_version()
            driver_version = self.checker.get_driver_version("chromedriver.exe")
            
            self.assertEqual(browser_version, "unknown")
            self.assertEqual(driver_version, "131.0.6778.85")
            
            # This scenario also means automation will fail
            self.assertEqual(browser_version, "unknown")
            self.assertNotEqual(driver_version, "unknown")
    
    def test_both_versions_unknown(self):
        """Test both browser and driver versions unknown."""
        with patch.object(self.checker, '_get_chrome_version') as mock_browser, \
             patch('os.path.exists') as mock_exists:
            
            # Both unknown
            mock_browser.return_value = "unknown"
            mock_exists.return_value = False
            
            browser_version = self.checker.get_browser_version()
            driver_version = self.checker.get_driver_version("chromedriver.exe")
            
            self.assertEqual(browser_version, "unknown")
            self.assertEqual(driver_version, "unknown")
    
    def test_perfect_version_match(self):
        """Test when browser and driver versions match perfectly."""
        with patch.object(self.checker, '_get_chrome_version') as mock_browser, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Perfect match scenario
            version = "131.0.6778.85"
            mock_browser.return_value = version
            
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = f"ChromeDriver {version}"
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_browser_version()
            driver_version = self.checker.get_driver_version("chromedriver.exe")
            
            self.assertEqual(browser_version, version)
            self.assertEqual(driver_version, version)
            self.assertEqual(browser_version, driver_version)
    
    def test_realistic_auto_update_scenario(self):
        """Test realistic scenario where browser auto-updated but driver didn't."""
        with patch.object(self.checker, '_get_chrome_version') as mock_browser, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Chrome auto-updated to latest
            mock_browser.return_value = "143.0.7499.193"
            
            # ChromeDriver still at older version
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "ChromeDriver 131.0.6778.85"
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_browser_version()
            driver_version = self.checker.get_driver_version("chromedriver.exe")
            
            # This is the classic Selenium failure scenario
            browser_major = int(browser_version.split('.')[0])
            driver_major = int(driver_version.split('.')[0])
            version_gap = browser_major - driver_major
            
            self.assertEqual(browser_version, "143.0.7499.193")
            self.assertEqual(driver_version, "131.0.6778.85")
            self.assertGreaterEqual(version_gap, 5)  # Significant version gap
            
            # This would cause SessionNotCreatedException in Selenium


if __name__ == '__main__':
    unittest.main()