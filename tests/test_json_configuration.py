"""
Tests for JsonConfiguration implementation.
"""
import unittest
import tempfile
import json
from pathlib import Path
from compass_core.json_configuration import JsonConfiguration
from compass_core.configuration import Configuration


class TestJsonConfiguration(unittest.TestCase):
    """Test JsonConfiguration implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = JsonConfiguration()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_configuration_protocol_compliance(self):
        """Test that JsonConfiguration implements Configuration protocol."""
        self.assertIsInstance(self.config, Configuration)
    
    def test_json_configuration_initialization(self):
        """Test JsonConfiguration initialization."""
        config = JsonConfiguration()
        self.assertEqual(config.get_all(), {})
    
    def test_load_valid_json_file(self):
        """Test loading a valid JSON configuration file."""
        # Create test JSON file
        test_data = {
            "database": {"host": "localhost", "port": 5432},
            "api_key": "test-key",
            "debug": True
        }
        
        test_file = self.temp_path / "test_config.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Test loading
        result = self.config.load(test_file)
        self.assertEqual(result, test_data)
        self.assertEqual(self.config.get_all(), test_data)
    
    def test_load_with_string_path(self):
        """Test loading with string path."""
        test_data = {"test": "value"}
        test_file = self.temp_path / "string_path_test.json"
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        result = self.config.load(str(test_file))
        self.assertEqual(result, test_data)
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent file raises FileNotFoundError."""
        nonexistent_file = self.temp_path / "nonexistent.json"
        
        with self.assertRaises(FileNotFoundError):
            self.config.load(nonexistent_file)
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON raises JSONDecodeError."""
        invalid_json_file = self.temp_path / "invalid.json"
        
        with open(invalid_json_file, 'w') as f:
            f.write("{invalid json content")
        
        with self.assertRaises(json.JSONDecodeError):
            self.config.load(invalid_json_file)
    
    def test_save_configuration(self):
        """Test saving configuration to JSON file."""
        test_data = {
            "application": {"name": "TestApp", "version": "1.0"},
            "settings": {"auto_save": True}
        }
        
        output_file = self.temp_path / "output_config.json"
        
        # Test saving
        result = self.config.save(test_data, output_file)
        self.assertTrue(result)
        self.assertTrue(output_file.exists())
        
        # Verify saved content
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, test_data)
    
    def test_save_with_string_path(self):
        """Test saving with string destination path."""
        test_data = {"test": "save"}
        output_file = self.temp_path / "string_save_test.json"
        
        result = self.config.save(test_data, str(output_file))
        self.assertTrue(result)
        self.assertTrue(output_file.exists())
    
    def test_save_creates_parent_directories(self):
        """Test that save creates parent directories if they don't exist."""
        test_data = {"nested": "directory"}
        nested_file = self.temp_path / "nested" / "dirs" / "config.json"
        
        result = self.config.save(test_data, nested_file)
        self.assertTrue(result)
        self.assertTrue(nested_file.exists())
    
    def test_get_simple_key(self):
        """Test getting values with simple keys."""
        self.config._config = {
            "simple_key": "simple_value",
            "number": 42,
            "boolean": True
        }
        
        self.assertEqual(self.config.get("simple_key"), "simple_value")
        self.assertEqual(self.config.get("number"), 42)
        self.assertEqual(self.config.get("boolean"), True)
    
    def test_get_nested_key_dot_notation(self):
        """Test getting values with dot notation for nested keys."""
        self.config._config = {
            "database": {
                "host": "localhost",
                "credentials": {
                    "username": "admin"
                }
            }
        }
        
        self.assertEqual(self.config.get("database.host"), "localhost")
        self.assertEqual(self.config.get("database.credentials.username"), "admin")
    
    def test_get_with_default_value(self):
        """Test getting non-existent keys returns default value."""
        self.config._config = {"existing": "value"}
        
        self.assertEqual(self.config.get("nonexistent", "default"), "default")
        self.assertIsNone(self.config.get("nonexistent"))
        
        # Test nested default
        self.assertEqual(self.config.get("missing.nested.key", "nested_default"), "nested_default")
    
    def test_set_simple_key(self):
        """Test setting values with simple keys."""
        result = self.config.set("test_key", "test_value")
        self.assertTrue(result)
        self.assertEqual(self.config.get("test_key"), "test_value")
        
        # Test different data types
        self.config.set("number", 123)
        self.config.set("boolean", False)
        self.config.set("list", [1, 2, 3])
        
        self.assertEqual(self.config.get("number"), 123)
        self.assertEqual(self.config.get("boolean"), False)
        self.assertEqual(self.config.get("list"), [1, 2, 3])
    
    def test_set_nested_key_dot_notation(self):
        """Test setting values with dot notation creates nested structure."""
        result = self.config.set("database.host", "localhost")
        self.assertTrue(result)
        self.assertEqual(self.config.get("database.host"), "localhost")
        
        # Test deeper nesting
        self.config.set("app.settings.auto_save", True)
        self.assertEqual(self.config.get("app.settings.auto_save"), True)
        
        # Test overwriting existing structure
        self.config.set("database.port", 5432)
        self.assertEqual(self.config.get("database.port"), 5432)
        self.assertEqual(self.config.get("database.host"), "localhost")  # Should preserve existing
    
    def test_validate_valid_configuration(self):
        """Test validation of valid configuration."""
        valid_config = {
            "application": "TestApp",
            "settings": {"debug": False},
            "numbers": [1, 2, 3]
        }
        
        result = self.config.validate(valid_config)
        
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["errors"], [])
        # May have warnings (e.g., for sensitive keys)
        self.assertIsInstance(result["warnings"], list)
    
    def test_validate_current_configuration(self):
        """Test validation of current configuration when no parameter given."""
        self.config._config = {"test": "data"}
        
        result = self.config.validate()
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["errors"], [])
    
    def test_validate_empty_configuration_warning(self):
        """Test validation warns about empty configuration."""
        result = self.config.validate({})
        
        self.assertEqual(result["status"], "valid")  # Empty is valid, but warned
        self.assertEqual(result["errors"], [])
        self.assertIn("Configuration is empty", result["warnings"])
    
    def test_validate_sensitive_data_warning(self):
        """Test validation warns about potentially sensitive data."""
        sensitive_config = {
            "api_key": "secret123",
            "password": "mypassword",
            "database_token": "token123"
        }
        
        result = self.config.validate(sensitive_config)
        
        self.assertEqual(result["status"], "valid")  # Sensitive data is valid, but warned
        self.assertEqual(result["errors"], [])
        
        # Should warn about sensitive keys
        warning_text = " ".join(result["warnings"])
        self.assertIn("api_key", warning_text)
        self.assertIn("password", warning_text)
        self.assertIn("database_token", warning_text)
    
    def test_validate_invalid_configuration(self):
        """Test validation of invalid configuration."""
        # Non-dict configuration
        result = self.config.validate("not a dict")
        
        self.assertEqual(result["status"], "invalid")
        self.assertGreater(len(result["errors"]), 0)
        self.assertIn("dictionary", result["errors"][0])
    
    def test_get_all_returns_copy_of_configuration(self):
        """Test get_all returns a copy of current configuration."""
        test_data = {
            "database": {"host": "localhost", "port": 5432},
            "api": {"timeout": 30}
        }
        
        # Set up test configuration
        for key, value in test_data.items():
            self.config._config[key] = value
        
        # Get all configuration
        result = self.config.get_all()
        
        # Should equal the test data
        self.assertEqual(result, test_data)
        
        # Should be a copy, not the same object
        self.assertIsNot(result, self.config._config)
        
        # Modifying returned dict should not affect internal config
        result["new_key"] = "new_value"
        self.assertNotIn("new_key", self.config._config)
    
    def test_get_all_empty_configuration(self):
        """Test get_all with empty configuration."""
        result = self.config.get_all()
        self.assertEqual(result, {})
        self.assertIsInstance(result, dict)
    
    def test_sensitive_key_patterns_constant(self):
        """Test that sensitive key patterns are accessible as class constant."""
        # Verify constant exists and has expected content
        self.assertTrue(hasattr(JsonConfiguration, 'SENSITIVE_KEY_PATTERNS'))
        self.assertIsInstance(JsonConfiguration.SENSITIVE_KEY_PATTERNS, list)
        self.assertIn('password', JsonConfiguration.SENSITIVE_KEY_PATTERNS)
        self.assertIn('api_key', JsonConfiguration.SENSITIVE_KEY_PATTERNS)
        
        # Verify it can be accessed via instance
        self.assertEqual(self.config.SENSITIVE_KEY_PATTERNS, JsonConfiguration.SENSITIVE_KEY_PATTERNS)


if __name__ == '__main__':
    unittest.main()