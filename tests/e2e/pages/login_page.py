"""
Microsoft Login Page Object Model for E2E testing.

This module provides a clean abstraction for interacting with Microsoft's
login pages, encapsulating element locators and actions.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class MicrosoftLoginPage:
    """Page Object Model for Microsoft login pages."""
    
    # Element locators
    EMAIL_INPUT = (By.ID, "i0116")
    PASSWORD_INPUT = (By.ID, "i0118")
    NEXT_BUTTON = (By.ID, "idSIButton9")
    SIGNIN_BUTTON = (By.ID, "idSIButton9")  # Same as next, but semantic naming
    ERROR_MESSAGE = (By.ID, "usernameError")
    
    def __init__(self, driver, timeout=10):
        """Initialize LoginPage with WebDriver instance.
        
        Args:
            driver: WebDriver instance
            timeout: Default timeout for element waits
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
    
    def is_login_page(self):
        """Check if current page is a Microsoft login page.
        
        Returns:
            bool: True if on login page, False otherwise
        """
        try:
            current_url = self.driver.current_url.lower()
            current_title = self.driver.title.lower()
            
            return (any(keyword in current_url for keyword in ['login.microsoftonline.com', 'login.live.com']) 
                    and any(keyword in current_title for keyword in ['sign in', 'login']))
        except:
            return False
    
    def enter_username(self, username):
        """Enter username/email into the login field.
        
        Args:
            username: Email address or username to enter
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print(f"📧 Entering username: {username}")
            
            # Wait for and find the email input field
            email_input = self.wait.until(
                EC.element_to_be_clickable(self.EMAIL_INPUT)
            )
            
            # Clear and enter username
            email_input.clear()
            email_input.send_keys(username)
            
            print(f"✅ Username entered successfully")
            return True
            
        except TimeoutException:
            print(f"❌ Timeout waiting for email input field")
            return False
        except Exception as e:
            print(f"❌ Failed to enter username: {e}")
            return False
    
    def click_next(self):
        """Click the Next button to proceed with login.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("👆 Clicking Next button...")
            
            # Wait for and click Next button
            next_button = self.wait.until(
                EC.element_to_be_clickable(self.NEXT_BUTTON)
            )
            next_button.click()
            
            print("✅ Next button clicked")
            return True
            
        except TimeoutException:
            print("❌ Timeout waiting for Next button")
            return False
        except Exception as e:
            print(f"❌ Failed to click Next button: {e}")
            return False
    
    def enter_password(self, password):
        """Enter password into the password field.
        
        Args:
            password: Password to enter
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("🔒 Entering password...")
            
            # Wait for password field to appear
            password_input = self.wait.until(
                EC.element_to_be_clickable(self.PASSWORD_INPUT)
            )
            
            # Clear and enter password
            password_input.clear()
            password_input.send_keys(password)
            
            print("✅ Password entered")
            return True
            
        except TimeoutException:
            print("❌ Timeout waiting for password field")
            return False
        except Exception as e:
            print(f"❌ Failed to enter password: {e}")
            return False
    
    def click_sign_in(self):
        """Click the Sign In button to complete login.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("🔐 Clicking Sign In button...")
            
            # Wait for and click Sign In button
            signin_button = self.wait.until(
                EC.element_to_be_clickable(self.SIGNIN_BUTTON)
            )
            signin_button.click()
            
            print("✅ Sign In button clicked")
            return True
            
        except TimeoutException:
            print("❌ Timeout waiting for Sign In button")
            return False
        except Exception as e:
            print(f"❌ Failed to click Sign In button: {e}")
            return False
    
    def get_error_message(self):
        """Get any error message displayed on the login page.
        
        Returns:
            str: Error message text, or empty string if no error
        """
        try:
            error_element = self.driver.find_element(*self.ERROR_MESSAGE)
            return error_element.text.strip()
        except NoSuchElementException:
            return ""
        except Exception:
            return ""
    
    def login(self, username, password=None):
        """Complete login process with username and optional password.
        
        Args:
            username: Email address or username
            password: Password (if required for this auth flow)
            
        Returns:
            dict: Login result with success status and message
        """
        try:
            # Step 1: Enter username
            if not self.enter_username(username):
                return {
                    'success': False,
                    'message': 'Failed to enter username'
                }
            
            # Step 2: Click Next
            if not self.click_next():
                return {
                    'success': False, 
                    'message': 'Failed to click Next button'
                }
            
            # Step 3: Handle password if provided
            if password:
                # Wait a moment for password field to appear
                import time
                time.sleep(2)
                
                if not self.enter_password(password):
                    return {
                        'success': False,
                        'message': 'Failed to enter password'
                    }
                
                if not self.click_sign_in():
                    return {
                        'success': False,
                        'message': 'Failed to click Sign In button'
                    }
            
            # Check for errors
            error_msg = self.get_error_message()
            if error_msg:
                return {
                    'success': False,
                    'message': f'Login error: {error_msg}'
                }
            
            return {
                'success': True,
                'message': 'Login process completed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Login process failed: {e}'
            }