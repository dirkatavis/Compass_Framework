"""
MVA collection management.

Provides data structures for managing and tracking MVA processing status.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .decorators import compass_public


@compass_public
class MvaStatus(str, Enum):
    """MVA processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
@compass_public
class MvaItem:
    """
    Individual MVA item with status tracking.
    
    Attributes:
        mva: MVA value (8-digit string)
        status: Current processing status
        result: Processing result (if completed)
        error: Error message (if failed)
        source_line: Line number in source CSV (optional)
    """
    mva: str
    status: MvaStatus = MvaStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source_line: Optional[int] = None
    
    @compass_public
    def mark_processing(self) -> None:
        """Mark item as currently being processed."""
        self.status = MvaStatus.PROCESSING
    
    @compass_public
    def mark_completed(self, result: Dict[str, Any]) -> None:
        """
        Mark item as completed with result.
        
        Args:
            result: Processing result dictionary (e.g., {'vin': '...', 'desc': '...'})
        """
        self.status = MvaStatus.COMPLETED
        self.result = result
        self.error = None
    
    @compass_public
    def mark_failed(self, error: str) -> None:
        """
        Mark item as failed with error message.
        
        Args:
            error: Error message describing the failure
        """
        self.status = MvaStatus.FAILED
        self.error = error
        self.result = None
    
    @compass_public
    def reset(self) -> None:
        """Reset item to pending status."""
        self.status = MvaStatus.PENDING
        self.result = None
        self.error = None
    
    @property
    @compass_public
    def is_pending(self) -> bool:
        """Check if item is pending."""
        return self.status == MvaStatus.PENDING
    
    @property
    @compass_public
    def is_processing(self) -> bool:
        """Check if item is being processed."""
        return self.status == MvaStatus.PROCESSING
    
    @property
    @compass_public
    def is_completed(self) -> bool:
        """Check if item is completed."""
        return self.status == MvaStatus.COMPLETED
    
    @property
    @compass_public
    def is_failed(self) -> bool:
        """Check if item failed."""
        return self.status == MvaStatus.FAILED


@compass_public
class MvaCollection:
    """
    Collection of MVA items with iteration and tracking support.
    
    Supports:
    - Iteration over items
    - Index access
    - Status filtering
    - Progress tracking
    - Results export
    
    Example:
        >>> collection = MvaCollection.from_list(['50227203', '12345678'])
        >>> for item in collection:
        ...     item.mark_processing()
        ...     # ... process MVA ...
        ...     item.mark_completed({'vin': 'ABC', 'desc': 'Vehicle'})
        >>> print(f"Progress: {collection.progress_percentage}%")
    """
    
    def __init__(self):
        """Initialize empty collection."""
        self._items: List[MvaItem] = []
    
    @classmethod
    @compass_public
    def from_list(cls, mvas: List[str], source_file: Optional[str] = None) -> 'MvaCollection':
        """
        Create collection from list of MVA strings.
        
        Args:
            mvas: List of MVA strings
            source_file: Optional source file path for metadata
        
        Returns:
            MvaCollection instance
        """
        collection = cls()
        collection.add_many(mvas)
        return collection
    
    @compass_public
    def add(self, mva: str, source_line: Optional[int] = None) -> MvaItem:
        """
        Add single MVA to collection.
        
        Args:
            mva: MVA value
            source_line: Optional source line number
        
        Returns:
            Created MvaItem
        """
        item = MvaItem(mva=mva, source_line=source_line)
        self._items.append(item)
        return item
    
    @compass_public
    def add_many(self, mvas: List[str]) -> None:
        """
        Add multiple MVAs to collection.
        
        Args:
            mvas: List of MVA values
        """
        for mva in mvas:
            self.add(mva)
    
    @compass_public
    def find_by_mva(self, mva: str) -> Optional[MvaItem]:
        """
        Find item by MVA value.
        
        Args:
            mva: MVA value to find
        
        Returns:
            MvaItem if found, None otherwise
        """
        for item in self._items:
            if item.mva == mva:
                return item
        return None
    
    @compass_public
    def get_pending(self) -> List[MvaItem]:
        """Get all pending items."""
        return [item for item in self._items if item.is_pending]
    
    @compass_public
    def get_completed(self) -> List[MvaItem]:
        """Get all completed items."""
        return [item for item in self._items if item.is_completed]
    
    @compass_public
    def get_failed(self) -> List[MvaItem]:
        """Get all failed items."""
        return [item for item in self._items if item.is_failed]
    
    @compass_public
    def to_results_list(self) -> List[Dict[str, Any]]:
        """
        Convert collection to results list format for CSV export.
        
        Returns:
            List of result dictionaries with mva, vin, desc, error fields
        """
        results = []
        for item in self._items:
            if item.is_completed and item.result:
                result_dict = {'mva': item.mva}
                result_dict.update(item.result)
                results.append(result_dict)
            elif item.is_failed:
                results.append({
                    'mva': item.mva,
                    'error': item.error or 'Unknown error'
                })
            else:
                # Pending or processing - include as N/A
                results.append({
                    'mva': item.mva,
                    'vin': 'N/A',
                    'desc': 'N/A'
                })
        return results
    
    @property
    @compass_public
    def total_count(self) -> int:
        """Total number of items in collection."""
        return len(self._items)
    
    @property
    @compass_public
    def pending_count(self) -> int:
        """Number of pending items."""
        return len(self.get_pending())
    
    @property
    @compass_public
    def completed_count(self) -> int:
        """Number of completed items."""
        return len(self.get_completed())
    
    @property
    @compass_public
    def failed_count(self) -> int:
        """Number of failed items."""
        return len(self.get_failed())
    
    @property
    @compass_public
    def progress_percentage(self) -> float:
        """
        Progress percentage (completed + failed / total).
        
        Returns:
            Progress as percentage (0.0 to 100.0)
        """
        if self.total_count == 0:
            return 0.0
        processed = self.completed_count + self.failed_count
        return (processed / self.total_count) * 100.0
    
    def __len__(self) -> int:
        """Return number of items."""
        return len(self._items)
    
    def __iter__(self):
        """Iterate over items."""
        return iter(self._items)
    
    def __getitem__(self, index: int) -> MvaItem:
        """Get item by index."""
        return self._items[index]
    
    def __contains__(self, mva: str) -> bool:
        """Check if MVA exists in collection."""
        return self.find_by_mva(mva) is not None
