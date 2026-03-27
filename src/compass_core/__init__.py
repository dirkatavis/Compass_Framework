from .decorators import compass_public
from .engine import CompassRunner
from .json_configuration import JsonConfiguration
from .ini_configuration import IniConfiguration
from .logging import StandardLogger, StandardLoggerFactory
from .workflow import StandardWorkflowManager, FlowContext, WorkflowStep, Workflow, WorkflowManager
from .driver_factory import DriverFactory
from .configuration import Configuration
from .driver_manager import DriverManager
from .logging import Logger, LoggerFactory
from .navigation import Navigator
from .pm_actions import PmActions
from .vehicle_data_actions import VehicleDataActions
from .version_checker import VersionChecker

# Optional PM flow - available when workflow protocols are present
try:
    from .pm_work_item_flow import PmWorkItemFlow
except ImportError:
    PmWorkItemFlow = None  # type: ignore

# Optional Vin2Mva flow
try:
    from .vin_to_mva_flow import Vin2MvaFlow
except ImportError:
    Vin2MvaFlow = None  # type: ignore

# Define base public API  – all certified protocol and implementation classes
__all__ = [
    # Decorator marker
    'compass_public',
    # Entry point
    'CompassRunner',
    # Configuration protocol + implementations
    'Configuration',
    'IniConfiguration',
    'JsonConfiguration',
    # Driver management
    'DriverFactory',
    'DriverManager',
    # Logging protocol + implementations
    'Logger',
    'LoggerFactory',
    'StandardLogger',
    'StandardLoggerFactory',
    # Navigation protocol
    'Navigator',
    # PM actions protocol
    'PmActions',
    # Vehicle data protocol
    'VehicleDataActions',
    # Version checking protocol
    'VersionChecker',
    # Workflow protocols + implementation
    'Workflow',
    'WorkflowManager',
    'WorkflowStep',
    'FlowContext',
    'StandardWorkflowManager',
]
if PmWorkItemFlow is not None:
    __all__.append('PmWorkItemFlow')

if Vin2MvaFlow is not None:
    __all__.append('Vin2MvaFlow')

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
    from .csv_utils import read_mva_list, write_results_csv, read_workitem_list
    __all__.extend(['read_mva_list', 'write_results_csv', 'read_workitem_list'])
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