"""
Navigation Interface for Compass Framework
Protocol for web navigation and page verification operations
"""
from typing import Protocol, runtime_checkable, Dict, Any, Optional, Tuple
from .decorators import compass_public


@compass_public
@runtime_checkable  
class Navigator(Protocol):
    """Protocol for web navigation operations"""
    
    @compass_public
    def navigate_to(self, url: str, label: str = "page", verify: bool = True, timeout: int = 15) -> Dict[str, Any]:
        """Navigate to a URL with optional verification"""
        ...
    
    @compass_public
    def verify_page(self, 
                   url: Optional[str] = None, 
                   check_locator: Optional[Tuple[str, str]] = None, 
                   timeout: int = 15) -> Dict[str, Any]:
        """Verify page has loaded correctly"""
        ...
        
    @compass_public
    def scroll_into_view_center(self, element: Any) -> Dict[str, Any]:
        """Scroll element into center of viewport to avoid header/footer collisions"""
        ...

