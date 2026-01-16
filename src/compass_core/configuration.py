"""
Configuration Interface for Compass Framework
Protocol for configuration loading, saving, and validation operations
"""
from typing import Protocol, runtime_checkable, Dict, Any, Optional, Union
from pathlib import Path


@runtime_checkable
class Configuration(Protocol):
    """Protocol for configuration management operations"""
    
    def load(self, source: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from a source (file path, URL, etc.)"""
        ...
    
    def save(self, config: Dict[str, Any], destination: Union[str, Path]) -> bool:
        """Save configuration to a destination"""
        ...
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value by key"""
        ...
    
    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value"""
        ...
    
    def validate(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate configuration structure and values"""
        ...