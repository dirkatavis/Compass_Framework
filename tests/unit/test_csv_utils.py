"""
Unit tests for CSV utilities.

Tests read_mva_list() and write_results_csv() functions.
"""
import unittest
import os
import tempfile
import csv
from unittest.mock import patch, mock_open
from compass_core.csv_utils import read_mva_list, read_workitem_list, write_results_csv


class TestReadMvaList(unittest.TestCase):
    """Test read_mva_list() function."""
    
    def setUp(self):
        """Create temporary test directory."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_csv(self, filename: str, content: str) -> str:
        """Helper to create test CSV file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_read_simple_mva_list(self):
        """Test reading simple MVA list."""
        csv_path = self._create_csv('simple.csv', '50227203\n12345678\n98765432\n')
        mvas = read_mva_list(csv_path)
        self.assertEqual(mvas, ['50227203', '12345678', '98765432'])
    
    def test_read_with_header_comment(self):
        """Test reading MVA list with header comment."""
        csv_path = self._create_csv('with_header.csv', '# MVA List\n50227203\n12345678\n')
        mvas = read_mva_list(csv_path)
        self.assertEqual(mvas, ['50227203', '12345678'])
    
    def test_read_with_mva_header(self):
        """Test reading MVA list with 'MVA' header."""
        csv_path = self._create_csv('mva_header.csv', 'MVA\n50227203\n12345678\n')
        mvas = read_mva_list(csv_path)
        self.assertEqual(mvas, ['50227203', '12345678'])
    
    def test_read_with_inline_comments(self):
        """Test reading MVA list with inline comments."""
        csv_path = self._create_csv('comments.csv', 
            '50227203\n# This is a comment\n12345678\n# Another comment\n98765432\n')
        mvas = read_mva_list(csv_path)
        self.assertEqual(mvas, ['50227203', '12345678', '98765432'])
    
    def test_read_with_empty_lines(self):
        """Test reading MVA list with empty lines."""
        csv_path = self._create_csv('empty_lines.csv', 
            '50227203\n\n12345678\n\n\n98765432\n')
        mvas = read_mva_list(csv_path)
        self.assertEqual(mvas, ['50227203', '12345678', '98765432'])
    
    def test_read_with_normalization(self):
        """Test MVA normalization (8-digit extraction)."""
        csv_path = self._create_csv('normalize.csv', 
            '50227203ABC\n12345678-EXTRA\n98765432999\n')
        mvas = read_mva_list(csv_path, normalize=True)
        self.assertEqual(mvas, ['50227203', '12345678', '98765432'])
    
    def test_read_without_normalization(self):
        """Test reading without normalization."""
        csv_path = self._create_csv('no_normalize.csv', 
            '50227203ABC\n12345678-EXTRA\n')
        mvas = read_mva_list(csv_path, normalize=False)
        self.assertEqual(mvas, ['50227203ABC', '12345678-EXTRA'])
    
    def test_read_whitespace_handling(self):
        """Test whitespace stripping."""
        csv_path = self._create_csv('whitespace.csv', 
            '  50227203  \n\t12345678\t\n  98765432\n')
        mvas = read_mva_list(csv_path)
        self.assertEqual(mvas, ['50227203', '12345678', '98765432'])
    
    def test_read_file_not_found(self):
        """Test error handling for missing file."""
        with self.assertRaises(FileNotFoundError) as context:
            read_mva_list('nonexistent.csv')
        self.assertIn('not found', str(context.exception))
    
    def test_read_empty_csv(self):
        """Test error handling for empty CSV."""
        csv_path = self._create_csv('empty.csv', '')
        with self.assertRaises(ValueError) as context:
            read_mva_list(csv_path)
        self.assertIn('No valid MVAs found', str(context.exception))
    
    def test_read_only_comments(self):
        """Test error handling for CSV with only comments."""
        csv_path = self._create_csv('only_comments.csv', 
            '# Comment 1\n# Comment 2\n# Comment 3\n')
        with self.assertRaises(ValueError) as context:
            read_mva_list(csv_path)
        self.assertIn('No valid MVAs found', str(context.exception))
    
    def test_read_only_header(self):
        """Test error handling for CSV with only header."""
        csv_path = self._create_csv('only_header.csv', 'MVA\n')
        with self.assertRaises(ValueError) as context:
            read_mva_list(csv_path)
        self.assertIn('No valid MVAs found', str(context.exception))


class TestWriteResultsCsv(unittest.TestCase):
    """Test write_results_csv() function."""
    
    def setUp(self):
        """Create temporary test directory."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _get_csv_path(self, filename: str) -> str:
        """Helper to get path for output CSV."""
        return os.path.join(self.temp_dir, filename)
    
    def _read_csv(self, filepath: str) -> list:
        """Helper to read CSV file."""
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def test_write_basic_results(self):
        """Test writing basic results."""
        results = [
            {'mva': '50227203', 'vin': '1HGBH41JXMN109186', 'desc': '2021 Honda Accord'},
            {'mva': '12345678', 'vin': 'WBADT43452G123456', 'desc': '2002 BMW 325i'}
        ]
        output_path = self._get_csv_path('results.csv')
        
        write_results_csv(results, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        rows = self._read_csv(output_path)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['mva'], '50227203')
        self.assertEqual(rows[0]['vin'], '1HGBH41JXMN109186')
        self.assertEqual(rows[0]['desc'], '2021 Honda Accord')
    
    def test_write_results_with_errors(self):
        """Test writing results with error field."""
        results = [
            {'mva': '50227203', 'vin': '1HGBH41JXMN109186', 'desc': '2021 Honda Accord', 'error': ''},
            {'mva': '12345678', 'vin': 'N/A', 'desc': 'N/A', 'error': 'MVA not found'}
        ]
        output_path = self._get_csv_path('results_with_errors.csv')
        
        write_results_csv(results, output_path)
        
        rows = self._read_csv(output_path)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]['error'], 'MVA not found')
    
    def test_write_results_missing_fields(self):
        """Test writing results with missing fields (uses N/A)."""
        results = [
            {'mva': '50227203'},  # Missing vin and desc
            {'vin': '1HGBH41JXMN109186'}  # Missing mva and desc
        ]
        output_path = self._get_csv_path('missing_fields.csv')
        
        write_results_csv(results, output_path)
        
        rows = self._read_csv(output_path)
        self.assertEqual(rows[0]['vin'], 'N/A')
        self.assertEqual(rows[0]['desc'], 'N/A')
        self.assertEqual(rows[1]['mva'], 'N/A')
    
    def test_write_empty_results(self):
        """Test writing empty results list."""
        results = []
        output_path = self._get_csv_path('empty_results.csv')
        
        write_results_csv(results, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        rows = self._read_csv(output_path)
        self.assertEqual(len(rows), 0)
    
    def test_write_single_result(self):
        """Test writing single result."""
        results = [
            {'mva': '50227203', 'vin': '1HGBH41JXMN109186', 'desc': '2021 Honda Accord'}
        ]
        output_path = self._get_csv_path('single_result.csv')
        
        write_results_csv(results, output_path)
        
        rows = self._read_csv(output_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['mva'], '50227203')
    
    def test_write_file_permission_error(self):
        """Test error handling for write permission errors."""
        results = [{'mva': '50227203', 'vin': 'ABC', 'desc': 'Test'}]
        
        # Use mock to simulate permission error
        with patch('builtins.open', side_effect=PermissionError('Access denied')):
            with self.assertRaises(IOError) as context:
                write_results_csv(results, 'test.csv')
            self.assertIn('Failed to write', str(context.exception))
    
    def test_write_creates_parent_directories(self):
        """Test that absolute path is used (directory must exist)."""
        results = [{'mva': '50227203', 'vin': 'ABC', 'desc': 'Test'}]
        output_path = self._get_csv_path('results.csv')
        
        write_results_csv(results, output_path)
        
        # File should be created with absolute path
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(os.path.isabs(os.path.abspath(output_path)))
    
    def test_write_utf8_encoding(self):
        """Test UTF-8 encoding for special characters."""
        results = [
            {'mva': '50227203', 'vin': 'ABC123', 'desc': 'Tëst Vëhíclé ñ'}
        ]
        output_path = self._get_csv_path('utf8_test.csv')
        
        write_results_csv(results, output_path)
        
        rows = self._read_csv(output_path)
        self.assertEqual(rows[0]['desc'], 'Tëst Vëhíclé ñ')
    
    def test_write_overwrite_existing(self):
        """Test that existing file is overwritten."""
        results1 = [{'mva': '11111111', 'vin': 'OLD', 'desc': 'Old'}]
        results2 = [{'mva': '22222222', 'vin': 'NEW', 'desc': 'New'}]
        output_path = self._get_csv_path('overwrite.csv')
        
        write_results_csv(results1, output_path)
        write_results_csv(results2, output_path)
        
        rows = self._read_csv(output_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['mva'], '22222222')

    def test_write_closeout_results_schema(self):
        """Test writing closeout results with status_update_result field."""
        results = [
            {'mva': '50227203', 'status_update_result': 'success', 'error': ''},
            {'mva': '12345678', 'status_update_result': 'failed', 'error': 'Status update failed'}
        ]
        output_path = self._get_csv_path('closeout_results.csv')

        write_results_csv(results, output_path)

        with open(output_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.assertEqual(
                reader.fieldnames,
                ['mva', 'status_update_result', 'error']
            )
            rows = list(reader)

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['status_update_result'], 'success')
        self.assertEqual(rows[1]['status_update_result'], 'failed')

    def test_write_rejects_mixed_result_schemas(self):
        """Test that mixed closeout and lookup schemas are rejected."""
        results = [
            {'mva': '50227203', 'status_update_result': 'success', 'error': ''},
            {'mva': '12345678', 'vin': 'ABC123', 'desc': 'Test Vehicle', 'error': ''}
        ]
        output_path = self._get_csv_path('mixed_schema.csv')

        with self.assertRaises(ValueError) as context:
            write_results_csv(results, output_path)

        self.assertIn('Mixed result schemas are not supported', str(context.exception))


class TestReadWorkitemList(unittest.TestCase):
    """Test read_workitem_list() function."""

    def setUp(self):
        """Create temporary test directory."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_csv(self, filename: str, content: str) -> str:
        """Helper to create test CSV file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def test_read_workitem_list_basic(self):
        """Test reading valid workitem list."""
        csv_path = self._create_csv(
            'workitems.csv',
            'MVA,DamageType,SubDamageType,CorrectionAction\n'
            '50227203,Glass Damage,Windshield,Replace\n'
            '12345678,Body Damage,Front Bumper,Repair\n'
        )
        workitems = read_workitem_list(csv_path)
        self.assertEqual(len(workitems), 2)
        self.assertEqual(workitems[0]['mva'], '50227203')
        self.assertEqual(workitems[0]['damage_type'], 'Glass Damage')
        self.assertEqual(workitems[0]['sub_damage_type'], 'Windshield')
        self.assertEqual(workitems[0]['correction_action'], 'Replace')

    def test_read_workitem_list_case_insensitive_headers(self):
        """Test header mapping is case-insensitive."""
        csv_path = self._create_csv(
            'workitems_case.csv',
            'mva,damagetype,subdamagetype,correctionaction\n'
            '50227203,PM,PM Gas,Regular maintenance\n'
        )
        workitems = read_workitem_list(csv_path)
        self.assertEqual(len(workitems), 1)
        self.assertEqual(workitems[0]['mva'], '50227203')

    def test_read_workitem_list_skips_comments_and_empty(self):
        """Test skipping comment rows and empty MVA rows."""
        csv_path = self._create_csv(
            'workitems_comments.csv',
            'MVA,DamageType,SubDamageType,CorrectionAction\n'
            '# Comment,PM,PM Gas,Ignored\n'
            ',PM,PM Gas,Ignored\n'
            '50227203,PM,PM Gas,Valid\n'
        )
        workitems = read_workitem_list(csv_path)
        self.assertEqual(len(workitems), 1)
        self.assertEqual(workitems[0]['correction_action'], 'Valid')

    def test_read_workitem_list_normalizes_mva(self):
        """Test MVA normalization (digits extraction + zero padding)."""
        csv_path = self._create_csv(
            'workitems_norm.csv',
            'MVA,DamageType,SubDamageType,CorrectionAction\n'
            'MVA-50227203X,PM,PM Gas,Action\n'
            '12345,PM,PM Gas,Action\n'
        )
        workitems = read_workitem_list(csv_path)
        self.assertEqual(workitems[0]['mva'], '50227203')
        self.assertEqual(workitems[1]['mva'], '00012345')

    def test_read_workitem_list_missing_columns(self):
        """Test error on missing required columns."""
        csv_path = self._create_csv(
            'workitems_missing_cols.csv',
            'MVA,DamageType,CorrectionAction\n'
            '50227203,PM,Action\n'
        )
        with self.assertRaises(ValueError) as context:
            read_workitem_list(csv_path)
        self.assertIn('missing required columns', str(context.exception).lower())

    def test_read_workitem_list_empty_headers(self):
        """Test error when CSV has no headers."""
        csv_path = self._create_csv('workitems_empty.csv', '')
        with self.assertRaises(ValueError) as context:
            read_workitem_list(csv_path)
        self.assertIn('no headers', str(context.exception).lower())

    def test_read_workitem_list_all_invalid_rows(self):
        """Test error when all rows are invalid or missing required fields."""
        csv_path = self._create_csv(
            'workitems_invalid.csv',
            'MVA,DamageType,SubDamageType,CorrectionAction\n'
            '50227203,,PM Gas,Action\n'
            '12345678,PM,,Action\n'
        )
        with self.assertRaises(ValueError) as context:
            read_workitem_list(csv_path)
        self.assertIn('no valid workitems', str(context.exception).lower())


if __name__ == '__main__':
    unittest.main()
