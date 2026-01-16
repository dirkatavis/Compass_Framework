"""
Tests for Configuration interface protocol compliance and behavior.
"""
import unittest
from typing import Dict, Any, Optional, Union
from pathlib import Path
from compass_core.configuration import Configuration


class MockConfiguration:
    """Mock implementation of Configuration protocol for testing."""
    
    def __init__(self):
        self._config = {}
    
    def load(self, source: Union[str, Path]) -> Dict[str, Any]:
        """Mock load implementation."""
        return {"loaded_from": str(source)}
    
    def save(self, config: Dict[str, Any], destination: Union[str, Path]) -> bool:
        """Mock save implementation."""
        return True
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Mock get implementation."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Mock set implementation."""
        self._config[key] = value
        return True
    
    def validate(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock validate implementation."""
        return {"status": "valid", "errors": []}


class TestConfigurationInterface(unittest.TestCase):
    """Test Configuration protocol interface and compliance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MockConfiguration()
    
    def test_configuration_protocol_compliance(self):
        """Test that MockConfiguration satisfies Configuration protocol."""
        self.assertIsInstance(self.mock_config, Configuration)
    
    def test_load_method_signature(self):
        """Test load method has correct signature and behavior."""
        # Test with string path
        result = self.mock_config.load("/path/to/config.json")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["loaded_from"], "/path/to/config.json")
        
        # Test with Path object
        path_obj = Path("/path/to/config.json")
        result = self.mock_config.load(path_obj)
        self.assertIsInstance(result, dict)
    
    def test_save_method_signature(self):
        """Test save method has correct signature and behavior."""
        config_data = {"test": "value"}
        
        # Test with string path
        result = self.mock_config.save(config_data, "/path/to/output.json")
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
        
        # Test with Path object
        path_obj = Path("/path/to/output.json")
        result = self.mock_config.save(config_data, path_obj)
        self.assertIsInstance(result, bool)
    
    def test_get_method_signature(self):
        """Test get method has correct signature and behavior."""
        # Set a value first
        self.mock_config.set("test_key", "test_value")
        
        # Test get with existing key
        result = self.mock_config.get("test_key")
        self.assertEqual(result, "test_value")
        
        # Test get with default
        result = self.mock_config.get("nonexistent", "default_value")
        self.assertEqual(result, "default_value")
        
        # Test get without default
        result = self.mock_config.get("nonexistent")
        self.assertIsNone(result)
    
    def test_set_method_signature(self):
        """Test set method has correct signature and behavior."""
        # Test setting various types
        result = self.mock_config.set("string_key", "string_value")
        self.assertIsInstance(result, bool)
        self.assertTrue(result)
        
        result = self.mock_config.set("int_key", 42)
        self.assertTrue(result)
        
        result = self.mock_config.set("dict_key", {"nested": "value"})
        self.assertTrue(result)
    
    def test_validate_method_signature(self):
        """Test validate method has correct signature and behavior."""
        # Test validate with config parameter
        test_config = {"test": "data"}
        result = self.mock_config.validate(test_config)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        
        # Test validate without parameter (validate current config)
        result = self.mock_config.validate()
        self.assertIsInstance(result, dict)
    
    def test_methods_have_correct_signatures(self):
        """Test that methods have expected type signatures."""
        import inspect
        
        # Check load method
        sig = inspect.signature(self.mock_config.load)
        self.assertEqual(len(sig.parameters), 1)
        self.assertIn("source", sig.parameters)
        
        # Check save method  
        sig = inspect.signature(self.mock_config.save)
        self.assertEqual(len(sig.parameters), 2)
        self.assertIn("config", sig.parameters)
        self.assertIn("destination", sig.parameters)
        
        # Check get method
        sig = inspect.signature(self.mock_config.get)
        self.assertEqual(len(sig.parameters), 2)
        self.assertIn("key", sig.parameters)
        self.assertIn("default", sig.parameters)
        
        # Check set method
        sig = inspect.signature(self.mock_config.set)
        self.assertEqual(len(sig.parameters), 2)
        self.assertIn("key", sig.parameters)
        self.assertIn("value", sig.parameters)
        
        # Check validate method
        sig = inspect.signature(self.mock_config.validate)
        self.assertEqual(len(sig.parameters), 1)
        self.assertIn("config", sig.parameters)


if __name__ == '__main__':
    unittest.main()