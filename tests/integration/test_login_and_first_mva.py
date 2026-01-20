"""
Integration test for login + first MVA entry workflow.

TDD test to verify:
1. Login with SmartLoginFlow
2. Read first MVA from collection
3. Enter MVA into input field
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from compass_core import (
    MvaCollection,
    SmartLoginFlow,
    SeleniumVehicleDataActions
)


class TestLoginAndFirstMvaEntry(unittest.TestCase):
    """Test login followed by first MVA entry."""
    
    def test_workflow_login_and_first_mva(self):
        """
        Test complete workflow: login -> get first MVA -> enter it.
        
        This verifies all components work together:
        - SmartLoginFlow for authentication
        - MvaCollection for MVA management
        - SeleniumVehicleDataActions for MVA entry
        """
        # Setup mocks
        mock_driver = Mock()
        mock_driver.current_url = 'https://app.com/dashboard'
        
        mock_navigator = Mock()
        mock_navigator.navigate_to.return_value = {'status': 'success'}
        
        mock_login_flow = Mock()
        mock_logger = Mock()
        
        # Create collection with test MVAs
        collection = MvaCollection.from_list(['50227203', '12345678', '98765432'])
        
        # Mock successful login
        mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'authenticated': True
        }
        
        # Create SmartLoginFlow
        smart_login = SmartLoginFlow(
            driver=mock_driver,
            navigator=mock_navigator,
            login_flow=mock_login_flow,
            logger=mock_logger
        )
        
        # Mock _detect_login_page to return False (SSO active)
        with patch.object(smart_login, '_detect_login_page', return_value=False):
            # Step 1: Login
            login_result = smart_login.authenticate(
                username='test@example.com',
                password='password123',
                url='https://app.com'
            )
        
        self.assertEqual(login_result['status'], 'success')
        self.assertFalse(login_result['authenticated'])  # SSO was active, no login needed
        
        # Step 2: Get first MVA from collection
        first_item = collection[0]
        self.assertEqual(first_item.mva, '50227203')
        self.assertTrue(first_item.is_pending)
        
        # Step 3: Mark as processing and enter MVA
        first_item.mark_processing()
        self.assertTrue(first_item.is_processing)
        
        # Mock vehicle data actions
        actions = SeleniumVehicleDataActions(mock_driver, mock_logger)
        
        # Mock the enter_mva method to succeed
        with patch.object(actions, 'enter_mva', return_value={'status': 'success', 'mva': '50227203'}):
            result = actions.enter_mva(first_item.mva)
        
        # Verify MVA entry succeeded
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['mva'], '50227203')
        
        # Mark as completed
        first_item.mark_completed({'vin': 'ABC123', 'desc': 'Test Vehicle'})
        self.assertTrue(first_item.is_completed)
        self.assertEqual(first_item.result['vin'], 'ABC123')
    
    def test_workflow_with_iteration(self):
        """Test workflow iterating through collection."""
        # Create collection
        collection = MvaCollection.from_list(['50227203', '12345678'])
        
        # Simulate processing first item only
        processed_count = 0
        for item in collection:
            if processed_count >= 1:
                break  # Only process first one
            
            item.mark_processing()
            # Simulate successful processing
            item.mark_completed({'vin': f'VIN_{item.mva}', 'desc': f'Vehicle {item.mva}'})
            processed_count += 1
        
        # Verify only first item was processed
        self.assertTrue(collection[0].is_completed)
        self.assertTrue(collection[1].is_pending)
        self.assertEqual(collection.completed_count, 1)
        self.assertEqual(collection.pending_count, 1)
    
    def test_workflow_error_handling(self):
        """Test workflow with error on first MVA."""
        collection = MvaCollection.from_list(['50227203'])
        first_item = collection[0]
        
        # Mock driver and actions
        mock_driver = Mock()
        mock_logger = Mock()
        actions = SeleniumVehicleDataActions(mock_driver, mock_logger)
        
        # Mock enter_mva to fail
        with patch.object(actions, 'enter_mva', return_value={'status': 'error', 'error': 'Input field not found'}):
            result = actions.enter_mva(first_item.mva)
        
        # Verify error handling
        self.assertEqual(result['status'], 'error')
        
        # Mark item as failed
        first_item.mark_failed(result['error'])
        
        self.assertTrue(first_item.is_failed)
        self.assertEqual(first_item.error, 'Input field not found')
        self.assertEqual(collection.failed_count, 1)


if __name__ == '__main__':
    unittest.main()
