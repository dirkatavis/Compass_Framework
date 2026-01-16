"""
INI Configuration implementation for Compass Framework.

Implements the Configuration protocol using Python's configparser
for reading INI-formatted configuration files.
"""
import configparser
from pathlib import Path
from typing import Dict, Any, Union, Optional
from .configuration import Configuration


class IniConfiguration(Configuration):
    """Configuration implementation using INI files with configparser."""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize INI configuration.
        
        Args:
            config_path: Optional path to INI file. If not provided,
                        will look for webdriver.ini.local then webdriver.ini
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self._data: Dict[str, Any] = {}
        
        # Load configuration on initialization if no path specified
        if config_path is None:
            self._load_default_config()
    
    def _load_default_config(self):
        """Load configuration using default file priority."""
        # Priority: webdriver.ini.local -> webdriver.ini -> empty config
        default_files = ['webdriver.ini.local', 'webdriver.ini']
        
        for filename in default_files:
            if Path(filename).exists():
                self.load(filename)
                break
    
    def load(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from INI file.
        
        Args:
            file_path: Path to the INI configuration file
            
        Returns:
            Dictionary representation of loaded configuration
            
        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            configparser.Error: If the INI file is malformed
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Read the INI file
        self.config.read(file_path)
        self.config_path = file_path
        
        # Convert configparser sections to nested dictionary
        self._data = {}
        for section_name in self.config.sections():
            section_dict = {}
            for key, value in self.config.items(section_name):
                # Try to convert common types
                section_dict[key] = self._convert_value(value)
            self._data[section_name] = section_dict
        
        return self._data.copy()
    
    def _convert_value(self, value: str) -> Any:
        """Convert string values to appropriate types."""
        # Convert boolean-like strings
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        elif value.lower() in ('false', 'no', 'off', '0'):
            return False
        
        # Try to convert to int
        try:
            return int(value)
        except ValueError:
            # Not a valid integer, try float conversion instead
            pass
        
        # Try to convert to float  
        try:
            return float(value)
        except ValueError:
            # Not a valid float either, return as-is
            pass
        
        # Return as string
        return value
    
    def save(self, config: Dict[str, Any], destination: Union[str, Path]) -> bool:
        """
        Save configuration to INI file.
        
        Args:
            config: Configuration data to save
            destination: Destination path for the INI file
            
        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            destination = Path(destination)
            
            # Ensure parent directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Create new configparser with provided data
            output_config = configparser.ConfigParser()
            
            for section_name, section_data in config.items():
                output_config.add_section(section_name)
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        output_config.set(section_name, key, str(value))
                else:
                    # Handle flat key-value pairs in a default section
                    output_config.set(section_name, str(section_data), '')
            
            # Write to file
            with open(destination, 'w') as configfile:
                output_config.write(configfile)
                
            return True
            
        except Exception:
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Supports dot notation for nested access (e.g., 'webdriver.edge_path').
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if '.' in key:
            section, option = key.split('.', 1)
            return self._data.get(section, {}).get(option, default)
        else:
            # Look for key in any section
            for section_data in self._data.values():
                if key in section_data:
                    return section_data[key]
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set configuration value by key.
        
        Supports dot notation for nested setting (e.g., 'webdriver.edge_path').
        
        Args:
            key: Configuration key (supports dot notation)  
            value: Value to set
            
        Returns:
            bool: True if set successful, False otherwise
        """
        try:
            if '.' in key:
                section, option = key.split('.', 1)
                if section not in self._data:
                    self._data[section] = {}
                self._data[section][option] = value
            else:
                # Default to 'DEFAULT' section for simple keys
                if 'DEFAULT' not in self._data:
                    self._data['DEFAULT'] = {}
                self._data['DEFAULT'][key] = value
            return True
        except Exception:
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration data.
        
        Returns:
            Copy of entire configuration dictionary
        """
        return self._data.copy()
    
    def validate(self, config_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate configuration data.
        
        Args:
            config_data: Optional configuration to validate. 
                        If None, validates current configuration.
                        
        Returns:
            Dictionary with validation results:
            {
                "status": str,  # "valid" or "invalid"
                "warnings": List[str],
                "errors": List[str]
            }
        """
        if config_data is None:
            config_data = self._data
        
        warnings = []
        errors = []
        
        # Check if configuration is empty
        if not config_data:
            warnings.append("Configuration is empty")
        
        # Check for webdriver section
        webdriver_section = config_data.get('webdriver', {})
        if webdriver_section:
            # Check driver paths exist
            for driver_type in ['edge_path', 'chrome_path']:
                if driver_type in webdriver_section:
                    driver_path = Path(webdriver_section[driver_type])
                    if not driver_path.exists():
                        errors.append(f"Driver not found: {driver_path}")
                    elif not driver_path.is_file():
                        errors.append(f"Driver path is not a file: {driver_path}")
        
        # Check timeout values
        timeouts_section = config_data.get('timeouts', {})
        for timeout_key in ['page_load', 'implicit_wait']:
            if timeout_key in timeouts_section:
                timeout_value = timeouts_section[timeout_key]
                if not isinstance(timeout_value, (int, float)) or timeout_value <= 0:
                    errors.append(f"Invalid timeout value for {timeout_key}: {timeout_value}")
        
        return {
            "status": "valid" if len(errors) == 0 else "invalid",
            "warnings": warnings,
            "errors": errors
        }