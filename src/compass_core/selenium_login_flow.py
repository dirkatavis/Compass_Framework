"""
Selenium-based LoginFlow implementation for Microsoft SSO.

Handles Microsoft authentication flow with username/password entry.
"""
from typing import Dict, Any
import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from compass_core.login_flow import LoginFlow
from compass_core.navigation import Navigator


class SeleniumLoginFlow:
    """
    Microsoft SSO authentication using Selenium WebDriver.
    
    Handles the typical Microsoft login flow:
    1. Navigate to login URL
    2. Enter username (email)
    3. Click "Next"
    4. Enter password
    5. Click "Sign in"
    6. Wait for redirect to application
    """
    
    def __init__(self, driver: WebDriver, navigator: Navigator, logger: logging.Logger = None):
        """
        Initialize login flow.
        
        Args:
            driver: Selenium WebDriver instance
            navigator: Navigator protocol implementation
            logger: Optional logger instance
        """
        self.driver = driver
        self.navigator = navigator
        self.logger = logger or logging.getLogger(__name__)
    
    def authenticate(
        self,
        username: str,
        password: str,
        login_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Authenticate with Microsoft SSO and optionally handle WWID entry.
        
        Args:
            username: User email address
            password: User password
            login_url: Microsoft login page URL
            **kwargs: Additional parameters:
                - login_id: str (optional WWID - Compass-specific)
                - timeout: int (default: 30)
                - verify_domain: str (optional domain verification)
                - stay_signed_in: bool (default: False - click "No", True - click "Yes")
        
        Returns:
            Dict with authentication result:
            {
                "status": "success" | "error",
                "message": str,
                "error": str (if status="error")
            }
        """
        timeout = kwargs.get('timeout', 30)
        login_id = kwargs.get('login_id')
        verify_domain = kwargs.get('verify_domain', None)
        stay_signed_in = kwargs.get('stay_signed_in', False)
        skip_navigation = kwargs.get('skip_navigation', False)  # Allow caller to skip navigation if already on page
        
        self.logger.info(f"[LOGIN] Starting authentication flow for: {username}")
        
        try:
            # Step 1: Navigate to login URL (unless already there)
            if not skip_navigation:
                nav_result = self.navigator.navigate_to(login_url, verify=False, timeout=timeout)
                if nav_result.get("status") != "success":
                    self.logger.error(f"[LOGIN] Failed to navigate to login URL: {nav_result.get('error')}")
                    return {
                        "status": "error",
                        "message": f"Failed to navigate to login URL",
                        "error": nav_result.get("error", "Unknown navigation error")
                    }
                
                self.logger.debug(f"[LOGIN] Navigated to: {login_url}")
            else:
                self.logger.debug(f"[LOGIN] Skipping navigation - already on login page")
            
            # Step 2: Enter username
            username_result = self._enter_username(username, timeout)
            if username_result.get("status") != "success":
                return username_result
            
            # Step 3: Enter password
            password_result = self._enter_password(password, timeout)
            if password_result.get("status") != "success":
                return password_result
            
            # Step 3.5: Handle "Stay signed in?" prompt if it appears (often after password)
            stay_signed_in_result = self._handle_stay_signed_in(timeout, stay_signed_in)
            if stay_signed_in_result.get("status") == "success":
                choice = "Yes" if stay_signed_in else "No"
                self.logger.debug(f"[LOGIN] Handled Stay signed in prompt: clicked '{choice}'")
            
            # Step 3.6: Enter login_id (WWID) if required - application-specific but commonly needed
            if login_id:
                # Check if WWID page opened in a new tab
                import time
                time.sleep(2)  # Wait for any new tab to open
                
                original_window = self.driver.current_window_handle
                all_windows = self.driver.window_handles
                
                if len(all_windows) > 1:
                    # Switch to the new tab (WWID page)
                    self.driver.switch_to.window(all_windows[-1])
                    self.logger.info(f"[LOGIN] Switched to new tab for WWID entry ({len(all_windows)} tabs total)")
                
                login_id_result = self._enter_wwid(login_id, timeout)
                if login_id_result.get("status") != "success":
                    self.logger.warning(f"[LOGIN] WWID entry failed: {login_id_result.get('message')}")
                    # Don't fail authentication - WWID might not be required for all apps
            
            # Step 4: Wait for redirect to application
            if verify_domain:
                verify_result = self._verify_login_success(verify_domain, timeout)
                if verify_result.get("status") != "success":
                    return verify_result
            
            self.logger.info(f"[LOGIN] Authentication successful for: {username}")
            return {
                "status": "success",
                "message": f"Authenticated successfully as {username}"
            }
            
        except Exception as e:
            self.logger.error(f"[LOGIN] Unexpected error during authentication: {e}")
            return {
                "status": "error",
                "message": "Authentication failed",
                "error": str(e)
            }
    
    def _enter_username(self, username: str, timeout: int) -> Dict[str, Any]:
        """Enter username and click Next button."""
        try:
            # Wait for username input field
            # Microsoft uses: input[type="email"], input[name="loginfmt"]
            username_field = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="loginfmt"]'))
            )
            
            if not username_field.is_displayed() or not username_field.is_enabled():
                self.logger.warning("[LOGIN][USERNAME] Field not ready, waiting...")
                username_field = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                    lambda d: (
                        (field := d.find_element(By.CSS_SELECTOR, 'input[type="email"], input[name="loginfmt"]'))
                        and field.is_displayed()
                        and field.is_enabled()
                        and field
                    )
                )
            
            username_field.clear()
            username_field.send_keys(username)
            self.logger.debug(f"[LOGIN][USERNAME] Entered: {username}")
            
            # Click Next button
            next_button = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]'))
            )
            next_button.click()
            self.logger.debug("[LOGIN][USERNAME] Clicked 'Next' button")
            
            return {"status": "success"}
            
        except TimeoutException:
            self.logger.error("[LOGIN][USERNAME] Timeout waiting for username field or Next button")
            return {
                "status": "error",
                "message": "Timeout waiting for username field",
                "error": "Username field not found within timeout"
            }
        except Exception as e:
            self.logger.error(f"[LOGIN][USERNAME] Error entering username: {e}")
            return {
                "status": "error",
                "message": "Failed to enter username",
                "error": str(e)
            }
    
    def _enter_password(self, password: str, timeout: int) -> Dict[str, Any]:
        """Enter password and click Sign in button."""
        try:
            # Wait for password input field
            # Microsoft uses: input[type="password"], input[name="passwd"]
            password_field = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"], input[name="passwd"]'))
            )
            
            if not password_field.is_displayed() or not password_field.is_enabled():
                self.logger.warning("[LOGIN][PASSWORD] Field not ready, waiting...")
                password_field = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                    lambda d: (
                        (field := d.find_element(By.CSS_SELECTOR, 'input[type="password"], input[name="passwd"]'))
                        and field.is_displayed()
                        and field.is_enabled()
                        and field
                    )
                )
            
            password_field.clear()
            password_field.send_keys(password)
            self.logger.debug("[LOGIN][PASSWORD] Entered password")
            
            # Click Sign in button
            signin_button = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"]'))
            )
            signin_button.click()
            self.logger.debug("[LOGIN][PASSWORD] Clicked 'Sign in' button")
            
            return {"status": "success"}
            
        except TimeoutException:
            self.logger.error("[LOGIN][PASSWORD] Timeout waiting for password field or Sign in button")
            return {
                "status": "error",
                "message": "Timeout waiting for password field",
                "error": "Password field not found within timeout"
            }
        except Exception as e:
            self.logger.error(f"[LOGIN][PASSWORD] Error entering password: {e}")
            return {
                "status": "error",
                "message": "Failed to enter password",
                "error": str(e)
            }
    
    def _handle_stay_signed_in(self, timeout: int, stay_signed_in: bool = False) -> Dict[str, Any]:
        """
        Handle 'Stay signed in?' prompt if it appears.
        
        Args:
            timeout: Maximum wait time
            stay_signed_in: If True, click "Yes". If False, click "No" (default)
        """
        try:
            # Determine which button to click
            if stay_signed_in:
                # Click "Yes" button
                button_selectors = [
                    'input[type="submit"][value="Yes"]',
                    'input[value="Yes"]',
                    'button[value="Yes"]',
                    '#idSIButton9'  # Microsoft ID for "Yes" button
                ]
                button_name = "Yes"
            else:
                # Click "No" button
                button_selectors = [
                    'input[type="button"][value="No"]',
                    'input[value="No"]',
                    'button[value="No"]',
                    '#idBtn_Back'  # Microsoft ID for "No" button
                ]
                button_name = "No"
            
            self.logger.debug(f"[LOGIN][STAY_SIGNED_IN] Looking for '{button_name}' button...")
            
            button = None
            for selector in button_selectors:
                try:
                    self.logger.debug(f"[LOGIN][STAY_SIGNED_IN] Trying selector: {selector}")
                    button = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    self.logger.debug(f"[LOGIN][STAY_SIGNED_IN] Found button with selector: {selector}")
                    break
                except TimeoutException:
                    self.logger.debug(f"[LOGIN][STAY_SIGNED_IN] Selector {selector} timed out")
                    continue
            
            if button:
                button.click()
                self.logger.info(f"[LOGIN][STAY_SIGNED_IN] Clicked '{button_name}' on Stay signed in prompt")
                return {"status": "success"}
            else:
                raise TimeoutException(f"{button_name} button not found")
            
        except TimeoutException:
            # Prompt didn't appear - not an error, just means it wasn't shown
            self.logger.debug("[LOGIN][STAY_SIGNED_IN] Prompt did not appear (timeout)")
            return {
                "status": "skipped",
                "message": "Stay signed in prompt did not appear"
            }
        except Exception as e:
            self.logger.warning(f"[LOGIN][STAY_SIGNED_IN] Error handling prompt: {e}")
            return {
                "status": "error",
                "message": "Failed to handle Stay signed in prompt",
                "error": str(e)
            }
    
    def _enter_wwid(self, login_id: str, timeout: int) -> Dict[str, Any]:
        """
        Enter WWID (login_id) on Compass-specific page.
        
        Based on working implementation from DevCompass login_page.py.
        Uses Compass-specific selectors for the WWID input field.
        """
        try:
            self.logger.info(f"[LOGIN][WWID] Looking for WWID input field...")
            
            # Wait for WWID input field (Compass-specific selector)
            # Selector from working code: input[class*='fleet-operations-pwa__text-input__']
            wwid_field = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[class*='fleet-operations-pwa__text-input__']"))
            )
            
            if not wwid_field.is_displayed() or not wwid_field.is_enabled():
                self.logger.warning("[LOGIN][WWID] Field not ready, waiting...")
                wwid_field = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                    lambda d: (
                        (field := d.find_element(By.CSS_SELECTOR, "input[class*='fleet-operations-pwa__text-input__']"))
                        and field.is_displayed()
                        and field.is_enabled()
                        and field
                    )
                )
            
            wwid_field.clear()
            wwid_field.send_keys(login_id)
            self.logger.info(f"[LOGIN][WWID] Entered WWID: {login_id}")
            
            # Click Submit button (Compass-specific selector)
            # Selector from working code: //button[.//span[normalize-space()='Submit']]
            self.logger.debug("[LOGIN][WWID] Looking for Submit button...")
            submit_button = WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[.//span[normalize-space()='Submit']]"))
            )
            submit_button.click()
            self.logger.info("[LOGIN][WWID] Clicked Submit button")
            
            # Wait a moment for redirect after WWID submission
            import time
            time.sleep(2)
            
            # Log current URL after WWID submission
            current_url_after_wwid = self.driver.current_url
            self.logger.info(f"[LOGIN][WWID] After submit, current URL: {current_url_after_wwid}")
            
            return {"status": "success"}
            
        except TimeoutException:
            self.logger.error("[LOGIN][WWID] Timeout waiting for WWID field or Submit button")
            return {
                "status": "error",
                "message": "Timeout waiting for WWID field",
                "error": "WWID field not found within timeout"
            }
        except Exception as e:
            self.logger.error(f"[LOGIN][WWID] Error entering WWID: {e}")
            return {
                "status": "error",
                "message": "Failed to enter WWID",
                "error": str(e)
            }
    
    def _verify_login_success(self, expected_domain: str, timeout: int) -> Dict[str, Any]:
        """Verify login succeeded by checking for domain in URL."""
        try:
            # Wait for URL to change to expected domain
            WebDriverWait(self.driver, 10, poll_frequency=0.5).until(
                lambda d: expected_domain in d.current_url
            )
            self.logger.debug(f"[LOGIN][VERIFY] Successfully redirected to: {self.driver.current_url}")
            return {"status": "success"}
            
        except TimeoutException:
            current_url = self.driver.current_url
            self.logger.warning(f"[LOGIN][VERIFY] Did not redirect to expected domain. Current: {current_url}")
            return {
                "status": "error",
                "message": "Login verification failed",
                "error": f"Expected domain '{expected_domain}' not found in URL: {current_url}"
            }
        except Exception as e:
            self.logger.error(f"[LOGIN][VERIFY] Error verifying login: {e}")
            return {
                "status": "error",
                "message": "Failed to verify login success",
                "error": str(e)
            }
