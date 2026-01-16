"""
BrowserVersionChecker - Concrete implementation of VersionChecker protocol.

This module provides Windows-based browser version detection for Chrome and Edge,
implementing the VersionChecker interface for dependency injection compatibility.
"""
import os
import re
import subprocess
import winreg
from typing import Optional

from .version_checker import VersionChecker


class BrowserVersionChecker(VersionChecker):
    """
    Windows browser version detection implementation.
    
    This class provides concrete browser version checking functionality for
    Chrome and Edge browsers on Windows, implementing the VersionChecker 
    interface for dependency injection compatibility.
    
    Example usage:
        checker = BrowserVersionChecker()
        chrome_version = checker.get_browser_version()  # Default: Chrome
        edge_version = checker.get_edge_version()
        driver_version = checker.get_driver_version("chromedriver.exe")
    """
    
    def __init__(self):
        """Initialize BrowserVersionChecker."""
        pass
    
    def get_browser_version(self) -> str:
        """
        Get Chrome browser version (default browser for automation).
        
        Returns:
            Chrome version string, or 'unknown' if not found
            
        Example:
            "131.0.6778.85"
        """
        return self._get_chrome_version()
    
    def get_edge_version(self) -> str:
        """
        Get Microsoft Edge browser version.
        
        Returns:
            Edge version string, or 'unknown' if not found
            
        Example:
            "131.0.2903.70"
        """
        return self._get_edge_version()
    
    def get_driver_version(self, driver_path: str) -> str:
        """
        Get WebDriver version from executable.
        
        Args:
            driver_path: Path to WebDriver executable (chromedriver.exe, msedgedriver.exe)
            
        Returns:
            Driver version string, or 'unknown' if not found/accessible
            
        Example:
            "131.0.6778.85"
        """
        return self._get_driver_version_from_executable(driver_path)
    
    def _get_chrome_version(self) -> str:
        """Get Chrome version using multiple detection methods."""
        # Method 1: Try registry
        version = self._get_chrome_version_from_registry()
        if version != 'unknown':
            return version
            
        # Method 2: Try executable version
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                version = self._get_version_from_executable(path)
                if version != 'unknown':
                    return version
        
        return 'unknown'
    
    def _get_edge_version(self) -> str:
        """Get Edge version using multiple detection methods."""
        # Method 1: Try registry
        version = self._get_edge_version_from_registry()
        if version != 'unknown':
            return version
            
        # Method 2: Try executable version
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        
        for path in edge_paths:
            if os.path.exists(path):
                version = self._get_version_from_executable(path)
                if version != 'unknown':
                    return version
        
        return 'unknown'
    
    def _get_chrome_version_from_registry(self) -> str:
        """Get Chrome version from Windows Registry."""
        try:
            # Try multiple registry locations for Chrome
            registry_paths = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Google\Chrome\BLBeacon"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon")
            ]
            
            for hkey, subkey in registry_paths:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        version, _ = winreg.QueryValueEx(key, "version")
                        if version:
                            return str(version)
                except (FileNotFoundError, OSError):
                    continue
                    
        except Exception:
            pass
        
        return 'unknown'
    
    def _get_edge_version_from_registry(self) -> str:
        """Get Edge version from Windows Registry."""
        try:
            # Try multiple registry locations for Edge
            registry_paths = [
                (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Edge\BLBeacon"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Edge\BLBeacon"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Edge\BLBeacon")
            ]
            
            for hkey, subkey in registry_paths:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        version, _ = winreg.QueryValueEx(key, "version")
                        if version:
                            return str(version)
                except (FileNotFoundError, OSError):
                    continue
                    
        except Exception:
            pass
        
        return 'unknown'
    
    def _get_version_from_executable(self, exe_path: str) -> str:
        """Get version by executing browser with --version flag."""
        try:
            result = subprocess.run(
                [exe_path, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract version number from output
                # Chrome: "Google Chrome 131.0.6778.85"
                # Edge: "Microsoft Edge 131.0.2903.70"
                version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                if version_match:
                    return version_match.group(1)
                    
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return 'unknown'
    
    def _get_driver_version_from_executable(self, driver_path: str) -> str:
        """Get WebDriver version from executable."""
        try:
            # Check if file exists
            if not os.path.exists(driver_path):
                return 'unknown'
                
            result = subprocess.run(
                [driver_path, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract version number from output
                # ChromeDriver: "ChromeDriver 131.0.6778.85"
                version_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout)
                if version_match:
                    return version_match.group(1)
                    
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        
        return 'unknown'
    
    def check_compatibility(self, browser_type: str = "chrome", driver_path: str = None) -> dict:
        """
        Check compatibility between browser and driver versions.
        
        Args:
            browser_type: "chrome" or "edge" (default: "chrome")
            driver_path: Optional path to driver executable for driver version check
            
        Returns:
            Dictionary with compatibility information:
            {
                "browser_version": "131.0.6778.85",
                "driver_version": "131.0.6778.85" or "unknown",
                "compatible": True/False,
                "major_match": True/False,
                "exact_match": True/False,
                "recommendation": "descriptive message"
            }
        """
        # Get browser version
        if browser_type.lower() == "edge":
            browser_version = self.get_edge_version()
            default_driver = "msedgedriver.exe"
        else:
            browser_version = self.get_browser_version()
            default_driver = "chromedriver.exe"
        
        # Get driver version
        driver_version = "unknown"
        if driver_path:
            driver_version = self.get_driver_version(driver_path)
        elif driver_path is None:
            # Try to find driver in common locations
            driver_version = self.get_driver_version(default_driver)
        
        # Analyze compatibility
        result = {
            "browser_version": browser_version,
            "driver_version": driver_version,
            "compatible": False,
            "major_match": False,
            "exact_match": False,
            "recommendation": ""
        }
        
        if browser_version == "unknown" and driver_version == "unknown":
            result["recommendation"] = f"Both {browser_type} browser and driver not found. Please install both."
        elif browser_version == "unknown":
            result["recommendation"] = f"{browser_type.title()} browser not found. Please install {browser_type}."
        elif driver_version == "unknown":
            result["recommendation"] = f"Driver not found at {driver_path or default_driver}. Please install WebDriver."
        else:
            # Both versions detected, check compatibility
            try:
                browser_major = int(browser_version.split('.')[0])
                driver_major = int(driver_version.split('.')[0])
                
                result["exact_match"] = browser_version == driver_version
                result["major_match"] = browser_major == driver_major
                
                # Chrome/Edge drivers generally require major version match
                result["compatible"] = result["major_match"]
                
                if result["exact_match"]:
                    result["recommendation"] = "Perfect version match. Automation should work reliably."
                elif result["major_match"]:
                    result["recommendation"] = f"Major versions match ({browser_major}). Should work, but exact match preferred."
                else:
                    version_gap = abs(browser_major - driver_major)
                    if browser_major > driver_major:
                        result["recommendation"] = f"Driver too old (gap: {version_gap} versions). Update WebDriver to v{browser_major}.x"
                    else:
                        result["recommendation"] = f"Driver too new (gap: {version_gap} versions). Update {browser_type} browser or downgrade driver."
                        
            except (ValueError, IndexError):
                result["recommendation"] = "Invalid version format detected. Manual verification needed."
        
        return result