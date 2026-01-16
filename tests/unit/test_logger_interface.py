"""
Tests for Logger interface
Focused on logging protocol contract
"""
import unittest
from typing import get_type_hints, Any, Optional
from compass_core.logging import Logger, LoggerFactory


class MockLogger:
    """Simple implementation for testing Logger interface"""
    
    def __init__(self):
        self.messages = []
    
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.messages.append(("DEBUG", message, args, kwargs))
    
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.messages.append(("INFO", message, args, kwargs))
    
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.messages.append(("WARNING", message, args, kwargs))
    
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.messages.append(("ERROR", message, args, kwargs))
    
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        self.messages.append(("CRITICAL", message, args, kwargs))


class MockLoggerFactory:
    """Simple implementation for testing LoggerFactory interface"""
    
    def create_logger(self, name: str, config: Optional[dict] = None) -> Logger:
        return MockLogger()


class TestLoggerInterface(unittest.TestCase):
    """Test the Logger protocol/interface"""
    
    def setUp(self):
        self.logger = MockLogger()
        self.factory = MockLoggerFactory()
    
    def test_logger_protocol_compliance(self):
        """Test that MockLogger satisfies Logger protocol"""
        # Runtime protocol compliance check
        self.assertIsInstance(self.logger, Logger)
        
        # Verify required methods exist
        required_methods = ['debug', 'info', 'warning', 'error', 'critical']
        for method_name in required_methods:
            self.assertTrue(hasattr(self.logger, method_name))
            self.assertTrue(callable(getattr(self.logger, method_name)))
    
    def test_factory_protocol_compliance(self):
        """Test that MockLoggerFactory satisfies LoggerFactory protocol"""
        self.assertIsInstance(self.factory, LoggerFactory)
        self.assertTrue(hasattr(self.factory, 'create_logger'))
        self.assertTrue(callable(self.factory.create_logger))
    
    def test_logger_method_signatures(self):
        """Test logger methods have correct signatures"""
        import inspect
        
        for method_name in ['debug', 'info', 'warning', 'error', 'critical']:
            method = getattr(self.logger, method_name)
            sig = inspect.signature(method)
            
            # Should accept message as first param
            params = list(sig.parameters.keys())
            self.assertGreater(len(params), 0)
            self.assertEqual(params[0], 'message')
            
            # Should accept *args and **kwargs
            self.assertTrue(any(p.kind == p.VAR_POSITIONAL for p in sig.parameters.values()))
            self.assertTrue(any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()))
    
    def test_logger_basic_functionality(self):
        """Test basic logging functionality"""
        # Test simple messages
        self.logger.info("Test message")
        self.assertEqual(len(self.logger.messages), 1)
        self.assertEqual(self.logger.messages[0][:2], ("INFO", "Test message"))
        
        # Test with args
        self.logger.debug("User %s logged in", "john")
        self.assertEqual(len(self.logger.messages), 2)
        self.assertEqual(self.logger.messages[1][:3], ("DEBUG", "User %s logged in", ("john",)))
        
        # Test with kwargs
        self.logger.error("Operation failed", exc_info=True)
        self.assertEqual(len(self.logger.messages), 3)
        self.assertEqual(self.logger.messages[2][3], {"exc_info": True})
    
    def test_all_log_levels(self):
        """Test all log levels work correctly"""
        test_cases = [
            ("debug", "DEBUG"),
            ("info", "INFO"), 
            ("warning", "WARNING"),
            ("error", "ERROR"),
            ("critical", "CRITICAL")
        ]
        
        for method_name, expected_level in test_cases:
            with self.subTest(level=expected_level):
                method = getattr(self.logger, method_name)
                method(f"Test {expected_level} message")
                
                # Check the last message
                last_message = self.logger.messages[-1]
                self.assertEqual(last_message[0], expected_level)
                self.assertEqual(last_message[1], f"Test {expected_level} message")
    
    def test_factory_creates_logger(self):
        """Test factory creates logger instances"""
        logger = self.factory.create_logger("test.logger")
        self.assertIsInstance(logger, Logger)
        
        # Test with config
        config = {"level": "DEBUG", "format": "%(message)s"}
        logger_with_config = self.factory.create_logger("test.configured", config)
        self.assertIsInstance(logger_with_config, Logger)
    
    def test_type_hints_compliance(self):
        """Test that methods have proper type hints"""
        debug_hints = get_type_hints(self.logger.debug)
        self.assertEqual(debug_hints.get('return'), type(None))
        
        factory_hints = get_type_hints(self.factory.create_logger)
        self.assertEqual(factory_hints.get('return'), Logger)


if __name__ == '__main__':
    unittest.main()