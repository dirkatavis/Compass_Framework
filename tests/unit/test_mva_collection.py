"""
Unit tests for MVA collection management.

TDD tests written BEFORE implementation.
"""
import unittest
from compass_core.mva_collection import MvaCollection, MvaItem, MvaStatus


class TestMvaItem(unittest.TestCase):
    """Test MvaItem data class."""
    
    def test_create_mva_item(self):
        """Test creating an MVA item."""
        item = MvaItem(mva="50227203")
        self.assertEqual(item.mva, "50227203")
        self.assertEqual(item.status, MvaStatus.PENDING)
        self.assertIsNone(item.result)
        self.assertIsNone(item.error)
    
    def test_mva_item_with_metadata(self):
        """Test creating MVA item with metadata."""
        item = MvaItem(mva="50227203", source_line=5)
        self.assertEqual(item.source_line, 5)
    
    def test_mva_item_mark_processing(self):
        """Test marking item as processing."""
        item = MvaItem(mva="50227203")
        item.mark_processing()
        self.assertEqual(item.status, MvaStatus.PROCESSING)
    
    def test_mva_item_mark_completed(self):
        """Test marking item as completed with result."""
        item = MvaItem(mva="50227203")
        result = {'vin': 'ABC123', 'desc': 'Test Vehicle'}
        item.mark_completed(result)
        self.assertEqual(item.status, MvaStatus.COMPLETED)
        self.assertEqual(item.result, result)
        self.assertIsNone(item.error)
    
    def test_mva_item_mark_failed(self):
        """Test marking item as failed with error."""
        item = MvaItem(mva="50227203")
        item.mark_failed("MVA not found")
        self.assertEqual(item.status, MvaStatus.FAILED)
        self.assertEqual(item.error, "MVA not found")
    
    def test_mva_item_is_pending(self):
        """Test is_pending property."""
        item = MvaItem(mva="50227203")
        self.assertTrue(item.is_pending)
        item.mark_processing()
        self.assertFalse(item.is_pending)
    
    def test_mva_item_is_completed(self):
        """Test is_completed property."""
        item = MvaItem(mva="50227203")
        self.assertFalse(item.is_completed)
        item.mark_completed({'vin': 'ABC'})
        self.assertTrue(item.is_completed)
    
    def test_mva_item_is_failed(self):
        """Test is_failed property."""
        item = MvaItem(mva="50227203")
        self.assertFalse(item.is_failed)
        item.mark_failed("Error")
        self.assertTrue(item.is_failed)


class TestMvaCollection(unittest.TestCase):
    """Test MvaCollection data structure."""
    
    def test_create_empty_collection(self):
        """Test creating empty collection."""
        collection = MvaCollection()
        self.assertEqual(len(collection), 0)
        self.assertEqual(collection.total_count, 0)
    
    def test_create_from_list(self):
        """Test creating collection from MVA list."""
        mvas = ["50227203", "12345678", "98765432"]
        collection = MvaCollection.from_list(mvas)
        self.assertEqual(len(collection), 3)
        self.assertEqual(collection.total_count, 3)
    
    def test_add_mva(self):
        """Test adding single MVA."""
        collection = MvaCollection()
        collection.add("50227203")
        self.assertEqual(len(collection), 1)
        self.assertEqual(collection[0].mva, "50227203")
    
    def test_add_multiple_mvas(self):
        """Test adding multiple MVAs."""
        collection = MvaCollection()
        collection.add_many(["50227203", "12345678"])
        self.assertEqual(len(collection), 2)
    
    def test_iteration(self):
        """Test iterating over collection."""
        mvas = ["50227203", "12345678", "98765432"]
        collection = MvaCollection.from_list(mvas)
        
        iterated_mvas = [item.mva for item in collection]
        self.assertEqual(iterated_mvas, mvas)
    
    def test_indexing(self):
        """Test accessing items by index."""
        collection = MvaCollection.from_list(["50227203", "12345678"])
        self.assertEqual(collection[0].mva, "50227203")
        self.assertEqual(collection[1].mva, "12345678")
    
    def test_get_pending(self):
        """Test getting pending items."""
        collection = MvaCollection.from_list(["50227203", "12345678", "98765432"])
        collection[0].mark_completed({'vin': 'ABC'})
        
        pending = collection.get_pending()
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0].mva, "12345678")
    
    def test_get_completed(self):
        """Test getting completed items."""
        collection = MvaCollection.from_list(["50227203", "12345678"])
        collection[0].mark_completed({'vin': 'ABC'})
        
        completed = collection.get_completed()
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0].mva, "50227203")
    
    def test_get_failed(self):
        """Test getting failed items."""
        collection = MvaCollection.from_list(["50227203", "12345678"])
        collection[1].mark_failed("Not found")
        
        failed = collection.get_failed()
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].mva, "12345678")
    
    def test_pending_count(self):
        """Test counting pending items."""
        collection = MvaCollection.from_list(["50227203", "12345678", "98765432"])
        collection[0].mark_completed({'vin': 'ABC'})
        self.assertEqual(collection.pending_count, 2)
    
    def test_completed_count(self):
        """Test counting completed items."""
        collection = MvaCollection.from_list(["50227203", "12345678"])
        collection[0].mark_completed({'vin': 'ABC'})
        collection[1].mark_completed({'vin': 'DEF'})
        self.assertEqual(collection.completed_count, 2)
    
    def test_failed_count(self):
        """Test counting failed items."""
        collection = MvaCollection.from_list(["50227203", "12345678", "98765432"])
        collection[1].mark_failed("Error 1")
        collection[2].mark_failed("Error 2")
        self.assertEqual(collection.failed_count, 2)
    
    def test_progress_percentage(self):
        """Test calculating progress percentage."""
        collection = MvaCollection.from_list(["50227203", "12345678", "98765432", "11111111"])
        collection[0].mark_completed({'vin': 'ABC'})
        collection[1].mark_failed("Error")
        
        # 2 out of 4 processed (completed + failed)
        self.assertEqual(collection.progress_percentage, 50.0)
    
    def test_progress_percentage_empty(self):
        """Test progress percentage for empty collection."""
        collection = MvaCollection()
        self.assertEqual(collection.progress_percentage, 0.0)
    
    def test_to_results_list(self):
        """Test converting to results list."""
        collection = MvaCollection.from_list(["50227203", "12345678"])
        collection[0].mark_completed({'vin': 'ABC123', 'desc': 'Vehicle 1'})
        collection[1].mark_failed("Not found")
        
        results = collection.to_results_list()
        self.assertEqual(len(results), 2)
        
        # First result (success)
        self.assertEqual(results[0]['mva'], "50227203")
        self.assertEqual(results[0]['vin'], 'ABC123')
        self.assertEqual(results[0]['desc'], 'Vehicle 1')
        
        # Second result (failure)
        self.assertEqual(results[1]['mva'], "12345678")
        self.assertEqual(results[1]['error'], "Not found")
    
    def test_find_by_mva(self):
        """Test finding item by MVA value."""
        collection = MvaCollection.from_list(["50227203", "12345678"])
        item = collection.find_by_mva("12345678")
        self.assertIsNotNone(item)
        self.assertEqual(item.mva, "12345678")
    
    def test_find_by_mva_not_found(self):
        """Test finding non-existent MVA."""
        collection = MvaCollection.from_list(["50227203"])
        item = collection.find_by_mva("99999999")
        self.assertIsNone(item)
    
    def test_contains(self):
        """Test checking if MVA exists in collection."""
        collection = MvaCollection.from_list(["50227203", "12345678"])
        self.assertTrue("50227203" in collection)
        self.assertFalse("99999999" in collection)
    
    def test_reset_item(self):
        """Test resetting item status."""
        collection = MvaCollection.from_list(["50227203"])
        item = collection[0]
        item.mark_failed("Error")
        
        item.reset()
        self.assertEqual(item.status, MvaStatus.PENDING)
        self.assertIsNone(item.result)
        self.assertIsNone(item.error)


class TestMvaStatus(unittest.TestCase):
    """Test MvaStatus enum."""
    
    def test_status_values(self):
        """Test status enum values exist."""
        self.assertEqual(MvaStatus.PENDING, "pending")
        self.assertEqual(MvaStatus.PROCESSING, "processing")
        self.assertEqual(MvaStatus.COMPLETED, "completed")
        self.assertEqual(MvaStatus.FAILED, "failed")


if __name__ == '__main__':
    unittest.main()
