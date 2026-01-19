# Data Directory

This directory contains sample and user data files for Compass Framework.

## Files

- **sample_mva_list.csv** - Example MVA list for testing glass_data_lookup.py
- **Your data files** - Add your own CSVs here (gitignored by default)

## CSV Format

MVA list format:
```
# Optional header comment
50227203
12345678
98765432
```

- One MVA per line
- 8 digits recommended
- Lines starting with `#` are ignored
- Header row starting with `#` or `MVA` is skipped
- Empty lines are ignored

## Usage

```bash
python scripts/glass_data_lookup.py --input data/sample_mva_list.csv --output results.csv
```
