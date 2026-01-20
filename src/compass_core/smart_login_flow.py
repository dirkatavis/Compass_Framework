"""
Smart Login Flow with conditional authentication.

Automatically detects if login is required (SSO cache miss) or if 
the user is already authenticated (SSO cache hit), performing login 
only when necessary.
"""
from typing import Dict, Any
import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from compass_core.login_flow import LoginFlow
from compass_core.navigation import Navigator

# WebDriver wait configuration
DEFAULT_WAIT_TIMEOUT = 10  # seconds
DEFAULT_POLL_FREQUENCY = 0.5  # seconds


class SmartLoginFlow(LoginFlow):
    """
    Intelligent login flow that only authenticates when necessary.
    
    Implements LoginFlow protocol with smart SSO cache detection.
    Interprets the 'url' parameter as the target application URL.
    
    Workflow:
    1. Navigate to target application URL
    2. Detect if redirected to login page
    3. If login page: perform authentication
    4. If already authenticated (SSO): skip login
    
    This handles both SSO cache hits (session active) and cache misses
    (login required) transparently.
    """
    
    def __init__(
        self,
        driver: WebDriver,
        navigator: Navigator,
        login_flow: LoginFlow,
        logger: logging.Logger = None
    ):
        """
        Initialize smart login flow.
        
        Args:
            driver: Selenium WebDriver instance
            navigator: Navigator protocol implementation
            login_flow: LoginFlow implementation for authentication
            logger: Optional logger instance
        """
        self.driver = driver
        self.navigator = navigator
        self.login_flow = login_flow
        self.logger = logger or logging.getLogger(__name__)
    
    def authenticate(
        self,
        username: str,
        password: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Smart authenticate: navigate to app, login only if needed.
        
        Args:
            username: User email/username
            password: User password
            url: Target application URL
            **kwargs: Additional parameters:
                - login_id: str (optional)
                - timeout: int (default: 30)
        
        Returns:
            Dict with authentication result:
            {
                "status": "success" | "error",
                "message": str,
                "authenticated": bool (True if login performed, False if SSO active),
                "error": str (if status="error")
            }
        """
        timeout = kwargs.get('timeout', 30)
        
        self.logger.info(f"[SMART_AUTH] Starting smart authentication for: {username}")
        self.logger.info(f"[SMART_AUTH] Target app URL: {url}")
        
        try:
            # Step 1: Navigate to target application
            self.logger.debug("[SMART_AUTH] Step 1: Navigate to application")
            
            # Handle potential alerts before navigation
            from selenium.common.exceptions import UnexpectedAlertPresentException
            from selenium.webdriver.common.alert import Alert
            
            try:
                nav_result = self.navigator.navigate_to(url, verify=False, timeout=timeout)
            except UnexpectedAlertPresentException:
                self.logger.warning("[SMART_AUTH] Alert detected during navigation, dismissing...")
                try:
                    alert = Alert(self.driver)
                    alert_text = alert.text
                    self.logger.info(f"[SMART_AUTH] Alert text: {alert_text}")
                    alert.accept()  # Dismiss alert
                except Exception as e:
                    self.logger.warning(f"[SMART_AUTH] Failed to dismiss alert: {e}")
                
                # Retry navigation after dismissing alert
                nav_result = self.navigator.navigate_to(url, verify=False, timeout=timeout)
            
            if nav_result.get("status") != "success":
                self.logger.error(f"[SMART_AUTH] Failed to navigate to app: {nav_result.get('error')}")
                return {
                    "status": "error",
                    "message": "Failed to navigate to application",
                    "authenticated": False,
                    "error": nav_result.get("error", "Navigation failed")
                }
            
            current_url = self.driver.current_url
            self.logger.debug(f"[SMART_AUTH] Current URL after navigation: {current_url}")
            
            # Give the page a moment to settle and trigger any SSO redirects
            import time
            time.sleep(2)
            
            # Check if URL changed after waiting (indicates redirect in progress)
            new_url = self.driver.current_url
            if new_url != current_url:
                self.logger.debug(f"[SMART_AUTH] URL changed after wait: {new_url}")
                current_url = new_url
                # Wait a bit more for redirect to complete
                time.sleep(2)
            
            # Step 2: Detect if we're on a login page
            self.logger.debug("[SMART_AUTH] Step 2: Detect login page")
            login_required = self._detect_login_page(timeout=DEFAULT_WAIT_TIMEOUT)  # Use global constant
            
            if not login_required:
                # SSO session active - already authenticated
                self.logger.info("[SMART_AUTH] SSO session active, user already authenticated")
                return {
                    "status": "success",
                    "message": f"Already authenticated via SSO (session active)",
                    "authenticated": False  # Did not need to login
                }
            
            # Step 3: Login required - perform authentication
            self.logger.info("[SMART_AUTH] Login page detected, performing authentication")
            
            # We're already on the login page after navigation, so skip re-navigation
            # Just pass the current URL for reference
            auth_result = self.login_flow.authenticate(
                username=username,
                password=password,
                url=current_url,
                skip_navigation=True,  # Already navigated - avoid double load
                **kwargs
            )
            
            if auth_result.get("status") != "success":
                self.logger.error(f"[SMART_AUTH] Authentication failed: {auth_result.get('error')}")
                return {
                    "status": "error",
                    "message": "Login failed",
                    "authenticated": False,
                    "error": auth_result.get("error", "Authentication failed")
                }
            
            self.logger.info(f"[SMART_AUTH] Authentication successful: {auth_result.get('message')}")
            return {
                "status": "success",
                "message": f"Authenticated successfully (SSO cache miss)",
                "authenticated": True  # Login was performed
            }
            
        except Exception as e:
            self.logger.error(f"[SMART_AUTH] Unexpected error: {e}")
            return {
                "status": "error",
                "message": "Smart authentication failed",
                "authenticated": False,
                "error": str(e)
            }
    
    def _detect_login_page(self, timeout: int = DEFAULT_WAIT_TIMEOUT) -> bool:
        """
        Detect if current page is a login page.
        
        Checks for presence of common login page elements:
        - Username/email input field
        - Password input field
        - WWID/login_id input field
        - Microsoft SSO indicators
        
        Args:
            timeout: Maximum time to wait for detection (seconds)
        
        Returns:
            bool: True if login page detected, False if already authenticated
        """
        try:
            # Check for Microsoft SSO login indicators
            # Look for username/email field (most reliable indicators)
            # Use a combined selector to check all at once instead of sequentially
            combined_selector = ','.join([
                'input[type="email"]',
                'input[name="loginfmt"]',
                'input[name="username"]',
                '#i0116'  # Microsoft-specific ID
            ])
            
            try:
                element = WebDriverWait(self.driver, timeout, poll_frequency=DEFAULT_POLL_FREQUENCY).until(
                    lambda d: d.find_element(By.CSS_SELECTOR, combined_selector)
                )
                
                if element and element.is_displayed():
                    self.logger.debug(f"[SMART_AUTH][DETECT] Login field found")
                    return True
                        
            except TimeoutException:
                # No login fields found - likely already authenticated
                self.logger.debug("[SMART_AUTH][DETECT] No login fields found - SSO session active")
                return False
            
        except Exception as e:
            self.logger.warning(f"[SMART_AUTH][DETECT] Error detecting login page: {e}")
            # Default to assuming login required (safer)
            return True
