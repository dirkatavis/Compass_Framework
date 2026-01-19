"""
Login Flow Protocol for Compass Framework.

Defines the interface for authentication workflows.
Implementations handle specific SSO providers (Microsoft, Okta, etc.).
"""
from typing import Protocol, Dict, Any, runtime_checkable


@runtime_checkable
class LoginFlow(Protocol):
    """
    Protocol for authentication workflows.
    
    Implementations handle login sequences for different SSO providers,
    managing credentials, redirects, and session establishment.
    """
    
    def authenticate(
        self,
        username: str,
        password: str,
        login_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Authenticate user with given credentials.
        
        Args:
            username: User email or username
            password: User password
            login_url: Login page URL (SSO entry point)
            **kwargs: Provider-specific parameters (e.g., login_id, tenant_id)
        
        Returns:
            Dict with status and optional error:
            {
                "status": "success" | "error",
                "message": "Authenticated successfully" | error details,
                "error": str (only if status="error")
            }
        
        Raises:
            None - returns error dict instead of raising exceptions
        """
        ...
