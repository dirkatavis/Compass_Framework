"""
Page Detector Classes for Authentication Flow.

Provides reusable, testable page detection logic for different authentication
states (login page, WWID page, authenticated app page).
"""
from typing import Optional
import logging
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Default timeout and polling configuration
DEFAULT_DETECTION_TIMEOUT = 10  # seconds
DEFAULT_POLL_FREQUENCY = 0.5  # seconds


class PageDetector:
    """
    Base class for page detection with common wait logic.
    
    Provides a reusable pattern for detecting page elements using Selenium
    Expected Conditions. Subclasses define specific page selectors and logic.
    """
    
    def __init__(self, driver: WebDriver, timeout: float = DEFAULT_DETECTION_TIMEOUT, 
                 logger: Optional[logging.Logger] = None):
        """
        Initialize page detector.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Maximum time to wait for element detection (seconds)
            logger: Optional logger for detection events
        """
        self.driver = driver
        self.timeout = timeout
        self.poll_frequency = DEFAULT_POLL_FREQUENCY
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    def _wait_for_element(self, selector: str, by: By = By.CSS_SELECTOR) -> Optional[any]:
        """
        Wait for element to be present and displayed.
        
        Uses Expected Conditions for efficient polling. Returns immediately
        when element is found rather than waiting full timeout.
        
        Args:
            selector: CSS selector or other locator string
            by: Selenium By locator type (default: CSS_SELECTOR)
        
        Returns:
            WebElement if found and displayed, None otherwise
        """
        try:
            element = WebDriverWait(
                self.driver, 
                self.timeout, 
                poll_frequency=self.poll_frequency
            ).until(
                EC.presence_of_element_located((by, selector))
            )
            
            # Verify element is actually displayed
            if element and element.is_displayed():
                return element
            else:
                self.logger.debug(f"Element found but not displayed: {selector}")
                return None
                
        except TimeoutException:
            self.logger.debug(f"Element not found within {self.timeout}s: {selector}")
            return None
        except Exception as e:
            self.logger.warning(f"Error waiting for element '{selector}': {e}")
            return None
    
    def is_present(self) -> bool:
        """
        Check if this page type is currently displayed.
        
        Must be implemented by subclasses to define specific detection logic.
        
        Returns:
            bool: True if page is detected, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_present()")


class LoginPageDetector(PageDetector):
    """
    Detects Microsoft SSO login page.
    
    Looks for email/username input fields that indicate a login page is displayed.
    Covers both Microsoft SSO and standard username/email entry forms.
    """
    
    # CSS selectors for login page indicators
    SELECTORS = [
        'input[type="email"]',      # Standard email input
        'input[name="loginfmt"]',   # Microsoft-specific login format
        'input[name="username"]',   # Standard username input
        '#i0116'                    # Microsoft-specific element ID
    ]
    
    def is_present(self) -> bool:
        """
        Check if login page is currently displayed.
        
        Returns:
            bool: True if any login field is detected, False otherwise
        """
        # Combine selectors with OR logic (comma-separated CSS)
        combined_selector = ','.join(self.SELECTORS)
        element = self._wait_for_element(combined_selector)
        
        if element:
            self.logger.debug(f"Login page detected - element: <{element.tag_name}>")
            return True
        
        return False


class WWIDPageDetector(PageDetector):
    """
    Detects WWID-only page (SSO auto-login scenario).
    
    This page appears when SSO authentication succeeds automatically but
    the application requires additional WWID (employee ID) entry.
    Distinguishes from full login by verifying NO Microsoft SSO fields present.
    """
    
    # Selector for WWID input field
    WWID_SELECTOR = "input[class*='fleet-operations-pwa__text-input__']"
    
    # Selectors that should NOT be present (Microsoft SSO fields)
    EXCLUSION_SELECTORS = [
        'input[type="email"]',
        'input[name="loginfmt"]',
        'input[name="username"]',
        '#i0116'
    ]
    
    def is_present(self) -> bool:
        """
        Check if WWID-only page is currently displayed.
        
        Returns True only if:
        1. WWID input field is present AND
        2. No Microsoft SSO login fields are present
        
        Returns:
            bool: True if WWID-only page detected, False otherwise
        """
        # First check for WWID field
        wwid_element = self._wait_for_element(self.WWID_SELECTOR)
        
        if not wwid_element:
            self.logger.debug("WWID page not detected - no WWID field found")
            return False
        
        # WWID field found - verify NO SSO fields present
        combined_exclusions = ','.join(self.EXCLUSION_SELECTORS)
        
        try:
            # Quick check - don't wait long for exclusions
            sso_element = self.driver.find_element(By.CSS_SELECTOR, combined_exclusions)
            if sso_element and sso_element.is_displayed():
                self.logger.debug("WWID page not detected - SSO fields also present")
                return False
        except Exception:
            # No SSO fields found - this is WWID-only
            pass
        
        self.logger.debug("WWID-only page detected (auto-login scenario)")
        return True


class AuthenticatedPageDetector(PageDetector):
    """
    Detects if user is already authenticated in the application.
    
    Looks for app-specific elements that only appear after successful authentication,
    such as navigation elements, action buttons, or entity displays.
    """
    
    # CSS selectors for authenticated app indicators
    SELECTORS = [
        "button:has(span[contains(., 'Add Work Item')])",  # Primary app action button
        "div[class*='bp6-entity-title']",                  # Entity title elements
        "div[class*='fleet-operations']",                  # App-specific components
        "nav[class*='navbar']"                             # Navigation bar
    ]
    
    def is_present(self) -> bool:
        """
        Check if application is loaded and user is authenticated.
        
        Returns:
            bool: True if app elements detected (authenticated), False otherwise
        """
        # Combine selectors with OR logic
        combined_selector = ','.join(self.SELECTORS)
        element = self._wait_for_element(combined_selector)
        
        if element:
            self.logger.debug(f"Authenticated app detected - element: <{element.tag_name}>")
            return True
        
        return False
