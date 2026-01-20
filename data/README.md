# Data Directory

This directory contains sample and user data files for Compass Framework vehicle lookup.

## Files

- **sample_mva_list.csv** - Example MVA list for testing vehicle lookup
- **Your data files** - Add your own CSVs here (gitignored by default)

## CSV Format

MVA list format:
```csv
# Optional header comment
50227203
12345678
98765432
```

- One MVA per line
- 8 digits recommended (will be normalized automatically)
- Lines starting with `#` are ignored
- Header row starting with `#` or `MVA` is skipped
- Empty lines are ignored

## Usage

### With CSV Input
```powershell
python scripts/vehicle_lookup_client.py --input data/sample_mva_list.csv --output results.csv
```

### With Direct MVA List
```powershell
python scripts/vehicle_lookup_client.py --mva 50227203,12345678 --output results.csv
```

### With Custom Properties
```powershell
python scripts/vehicle_lookup_client.py --input data/mva.csv --output results.csv --properties VIN,Desc,Year
```

## Output Format

Results are written as CSV:
```csv
MVA,VIN,Desc
50227203,1HGBH41JXMN109186,2021 Honda Accord
12345678,N/A,N/A
```
