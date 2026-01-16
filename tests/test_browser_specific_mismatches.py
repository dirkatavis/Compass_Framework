"""
Browser-specific version mismatch tests for Chrome and Edge.
Tests browser-specific differences in version detection and compatibility.
"""
import unittest
from unittest.mock import patch, MagicMock
from compass_core.browser_version_checker import BrowserVersionChecker


class TestChromeSpecificMismatches(unittest.TestCase):
    """Test Chrome-specific version mismatch scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = BrowserVersionChecker()
    
    def test_chrome_auto_update_realistic_scenario(self):
        """Test realistic Chrome auto-update scenario with specific version gap."""
        with patch.object(self.checker, '_get_chrome_version_from_registry') as mock_registry, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Chrome auto-updated from 130 → 143 (13 version gap)
            mock_registry.return_value = "143.0.7499.193"
            
            # ChromeDriver still at version 130
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "ChromeDriver 130.0.6723.116"
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_browser_version()
            driver_version = self.checker.get_driver_version("chromedriver.exe")
            
            # Verify specific Chrome version format and major version gap
            self.assertEqual(browser_version, "143.0.7499.193")
            self.assertEqual(driver_version, "130.0.6723.116")
            
            browser_major = int(browser_version.split('.')[0])
            driver_major = int(driver_version.split('.')[0])
            self.assertEqual(browser_major - driver_major, 13)
    
    def test_chrome_driver_output_format_parsing(self):
        """Test Chrome-specific driver output format parsing."""
        with patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            # Chrome-specific output format
            mock_result.stdout = "ChromeDriver 131.0.6778.85 (a1b2c3d4-refs/branch-heads/6778@{#85})"
            mock_run.return_value = mock_result
            
            driver_version = self.checker.get_driver_version("chromedriver.exe")
            
            # Should extract just the version number from Chrome-specific format
            self.assertEqual(driver_version, "131.0.6778.85")
    
    def test_chrome_registry_fallback_scenario(self):
        """Test Chrome-specific registry fallback behavior."""
        with patch('compass_core.browser_version_checker.winreg') as mock_winreg, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Chrome registry fails (common in restricted environments)
            mock_winreg.OpenKey.side_effect = FileNotFoundError()
            
            # Chrome executable fallback succeeds
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Google Chrome 143.0.7499.193"
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_browser_version()
            
            # Should get version from executable when registry fails
            self.assertEqual(browser_version, "143.0.7499.193")
    
    def test_chrome_version_number_edge_cases(self):
        """Test Chrome version number edge cases and parsing."""
        test_cases = [
            ("ChromeDriver 143.0.7499.0", "143.0.7499.0"),  # Zero patch
            ("ChromeDriver 200.1.2.3", "200.1.2.3"),      # Future version
            ("ChromeDriver 99.0.4844.51", "99.0.4844.51"), # Past version
        ]
        
        for stdout_text, expected_version in test_cases:
            with self.subTest(stdout=stdout_text):
                with patch('os.path.exists') as mock_exists, \
                     patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
                    
                    mock_exists.return_value = True
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    mock_result.stdout = stdout_text
                    mock_run.return_value = mock_result
                    
                    driver_version = self.checker.get_driver_version("chromedriver.exe")
                    self.assertEqual(driver_version, expected_version)


class TestEdgeSpecificMismatches(unittest.TestCase):
    """Test Edge-specific version mismatch scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = BrowserVersionChecker()
    
    def test_edge_auto_update_realistic_scenario(self):
        """Test realistic Edge auto-update scenario with specific version gap."""
        with patch.object(self.checker, '_get_edge_version_from_registry') as mock_registry, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Edge auto-updated from 127 → 143 (16 version gap)
            mock_registry.return_value = "143.0.3650.139"
            
            # EdgeDriver still at version 127
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Microsoft Edge WebDriver 127.0.2651.105"
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_edge_version()
            driver_version = self.checker.get_driver_version("msedgedriver.exe")
            
            # Verify specific Edge version format and major version gap
            self.assertEqual(browser_version, "143.0.3650.139")
            self.assertEqual(driver_version, "127.0.2651.105")
            
            browser_major = int(browser_version.split('.')[0])
            driver_major = int(driver_version.split('.')[0])
            self.assertEqual(browser_major - driver_major, 16)
    
    def test_edge_driver_output_format_parsing(self):
        """Test Edge-specific driver output format parsing."""
        with patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            # Edge-specific output format (different from Chrome)
            mock_result.stdout = "Microsoft Edge WebDriver 143.0.3650.139 (a1b2c3d4e5f6)"
            mock_run.return_value = mock_result
            
            driver_version = self.checker.get_driver_version("msedgedriver.exe")
            
            # Should extract version from Edge-specific format
            self.assertEqual(driver_version, "143.0.3650.139")
    
    def test_edge_major_version_mismatch_driver_old(self):
        """Test Edge with outdated driver (major version mismatch)."""
        with patch.object(self.checker, 'get_edge_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            # Edge browser newer
            mock_browser.return_value = "143.0.3650.139"
            # Edge driver much older
            mock_driver.return_value = "119.0.2151.97"
            
            result = self.checker.check_compatibility("edge", "msedgedriver.exe")
            
            self.assertFalse(result["compatible"])
            self.assertFalse(result["major_match"])
            self.assertIn("Driver too old", result["recommendation"])
            self.assertIn("gap: 24 versions", result["recommendation"])
    
    def test_edge_major_version_mismatch_driver_new(self):
        """Test Edge with newer driver (less common but possible)."""
        with patch.object(self.checker, 'get_edge_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            # Edge browser older
            mock_browser.return_value = "131.0.2903.70"
            # Edge driver newer
            mock_driver.return_value = "143.0.3650.139"
            
            result = self.checker.check_compatibility("edge", "msedgedriver.exe")
            
            self.assertFalse(result["compatible"])
            self.assertFalse(result["major_match"])
            self.assertIn("Driver too new", result["recommendation"])
            self.assertIn("gap: 12 versions", result["recommendation"])
    
    def test_edge_minor_version_mismatch(self):
        """Test Edge with minor version differences (should be compatible)."""
        with patch.object(self.checker, 'get_edge_version') as mock_browser, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            # Same major version, different minor versions
            mock_browser.return_value = "131.0.3650.200"
            mock_driver.return_value = "131.0.2903.70"
            
            result = self.checker.check_compatibility("edge", "msedgedriver.exe")
            
            self.assertTrue(result["compatible"])
            self.assertTrue(result["major_match"])
            self.assertFalse(result["exact_match"])
            self.assertIn("Major versions match", result["recommendation"])
    
    def test_edge_registry_fallback_scenario(self):
        """Test Edge-specific registry fallback behavior."""
        with patch('compass_core.browser_version_checker.winreg') as mock_winreg, \
             patch('os.path.exists') as mock_exists, \
             patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
            
            # Edge registry fails
            mock_winreg.OpenKey.side_effect = FileNotFoundError()
            
            # Edge executable fallback succeeds
            mock_exists.return_value = True
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "Microsoft Edge 143.0.3650.139"
            mock_run.return_value = mock_result
            
            browser_version = self.checker.get_edge_version()
            
            # Should get version from executable when registry fails
            self.assertEqual(browser_version, "143.0.3650.139")
    
    def test_edge_version_number_edge_cases(self):
        """Test Edge version number edge cases and parsing."""
        test_cases = [
            ("Microsoft Edge WebDriver 143.0.3650.0", "143.0.3650.0"),     # Zero patch
            ("Microsoft Edge WebDriver 200.1.2.3", "200.1.2.3"),         # Future version
            ("Microsoft Edge WebDriver 80.0.361.109", "80.0.361.109"),    # Old EdgeHTML era
        ]
        
        for stdout_text, expected_version in test_cases:
            with self.subTest(stdout=stdout_text):
                with patch('os.path.exists') as mock_exists, \
                     patch('compass_core.browser_version_checker.subprocess.run') as mock_run:
                    
                    mock_exists.return_value = True
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    mock_result.stdout = stdout_text
                    mock_run.return_value = mock_result
                    
                    driver_version = self.checker.get_driver_version("msedgedriver.exe")
                    self.assertEqual(driver_version, expected_version)


class TestCrosseBrowserMismatchComparison(unittest.TestCase):
    """Test cross-browser compatibility comparison scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = BrowserVersionChecker()
    
    def test_chrome_vs_edge_version_detection_independence(self):
        """Test that Chrome and Edge version detection are independent."""
        with patch.object(self.checker, '_get_chrome_version') as mock_chrome, \
             patch.object(self.checker, '_get_edge_version') as mock_edge:
            
            mock_chrome.return_value = "143.0.7499.193"
            mock_edge.return_value = "143.0.3650.139"
            
            chrome_version = self.checker.get_browser_version()  # Delegates to Chrome
            edge_version = self.checker.get_edge_version()
            
            # Different browsers can have different version numbers even at same major
            self.assertNotEqual(chrome_version, edge_version)
            self.assertEqual(chrome_version.split('.')[0], edge_version.split('.')[0])  # Same major
    
    def test_browser_specific_driver_paths(self):
        """Test that each browser uses correct driver executable names."""
        with patch.object(self.checker, 'get_browser_version') as mock_chrome, \
             patch.object(self.checker, 'get_edge_version') as mock_edge, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            mock_chrome.return_value = "143.0.7499.193"
            mock_edge.return_value = "143.0.3650.139"
            mock_driver.return_value = "143.0.0.0"
            
            # Test Chrome compatibility (should use chromedriver.exe)
            chrome_result = self.checker.check_compatibility("chrome")
            mock_driver.assert_called_with("chromedriver.exe")
            
            # Test Edge compatibility (should use msedgedriver.exe)
            edge_result = self.checker.check_compatibility("edge")
            mock_driver.assert_called_with("msedgedriver.exe")
    
    def test_browser_specific_compatibility_messages(self):
        """Test that compatibility messages are browser-specific."""
        with patch.object(self.checker, 'get_browser_version') as mock_chrome, \
             patch.object(self.checker, 'get_edge_version') as mock_edge, \
             patch.object(self.checker, 'get_driver_version') as mock_driver:
            
            # Both browsers not found
            mock_chrome.return_value = "unknown"
            mock_edge.return_value = "unknown"
            mock_driver.return_value = "unknown"
            
            chrome_result = self.checker.check_compatibility("chrome")
            edge_result = self.checker.check_compatibility("edge")
            
            # Should mention browser names specifically
            self.assertIn("chrome", chrome_result["recommendation"].lower())
            self.assertIn("edge", edge_result["recommendation"].lower())


if __name__ == '__main__':
    unittest.main()