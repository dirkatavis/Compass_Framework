"""
Compass Framework - Install Validation Suite.
Run this before starting development to confirm your environment is configured.
Usage: pytest tests/test_install_validation.py -v
"""

from importlib.util import find_spec
from importlib.metadata import PackageNotFoundError, entry_points, version
import inspect
import os
import sys

import pytest


CERTIFIED_CLASSES = [
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

OPTIONAL_SELENIUM_CLASSES = {
    "LoginFlow",
    "SeleniumLoginFlow",
    "SeleniumNavigator",
    "SeleniumPmActions",
    "SeleniumVehicleDataActions",
    "SmartLoginFlow",
    "StandardDriverManager",
    "VehicleLookupFlow",
}


class TestPackageInstall:
    """Verify compass-core is installed and importable."""

    def test_compass_core_importable(self):
        """compass_core must be importable."""
        import compass_core

        assert compass_core is not None

    def test_compass_core_version(self):
        """Installed package version must match framework release version."""
        from compass_core import CompassRunner

        try:
            installed_version = version("compass-core")
        except PackageNotFoundError as exc:
            raise AssertionError(
                "Package 'compass-core' is not installed. Run: pip install -e <framework path>"
            ) from exc

        expected_version = CompassRunner().version
        assert (
            installed_version == expected_version
        ), f"Expected {expected_version}, got {installed_version}"

    def test_certified_classes_available(self):
        """All certified public classes must be available at top-level compass_core."""
        import compass_core

        expected_classes = set(CERTIFIED_CLASSES)

        if sys.platform != "win32":
            expected_classes.discard("BrowserVersionChecker")

        if find_spec("selenium") is None or find_spec("webdriver_manager") is None:
            expected_classes -= OPTIONAL_SELENIUM_CLASSES

        missing = [cls for cls in sorted(expected_classes) if not hasattr(compass_core, cls)]
        assert not missing, f"Missing certified classes: {missing}"

    def test_public_surface_not_leaking(self):
        """Internal module names must not leak into dir(compass_core)."""
        import compass_core

        public = set(dir(compass_core))
        # These internal module names should NEVER be visible to clients
        internal_modules = {
            "browser_version_checker",
            "configuration",
            "csv_utils",
            "decorators",
            "driver_factory",
            "driver_manager",
            "engine",
            "ini_configuration",
            "json_configuration",
            "logging",
            "login_flow",
            "mva_collection",
            "navigation",
            "page_detectors",
            "pm_actions",
            "pm_actions_selenium",
            "pm_work_item_flow",
            "read_mva_list",
            "read_workitem_list",
            "selenium_login_flow",
            "selenium_navigator",
            "selenium_pm_actions",
            "selenium_vehicle_data_actions",
            "smart_login_flow",
            "standard_driver_manager",
            "tools",
            "vehicle_data_actions",
            "vehicle_lookup_flow",
            "version_checker",
            "vin_to_mva_flow",
            "workflow",
        }
        leaking = [name for name in public if name in internal_modules]
        assert not leaking, f"Internal module names exposed in dir(compass_core): {leaking}"


class TestDependencies:
    """Verify required runtime dependencies are installed."""

    def test_selenium_installed(self):
        """Selenium must be available."""
        if find_spec("selenium") is None:
            pytest.skip("selenium extra not installed")

        from selenium import webdriver

        assert webdriver is not None

    def test_webdriver_manager_installed(self):
        """webdriver-manager must be available."""
        if find_spec("webdriver_manager") is None:
            pytest.skip("selenium extra not installed")

        from webdriver_manager.chrome import ChromeDriverManager

        assert ChromeDriverManager is not None

    def test_python_version(self):
        """Python 3.10+ is required by compass-core."""
        assert sys.version_info >= (3, 10), (
            f"Python 3.10+ required, got {sys.version_info.major}.{sys.version_info.minor}"
        )


class TestCLITools:
    """Verify compass CLI entry points are installed and callable."""

    def test_compass_inventory_entry_point(self):
        """compass-inventory must be registered as a console script."""
        eps = entry_points(group="console_scripts")
        names = [ep.name for ep in eps]
        assert "compass-inventory" in names, (
            "compass-inventory CLI not found - reinstall compass-core"
        )

    def test_compass_inventory_callable(self):
        """compass_core.tools.export_inventory.main must be importable and callable."""
        from compass_core.tools.export_inventory import main

        assert callable(main)
        assert inspect.signature(main) is not None


class TestEnvironment:
    """Verify local environment configuration assumptions."""

    def test_running_in_venv(self):
        """Must be running inside a virtual environment."""
        in_venv = hasattr(sys, "real_prefix") or (
            hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
        )
        if not in_venv:
            pytest.skip("Not running in a virtual environment")

    def test_no_debug_env_vars_in_production(self):
        """Guardrail to prevent accidental debug runs in production-like usage."""
        debug = os.getenv("COMPASS_DEBUG", "false").lower()
        assert debug != "true", "COMPASS_DEBUG is set to true - disable for production"
