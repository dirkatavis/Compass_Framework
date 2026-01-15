from .engine import CompassRunner

# Optional imports - only available if dependencies are installed
try:
    from .selenium_navigator import SeleniumNavigator
except ImportError:
    # selenium not installed - SeleniumNavigator not available
    pass