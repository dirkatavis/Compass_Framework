"""
Unit tests for DriverFactory.
Ensures self-healing, process management, and dual-approach logic works correctly.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException
from compass_core.driver_factory import DriverFactory

class TestDriverFactory(unittest.TestCase):
    
    def setUp(self):
        self.mock_logger = Mock()
        self.factory = DriverFactory(driver_path="test_driver.exe", logger=self.mock_logger)

    @patch('subprocess.run')
    def test_kill_locked_drivers(self, mock_run):
        """Test that taskkill is called to release locked drivers."""
        with patch('sys.platform', 'win32'):
            self.factory.kill_locked_drivers()
            mock_run.assert_called_with(
                ["taskkill", "/F", "/IM", "msedgedriver.exe", "/T"],
                capture_output=True, check=False
            )

    @patch('webdriver_manager.microsoft.EdgeChromiumDriverManager.install')
    @patch.object(DriverFactory, 'kill_locked_drivers')
    def test_update_driver_approach_a_success(self, mock_kill, mock_install):
        """Test Approach A (webdriver-manager) integration."""
        mock_install.return_value = "new/path/to/driver.exe"
        
        path = self.factory.update_driver_approach_a()
        
        self.assertEqual(path, "new/path/to/driver.exe")
        mock_kill.assert_called_once()
        mock_install.assert_called_once()

    @patch('selenium.webdriver.Edge')
    @patch.object(DriverFactory, 'update_driver_approach_a')
    def test_get_driver_self_healing_success(self, mock_update, mock_edge):
        """Test that get_driver heals and retries on version mismatch."""
        # 1. First attempt fails with version error
        # 2. Update succeeds
        # 3. Second attempt succeeds
        mock_edge.side_effect = [
            SessionNotCreatedException("This version of Microsoft Edge WebDriver only supports version 120"),
            Mock() # Success on second call
        ]
        mock_update.return_value = "updated_driver.exe"
        
        driver = self.factory.get_driver()
        
        self.assertIsNotNone(driver)
        self.assertEqual(mock_update.call_count, 1)
        self.assertEqual(mock_edge.call_count, 2)
        self.assertEqual(self.factory.driver_path, "updated_driver.exe")

    @patch('selenium.webdriver.Edge')
    def test_get_driver_unrecoverable_error(self, mock_edge):
        """Test that non-version related errors are not healed and raise immediately."""
        mock_edge.side_effect = WebDriverException("Some other random error")
        
        with self.assertRaises(RuntimeError) as context:
            self.factory.get_driver()
        
        self.assertIn("Unrecoverable WebDriver error", str(context.exception))
        self.assertEqual(mock_edge.call_count, 1)

    @patch('urllib.request.urlopen')
    @patch('zipfile.ZipFile')
    @patch('builtins.open', new_callable=MagicMock)
    @patch.object(DriverFactory, 'kill_locked_drivers')
    def test_update_driver_approach_b_manual(self, mock_kill, mock_open, mock_zip, mock_urlopen):
        """Test Approach B (Manual Scrape) fallback logic."""
        # Mock browser version detection
        self.factory.checker = Mock()
        self.factory.checker.get_edge_version.return_value = "145.0.0.0"
        
        # Mock URL download
        mock_response = MagicMock()
        mock_response.read.return_value = b"zip_content"
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Mock Zip extraction
        mock_zip_instance = mock_zip.return_value.__enter__.return_value
        mock_zip_instance.namelist.return_value = ["msedgedriver.exe"]
        mock_zip_instance.read.return_value = b"exe_content"
        
        path = self.factory.update_driver_approach_b()
        
        self.assertEqual(path, "test_driver.exe")
        mock_kill.assert_called_once()
        self.assertIn("145.0.0.0", mock_urlopen.call_args[0][0])
        mock_open.assert_called()

if __name__ == '__main__':
    unittest.main()
