"""
Tests for SmartLoginFlow implementation.

This module validates the smart authentication logic that detects SSO cache state
and conditionally performs login only when necessary.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch
from compass_core.login_flow import LoginFlow


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
    
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_authenticate_sso_cache_hit(self, mock_wait_class):
        """Test authenticate when SSO session is active (cache hit)."""
        from selenium.common.exceptions import TimeoutException
        
        # Mock successful navigation
        self.mock_navigator.navigate_to.return_value = {"status": "success"}
        
        # Mock no login page detected (TimeoutException means no login fields found)
        mock_wait = Mock()
        mock_wait.until.side_effect = TimeoutException("No login fields")
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
    
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_authenticate_sso_cache_miss(self, mock_wait_class):
        """Test authenticate when SSO session is missing (cache miss)."""
        # Mock successful navigation
        self.mock_navigator.navigate_to.return_value = {"status": "success"}
        
        # Mock login page detected (login field found)
        mock_wait = Mock()
        mock_login_field = Mock()
        mock_login_field.is_displayed.return_value = True
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
    
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_authenticate_login_failure(self, mock_wait_class):
        """Test authenticate when base login fails."""
        # Mock successful navigation and login page detection
        self.mock_navigator.navigate_to.return_value = {"status": "success"}
        
        mock_wait = Mock()
        mock_login_field = Mock()
        mock_login_field.is_displayed.return_value = True
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
    
    def test_authenticate_handles_alert(self):
        """Test authenticate handles unexpected alerts."""
        from selenium.common.exceptions import UnexpectedAlertPresentException
        
        # Mock alert during navigation
        self.mock_navigator.navigate_to.side_effect = [
            UnexpectedAlertPresentException("Alert present"),
            {"status": "success"}  # Success on retry
        ]
        
        # Mock alert handling
        with patch('selenium.webdriver.common.alert.Alert') as mock_alert_class:
            mock_alert = Mock()
            mock_alert.text = "Alert message"
            mock_alert_class.return_value = mock_alert
            
            with patch('compass_core.smart_login_flow.WebDriverWait') as mock_wait_class:
                from selenium.common.exceptions import TimeoutException
                
                # Mock no login page (SSO active)
                mock_wait = Mock()
                mock_wait.until.side_effect = TimeoutException("No login fields")
                mock_wait_class.return_value = mock_wait
                
                result = self.smart_login.authenticate(
                    username="test@example.com",
                    password="password123",
                    url="https://app.example.com/"
                )
                
                # Should handle alert and succeed
                mock_alert.accept.assert_called_once()
                self.assertEqual(result['status'], 'success')
    
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_detect_login_page_found(self, mock_wait_class):
        """Test _detect_login_page when login page is present."""
        # Mock login field found
        mock_wait = Mock()
        mock_field = Mock()
        mock_field.is_displayed.return_value = True
        mock_wait.until.return_value = mock_field
        mock_wait_class.return_value = mock_wait
        
        result = self.smart_login._detect_login_page(timeout=5)
        
        self.assertTrue(result, "Should detect login page")
    
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_detect_login_page_not_found(self, mock_wait_class):
        """Test _detect_login_page when no login page."""
        from selenium.common.exceptions import TimeoutException
        
        # Mock no login fields (timeout)
        mock_wait = Mock()
        mock_wait.until.side_effect = TimeoutException("No fields")
        mock_wait_class.return_value = mock_wait
        
        result = self.smart_login._detect_login_page(timeout=5)
        
        self.assertFalse(result, "Should not detect login page")
    
    @patch('compass_core.smart_login_flow.WebDriverWait')
    def test_detect_login_page_uses_combined_selector(self, mock_wait_class):
        """Test _detect_login_page uses optimized combined selector."""
        # Mock login field found
        mock_wait = Mock()
        mock_field = Mock()
        mock_field.is_displayed.return_value = True
        
        def mock_find_element(selector_type, selector):
            # Verify combined selector is used
            self.assertIn(',', selector, "Should use combined selector with comma")
            return mock_field
        
        self.mock_driver.find_element = mock_find_element
        mock_wait.until.return_value = mock_field
        mock_wait_class.return_value = mock_wait
        
        result = self.smart_login._detect_login_page(timeout=5)
        
        self.assertTrue(result)
    
    def test_authenticate_passes_kwargs(self):
        """Test that authenticate passes kwargs to base login flow."""
        with patch('compass_core.smart_login_flow.WebDriverWait') as mock_wait_class:
            # Mock login page detected
            self.mock_navigator.navigate_to.return_value = {"status": "success"}
            
            mock_wait = Mock()
            mock_field = Mock()
            mock_field.is_displayed.return_value = True
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
            call_kwargs = self.mock_base_login_flow.authenticate.call_args[1]
            self.assertEqual(call_kwargs.get('login_id'), "ABC123")
            self.assertEqual(call_kwargs.get('timeout'), 30)
            self.assertEqual(call_kwargs.get('custom_param'), "value")
    
    def test_constants_defined(self):
        """Test that timeout constants are defined."""
        from compass_core import smart_login_flow
        
        self.assertTrue(hasattr(smart_login_flow, 'DEFAULT_WAIT_TIMEOUT'))
        self.assertTrue(hasattr(smart_login_flow, 'DEFAULT_POLL_FREQUENCY'))
        self.assertEqual(smart_login_flow.DEFAULT_WAIT_TIMEOUT, 10)
        self.assertEqual(smart_login_flow.DEFAULT_POLL_FREQUENCY, 0.5)


if __name__ == '__main__':
    unittest.main()
