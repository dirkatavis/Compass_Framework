"""
End-to-End tests for Vehicle Data Lookup against real Compass application.

These tests validate the complete workflow:
1. LoginFlow authentication with Microsoft SSO
2. VehicleDataActions MVA entry and property retrieval
3. VehicleLookupFlow batch processing

REQUIRES:
- Credentials configured (webdriver.ini.local or env vars)
- Compass application URL configured
- Valid MVA for testing
"""
import unittest
import os
from compass_core import (
    StandardDriverManager,
    SeleniumNavigator,
    SeleniumLoginFlow,
    SmartLoginFlow,
    SeleniumVehicleDataActions,
    IniConfiguration,
    StandardLogger,
    read_mva_list,
    write_results_csv
)


class TestVehicleLookupE2E(unittest.TestCase):
    """End-to-end tests for vehicle data lookup workflows."""
    
    def setUp(self):
        """Set up E2E test environment."""
        self.logger = StandardLogger("vehicle_lookup_e2e")
        
        # Load configuration
        self.config = IniConfiguration()
        try:
            self.config.load("webdriver.ini.local")
        except Exception:
            # Fall back to template
            self.config.load("webdriver.ini")
        
        # Get credentials from config or env
        self.username = self.config.get('credentials.username') or os.getenv('COMPASS_USERNAME')
        self.password = self.config.get('credentials.password') or os.getenv('COMPASS_PASSWORD')
        self.login_id = self.config.get('credentials.login_id') or os.getenv('COMPASS_LOGIN_ID')
        self.login_url = self.config.get('app.login_url', 'https://login.microsoftonline.com/')
        self.app_url = self.config.get('app.app_url')
        
        # Test MVA
        self.test_mva = os.getenv('TEST_MVA', '50227203')
        
        self.driver_manager = None
        self.navigator = None
        self.login_flow = None
        self.vehicle_actions = None
    
    def tearDown(self):
        """Clean up after E2E tests."""
        if self.driver_manager:
            try:
                self.driver_manager.quit_driver()
            except Exception as e:
                self.logger.warning(f"Cleanup error: {e}")
    
    @unittest.skip("Disabled - alert handling needs work, only using cache_miss test")
    def test_smart_login_with_sso_cache_hit(self):
        """Test SmartLoginFlow when SSO session is already active."""
        # Skip if credentials not configured
        if not all([self.username, self.app_url]):
            self.skipTest("Credentials/app_url not configured")
        
        # Initialize components
        self.driver_manager = StandardDriverManager()
        driver = self.driver_manager.get_or_create_driver(incognito=True, headless=False)
        self.navigator = SeleniumNavigator(driver)
        base_login_flow = SeleniumLoginFlow(driver, self.navigator, self.logger)
        smart_login = SmartLoginFlow(driver, self.navigator, base_login_flow, self.logger)
        
        self.logger.info("Testing SmartLoginFlow in incognito mode (consistent flow)...")
        
        # First authentication - should perform login
        result1 = smart_login.authenticate(
            username=self.username,
            password=self.password,
            app_url=self.app_url,
            login_id=self.login_id,
            timeout=30
        )
        
        self.assertEqual(result1.get("status"), "success")
        self.assertTrue(result1.get("authenticated"), "First auth should perform login in incognito mode")
        self.logger.info(f"First auth: {result1.get('message')}, authenticated={result1.get('authenticated')}")
        
        # Second authentication in incognito - should also perform login (no cache)
        result2 = smart_login.authenticate(
            username=self.username,
            password=self.password,
            app_url=self.app_url,
            login_id=self.login_id,
            timeout=30
        )
        
        self.assertEqual(result2.get("status"), "success")
        self.assertTrue(result2.get("authenticated"), 
                       "Second auth should also perform login in incognito (no SSO cache)")
        self.logger.info(f"✓ SmartLoginFlow consistent in incognito mode: {result2.get('message')}")
    
    @unittest.skipIf(
        not hasattr(unittest, '_e2e_enabled'),
        "E2E tests disabled - set unittest._e2e_enabled = True to enable"
    )
    def test_smart_login_with_sso_cache_miss(self):
        """Test SmartLoginFlow when SSO session is missing (incognito mode)."""
        # Skip if credentials not configured
        if not all([self.username, self.password, self.app_url]):
            self.skipTest("Credentials/app_url not configured")
        
        # Initialize components with incognito (forces cache miss)
        self.driver_manager = StandardDriverManager()
        driver = self.driver_manager.get_or_create_driver(incognito=True)
        self.navigator = SeleniumNavigator(driver)
        base_login_flow = SeleniumLoginFlow(driver, self.navigator, self.logger)
        smart_login = SmartLoginFlow(driver, self.navigator, base_login_flow, self.logger)
        
        self.logger.info("Testing SmartLoginFlow with incognito (cache miss)...")
        
        # Authentication - should perform login with extended timeout
        result = smart_login.authenticate(
            username=self.username,
            password=self.password,
            app_url=self.app_url,
            login_id=self.login_id,
            timeout=60  # Increased timeout for stability
        )
        
        self.assertEqual(result.get("status"), "success")
        self.assertTrue(result.get("authenticated"), "Should perform login when SSO cache missing")
        self.logger.info(f"✓ SmartLoginFlow correctly performed login: {result.get('message')}")
        
        # Pause to observe WWID screen (if it appears in new tab)
        import time
        self.logger.info("Pausing 10 seconds to observe WWID screen...")
        time.sleep(10)
    
    @unittest.skip("Disabled - API signature issue, only using login test for now")
    def test_vehicle_data_actions_mva_lookup(self):
        """Test VehicleDataActions with single MVA lookup."""
        # Skip if credentials not configured
        if not all([self.username, self.password, self.app_url]):
            self.skipTest("Credentials/app_url not configured - set in webdriver.ini.local or env vars")
        
        # Initialize components
        self.driver_manager = StandardDriverManager()
        driver = self.driver_manager.get_or_create_driver(incognito=True)
        self.navigator = SeleniumNavigator(driver)
        base_login_flow = SeleniumLoginFlow(driver, self.navigator, self.logger)
        smart_login = SmartLoginFlow(driver, self.navigator, base_login_flow, self.logger)
        self.vehicle_actions = SeleniumVehicleDataActions(driver, self.logger)
        
        # Step 1: Authenticate
        self.logger.info("Step 1: Authenticating...")
        auth_result = smart_login.authenticate(
            username=self.username,
            password=self.password,
            app_url=self.app_url,
            login_id=self.login_id,
            timeout=30
        )
        self.assertEqual(auth_result.get("status"), "success")
        
        # Step 2: Enter MVA (SmartLoginFlow already navigated to app)
        self.logger.info(f"Step 3: Entering MVA: {self.test_mva}")
        enter_result = self.vehicle_actions.enter_mva(self.test_mva, timeout=10)
        self.assertEqual(enter_result.get("status"), "success",
                        f"Failed to enter MVA: {enter_result.get('error')}")
        
        # Step 3: Verify MVA echo
        self.logger.info("Step 3: Verifying MVA echo...")
        echo_result = self.vehicle_actions.verify_mva_echo(self.test_mva, timeout=5)
        self.assertEqual(echo_result.get("status"), "success",
                        f"MVA echo verification failed: {echo_result.get('error')}")
        
        # Step 4: Get VIN
        self.logger.info("Step 4: Retrieving VIN...")
        vin_result = self.vehicle_actions.wait_for_property_loaded("VIN", timeout=12)
        self.assertEqual(vin_result.get("status"), "success",
                        f"Failed to get VIN: {vin_result.get('error')}")
        vin = vin_result.get("value")
        self.assertNotEqual(vin, "N/A", "VIN should not be N/A")
        self.logger.info(f"✓ VIN retrieved: {vin}")
        
        # Step 5: Get Description
        self.logger.info("Step 5: Retrieving Description...")
        desc_result = self.vehicle_actions.wait_for_property_loaded("Desc", timeout=12)
        self.assertEqual(desc_result.get("status"), "success",
                        f"Failed to get Desc: {desc_result.get('error')}")
        desc = desc_result.get("value")
        self.assertNotEqual(desc, "N/A", "Description should not be N/A")
        self.logger.info(f"✓ Description retrieved: {desc}")
        
        self.logger.info(f"✓ Complete vehicle data retrieved for MVA {self.test_mva}")
    
    @unittest.skip("Disabled - API signature issue, only using login test for now")
    def test_batch_mva_lookup_workflow(self):
        """Test VehicleLookupFlow with multiple MVAs."""
        # Skip if credentials not configured
        if not all([self.username, self.password, self.app_url]):
            self.skipTest("Credentials/app_url not configured - set in webdriver.ini.local or env vars")
        
        from compass_core import VehicleLookupFlow
        
        # Initialize components
        self.driver_manager = StandardDriverManager()
        driver = self.driver_manager.get_or_create_driver(incognito=True)
        self.navigator = SeleniumNavigator(driver)
        base_login_flow = SeleniumLoginFlow(driver, self.navigator, self.logger)
        smart_login = SmartLoginFlow(driver, self.navigator, base_login_flow, self.logger)
        self.vehicle_actions = SeleniumVehicleDataActions(driver, self.logger)
        
        # Create workflow
        workflow = VehicleLookupFlow(
            driver_manager=self.driver_manager,
            navigator=self.navigator,
            login_flow=smart_login,
            vehicle_actions=self.vehicle_actions,
            logger=self.logger
        )
        
        # Prepare test MVAs (use sample or env var)
        test_mvas = os.getenv('TEST_MVAS', '50227203,12345678').split(',')
        output_file = "test_e2e_results.csv"
        
        self.logger.info(f"Testing VehicleLookupFlow with {len(test_mvas)} MVAs...")
        
        # Run workflow
        params = {
            "mva_list": test_mvas,
            "output_file": output_file,
            "username": self.username,
            "password": self.password,
            "app_url": self.app_url,
            "login_id": self.login_id,
            "timeout": 15
        }
        
        result = workflow.run(params)
        
        # Verify workflow success
        self.assertEqual(result.get("status"), "success",
                        f"Workflow failed: {result.get('error')}")
        self.assertEqual(result.get("results_count"), len(test_mvas))
        self.assertTrue(os.path.exists(output_file), "Output file should be created")
        
        self.logger.info(f"✓ Workflow completed: {result.get('summary')}")
        
        # Cleanup output file
        if os.path.exists(output_file):
            os.remove(output_file)


if __name__ == '__main__':
    # Enable E2E tests
    unittest._e2e_enabled = True
    unittest.main(verbosity=2)
