"""
Logger Interface for Compass Framework
Protocol for structured logging operations with dependency injection
"""
import logging
import time
import sys
from typing import Protocol, runtime_checkable, Optional, Any


@runtime_checkable
class Logger(Protocol):
    """Protocol for logging operations"""
    
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message"""
        ...
    
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message"""
        ...
    
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message"""
        ...
    
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message"""
        ...
    
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message"""
        ...


@runtime_checkable  
class LoggerFactory(Protocol):
    """Protocol for creating logger instances with configuration"""
    
    def create_logger(self, name: str, config: Optional[dict] = None) -> Logger:
        """Create a configured logger instance"""
        ...


class StandardLogger(Logger):
    """
    Standard implementation of Logger protocol using Python's built-in logging.
    
    This class provides concrete logging functionality using Python's logging module,
    implementing the Logger interface for dependency injection compatibility.
    
    Example usage:
        logger = StandardLogger("my_app")
        logger.info("Application started")
        logger.error("Error occurred: %s", error_message)
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize StandardLogger with specified name and level.
        Outputs a professional session header with centered date and decorative border.
        Args:
            name: Logger name (ignored in log output)
            level: Logging level (default: INFO)
        """
        self.name = name
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.level = level
        # Always use a unique logger name to avoid root logger interference
        self._logger = logging.getLogger(f"compass_core.standard_logger.{name}")
        self._logger.setLevel(level)
        # Remove all existing handlers to ensure only our formatter is used
        for h in list(self._logger.handlers):
            self._logger.removeHandler(h)
        handler = logging.StreamHandler(sys.stdout)
        # Formatter: only time (with milliseconds) and message
        class MilliFormatter(logging.Formatter):
            def format(self, record):
                record.msg = record.getMessage()
                record.message = record.msg
                record.asctime = self.formatTime(record, self.datefmt)
                return f"{record.asctime} - {record.message}"
            def formatTime(self, record, datefmt=None):
                ct = self.converter(record.created)
                t = time.strftime('%H:%M:%S', ct)
                s = "%s.%03d" % (t, int(record.msecs))
                return s
        formatter = MilliFormatter()
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        # Write session header
        self._write_session_header()

    @staticmethod
    def make_session_header(date_str=None):
        """Generate the session header string for logs."""
        from datetime import datetime
        if date_str is None:
            date_str = datetime.now().strftime('%B %d, %Y')
        border = '*' * 40
        header = f"\n{border}\n{'Log Session Start':^40}\n{date_str:^40}\n{border}\n"
        return header

    def _write_session_header(self):
        header = self.make_session_header()
        sys.stdout.write(header)
    
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message. Output format: HH:MM:SS.ms - message"""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message. Output format: HH:MM:SS.ms - message"""
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message. Output format: HH:MM:SS.ms - message"""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message. Output format: HH:MM:SS.ms - message"""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message. Output format: HH:MM:SS.ms - message"""
        self._logger.critical(message, *args, **kwargs)


class StandardLoggerFactory(LoggerFactory):
    """
    Standard implementation of LoggerFactory protocol.
    
    This class provides a factory for creating StandardLogger instances with
    optional configuration, implementing the LoggerFactory interface for
    dependency injection compatibility.
    
    Example usage:
        factory = StandardLoggerFactory()
        logger = factory.create_logger("my_app")
        debug_logger = factory.create_logger("debug_app", {"level": "DEBUG"})
    """
    
    def create_logger(self, name: str, config: Optional[dict] = None) -> Logger:
        """
        Create a configured StandardLogger instance.
        
        Args:
            name: Logger name 
            config: Optional configuration dictionary with keys:
                   - level: Logging level (string or int)
                   - format: Custom format string
                   
        Returns:
            StandardLogger instance implementing Logger protocol
        """
        level = logging.INFO  # Default level
        
        if config:
            # Handle level configuration
            config_level = config.get('level', logging.INFO)
            if isinstance(config_level, str):
                level = getattr(logging, config_level.upper(), logging.INFO)
            elif isinstance(config_level, int):
                level = config_level
        
        return StandardLogger(name, level)