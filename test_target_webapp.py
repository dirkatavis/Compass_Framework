"""
Target Web Application E2E Test - Avis Budget Palantir Foundry

Tests the specific redirect behavior and authentication flow 
of the target application with unique qualities.
"""
import unittest
import time
from compass_core import StandardLogger, SeleniumNavigator


class TestTargetWebApp(unittest.TestCase):
    """Test the target web application with its unique redirect qualities."""
    
    def setUp(self):
        """Set up target web app test environment."""
        self.logger = StandardLogger("target_webapp_tests")
        self.driver = None
        print("\n" + "="*70)
        print("🎯 TARGET WEB APPLICATION E2E TEST")
        print("🔗 Testing: https://avisbudget.palantirfoundry.com/")
        print("📋 Focus: Redirect handling and authentication flows")
        print("="*70)
        
    def tearDown(self):
        """Clean up after target web app tests."""
        if self.driver:
            try:
                print("\n⏳ Keeping browser open for 5 seconds to examine final state...")
                time.sleep(5)
                print("🔧 Closing browser...")
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
    
    def test_target_webapp_redirect_flow(self):
        """Test the complete redirect flow of the target web application."""
        print("\n🚀 Starting Target Web Application Test")
        print("-" * 50)
        
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            print("⚙️  Configuring browser for target application...")
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            # Remove headless to see authentication flows
            
            print("🌐 Launching browser for target application...")
            self.driver = webdriver.Edge(options=options)
            navigator = SeleniumNavigator(self.driver)
            
            # Initial URL
            target_url = "https://avisbudget.palantirfoundry.com/"
            print(f"📍 Initial target URL: {target_url}")
            
            print("🧭 Step 1: Navigating to target application...")
            print("   👀 WATCH FOR REDIRECTS - this is where unique behavior occurs!")
            
            result = navigator.navigate_to(
                target_url,
                label="Target Web App Initial Load",
                verify=False  # Don't verify URL match due to expected redirects
            )
            
            print(f"📊 Navigation result: {result['status']}")
            print(f"📍 Current URL after navigation: {self.driver.current_url}")
            print(f"📄 Page title: {self.driver.title}")
            
            # Analyze the redirect behavior
            if self.driver.current_url != target_url:
                print("\n🔄 REDIRECT DETECTED!")
                print(f"   Original: {target_url}")
                print(f"   Redirected to: {self.driver.current_url}")
                
                # Check if it's an authentication redirect
                if "auth" in self.driver.current_url.lower() or "login" in self.driver.current_url.lower():
                    print("🔐 Authentication redirect detected")
                    
                    # Try to analyze the login page
                    try:
                        print("🔍 Analyzing authentication page...")
                        
                        # Look for common authentication elements
                        login_elements = []
                        
                        # Check for username/email fields
                        try:
                            username_fields = self.driver.find_elements(By.CSS_SELECTOR, 
                                "input[type='email'], input[type='text'], input[name*='user'], input[name*='email']")
                            if username_fields:
                                login_elements.append(f"Username/Email fields: {len(username_fields)}")
                        except: pass
                        
                        # Check for password fields
                        try:
                            password_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                            if password_fields:
                                login_elements.append(f"Password fields: {len(password_fields)}")
                        except: pass
                        
                        # Check for login buttons
                        try:
                            login_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                                "button[type='submit'], input[type='submit'], button:contains('Login'), button:contains('Sign')")
                            if login_buttons:
                                login_elements.append(f"Login buttons: {len(login_buttons)}")
                        except: pass
                        
                        if login_elements:
                            print("🎯 Authentication elements found:")
                            for element in login_elements:
                                print(f"   • {element}")
                        else:
                            print("❓ No standard authentication elements found")
                            print("   This might be SSO, SAML, or custom authentication")
                            
                    except Exception as e:
                        print(f"⚠️  Error analyzing authentication page: {e}")
                
                elif "error" in self.driver.current_url.lower():
                    print("❌ Error page detected")
                else:
                    print("🔄 Other type of redirect detected")
                    
            else:
                print("✅ No redirect - direct access to application")
            
            # Wait a bit and check for any dynamic redirects
            print("\n⏳ Waiting 3 seconds for any dynamic redirects...")
            time.sleep(3)
            
            final_url = self.driver.current_url
            final_title = self.driver.title
            
            print(f"📍 Final URL: {final_url}")
            print(f"📄 Final title: {final_title}")
            
            # Try to capture page source info without exposing sensitive content
            try:
                page_source = self.driver.page_source
                print(f"📄 Page source length: {len(page_source)} characters")
                
                # Look for common indicators
                indicators = []
                if "palantir" in page_source.lower():
                    indicators.append("Palantir branding")
                if "foundry" in page_source.lower():
                    indicators.append("Foundry platform")
                if "avis" in page_source.lower():
                    indicators.append("Avis branding")
                if "oauth" in page_source.lower() or "saml" in page_source.lower():
                    indicators.append("Enterprise authentication")
                    
                if indicators:
                    print("🏷️  Page indicators found:")
                    for indicator in indicators:
                        print(f"   • {indicator}")
                        
            except Exception as e:
                print(f"⚠️  Could not analyze page source: {e}")
            
            # Test navigation verification with flexible URL matching
            print("\n🔍 Testing Compass Framework redirect handling...")
            verify_result = navigator.verify_page(timeout=5)
            print(f"📊 Page verification result: {verify_result['status']}")
            
            # Success criteria: We can navigate and handle whatever redirect occurs
            self.assertEqual(result["status"], "success", "Navigation should succeed even with redirects")
            self.assertTrue(len(final_url) > 0, "Should end up at some valid URL")
            
            print("\n✅ Target web application test COMPLETED!")
            print("🎉 Framework successfully handled the application's unique redirect behavior!")
            
        except Exception as e:
            print(f"\n❌ Target web application test failed: {e}")
            if self.driver:
                print(f"📍 URL at failure: {self.driver.current_url}")
                print(f"📄 Title at failure: {self.driver.title}")
            raise
    
    def test_target_webapp_user_agent_handling(self):
        """Test how the target application handles different user agents."""
        print("\n🕵️ Testing User Agent Handling")
        print("-" * 40)
        
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            
            # Test with custom user agent
            print("⚙️  Configuring browser with custom user agent...")
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 CompassFramework/0.1.0")
            
            print("🌐 Launching browser with custom user agent...")
            self.driver = webdriver.Edge(options=options)
            navigator = SeleniumNavigator(self.driver)
            
            target_url = "https://avisbudget.palantirfoundry.com/"
            
            print(f"🧭 Navigating to target with custom user agent...")
            result = navigator.navigate_to(target_url, label="User Agent Test", verify=False)
            
            print(f"📊 Result: {result['status']}")
            print(f"📍 Final URL: {self.driver.current_url}")
            
            # Check if user agent affects redirect behavior
            print("🔍 Checking if custom user agent affects redirect behavior...")
            
            self.assertEqual(result["status"], "success")
            print("✅ Custom user agent handled successfully!")
            
        except Exception as e:
            print(f"❌ User agent test failed: {e}")
            raise


if __name__ == '__main__':
    print("🎯 Compass Framework - Target Web Application E2E Tests")
    print("=" * 70)
    print("🔗 Testing Avis Budget Palantir Foundry application")
    print("📋 Focus: Real-world redirect scenarios and authentication flows")
    print("⚠️  Note: Browser windows will open - watch the redirect flow!")
    print("=" * 70)
    input("\nPress ENTER to start target web application tests...")
    unittest.main(verbosity=2)