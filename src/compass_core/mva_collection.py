"""
MVA collection management.

Provides data structures for managing and tracking MVA processing status.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class MvaStatus(str, Enum):
    """MVA processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
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
    
    def mark_processing(self) -> None:
        """Mark item as currently being processed."""
        self.status = MvaStatus.PROCESSING
    
    def mark_completed(self, result: Dict[str, Any]) -> None:
        """
        Mark item as completed with result.
        
        Args:
            result: Processing result dictionary (e.g., {'vin': '...', 'desc': '...'})
        """
        self.status = MvaStatus.COMPLETED
        self.result = result
        self.error = None
    
    def mark_failed(self, error: str) -> None:
        """
        Mark item as failed with error message.
        
        Args:
            error: Error message describing the failure
        """
        self.status = MvaStatus.FAILED
        self.error = error
        self.result = None
    
    def reset(self) -> None:
        """Reset item to pending status."""
        self.status = MvaStatus.PENDING
        self.result = None
        self.error = None
    
    @property
    def is_pending(self) -> bool:
        """Check if item is pending."""
        return self.status == MvaStatus.PENDING
    
    @property
    def is_processing(self) -> bool:
        """Check if item is being processed."""
        return self.status == MvaStatus.PROCESSING
    
    @property
    def is_completed(self) -> bool:
        """Check if item is completed."""
        return self.status == MvaStatus.COMPLETED
    
    @property
    def is_failed(self) -> bool:
        """Check if item failed."""
        return self.status == MvaStatus.FAILED


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
    
    def add_many(self, mvas: List[str]) -> None:
        """
        Add multiple MVAs to collection.
        
        Args:
            mvas: List of MVA values
        """
        for mva in mvas:
            self.add(mva)
    
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
    
    def get_pending(self) -> List[MvaItem]:
        """Get all pending items."""
        return [item for item in self._items if item.is_pending]
    
    def get_completed(self) -> List[MvaItem]:
        """Get all completed items."""
        return [item for item in self._items if item.is_completed]
    
    def get_failed(self) -> List[MvaItem]:
        """Get all failed items."""
        return [item for item in self._items if item.is_failed]
    
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
    def total_count(self) -> int:
        """Total number of items in collection."""
        return len(self._items)
    
    @property
    def pending_count(self) -> int:
        """Number of pending items."""
        return len(self.get_pending())
    
    @property
    def completed_count(self) -> int:
        """Number of completed items."""
        return len(self.get_completed())
    
    @property
    def failed_count(self) -> int:
        """Number of failed items."""
        return len(self.get_failed())
    
    @property
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
