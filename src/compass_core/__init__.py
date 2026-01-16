from .engine import CompassRunner

# Define base public API
__all__ = ['CompassRunner']

# Optional imports - only available if dependencies are installed
try:
    from .selenium_navigator import SeleniumNavigator
    __all__.append('SeleniumNavigator')
except ImportError:
    # selenium not installed - SeleniumNavigator not available
    pass