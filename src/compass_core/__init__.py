from .engine import CompassRunner
from .json_configuration import JsonConfiguration
from .ini_configuration import IniConfiguration
from .logging import StandardLogger, StandardLoggerFactory

# Define base public API
__all__ = ['CompassRunner', 'JsonConfiguration', 'IniConfiguration', 'StandardLogger', 'StandardLoggerFactory']

# Optional imports - only available if dependencies are installed
try:
    from .selenium_navigator import SeleniumNavigator
    __all__.append('SeleniumNavigator')
except ImportError:
    # selenium not installed - SeleniumNavigator not available
    pass

# DriverManager - requires selenium for WebDriver support
try:
    from .standard_driver_manager import StandardDriverManager
    __all__.append('StandardDriverManager')
except ImportError:
    # selenium not installed - StandardDriverManager not available
    pass

# Windows-only imports - only available on Windows
try:
    from .browser_version_checker import BrowserVersionChecker
    __all__.append('BrowserVersionChecker')
except ImportError:
    # winreg not available (non-Windows) - BrowserVersionChecker not available
    pass