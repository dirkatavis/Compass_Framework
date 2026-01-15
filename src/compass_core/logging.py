"""
Logger Interface for Compass Framework
Protocol for structured logging operations with dependency injection
"""
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