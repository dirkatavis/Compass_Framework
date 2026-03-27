"""
Negative test: Simulate driver version mismatch to verify error handling.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import SessionNotCreatedException
from compass_core.standard_driver_manager import StandardDriverManager


class TestDriverVersionMismatch(unittest.TestCase):
    """Test driver manager behavior when browser and driver versions don't match."""
    
    @patch('compass_core.standard_driver_manager.DriverFactory')
    def test_driver_version_mismatch_detected(self, mock_factory_class):
        """Test that driver manager detects and reports version mismatches."""
        # Create mock factory
        mock_factory = MagicMock()
        mock_factory_class.return_value = mock_factory
        
        # Simulate version mismatch by making get_driver fail with version error
        mock_factory.get_driver.side_effect = SessionNotCreatedException(
            "This version of Microsoft Edge WebDriver only supports version 127 "
            "(but you have version 145)"
        )
        
        manager = StandardDriverManager(driver_path="test_driver.exe")
        
        # Attempt to create driver should fail with version mismatch
        with self.assertRaises(RuntimeError) as context:
            manager.get_or_create_driver()
        
        self.assertIn("Failed to create WebDriver session", str(context.exception))
        self.assertIn("version", str(context.exception).lower())
    
    @patch.object(StandardDriverManager, '_get_browser_version')
    @patch.object(StandardDriverManager, 'get_driver_version')
    def test_check_version_compatibility_major_mismatch(self, mock_driver_version, mock_browser_version):
        """Test version compatibility check with major version mismatch."""
        mock_browser_version.return_value = "145.0.7400.100"
        mock_driver_version.return_value = "127.0.6533.88"
        
        manager = StandardDriverManager()
        
        # Browser is 145, driver is 127 - should be incompatible
        result = manager.check_version_compatibility("145.0.7400.100", "127.0.6533.88")
        
        self.assertFalse(result["compatible"])
        self.assertEqual(result["status"], "major_version_mismatch")
        self.assertIn("145", result["recommendation"])
    
    @patch.object(StandardDriverManager, '_get_browser_version')
    @patch.object(StandardDriverManager, 'get_driver_version')
    def test_check_version_compatibility_minor_mismatch_is_ok(self, mock_driver_version, mock_browser_version):
        """Test version compatibility with matching major versions but different minor."""
        mock_browser_version.return_value = "127.0.6533.119"
        mock_driver_version.return_value = "127.0.6533.88"
        
        manager = StandardDriverManager()
        
        # Same major version (127) - should be compatible
        result = manager.check_version_compatibility("127.0.6533.119", "127.0.6533.88")
        
        self.assertTrue(result["compatible"])
        self.assertEqual(result["status"], "ok")
    
    @patch.object(StandardDriverManager, 'get_driver_version')
    def test_check_version_compatibility_unknown_driver_version(self, mock_driver_version):
        """Test compatibility check when driver version is unknown."""
        mock_driver_version.return_value = "unknown"
        
        manager = StandardDriverManager()
        
        result = manager.check_version_compatibility("127.0.6533.119", "unknown")
        
        self.assertFalse(result["compatible"])
        self.assertEqual(result["status"], "version_unknown")
        self.assertIn("Cannot determine", result["reason"])
    
    @patch('compass_core.standard_driver_manager.DriverFactory')
    @patch.object(StandardDriverManager, 'get_or_create_driver', side_effect=RuntimeError("Failed to create"))
    def test_driver_creation_failure_is_catchable(self, mock_get_driver, mock_factory):
        """Test that driver creation failures can be caught and handled."""
        manager = StandardDriverManager()
        
        # Caller can catch the RuntimeError
        with self.assertRaises(RuntimeError):
            manager.get_or_create_driver()


if __name__ == "__main__":
    unittest.main()
