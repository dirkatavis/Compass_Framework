# Data Directory

This directory contains sample and user data files for Compass Framework vehicle lookup.

## Files

- **vehicle_lookup_sample.csv** - Example MVA list for testing vehicle lookup
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

### Navigate to Client Directory
```powershell
cd clients/vehicle_lookup
```

### With CSV Input
```powershell
python VehicleLookup.py --input ../../data/vehicle_lookup_sample.csv --output VehicleLookup_results.csv
```

### With Verbose Logging
```powershell
python VehicleLookup.py --verbose
```

### With Incognito Mode (Forces Fresh Login)
```powershell
python VehicleLookup.py --incognito
```

## Output Format

Results are written as CSV:
```csv
MVA,VIN,Desc
50227203,1HGBH41JXMN109186,2021 Honda Accord
12345678,N/A,N/A
```
