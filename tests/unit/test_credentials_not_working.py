"""
Test that demonstrates IniConfiguration does NOT read credentials yet.

This test SHOULD FAIL - it exposes that we haven't implemented
credential reading support in IniConfiguration.
"""
import unittest
import os
from compass_core import IniConfiguration


class TestCredentialReadingNotImplemented(unittest.TestCase):
    """Test credential reading functionality."""
    
    def test_read_credentials_from_local_config(self):
        """
        Test that IniConfiguration CAN read credentials from webdriver.ini.local.
        
        This verifies the [credentials] and [app] sections work correctly.
        """
        # Skip if webdriver.ini.local doesn't exist
        if not os.path.exists('webdriver.ini.local'):
            self.skipTest("webdriver.ini.local not found - create it to run this test")
        
        # Try to read credentials
        config = IniConfiguration()
        config.load('webdriver.ini.local')
        
        # These should return values from [credentials] section
        username = config.get('credentials.username')
        password = config.get('credentials.password')
        login_id = config.get('credentials.login_id')
        
        # These assertions will FAIL because IniConfiguration
        # doesn't support credentials.* keys yet
        self.assertIsNotNone(username, 
            "IniConfiguration should read credentials.username from [credentials] section")
        self.assertIsNotNone(password,
            "IniConfiguration should read credentials.password from [credentials] section")
        self.assertIsNotNone(login_id,
            "IniConfiguration should read credentials.login_id from [credentials] section")
        
        # Print what we got (for debugging)
        print(f"\nCredentials read:")
        print(f"  username: {username}")
        print(f"  password: {'*' * len(password) if password else None}")
        print(f"  login_id: {login_id}")
    
    def test_read_app_urls_from_local_config(self):
        """
        Test that IniConfiguration CAN read app URLs from webdriver.ini.local.
        
        This verifies the [app] section works correctly.
        """
        # Skip if webdriver.ini.local doesn't exist
        if not os.path.exists('webdriver.ini.local'):
            self.skipTest("webdriver.ini.local not found")
        
        # Try to read app URLs
        config = IniConfiguration()
        config.load('webdriver.ini.local')
        
        # These should return values from [app] section
        login_url = config.get('app.login_url')
        app_url = config.get('app.app_url')
        
        # At least one app setting should be present (either login_url or app_url)
        self.assertTrue(login_url is not None or app_url is not None,
            "IniConfiguration should read at least one value from [app] section")
        
        # Print what we got
        print(f"\nApp URLs read:")
        print(f"  login_url: {login_url}")
        print(f"  app_url: {app_url}")


if __name__ == '__main__':
    # Run with verbose output to see the failures
    unittest.main(verbosity=2)
