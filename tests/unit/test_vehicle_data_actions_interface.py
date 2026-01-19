"""
Tests for VehicleDataActions protocol interface compliance.
"""
import unittest
from typing import Dict, Any, Optional, List
from compass_core.vehicle_data_actions import VehicleDataActions


class MockVehicleDataActions:
    """Mock implementation of VehicleDataActions protocol for testing."""
    
    def __init__(self):
        self._properties = {
            'VIN': '1HGBH41JXMN109186',
            'Desc': '2021 Honda Accord EX',
            'Make': 'Honda',
            'Model': 'Accord'
        }
        self._current_mva = None
    
    def enter_mva(self, mva: str, clear_existing: bool = True) -> Dict[str, Any]:
        """Mock MVA entry."""
        self._current_mva = mva
        return {'status': 'ok', 'mva': mva}
    
    def get_vehicle_property(self, label: str, timeout: int = 10) -> Optional[str]:
        """Mock property retrieval."""
        return self._properties.get(label)
    
    def get_vehicle_properties(self, labels: List[str], timeout: int = 10) -> Dict[str, str]:
        """Mock multiple property retrieval."""
        return {label: self._properties.get(label, 'N/A') for label in labels}
    
    def verify_mva_echo(self, mva: str, timeout: int = 5) -> bool:
        """Mock MVA echo verification."""
        return self._current_mva is not None and mva in self._current_mva
    
    def wait_for_property_loaded(self, label: str, timeout: int = 10) -> bool:
        """Mock property load wait."""
        return label in self._properties


class TestVehicleDataActionsInterface(unittest.TestCase):
    """Test VehicleDataActions protocol interface and compliance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_actions = MockVehicleDataActions()
    
    def test_protocol_compliance(self):
        """Test that MockVehicleDataActions satisfies VehicleDataActions protocol."""
        self.assertIsInstance(self.mock_actions, VehicleDataActions)
    
    def test_enter_mva_signature(self):
        """Test enter_mva method signature and behavior."""
        result = self.mock_actions.enter_mva("50227203")
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertIn('mva', result)
        self.assertEqual(result['mva'], "50227203")
    
    def test_enter_mva_with_clear(self):
        """Test enter_mva with clear_existing parameter."""
        result = self.mock_actions.enter_mva("12345678", clear_existing=True)
        self.assertEqual(result['status'], 'ok')
        
        result = self.mock_actions.enter_mva("87654321", clear_existing=False)
        self.assertEqual(result['status'], 'ok')
    
    def test_get_vehicle_property_signature(self):
        """Test get_vehicle_property method signature."""
        vin = self.mock_actions.get_vehicle_property("VIN")
        self.assertIsInstance(vin, (str, type(None)))
        
        # Test with timeout parameter
        desc = self.mock_actions.get_vehicle_property("Desc", timeout=15)
        self.assertIsInstance(desc, (str, type(None)))
    
    def test_get_vehicle_property_returns_value(self):
        """Test that get_vehicle_property returns expected values."""
        vin = self.mock_actions.get_vehicle_property("VIN")
        self.assertEqual(vin, '1HGBH41JXMN109186')
        
        desc = self.mock_actions.get_vehicle_property("Desc")
        self.assertEqual(desc, '2021 Honda Accord EX')
    
    def test_get_vehicle_property_missing(self):
        """Test get_vehicle_property with non-existent property."""
        result = self.mock_actions.get_vehicle_property("NonExistent")
        self.assertIsNone(result)
    
    def test_get_vehicle_properties_signature(self):
        """Test get_vehicle_properties method signature."""
        labels = ["VIN", "Desc", "Make"]
        props = self.mock_actions.get_vehicle_properties(labels)
        self.assertIsInstance(props, dict)
        self.assertEqual(len(props), 3)
    
    def test_get_vehicle_properties_returns_dict(self):
        """Test that get_vehicle_properties returns all requested properties."""
        labels = ["VIN", "Desc", "NonExistent"]
        props = self.mock_actions.get_vehicle_properties(labels)
        
        self.assertEqual(props['VIN'], '1HGBH41JXMN109186')
        self.assertEqual(props['Desc'], '2021 Honda Accord EX')
        self.assertEqual(props['NonExistent'], 'N/A')
    
    def test_verify_mva_echo_signature(self):
        """Test verify_mva_echo method signature."""
        self.mock_actions.enter_mva("50227203")
        result = self.mock_actions.verify_mva_echo("50227203")
        self.assertIsInstance(result, bool)
        
        # Test with timeout parameter
        result = self.mock_actions.verify_mva_echo("50227203", timeout=3)
        self.assertIsInstance(result, bool)
    
    def test_verify_mva_echo_behavior(self):
        """Test verify_mva_echo returns True for entered MVA."""
        self.mock_actions.enter_mva("50227203")
        self.assertTrue(self.mock_actions.verify_mva_echo("50227203"))
        self.assertTrue(self.mock_actions.verify_mva_echo("27203"))  # Last digits
    
    def test_wait_for_property_loaded_signature(self):
        """Test wait_for_property_loaded method signature."""
        result = self.mock_actions.wait_for_property_loaded("VIN")
        self.assertIsInstance(result, bool)
        
        # Test with timeout parameter
        result = self.mock_actions.wait_for_property_loaded("VIN", timeout=20)
        self.assertIsInstance(result, bool)
    
    def test_wait_for_property_loaded_behavior(self):
        """Test wait_for_property_loaded returns True for available properties."""
        self.assertTrue(self.mock_actions.wait_for_property_loaded("VIN"))
        self.assertTrue(self.mock_actions.wait_for_property_loaded("Desc"))
        self.assertFalse(self.mock_actions.wait_for_property_loaded("NonExistent"))
    
    def test_protocol_methods_exist(self):
        """Verify all protocol methods exist."""
        required_methods = [
            'enter_mva',
            'get_vehicle_property',
            'get_vehicle_properties',
            'verify_mva_echo',
            'wait_for_property_loaded'
        ]
        
        for method_name in required_methods:
            self.assertTrue(
                hasattr(self.mock_actions, method_name),
                f"Method {method_name} missing from implementation"
            )
            self.assertTrue(
                callable(getattr(self.mock_actions, method_name)),
                f"Method {method_name} is not callable"
            )


if __name__ == '__main__':
    unittest.main()
