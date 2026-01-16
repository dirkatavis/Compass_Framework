"""
Navigation Interface for Compass Framework
Protocol for web navigation and page verification operations
"""
from typing import Protocol, runtime_checkable, Dict, Any, Optional, Tuple


@runtime_checkable  
class Navigator(Protocol):
    """Protocol for web navigation operations"""
    
    def navigate_to(self, url: str, label: str = "page", verify: bool = True, timeout: int = 15) -> Dict[str, Any]:
        """Navigate to a URL with optional verification"""
        ...
    
    def verify_page(self, 
                   url: Optional[str] = None, 
                   check_locator: Optional[Tuple[str, str]] = None, 
                   timeout: int = 15) -> Dict[str, Any]:
        """Verify page has loaded correctly"""
        ...