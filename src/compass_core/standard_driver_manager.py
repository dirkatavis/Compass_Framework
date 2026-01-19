"""
StandardDriverManager implementation for WebDriver lifecycle management.

Concrete implementation of DriverManager protocol supporting Edge WebDriver
with singleton pattern, based on DevCompass driver_manager.py patterns.
"""
import subprocess
import re
import os
import logging
from typing import Any, Dict, Optional
from selenium import webdriver
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from .driver_manager import DriverManager


class StandardDriverManager(DriverManager):
    """Standard implementation of DriverManager protocol for Edge WebDriver.
    
    Provides singleton WebDriver management with version compatibility checking
    and comprehensive configuration options.
    """
    
    def __init__(self, driver_path: Optional[str] = None):
        """Initialize StandardDriverManager.
        
        Args:
            driver_path: Path to WebDriver executable. If None, uses INI config or default path.
        """
        self._driver: Optional[WebDriver] = None
        self._config: Optional[Any] = None  # Cached configuration instance
        self._driver_path = driver_path or self._get_configured_driver_path()
        self._logger = logging.getLogger(__name__)
        
    def _get_config(self):
        """Get cached configuration instance, creating it if needed."""
        if self._config is None:
            try:
                from .ini_configuration import IniConfiguration
                self._config = IniConfiguration()  # Auto-loads webdriver.ini.local or webdriver.ini
            except Exception as e:
                self._logger.debug(f"[DRIVER] Could not load INI config: {e}")
                self._config = None  # Mark as failed to avoid retries
        return self._config
        
    def _get_configured_driver_path(self) -> str:
        """Get driver path from INI configuration with fallback to default."""
        config = self._get_config()
        if config is not None:
            # Try to get edge_path from cached configuration
            edge_path = config.get('webdriver.edge_path')
            if edge_path and os.path.exists(edge_path):
                return edge_path
        
        # Fallback to default path
        return self._get_default_driver_path()
        
    def _get_default_driver_path(self) -> str:
        """Get default driver path based on project structure."""
        # Try local drivers first
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        local_path = os.path.join(project_root, "drivers.local", "msedgedriver.exe")
        if os.path.exists(local_path):
            return local_path
            
        # Fallback to project root (original pattern)
        default_path = os.path.join(project_root, "msedgedriver.exe")
        return default_path
        
    def get_or_create_driver(self, **kwargs) -> WebDriver:
        """Get existing driver or create new Edge WebDriver instance.
        
        Implements singleton pattern from DevCompass driver_manager.py.
        Includes version compatibility checking before driver creation.
        
        Args:
            **kwargs: Driver configuration options (headless, window_size, etc.)
            
        Returns:
            WebDriver: Active Edge WebDriver instance
            
        Raises:
            RuntimeError: If version mismatch or driver creation fails
        """
        if self._driver:
            return self._driver
            
        # Version compatibility check (like DevCompass pattern)
        browser_version = self._get_browser_version()
        driver_version = self.get_driver_version(self._driver_path)
        
        self._logger.info(f"[DRIVER] Detected Browser={browser_version}, Driver={driver_version}")
        
        compatibility = self.check_version_compatibility(browser_version, driver_version)
        if not compatibility["compatible"]:
            error_msg = f"Version mismatch - Browser {browser_version}, Driver {driver_version}"
            self._logger.error(f"[DRIVER] {error_msg}")
            raise RuntimeError(error_msg)
            
        try:
            self._logger.info(f"[DRIVER] Launching Edge - Browser {browser_version}, Driver {driver_version}")
            options = self.configure_driver_options()
            
            # Apply any custom configuration from kwargs
            if kwargs.get("headless", False):
                options.add_argument("--headless")
            if kwargs.get("incognito", False):
                options.add_argument("--inprivate")
                self._logger.info("[DRIVER] InPrivate mode enabled")
            if "window_size" in kwargs:
                width, height = kwargs["window_size"]
                options.add_argument(f"--window-size={width},{height}")
                
            service = self.create_driver_service(self._driver_path)
            self._driver = webdriver.Edge(service=service, options=options)
            
            # Default DevCompass configuration
            self._driver.maximize_window()
            self._driver.implicitly_wait(10)
            
            return self._driver
            
        except SessionNotCreatedException as e:
            self._logger.error(f"[DRIVER] Session creation failed: {e}")
            raise RuntimeError(f"Failed to create WebDriver session: {e}")
    
    def quit_driver(self) -> None:
        """Quit and cleanup WebDriver instance.
        
        Implements DevCompass singleton cleanup pattern.
        Safe to call multiple times or when no driver exists.
        """
        if self._driver:
            self._logger.info("[DRIVER] Quitting Edge WebDriver...")
            try:
                self._driver.quit()
            except Exception as e:
                self._logger.warning(f"[DRIVER] Exception during quit: {e}")
            finally:
                self._driver = None
    
    def get_driver_version(self, driver_path: str) -> str:
        """Get version of Edge WebDriver executable.
        
        Based on DevCompass get_driver_version function.
        
        Args:
            driver_path: Path to WebDriver executable
            
        Returns:
            str: Version string (e.g., "120.0.6099.109") or "unknown"
        """
        if not os.path.exists(driver_path):
            self._logger.error(f"[DRIVER] Driver binary not found at {driver_path}")
            return "unknown"
            
        try:
            output = subprocess.check_output([driver_path, "--version"], text=True, timeout=10)
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
            if match:
                return match.group(1)
            else:
                self._logger.warning(f"[DRIVER] No version pattern found in output: {output}")
                return "unknown"
        except subprocess.TimeoutExpired:
            self._logger.error(f"[DRIVER] Timeout getting version from {driver_path}")
            return "unknown"
        except Exception as e:
            self._logger.error(f"[DRIVER] Failed to get driver version from {driver_path} - {e}")
            return "unknown"
    
    def configure_driver_options(self) -> EdgeOptions:
        """Configure Edge browser options.
        
        Based on DevCompass driver configuration patterns.
        
        Returns:
            EdgeOptions: Configured options for Edge WebDriver
        """
        options = EdgeOptions()
        
        # DevCompass standard configuration
        options.add_argument("--start-maximized")
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 2
        })
        
        # Additional stability options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        return options
    
    def create_driver_service(self, driver_path: str) -> Service:
        """Create Edge WebDriver service.
        
        Args:
            driver_path: Path to Edge WebDriver executable
            
        Returns:
            Service: Configured service for Edge WebDriver
        """
        return Service(driver_path)
    
    def is_driver_active(self) -> bool:
        """Check if WebDriver instance is currently active.
        
        Returns:
            bool: True if active driver exists, False otherwise
        """
        if not self._driver:
            return False
            
        try:
            # Test if driver is responsive
            _ = self._driver.current_url
            return True
        except Exception:
            # Driver session is dead
            self._driver = None
            return False
    
    def check_version_compatibility(self, browser_version: str, driver_version: str) -> Dict[str, Any]:
        """Check compatibility between browser and driver versions.
        
        Based on DevCompass version checking logic.
        
        Args:
            browser_version: Browser version string
            driver_version: Driver version string
            
        Returns:
            Dict with compatibility status and recommendations
        """
        if browser_version == "unknown" or driver_version == "unknown":
            return {
                "compatible": False,
                "status": "version_unknown",
                "reason": "Cannot determine version compatibility",
                "recommendation": "Verify browser and driver installation"
            }
            
        try:
            browser_major = browser_version.split(".")[0]
            driver_major = driver_version.split(".")[0]
            
            if browser_major == driver_major:
                return {
                    "compatible": True,
                    "status": "ok",
                    "browser_version": browser_version,
                    "driver_version": driver_version
                }
            else:
                return {
                    "compatible": False,
                    "status": "major_version_mismatch",
                    "reason": f"Major version mismatch: Browser {browser_major}.x vs Driver {driver_major}.x",
                    "recommendation": f"Update driver to version {browser_major}.x.x.x",
                    "browser_version": browser_version,
                    "driver_version": driver_version
                }
        except (IndexError, ValueError, AttributeError) as e:
            return {
                "compatible": False,
                "status": "parse_error",
                "reason": f"Failed to parse versions: {e}",
                "recommendation": "Check version format"
            }
    
    def _get_browser_version(self) -> str:
        """Get installed Edge browser version from Windows registry.
        
        Based on DevCompass get_browser_version function.
        
        Returns:
            str: Browser version or "unknown"
        """
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Edge\BLBeacon")
            value, _ = winreg.QueryValueEx(key, "version")
            winreg.CloseKey(key)
            return value
        except ImportError:
            # winreg not available (non-Windows)
            self._logger.warning("[DRIVER] winreg not available - cannot detect browser version")
            return "unknown"
        except Exception as e:
            self._logger.error(f"[DRIVER] Failed to get browser version: {e}")
            return "unknown"