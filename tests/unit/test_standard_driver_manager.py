import subprocess
import types
import pytest

from unittest.mock import Mock

from compass_core.standard_driver_manager import StandardDriverManager


@pytest.mark.new_slice
def test_get_driver_version_success(monkeypatch, tmp_path):
    manager = StandardDriverManager(driver_path=str(tmp_path / 'msedgedriver.exe'))

    # pretend the file exists
    monkeypatch.setattr('os.path.exists', lambda p: True)

    # mock subprocess.check_output to return a version string
    monkeypatch.setattr(subprocess, 'check_output', lambda *a, **k: 'MSEdgeDriver 120.0.6099.109')

    v = manager.get_driver_version(manager._driver_path)
    assert v == '120.0.6099.109'


@pytest.mark.new_slice
def test_get_driver_version_missing_file(monkeypatch):
    manager = StandardDriverManager(driver_path='nope.exe')
    monkeypatch.setattr('os.path.exists', lambda p: False)
    v = manager.get_driver_version('nope.exe')
    assert v == 'unknown'


@pytest.mark.new_slice
def test_get_driver_version_timeout_and_exception(monkeypatch, tmp_path):
    manager = StandardDriverManager(driver_path=str(tmp_path / 'msedgedriver.exe'))
    monkeypatch.setattr('os.path.exists', lambda p: True)

    # TimeoutExpired
    def raise_timeout(*a, **k):
        raise subprocess.TimeoutExpired(cmd=a[0], timeout=1)

    monkeypatch.setattr(subprocess, 'check_output', raise_timeout)
    assert manager.get_driver_version(manager._driver_path) == 'unknown'

    # Generic exception
    def raise_exc(*a, **k):
        raise RuntimeError('boom')

    monkeypatch.setattr(subprocess, 'check_output', raise_exc)
    assert manager.get_driver_version(manager._driver_path) == 'unknown'


@pytest.mark.new_slice
def test_check_version_compatibility_various():
    manager = StandardDriverManager(driver_path='d')
    # unknown versions
    assert manager.check_version_compatibility('unknown', 'unknown')['compatible'] is False

    # same major
    r = manager.check_version_compatibility('120.1.2.3', '120.0.0.1')
    assert r['compatible'] is True

    # different major
    r2 = manager.check_version_compatibility('121.0.0.0', '120.0.0.1')
    assert r2['compatible'] is False and r2['status'] == 'major_version_mismatch'

    # parse error
    r3 = manager.check_version_compatibility(None, 123)
    assert r3['compatible'] is False and r3['status'] in ('parse_error', 'version_unknown')


@pytest.mark.new_slice
def test_get_or_create_driver_raises_on_version_mismatch(monkeypatch, tmp_path):
    manager = StandardDriverManager(driver_path=str(tmp_path / 'msedgedriver.exe'))
    monkeypatch.setattr('os.path.exists', lambda p: True)

    # Force browser and driver versions that mismatch
    monkeypatch.setattr(manager, '_get_browser_version', lambda: '121.0.0.0')
    monkeypatch.setattr(manager, 'get_driver_version', lambda p: '120.0.0.1')

    with pytest.raises(RuntimeError):
        manager.get_or_create_driver()


@pytest.mark.new_slice
def test_get_or_create_driver_creates_and_quits(monkeypatch, tmp_path):
    manager = StandardDriverManager(driver_path=str(tmp_path / 'msedgedriver.exe'))
    monkeypatch.setattr('os.path.exists', lambda p: True)

    # compatible versions
    monkeypatch.setattr(manager, '_get_browser_version', lambda: '120.0.0.0')
    monkeypatch.setattr(manager, 'get_driver_version', lambda p: '120.0.0.1')

    # Mock Edge WebDriver creation
    fake_driver = Mock()
    fake_driver.maximize_window = Mock()
    fake_driver.quit = Mock()
    fake_driver.current_url = 'http://example'

    # patch the webdriver.Edge symbol used in the module
    monkeypatch.setattr('selenium.webdriver.Edge', lambda *a, **k: fake_driver)

    drv = manager.get_or_create_driver(headless=True, incognito=True, window_size=(800, 600))
    assert drv is fake_driver
    assert manager.is_driver_active() is True

    # After quit, driver should be None and is_driver_active returns False
    manager.quit_driver()
    assert manager._driver is None
    assert manager.is_driver_active() is False
"""
Tests for StandardDriverManager implementation.
TDD approach - test the concrete implementation thoroughly.
"""
import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from selenium.common.exceptions import SessionNotCreatedException

from compass_core.driver_manager import DriverManager
from compass_core.standard_driver_manager import StandardDriverManager


class TestStandardDriverManager(unittest.TestCase):
    """Test StandardDriverManager concrete implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_driver_path = os.path.join(tempfile.gettempdir(), "test_msedgedriver.exe")
        self.manager = StandardDriverManager(driver_path=self.test_driver_path)
    
    def tearDown(self):
        """Clean up after tests."""
        # Ensure driver is cleaned up
        if hasattr(self.manager, '_driver') and self.manager._driver:
            try:
                self.manager.quit_driver()
            except Exception:
                pass
                
        # Clean up test files
        if os.path.exists(self.test_driver_path):
            try:
                os.remove(self.test_driver_path)
            except Exception:
                pass
    
    def test_protocol_compliance(self):
        """Test that StandardDriverManager implements DriverManager protocol."""
        self.assertIsInstance(self.manager, DriverManager)
        
        # Verify required methods exist
        required_methods = [
            'get_or_create_driver', 'quit_driver', 'get_driver_version',
            'configure_driver_options', 'create_driver_service', 
            'is_driver_active', 'check_version_compatibility'
        ]
        for method_name in required_methods:
            self.assertTrue(hasattr(self.manager, method_name))
            self.assertTrue(callable(getattr(self.manager, method_name)))
    
    def test_initialization_with_custom_path(self):
        """Test StandardDriverManager initialization with custom driver path."""
        custom_path = "/custom/path/driver.exe"
        manager = StandardDriverManager(driver_path=custom_path)
        self.assertEqual(manager._driver_path, custom_path)
        self.assertIsNone(manager._driver)  # Should start with no active driver
    
    def test_initialization_with_default_path(self):
        """Test StandardDriverManager initialization with default driver path."""
        manager = StandardDriverManager()
        self.assertIsNotNone(manager._driver_path)
        self.assertTrue(manager._driver_path.endswith("msedgedriver.exe"))
        self.assertIsNone(manager._driver)
    
    def test_get_driver_version_file_not_exists(self):
        """Test get_driver_version when driver file doesn't exist."""
        version = self.manager.get_driver_version("/nonexistent/path/driver.exe")
        self.assertEqual(version, "unknown")
    
    @patch('subprocess.check_output')
    def test_get_driver_version_success(self, mock_subprocess):
        """Test get_driver_version with successful version detection."""
        # Mock subprocess output with version info
        mock_subprocess.return_value = "MSEdgeDriver 120.0.6099.109"
        
        # Create temporary driver file
        with open(self.test_driver_path, 'w') as f:
            f.write("dummy driver content")
        
        version = self.manager.get_driver_version(self.test_driver_path)
        self.assertEqual(version, "120.0.6099.109")
        mock_subprocess.assert_called_once_with([self.test_driver_path, "--version"], text=True, timeout=10)
    
    @patch('subprocess.check_output')
    def test_get_driver_version_no_version_pattern(self, mock_subprocess):
        """Test get_driver_version when output has no version pattern."""
        mock_subprocess.return_value = "Some output without version"
        
        with open(self.test_driver_path, 'w') as f:
            f.write("dummy driver content")
        
        version = self.manager.get_driver_version(self.test_driver_path)
        self.assertEqual(version, "unknown")
    
    @patch('subprocess.check_output')
    def test_get_driver_version_subprocess_error(self, mock_subprocess):
        """Test get_driver_version when subprocess fails."""
        mock_subprocess.side_effect = Exception("Command failed")
        
        with open(self.test_driver_path, 'w') as f:
            f.write("dummy driver content")
        
        version = self.manager.get_driver_version(self.test_driver_path)
        self.assertEqual(version, "unknown")
    
    def test_configure_driver_options(self):
        """Test configure_driver_options returns Edge options."""
        options = self.manager.configure_driver_options()
        
        # Should return EdgeOptions object
        self.assertIsNotNone(options)
        # Verify it has expected Edge-specific configuration
        self.assertIn("--start-maximized", options.arguments)
    
    def test_create_driver_service(self):
        """Test create_driver_service creates Edge service."""
        service = self.manager.create_driver_service(self.test_driver_path)
        
        # Should return Service object
        self.assertIsNotNone(service)
        # Should be configured with the driver path
        self.assertEqual(service.path, self.test_driver_path)
    
    def test_is_driver_active_no_driver(self):
        """Test is_driver_active when no driver exists."""
        self.assertFalse(self.manager.is_driver_active())
    
    @patch.object(StandardDriverManager, '_get_browser_version')
    def test_is_driver_active_with_mock_driver(self, mock_browser_version):
        """Test is_driver_active with mock driver."""
        mock_browser_version.return_value = "120.0.0.0"
        
        # Mock an active driver
        mock_driver = Mock()
        mock_driver.current_url = "https://example.com"
        self.manager._driver = mock_driver
        
        self.assertTrue(self.manager.is_driver_active())
    
    def test_is_driver_active_dead_driver(self):
        """Test is_driver_active when driver session is dead."""
        # Mock a dead driver that raises exception
        mock_driver = Mock()
        # Use a property mock that raises exception when accessed
        type(mock_driver).current_url = PropertyMock(side_effect=Exception("Session is dead"))
        self.manager._driver = mock_driver
        
        self.assertFalse(self.manager.is_driver_active())
        self.assertIsNone(self.manager._driver)  # Should reset driver to None
    
    def test_quit_driver_no_driver(self):
        """Test quit_driver when no driver exists."""
        # Should not raise exception
        try:
            self.manager.quit_driver()
        except Exception as e:
            self.fail(f"quit_driver raised exception when no driver exists: {e}")
    
    def test_quit_driver_with_mock_driver(self):
        """Test quit_driver with mock driver."""
        mock_driver = Mock()
        self.manager._driver = mock_driver
        
        self.manager.quit_driver()
        
        mock_driver.quit.assert_called_once()
        self.assertIsNone(self.manager._driver)
    
    def test_quit_driver_exception_handling(self):
        """Test quit_driver handles exceptions during quit."""
        mock_driver = Mock()
        mock_driver.quit.side_effect = Exception("Quit failed")
        self.manager._driver = mock_driver
        
        # Should not raise exception, but should reset driver
        self.manager.quit_driver()
        self.assertIsNone(self.manager._driver)
    
    def test_check_version_compatibility_unknown_versions(self):
        """Test check_version_compatibility with unknown versions."""
        result = self.manager.check_version_compatibility("unknown", "120.0.0.0")
        self.assertFalse(result["compatible"])
        self.assertEqual(result["status"], "version_unknown")
        
        result = self.manager.check_version_compatibility("120.0.0.0", "unknown")
        self.assertFalse(result["compatible"])
        self.assertEqual(result["status"], "version_unknown")
    
    def test_check_version_compatibility_matching_major(self):
        """Test check_version_compatibility with matching major versions."""
        result = self.manager.check_version_compatibility("120.0.6099.109", "120.0.6000.50")
        self.assertTrue(result["compatible"])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["browser_version"], "120.0.6099.109")
        self.assertEqual(result["driver_version"], "120.0.6000.50")
    
    def test_check_version_compatibility_mismatched_major(self):
        """Test check_version_compatibility with mismatched major versions."""
        result = self.manager.check_version_compatibility("120.0.6099.109", "119.0.6000.50")
        self.assertFalse(result["compatible"])
        self.assertEqual(result["status"], "major_version_mismatch")
        self.assertIn("Update driver to version 120", result["recommendation"])
    
    def test_check_version_compatibility_parse_error(self):
        """Test check_version_compatibility with invalid version format."""
        # Test with None values that will cause AttributeError
        result = self.manager.check_version_compatibility(None, "120.0.0.0") 
        self.assertFalse(result["compatible"])
        self.assertEqual(result["status"], "parse_error")
    
    @patch.object(StandardDriverManager, '_get_browser_version')
    @patch.object(StandardDriverManager, 'get_driver_version')
    @patch('compass_core.standard_driver_manager.webdriver.Edge')
    def test_get_or_create_driver_success(self, mock_edge, mock_get_driver_version, mock_get_browser_version):
        """Test successful driver creation with version compatibility."""
        # Mock version detection
        mock_get_browser_version.return_value = "120.0.6099.109"
        mock_get_driver_version.return_value = "120.0.6000.50"
        
        # Mock WebDriver creation
        mock_driver = Mock()
        mock_edge.return_value = mock_driver
        
        driver = self.manager.get_or_create_driver()
        
        # Verify driver was created and configured
        self.assertEqual(driver, mock_driver)
        self.assertEqual(self.manager._driver, mock_driver)
        mock_driver.maximize_window.assert_called_once()
        mock_driver.implicitly_wait.assert_called_once_with(10)
    
    @patch.object(StandardDriverManager, '_get_browser_version')
    @patch.object(StandardDriverManager, 'get_driver_version')
    def test_get_or_create_driver_version_mismatch(self, mock_get_driver_version, mock_get_browser_version):
        """Test driver creation fails with version mismatch."""
        # Mock mismatched versions
        mock_get_browser_version.return_value = "120.0.6099.109"
        mock_get_driver_version.return_value = "119.0.6000.50"
        
        with self.assertRaises(RuntimeError) as context:
            self.manager.get_or_create_driver()
        
        self.assertIn("Version mismatch", str(context.exception))
    
    @patch.object(StandardDriverManager, '_get_browser_version')
    @patch.object(StandardDriverManager, 'get_driver_version')
    @patch('compass_core.standard_driver_manager.webdriver.Edge')
    def test_get_or_create_driver_singleton_pattern(self, mock_edge, mock_get_driver_version, mock_get_browser_version):
        """Test that get_or_create_driver implements singleton pattern."""
        # Mock version detection
        mock_get_browser_version.return_value = "120.0.6099.109"
        mock_get_driver_version.return_value = "120.0.6000.50"
        
        # Mock WebDriver creation
        mock_driver = Mock()
        mock_edge.return_value = mock_driver
        
        # First call should create driver
        driver1 = self.manager.get_or_create_driver()
        self.assertEqual(mock_edge.call_count, 1)
        
        # Second call should return same driver
        driver2 = self.manager.get_or_create_driver()
        self.assertEqual(mock_edge.call_count, 1)  # Should not create another
        self.assertEqual(driver1, driver2)
    
    @patch.object(StandardDriverManager, '_get_browser_version')
    @patch.object(StandardDriverManager, 'get_driver_version')
    @patch('compass_core.standard_driver_manager.webdriver.Edge')
    def test_get_or_create_driver_with_custom_options(self, mock_edge, mock_get_driver_version, mock_get_browser_version):
        """Test driver creation with custom options."""
        mock_get_browser_version.return_value = "120.0.6099.109"
        mock_get_driver_version.return_value = "120.0.6000.50"
        mock_edge.return_value = Mock()
        
        # Create driver with custom options
        self.manager.get_or_create_driver(headless=True, window_size=(1920, 1080))
        
        # Verify Edge was called (options verification would be more complex)
        mock_edge.assert_called_once()
    
    @patch.object(StandardDriverManager, '_get_browser_version')
    @patch.object(StandardDriverManager, 'get_driver_version')
    @patch('compass_core.standard_driver_manager.webdriver.Edge')
    def test_get_or_create_driver_session_creation_error(self, mock_edge, mock_get_driver_version, mock_get_browser_version):
        """Test driver creation handles SessionNotCreatedException."""
        mock_get_browser_version.return_value = "120.0.6099.109"
        mock_get_driver_version.return_value = "120.0.6000.50"
        mock_edge.side_effect = SessionNotCreatedException("Session creation failed")
        
        with self.assertRaises(RuntimeError) as context:
            self.manager.get_or_create_driver()
        
        self.assertIn("Failed to create WebDriver session", str(context.exception))
    
    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    @patch('winreg.CloseKey')
    def test_get_browser_version_success(self, mock_close_key, mock_query_value, mock_open_key):
        """Test successful browser version detection."""
        mock_query_value.return_value = ("120.0.6099.109", None)
        
        version = self.manager._get_browser_version()
        self.assertEqual(version, "120.0.6099.109")
        mock_open_key.assert_called_once()
        mock_query_value.assert_called_once()
        mock_close_key.assert_called_once()
    
    @patch('winreg.OpenKey')
    def test_get_browser_version_registry_error(self, mock_open_key):
        """Test browser version detection handles registry errors."""
        mock_open_key.side_effect = Exception("Registry access failed")
        
        version = self.manager._get_browser_version()
        self.assertEqual(version, "unknown")
    
    @patch('compass_core.ini_configuration.IniConfiguration')
    def test_configuration_caching_performance(self, mock_ini_config_class):
        """Test that IniConfiguration is cached and not created repeatedly."""
        # Setup mock configuration instance
        mock_config = Mock()
        mock_config.get.return_value = ""
        mock_config.load.return_value = True
        mock_ini_config_class.return_value = mock_config
        
        # Create a new manager instance to trigger initialization
        # This will call _get_configured_driver_path once during init
        manager = StandardDriverManager()
        
        # Configuration should be created only once during initialization
        self.assertEqual(mock_ini_config_class.call_count, 1)
        # Config.get was called once during initialization
        init_call_count = mock_config.get.call_count
        
        # Call _get_configured_driver_path multiple additional times
        path1 = manager._get_configured_driver_path()
        path2 = manager._get_configured_driver_path()
        path3 = manager._get_configured_driver_path()
        
        # Configuration should still only be created once (cached)
        self.assertEqual(mock_ini_config_class.call_count, 1)
        
        # Config.get should be called for each additional lookup (init + 3 new calls)
        self.assertEqual(mock_config.get.call_count, init_call_count + 3)
        
        # All paths should be the same (fallback path since mock returns empty)
        self.assertEqual(path1, path2)
        self.assertEqual(path2, path3)


if __name__ == '__main__':
    unittest.main()