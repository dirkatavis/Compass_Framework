import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from compass_core.legacy_driver import LegacyDriverManager


class TestLegacyDriverManager(unittest.TestCase):
    """Tests for the legacy driver manager - testing current behavior before refactoring."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.driver_manager = LegacyDriverManager(project_root=self.temp_dir)

    def test_driver_manager_initialization(self):
        """Test that driver manager initializes with correct paths."""
        self.assertEqual(self.driver_manager.project_root, self.temp_dir)
        expected_driver_path = os.path.join(self.temp_dir, "msedgedriver.exe")
        self.assertEqual(self.driver_manager.driver_path, expected_driver_path)

    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    def test_get_browser_version_success(self, mock_query, mock_open):
        """Test successful browser version retrieval."""
        mock_query.return_value = ("131.0.2903.70", None)
        
        version = self.driver_manager.get_browser_version()
        
        self.assertEqual(version, "131.0.2903.70")
        mock_open.assert_called_once()
        mock_query.assert_called_once()

    @patch('winreg.OpenKey', side_effect=Exception("Registry error"))
    def test_get_browser_version_error(self, mock_open):
        """Test browser version retrieval when registry access fails."""
        version = self.driver_manager.get_browser_version()
        
        self.assertEqual(version, "unknown")

    def test_get_driver_version_file_not_found(self):
        """Test driver version when file doesn't exist."""
        # Driver file doesn't exist in temp directory
        version = self.driver_manager.get_driver_version()
        
        self.assertEqual(version, "unknown")

    @patch('subprocess.check_output')
    @patch('os.path.exists', return_value=True)
    def test_get_driver_version_success(self, mock_exists, mock_subprocess):
        """Test successful driver version retrieval."""
        mock_subprocess.return_value = "MSEdgeDriver 131.0.2903.70 (some_hash)"
        
        version = self.driver_manager.get_driver_version()
        
        self.assertEqual(version, "131.0.2903.70")

    @patch('subprocess.check_output', side_effect=Exception("Subprocess error"))
    @patch('os.path.exists', return_value=True)
    def test_get_driver_version_subprocess_error(self, mock_exists, mock_subprocess):
        """Test driver version when subprocess fails."""
        version = self.driver_manager.get_driver_version()
        
        self.assertEqual(version, "unknown")

    def test_version_mismatch_detection(self):
        """Test that version mismatch is properly detected."""
        with patch.object(self.driver_manager, 'get_browser_version', return_value="131.0.2903.70"):
            with patch.object(self.driver_manager, 'get_driver_version', return_value="130.0.2849.68"):
                with self.assertRaises(RuntimeError) as context:
                    self.driver_manager.get_or_create_driver()
                
                self.assertIn("version mismatch", str(context.exception).lower())

    @patch('compass_core.legacy_driver._driver', None)
    def test_global_state_isolation(self):
        """Test that global state affects multiple instances (demonstrating coupling issue)."""
        # This test documents the current coupling problem
        import compass_core.legacy_driver as driver_module
        
        # Initially no driver
        self.assertIsNone(driver_module._driver)
        
        # This demonstrates the problematic global state
        driver_module._driver = Mock()
        
        # Both instances see the same global state
        dm1 = LegacyDriverManager()
        dm2 = LegacyDriverManager()
        
        # Clean up
        driver_module._driver = None


if __name__ == '__main__':
    unittest.main()