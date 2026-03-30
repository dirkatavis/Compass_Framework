from .decorators import compass_public
from .engine import CompassRunner
from .json_configuration import JsonConfiguration
from .ini_configuration import IniConfiguration
from .logging import StandardLogger, StandardLoggerFactory
from .workflow import StandardWorkflowManager, FlowContext, WorkflowStep, Workflow, WorkflowManager
try:
    from .driver_factory import DriverFactory
except ImportError:
    # selenium not installed - DriverFactory not available
    DriverFactory = None  # type: ignore

from .configuration import Configuration

try:
    from .driver_manager import DriverManager
except ImportError:
    # selenium not installed - DriverManager not available
    DriverManager = None  # type: ignore
from .logging import Logger, LoggerFactory
from .navigation import Navigator
from .pm_actions import PmActions
from .vehicle_data_actions import VehicleDataActions
from .version_checker import VersionChecker
from .csv_utils import read_mva_list, write_results_csv, read_workitem_list

# Optional PM flow - available when workflow protocols are present
try:
    from .pm_work_item_flow import PmWorkItemFlow
except ImportError:
    pass

# Optional Vin2Mva flow
try:
    from .vin_to_mva_flow import Vin2MvaFlow
except ImportError:
    pass

# Optional imports - only available if dependencies are installed
try:
    from .selenium_navigator import SeleniumNavigator
except ImportError:
    SeleniumNavigator = None  # type: ignore

# Optional Selenium-backed PM actions - available when selenium and protocol present
try:
    from .pm_actions_selenium import SeleniumPmActions
except ImportError:
    SeleniumPmActions = None  # type: ignore

# Optional Vehicle Data Actions - available when selenium installed
try:
    from .selenium_vehicle_data_actions import SeleniumVehicleDataActions
except ImportError:
    SeleniumVehicleDataActions = None  # type: ignore

# DriverManager - requires selenium for WebDriver support
try:
    from .standard_driver_manager import StandardDriverManager
except ImportError:
    StandardDriverManager = None  # type: ignore

# LoginFlow - authentication protocol and Selenium implementation
try:
    from .login_flow import LoginFlow
    from .selenium_login_flow import SeleniumLoginFlow
    from .smart_login_flow import SmartLoginFlow
except ImportError:
    LoginFlow = None  # type: ignore
    SeleniumLoginFlow = None  # type: ignore
    SmartLoginFlow = None  # type: ignore

# VehicleLookupFlow - batch MVA processing workflow
try:
    from .vehicle_lookup_flow import VehicleLookupFlow
except ImportError:
    VehicleLookupFlow = None  # type: ignore

# MVA collection management - data structures for MVA tracking
try:
    from .mva_collection import MvaCollection, MvaItem, MvaStatus
except ImportError:
    MvaCollection = None  # type: ignore
    MvaItem = None  # type: ignore
    MvaStatus = None  # type: ignore

# Windows-only imports - only available on Windows
try:
    from .browser_version_checker import BrowserVersionChecker
except ImportError:
    BrowserVersionChecker = None  # type: ignore

_CERTIFIED_EXPORTS = [
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
    "read_mva_list",
    "write_results_csv",
    "read_workitem_list",
]

__all__ = [name for name in _CERTIFIED_EXPORTS if name in globals()]


def __dir__():
    return __all__
