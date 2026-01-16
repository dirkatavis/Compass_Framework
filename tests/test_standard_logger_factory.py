"""
Tests for StandardLoggerFactory implementation.
"""
import unittest
import logging

from compass_core.logging import Logger, LoggerFactory, StandardLoggerFactory


class TestStandardLoggerFactory(unittest.TestCase):
    """Test StandardLoggerFactory concrete implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = StandardLoggerFactory()
    
    def test_protocol_compliance(self):
        """Test that StandardLoggerFactory implements LoggerFactory protocol."""
        self.assertIsInstance(self.factory, LoggerFactory)
        
        # Verify required methods exist
        self.assertTrue(hasattr(self.factory, 'create_logger'))
        self.assertTrue(callable(self.factory.create_logger))
    
    def test_create_logger_basic(self):
        """Test basic logger creation."""
        logger = self.factory.create_logger("test_logger")
        
        self.assertIsInstance(logger, Logger)
        self.assertEqual(logger.name, "test_logger")
        self.assertEqual(logger.level, logging.INFO)
    
    def test_create_logger_with_config_level_string(self):
        """Test logger creation with string level configuration."""
        config = {"level": "DEBUG"}
        logger = self.factory.create_logger("debug_logger", config)
        
        self.assertEqual(logger.name, "debug_logger")
        self.assertEqual(logger.level, logging.DEBUG)
    
    def test_create_logger_with_config_level_int(self):
        """Test logger creation with integer level configuration."""
        config = {"level": logging.WARNING}
        logger = self.factory.create_logger("warn_logger", config)
        
        self.assertEqual(logger.name, "warn_logger")
        self.assertEqual(logger.level, logging.WARNING)
    
    def test_create_logger_with_invalid_level(self):
        """Test logger creation with invalid level falls back to INFO."""
        config = {"level": "INVALID_LEVEL"}
        logger = self.factory.create_logger("fallback_logger", config)
        
        self.assertEqual(logger.name, "fallback_logger")
        self.assertEqual(logger.level, logging.INFO)
    
    def test_create_logger_with_empty_config(self):
        """Test logger creation with empty config dictionary."""
        config = {}
        logger = self.factory.create_logger("empty_config_logger", config)
        
        self.assertEqual(logger.name, "empty_config_logger")
        self.assertEqual(logger.level, logging.INFO)
    
    def test_create_logger_without_config(self):
        """Test logger creation without config parameter."""
        logger = self.factory.create_logger("no_config_logger")
        
        self.assertEqual(logger.name, "no_config_logger")
        self.assertEqual(logger.level, logging.INFO)
    
    def test_create_multiple_loggers(self):
        """Test creating multiple logger instances."""
        logger1 = self.factory.create_logger("logger1")
        logger2 = self.factory.create_logger("logger2")
        
        self.assertIsInstance(logger1, Logger)
        self.assertIsInstance(logger2, Logger)
        self.assertEqual(logger1.name, "logger1")
        self.assertEqual(logger2.name, "logger2")
        # Should be different instances
        self.assertIsNot(logger1, logger2)


if __name__ == '__main__':
    unittest.main()