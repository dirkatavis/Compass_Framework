"""
Tests for Vin2MvaFlow workflow.

Verifies the orchestration logic for batch VIN to MVA lookups, 
including parameter validation, VIN processing, and result writing.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
import os
import tempfile
import sys
from pathlib import Path

# Add src to sys.path for framework access
src_path = str(Path(__file__).resolve().parents[2] / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

class TestVin2MvaFlow(unittest.TestCase):
    """Test Vin2MvaFlow workflow implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            from compass_core.vin_to_mva_flow import Vin2MvaFlow
            self.Vin2MvaFlow = Vin2MvaFlow
        except ImportError:
            self.skipTest("Vin2MvaFlow dependencies not available")
            
        self.mock_driver_manager = Mock()
        self.mock_navigator = Mock()
        self.mock_login_flow = Mock()
        self.mock_vehicle_actions = Mock()
        self.mock_logger = Mock()
        
        self.workflow = self.Vin2MvaFlow(
            driver_manager=self.mock_driver_manager,
            navigator=self.mock_navigator,
            login_flow=self.mock_login_flow,
            vehicle_actions=self.mock_vehicle_actions,
            logger=self.mock_logger
        )
        
    def test_workflow_id(self):
        """Test workflow ID is correct."""
        self.assertEqual(self.workflow.id(), "vin_to_mva_flow")
        
    def test_workflow_plan(self):
        """Test workflow execution plan is defined."""
        plan = self.workflow.plan()
        step_names = [step["name"] for step in plan]
        self.assertIn("authenticate", step_names)
        self.assertIn("load_vins", step_names)
        self.assertIn("process_vins", step_names)
        self.assertIn("write_results", step_names)

    @patch("compass_core.vin_to_mva_flow.read_vin_list")
    @patch("compass_core.vin_to_mva_flow.write_results_csv")
    def test_run_success(self, mock_write, mock_read):
        """Test successful execution of the workflow."""
        # Mock inputs
        mock_read.return_value = ["VIN1", "VIN2"]
        
        # Mock auth success
        self.mock_login_flow.authenticate.return_value = {
            "status": "success",
            "message": "Logged in"
        }
        
        # Mock vehicle actions
        self.mock_vehicle_actions.enter_vin.return_value = {"status": "success"}
        self.mock_vehicle_actions.get_vehicle_property.side_effect = ["MVA1", None] # Success for 1, Timeout for 2
        
        params = {
            "username": "user",
            "password": "pass",
            "app_url": "http://app",
            "input_file": "vins.csv",
            "output_file": "results.csv",
            "timeout": 5
        }
        
        result = self.workflow.run(params)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results_count"], 2)
        
        # Verify vehicle actions were called for each VIN
        self.assertEqual(self.mock_vehicle_actions.enter_vin.call_count, 2)
        
        # Verify results written to CSV
        mock_write.assert_called_once()
        results = mock_write.call_args[0][0]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["vin"], "VIN1")
        self.assertEqual(results[0]["mva"], "MVA1")
        self.assertEqual(results[1]["vin"], "VIN2")
        self.assertEqual(results[1]["mva"], "Not Found")

    def test_run_missing_required_parameters(self):
        """Test run fails with missing required parameters."""
        params = {"username": "user"} # Missing others
        result = self.workflow.run(params)
        self.assertEqual(result["status"], "error")
        self.assertIn("Missing required parameters", result["error"])

if __name__ == "__main__":
    unittest.main()
