"""
Logger Interface for Compass Framework
Protocol for structured logging operations with dependency injection
"""
import logging
import sys
from .decorators import compass_public
from typing import Protocol, runtime_checkable, Optional, Any


@compass_public
@runtime_checkable
class Logger(Protocol):
    """Protocol for logging operations"""
    
    @compass_public
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message"""
        ...
    
    @compass_public
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message"""
        ...
    
    @compass_public
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message"""
        ...
    
    @compass_public
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message"""
        ...
    
    @compass_public
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message"""
        ...


@compass_public
@runtime_checkable  
class LoggerFactory(Protocol):
    """Protocol for creating logger instances with configuration"""
    
    @compass_public
    def create_logger(self, name: str, config: Optional[dict] = None) -> Logger:
        """Create a configured logger instance"""
        ...


@compass_public
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
        
        Args:
            name: Logger name (typically module or application name)
            level: Logging level (default: INFO)
        """
        self.name = name
        # Convert string levels to logging constants
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.level = level
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        
        # Only add handler if none exist (avoid duplicate handlers)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    @compass_public
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self._logger.debug(message, *args, **kwargs)
    
    @compass_public
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self._logger.info(message, *args, **kwargs)
    
    @compass_public
    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self._logger.warning(message, *args, **kwargs)
    
    @compass_public
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self._logger.error(message, *args, **kwargs)
    
    @compass_public
    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a critical message."""
        self._logger.critical(message, *args, **kwargs)


@compass_public
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
    
    @compass_public
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