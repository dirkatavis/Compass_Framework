"""
Tests for Navigator interface
Focused on navigation protocol contract
"""
import unittest
from typing import get_type_hints, Dict, Any, Optional, Tuple
from compass_core.navigation import Navigator


class MockNavigator:
    """Simple implementation for testing the Navigator interface"""
    
    def navigate_to(self, url: str, label: str = "page", verify: bool = True) -> Dict[str, Any]:
        return {"status": "ok", "url": url, "label": label, "verified": verify}
    
    def verify_page(self, 
                   url: Optional[str] = None, 
                   check_locator: Optional[Tuple[str, str]] = None, 
                   timeout: int = 15) -> Dict[str, Any]:
        return {"status": "ok", "url": url, "locator": check_locator, "timeout": timeout}


class TestNavigatorInterface(unittest.TestCase):
    """Test the Navigator protocol/interface"""
    
    def setUp(self):
        self.navigator = MockNavigator()
    
    def test_navigator_protocol_compliance(self):
        """Test that MockNavigator satisfies Navigator protocol"""
        # Runtime protocol compliance check
        self.assertIsInstance(self.navigator, Navigator)
        
        # Verify required methods exist
        self.assertTrue(hasattr(self.navigator, 'navigate_to'))
        self.assertTrue(hasattr(self.navigator, 'verify_page'))
        self.assertTrue(callable(self.navigator.navigate_to))
        self.assertTrue(callable(self.navigator.verify_page))
    
    def test_navigate_to_method_signature(self):
        """Test navigate_to has correct signature and behavior"""
        import inspect
        sig = inspect.signature(self.navigator.navigate_to)
        
        # Check parameters
        params = list(sig.parameters.keys())
        self.assertIn('url', params)
        self.assertIn('label', params) 
        self.assertIn('verify', params)
        
        # Check defaults
        self.assertEqual(sig.parameters['label'].default, "page")
        self.assertEqual(sig.parameters['verify'].default, True)
        
        # Test basic call
        result = self.navigator.navigate_to("https://example.com")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "ok")
    
    def test_verify_page_method_signature(self):
        """Test verify_page has correct signature and behavior"""
        import inspect
        sig = inspect.signature(self.navigator.verify_page)
        
        # Check parameters
        params = list(sig.parameters.keys())
        self.assertIn('url', params)
        self.assertIn('check_locator', params)
        self.assertIn('timeout', params)
        
        # Check defaults
        self.assertEqual(sig.parameters['url'].default, None)
        self.assertEqual(sig.parameters['check_locator'].default, None)
        self.assertEqual(sig.parameters['timeout'].default, 15)
        
        # Test basic call
        result = self.navigator.verify_page()
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "ok")
    
    def test_navigate_to_return_type(self):
        """Test navigate_to returns expected structure"""
        result = self.navigator.navigate_to("https://example.com", "test page")
        
        # Should return dict with status
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        
        # Test with verification disabled
        result = self.navigator.navigate_to("https://example.com", verify=False)
        self.assertEqual(result["verified"], False)
    
    def test_verify_page_with_parameters(self):
        """Test verify_page with different parameter combinations"""
        # Test with URL only
        result = self.navigator.verify_page(url="https://example.com")
        self.assertEqual(result["url"], "https://example.com")
        
        # Test with locator
        locator = ("id", "submit-button")
        result = self.navigator.verify_page(check_locator=locator)
        self.assertEqual(result["locator"], locator)
        
        # Test with custom timeout
        result = self.navigator.verify_page(timeout=30)
        self.assertEqual(result["timeout"], 30)
    
    def test_type_hints_compliance(self):
        """Test that methods have proper type hints"""
        navigate_hints = get_type_hints(self.navigator.navigate_to)
        verify_hints = get_type_hints(self.navigator.verify_page)
        
        # Check return types
        self.assertEqual(navigate_hints.get('return'), Dict[str, Any])
        self.assertEqual(verify_hints.get('return'), Dict[str, Any])


if __name__ == '__main__':
    unittest.main()