"""
Tests for SeleniumLoginFlow implementation.

This module validates the concrete implementation of LoginFlow using Selenium WebDriver
for Microsoft SSO authentication.
"""
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from compass_core.login_flow import LoginFlow


class TestSeleniumLoginFlow(unittest.TestCase):
    """Test SeleniumLoginFlow concrete implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Import here to handle optional selenium dependency
        try:
            from compass_core.selenium_login_flow import SeleniumLoginFlow
            self.SeleniumLoginFlow = SeleniumLoginFlow
            self.selenium_available = True
        except ImportError:
            self.selenium_available = False
            self.skipTest("Selenium not available")
        
        # Create mocks
        self.mock_driver = Mock()
        self.mock_navigator = Mock()
        self.mock_logger = Mock()
        
        # Setup mock driver behavior
        self.mock_driver.current_url = "https://login.microsoftonline.com/"
        
        # Create instance
        self.login_flow = self.SeleniumLoginFlow(
            driver=self.mock_driver,
            navigator=self.mock_navigator,
            logger=self.mock_logger
        )
    
    def test_protocol_compliance(self):
        """Test that SeleniumLoginFlow implements LoginFlow protocol."""
        self.assertIsInstance(self.login_flow, LoginFlow)
    
    def test_initialization(self):
        """Test proper initialization."""
        self.assertEqual(self.login_flow.driver, self.mock_driver)
        self.assertEqual(self.login_flow.navigator, self.mock_navigator)
        self.assertEqual(self.login_flow.logger, self.mock_logger)
    
    def test_authenticate_method_exists(self):
        """Test that authenticate method has correct signature."""
        self.assertTrue(hasattr(self.login_flow, 'authenticate'))
        self.assertTrue(callable(self.login_flow.authenticate))
    
    @patch('compass_core.selenium_login_flow.WebDriverWait')
    def test_authenticate_basic_flow(self, mock_wait_class):
        """Test basic authentication flow."""
        # Setup mocks
        self.mock_navigator.navigate_to.return_value = {"status": "success"}
        
        # Mock WebDriverWait for username field
        mock_wait = Mock()
        mock_username_field = Mock()
        mock_username_field.is_displayed.return_value = True
        mock_username_field.is_enabled.return_value = True
        
        mock_next_button = Mock()
        
        # Mock password field
        mock_password_field = Mock()
        mock_password_field.is_displayed.return_value = True
        mock_password_field.is_enabled.return_value = True
        
        mock_signin_button = Mock()
        
        # Setup wait behavior for username and password steps
        mock_wait.until.side_effect = [
            mock_username_field,  # Username field
            mock_next_button,      # Next button
            mock_password_field,   # Password field
            mock_signin_button     # Sign in button
        ]
        mock_wait_class.return_value = mock_wait
        
        # Call authenticate
        result = self.login_flow.authenticate(
            username="test@example.com",
            password="password123",
            url="https://login.microsoftonline.com/"
        )
        
        # Verify result
        self.assertEqual(result['status'], 'success')
        self.assertIn('message', result)
        
        # Verify navigation was called
        self.mock_navigator.navigate_to.assert_called_once()
        
        # Verify username was entered
        mock_username_field.send_keys.assert_called_with("test@example.com")
        mock_next_button.click.assert_called_once()
        
        # Verify password was entered
        mock_password_field.send_keys.assert_called_with("password123")
        mock_signin_button.click.assert_called_once()
    
    def test_authenticate_skip_navigation(self):
        """Test authenticate with skip_navigation=True."""
        with patch('compass_core.selenium_login_flow.WebDriverWait'):
            result = self.login_flow.authenticate(
                username="test@example.com",
                password="password123",
                url="https://login.microsoftonline.com/",
                skip_navigation=True
            )
            
            # Should not call navigator
            self.mock_navigator.navigate_to.assert_not_called()
    
    def test_authenticate_navigation_failure(self):
        """Test authenticate when navigation fails."""
        # Mock navigation failure
        self.mock_navigator.navigate_to.return_value = {
            "status": "error",
            "error": "Navigation failed"
        }
        
        result = self.login_flow.authenticate(
            username="test@example.com",
            password="password123",
            url="https://login.microsoftonline.com/"
        )
        
        # Should return error
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
    
    @patch('compass_core.selenium_login_flow.WebDriverWait')
    def test_enter_username_timeout(self, mock_wait_class):
        """Test username entry with timeout exception."""
        from selenium.common.exceptions import TimeoutException
        
        # Mock timeout on username field
        mock_wait = Mock()
        mock_wait.until.side_effect = TimeoutException("Username field not found")
        mock_wait_class.return_value = mock_wait
        
        result = self.login_flow._enter_username("test@example.com", timeout=10)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
    
    @patch('compass_core.selenium_login_flow.WebDriverWait')
    def test_enter_password_timeout(self, mock_wait_class):
        """Test password entry with timeout exception."""
        from selenium.common.exceptions import TimeoutException
        
        # Mock timeout on password field
        mock_wait = Mock()
        mock_wait.until.side_effect = TimeoutException("Password field not found")
        mock_wait_class.return_value = mock_wait
        
        result = self.login_flow._enter_password("password123", timeout=10)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
    
    @patch('compass_core.selenium_login_flow.WebDriverWait')
    def test_handle_stay_signed_in_no_prompt(self, mock_wait_class):
        """Test stay signed in handling when prompt doesn't appear."""
        from selenium.common.exceptions import TimeoutException
        
        # Mock timeout (prompt didn't appear)
        mock_wait = Mock()
        mock_wait.until.side_effect = TimeoutException("Prompt not found")
        mock_wait_class.return_value = mock_wait
        
        result = self.login_flow._handle_stay_signed_in(timeout=10, stay_signed_in=False)
        
        # Should return skipped status
        self.assertEqual(result['status'], 'skipped')
    
    @patch('compass_core.selenium_login_flow.WebDriverWait')
    def test_handle_stay_signed_in_click_no(self, mock_wait_class):
        """Test stay signed in handling when clicking No."""
        # Mock "No" button found
        mock_wait = Mock()
        mock_no_button = Mock()
        mock_wait.until.return_value = mock_no_button
        mock_wait_class.return_value = mock_wait
        
        result = self.login_flow._handle_stay_signed_in(timeout=10, stay_signed_in=False)
        
        # Should click No button
        self.assertEqual(result['status'], 'success')
        mock_no_button.click.assert_called_once()
    
    @patch('compass_core.selenium_login_flow.WebDriverWait')
    def test_handle_stay_signed_in_click_yes(self, mock_wait_class):
        """Test stay signed in handling when clicking Yes."""
        # Mock "Yes" button found
        mock_wait = Mock()
        mock_yes_button = Mock()
        mock_wait.until.return_value = mock_yes_button
        mock_wait_class.return_value = mock_wait
        
        result = self.login_flow._handle_stay_signed_in(timeout=10, stay_signed_in=True)
        
        # Should click Yes button
        self.assertEqual(result['status'], 'success')
        mock_yes_button.click.assert_called_once()
    
    @patch('compass_core.selenium_login_flow.WebDriverWait')
    def test_enter_wwid_success(self, mock_wait_class):
        """Test WWID entry success."""
        # Mock WWID field and submit button
        mock_wait = Mock()
        mock_wwid_field = Mock()
        mock_wwid_field.is_displayed.return_value = True
        mock_wwid_field.is_enabled.return_value = True
        
        mock_submit_button = Mock()
        
        mock_wait.until.side_effect = [mock_wwid_field, mock_submit_button]
        mock_wait_class.return_value = mock_wait
        
        result = self.login_flow._enter_wwid("ABC123", timeout=10)
        
        self.assertEqual(result['status'], 'success')
        mock_wwid_field.send_keys.assert_called_with("ABC123")
        mock_submit_button.click.assert_called_once()
    
    @patch('compass_core.selenium_login_flow.WebDriverWait')
    def test_enter_wwid_timeout(self, mock_wait_class):
        """Test WWID entry timeout."""
        from selenium.common.exceptions import TimeoutException
        
        # Mock timeout on WWID field
        mock_wait = Mock()
        mock_wait.until.side_effect = TimeoutException("WWID field not found")
        mock_wait_class.return_value = mock_wait
        
        result = self.login_flow._enter_wwid("ABC123", timeout=10)
        
        self.assertEqual(result['status'], 'error')
    
    def test_authenticate_with_login_id(self):
        """Test authenticate with login_id (WWID) parameter."""
        # This test verifies login_id parameter is accepted and handled
        # Full flow testing is done in E2E tests
        with patch.object(self.login_flow, '_enter_username') as mock_username:
            with patch.object(self.login_flow, '_enter_password') as mock_password:
                with patch.object(self.login_flow, '_handle_stay_signed_in') as mock_stay:
                    with patch.object(self.login_flow, '_enter_wwid') as mock_wwid:
                        # Setup successful responses
                        self.mock_navigator.navigate_to.return_value = {"status": "success"}
                        mock_username.return_value = {"status": "success"}
                        mock_password.return_value = {"status": "success"}
                        mock_stay.return_value = {"status": "skipped"}
                        mock_wwid.return_value = {"status": "success"}
                        
                        # Mock window handles for tab switching logic
                        self.mock_driver.current_window_handle = "main"
                        self.mock_driver.window_handles = ["main"]  # Single tab
                        
                        result = self.login_flow.authenticate(
                            username="test@example.com",
                            password="password123",
                            url="https://login.microsoftonline.com/",
                            login_id="ABC123"
                        )
                        
                        # Should succeed
                        self.assertEqual(result['status'], 'success')
                        
                        # Verify WWID method was called
                        mock_wwid.assert_called_once()
    
    def test_constants_defined(self):
        """Test that timeout constants are defined."""
        from compass_core import selenium_login_flow
        
        self.assertTrue(hasattr(selenium_login_flow, 'DEFAULT_WAIT_TIMEOUT'))
        self.assertTrue(hasattr(selenium_login_flow, 'DEFAULT_POLL_FREQUENCY'))
        self.assertEqual(selenium_login_flow.DEFAULT_WAIT_TIMEOUT, 10)
        self.assertEqual(selenium_login_flow.DEFAULT_POLL_FREQUENCY, 0.5)


if __name__ == '__main__':
    unittest.main()
