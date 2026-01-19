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
        Authenticate with Microsoft SSO.
        
        Args:
            username: User email address
            password: User password
            login_url: Microsoft login page URL
            **kwargs: Additional parameters (login_id, timeout, verify_domain)
        
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
        
        self.logger.info(f"[LOGIN] Starting authentication flow for: {username}")
        
        try:
            # Step 1: Navigate to login URL
            nav_result = self.navigator.navigate_to(login_url, verify=False, timeout=timeout)
            if nav_result.get("status") != "success":
                self.logger.error(f"[LOGIN] Failed to navigate to login URL: {nav_result.get('error')}")
                return {
                    "status": "error",
                    "message": f"Failed to navigate to login URL",
                    "error": nav_result.get("error", "Unknown navigation error")
                }
            
            self.logger.debug(f"[LOGIN] Navigated to: {login_url}")
            
            # Step 2: Enter username
            username_result = self._enter_username(username, timeout)
            if username_result.get("status") != "success":
                return username_result
            
            # Step 3: Enter password
            password_result = self._enter_password(password, timeout)
            if password_result.get("status") != "success":
                return password_result
            
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
            username_field = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"], input[name="loginfmt"]'))
            )
            
            if not username_field.is_displayed() or not username_field.is_enabled():
                self.logger.warning("[LOGIN][USERNAME] Field not ready, waiting...")
                username_field = WebDriverWait(self.driver, timeout).until(
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
            next_button = WebDriverWait(self.driver, timeout).until(
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
            password_field = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"], input[name="passwd"]'))
            )
            
            if not password_field.is_displayed() or not password_field.is_enabled():
                self.logger.warning("[LOGIN][PASSWORD] Field not ready, waiting...")
                password_field = WebDriverWait(self.driver, timeout).until(
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
            signin_button = WebDriverWait(self.driver, timeout).until(
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
    
    def _verify_login_success(self, expected_domain: str, timeout: int) -> Dict[str, Any]:
        """Verify login succeeded by checking for domain in URL."""
        try:
            # Wait for URL to change to expected domain
            WebDriverWait(self.driver, timeout).until(
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
