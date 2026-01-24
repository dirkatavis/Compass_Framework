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
