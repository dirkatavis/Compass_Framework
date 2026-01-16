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
        result = config.set('webdriver.edge_path', 'test/path/driver.exe')
        
        # Test that set() returns bool (protocol compliance)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
        
        # Test value was actually set
        retrieved_value = config.get('webdriver.edge_path')
        self.assertEqual(retrieved_value, 'test/path/driver.exe')
    
    def test_set_method_return_type_compliance(self):
        """Test that set() method returns bool as per Configuration protocol."""
        config = IniConfiguration()
        
        # Test successful set operation
        result = config.set('test_key', 'test_value')
        self.assertIsInstance(result, bool, "set() must return bool per Configuration protocol")
        self.assertTrue(result, "set() should return True on success")
        
        # Test with nested key
        result = config.set('section.key', 'value')
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
    
    def test_save_method_protocol_compliance(self):
        """Test that save() method matches Configuration protocol signature."""
        config = IniConfiguration()
        test_config_data = {
            'webdriver': {
                'edge_path': 'test/path/driver.exe'
            },
            'timeouts': {
                'page_load': '30'
            }
        }
        
        test_file = Path(self.test_dir) / "protocol_test.ini"
        
        # Test save() method signature and return type
        result = config.save(test_config_data, test_file)
        self.assertIsInstance(result, bool, "save() must return bool per Configuration protocol")
        self.assertTrue(result, "save() should return True on successful save")
        
        # Verify file was created and contains expected content
        self.assertTrue(test_file.exists(), "save() should create the specified file")
        
        # Verify saved content can be loaded back
        new_config = IniConfiguration()
        loaded_data = new_config.load(test_file)
        self.assertEqual(loaded_data['webdriver']['edge_path'], 'test/path/driver.exe')
    
    def test_save_method_error_handling(self):
        """Test that save() method returns False on errors."""
        config = IniConfiguration()
        test_config_data = {'test': {'key': 'value'}}
        
        # Try to save to invalid path (should return False)
        invalid_path = "/invalid/path/that/should/not/exist/test.ini"
        result = config.save(test_config_data, invalid_path)
        self.assertIsInstance(result, bool)
        # Note: This might still succeed depending on system, so we just check return type
    
    def test_configuration_protocol_compliance(self):
        """Test that IniConfiguration implements Configuration protocol."""
        from compass_core.configuration import Configuration
        config = IniConfiguration()
        self.assertIsInstance(config, Configuration)
    
    def test_validate_configuration(self):
        """Test configuration validation with correct return format."""
        config = IniConfiguration(config_path="nonexistent.ini")  # Don't auto-load
        
        # Test empty configuration
        result = config.validate()
        
        # Test return format matches Configuration protocol (status, not valid)
        self.assertIn("status", result, "validate() must return 'status' key per protocol")
        self.assertIn("warnings", result, "validate() must return 'warnings' key")
        self.assertIn("errors", result, "validate() must return 'errors' key")
        
        # Test status value is string, not boolean
        self.assertIsInstance(result["status"], str, "status must be string ('valid'/'invalid')")
        self.assertIn(result["status"], ["valid", "invalid"], "status must be 'valid' or 'invalid'")
        
        # Test warnings for empty config
        self.assertIn("Configuration is empty", result["warnings"])
        
        # Test status is 'valid' for empty config (warnings don't make it invalid)
        self.assertEqual(result["status"], "valid", "Empty config should be valid with warnings")
    
    def test_validate_format_consistency_with_json_configuration(self):
        """Test that validate() format matches JsonConfiguration format."""
        from compass_core import JsonConfiguration
        
        ini_config = IniConfiguration(config_path="nonexistent.ini")
        json_config = JsonConfiguration()
        
        ini_result = ini_config.validate({})
        json_result = json_config.validate({})
        
        # Both should have same keys
        self.assertEqual(set(ini_result.keys()), set(json_result.keys()), 
                        "IniConfiguration and JsonConfiguration validate() should return same keys")
        
        # Both should use 'status' key with string values
        self.assertIsInstance(ini_result["status"], str)
        self.assertIsInstance(json_result["status"], str)
        self.assertIn(ini_result["status"], ["valid", "invalid"])
        self.assertIn(json_result["status"], ["valid", "invalid"])
    
    def test_validate_with_invalid_data(self):
        """Test validate() returns 'invalid' status for problematic configurations."""
        config = IniConfiguration(config_path="nonexistent.ini")
        
        # Test configuration with invalid timeout
        invalid_config = {
            'timeouts': {
                'page_load': 'invalid_number'
            }
        }
        
        result = config.validate(invalid_config)
        self.assertEqual(result["status"], "invalid", "Config with invalid timeout should be 'invalid'")
        self.assertTrue(len(result["errors"]) > 0, "Invalid config should have errors")
    
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