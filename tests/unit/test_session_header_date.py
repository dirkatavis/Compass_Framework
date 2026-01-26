"""
Test that the session header contains the date and is only present at the top of the log output.
"""
import unittest
import io
import sys
from datetime import datetime
from compass_core.logging import StandardLogger

class TestSessionHeaderDate(unittest.TestCase):
    def test_session_header_contains_date(self):
        captured = io.StringIO()
        sys_stdout = sys.stdout
        sys.stdout = captured
        try:
            logger = StandardLogger("header_date_test")
            output = captured.getvalue()
            date_str = datetime.now().strftime('%B %d, %Y')
            # Header should contain the date
            self.assertIn(date_str, output)
            self.assertIn('Log Session Start', output)
            # Header should be at the very top
            self.assertTrue(output.strip().startswith('*'))
            # Date should not appear in subsequent log lines
            logger.info("Test message after header")
            output2 = captured.getvalue()
            # Only one occurrence of the date (in header)
            self.assertEqual(output2.count(date_str), 1)
        finally:
            sys.stdout = sys_stdout

if __name__ == '__main__':
    unittest.main()
