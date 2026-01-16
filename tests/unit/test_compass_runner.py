import unittest
from unittest.mock import patch
from io import StringIO
import sys
from compass_core import CompassRunner


class TestCompassRunner(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.runner = CompassRunner()

    def test_compass_runner_initialization(self):
        """Test that CompassRunner initializes with correct version."""
        self.assertEqual(self.runner.version, "0.1.0")

    def test_compass_runner_run_output(self):
        """Test that run() method produces expected output."""
        # Capture stdout
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            self.runner.run()
        
        output = captured_output.getvalue().strip()
        expected_output = "Compass Framework (v0.1.0) is active and isolated."
        self.assertEqual(output, expected_output)

    def test_compass_runner_run_contains_version(self):
        """Test that run() output contains the version number."""
        captured_output = StringIO()
        
        with patch('sys.stdout', captured_output):
            self.runner.run()
        
        output = captured_output.getvalue()
        self.assertIn(self.runner.version, output)
        self.assertIn("v0.1.0", output)

    def test_compass_runner_version_consistency(self):
        """Test that version is consistent and properly formatted."""
        # Version should be a string
        self.assertIsInstance(self.runner.version, str)
        
        # Version should follow semantic versioning pattern (basic check)
        version_parts = self.runner.version.split('.')
        self.assertEqual(len(version_parts), 3)
        
        # Each part should be numeric
        for part in version_parts:
            self.assertTrue(part.isdigit())


if __name__ == '__main__':
    unittest.main()