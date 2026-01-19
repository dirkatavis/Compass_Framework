"""
Vehicle Lookup Flow - Batch MVA processing workflow.

Orchestrates the complete vehicle data lookup process:
1. Authenticate with LoginFlow
2. Read MVA list from CSV
3. Iterate through MVAs, retrieving properties
4. Write results to output CSV

Implements the Workflow protocol for integration with Compass Framework.
"""
from typing import Dict, Any, List
import logging
import os

from compass_core.workflow import Workflow
from compass_core.login_flow import LoginFlow
from compass_core.vehicle_data_actions import VehicleDataActions
from compass_core.driver_manager import DriverManager
from compass_core.navigation import Navigator
from compass_core.csv_utils import read_mva_list, write_results_csv


class VehicleLookupFlow:
    """
    Workflow for batch vehicle property lookups via MVA.
    
    This workflow implements the complete GlassDataParser functionality
    using Compass Framework protocols.
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
        Initialize vehicle lookup workflow.
        
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
        return "vehicle_lookup_flow"
    
    def plan(self) -> List[Dict[str, str]]:
        """
        Return workflow execution plan.
        
        Returns:
            List of step dictionaries with 'name' and 'description'
        """
        return [
            {"name": "authenticate", "description": "Login to Compass application"},
            {"name": "load_mvas", "description": "Read MVA list from CSV or parameters"},
            {"name": "process_mvas", "description": "Iterate MVAs and retrieve properties"},
            {"name": "write_results", "description": "Write results to output CSV"}
        ]
    
    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute vehicle lookup workflow.
        
        Args:
            params: Workflow parameters:
                - input_file: str (CSV path) OR mva_list: List[str]
                - output_file: str (CSV output path)
                - username: str
                - password: str
                - login_url: str
                - login_id: str (optional)
                - verify_domain: str (optional - for login verification)
                - properties: List[str] (optional, default: ["VIN", "Desc"])
                - timeout: int (optional, default: 12)
        
        Returns:
            Dict with workflow result:
            {
                "status": "success" | "error",
                "summary": str,
                "results_count": int,
                "output_file": str,
                "error": str (if status="error")
            }
        """
        self.logger.info("=" * 60)
        self.logger.info("Vehicle Lookup Flow - Starting")
        self.logger.info("=" * 60)
        
        try:
            # Extract parameters
            username = params.get('username')
            password = params.get('password')
            login_url = params.get('login_url')
            output_file = params.get('output_file')
            properties = params.get('properties', ['VIN', 'Desc'])
            timeout = params.get('timeout', 12)
            
            # Validate required parameters
            if not all([username, password, login_url, output_file]):
                missing = [k for k in ['username', 'password', 'login_url', 'output_file'] if not params.get(k)]
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
                login_url=login_url,
                login_id=params.get('login_id'),
                verify_domain=params.get('verify_domain'),
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
            
            # STEP 2: Load MVAs
            self.logger.info("STEP 2: Load MVAs")
            
            if params.get('mva_list'):
                mvas = params['mva_list']
                self.logger.info(f"[WORKFLOW] Using provided MVA list: {len(mvas)} MVAs")
            elif params.get('input_file'):
                try:
                    mvas = read_mva_list(params['input_file'])
                    self.logger.info(f"[WORKFLOW] Read {len(mvas)} MVAs from: {params['input_file']}")
                except Exception as e:
                    self.logger.error(f"[WORKFLOW] Failed to read MVA list: {e}")
                    return {
                        "status": "error",
                        "error": str(e),
                        "summary": "Failed to read input CSV"
                    }
            else:
                error_msg = "No MVA source provided (need input_file or mva_list)"
                self.logger.error(f"[WORKFLOW] {error_msg}")
                return {
                    "status": "error",
                    "error": error_msg,
                    "summary": "No MVA source"
                }
            
            # STEP 3: Process MVAs
            self.logger.info(f"STEP 3: Process {len(mvas)} MVAs")
            results = []
            
            for idx, mva in enumerate(mvas, 1):
                self.logger.info(f"[{idx}/{len(mvas)}] Processing MVA: {mva}")
                
                try:
                    # Enter MVA
                    enter_result = self.vehicle_actions.enter_mva(mva, timeout=timeout)
                    if enter_result.get("status") != "success":
                        self.logger.warning(f"  Failed to enter MVA: {enter_result.get('error')}")
                        result = {"mva": mva, "error": enter_result.get('error')}
                        for prop in properties:
                            result[prop.lower()] = "N/A"
                        results.append(result)
                        continue
                    
                    # Verify echo
                    echo_result = self.vehicle_actions.verify_mva_echo(mva, timeout=5)
                    if echo_result.get("status") != "success":
                        self.logger.warning(f"  MVA echo verification failed: {echo_result.get('error')}")
                    
                    # Get properties
                    result = {"mva": mva}
                    for prop in properties:
                        prop_result = self.vehicle_actions.wait_for_property_loaded(prop, timeout=timeout)
                        value = prop_result.get("value", "N/A") if prop_result.get("status") == "success" else "N/A"
                        result[prop.lower()] = value
                        self.logger.debug(f"  {prop}: {value}")
                    
                    result['error'] = None
                    results.append(result)
                    self.logger.info(f"  Success: {', '.join([f'{k}={v}' for k, v in result.items() if k != 'mva' and k != 'error'])}")
                    
                except Exception as e:
                    self.logger.error(f"  Error processing MVA {mva}: {e}")
                    result = {"mva": mva, "error": str(e)}
                    for prop in properties:
                        result[prop.lower()] = "N/A"
                    results.append(result)
            
            # STEP 4: Write results
            self.logger.info("STEP 4: Write results")
            
            try:
                write_results_csv(results, output_file)
                abs_output = os.path.abspath(output_file)
                self.logger.info(f"[WORKFLOW] Results written to: {abs_output}")
            except Exception as e:
                self.logger.error(f"[WORKFLOW] Failed to write results: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "summary": f"Processed {len(results)} MVAs but failed to write output",
                    "results_count": len(results)
                }
            
            # Success
            success_count = sum(1 for r in results if not r.get('error'))
            self.logger.info("=" * 60)
            self.logger.info(f"Workflow completed: {success_count}/{len(results)} successful")
            self.logger.info("=" * 60)
            
            return {
                "status": "success",
                "summary": f"Processed {len(results)} MVAs ({success_count} successful)",
                "results_count": len(results),
                "success_count": success_count,
                "output_file": os.path.abspath(output_file)
            }
            
        except Exception as e:
            self.logger.error(f"[WORKFLOW] Unexpected error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "summary": "Workflow failed with unexpected error"
            }
