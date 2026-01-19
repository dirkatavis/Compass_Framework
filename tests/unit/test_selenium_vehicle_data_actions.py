"""
Tests for SeleniumVehicleDataActions implementation.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from compass_core.vehicle_data_actions import VehicleDataActions


class TestSeleniumVehicleDataActions(unittest.TestCase):
    """Test SeleniumVehicleDataActions implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to allow test to be skipped if selenium not available
        try:
            from compass_core.selenium_vehicle_data_actions import SeleniumVehicleDataActions
            self.SeleniumVehicleDataActions = SeleniumVehicleDataActions
            self.selenium_available = True
        except ImportError:
            self.selenium_available = False
            self.skipTest("Selenium not available")
        
        self.mock_driver = Mock()
        self.mock_driver.find_elements = Mock(return_value=[])
        self.actions = self.SeleniumVehicleDataActions(self.mock_driver, timeout=5)
    
    def test_protocol_compliance(self):
        """Test that SeleniumVehicleDataActions satisfies VehicleDataActions protocol."""
        self.assertIsInstance(self.actions, VehicleDataActions)
    
    def test_initialization(self):
        """Test proper initialization."""
        self.assertEqual(self.actions.driver, self.mock_driver)
        self.assertEqual(self.actions.timeout, 5)
        self.assertIsNotNone(self.actions.wait)
    
    def test_enter_mva_input_not_found(self):
        """Test enter_mva when input field is not found."""
        self.mock_driver.find_elements = Mock(return_value=[])
        
        result = self.actions.enter_mva("50227203")
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertEqual(result['mva'], "50227203")
    
    def test_enter_mva_success(self):
        """Test successful MVA entry."""
        # Create mock input element
        mock_input = Mock()
        mock_input.is_displayed = Mock(return_value=True)
        mock_input.is_enabled = Mock(return_value=True)
        mock_input.get_attribute = Mock(return_value="")
        mock_input.send_keys = Mock()
        mock_input.clear = Mock()
        
        self.mock_driver.find_elements = Mock(return_value=[mock_input])
        
        result = self.actions.enter_mva("50227203")
        
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['mva'], "50227203")
        mock_input.send_keys.assert_called()
    
    def test_get_vehicle_property_timeout(self):
        """Test get_vehicle_property when property not found."""
        from selenium.common.exceptions import TimeoutException
        
        with patch('compass_core.selenium_vehicle_data_actions.WebDriverWait') as mock_wait_class:
            mock_wait_instance = Mock()
            mock_wait_instance.until.side_effect = TimeoutException("Element not found")
            mock_wait_class.return_value = mock_wait_instance
            
            result = self.actions.get_vehicle_property("VIN", timeout=1)
            
            self.assertIsNone(result)
    
    def test_get_vehicle_properties_multiple(self):
        """Test getting multiple properties."""
        with patch.object(self.actions, '_get_property_by_label') as mock_get:
            mock_get.side_effect = lambda label, timeout: {
                'VIN': '1HGBH41JXMN109186',
                'Desc': '2021 Honda Accord'
            }.get(label)
            
            result = self.actions.get_vehicle_properties(['VIN', 'Desc', 'Missing'])
            
            self.assertEqual(result['VIN'], '1HGBH41JXMN109186')
            self.assertEqual(result['Desc'], '2021 Honda Accord')
            self.assertEqual(result['Missing'], 'N/A')
    
    def test_verify_mva_echo_found(self):
        """Test MVA echo verification when found."""
        with patch.object(self.actions, '_find_mva_echo') as mock_find:
            mock_find.return_value = True
            
            result = self.actions.verify_mva_echo("50227203")
            
            self.assertTrue(result)
            mock_find.assert_called_once()
    
    def test_verify_mva_echo_not_found(self):
        """Test MVA echo verification when not found."""
        with patch.object(self.actions, '_find_mva_echo') as mock_find:
            mock_find.return_value = False
            
            result = self.actions.verify_mva_echo("50227203")
            
            self.assertFalse(result)
    
    def test_wait_for_property_loaded_success(self):
        """Test waiting for property to load successfully."""
        with patch.object(self.actions, '_get_property_by_label') as mock_get:
            mock_get.return_value = "Some Value"
            
            result = self.actions.wait_for_property_loaded("VIN", timeout=2)
            
            self.assertTrue(result)
    
    def test_wait_for_property_loaded_timeout(self):
        """Test waiting for property times out."""
        with patch.object(self.actions, '_get_property_by_label') as mock_get:
            mock_get.return_value = None
            
            result = self.actions.wait_for_property_loaded("VIN", timeout=1)
            
            self.assertFalse(result)
    
    def test_has_required_methods(self):
        """Verify all required protocol methods are implemented."""
        required_methods = [
            'enter_mva',
            'get_vehicle_property',
            'get_vehicle_properties',
            'verify_mva_echo',
            'wait_for_property_loaded'
        ]
        
        for method_name in required_methods:
            self.assertTrue(hasattr(self.actions, method_name))
            self.assertTrue(callable(getattr(self.actions, method_name)))


if __name__ == '__main__':
    unittest.main()
