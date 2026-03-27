"""
Version Checker Interface for Compass Framework
Focused extraction of version checking responsibilities
"""
from typing import Protocol, runtime_checkable
from .decorators import compass_public


@compass_public
@runtime_checkable
class VersionChecker(Protocol):
    """Protocol for checking browser and driver versions"""
    
    @compass_public
    def get_browser_version(self) -> str:
        """Return the installed browser version or 'unknown' if unavailable"""
        ...
    
    @compass_public
    def get_driver_version(self, driver_path: str) -> str:
        """Return the driver version or 'unknown' if unavailable"""
        ...