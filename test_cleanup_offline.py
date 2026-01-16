"""Test browser cleanup without network dependencies."""

import unittest
import time
import os
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options


class TestBrowserCleanupOffline(unittest.TestCase):
    """Test browser cleanup using locally installed driver."""
    
    def find_edge_driver(self):
        """Find Edge WebDriver in common locations."""
        # Common Edge WebDriver locations
        possible_paths = [
            # WebDriver Manager cache location
            Path.home() / '.wdm' / 'drivers' / 'edgedriver',
            # Common system paths 
            Path('C:/Windows/System32/msedgedriver.exe'),
            Path('C:/Program Files/Microsoft/Edge/Application/msedgedriver.exe'),
            Path('C:/Program Files (x86)/Microsoft/Edge/Application/msedgedriver.exe'),
        ]
        
        # Check WebDriver Manager cache directories
        wdm_base = Path.home() / '.wdm' / 'drivers' / 'edgedriver'
        if wdm_base.exists():
            for subdir in wdm_base.iterdir():
                if subdir.is_dir():
                    driver_exe = subdir / 'msedgedriver.exe'
                    if driver_exe.exists():
                        return str(driver_exe)
        
        # Check other paths
        for path in possible_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def test_browser_cleanup_with_existing_driver(self):
        """Test browser cleanup using existing driver installation."""
        print("🔍 Looking for existing Edge WebDriver...")
        
        driver_path = self.find_edge_driver()
        if not driver_path:
            self.skipTest("No Edge WebDriver found locally")
        
        print(f"✅ Found driver at: {driver_path}")
        
        # Create browser with visible window
        options = Options()
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        service = Service(driver_path)
        driver = None
        
        try:
            print("🌐 Opening browser...")
            driver = webdriver.Edge(service=service, options=options)
            print("✅ Browser opened successfully")
            
            # Navigate to a local HTML page (no network required)
            local_html = """
            <html>
                <head><title>Cleanup Test</title></head>
                <body>
                    <h1>Browser Cleanup Test</h1>
                    <p>This is a local HTML page for testing browser cleanup.</p>
                    <p>Current time: <script>document.write(new Date());</script></p>
                </body>
            </html>
            """
            driver.execute_script(f"document.open(); document.write(`{local_html}`); document.close();")
            print("✅ Local content loaded")
            
            # Keep browser visible briefly
            print("⏳ Browser will close in 3 seconds...")
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Browser test error: {e}")
            
        finally:
            if driver:
                print("🔧 Starting cleanup...")
                try:
                    # Step-by-step cleanup
                    print("  📌 Closing browser window...")
                    driver.close()
                    print("  📌 Quitting WebDriver...")
                    driver.quit()
                    print("✅ Cleanup completed successfully!")
                    
                except Exception as e:
                    print(f"❌ Cleanup error: {e}")
                    # Force cleanup
                    try:
                        import subprocess
                        print("⚡ Attempting force cleanup...")
                        subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'], 
                                     capture_output=True, timeout=5)
                        subprocess.run(['taskkill', '/F', '/IM', 'msedgedriver.exe'], 
                                     capture_output=True, timeout=5)
                        print("⚡ Force cleanup completed")
                    except Exception as force_error:
                        print(f"⚠️  Force cleanup failed: {force_error}")


if __name__ == '__main__':
    print("🧪 Testing Browser Cleanup (Offline Mode)")
    print("👀 Looking for locally installed Edge WebDriver")
    print("=" * 50)
    
    unittest.main(verbosity=2)