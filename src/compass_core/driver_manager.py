"""
DriverManager protocol definition for WebDriver lifecycle management.

This protocol defines the interface for managing WebDriver instances,
inspired by DevCompass driver_manager.py patterns.
"""
from typing import Protocol, runtime_checkable, Any, Dict
from selenium.webdriver.common.service import Service
from selenium.webdriver.remote.webdriver import WebDriver


@runtime_checkable
class DriverManager(Protocol):
    """Protocol for WebDriver lifecycle management and configuration.
    
    This protocol abstracts WebDriver creation, configuration, and lifecycle
    management, supporting singleton patterns and version compatibility.
    
    Example usage:
        manager = StandardDriverManager()
        driver = manager.get_or_create_driver()
        # Use driver for automation
        manager.quit_driver()
    """
    
    def get_or_create_driver(self, **kwargs) -> WebDriver:
        """Get existing driver or create new WebDriver instance.
        
        Args:
            **kwargs: Driver-specific configuration options
            
        Returns:
            WebDriver: Active WebDriver instance
            
        Raises:
            RuntimeError: If driver creation fails or version mismatch detected
        """
        ...
    
    def quit_driver(self) -> None:
        """Quit and cleanup WebDriver instance.
        
        Should handle singleton cleanup and resource deallocation.
        Safe to call multiple times or when no driver exists.
        """
        ...
    
    def get_driver_version(self, driver_path: str) -> str:
        """Get version of WebDriver executable.
        
        Args:
            driver_path: Path to WebDriver executable
            
        Returns:
            str: Version string (e.g., "120.0.6099.109") or "unknown"
        """
        ...
    
    def configure_driver_options(self) -> Any:
        """Configure browser-specific options for WebDriver.
        
        Returns:
            Browser options object (EdgeOptions, ChromeOptions, etc.)
        """
        ...
    
    def create_driver_service(self, driver_path: str) -> Service:
        """Create WebDriver service with specified driver path.
        
        Args:
            driver_path: Path to WebDriver executable
            
        Returns:
            Service: Configured service for WebDriver
        """
        ...
    
    def is_driver_active(self) -> bool:
        """Check if WebDriver instance is currently active.
        
        Returns:
            bool: True if active driver exists, False otherwise
        """
        ...
    
    def check_version_compatibility(self, browser_version: str, driver_version: str) -> Dict[str, Any]:
        """Check compatibility between browser and driver versions.
        
        Args:
            browser_version: Browser version string
            driver_version: Driver version string
            
        Returns:
            Dict with compatibility status and recommendations
        """
        ...