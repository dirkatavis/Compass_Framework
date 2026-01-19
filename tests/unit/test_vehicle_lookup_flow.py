"""
Tests for VehicleLookupFlow workflow.

This module validates the orchestration logic for batch vehicle data lookup,
including parameter validation, MVA processing, error handling, and CSV operations.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch, call
import os
import tempfile


class TestVehicleLookupFlow(unittest.TestCase):
    """Test VehicleLookupFlow workflow implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to handle dependencies
        try:
            from compass_core.vehicle_lookup_flow import VehicleLookupFlow
            self.VehicleLookupFlow = VehicleLookupFlow
        except ImportError:
            self.skipTest("VehicleLookupFlow dependencies not available")
        
        # Create mocks for all dependencies
        self.mock_driver_manager = Mock()
        self.mock_navigator = Mock()
        self.mock_login_flow = Mock()
        self.mock_vehicle_actions = Mock()
        self.mock_logger = Mock()
        
        # Create workflow instance
        self.workflow = self.VehicleLookupFlow(
            driver_manager=self.mock_driver_manager,
            navigator=self.mock_navigator,
            login_flow=self.mock_login_flow,
            vehicle_actions=self.mock_vehicle_actions,
            logger=self.mock_logger
        )
    
    def test_initialization(self):
        """Test proper initialization with dependencies."""
        self.assertEqual(self.workflow.driver_manager, self.mock_driver_manager)
        self.assertEqual(self.workflow.navigator, self.mock_navigator)
        self.assertEqual(self.workflow.login_flow, self.mock_login_flow)
        self.assertEqual(self.workflow.vehicle_actions, self.mock_vehicle_actions)
        self.assertEqual(self.workflow.logger, self.mock_logger)
    
    def test_workflow_id(self):
        """Test workflow ID is correct."""
        self.assertEqual(self.workflow.id(), "vehicle_lookup_flow")
    
    def test_workflow_plan(self):
        """Test workflow execution plan is defined."""
        plan = self.workflow.plan()
        
        # Should return list of steps
        self.assertIsInstance(plan, list)
        self.assertGreater(len(plan), 0)
        
        # Each step should have name and description
        for step in plan:
            self.assertIn('name', step)
            self.assertIn('description', step)
            self.assertIsInstance(step['name'], str)
            self.assertIsInstance(step['description'], str)
        
        # Should have expected steps
        step_names = [step['name'] for step in plan]
        self.assertIn('authenticate', step_names)
        self.assertIn('load_mvas', step_names)
        self.assertIn('process_mvas', step_names)
        self.assertIn('write_results', step_names)
    
    def test_run_missing_required_parameters(self):
        """Test run fails with missing required parameters."""
        # Missing username
        params = {
            'password': 'pass',
            'app_url': 'https://app.example.com',
            'output_file': 'output.csv'
        }
        result = self.workflow.run(params)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertIn('username', result['error'])
    
    def test_run_authentication_failure(self):
        """Test run fails when authentication fails."""
        # Mock authentication failure
        self.mock_login_flow.authenticate.return_value = {
            'status': 'error',
            'error': 'Invalid credentials'
        }
        
        params = {
            'username': 'test@example.com',
            'password': 'password',
            'app_url': 'https://app.example.com',
            'output_file': 'output.csv',
            'mva_list': ['12345678']
        }
        
        result = self.workflow.run(params)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.mock_login_flow.authenticate.assert_called_once()
    
    def test_run_with_mva_list(self):
        """Test run with MVA list provided directly."""
        # Mock successful authentication
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        
        # Mock successful MVA processing
        self.mock_vehicle_actions.enter_mva.return_value = {'status': 'success'}
        self.mock_vehicle_actions.verify_mva_echo.return_value = True
        self.mock_vehicle_actions.wait_for_property_loaded.return_value = True
        self.mock_vehicle_actions.get_vehicle_property.side_effect = lambda prop, timeout: {
            'VIN': '1HGBH41JXMN109186',
            'Desc': '2021 Honda Accord'
        }.get(prop, 'N/A')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            params = {
                'username': 'test@example.com',
                'password': 'password',
                'app_url': 'https://app.example.com',
                'output_file': output_file,
                'mva_list': ['50227203', '12345678'],
                'properties': ['VIN', 'Desc']
            }
            
            result = self.workflow.run(params)
            
            # Should succeed
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['results_count'], 2)
            self.assertEqual(result['success_count'], 2)
            
            # Should have called enter_mva for each MVA
            self.assertEqual(self.mock_vehicle_actions.enter_mva.call_count, 2)
            
            # Output file should exist
            self.assertTrue(os.path.exists(output_file))
            
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    @patch('compass_core.vehicle_lookup_flow.read_mva_list')
    def test_run_with_input_file(self, mock_read_mva):
        """Test run with input CSV file."""
        # Mock CSV reading
        mock_read_mva.return_value = ['50227203', '12345678']
        
        # Mock successful authentication
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        
        # Mock successful MVA processing
        self.mock_vehicle_actions.enter_mva.return_value = {'status': 'success'}
        self.mock_vehicle_actions.verify_mva_echo.return_value = True
        self.mock_vehicle_actions.wait_for_property_loaded.return_value = True
        self.mock_vehicle_actions.get_vehicle_property.return_value = 'Test Value'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            params = {
                'username': 'test@example.com',
                'password': 'password',
                'app_url': 'https://app.example.com',
                'input_file': 'input.csv',
                'output_file': output_file
            }
            
            result = self.workflow.run(params)
            
            # Should succeed
            self.assertEqual(result['status'], 'success')
            
            # Should have read from CSV
            mock_read_mva.assert_called_once_with('input.csv')
            
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    @patch('compass_core.vehicle_lookup_flow.read_mva_list')
    def test_run_csv_read_failure(self, mock_read_mva):
        """Test run fails when CSV reading fails."""
        # Mock CSV reading failure
        mock_read_mva.side_effect = FileNotFoundError("File not found")
        
        # Mock successful authentication
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        
        params = {
            'username': 'test@example.com',
            'password': 'password',
            'app_url': 'https://app.example.com',
            'input_file': 'nonexistent.csv',
            'output_file': 'output.csv'
        }
        
        result = self.workflow.run(params)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
    
    def test_run_no_mva_source(self):
        """Test run fails when no MVA source provided."""
        # Mock successful authentication
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        
        params = {
            'username': 'test@example.com',
            'password': 'password',
            'app_url': 'https://app.example.com',
            'output_file': 'output.csv'
            # No mva_list or input_file
        }
        
        result = self.workflow.run(params)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('No MVA source', result['summary'])
    
    def test_run_mva_entry_failure(self):
        """Test run handles MVA entry failures gracefully."""
        # Mock successful authentication
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        
        # Mock MVA entry failure
        self.mock_vehicle_actions.enter_mva.return_value = {
            'status': 'error',
            'error': 'Input field not found'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            params = {
                'username': 'test@example.com',
                'password': 'password',
                'app_url': 'https://app.example.com',
                'output_file': output_file,
                'mva_list': ['50227203']
            }
            
            result = self.workflow.run(params)
            
            # Should still succeed (workflow completes)
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['results_count'], 1)
            self.assertEqual(result['success_count'], 0)  # No successful lookups
            
            # Output file should exist with error row
            self.assertTrue(os.path.exists(output_file))
            
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def test_run_property_timeout(self):
        """Test run handles property loading timeouts."""
        # Mock successful authentication and MVA entry
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        self.mock_vehicle_actions.enter_mva.return_value = {'status': 'success'}
        self.mock_vehicle_actions.verify_mva_echo.return_value = True
        
        # Mock property timeout (returns False)
        self.mock_vehicle_actions.wait_for_property_loaded.return_value = False
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            params = {
                'username': 'test@example.com',
                'password': 'password',
                'app_url': 'https://app.example.com',
                'output_file': output_file,
                'mva_list': ['50227203'],
                'properties': ['VIN']
            }
            
            result = self.workflow.run(params)
            
            # Should succeed with N/A value
            self.assertEqual(result['status'], 'success')
            
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    @patch('compass_core.vehicle_lookup_flow.write_results_csv')
    def test_run_csv_write_failure(self, mock_write_csv):
        """Test run fails when CSV writing fails."""
        # Mock successful authentication and processing
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        self.mock_vehicle_actions.enter_mva.return_value = {'status': 'success'}
        self.mock_vehicle_actions.verify_mva_echo.return_value = True
        self.mock_vehicle_actions.wait_for_property_loaded.return_value = True
        self.mock_vehicle_actions.get_vehicle_property.return_value = 'Test'
        
        # Mock CSV write failure
        mock_write_csv.side_effect = IOError("Permission denied")
        
        params = {
            'username': 'test@example.com',
            'password': 'password',
            'app_url': 'https://app.example.com',
            'output_file': '/invalid/path/output.csv',
            'mva_list': ['50227203']
        }
        
        result = self.workflow.run(params)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
    
    def test_run_custom_timeout(self):
        """Test run respects custom timeout parameter."""
        # Mock successful flow
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        self.mock_vehicle_actions.enter_mva.return_value = {'status': 'success'}
        self.mock_vehicle_actions.verify_mva_echo.return_value = True
        self.mock_vehicle_actions.wait_for_property_loaded.return_value = True
        self.mock_vehicle_actions.get_vehicle_property.return_value = 'Test'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            params = {
                'username': 'test@example.com',
                'password': 'password',
                'app_url': 'https://app.example.com',
                'output_file': output_file,
                'mva_list': ['50227203'],
                'timeout': 20  # Custom timeout
            }
            
            result = self.workflow.run(params)
            
            self.assertEqual(result['status'], 'success')
            
            # Verify authenticate was called with timeout
            auth_kwargs = self.mock_login_flow.authenticate.call_args[1]
            self.assertEqual(auth_kwargs.get('timeout'), 20)
            
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def test_run_passes_login_id(self):
        """Test run passes login_id to authenticate."""
        # Mock successful flow
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        self.mock_vehicle_actions.enter_mva.return_value = {'status': 'success'}
        self.mock_vehicle_actions.verify_mva_echo.return_value = True
        self.mock_vehicle_actions.wait_for_property_loaded.return_value = True
        self.mock_vehicle_actions.get_vehicle_property.return_value = 'Test'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            params = {
                'username': 'test@example.com',
                'password': 'password',
                'app_url': 'https://app.example.com',
                'output_file': output_file,
                'mva_list': ['50227203'],
                'login_id': 'ABC123'
            }
            
            result = self.workflow.run(params)
            
            self.assertEqual(result['status'], 'success')
            
            # Verify authenticate was called with login_id
            auth_kwargs = self.mock_login_flow.authenticate.call_args[1]
            self.assertEqual(auth_kwargs.get('login_id'), 'ABC123')
            
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
    
    def test_run_exception_handling(self):
        """Test run handles unexpected exceptions gracefully."""
        # Mock authentication to raise unexpected exception
        self.mock_login_flow.authenticate.side_effect = RuntimeError("Unexpected error")
        
        params = {
            'username': 'test@example.com',
            'password': 'password',
            'app_url': 'https://app.example.com',
            'output_file': 'output.csv',
            'mva_list': ['50227203']
        }
        
        result = self.workflow.run(params)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
        self.assertIn('Unexpected error', result['error'])
    
    def test_run_multiple_mvas_mixed_results(self):
        """Test run with multiple MVAs having mixed success/failure."""
        # Mock successful authentication
        self.mock_login_flow.authenticate.return_value = {
            'status': 'success',
            'message': 'Authenticated'
        }
        
        # Mock mixed results for enter_mva
        self.mock_vehicle_actions.enter_mva.side_effect = [
            {'status': 'success'},  # MVA 1 succeeds
            {'status': 'error', 'error': 'Field not found'},  # MVA 2 fails
            {'status': 'success'}   # MVA 3 succeeds
        ]
        
        self.mock_vehicle_actions.verify_mva_echo.return_value = True
        self.mock_vehicle_actions.wait_for_property_loaded.return_value = True
        self.mock_vehicle_actions.get_vehicle_property.return_value = 'Test'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_file = f.name
        
        try:
            params = {
                'username': 'test@example.com',
                'password': 'password',
                'app_url': 'https://app.example.com',
                'output_file': output_file,
                'mva_list': ['50227203', '12345678', '98765432']
            }
            
            result = self.workflow.run(params)
            
            # Should succeed overall
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['results_count'], 3)
            self.assertEqual(result['success_count'], 2)  # 2 successful
            
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)


if __name__ == '__main__':
    unittest.main()
