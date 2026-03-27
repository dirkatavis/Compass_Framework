"""
Vin2Mva Flow - Batch VIN to MVA processing workflow.

Orchestrates the complete VIN to MVA lookup process:
1. Authenticate with LoginFlow
2. Read VIN list from CSV
3. Iterate through VINs, entering them into the search box
4. Extract MVA from the resulting vehicle properties
5. Handle "Not Found" cases based on 20s timeout
6. Write results to output CSV (VIN, MVA)

Implements the Workflow protocol for integration with Compass Framework.
"""
from typing import Dict, Any, List, Optional
import logging
import time
import os

from compass_core.workflow import Workflow
from compass_core.login_flow import LoginFlow
from compass_core.vehicle_data_actions import VehicleDataActions
from compass_core.driver_manager import DriverManager
from compass_core.navigation import Navigator
from compass_core.csv_utils import read_vin_list, write_results_csv


class Vin2MvaFlow:
    """
    Workflow for batch vehicle MVA lookups via VIN.
    
    This workflow implements the Vin2Mva tool requirements:
    - Reads VINs from CSV
    - Enters VIN into search
    - Waits up to 20s for vehicle details
    - Extracts MVA from page properties
    - Writes (VIN, MVA) to output CSV
    """
    
    def __init__(
        self,
        driver_manager: DriverManager,
        navigator: Navigator,
        login_flow: LoginFlow,
        vehicle_actions: VehicleDataActions,
        logger: logging.Logger = None
    ):
        """
        Initialize Vin2Mva workflow.
        
        Args:
            driver_manager: Driver management protocol
            navigator: Navigation protocol
            login_flow: Authentication protocol
            vehicle_actions: Vehicle data operations protocol
            logger: Optional logger instance
        """
        self.driver_manager = driver_manager
        self.navigator = navigator
        self.login_flow = login_flow
        self.vehicle_actions = vehicle_actions
        self.logger = logger or logging.getLogger(__name__)
    
    def id(self) -> str:
        """Return workflow identifier."""
        return "vin_to_mva_flow"
    
    def plan(self) -> List[Dict[str, str]]:
        """
        Return workflow execution plan.
        
        Returns:
            List of step dictionaries with 'name' and 'description'
        """
        return [
            {"name": "authenticate", "description": "Login to Compass application"},
            {"name": "load_vins", "description": "Read VIN list from CSV"},
            {"name": "process_vins", "description": "Iterate VINs and extract MVAs"},
            {"name": "write_results", "description": "Write results (VIN, MVA) to output CSV"}
        ]
    
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Vin2Mva workflow.
        
        Args:
            params: Workflow parameters:
                - input_file: str (CSV path)
                - output_file: str (CSV output path)
                - username: str
                - password: str
                - app_url: str
                - login_id: str (optional)
                - timeout: int (optional, default: 20)
        
        Returns:
            Dict with workflow result.
        """
        self.logger.info("=" * 60)
        self.logger.info("Vin2Mva Flow - Starting")
        self.logger.info("=" * 60)
        
        try:
            # Extract parameters
            username = params.get('username')
            password = params.get('password')
            app_url = params.get('app_url')
            input_file = params.get('input_file')
            output_file = params.get('output_file')
            timeout = params.get('timeout', 20)
            
            # Validate required parameters
            if not all([username, password, app_url, input_file, output_file]):
                missing = [k for k in ['username', 'password', 'app_url', 'input_file', 'output_file'] if not params.get(k)]
                error_msg = f"Missing required parameters: {', '.join(missing)}"
                self.logger.error(f"[WORKFLOW] {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "summary": "Workflow validation failed"
                }
            
            # STEP 1: Authenticate
            self.logger.info("STEP 1: Authentication")
            auth_result = self.login_flow.authenticate(
                username=username,
                password=password,
                url=app_url,
                login_id=params.get('login_id'),
                timeout=timeout
            )
            
            if auth_result.get('status') != 'success':
                self.logger.error(f"[WORKFLOW] Authentication failed: {auth_result.get('error')}")
                return {
                    "status": "error",
                    "error": auth_result.get('error', 'Authentication failed'),
                    "summary": "Login failed"
                }
            
            self.logger.info(f"[WORKFLOW] {auth_result.get('message')}")
            
            # STEP 2: Load VINs
            self.logger.info("STEP 2: Load VINs")
            try:
                vins = read_vin_list(input_file)
                self.logger.info(f"[WORKFLOW] Loaded {len(vins)} VINs from: {input_file}")
            except Exception as e:
                self.logger.error(f"[WORKFLOW] Failed to read VIN list: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "summary": "File read failed"
                }
            
            # STEP 3: Process VINs
            self.logger.info("STEP 3: Process VINs")
            results = []
            
            for i, vin in enumerate(vins):
                self.logger.info(f"[WORKFLOW] [{i+1}/{len(vins)}] Processing VIN: {vin}")
                
                # Enter VIN
                entry_result = self.vehicle_actions.enter_vin(vin)
                
                if entry_result.get('status') == 'success':
                    # Extract MVA property
                    # Use provided timeout (default 20s) for detection
                    mva = self.vehicle_actions.get_vehicle_property("MVA", timeout=timeout)
                    
                    if mva:
                        self.logger.info(f"[WORKFLOW] Found MVA for {vin}: {mva}")
                        results.append({"vin": vin, "mva": mva, "status": "success"})
                    else:
                        self.logger.warning(f"[WORKFLOW] No MVA found for {vin} within {timeout}s - marking as Not Found")
                        results.append({"vin": vin, "mva": "Not Found", "status": "failure", "error": "Timeout - No data displayed"})
                else:
                    self.logger.error(f"[WORKFLOW] Failed to enter VIN {vin}: {entry_result.get('error')}")
                    results.append({"vin": vin, "mva": "Error", "status": "error", "error": entry_result.get('error')})
            
            # STEP 4: Write Results
            self.logger.info("STEP 4: Write Results")
            try:
                write_results_csv(results, output_file)
                self.logger.info(f"[WORKFLOW] Results written to: {output_file}")
            except Exception as e:
                self.logger.error(f"[WORKFLOW] Failed to write results: {e}")
                return {
                    "status": "partial_success",
                    "error": f"Results processed but writing failed: {str(e)}",
                    "results_count": len(results),
                    "summary": "Results write failed"
                }
            
            self.logger.info("=" * 60)
            self.logger.info("Vin2Mva Flow - Completed Successfully")
            self.logger.info("=" * 60)
            
            return {
                "status": "success",
                "summary": f"Processed {len(vins)} VINs, {len([r for r in results if r['status'] == 'success'])} found",
                "results_count": len(results),
                "output_file": output_file
            }
            
        except Exception as e:
            self.logger.critical(f"[WORKFLOW] Critical failure in Vin2MvaFlow: {e}")
            import traceback
            self.logger.critical(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "summary": "Critical workflow failure"
            }
