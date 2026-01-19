"""
CSV utility functions for Compass Framework.

Provides helper functions for reading MVA lists and writing results.
"""
import csv
import re
import os
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def read_mva_list(csv_path: str, normalize: bool = True) -> List[str]:
    """
    Read MVA list from CSV file.
    
    Features:
    - Normalizes MVAs to 8 digits (if normalize=True)
    - Skips header rows (starting with '#' or 'MVA')
    - Ignores comment lines (starting with '#')
    - Handles empty rows
    
    Args:
        csv_path: Path to CSV file
        normalize: Whether to normalize MVAs to 8 digits (default: True)
    
    Returns:
        List of MVA strings
    
    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV is empty or invalid
    
    Example CSV format:
        # MVA List for Glass Data Lookup
        50227203
        12345678
        # Another comment
        98765432
    """
    if not os.path.exists(csv_path):
        logger.error(f"[CSV] File not found: {csv_path}")
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    def normalize_mva(raw: str) -> str:
        """Normalize MVA to 8 digits."""
        s = raw.strip()
        # Prefer leading 8 digits
        m = re.match(r'^(\d{8})', s)
        if m:
            return m.group(1)
        # Fallback: take first 8 characters
        return s[:8]
    
    mvas = []
    
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = [row[0] for row in reader if row and len(row) > 0]  # Get first column, skip empty rows
            
            # Skip header if present
            if rows and (rows[0].startswith('#') or rows[0].lower().startswith('mva')):
                rows = rows[1:]
            
            for raw in rows:
                if not raw or raw.startswith('#'):
                    continue
                
                if normalize:
                    mvas.append(normalize_mva(raw))
                else:
                    mvas.append(raw.strip())
        
        if not mvas:
            logger.warning(f"[CSV] No MVAs found in: {csv_path}")
            raise ValueError(f"No valid MVAs found in CSV file: {csv_path}")
        
        logger.info(f"[CSV] Read {len(mvas)} MVAs from: {csv_path}")
        return mvas
        
    except Exception as e:
        logger.error(f"[CSV] Error reading file: {e}")
        raise


def write_results_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write lookup results to CSV file.
    
    Args:
        results: List of result dictionaries with keys:
            - mva: str
            - vin: str
            - desc: str
            - error: str (optional)
        output_path: Path to output CSV file
    
    Raises:
        IOError: If file cannot be written
    
    Example output:
        MVA,VIN,Desc,Error
        50227203,1HGBH41JXMN109186,2021 Honda Accord,
        12345678,N/A,N/A,MVA not found
    """
    abs_path = os.path.abspath(output_path)
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            # Determine fieldnames from first result or use defaults
            fieldnames = ['mva', 'vin', 'desc']
            if results and 'error' in results[0]:
                fieldnames.append('error')
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in results:
                # Ensure all required fields exist
                row = {
                    'mva': result.get('mva', 'N/A'),
                    'vin': result.get('vin', 'N/A'),
                    'desc': result.get('desc', 'N/A'),
                }
                if 'error' in fieldnames:
                    row['error'] = result.get('error', '')
                
                writer.writerow(row)
        
        logger.info(f"[CSV] Wrote {len(results)} results to: {abs_path}")
        
    except Exception as e:
        logger.error(f"[CSV] Error writing results file: {e}")
        raise IOError(f"Failed to write results to {output_path}: {e}")
