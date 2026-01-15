"""
Tests for SeleniumNavigator concrete implementation.

This module validates that SeleniumNavigator properly implements the Navigator
protocol and handles Selenium WebDriver navigation operations correctly.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from compass_core.navigation import Navigator
from compass_core.selenium_navigator import SeleniumNavigator


class TestSeleniumNavigator(unittest.TestCase):
    """Test SeleniumNavigator concrete implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock WebDriver for testing
        self.mock_driver = Mock()
        self.mock_driver.get = Mock()
        self.mock_driver.current_url = "https://example.com/test"
        self.mock_driver.execute_script = Mock(return_value="complete")
        
        # Create SeleniumNavigator instance
        self.navigator = SeleniumNavigator(self.mock_driver)
    
    def test_navigator_protocol_compliance(self):
        """Test that SeleniumNavigator implements Navigator protocol."""
        # Verify isinstance check passes
        self.assertIsInstance(self.navigator, Navigator)
        
        # Verify required methods exist
        self.assertTrue(hasattr(self.navigator, 'navigate_to'))
        self.assertTrue(hasattr(self.navigator, 'verify_page'))
        self.assertTrue(callable(self.navigator.navigate_to))
        self.assertTrue(callable(self.navigator.verify_page))
    
    @patch('compass_core.selenium_navigator.WebDriverWait')
    def test_navigate_to_basic(self, mock_wait):
        """Test basic navigate_to functionality."""
        # Setup mock wait
        mock_wait.return_value.until = Mock()
        
        # Test basic navigation
        result = self.navigator.navigate_to("https://example.com", "test page")
        
        # Verify driver.get was called
        self.mock_driver.get.assert_called_once_with("https://example.com")
        
        # Verify return format
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        
    @patch('compass_core.selenium_navigator.WebDriverWait')  
    def test_navigate_to_success_status(self, mock_wait):
        """Test navigate_to returns success status."""
        # Setup successful wait
        mock_wait.return_value.until = Mock()
        
        result = self.navigator.navigate_to("https://example.com", "test page")
        
        # Should return success status
        self.assertEqual(result['status'], 'success')
        
    @patch('compass_core.selenium_navigator.WebDriverWait')
    def test_navigate_to_with_verification_disabled(self, mock_wait):
        """Test navigate_to with verification disabled."""
        mock_wait.return_value.until = Mock()
        
        result = self.navigator.navigate_to("https://example.com", "test page", verify=False)
        
        # Should still call driver.get
        self.mock_driver.get.assert_called_once_with("https://example.com")
        
        # Should return success without waiting for page load
        self.assertEqual(result['status'], 'success')
    
    @patch('compass_core.selenium_navigator.WebDriverWait')
    def test_verify_page_document_ready(self, mock_wait):
        """Test verify_page waits for document ready state."""
        # Setup mock wait behavior
        wait_instance = Mock()
        mock_wait.return_value = wait_instance
        
        result = self.navigator.verify_page()
        
        # Should create WebDriverWait with driver and default timeout
        mock_wait.assert_called_once_with(self.mock_driver, 15)
        
        # Should wait for document.readyState complete
        wait_instance.until.assert_called_once()
        
        # Verify the lambda function checks readyState
        wait_func = wait_instance.until.call_args[0][0]
        wait_func(self.mock_driver)
        self.mock_driver.execute_script.assert_called_with("return document.readyState")
        
        # Should return success
        self.assertEqual(result['status'], 'success')
        
    @patch('compass_core.selenium_navigator.WebDriverWait')
    def test_verify_page_url_mismatch(self, mock_wait):
        """Test verify_page detects URL mismatches."""
        # Setup wait mock
        mock_wait.return_value.until = Mock()
        
        # Set current_url to something different than expected
        self.mock_driver.current_url = "https://different.com"
        
        result = self.navigator.verify_page(expected_url="https://example.com")
        
        # Should return failure status for URL mismatch
        self.assertEqual(result['status'], 'failure')
        self.assertEqual(result['error'], 'url_mismatch')
        self.assertIn('expected', result)
        self.assertIn('actual', result)
    
    @patch('compass_core.selenium_navigator.WebDriverWait')
    def test_verify_page_url_match(self, mock_wait):
        """Test verify_page with matching URL."""
        mock_wait.return_value.until = Mock()
        
        # Set matching URL
        self.mock_driver.current_url = "https://example.com/page"
        
        result = self.navigator.verify_page(expected_url="https://example.com")
        
        # Should return success for URL that starts with expected
        self.assertEqual(result['status'], 'success')
    
    @patch('compass_core.selenium_navigator.WebDriverWait')
    def test_verify_page_custom_timeout(self, mock_wait):
        """Test verify_page with custom timeout."""
        mock_wait.return_value.until = Mock()
        
        self.navigator.verify_page(timeout=30)
        
        # Should use custom timeout
        mock_wait.assert_called_once_with(self.mock_driver, 30)
        
    def test_selenium_navigator_initialization(self):
        """Test SeleniumNavigator initialization."""
        navigator = SeleniumNavigator(self.mock_driver)
        
        # Should store driver reference
        self.assertEqual(navigator.driver, self.mock_driver)
        
    @patch('compass_core.selenium_navigator.WebDriverWait')
    def test_navigate_to_exception_handling(self, mock_wait):
        """Test navigate_to handles WebDriver exceptions."""
        # Setup driver to raise exception
        self.mock_driver.get.side_effect = Exception("Navigation failed")
        
        result = self.navigator.navigate_to("https://example.com", "test page")
        
        # Should return failure status
        self.assertEqual(result['status'], 'failure') 
        self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main()