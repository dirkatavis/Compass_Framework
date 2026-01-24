"""
Tests for SmartLoginFlow implementation.

This module validates the smart authentication logic that detects SSO cache state
and conditionally performs login only when necessary.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from compass_core.login_flow import LoginFlow
from compass_core.page_detectors import (
    LoginPageDetector,
    WWIDPageDetector,
    AuthenticatedPageDetector
)


class TestSmartLoginFlow(unittest.TestCase):
    """Test SmartLoginFlow smart authentication logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to handle optional selenium dependency
        try:
            from compass_core.smart_login_flow import SmartLoginFlow
            self.SmartLoginFlow = SmartLoginFlow
            self.selenium_available = True
        except ImportError:
            self.selenium_available = False
            self.skipTest("Selenium not available")
        
        # Create mocks
        self.mock_driver = Mock()
        self.mock_navigator = Mock()
        self.mock_base_login_flow = Mock()
        self.mock_logger = Mock()
        
        # Setup mock driver behavior
        self.mock_driver.current_url = "https://app.example.com/dashboard"
        self.mock_driver.title = "App Dashboard"
        self.mock_driver.window_handles = ["main-window"]  # Single window by default
        
        # Create instance
        self.smart_login = self.SmartLoginFlow(
            driver=self.mock_driver,
            navigator=self.mock_navigator,
            login_flow=self.mock_base_login_flow,
            logger=self.mock_logger
        )
    
    def test_protocol_compliance(self):
        """Test that SmartLoginFlow implements LoginFlow protocol."""
        self.assertIsInstance(self.smart_login, LoginFlow)
    
    def test_initialization(self):
        """Test proper initialization."""
        self.assertEqual(self.smart_login.driver, self.mock_driver)
        self.assertEqual(self.smart_login.navigator, self.mock_navigator)
        self.assertEqual(self.smart_login.login_flow, self.mock_base_login_flow)
        self.assertEqual(self.smart_login.logger, self.mock_logger)
    
    def test_authenticate_method_exists(self):
        """Test that authenticate method has correct signature."""
        self.assertTrue(hasattr(self.smart_login, 'authenticate'))
        self.assertTrue(callable(self.smart_login.authenticate))
    
    @patch('compass_core.smart_login_flow.AuthenticatedPageDetector')
    @patch('compass_core.smart_login_flow.LoginPageDetector')
    @patch('compass_core.smart_login_flow.WWIDPageDetector')
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_authenticate_sso_cache_hit(self, mock_wait_class, mock_wwid_detector_class, 
                                       mock_login_detector_class, mock_auth_detector_class):
        """Test authenticate when SSO session is active (cache hit)."""
        # Mock successful navigation
        self.mock_navigator.navigate_to.return_value = {"status": "success"}
        
        # Mock WWID detector - no WWID page
        mock_wwid_detector = Mock()
        mock_wwid_detector.is_present.return_value = False
        mock_wwid_detector_class.return_value = mock_wwid_detector
        
        # Mock detectors with selectors
        mock_login_detector = Mock()
        mock_login_detector.SELECTORS = ['input[type="email"]']
        mock_login_detector_class.return_value = mock_login_detector
        
        mock_auth_detector = Mock()
        mock_auth_detector.SELECTORS = ['button', 'nav']
        mock_auth_detector_class.return_value = mock_auth_detector
        
        # Mock WebDriverWait to return authenticated element
        mock_wait = Mock()
        mock_app_element = Mock()
        mock_app_element.is_displayed.return_value = True
        mock_app_element.tag_name = 'button'
        mock_app_element.get_attribute.return_value = 'navbar'
        mock_wait.until.return_value = mock_app_element
        mock_wait_class.return_value = mock_wait
        
        result = self.smart_login.authenticate(
            username="test@example.com",
            password="password123",
            url="https://app.example.com/"
        )
        
        # Should succeed without calling base login flow
        self.assertEqual(result['status'], 'success')
        self.assertFalse(result['authenticated'], "Should not authenticate when SSO active")
        self.assertIn('SSO', result['message'])
        
        # Base login flow should NOT be called
        self.mock_base_login_flow.authenticate.assert_not_called()
    
    @patch('compass_core.smart_login_flow.AuthenticatedPageDetector')
    @patch('compass_core.smart_login_flow.LoginPageDetector')
    @patch('compass_core.smart_login_flow.WWIDPageDetector')
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_authenticate_sso_cache_miss(self, mock_wait_class, mock_wwid_detector_class,
                                        mock_login_detector_class, mock_auth_detector_class):
        """Test authenticate when SSO session is missing (cache miss)."""
        # Mock successful navigation
        self.mock_navigator.navigate_to.return_value = {"status": "success"}
        
        # Mock WWID detector - no WWID page
        mock_wwid_detector = Mock()
        mock_wwid_detector.is_present.return_value = False
        mock_wwid_detector_class.return_value = mock_wwid_detector
        
        # Mock detectors with selectors
        mock_login_detector = Mock()
        mock_login_detector.SELECTORS = ['input[type="email"]']
        mock_login_detector_class.return_value = mock_login_detector
        
        mock_auth_detector = Mock()
        mock_auth_detector.SELECTORS = ['button', 'nav']
        mock_auth_detector_class.return_value = mock_auth_detector
        
        # Mock WebDriverWait to return login field
        mock_wait = Mock()
        mock_login_field = Mock()
        mock_login_field.is_displayed.return_value = True
        mock_login_field.tag_name = 'input'
        mock_login_field.get_attribute.side_effect = lambda attr: 'email' if attr == 'type' else 'form-control'
        mock_wait.until.return_value = mock_login_field
        mock_wait_class.return_value = mock_wait
        
        # Mock successful base login
        self.mock_base_login_flow.authenticate.return_value = {
            "status": "success",
            "message": "Authenticated successfully"
        }
        
        result = self.smart_login.authenticate(
            username="test@example.com",
            password="password123",
            url="https://app.example.com/"
        )
        
        # Should succeed with authentication performed
        self.assertEqual(result['status'], 'success')
        self.assertTrue(result['authenticated'], "Should authenticate when SSO missing")
        
        # Base login flow should be called
        self.mock_base_login_flow.authenticate.assert_called_once()
        
        # Verify skip_navigation was passed
        call_kwargs = self.mock_base_login_flow.authenticate.call_args[1]
        self.assertTrue(call_kwargs.get('skip_navigation'))
    
    def test_authenticate_navigation_failure(self):
        """Test authenticate when navigation fails."""
        # Mock navigation failure
        self.mock_navigator.navigate_to.return_value = {
            "status": "error",
            "error": "Navigation failed"
        }
        
        result = self.smart_login.authenticate(
            username="test@example.com",
            password="password123",
            url="https://app.example.com/"
        )
        
        # Should return error
        self.assertEqual(result['status'], 'error')
        self.assertFalse(result['authenticated'])
        self.assertIn('error', result)
    
    @patch('compass_core.smart_login_flow.AuthenticatedPageDetector')
    @patch('compass_core.smart_login_flow.LoginPageDetector')
    @patch('compass_core.smart_login_flow.WWIDPageDetector')
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_authenticate_login_failure(self, mock_wait_class, mock_wwid_detector_class,
                                       mock_login_detector_class, mock_auth_detector_class):
        """Test authenticate when base login fails."""
        # Mock successful navigation and login page detection
        self.mock_navigator.navigate_to.return_value = {"status": "success"}
        
        # Mock detectors
        mock_wwid_detector = Mock()
        mock_wwid_detector.is_present.return_value = False
        mock_wwid_detector_class.return_value = mock_wwid_detector
        
        mock_login_detector = Mock()
        mock_login_detector.SELECTORS = ['input[type="email"]']
        mock_login_detector_class.return_value = mock_login_detector
        
        mock_auth_detector = Mock()
        mock_auth_detector.SELECTORS = ['button']
        mock_auth_detector_class.return_value = mock_auth_detector
        
        # Mock login field detected
        mock_wait = Mock()
        mock_login_field = Mock()
        mock_login_field.is_displayed.return_value = True
        mock_login_field.tag_name = 'input'
        mock_login_field.get_attribute.side_effect = lambda attr: 'email' if attr == 'type' else ''
        mock_wait.until.return_value = mock_login_field
        mock_wait_class.return_value = mock_wait
        
        # Mock failed base login
        self.mock_base_login_flow.authenticate.return_value = {
            "status": "error",
            "error": "Invalid credentials"
        }
        
        result = self.smart_login.authenticate(
            username="test@example.com",
            password="wrongpassword",
            url="https://app.example.com/"
        )
        
        # Should return error
        self.assertEqual(result['status'], 'error')
        self.assertFalse(result['authenticated'])
        self.assertIn('error', result)
    
    @patch('compass_core.smart_login_flow.AuthenticatedPageDetector')
    @patch('compass_core.smart_login_flow.LoginPageDetector')
    @patch('compass_core.smart_login_flow.WWIDPageDetector')
    def test_authenticate_handles_alert(self, mock_wwid_detector_class, mock_login_detector_class, mock_auth_detector_class):
        """Test authenticate handles unexpected alerts."""
        from selenium.common.exceptions import UnexpectedAlertPresentException
        
        # Mock alert during navigation
        self.mock_navigator.navigate_to.side_effect = [
            UnexpectedAlertPresentException("Alert present"),
            {"status": "success"}  # Success on retry
        ]
        
        # Mock detectors
        mock_wwid_detector = Mock()
        mock_wwid_detector.is_present.return_value = False
        mock_wwid_detector_class.return_value = mock_wwid_detector
        
        mock_login_detector = Mock()
        mock_login_detector.SELECTORS = ['input[type="email"]']
        mock_login_detector_class.return_value = mock_login_detector
        
        mock_auth_detector = Mock()
        mock_auth_detector.SELECTORS = ['button', 'nav']
        mock_auth_detector_class.return_value = mock_auth_detector
        
        # Mock alert handling
        with patch('selenium.webdriver.common.alert.Alert') as mock_alert_class:
            mock_alert = Mock()
            mock_alert.text = "Alert message"
            mock_alert_class.return_value = mock_alert
            
            with patch('compass_core.smart_login_flow.WebDriverWait') as mock_wait_class:
                # Mock authenticated (SSO active)
                mock_wait = Mock()
                mock_app_element = Mock()
                mock_app_element.is_displayed.return_value = True
                mock_app_element.tag_name = 'button'
                mock_app_element.get_attribute.return_value = ''
                mock_wait.until.return_value = mock_app_element
                mock_wait_class.return_value = mock_wait
                
                result = self.smart_login.authenticate(
                    username="test@example.com",
                    password="password123",
                    url="https://app.example.com/"
                )
                
                # Should handle alert and succeed
                mock_alert.accept.assert_called_once()
                self.assertEqual(result['status'], 'success')
    
    def test_uses_page_detectors(self):
        """Test that SmartLoginFlow uses page detector classes."""
        # Verify detectors are imported and available
        from compass_core.smart_login_flow import (
            LoginPageDetector,
            WWIDPageDetector,
            AuthenticatedPageDetector
        )
        
        self.assertIsNotNone(LoginPageDetector)
        self.assertIsNotNone(WWIDPageDetector)
        self.assertIsNotNone(AuthenticatedPageDetector)
    
    @patch('compass_core.smart_login_flow.AuthenticatedPageDetector')
    @patch('compass_core.smart_login_flow.LoginPageDetector')
    @patch('compass_core.smart_login_flow.WWIDPageDetector')
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_authenticate_passes_kwargs(self, mock_wait_class, mock_wwid_detector_class,
                                       mock_login_detector_class, mock_auth_detector_class):
        """Test that authenticate passes kwargs to base login flow."""
        # Mock successful navigation
        self.mock_navigator.navigate_to.return_value = {"status": "success"}
        
        # Mock detectors
        mock_wwid_detector = Mock()
        mock_wwid_detector.is_present.return_value = False
        mock_wwid_detector_class.return_value = mock_wwid_detector
        
        mock_login_detector = Mock()
        mock_login_detector.SELECTORS = ['input[type="email"]']
        mock_login_detector_class.return_value = mock_login_detector
        
        mock_auth_detector = Mock()
        mock_auth_detector.SELECTORS = ['button']
        mock_auth_detector_class.return_value = mock_auth_detector
        
        # Mock login page detected
        mock_wait = Mock()
        mock_field = Mock()
        mock_field.is_displayed.return_value = True
        mock_field.tag_name = 'input'
        mock_field.get_attribute.side_effect = lambda attr: 'email' if attr == 'type' else ''
        mock_wait.until.return_value = mock_field
        mock_wait_class.return_value = mock_wait
        
        # Mock successful login
        self.mock_base_login_flow.authenticate.return_value = {
            "status": "success",
            "message": "Success"
        }
        
        # Call with extra kwargs
        result = self.smart_login.authenticate(
            username="test@example.com",
            password="password123",
            url="https://app.example.com/",
            login_id="ABC123",
            timeout=30,
            custom_param="value"
        )
        
        # Verify kwargs were passed
        self.mock_base_login_flow.authenticate.assert_called_once()
        call_kwargs = self.mock_base_login_flow.authenticate.call_args[1]
        self.assertEqual(call_kwargs.get('login_id'), "ABC123")
        self.assertEqual(call_kwargs.get('timeout'), 30)
        self.assertEqual(call_kwargs.get('custom_param'), "value")
        self.assertTrue(call_kwargs.get('skip_navigation'))
    
    def test_constants_defined(self):
        """Test that timeout constants are defined."""
        from compass_core import smart_login_flow
        
        self.assertTrue(hasattr(smart_login_flow, 'DEFAULT_WAIT_TIMEOUT'))
        self.assertTrue(hasattr(smart_login_flow, 'DEFAULT_POLL_FREQUENCY'))
        self.assertEqual(smart_login_flow.DEFAULT_WAIT_TIMEOUT, 10)
        self.assertEqual(smart_login_flow.DEFAULT_POLL_FREQUENCY, 0.5)


if __name__ == '__main__':
    unittest.main()
