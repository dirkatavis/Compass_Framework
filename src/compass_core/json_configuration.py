"""
JsonConfiguration - Concrete implementation of Configuration protocol.

This module provides a JSON-based implementation of the Configuration
interface, enabling configuration loading, saving, and management operations.
"""
import json
from typing import Dict, Any, Optional, Union
from pathlib import Path

from .configuration import Configuration


class JsonConfiguration(Configuration):
    """
    JSON-based implementation of Configuration protocol.
    
    This class provides concrete configuration functionality using JSON files,
    implementing the Configuration interface for dependency injection compatibility.
    
    Example usage:
        config = JsonConfiguration()
        data = config.load("settings.json")
        config.set("api_key", "your-key-here")
        config.save(config.get_all(), "updated_settings.json")
        validation = config.validate()
    """
    
    def __init__(self):
        """Initialize JsonConfiguration with empty config."""
        self._config: Dict[str, Any] = {}
    
    def load(self, source: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from a JSON file.
        
        Args:
            source: Path to JSON file (string or Path object)
            
        Returns:
            Dictionary containing loaded configuration data
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
            IOError: If file cannot be read
        """
        try:
            source_path = Path(source)
            
            if not source_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {source}")
            
            with open(source_path, 'r', encoding='utf-8') as file:
                self._config = json.load(file)
                return self._config.copy()
                
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in configuration file {source}: {e.msg}",
                e.doc,
                e.pos
            )
        except (IOError, OSError) as e:
            # Only catch actual IO errors, not our FileNotFoundError
            if isinstance(e, FileNotFoundError):
                raise  # Re-raise FileNotFoundError as-is
            raise IOError(f"Cannot read configuration file {source}: {e}")
    
    def save(self, config: Dict[str, Any], destination: Union[str, Path]) -> bool:
        """
        Save configuration to a JSON file.
        
        Args:
            config: Configuration dictionary to save
            destination: Target file path (string or Path object)
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            dest_path = Path(destination)
            
            # Create parent directories if they don't exist
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dest_path, 'w', encoding='utf-8') as file:
                json.dump(config, file, indent=2, ensure_ascii=False)
            
            return True
            
        except (IOError, TypeError) as e:
            # Log error in real implementation
            return False
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value by key.
        
        Supports nested keys using dot notation (e.g., "database.host").
        
        Args:
            key: Configuration key (supports dot notation for nested values)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            value = self._config
            
            # Handle nested keys with dot notation
            for part in key.split('.'):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set a configuration value.
        
        Supports nested keys using dot notation (e.g., "database.host").
        Creates nested dictionaries as needed.
        
        Args:
            key: Configuration key (supports dot notation for nested values)
            value: Value to set
            
        Returns:
            True if set successful, False otherwise
        """
        try:
            if '.' in key:
                # Handle nested keys
                keys = key.split('.')
                current = self._config
                
                # Navigate to parent of target key, creating dicts as needed
                for part in keys[:-1]:
                    if part not in current or not isinstance(current[part], dict):
                        current[part] = {}
                    current = current[part]
                
                # Set the final value
                current[keys[-1]] = value
            else:
                # Simple key
                self._config[key] = value
            
            return True
            
        except (TypeError, AttributeError):
            return False
    
    def validate(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate configuration structure and values.
        
        Args:
            config: Configuration to validate (uses current if None)
            
        Returns:
            Dictionary with validation results:
            - status: 'valid' or 'invalid'
            - errors: List of validation error messages
            - warnings: List of validation warnings
        """
        target_config = config if config is not None else self._config
        errors = []
        warnings = []
        
        try:
            # Basic JSON serialization test
            json.dumps(target_config)
            
            # Check for common configuration issues
            if not isinstance(target_config, dict):
                errors.append("Configuration must be a dictionary")
            
            # Check for circular references (would fail JSON serialization)
            # This is implicitly tested by json.dumps above
            
            # Add any custom validation rules here
            if isinstance(target_config, dict):
                # Example: warn about empty configuration
                if not target_config:
                    warnings.append("Configuration is empty")
                
                # Example: check for sensitive data that shouldn't be in config
                sensitive_keys = ['password', 'secret', 'token', 'api_key']
                for key in target_config:
                    if any(sensitive in key.lower() for sensitive in sensitive_keys):
                        warnings.append(f"Potential sensitive data in key: {key}")
        
        except (TypeError, ValueError) as e:
            errors.append(f"Configuration is not JSON serializable: {e}")
        
        return {
            'status': 'valid' if not errors else 'invalid',
            'errors': errors,
            'warnings': warnings
        }
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get a copy of the current configuration.
        
        Returns:
            Dictionary containing all current configuration data
        """
        return self._config.copy()