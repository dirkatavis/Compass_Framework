"""
End-to-End (E2E) tests for Compass Framework.

Tests complete user workflows with real browser automation, 
validating that all protocols work together in production scenarios.
"""
import unittest
from compass_core import (
    StandardDriverManager, SeleniumNavigator, BrowserVersionChecker, 
    StandardLogger, JsonConfiguration
)


class TestE2E(unittest.TestCase):
    """End-to-end tests with real browser automation."""
    
    def setUp(self):
        """Set up E2E test environment."""
        self.logger = StandardLogger("e2e_tests")
        self.version_checker = BrowserVersionChecker()
        self.driver_manager = None
        self.navigator = None
        
    def tearDown(self):
        """Clean up after E2E tests."""
        if self.driver_manager:
            try:
                self.driver_manager.quit_driver()
            except Exception as e:
                self.logger.warning(f"Cleanup error: {e}")
    
    @unittest.skipIf(
        not hasattr(unittest, '_e2e_enabled'), 
        "E2E tests disabled - set unittest._e2e_enabled = True to enable"
    )
    def test_basic_web_navigation(self):
        """Test basic web navigation with example.com."""
        # Pre-flight compatibility check
        compatibility = self.version_checker.check_compatibility("edge")
        self.assertTrue(compatibility["compatible"], 
                       f"Browser compatibility failed: {compatibility}")
        
        # Initialize WebDriver and Navigator
        self.driver_manager = StandardDriverManager()
        driver = self.driver_manager.get_or_create_driver()
        self.navigator = SeleniumNavigator(driver)
        
        # Navigate and verify
        result = self.navigator.navigate_to(
            "https://example.com", 
            label="Example.com Test", 
            verify=True
        )
        
        self.assertEqual(result["status"], "ok", f"Navigation failed: {result}")
        self.logger.info(f"Successfully navigated to: {driver.current_url}")
        
        # Verify page loaded
        page_verify = self.navigator.verify_page(url="https://example.com")
        self.assertEqual(page_verify["status"], "ok")
    
    @unittest.skipIf(
        not hasattr(unittest, '_e2e_enabled'), 
        "E2E tests disabled - set unittest._e2e_enabled = True to enable"
    )
    def test_palantir_redirect_handling(self):
        """Test real-world redirect handling with Avis Palantir Foundry."""
        # Pre-flight compatibility check
        compatibility = self.version_checker.check_compatibility("edge")
        self.assertTrue(compatibility["compatible"])
        
        # Initialize components
        self.driver_manager = StandardDriverManager()
        driver = self.driver_manager.get_or_create_driver()
        self.navigator = SeleniumNavigator(driver)
        
        # Navigate with redirect tolerance - using startswith() validation
        result = self.navigator.navigate_to(
            "https://avisbudget.palantirfoundry.com/",
            label="Avis Palantir Foundry", 
            verify=True  # Will handle redirects with startswith()
        )
        
        self.assertEqual(result["status"], "ok", f"Navigation failed: {result}")
        self.logger.info(f"Handled redirect to: {driver.current_url}")
        
        # Verify we ended up on correct domain
        self.assertTrue(
            driver.current_url.startswith("https://avisbudget.palantirfoundry.com"),
            f"Unexpected redirect destination: {driver.current_url}"
        )
    
    @unittest.skipIf(
        not hasattr(unittest, '_e2e_enabled'), 
        "E2E tests disabled - set unittest._e2e_enabled = True to enable"
    )
    def test_configuration_driven_navigation(self):
        """Test navigation using JsonConfiguration for URLs."""
        import tempfile
        import json
        import os
        
        # Create test configuration
        config_data = {
            "test_urls": {
                "example": "https://example.com",
                "httpbin": "https://httpbin.org/get"
            },
            "timeouts": {
                "page_load": 10,
                "verify": 5
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # Load configuration
            config = JsonConfiguration()
            config.load(config_file)
            
            # Pre-flight check
            compatibility = self.version_checker.check_compatibility("edge")
            self.assertTrue(compatibility["compatible"])
            
            # Initialize browser
            self.driver_manager = StandardDriverManager()
            driver = self.driver_manager.get_or_create_driver()
            self.navigator = SeleniumNavigator(driver)
            
            # Test configuration-driven navigation
            test_url = config.get("test_urls.example")
            self.assertEqual(test_url, "https://example.com")
            
            result = self.navigator.navigate_to(test_url, verify=True)
            self.assertEqual(result["status"], "ok")
            
            self.logger.info(f"Configuration-driven navigation successful: {test_url}")
            
        finally:
            # Cleanup config file
            if os.path.exists(config_file):
                os.unlink(config_file)
    
    @unittest.skipIf(
        not hasattr(unittest, '_e2e_enabled'), 
        "E2E tests disabled - set unittest._e2e_enabled = True to enable"
    )
    def test_driver_lifecycle_management(self):
        """Test complete driver lifecycle with multiple operations."""
        # Pre-flight check
        compatibility = self.version_checker.check_compatibility("edge")
        self.assertTrue(compatibility["compatible"])
        
        # Test driver creation
        self.driver_manager = StandardDriverManager()
        self.assertFalse(self.driver_manager.is_driver_active())
        
        # Create driver
        driver = self.driver_manager.get_or_create_driver()
        self.assertTrue(self.driver_manager.is_driver_active())
        
        # Test singleton pattern - should return same driver
        driver2 = self.driver_manager.get_or_create_driver()
        self.assertEqual(driver, driver2)
        
        # Test navigation
        self.navigator = SeleniumNavigator(driver)
        result = self.navigator.navigate_to("https://httpbin.org/get", verify=True)
        self.assertEqual(result["status"], "ok")
        
        # Test explicit cleanup
        self.driver_manager.quit_driver()
        self.assertFalse(self.driver_manager.is_driver_active())
        
        self.logger.info("Driver lifecycle management test completed successfully")


# Helper to enable E2E tests
def enable_e2e_tests():
    """Enable E2E tests - call before running test suite."""
    unittest._e2e_enabled = True


if __name__ == '__main__':
    # Uncomment to enable E2E tests
    # enable_e2e_tests()
    unittest.main()