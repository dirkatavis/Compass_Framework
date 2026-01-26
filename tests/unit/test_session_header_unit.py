"""
Unit test for StandardLogger.make_session_header.
"""
import unittest
from datetime import datetime
from compass_core.logging import StandardLogger

class TestSessionHeaderUnit(unittest.TestCase):
    def test_make_session_header_contains_date_and_format(self):
        date_str = "January 26, 2026"
        header = StandardLogger.make_session_header(date_str)
        self.assertIn(date_str, header)
        self.assertIn('Log Session Start', header)
        self.assertTrue(header.strip().startswith('*'))
        self.assertTrue(header.strip().endswith('*'))
        # Should be 4 lines: border, title, date, border
        lines = [line for line in header.strip().split('\n') if line.strip()]
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[1].strip(), 'Log Session Start')
        self.assertEqual(lines[2].strip(), date_str)

if __name__ == '__main__':
    unittest.main()
