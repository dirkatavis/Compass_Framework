from .engine import CompassRunner
from .json_configuration import JsonConfiguration
from .ini_configuration import IniConfiguration
from .logging import StandardLogger, StandardLoggerFactory
from .workflow import StandardWorkflowManager

# Optional PM flow - available when workflow protocols are present
try:
    from .pm_work_item_flow import PmWorkItemFlow
except ImportError:
    PmWorkItemFlow = None  # type: ignore

# Define base public API
__all__ = [
    'CompassRunner',
    'JsonConfiguration',
    'IniConfiguration',
    'StandardLogger',
    'StandardLoggerFactory',
    'StandardWorkflowManager'
]
if PmWorkItemFlow is not None:
    __all__.append('PmWorkItemFlow')

# Optional imports - only available if dependencies are installed
try:
    from .selenium_navigator import SeleniumNavigator
    __all__.append('SeleniumNavigator')
except ImportError:
    # selenium not installed - SeleniumNavigator not available
    pass

# Optional Selenium-backed PM actions - available when selenium and protocol present
try:
    from .pm_actions_selenium import SeleniumPmActions
    __all__.append('SeleniumPmActions')
except ImportError:
    # selenium or pm_actions not installed - SeleniumPmActions not available
    pass

# Optional Vehicle Data Actions - available when selenium installed
try:
    from .selenium_vehicle_data_actions import SeleniumVehicleDataActions
    __all__.append('SeleniumVehicleDataActions')
except ImportError:
    # selenium not installed - SeleniumVehicleDataActions not available
    pass

# DriverManager - requires selenium for WebDriver support
try:
    from .standard_driver_manager import StandardDriverManager
    __all__.append('StandardDriverManager')
except ImportError:
    # selenium not installed - StandardDriverManager not available
    pass

# LoginFlow - authentication protocol and Selenium implementation
try:
    from .login_flow import LoginFlow
    __all__.append('LoginFlow')
    
    from .selenium_login_flow import SeleniumLoginFlow
    __all__.append('SeleniumLoginFlow')
    
    from .smart_login_flow import SmartLoginFlow
    __all__.append('SmartLoginFlow')
except ImportError:
    # selenium not installed - LoginFlow components not available
    pass

# VehicleLookupFlow - batch MVA processing workflow
try:
    from .vehicle_lookup_flow import VehicleLookupFlow
    __all__.append('VehicleLookupFlow')
except ImportError:
    # Dependencies not installed - VehicleLookupFlow not available
    pass

# CSV utilities - MVA list reading and results writing
try:
    from .csv_utils import read_mva_list, write_results_csv
    __all__.extend(['read_mva_list', 'write_results_csv'])
except ImportError:
    # CSV utilities not available
    pass

# MVA collection management - data structures for MVA tracking
try:
    from .mva_collection import MvaCollection, MvaItem, MvaStatus
    __all__.extend(['MvaCollection', 'MvaItem', 'MvaStatus'])
except ImportError:
    # MVA collection not available
    pass

# Windows-only imports - only available on Windows
try:
    from .browser_version_checker import BrowserVersionChecker
    __all__.append('BrowserVersionChecker')
except ImportError:
    # winreg not available (non-Windows) - BrowserVersionChecker not available
    pass

# Note: Additional public API exports (e.g., WorkflowManager, flows, and Selenium-backed PM actions)
# will be added once their modules land on main to avoid misleading API entries and ImportErrors.