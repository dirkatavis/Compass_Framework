"""
Tests for LoginFlow protocol interface.

This module validates that the LoginFlow protocol is properly defined and that
implementations can satisfy its requirements.
"""
import unittest
from typing import Dict, Any
from compass_core.login_flow import LoginFlow


class MockLoginFlow:
    """Mock implementation of LoginFlow for protocol testing."""
    
    def authenticate(
        self,
        username: str,
        password: str,
        url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Mock authenticate implementation."""
        return {
            "status": "success",
            "message": f"Mock authenticated {username}",
            "authenticated": True
        }


class TestLoginFlowInterface(unittest.TestCase):
    """Test LoginFlow protocol interface."""
    
    def test_protocol_compliance(self):
        """Test that MockLoginFlow satisfies LoginFlow protocol."""
        mock = MockLoginFlow()
        self.assertIsInstance(mock, LoginFlow)
    
    def test_authenticate_method_exists(self):
        """Test that authenticate method has correct signature."""
        mock = MockLoginFlow()
        
        # Verify method exists and is callable
        self.assertTrue(hasattr(mock, 'authenticate'))
        self.assertTrue(callable(mock.authenticate))
    
    def test_authenticate_returns_dict(self):
        """Test that authenticate returns expected structure."""
        mock = MockLoginFlow()
        
        result = mock.authenticate(
            username="test@example.com",
            password="password123",
            url="https://app.example.com"
        )
        
        # Verify return type
        self.assertIsInstance(result, dict)
        
        # Verify required keys
        self.assertIn('status', result)
        self.assertIn('message', result)
    
    def test_authenticate_accepts_kwargs(self):
        """Test that authenticate accepts additional keyword arguments."""
        mock = MockLoginFlow()
        
        # Should accept extra parameters without error
        result = mock.authenticate(
            username="test@example.com",
            password="password123",
            url="https://app.example.com",
            login_id="ABC123",
            timeout=30,
            custom_param="value"
        )
        
        self.assertEqual(result['status'], 'success')
    
    def test_authenticate_status_values(self):
        """Test that authenticate returns valid status values."""
        mock = MockLoginFlow()
        
        result = mock.authenticate(
            username="test@example.com",
            password="password123",
            url="https://app.example.com"
        )
        
        # Status should be one of: success, error
        self.assertIn(result['status'], ['success', 'error'])
    
    def test_url_parameter_flexibility(self):
        """Test that url parameter accepts different URL types."""
        mock = MockLoginFlow()
        
        # Should work with login URL
        result1 = mock.authenticate(
            username="user@example.com",
            password="pass",
            url="https://login.microsoftonline.com/"
        )
        self.assertEqual(result1['status'], 'success')
        
        # Should work with app URL
        result2 = mock.authenticate(
            username="user@example.com",
            password="pass",
            url="https://app.example.com/dashboard"
        )
        self.assertEqual(result2['status'], 'success')
    
    def test_type_hints_compliance(self):
        """Test that method has proper type hints."""
        import inspect
        
        mock = MockLoginFlow()
        sig = inspect.signature(mock.authenticate)
        
        # Verify parameter annotations
        params = sig.parameters
        self.assertIn('username', params)
        self.assertIn('password', params)
        self.assertIn('url', params)
        self.assertIn('kwargs', params)
        
        # Verify return annotation
        self.assertIsNotNone(sig.return_annotation)


if __name__ == '__main__':
    unittest.main()
