"""
E2E test: Login + Read First MVA + Enter into Field.

Tests the complete workflow:
1. Login using SmartLoginFlow
2. Read first MVA from MvaCollection
3. Enter MVA into input field using SeleniumVehicleDataActions

REQUIRES:
- Credentials configured (webdriver.ini.local or env vars)
- App URL configured
- Real browser WebDriver
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
    MvaCollection
)


class TestLoginReadFirstMvaE2E(unittest.TestCase):
    """E2E test for login -> read first MVA -> enter into field."""
    
    def setUp(self):
        """Set up E2E test environment."""
        # Check if E2E tests are enabled
        if not hasattr(unittest, '_e2e_enabled') or not unittest._e2e_enabled:
            self.skipTest("E2E tests not enabled (run with --enable-e2e)")
        
        self.logger = StandardLogger("login_first_mva_e2e")
        
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
        self.app_url = self.config.get('app.app_url')
        
        # Skip if credentials not configured
        if not all([self.username, self.password, self.app_url]):
            self.skipTest("Credentials/app_url not configured")
        
        self.driver_manager = None
        self.driver = None
        self.navigator = None
    
    def tearDown(self):
        """Clean up after E2E tests."""
        if self.driver_manager:
            try:
                self.driver_manager.quit_driver()
            except Exception as e:
                self.logger.warning(f"Cleanup error: {e}")
    
    def test_login_and_enter_first_mva(self):
        """
        Complete E2E workflow:
        1. Initialize browser and navigate
        2. Login using SmartLoginFlow
        3. Create MvaCollection with test MVAs
        4. Read first MVA from collection
        5. Enter first MVA into input field
        """
        # Step 0: Initialize components
        self.logger.info("=== E2E Test: Login + First MVA Entry ===")
        
        # Create driver (incognito to force fresh login)
        self.driver_manager = StandardDriverManager()
        self.driver = self.driver_manager.get_or_create_driver(
            incognito=True,
            headless=False  # Keep visible for debugging
        )
        
        self.navigator = SeleniumNavigator(self.driver)
        
        # Create login flows
        base_login_flow = SeleniumLoginFlow(self.driver, self.navigator, self.logger)
        smart_login = SmartLoginFlow(self.driver, self.navigator, base_login_flow, self.logger)
        
        # Create vehicle data actions
        vehicle_actions = SeleniumVehicleDataActions(self.driver, self.logger)
        
        # Step 1: Login with SmartLoginFlow
        self.logger.info("\n[STEP 1] Performing login with SmartLoginFlow...")
        login_result = smart_login.authenticate(
            username=self.username,
            password=self.password,
            url=self.app_url,
            login_id=self.login_id,
            timeout=60  # Increase timeout to allow for SSO redirects
        )
        
        self.logger.info(f"Login result: {login_result}")
        self.assertEqual(login_result['status'], 'success', 
                        f"Login failed: {login_result.get('error', 'Unknown error')}")
        
        # Step 2: Create MVA collection with test MVAs
        self.logger.info("\n[STEP 2] Creating MVA collection...")
        test_mvas = ['50227203']  # Happy path: use only valid MVA
        collection = MvaCollection.from_list(test_mvas)
        
        self.logger.info(f"Created collection with {len(collection)} MVAs: {test_mvas}")
        self.assertEqual(len(collection), 1, "Collection should have 1 MVA")
        
        # Step 3-8: Process all MVAs in collection
        self.logger.info(f"\n[STEP 3] Processing all {len(collection)} MVAs...")
        
        properties_to_get = ['MVA', 'Plate', 'VIN', 'Desc', 'Region Brand', 'Car Class Code']
        
        for idx, mva_item in enumerate(collection, start=1):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Processing MVA {idx}/{len(collection)}: {mva_item.mva}")
            self.logger.info(f"{'='*60}")
            
            # Mark as processing
            self.logger.info(f"[{idx}.1] Marking MVA as processing...")
            mva_item.mark_processing()
            self.assertTrue(mva_item.is_processing, f"MVA {mva_item.mva} should be marked as processing")
            
            # Enter MVA into input field
            self.logger.info(f"[{idx}.2] Entering MVA ({mva_item.mva}) into input field...")
            entry_result = vehicle_actions.enter_mva(mva_item.mva, clear_existing=True)
            
            self.assertEqual(entry_result['status'], 'success', 
                            f"MVA entry failed for {mva_item.mva}: {entry_result.get('error', 'Unknown error')}")
            
            # Verify MVA echo
            self.logger.info(f"[{idx}.3] Verifying MVA echo...")
            verify_result = vehicle_actions.verify_mva_echo(mva_item.mva)
            self.assertTrue(verify_result, f"MVA echo verification should pass for {mva_item.mva}")
            
            # Wait for property page to load
            self.logger.info(f"[{idx}.4] Waiting for property page to load...")
            property_page_loaded = vehicle_actions.wait_for_property_page_loaded(mva_item.mva, timeout=15)
            
            if not property_page_loaded:
                # Mark as failed if property page doesn't load
                self.logger.error(f"Property page failed to load for MVA: {mva_item.mva}")
                mva_item.mark_failed({'error': 'Property page did not load'})
                continue
            
            # Retrieve vehicle properties
            self.logger.info(f"[{idx}.5] Retrieving vehicle properties...")
            retrieved_properties = {}
            
            for prop_name in properties_to_get:
                value = vehicle_actions.get_vehicle_property(prop_name, timeout=5)
                retrieved_properties[prop_name] = value
                self.logger.info(f"  {prop_name}: {value}")
            
            # Verify we got at least the MVA
            self.assertIsNotNone(retrieved_properties.get('MVA'), 
                               f"MVA property should be retrieved for {mva_item.mva}")
            
            # Store in MvaItem result and mark completed
            mva_item.mark_completed(retrieved_properties)
            self.logger.info(f"[{idx}.6] ✓ Completed MVA {mva_item.mva}")
            self.logger.info(f"Progress: {collection.progress_percentage:.1f}% ({collection.completed_count}/{len(collection)})")
        
        # Step 9: Final verification
        self.logger.info("\n[STEP 9] Final verification...")
        self.assertEqual(collection.completed_count, 1, "All 1 MVA should be completed")
        self.assertEqual(collection.pending_count, 0, "No MVAs should be pending")
        self.assertEqual(collection.failed_count, 0, "No MVAs should have failed")
        
        # Final verification
        self.logger.info("\n=== E2E Test Summary ===")
        self.logger.info(f"Total MVAs in collection: {len(collection)}")
        self.logger.info(f"Completed: {collection.completed_count}")
        self.logger.info(f"Pending: {collection.pending_count}")
        self.logger.info(f"Progress: {collection.progress_percentage:.1f}%")
        
        self.assertEqual(collection.completed_count, 1, "Should have 1 completed MVA")
        self.assertEqual(collection.pending_count, 2, "Should have 2 pending MVAs")
        
        self.logger.info("\n✅ E2E Test PASSED: Login + MVA Entry + Property Page Wait Complete!")


if __name__ == '__main__':
    unittest.main()
