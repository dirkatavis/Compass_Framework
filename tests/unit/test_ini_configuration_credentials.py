"""
Unit tests for INI configuration credential and app URL support.

Tests the new [credentials] and [app] sections added for LoginFlow
and VehicleLookupFlow support.
"""
import unittest
import os
import tempfile
from compass_core import IniConfiguration


class TestIniConfigurationCredentials(unittest.TestCase):
    """Test credential and app URL configuration."""
    
    def setUp(self):
        """Create temporary INI file for testing."""
        self.config = IniConfiguration()
        
        # Create a temporary INI file
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        self.temp_file.write("""
[webdriver]
edge_path = drivers.local/msedgedriver.exe

[credentials]
username = test.user@example.com
password = TestPassword123
login_id = common

[app]
login_url = https://login.microsoftonline.com/
app_url = https://compass-test.example.com/
        """)
        self.temp_file.close()
    
    def tearDown(self):
        """Clean up temporary file."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_read_credentials_username(self):
        """Test reading username from credentials section."""
        self.config.load(self.temp_file.name)
        username = self.config.get('credentials.username')
        self.assertEqual(username, 'test.user@example.com')
    
    def test_read_credentials_password(self):
        """Test reading password from credentials section."""
        self.config.load(self.temp_file.name)
        password = self.config.get('credentials.password')
        self.assertEqual(password, 'TestPassword123')
    
    def test_read_credentials_login_id(self):
        """Test reading login_id from credentials section."""
        self.config.load(self.temp_file.name)
        login_id = self.config.get('credentials.login_id')
        self.assertEqual(login_id, 'common')
    
    def test_read_app_login_url(self):
        """Test reading login_url from app section."""
        self.config.load(self.temp_file.name)
        login_url = self.config.get('app.login_url')
        self.assertEqual(login_url, 'https://login.microsoftonline.com/')
    
    def test_read_app_url(self):
        """Test reading app_url from app section."""
        self.config.load(self.temp_file.name)
        app_url = self.config.get('app.app_url')
        self.assertEqual(app_url, 'https://compass-test.example.com/')
    
    def test_missing_credential_returns_none(self):
        """Test that missing credential returns None."""
        self.config.load(self.temp_file.name)
        result = self.config.get('credentials.nonexistent')
        self.assertIsNone(result)
    
    def test_default_value_for_missing_credential(self):
        """Test default value when credential missing."""
        self.config.load(self.temp_file.name)
        result = self.config.get('credentials.nonexistent', 'default_value')
        self.assertEqual(result, 'default_value')
    
    def test_environment_variable_fallback(self):
        """Test environment variable fallback pattern."""
        self.config.load(self.temp_file.name)
        
        # Simulate env var fallback pattern used in client scripts
        username = self.config.get('credentials.username') or os.getenv('TEST_USERNAME', 'fallback')
        self.assertEqual(username, 'test.user@example.com')
        
        # Test missing value with env var
        missing = self.config.get('credentials.missing') or os.getenv('TEST_MISSING', 'from_env')
        self.assertEqual(missing, 'from_env')
    
    def test_empty_credentials_section(self):
        """Test behavior with empty credentials section."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        temp_file.write("""
[webdriver]
edge_path = test.exe

[credentials]
# Empty section
        """)
        temp_file.close()
        
        try:
            # Pass config_path to prevent auto-loading webdriver.ini.local
            fresh_config = IniConfiguration(config_path=temp_file.name)
            username = fresh_config.get('credentials.username')
            self.assertIsNone(username, "Empty credentials section should return None for username")
        finally:
            os.unlink(temp_file.name)
    
    def test_missing_sections_graceful_handling(self):
        """Test graceful handling when sections don't exist."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        temp_file.write("""
[webdriver]
edge_path = test.exe
        """)
        temp_file.close()
        
        try:
            # Create fresh config and load temp file
            fresh_config = IniConfiguration()
            fresh_config.load(temp_file.name)
            username = fresh_config.get('credentials.username')
            self.assertIsNone(username, "Missing credentials section should return None")
            
            login_url = fresh_config.get('app.login_url')
            self.assertIsNone(login_url, "Missing app section should return None")
        finally:
            os.unlink(temp_file.name)
    
    def test_webdriver_section_still_works(self):
        """Test that existing webdriver section still works."""
        self.config.load(self.temp_file.name)
        edge_path = self.config.get('webdriver.edge_path')
        self.assertEqual(edge_path, 'drivers.local/msedgedriver.exe')
    
    def test_all_credential_fields_present(self):
        """Test that all expected credential fields can be read."""
        self.config.load(self.temp_file.name)
        
        credentials = {
            'username': self.config.get('credentials.username'),
            'password': self.config.get('credentials.password'),
            'login_id': self.config.get('credentials.login_id')
        }
        
        self.assertTrue(all(credentials.values()), 
                       "All credential fields should be present")
        self.assertEqual(len(credentials), 3)
    
    def test_all_app_fields_present(self):
        """Test that all expected app fields can be read."""
        self.config.load(self.temp_file.name)
        
        app_config = {
            'login_url': self.config.get('app.login_url'),
            'app_url': self.config.get('app.app_url')
        }
        
        self.assertTrue(all(app_config.values()), 
                       "All app fields should be present")
        self.assertEqual(len(app_config), 2)
    
    def test_validate_with_credentials(self):
        """Test that validate() works with credentials section."""
        self.config.load(self.temp_file.name)
        
        # Should not raise exception
        try:
            self.config.validate()
            validation_passed = True
        except Exception:
            validation_passed = False
        
        self.assertTrue(validation_passed, "Validation should pass with credentials")


class TestCredentialSecurityPatterns(unittest.TestCase):
    """Test security patterns for credential handling."""
    
    def test_credentials_not_in_default_template(self):
        """Test that template file doesn't contain real credentials."""
        # Read the template file
        template_path = 'webdriver.ini'
        
        if not os.path.exists(template_path):
            self.skipTest("Template file not found")
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Verify credentials are commented out
        self.assertIn('# username =', content, 
                     "Template should have commented username")
        self.assertIn('# password =', content, 
                     "Template should have commented password")
    
    def test_local_config_pattern(self):
        """Test that .local pattern is documented."""
        template_path = 'webdriver.ini'
        
        if not os.path.exists(template_path):
            self.skipTest("Template file not found")
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Should mention .local file pattern
        self.assertIn('webdriver.ini.local', content,
                     "Template should mention .local file pattern")


if __name__ == '__main__':
    unittest.main(verbosity=2)
