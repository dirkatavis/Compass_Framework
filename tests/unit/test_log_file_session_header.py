"""
Test that the session header (with date) is present at the top of the log file and not repeated in log lines.
"""
import unittest
import os
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(__file__), '../../clients/vehicle_lookup/vehicle_lookup.log')

class TestLogFileSessionHeader(unittest.TestCase):
    def test_log_file_session_header(self):
        # Ensure log file exists and is not empty
        self.assertTrue(os.path.exists(LOG_PATH))
        with open(LOG_PATH, encoding='utf-8') as f:
            content = f.read()
        date_str = datetime.now().strftime('%B %d, %Y')
        # Header should contain the date
        self.assertIn(date_str, content)
        self.assertIn('Log Session Start', content)
        # Header should be at the very top
        self.assertTrue(content.strip().startswith('*'))
        # Date should not appear in subsequent log lines
        self.assertEqual(content.count(date_str), 1)

if __name__ == '__main__':
    unittest.main()
