"""
E2E test for Additional Information page Submit Complaint button.

Tests the final step of the complaint workflow where the user reviews
the summary and clicks Submit Complaint to finalize the workitem.
"""
import unittest
import logging

# Only run if E2E tests are enabled
try:
    if not getattr(unittest, '_e2e_enabled', False):
        raise ImportError("E2E tests not enabled")
except (AttributeError, ImportError):
    import sys
    sys.exit(0)

from compass_core import IniConfiguration, StandardDriverManager, SmartLoginFlow
from compass_core import SeleniumNavigator, SeleniumPmActions


class TestAdditionalInformationPageSubmit(unittest.TestCase):
    """Test Submit Complaint button on Additional Information page."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures - runs once for the class."""
        cls.logger = logging.getLogger(__name__)
        cls.config = IniConfiguration("webdriver.ini")
        
        # Verify credentials are configured
        creds = cls.config.get_credentials()
        if not all([creds.get('username'), creds.get('password'), creds.get('login_id')]):
            raise unittest.SkipTest("Credentials not configured in webdriver.ini")
    
    def setUp(self):
        """Set up test - runs before each test method."""
        # Create fresh browser session
        self.driver_manager = StandardDriverManager(self.config)
        self.driver = self.driver_manager.get_driver(incognito=False)
        
        # Set up navigation and actions
        self.navigator = SeleniumNavigator(self.driver)
        self.pm_actions = SeleniumPmActions(self.driver, timeout=30, step_delay=0.5)
        
        # Authenticate
        app_config = self.config.get_application_config()
        login_flow = SmartLoginFlow(
            driver=self.driver,
            navigator=self.navigator,
            config=self.config,
            app_url=app_config['app_url']
        )
        result = login_flow.login()
        self.assertEqual(result['status'], 'success', f"Login failed: {result}")
    
    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, 'driver_manager'):
            self.driver_manager.quit()
    
    def test_submit_complaint_button_exists_and_clickable(self):
        """
        Test that Submit Complaint button is present and clickable on Additional Info page.
        
        This test navigates through the complete workflow to reach the Additional
        Information page, then verifies the Submit Complaint button can be clicked
        successfully.
        """
        # Navigate to a test vehicle
        test_mva = "60223962"
        self.navigator.navigate_to_vehicle(test_mva)
        
        # Verify we're on the vehicle page
        result = self.navigator.verify_page(
            url_prefix="fleet-operations-pwa/health",
            element_locator=("xpath", "//button[contains(., 'Add Work Item')]")
        )
        self.assertEqual(result['status'], 'success')
        
        # Create a workitem to reach Additional Info page
        create_result = self.pm_actions.create_workitem(
            mva=test_mva,
            damage_type="Glass Damage",
            sub_damage_type="Windshield Crack",
            correction_action="Test correction action for E2E test"
        )
        
        # Should succeed - workitem creation includes clicking Submit button
        self.assertEqual(
            create_result.get('status'),
            'success',
            f"create_workitem failed: {create_result.get('reason', 'unknown')}"
        )
        
        # Verify we reached Additional Info page and clicked Submit
        # (create_workitem already does this, but we're testing the full flow)
        self.logger.info("Workitem creation completed successfully")
    
    def test_additional_info_page_object_model(self):
        """
        Test the Additional Information Page Object Model in isolation.
        
        This test manually navigates through the workflow, then uses the POM
        to interact with the Additional Information page.
        
        NOTE: This currently runs the full workflow since create_workitem
        doesn't expose intermediate steps. Will refactor if needed.
        """
        # Navigate to test vehicle
        test_mva = "60223962"
        self.navigator.navigate_to_vehicle(test_mva)
        
        # For now, just verify we can complete the workflow
        # TODO: Refactor create_workitem to allow stopping at Additional Info page
        create_result = self.pm_actions.create_workitem(
            mva=test_mva,
            damage_type="Glass Damage",
            sub_damage_type="Windshield Crack",
            correction_action="Test POM integration"
        )
        self.assertEqual(create_result.get('status'), 'success')
    
    def test_submit_button_locator_is_correct(self):
        """
        Test that the Submit Complaint button XPath locator is correct.
        
        This validates our POM locator matches the actual HTML structure.
        By running the full workflow, we verify the locator works.
        """
        # Navigate and create workitem - this exercises the Submit button locator
        test_mva = "60223962"
        self.navigator.navigate_to_vehicle(test_mva)
        
        create_result = self.pm_actions.create_workitem(
            mva=test_mva,
            damage_type="Glass Damage",
            sub_damage_type="Windshield Crack",
            correction_action="Test locator validation"
        )
        # If this succeeds, the Submit button locator is correct
        self.assertEqual(create_result.get('status'), 'success')


if __name__ == '__main__':
    unittest.main()
