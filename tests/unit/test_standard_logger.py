"""
Tests for StandardLogger implementation.
TDD approach - write tests first, then implement.
"""
import unittest
import logging

from compass_core.logging import Logger


class TestStandardLogger(unittest.TestCase):
    """Test StandardLogger concrete implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        from compass_core.logging import StandardLogger
        self.logger_class = StandardLogger
    
    def test_protocol_compliance(self):
        """Test that StandardLogger implements Logger protocol."""
        logger = self.logger_class("test_logger")
        self.assertIsInstance(logger, Logger)
        
        # Verify required methods exist
        required_methods = ['debug', 'info', 'warning', 'error', 'critical']
        for method_name in required_methods:
            self.assertTrue(hasattr(logger, method_name))
            self.assertTrue(callable(getattr(logger, method_name)))
    
    def test_logger_initialization_with_name(self):
        """Test StandardLogger initialization with name."""
        logger = self.logger_class("test_logger")
        self.assertIsNotNone(logger)
        # Should store the logger name
        self.assertEqual(logger.name, "test_logger")
    
    def test_logger_initialization_default_level(self):
        """Test StandardLogger has default logging level."""
        logger = self.logger_class("test_logger")
        # Should default to INFO level
        self.assertEqual(logger.level, logging.INFO)
    
    def test_info_logging_basic(self):
        """Test basic info logging functionality."""
        with self.assertLogs(level='INFO') as log_context:
            logger = self.logger_class("test_logger")
            logger.info("Test info message")
            
            self.assertIn("Test info message", log_context.output[0])
    
    def test_error_logging_basic(self):
        """Test basic error logging functionality.""" 
        with self.assertLogs(level='ERROR') as log_context:
            logger = self.logger_class("test_logger")
            logger.error("Test error message")
            
            self.assertIn("Test error message", log_context.output[0])
    
    def test_warning_logging_basic(self):
        """Test basic warning logging functionality."""
        with self.assertLogs(level='WARNING') as log_context:
            logger = self.logger_class("test_logger")
            logger.warning("Test warning message")
            
            self.assertIn("Test warning message", log_context.output[0])
    
    def test_debug_logging_basic(self):
        """Test basic debug logging functionality."""
        logger = self.logger_class("test_logger", level=logging.DEBUG)
        with self.assertLogs(level='DEBUG') as log_context:
            logger.debug("Test debug message")
            
            self.assertIn("Test debug message", log_context.output[0])
    
    def test_critical_logging_basic(self):
        """Test basic critical logging functionality."""
        with self.assertLogs(level='CRITICAL') as log_context:
            logger = self.logger_class("test_logger")
            logger.critical("Test critical message")
            
            self.assertIn("Test critical message", log_context.output[0])
    
    def test_logging_with_args(self):
        """Test logging with string formatting args."""
        with self.assertLogs(level='INFO') as log_context:
            logger = self.logger_class("test_logger")
            logger.info("User %s logged in", "john")
            
            self.assertIn("User john logged in", log_context.output[0])
    
    def test_logging_with_kwargs(self):
        """Test logging with keyword arguments (like exc_info)."""
        with self.assertLogs(level='ERROR') as log_context:
            logger = self.logger_class("test_logger")
            logger.error("Operation failed", extra={'user_id': 123})
            
            self.assertIn("Operation failed", log_context.output[0])


if __name__ == '__main__':
    unittest.main()