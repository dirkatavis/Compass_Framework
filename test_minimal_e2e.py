"""
Minimal E2E test that tries to work with whatever is available.
"""
import unittest
import tempfile
import os
from pathlib import Path


class TestMinimalE2E(unittest.TestCase):
    """Minimal E2E test to demonstrate browser automation."""
    
    def test_try_real_browser_automation(self):
        """Try to actually run browser automation if possible."""
        print("\n🔍 Attempting real browser automation...")
        
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            from selenium.webdriver.edge.service import Service
            from selenium.common.exceptions import WebDriverException
            
            print("✅ Selenium imported successfully")
            
            # Try various WebDriver locations
            possible_driver_paths = [
                "msedgedriver.exe",  # Current directory
                str(Path.cwd() / "msedgedriver.exe"),  # Current directory explicit
                "C:\\Program Files\\Microsoft Edge\\msedgedriver.exe",  # Common location 1
                "C:\\Program Files (x86)\\Microsoft Edge\\msedgedriver.exe",  # Common location 2
                "C:\\Windows\\System32\\msedgedriver.exe",  # System location
            ]
            
            # Configure Edge options for headless mode (no visible browser)
            options = Options()
            options.add_argument("--headless")  # Run without GUI
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            driver = None
            driver_found = False
            
            # Try to find and use a working WebDriver
            for driver_path in possible_driver_paths:
                try:
                    print(f"  🔧 Trying WebDriver at: {driver_path}")
                    if os.path.exists(driver_path):
                        print(f"    📁 File exists")
                        service = Service(driver_path)
                        driver = webdriver.Edge(service=service, options=options)
                        driver_found = True
                        print(f"    ✅ WebDriver started successfully!")
                        break
                    else:
                        print(f"    ❌ File not found")
                except Exception as e:
                    print(f"    ⚠️  Failed: {str(e)[:100]}...")
                    continue
            
            if not driver_found:
                # Try without specifying driver path (system PATH)
                try:
                    print("  🔧 Trying system PATH WebDriver...")
                    driver = webdriver.Edge(options=options)
                    driver_found = True
                    print("  ✅ System PATH WebDriver started!")
                except Exception as e:
                    print(f"  ❌ System PATH failed: {str(e)[:100]}...")
            
            if driver_found and driver:
                try:
                    print("  🌐 Navigating to example.com...")
                    driver.get("https://example.com")
                    
                    print(f"  📍 Current URL: {driver.current_url}")
                    print(f"  📄 Page title: {driver.title}")
                    
                    # Simple validation
                    self.assertIn("example.com", driver.current_url.lower())
                    self.assertIn("example", driver.title.lower())
                    
                    print("  ✅ Real browser automation SUCCESSFUL!")
                    
                except Exception as e:
                    print(f"  ❌ Navigation failed: {e}")
                    self.fail(f"Browser automation navigation failed: {e}")
                
                finally:
                    print("  🔧 Closing browser...")
                    driver.quit()
                    print("  ✅ Browser closed")
            else:
                print("  ❌ No working WebDriver found")
                print("  💡 To enable real E2E tests:")
                print("     1. Download msedgedriver.exe from Microsoft")
                print("     2. Place in project directory or system PATH")
                print("     3. Ensure version matches your Edge browser (143.0.3650.139)")
                
                # Don't fail the test - just skip
                self.skipTest("WebDriver not available for real browser automation")
                
        except ImportError:
            self.fail("Selenium not available")
        except Exception as e:
            self.fail(f"Unexpected error in browser automation: {e}")


if __name__ == '__main__':
    print("🧪 Minimal E2E Test - Attempting Real Browser Automation")
    print("=" * 60)
    unittest.main(verbosity=2)