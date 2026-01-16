"""
Visual E2E test with browser window visible so you can see the automation in action!
"""
import unittest
import tempfile
import json
import os
import time
from compass_core import (
    StandardDriverManager, SeleniumNavigator, 
    StandardLogger, JsonConfiguration
)


class TestVisualE2E(unittest.TestCase):
    """Visual E2E tests with browser window visible."""
    
    def setUp(self):
        """Set up visual E2E test environment."""
        self.logger = StandardLogger("visual_e2e_tests")
        self.driver = None  # Track the actual driver instance
        print("\n" + "="*60)
        print("🎬 VISUAL BROWSER AUTOMATION STARTING")
        print("👀 Watch your screen - browser window will appear!")
        print("="*60)
        
    def tearDown(self):
        """Clean up after visual E2E tests."""
        if self.driver:
            try:
                print("\n⏳ Keeping browser open for 3 seconds so you can see the result...")
                time.sleep(3)
                print("🔧 Closing browser...")
                
                # Force close any open windows first
                try:
                    self.driver.close()
                except:
                    pass
                
                # Then quit the driver
                self.driver.quit()
                self.driver = None
                print("✅ Browser closed")
            except Exception as e:
                self.logger.warning(f"Cleanup error: {e}")
                try:
                    # Force close if normal quit fails
                    if self.driver:
                        self.driver.quit()
                        self.driver = None
                except:
                    pass
                # Force kill any remaining processes
                import subprocess
                try:
                    subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'], 
                                 capture_output=True, timeout=5)
                    subprocess.run(['taskkill', '/F', '/IM', 'msedgedriver.exe'], 
                                 capture_output=True, timeout=5)
                except:
                    pass
    
    def test_visual_navigation_example_com(self):
        """Visual test - navigate to example.com with visible browser."""
        print("\n🎯 Test 1: Visual Navigation to Example.com")
        print("-" * 50)
        
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            
            print("⚙️  Configuring browser options...")
            options = Options()
            # Remove headless mode so browser is visible!
            options.add_argument("--start-maximized")  # Start maximized for better visibility
            options.add_argument("--disable-web-security")  # Help with some sites
            options.add_experimental_option("detach", True)  # Keep browser open longer
            
            print("🚀 Launching visible Edge browser...")
            self.driver = webdriver.Edge(options=options)
            
            print("🧭 Creating Compass SeleniumNavigator...")
            navigator = SeleniumNavigator(self.driver)
            
            print("🌐 Navigating to https://example.com...")
            print("   👀 WATCH YOUR SCREEN - Browser should appear now!")
            
            result = navigator.navigate_to(
                "https://example.com", 
                label="Visual Example Test", 
                verify=True
            )
            
            print(f"📊 Navigation result: {result['status']}")
            print(f"📍 Current URL: {self.driver.current_url}")
            print(f"📄 Page title: {self.driver.title}")
            
            # Add some visual actions you can see
            print("🎭 Performing visible actions...")
            
            # Scroll down to show movement
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            # Scroll back up
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Verify success
            self.assertEqual(result["status"], "success")
            self.assertIn("example.com", self.driver.current_url.lower())
            
            print("✅ Visual navigation test SUCCESSFUL!")
            print("   🎉 You should see example.com loaded in the browser!")
            
        except Exception as e:
            self.fail(f"Visual E2E test failed: {e}")
    
    def test_visual_multiple_page_navigation(self):
        """Visual test - navigate to multiple pages with visible browser."""
        print("\n🎯 Test 2: Visual Multi-Page Navigation")
        print("-" * 50)
        
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            
            print("⚙️  Configuring browser for multi-page test...")
            options = Options()
            options.add_argument("--start-maximized")
            
            print("🚀 Launching browser for multi-page test...")
            self.driver = webdriver.Edge(options=options)
            navigator = SeleniumNavigator(self.driver)
            
            # Page 1: Example.com
            print("\n📍 Step 1: Navigating to Example.com...")
            result1 = navigator.navigate_to("https://example.com", 
                                          label="Multi-test Page 1")
            print(f"   ✅ Page 1 loaded: {result1['status']}")
            time.sleep(2)  # Pause so you can see it
            
            # Page 2: httpbin.org  
            print("📍 Step 2: Navigating to httpbin.org/get...")
            result2 = navigator.navigate_to("https://httpbin.org/get", 
                                          label="Multi-test Page 2")
            print(f"   ✅ Page 2 loaded: {result2['status']}")
            time.sleep(2)
            
            # Page 3: httpbin.org user-agent
            print("📍 Step 3: Navigating to httpbin.org/user-agent...")
            result3 = navigator.navigate_to("https://httpbin.org/user-agent", 
                                          label="Multi-test Page 3")
            print(f"   ✅ Page 3 loaded: {result3['status']}")
            
            # Verify all navigations worked
            self.assertEqual(result1["status"], "success")
            self.assertEqual(result2["status"], "success") 
            self.assertEqual(result3["status"], "success")
            
            print(f"\n📊 Final URL: {self.driver.current_url}")
            print("🎉 Multi-page navigation SUCCESSFUL!")
            print("   👀 You should see the httpbin user-agent page!")
            
        except Exception as e:
            self.fail(f"Visual multi-page test failed: {e}")
    
    def test_visual_configuration_driven_navigation(self):
        """Visual test - configuration-driven navigation with multiple URLs."""
        print("\n🎯 Test 3: Visual Configuration-Driven Navigation")
        print("-" * 50)
        
        # Create a more interesting configuration
        config_data = {
            "test_sequence": [
                {"name": "example", "url": "https://example.com", "wait": 2},
                {"name": "json_test", "url": "https://httpbin.org/json", "wait": 2},
                {"name": "headers", "url": "https://httpbin.org/headers", "wait": 2}
            ],
            "browser_settings": {
                "maximized": True,
                "timeout": 15
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            config_file = f.name
        
        try:
            print("📄 Loading configuration file...")
            config = JsonConfiguration()
            config.load(config_file)
            
            print("🔧 Starting browser with configuration settings...")
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            
            options = Options()
            if config.get("browser_settings.maximized"):
                options.add_argument("--start-maximized")
            
            self.driver = webdriver.Edge(options=options)
            navigator = SeleniumNavigator(self.driver)
            
            # Execute the configured sequence
            test_sequence = config.get("test_sequence")
            print(f"🎭 Executing {len(test_sequence)} configured navigation steps...")
            
            for i, step in enumerate(test_sequence, 1):
                print(f"\n📍 Step {i}: {step['name']} -> {step['url']}")
                
                result = navigator.navigate_to(step['url'], 
                                             label=f"Config Step {i}: {step['name']}")
                
                print(f"   ✅ Status: {result['status']}")
                print(f"   📄 Title: {self.driver.title}")
                
                self.assertEqual(result["status"], "success")
                
                # Wait as configured
                wait_time = step.get('wait', 1)
                print(f"   ⏳ Waiting {wait_time} seconds...")
                time.sleep(wait_time)
            
            print("\n🎉 Configuration-driven navigation SUCCESSFUL!")
            print("   📊 All configured URLs were visited!")
            
        except Exception as e:
            self.fail(f"Configuration-driven test failed: {e}")
        finally:
            # Cleanup config file
            if os.path.exists(config_file):
                os.unlink(config_file)


if __name__ == '__main__':
    print("🎬 Compass Framework VISUAL E2E Tests")
    print("=" * 60)
    print("🚨 ATTENTION: Browser windows will open on your screen!")
    print("👀 Watch the browser automation happen in real-time!")
    print("=" * 60)
    input("\nPress ENTER to start the visual tests...")
    unittest.main(verbosity=2)