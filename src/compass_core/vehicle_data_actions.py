"""
Vehicle Data Actions Protocol

Defines interface for vehicle property lookup and MVA data extraction operations.
This protocol abstracts interactions needed for bulk vehicle data retrieval workflows.
"""
from typing import Protocol, runtime_checkable, Dict, Any, Optional, List


@runtime_checkable
class VehicleDataActions(Protocol):
    """Protocol for vehicle data lookup operations in Compass.
    
    This protocol defines the interface for entering MVAs and retrieving
    vehicle properties (VIN, Description, etc.) from the Compass UI.
    """
    
    def enter_mva(self, mva: str, clear_existing: bool = True) -> Dict[str, Any]:
        """Enter an MVA into the Compass search/input field.
        
        Args:
            mva: The MVA identifier to enter (typically 8 digits)
            clear_existing: Whether to clear any existing value first
            
        Returns:
            Dictionary with operation result:
            - status: 'ok' or 'error'
            - mva: The MVA that was entered
            - error: Error message if status is 'error'
        """
        ...
    
    def get_vehicle_property(self, label: str, timeout: int = 10) -> Optional[str]:
        """Get a vehicle property value by its display label.
        
        Args:
            label: The property label (e.g., 'VIN', 'Desc', 'Make', 'Model')
            timeout: Maximum time to wait for the property to appear
            
        Returns:
            The property value as a string, or None if not found/timeout
        """
        ...
    
    def get_vehicle_properties(self, labels: List[str], timeout: int = 10) -> Dict[str, str]:
        """Get multiple vehicle properties in a single call.
        
        Args:
            labels: List of property labels to retrieve
            timeout: Maximum time to wait for properties to appear
            
        Returns:
            Dictionary mapping label to value, with 'N/A' for missing properties
        """
        ...
    
    def verify_mva_echo(self, mva: str, timeout: int = 5) -> bool:
        """Verify that the UI has echoed the entered MVA.
        
        This helps ensure that displayed data corresponds to the entered MVA
        and not stale data from a previous query.
        
        Args:
            mva: The MVA to verify (typically last 8 digits)
            timeout: Maximum time to wait for echo
            
        Returns:
            True if MVA is echoed in the UI, False otherwise
        """
        ...
    
    def wait_for_property_loaded(self, label: str, timeout: int = 10) -> bool:
        """Wait for a specific property to be loaded and visible.
        
        Args:
            label: The property label to wait for
            timeout: Maximum time to wait
            
        Returns:
            True if property loaded successfully, False on timeout
        """
        ...

    def set_vehicle_status(self, status: str) -> Dict[str, Any]:
        """Set the vehicle status on the current vehicle record.

        Args:
            status: Target status text (e.g., 'Closed')

        Returns:
            Dictionary with operation result:
            - status: 'success' or 'error'
            - status_value: Requested status value
            - error: Error message if status is 'error'
        """
        ...

    def save_vehicle(self) -> Dict[str, Any]:
        """Save or update the currently loaded vehicle record.

        Returns:
            Dictionary with operation result:
            - status: 'success' or 'error'
            - error: Error message if status is 'error'
        """
        ...
