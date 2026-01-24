"""
Smart Login Flow with conditional authentication.

Automatically detects if login is required (SSO cache miss) or if 
the user is already authenticated (SSO cache hit), performing login 
only when necessary.
"""
from typing import Dict, Any
import logging
import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
            self.logger.info(f"[SMART_AUTH] About to wait for SSO redirects...")
            
            # Give the page a moment to settle and trigger any SSO redirects
            time.sleep(2)
            
            self.logger.info(f"[SMART_AUTH] After initial 2s wait")
            
            # Check if URL changed after waiting (indicates redirect in progress)
            new_url = self.driver.current_url
            if new_url != current_url:
                self.logger.debug(f"[SMART_AUTH] URL changed after wait: {new_url}")
                current_url = new_url
                # Wait a bit more for redirect to complete
                time.sleep(2)
            
            # Wait for WWID tab to open (appears after SSO completes)
            # Reduced timeout since tabs open quickly if they're going to appear
            self.logger.info("[SMART_AUTH] Waiting for potential WWID tab to open...")
            max_wait = 1  # Quick check - tabs open instantly if they will
            all_windows = self.driver.window_handles
            if len(all_windows) == 1:
                time.sleep(max_wait)  # Single brief wait
                all_windows = self.driver.window_handles
                if len(all_windows) > 1:
                    self.logger.info(f"[SMART_AUTH] New tab detected after {max_wait}s")
                else:
                    self.logger.debug(f"[SMART_AUTH] No new tab appeared after {max_wait}s")
            
            # Step 2: Detect authentication scenario
            self.logger.debug("[SMART_AUTH] Step 2: Detect authentication scenario")
            self.logger.info(f"[SMART_AUTH] Current URL for detection: {self.driver.current_url}")
            self.logger.info(f"[SMART_AUTH] Page title: {self.driver.title}")
            
            # Check if WWID page opened in a new tab
            all_windows = self.driver.window_handles
            self.logger.info(f"[SMART_AUTH] Window/tab count: {len(all_windows)}")
            
            if len(all_windows) > 1:
                # Switch to the new tab (likely WWID page)
                self.driver.switch_to.window(all_windows[-1])
                self.logger.info(f"[SMART_AUTH] Switched to new tab/window")
                self.logger.info(f"[SMART_AUTH] New tab URL: {self.driver.current_url}")
                self.logger.info(f"[SMART_AUTH] New tab title: {self.driver.title}")
            
            # Check for WWID-only page first (auto-login scenario)
            self.logger.debug("[SMART_AUTH] Checking for WWID-only page...")
            wwid_only = self._detect_wwid_only_page(timeout=0.5)  # EC makes this instant
            
            if wwid_only:
                # Auto-login succeeded, only WWID entry needed
                self.logger.info("[SMART_AUTH] Auto-login detected (WWID-only page)")
                
                # Get login_id from kwargs
                login_id = kwargs.get('login_id')
                if not login_id:
                    self.logger.warning("[SMART_AUTH] WWID page detected but no login_id provided")
                    return {
                        "status": "error",
                        "message": "WWID required but not provided",
                        "authenticated": False,
                        "error": "login_id parameter missing"
                    }
                
                # Handle WWID entry directly
                auth_result = self.login_flow.authenticate(
                    username=username,
                    password=password,
                    url=current_url,
                    skip_navigation=True,
                    **kwargs
                )
                
                if auth_result.get("status") != "success":
                    return {
                        "status": "error",
                        "message": "WWID entry failed",
                        "authenticated": False,
                        "error": auth_result.get("error", "WWID entry failed")
                    }
                
                self.logger.info("[SMART_AUTH] Auto-login with WWID entry successful")
                return {
                    "status": "success",
                    "message": "Authenticated via auto-login (WWID-only)",
                    "authenticated": True
                }
            
            # Check for Microsoft SSO login page
            self.logger.debug("[SMART_AUTH] Checking for login page (SSO fields)...")
            login_required = self._detect_login_page(timeout=DEFAULT_WAIT_TIMEOUT)
            self.logger.info(f"[SMART_AUTH] Login required: {login_required}")
            
            if not login_required:
                # Fully authenticated - no login or WWID needed
                self.logger.info("[SMART_AUTH] Fully authenticated, no action needed")
                self.logger.info(f"[SMART_AUTH] Final URL: {self.driver.current_url}")
                return {
                    "status": "success",
                    "message": f"Already authenticated via SSO (session active)",
                    "authenticated": False  # Did not need to login
                }
            
            # Step 3: Standard login required - perform full authentication
            self.logger.info("[SMART_AUTH] Standard login page detected, performing authentication")
            
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
        Detect if current page is a login page or already authenticated.
        
        Efficiently waits for EITHER condition (whichever appears first):
        - Login/WWID fields present → login required
        - App indicators present → already authenticated
        
        Uses polling to handle SPA rendering - no reliance on document.readyState
        which doesn't account for dynamic/async content in modern SPAs.
        
        Args:
            timeout: Maximum time to wait for detection (seconds)
        
        Returns:
            bool: True if login/WWID page detected, False if already fully authenticated
        """
        start_time = time.time()
        
        try:
            # Login page indicators (Microsoft SSO + WWID)
            login_selector = ','.join([
                'input[type="email"]',
                'input[name="loginfmt"]',
                'input[name="username"]',
                '#i0116',  # Microsoft-specific ID
                "input[class*='fleet-operations-pwa__text-input__']"  # WWID field
            ])
            
            # App-authenticated indicators (Compass-specific elements that only appear when logged in)
            # These are rendered by the SPA after successful authentication
            app_selector = ','.join([
                "button:has(span[contains(., 'Add Work Item')])",  # Main app button
                "div[class*='bp6-entity-title']",  # Entity title (appears in app)
                "div[class*='fleet-operations']",  # App-specific components
                "nav[class*='navbar']",  # Navigation bar
            ])
            
            self.logger.info(f"[SMART_AUTH][DETECT] Starting either/or detection (timeout={timeout}s, poll={DEFAULT_POLL_FREQUENCY}s)")
            self.logger.debug(f"[SMART_AUTH][DETECT] Current URL: {self.driver.current_url}")
            self.logger.debug(f"[SMART_AUTH][DETECT] Login selectors: {login_selector[:100]}...")
            self.logger.debug(f"[SMART_AUTH][DETECT] App selectors: {app_selector[:100]}...")
            
            try:
                # Wait for EITHER login fields OR app elements (whichever appears first)
                # Polling handles SPA rendering delays naturally
                self.logger.debug(f"[SMART_AUTH][DETECT] Polling started - checking every {DEFAULT_POLL_FREQUENCY}s")
                
                element = WebDriverWait(self.driver, timeout, poll_frequency=DEFAULT_POLL_FREQUENCY).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, login_selector)),
                        EC.presence_of_element_located((By.CSS_SELECTOR, app_selector))
                    )
                )
                
                elapsed = time.time() - start_time
                
                # Determine which condition was met
                if element and element.is_displayed():
                    elem_tag = element.tag_name
                    elem_type = element.get_attribute('type') or 'N/A'
                    elem_class = element.get_attribute('class') or ''
                    elem_text = element.text[:30] if element.text else ''
                    
                    # Check if it's a login field or app element
                    is_login_field = elem_tag == 'input' or 'text-input' in elem_class.lower()
                    
                    if is_login_field:
                        self.logger.info(f"[SMART_AUTH][DETECT] ✓ LOGIN PAGE detected in {elapsed:.2f}s")
                        self.logger.info(f"[SMART_AUTH][DETECT]   Element: <{elem_tag} type='{elem_type}' class='{elem_class[:50]}'>")
                        return True
                    else:
                        self.logger.info(f"[SMART_AUTH][DETECT] ✓ APP PAGE detected in {elapsed:.2f}s - already authenticated")
                        self.logger.info(f"[SMART_AUTH][DETECT]   Element: <{elem_tag}> text='{elem_text}' class='{elem_class[:50]}'>")
                        return False
                else:
                    elapsed = time.time() - start_time
                    self.logger.warning(f"[SMART_AUTH][DETECT] Element found but not displayed after {elapsed:.2f}s")
                    return False
                        
            except TimeoutException:
                # Neither login nor app elements found within timeout
                elapsed = time.time() - start_time
                self.logger.warning(f"[SMART_AUTH][DETECT] ✗ TIMEOUT after {elapsed:.2f}s - no login or app elements found")
                self.logger.warning(f"[SMART_AUTH][DETECT]   Current URL: {self.driver.current_url}")
                # Default to assuming login required (safer)
                return True
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(f"[SMART_AUTH][DETECT] ✗ ERROR after {elapsed:.2f}s: {e}")
            self.logger.error(f"[SMART_AUTH][DETECT]   Current URL: {self.driver.current_url}")
            # Default to assuming login required (safer)
            return True    
    def _detect_wwid_only_page(self, timeout: int = 2) -> bool:
        """
        Detect if current page is WWID-only (auto-login already succeeded).
        
        Checks for WWID input field WITHOUT Microsoft SSO login fields.
        
        Args:
            timeout: Maximum time to wait for detection (seconds)
        
        Returns:
            bool: True if WWID-only page detected, False otherwise
        """
        try:
            # Quick check for WWID field using EC for instant detection
            try:
                wwid_field = WebDriverWait(self.driver, timeout, poll_frequency=DEFAULT_POLL_FREQUENCY).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[class*='fleet-operations-pwa__text-input__']"))
                )
                
                if not (wwid_field and wwid_field.is_displayed()):
                    return False
                
                # WWID field found - now verify NO Microsoft SSO fields present
                try:
                    sso_field = self.driver.find_element(By.CSS_SELECTOR, 
                        'input[type="email"], input[name="loginfmt"], input[name="username"], #i0116')
                    if sso_field and sso_field.is_displayed():
                        # Both WWID and SSO fields present - not WWID-only
                        return False
                except Exception as exc:
                    self.logger.debug(f"[SMART_AUTH][DETECT] No SSO fields detected ({type(exc).__name__}: {exc})")
                    # No SSO fields - this is WWID-only
                
                self.logger.debug("[SMART_AUTH][DETECT] WWID-only page detected (auto-login)")
                return True
                
            except TimeoutException:
                return False
                
        except Exception as e:
            self.logger.warning(f"[SMART_AUTH][DETECT] Error detecting WWID-only page: {e}")
            return False