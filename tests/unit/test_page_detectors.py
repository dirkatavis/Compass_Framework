"""
Unit tests for Page Detector classes.

Tests the page detection logic in isolation using mock WebDriver instances.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from compass_core.page_detectors import (
    PageDetector,
    LoginPageDetector,
    WWIDPageDetector,
    AuthenticatedPageDetector
)


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


class TestLoginPageDetector(unittest.TestCase):
    """Test the LoginPageDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_driver = Mock()
        self.detector = LoginPageDetector(self.mock_driver, timeout=1)
    
    @patch.object(LoginPageDetector, '_wait_for_element')
    def test_is_present_when_login_field_found(self, mock_wait):
        """Test is_present returns True when login field detected."""
        mock_element = Mock()
        mock_element.tag_name = 'input'
        mock_wait.return_value = mock_element
        
        result = self.detector.is_present()
        
        self.assertTrue(result)
        mock_wait.assert_called_once()
    
    @patch.object(LoginPageDetector, '_wait_for_element')
    def test_is_present_when_no_login_field(self, mock_wait):
        """Test is_present returns False when no login field found."""
        mock_wait.return_value = None
        
        result = self.detector.is_present()
        
        self.assertFalse(result)
    
    def test_selectors_defined(self):
        """Test that login selectors are properly defined."""
        self.assertIsInstance(LoginPageDetector.SELECTORS, list)
        self.assertGreater(len(LoginPageDetector.SELECTORS), 0)
        self.assertIn('input[type="email"]', LoginPageDetector.SELECTORS)


class TestWWIDPageDetector(unittest.TestCase):
    """Test the WWIDPageDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_driver = Mock()
        self.detector = WWIDPageDetector(self.mock_driver, timeout=1)
    
    @patch.object(WWIDPageDetector, '_wait_for_element')
    def test_is_present_wwid_only(self, mock_wait):
        """Test is_present returns True for WWID-only page (no SSO fields)."""
        # WWID field found
        mock_wwid = Mock()
        mock_wait.return_value = mock_wwid
        
        # No SSO fields found
        self.mock_driver.find_element.side_effect = Exception("Element not found")
        
        result = self.detector.is_present()
        
        self.assertTrue(result)
    
    @patch.object(WWIDPageDetector, '_wait_for_element')
    def test_is_present_no_wwid_field(self, mock_wait):
        """Test is_present returns False when WWID field not found."""
        mock_wait.return_value = None
        
        result = self.detector.is_present()
        
        self.assertFalse(result)
    
    @patch.object(WWIDPageDetector, '_wait_for_element')
    def test_is_present_wwid_and_sso_fields(self, mock_wait):
        """Test is_present returns False when both WWID and SSO fields present."""
        # WWID field found
        mock_wwid = Mock()
        mock_wait.return_value = mock_wwid
        
        # SSO field also found (not WWID-only)
        mock_sso = Mock()
        mock_sso.is_displayed.return_value = True
        self.mock_driver.find_element.return_value = mock_sso
        
        result = self.detector.is_present()
        
        self.assertFalse(result)
    
    def test_selectors_defined(self):
        """Test that WWID selectors are properly defined."""
        self.assertIsInstance(WWIDPageDetector.WWID_SELECTOR, str)
        self.assertIsInstance(WWIDPageDetector.EXCLUSION_SELECTORS, list)
        self.assertGreater(len(WWIDPageDetector.EXCLUSION_SELECTORS), 0)


class TestAuthenticatedPageDetector(unittest.TestCase):
    """Test the AuthenticatedPageDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_driver = Mock()
        self.detector = AuthenticatedPageDetector(self.mock_driver, timeout=1)
    
    @patch.object(AuthenticatedPageDetector, '_wait_for_element')
    def test_is_present_when_app_element_found(self, mock_wait):
        """Test is_present returns True when app element detected."""
        mock_element = Mock()
        mock_element.tag_name = 'button'
        mock_wait.return_value = mock_element
        
        result = self.detector.is_present()
        
        self.assertTrue(result)
    
    @patch.object(AuthenticatedPageDetector, '_wait_for_element')
    def test_is_present_when_no_app_element(self, mock_wait):
        """Test is_present returns False when no app element found."""
        mock_wait.return_value = None
        
        result = self.detector.is_present()
        
        self.assertFalse(result)
    
    def test_selectors_defined(self):
        """Test that authenticated page selectors are properly defined."""
        self.assertIsInstance(AuthenticatedPageDetector.SELECTORS, list)
        self.assertGreater(len(AuthenticatedPageDetector.SELECTORS), 0)


if __name__ == '__main__':
    unittest.main()
