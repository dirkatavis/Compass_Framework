"""
SeleniumNavigator - Concrete implementation of Navigator protocol.

This module provides a Selenium WebDriver-based implementation of the Navigator
interface, enabling web navigation and page verification operations.
"""
from typing import Dict, Any, Optional, Tuple
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
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
    
    def navigate_to(self, url: str, verify: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Navigate to a URL using Selenium WebDriver.
        
        Args:
            url: Target URL to navigate to
            verify: Whether to verify page load after navigation
            **kwargs: Additional parameters (timeout, etc.)
        
        Returns:
            Dictionary with navigation result:
            - status: 'success' or 'failure' 
            - error: Error message if navigation failed
            - url: The URL that was navigated to
        """
        try:
            # Perform navigation
            self.driver.get(url)
            
            # Optionally verify the page loaded correctly
            if verify:
                timeout = kwargs.get('timeout', 15)
                verify_result = self.verify_page(expected_url=url, timeout=timeout)
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
                'current_url': self.driver.current_url
            }
            
        except Exception as e:
            return {
                'status': 'failure',
                'error': f"Navigation failed: {str(e)}",
                'url': url
            }
    
    def verify_page(self, expected_url: Optional[str] = None, timeout: int = 15, **kwargs) -> Dict[str, Any]:
        """
        Verify that the current page has loaded correctly.
        
        Args:
            expected_url: Optional URL to verify against current URL
            timeout: Maximum time to wait for page to load (default 15s)
            **kwargs: Additional verification parameters
        
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
            if expected_url and not current_url.startswith(expected_url):
                return {
                    'status': 'failure',
                    'error': 'url_mismatch',
                    'expected': expected_url,
                    'actual': current_url
                }
            
            # Check for optional element presence
            check_locator = kwargs.get('check_locator')
            if check_locator:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(check_locator)
                )
            
            return {
                'status': 'success',
                'current_url': current_url,
                **({"expected_url": expected_url} if expected_url else {})
            }
            
        except Exception as e:
            return {
                'status': 'failure',
                'error': f"Page verification failed: {str(e)}",
                'current_url': getattr(self.driver, 'current_url', 'unknown')
            }