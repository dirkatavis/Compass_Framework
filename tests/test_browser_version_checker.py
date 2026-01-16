"""
Tests for BrowserVersionChecker implementation.
"""
import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
from compass_core.browser_version_checker import BrowserVersionChecker
from compass_core.version_checker import VersionChecker


class TestBrowserVersionChecker(unittest.TestCase):
    """Test BrowserVersionChecker implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.checker = BrowserVersionChecker()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.temp_dir.name
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_version_checker_protocol_compliance(self):
        """Test that BrowserVersionChecker implements VersionChecker protocol."""
        self.assertIsInstance(self.checker, VersionChecker)
    
    def test_browser_version_checker_initialization(self):
        """Test BrowserVersionChecker initialization."""
        checker = BrowserVersionChecker()
        self.assertIsInstance(checker, BrowserVersionChecker)
    
    @patch('compass_core.browser_version_checker.BrowserVersionChecker._get_chrome_version')
    def test_get_browser_version_delegates_to_chrome(self, mock_chrome):
        """Test get_browser_version delegates to Chrome version detection."""
        mock_chrome.return_value = "131.0.6778.85"
        
        result = self.checker.get_browser_version()
        
        self.assertEqual(result, "131.0.6778.85")
        mock_chrome.assert_called_once()
    
    @patch('compass_core.browser_version_checker.winreg')
    def test_get_chrome_version_from_registry_success(self, mock_winreg):
        """Test Chrome version detection from registry."""
        # Mock successful registry read
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.QueryValueEx.return_value = ("131.0.6778.85", None)
        
        result = self.checker._get_chrome_version_from_registry()
        
        self.assertEqual(result, "131.0.6778.85")
    
    @patch('compass_core.browser_version_checker.winreg')
    def test_get_chrome_version_from_registry_not_found(self, mock_winreg):
        """Test Chrome version detection when registry key not found."""
        mock_winreg.OpenKey.side_effect = FileNotFoundError()
        
        result = self.checker._get_chrome_version_from_registry()
        
        self.assertEqual(result, "unknown")
    
    @patch('compass_core.browser_version_checker.winreg')
    def test_get_edge_version_from_registry_success(self, mock_winreg):
        """Test Edge version detection from registry."""
        # Mock successful registry read
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.QueryValueEx.return_value = ("131.0.2903.70", None)
        
        result = self.checker._get_edge_version_from_registry()
        
        self.assertEqual(result, "131.0.2903.70")
    
    @patch('compass_core.browser_version_checker.subprocess.run')
    def test_get_version_from_executable_success(self, mock_run):
        """Test version detection from executable --version output."""
        # Mock successful subprocess call
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Google Chrome 131.0.6778.85"
        mock_run.return_value = mock_result
        
        result = self.checker._get_version_from_executable("chrome.exe")
        
        self.assertEqual(result, "131.0.6778.85")
        mock_run.assert_called_once_with(
            ["chrome.exe", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
    
    @patch('compass_core.browser_version_checker.subprocess.run')
    def test_get_version_from_executable_no_version_match(self, mock_run):
        """Test version detection when executable output has no version."""
        # Mock subprocess call with no version in output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Invalid output"
        mock_run.return_value = mock_result
        
        result = self.checker._get_version_from_executable("chrome.exe")
        
        self.assertEqual(result, "unknown")
    
    @patch('compass_core.browser_version_checker.subprocess.run')
    def test_get_version_from_executable_timeout(self, mock_run):
        """Test version detection when subprocess times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("chrome.exe", 10)
        
        result = self.checker._get_version_from_executable("chrome.exe")
        
        self.assertEqual(result, "unknown")
    
    @patch('compass_core.browser_version_checker.subprocess.run')
    def test_get_version_from_executable_file_not_found(self, mock_run):
        """Test version detection when executable not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = self.checker._get_version_from_executable("nonexistent.exe")
        
        self.assertEqual(result, "unknown")
    
    @patch('os.path.exists')
    @patch('compass_core.browser_version_checker.subprocess.run')
    def test_get_driver_version_success(self, mock_run, mock_exists):
        """Test driver version detection success."""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "ChromeDriver 131.0.6778.85"
        mock_run.return_value = mock_result
        
        result = self.checker.get_driver_version("chromedriver.exe")
        
        self.assertEqual(result, "131.0.6778.85")
        mock_exists.assert_called_once_with("chromedriver.exe")
    
    @patch('os.path.exists')
    def test_get_driver_version_file_not_exists(self, mock_exists):
        """Test driver version detection when file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.checker.get_driver_version("nonexistent_driver.exe")
        
        self.assertEqual(result, "unknown")
    
    @patch('compass_core.browser_version_checker.BrowserVersionChecker._get_chrome_version_from_registry')
    @patch('os.path.exists')
    @patch('compass_core.browser_version_checker.BrowserVersionChecker._get_version_from_executable')
    def test_get_chrome_version_fallback_to_executable(self, mock_exe_version, mock_exists, mock_registry):
        """Test Chrome version detection falls back to executable when registry fails."""
        # Registry fails
        mock_registry.return_value = "unknown"
        # Executable succeeds
        mock_exists.return_value = True
        mock_exe_version.return_value = "131.0.6778.85"
        
        result = self.checker._get_chrome_version()
        
        self.assertEqual(result, "131.0.6778.85")
        mock_registry.assert_called_once()
        mock_exe_version.assert_called_once()
    
    @patch('compass_core.browser_version_checker.BrowserVersionChecker._get_edge_version_from_registry')
    @patch('os.path.exists')
    @patch('compass_core.browser_version_checker.BrowserVersionChecker._get_version_from_executable')
    def test_get_edge_version_fallback_to_executable(self, mock_exe_version, mock_exists, mock_registry):
        """Test Edge version detection falls back to executable when registry fails."""
        # Registry fails
        mock_registry.return_value = "unknown"
        # Executable succeeds
        mock_exists.return_value = True
        mock_exe_version.return_value = "131.0.2903.70"
        
        result = self.checker._get_edge_version()
        
        self.assertEqual(result, "131.0.2903.70")
        mock_registry.assert_called_once()
        mock_exe_version.assert_called_once()
    
    @patch('compass_core.browser_version_checker.BrowserVersionChecker._get_chrome_version_from_registry')
    @patch('os.path.exists')
    def test_get_chrome_version_all_methods_fail(self, mock_exists, mock_registry):
        """Test Chrome version detection when all methods fail."""
        # Registry fails
        mock_registry.return_value = "unknown"
        # No executable files exist
        mock_exists.return_value = False
        
        result = self.checker._get_chrome_version()
        
        self.assertEqual(result, "unknown")
    
    def test_get_edge_version_method_exists(self):
        """Test that get_edge_version method exists and is callable."""
        self.assertTrue(hasattr(self.checker, 'get_edge_version'))
        self.assertTrue(callable(self.checker.get_edge_version))
    
    def test_check_compatibility_method_exists(self):
        """Test that check_compatibility method exists and is callable."""
        self.assertTrue(hasattr(self.checker, 'check_compatibility'))
        self.assertTrue(callable(self.checker.check_compatibility))
    
    @patch.object(BrowserVersionChecker, 'get_browser_version')
    @patch.object(BrowserVersionChecker, 'get_driver_version')
    def test_check_compatibility_returns_dict(self, mock_driver, mock_browser):
        """Test check_compatibility returns proper dictionary structure."""
        mock_browser.return_value = "131.0.6778.85"
        mock_driver.return_value = "131.0.6778.85"
        
        result = self.checker.check_compatibility()
        
        self.assertIsInstance(result, dict)
        required_keys = ["browser_version", "driver_version", "compatible", 
                        "major_match", "exact_match", "recommendation"]
        for key in required_keys:
            self.assertIn(key, result)
    
    @patch('compass_core.browser_version_checker.BrowserVersionChecker._get_edge_version')
    def test_get_edge_version_returns_string(self, mock_edge):
        """Test get_edge_version returns string."""
        mock_edge.return_value = "131.0.2903.70"
        
        result = self.checker.get_edge_version()
        
        self.assertIsInstance(result, str)
        self.assertEqual(result, "131.0.2903.70")


# Import subprocess for TimeoutExpired in tests
import subprocess


if __name__ == '__main__':
    unittest.main()