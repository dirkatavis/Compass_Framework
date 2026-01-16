"""Test INI Configuration implementation."""

import unittest
import tempfile
import os
from pathlib import Path

from compass_core import IniConfiguration


class TestIniConfiguration(unittest.TestCase):
    """Test INI configuration functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.ini_file = Path(self.test_dir) / "test.ini"
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_ini_configuration_initialization(self):
        """Test IniConfiguration initialization."""
        config = IniConfiguration()
        self.assertIsInstance(config, IniConfiguration)
    
    def test_load_valid_ini_file(self):
        """Test loading a valid INI configuration file."""
        # Create test INI file
        ini_content = """
[webdriver]
edge_path = drivers.local/edge/msedgedriver.exe
chrome_path = drivers.local/chrome/chromedriver.exe

[timeouts]
page_load = 30
implicit_wait = 10
"""
        with open(self.ini_file, 'w') as f:
            f.write(ini_content)
        
        config = IniConfiguration()
        data = config.load(self.ini_file)
        
        self.assertIn('webdriver', data)
        self.assertIn('timeouts', data)
        self.assertEqual(data['webdriver']['edge_path'], 'drivers.local/edge/msedgedriver.exe')
        self.assertEqual(data['timeouts']['page_load'], 30)
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises FileNotFoundError."""
        config = IniConfiguration()
        with self.assertRaises(FileNotFoundError):
            config.load(Path(self.test_dir) / "nonexistent.ini")
    
    def test_get_with_dot_notation(self):
        """Test getting values with dot notation for nested keys."""
        ini_content = """
[webdriver]
edge_path = drivers.local/edge/msedgedriver.exe
"""
        with open(self.ini_file, 'w') as f:
            f.write(ini_content)
        
        config = IniConfiguration()
        config.load(self.ini_file)
        
        result = config.get('webdriver.edge_path')
        self.assertEqual(result, 'drivers.local/edge/msedgedriver.exe')
    
    def test_get_with_default_value(self):
        """Test getting non-existent keys returns default value."""
        # Create empty INI file
        with open(self.ini_file, 'w') as f:
            f.write("")
            
        config = IniConfiguration()
        config.load(self.ini_file)  # Empty file
        
        result = config.get('nonexistent.key', 'default_value')
        self.assertEqual(result, 'default_value')
    
    def test_set_with_dot_notation(self):
        """Test setting values with dot notation creates nested structure."""
        config = IniConfiguration()
        config.set('webdriver.edge_path', 'test/path/driver.exe')
        
        result = config.get('webdriver.edge_path')
        self.assertEqual(result, 'test/path/driver.exe')
    
    def test_configuration_protocol_compliance(self):
        """Test that IniConfiguration implements Configuration protocol."""
        from compass_core.configuration import Configuration
        config = IniConfiguration()
        self.assertIsInstance(config, Configuration)
    
    def test_validate_configuration(self):
        """Test configuration validation."""
        config = IniConfiguration(config_path="nonexistent.ini")  # Don't auto-load
        
        # Test empty configuration
        result = config.validate()
        self.assertIn("Configuration is empty", result["warnings"])
    
    def test_default_config_loading(self):
        """Test that default configuration loading works."""
        # Create webdriver.ini.local in current directory
        local_ini = Path("webdriver.ini.local")
        if local_ini.exists():
            # Test with existing local config
            config = IniConfiguration()
            data = config.get_all()
            self.assertIsInstance(data, dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)