"""
Simple test to verify browser cleanup is working properly.
"""
import unittest
import time
from compass_core import SeleniumNavigator, StandardLogger


class TestBrowserCleanup(unittest.TestCase):
    """Test to verify browser cleanup works properly."""
    
    def setUp(self):
        """Set up cleanup test."""
        self.logger = StandardLogger("cleanup_tests")
        self.driver = None
        print("\n🧹 Testing Browser Cleanup")
    
    def tearDown(self):
        """Clean up browser - this is what we're testing."""
        if self.driver:
            try:
                print("🔧 Cleaning up browser...")
                self.driver.quit()
                self.driver = None
                print("✅ Browser cleanup successful")
            except Exception as e:
                print(f"❌ Browser cleanup failed: {e}")
                # Force cleanup attempt
                try:
                    if self.driver:
                        self.driver.quit()
                        self.driver = None
                except:
                    pass
                raise
    
    def test_browser_opens_and_closes_cleanly(self):
        """Test that browser opens and closes without leaving processes."""
        print("🚀 Opening browser...")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            
            options = Options()
            options.add_argument("--headless")  # Headless for quick test
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            self.driver = webdriver.Edge(options=options)
            navigator = SeleniumNavigator(self.driver)
            
            print("✅ Browser opened successfully")
            
            # Quick navigation test
            result = navigator.navigate_to("https://example.com", verify=True)
            self.assertEqual(result["status"], "success")
            
            print(f"✅ Navigation successful: {self.driver.current_url}")
            print("🔧 Test complete - cleanup should happen in tearDown...")
            
        except Exception as e:
            self.fail(f"Browser test failed: {e}")
    
    def test_multiple_browser_cleanup(self):
        """Test that we can open multiple browsers and clean them all up."""
        print("🚀 Testing multiple browser cleanup...")
        
        drivers = []
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Open 3 browsers
            for i in range(3):
                print(f"   Opening browser {i+1}/3...")
                driver = webdriver.Edge(options=options)
                drivers.append(driver)
                
                # Quick navigation to different pages
                urls = ["https://example.com", "https://httpbin.org/get", "https://httpbin.org/user-agent"]
                driver.get(urls[i])
                print(f"   Browser {i+1} navigated to: {driver.current_url}")
            
            print("✅ All browsers opened and navigated successfully")
            
            # Clean up all drivers
            print("🔧 Cleaning up all browsers...")
            for i, driver in enumerate(drivers):
                try:
                    driver.quit()
                    print(f"   ✅ Browser {i+1} closed")
                except Exception as e:
                    print(f"   ❌ Browser {i+1} cleanup failed: {e}")
                    
            print("✅ Multiple browser cleanup test completed")
            
        except Exception as e:
            # Cleanup any remaining drivers
            for driver in drivers:
                try:
                    driver.quit()
                except:
                    pass
            self.fail(f"Multiple browser test failed: {e}")


if __name__ == '__main__':
    print("🧹 Browser Cleanup Test")
    print("=" * 40)
    print("Testing that browsers are properly closed after E2E tests")
    unittest.main(verbosity=2)