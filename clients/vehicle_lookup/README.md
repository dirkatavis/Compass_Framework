# Vehicle Lookup Client

Production client for batch vehicle data retrieval using the Compass Framework.

## Self-Contained Structure

This client is **fully self-contained** and portable:
- ✅ **Script**: `VehicleLookup.py` - the main executable
- ✅ **Sample Data**: `vehicle_lookup_sample.csv` - example MVA list
- ✅ **Config** (optional): `webdriver.ini.local` - your credentials
- ✅ **Output**: `VehicleLookup_results.csv` - generated results
- ✅ **Logs**: `vehicle_lookup.log` - execution log

You can copy this entire directory to another location and it will work independently.

## Features

✅ **Batch Processing**: Process multiple MVAs from CSV input  
✅ **Smart Authentication**: Automatic SSO cache detection and reuse  
✅ **Progress Tracking**: Real-time progress with percentage completion  
✅ **Session Management**: Automatic cleanup of previous output files  
✅ **Error Handling**: Detailed error messages for failed MVAs  
✅ **Property Logging**: INFO-level logging of each property retrieval

## Setup

1. **Use framework's virtual environment:**
   ```powershell
   # From repository root
   .\.venv-1\Scripts\Activate.ps1
   ```

2. **Verify framework is installed:**
   ```powershell
   python -c "import compass_core; print(compass_core.__version__)"
   ```

## Usage

### Quick Start (Uses Local Sample)
```powershell
cd clients/vehicle_lookup
python VehicleLookup.py
```
Uses the included `vehicle_lookup_sample.csv` by default.

### With Custom Input/Output
```powershell
python VehicleLookup.py --input my_mvas.csv --output my_results.csv
```

### Headless Mode
```powershell
python VehicleLookup.py --headless
```

### Verbose Logging
```powershell
python VehicleLookup.py --verbose
```

## Configuration

### Credentials (Required)

Create `webdriver.ini.local` in this directory:

```ini
[credentials]
username = your.email@example.com
password = your_password
login_id = YOUR_WWID

[app]
app_url = https://your-app-url.com
```

**Note**: The client looks for config in this order:
1. `./webdriver.ini.local` (this directory)
2. `../../webdriver.ini.local` (project root, if exists)

### WebDriver

Edge driver should be in `../../drivers.local/` or system PATH.

See `../../webdriver.ini` for full configuration template.

## Input Format

CSV file with MVA numbers (one per line, comments allowed):
```csv
# MVA List for Vehicle Lookup
# Lines starting with # are comments
50227203
12345678
98765432
```

- Comments: Lines starting with `#`
- Empty lines are ignored
- MVAs are automatically normalized

## Output Format

`VehicleLookup_results.csv` contains retrieved data:
```csv
mva,vin,desc
50227203,1HGBH41JXMN109186,Honda Accord
12345678,N/A,N/A
98765432,5FNRL6H73MB012345,Honda Odyssey
```

- **mva**: Vehicle MVA number
- **vin**: Vehicle Identification Number (or N/A if not found)
- **desc**: Vehicle description (or N/A if not found)

## Logging

### Default Logging

The client creates `vehicle_lookup.log` with:
- Authentication status
- MVA processing progress
- Property retrieval details (INFO level)
- Summary statistics

### Verbose Mode

Enable DEBUG-level logging:
```powershell
python main.py --verbose
```

### Log Output Example

```
2026-01-20 06:50:09,117 - INFO - [PROPERTY_PAGE] Property page loaded successfully with MVA: 56903346
2026-01-20 06:50:09,117 - INFO -   Retrieving properties: MVA, VIN, Desc
2026-01-20 06:50:09,155 - INFO -     MVA: 056903346
2026-01-20 06:50:09,179 - INFO -     VIN: 3FMCR9CN0SRE34030
2026-01-20 06:50:09,201 - INFO -     Desc: FORD BRONCO SPORT
2026-01-20 06:50:09,202 - INFO -   Progress: 8.3%
```

## Performance

- **Average**: ~11-13 seconds per MVA
- **Batch of 12 MVAs**: ~3-4 minutes total
- **Authentication**: One-time SSO login (cached for subsequent runs)

## Troubleshooting

**Import errors:**
- Ensure framework venv is activated
- Framework should be installed in editable mode: `pip install -e ../..`

**Authentication fails:**
- Check credentials in `webdriver.ini.local`
- Verify SSO redirect handling

**Property retrieval fails:**
- Check XPath selectors in framework
- Increase timeouts with `--verbose` to see detailed logs
