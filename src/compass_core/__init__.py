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

# Optional imports - only available if dependencies are installed
try:
    from .selenium_navigator import SeleniumNavigator
except ImportError:
    # selenium not installed - SeleniumNavigator not available
    pass

# Optional Selenium-backed PM actions - available when selenium and protocol present
try:
    from .pm_actions_selenium import SeleniumPmActions
except ImportError:
    # selenium or pm_actions not installed - SeleniumPmActions not available
    pass

# Optional Vehicle Data Actions - available when selenium installed
try:
    from .selenium_vehicle_data_actions import SeleniumVehicleDataActions
except ImportError:
    # selenium not installed - SeleniumVehicleDataActions not available
    pass

# DriverManager - requires selenium for WebDriver support
try:
    from .standard_driver_manager import StandardDriverManager
except ImportError:
    # selenium not installed - StandardDriverManager not available
    pass

# LoginFlow - authentication protocol and Selenium implementation
try:
    from .login_flow import LoginFlow
    
    from .selenium_login_flow import SeleniumLoginFlow
    
    from .smart_login_flow import SmartLoginFlow
except ImportError:
    # selenium not installed - LoginFlow components not available
    pass

# VehicleLookupFlow - batch MVA processing workflow
try:
    from .vehicle_lookup_flow import VehicleLookupFlow
except ImportError:
    # Dependencies not installed - VehicleLookupFlow not available
    pass

# MVA collection management - data structures for MVA tracking
try:
    from .mva_collection import MvaCollection, MvaItem, MvaStatus
except ImportError:
    # MVA collection not available
    pass

# Windows-only imports - only available on Windows
try:
    from .browser_version_checker import BrowserVersionChecker
except ImportError:
    # winreg not available (non-Windows) - BrowserVersionChecker not available
    pass

__all__ = [
    "BrowserVersionChecker",
    "CompassRunner",
    "Configuration",
    "DriverFactory",
    "DriverManager",
    "FlowContext",
    "IniConfiguration",
    "JsonConfiguration",
    "Logger",
    "LoggerFactory",
    "LoginFlow",
    "MvaCollection",
    "MvaItem",
    "MvaStatus",
    "Navigator",
    "PmActions",
    "PmWorkItemFlow",
    "SeleniumLoginFlow",
    "SeleniumNavigator",
    "SeleniumPmActions",
    "SeleniumVehicleDataActions",
    "SmartLoginFlow",
    "StandardDriverManager",
    "StandardLogger",
    "StandardLoggerFactory",
    "StandardWorkflowManager",
    "VehicleDataActions",
    "VehicleLookupFlow",
    "VersionChecker",
    "Vin2MvaFlow",
    "Workflow",
    "WorkflowManager",
    "WorkflowStep",
]


def __dir__():
    return __all__
