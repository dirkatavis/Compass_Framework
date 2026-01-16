"""
Modified E2E test that bypasses compatibility check since WebDriver is actually available.
"""
import unittest
import tempfile
import json
import os
from compass_core import (
    StandardDriverManager, SeleniumNavigator, 
    StandardLogger, JsonConfiguration
)


class TestE2EBypass(unittest.TestCase):
    """E2E tests that bypass compatibility check."""
    
    def setUp(self):
        """Set up E2E test environment."""
        self.logger = StandardLogger("e2e_tests")
        self.driver_manager = None
        self.navigator = None
        
    def tearDown(self):
        """Clean up after E2E tests."""
        if self.driver_manager:
            try:
                self.driver_manager.quit_driver()
            except Exception as e:
                self.logger.warning(f"Cleanup error: {e}")
    
    def test_bypass_compatibility_navigation(self):
        """Test navigation by bypassing compatibility check."""
        print("\n🌐 Attempting real navigation with compatibility bypass...")
        
        try:
            # Skip compatibility check and try direct creation
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            
            # Configure headless mode
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox") 
            options.add_argument("--disable-dev-shm-usage")
            
            print("  🔧 Creating WebDriver directly...")
            driver = webdriver.Edge(options=options)
            
            print("  🧭 Creating SeleniumNavigator...")
            navigator = SeleniumNavigator(driver)
            
            print("  🌐 Navigating to example.com...")
            result = navigator.navigate_to(
                "https://example.com", 
                label="Example.com Test", 
                verify=True
            )
            
            print(f"  📊 Navigation result: {result}")
            self.assertEqual(result["status"], "success", f"Navigation failed: {result}")
            
            print(f"  📍 Current URL: {driver.current_url}")
            print(f"  📄 Page title: {driver.title}")
            
            # Verify page loaded correctly
            self.assertIn("example.com", driver.current_url.lower())
            self.assertIn("example", driver.title.lower())
            
            print("  ✅ Real E2E navigation SUCCESSFUL!")
            
        except Exception as e:
            self.fail(f"E2E navigation failed: {e}")
        finally:
            if 'driver' in locals():
                print("  🔧 Closing browser...")
                driver.quit()
    
    def test_configuration_driven_real_navigation(self):
        """Test real configuration-driven navigation."""
        print("\n📋 Testing configuration-driven real navigation...")
        
        # Create test configuration
        config_data = {
            "test_urls": {
                "httpbin": "https://httpbin.org/get"
            },
            "browser_settings": {
                "headless": True,
                "timeout": 10
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            print("  📄 Loading configuration...")
            config = JsonConfiguration()
            config.load(config_file)
            
            print("  🌐 Starting browser with config settings...")
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            
            options = Options()
            if config.get("browser_settings.headless"):
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            driver = webdriver.Edge(options=options)
            navigator = SeleniumNavigator(driver)
            
            # Test configuration-driven navigation
            test_url = config.get("test_urls.httpbin")
            print(f"  🧭 Navigating to configured URL: {test_url}")
            
            result = navigator.navigate_to(test_url, verify=True)
            self.assertEqual(result["status"], "success")
            
            print(f"  📍 Successfully reached: {driver.current_url}")
            print(f"  📄 Page title: {driver.title}")
            
            # httpbin.org/get returns JSON, so title might be empty or JSON
            self.assertTrue(driver.current_url.startswith("https://httpbin.org"))
            
            print("  ✅ Configuration-driven E2E SUCCESSFUL!")
            
        finally:
            # Cleanup
            if 'driver' in locals():
                driver.quit()
            if os.path.exists(config_file):
                os.unlink(config_file)


if __name__ == '__main__':
    print("🧪 Compass Framework E2E Tests (Compatibility Bypass)")
    print("=" * 60)
    unittest.main(verbosity=2)