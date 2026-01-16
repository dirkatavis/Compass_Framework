"""Simplified browser cleanup validation test."""

import unittest
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager


class TestBrowserCleanupSimple(unittest.TestCase):
    """Test browser cleanup with a single browser instance."""
    
    def test_single_browser_cleanup(self):
        """Test cleanup with a single browser instance."""
        print("🌐 Testing single browser cleanup...")
        
        # Create browser with visible window
        options = Options()
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        service = Service(EdgeChromiumDriverManager().install())
        driver = webdriver.Edge(service=service, options=options)
        
        try:
            print("✅ Browser opened")
            driver.get("https://httpbin.org/user-agent")
            print("✅ Navigation completed")
            
            # Keep browser open briefly so user can see it
            time.sleep(3)
            
        finally:
            print("🔧 Starting cleanup...")
            try:
                driver.close()  # Close current window
                driver.quit()   # Quit driver
                print("✅ Browser cleanup completed successfully")
            except Exception as e:
                print(f"❌ Cleanup error: {e}")
                # Force kill if needed
                import subprocess
                try:
                    subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'], 
                                 capture_output=True, timeout=5)
                    subprocess.run(['taskkill', '/F', '/IM', 'msedgedriver.exe'], 
                                 capture_output=True, timeout=5)
                    print("⚡ Force killed browser processes")
                except:
                    print("⚠️  Could not force kill processes")


if __name__ == '__main__':
    print("🧪 Running Simplified Browser Cleanup Test")
    print("👀 You should see an Edge browser window open and close")
    print("=" * 50)
    
    unittest.main(verbosity=2)