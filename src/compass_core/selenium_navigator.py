"""
SeleniumNavigator - Concrete implementation of Navigator protocol.

This module provides a Selenium WebDriver-based implementation of the Navigator
interface, enabling web navigation and page verification operations.
"""
from typing import Dict, Any, Optional, Tuple
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver

from .navigation import Navigator


class SeleniumNavigator(Navigator):
    """
    Selenium WebDriver implementation of Navigator protocol.
    
    This class provides concrete navigation functionality using Selenium WebDriver,
    implementing the Navigator interface for dependency injection compatibility.
    
    Example usage:
        driver = webdriver.Chrome()
        navigator = SeleniumNavigator(driver)
        result = navigator.navigate_to("https://example.com")
        verification = navigator.verify_page(expected_url="https://example.com")
    """
    
    def __init__(self, driver: WebDriver):
        """
        Initialize SeleniumNavigator with WebDriver instance.
        
        Args:
            driver: Selenium WebDriver instance for browser automation
        """
        self.driver = driver
    
    def navigate_to(self, url: str, label: str = "page", verify: bool = True, timeout: int = 15) -> Dict[str, Any]:
        """
        Navigate to a URL using Selenium WebDriver.
        
        Args:
            url: Target URL to navigate to
            label: Descriptive label for the page (for logging/reporting)
            verify: Whether to verify page load after navigation
            timeout: Maximum time to wait for operations (default 15s)
        
        Returns:
            Dictionary with navigation result:
            - status: 'success' or 'failure' 
            - error: Error message if navigation failed
            - url: The URL that was navigated to
            - label: The page label that was provided
        """
        try:
            # Perform navigation
            self.driver.get(url)
            
            # Optionally verify the page loaded correctly
            if verify:
                verify_result = self.verify_page(url=url, timeout=timeout)
                if verify_result['status'] == 'failure':
                    return {
                        'status': 'failure',
                        'error': f"Navigation succeeded but verification failed: {verify_result.get('error', 'unknown')}",
                        'url': url,
                        'verification_details': verify_result
                    }
            
            return {
                'status': 'success',
                'url': url,
                'label': label,
                'current_url': self.driver.current_url
            }
            
        except Exception as e:
            return {
                'status': 'failure',
                'error': f"Navigation failed: {str(e)}",
                'url': url,
                'label': label
            }
    
    def verify_page(self, 
                   url: Optional[str] = None, 
                   check_locator: Optional[Tuple[str, str]] = None, 
                   timeout: int = 15,
                   match: str = "prefix") -> Dict[str, Any]:
        """
        Verify that the current page has loaded correctly.
        
        Args:
            url: Optional URL to verify against current URL
            check_locator: Optional element locator to verify presence  
            timeout: Maximum time to wait for page to load (default 15s)
        
        Returns:
            Dictionary with verification result:
            - status: 'success' or 'failure'
            - error: Error message if verification failed  
            - current_url: The actual current URL
            - expected_url: The expected URL (if provided)
        """
        try:
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            current_url = self.driver.current_url
            
            # Check URL match if expected URL provided
            if url:
                try:
                    from urllib.parse import urlparse
                    if match == "exact":
                        url_match = (current_url == url)
                    elif match == "domain":
                        expected_base = urlparse(url)
                        actual_base = urlparse(current_url)
                        url_match = (
                            expected_base.scheme == actual_base.scheme and
                            expected_base.netloc == actual_base.netloc
                        )
                    else:  # 'prefix' default
                        url_match = current_url.startswith(url)
                except Exception:
                    # Fallback to prefix match on parse errors
                    url_match = current_url.startswith(url)

                if not url_match:
                    return {
                        'status': 'failure',
                        'error': 'url_mismatch',
                        'expected': url,
                        'actual': current_url,
                        'match': match
                    }
            
            # Check for optional element presence
            if check_locator:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(check_locator)
                )
            
            return {
                'status': 'success',
                'current_url': current_url,
                **({"expected_url": url} if url else {}),
                **({"match": match} if url else {})
            }
            
        except Exception as e:
            return {
                'status': 'failure',
                'error': f"Page verification failed: {str(e)}",
                'current_url': getattr(self.driver, 'current_url', 'unknown')
            }