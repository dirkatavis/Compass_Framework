"""
Unit tests for Page Detector classes.

Tests the page detection logic in isolation using mock WebDriver instances.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from compass_core.page_detectors import PageDetector


class TestPageDetectorBase(unittest.TestCase):
    """Test the base PageDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_driver = Mock()
        self.detector = PageDetector(self.mock_driver, timeout=1)
    
    def test_initialization(self):
        """Test PageDetector initialization."""
        self.assertEqual(self.detector.driver, self.mock_driver)
        self.assertEqual(self.detector.timeout, 1)
        self.assertIsNotNone(self.detector.logger)
    
    def test_is_present_not_implemented(self):
        """Test that is_present raises NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            self.detector.is_present()
    
    @patch('compass_core.page_detectors.WebDriverWait')
    def test_wait_for_element_found_and_displayed(self, mock_wait_class):
        """Test _wait_for_element when element is found and displayed."""
        # Setup mock element
        mock_element = Mock()
        mock_element.is_displayed.return_value = True
        
        # Setup mock wait
        mock_wait = Mock()
        mock_wait.until.return_value = mock_element
        mock_wait_class.return_value = mock_wait
        
        # Test
        result = self.detector._wait_for_element('input[type="email"]')
        
        self.assertEqual(result, mock_element)
        mock_element.is_displayed.assert_called_once()
    
    @patch('compass_core.page_detectors.WebDriverWait')
    def test_wait_for_element_found_but_not_displayed(self, mock_wait_class):
        """Test _wait_for_element when element exists but not displayed."""
        # Setup mock element that's not displayed
        mock_element = Mock()
        mock_element.is_displayed.return_value = False
        
        # Setup mock wait
        mock_wait = Mock()
        mock_wait.until.return_value = mock_element
        mock_wait_class.return_value = mock_wait
        
        # Test
        result = self.detector._wait_for_element('input[type="email"]')
        
        self.assertIsNone(result)
    
    @patch('compass_core.page_detectors.WebDriverWait')
    def test_wait_for_element_timeout(self, mock_wait_class):
        """Test _wait_for_element when element not found (timeout)."""
        # Setup mock wait that times out
        mock_wait = Mock()
        mock_wait.until.side_effect = TimeoutException()
        mock_wait_class.return_value = mock_wait
        
        # Test
        result = self.detector._wait_for_element('input[type="email"]')
        
        self.assertIsNone(result)
    
    @patch('compass_core.page_detectors.WebDriverWait')
    def test_wait_for_element_exception(self, mock_wait_class):
        """Test _wait_for_element handles unexpected exceptions."""
        # Setup mock wait that raises exception
        mock_wait = Mock()
        mock_wait.until.side_effect = Exception("Unexpected error")
        mock_wait_class.return_value = mock_wait
        
        # Test
        result = self.detector._wait_for_element('input[type="email"]')
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
