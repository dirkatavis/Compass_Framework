# Create Missing WorkItems Client

Automates the creation and verification of vehicle workitems by reading specifications from CSV files.

## Self-Contained Structure

This client is **fully self-contained** and portable:
- ✅ **Script**: `CreateMissingWorkItems.py` - the main executable
- ✅ **Sample Data**: `create_missing_workitems_sample.csv` - example workitem specs
- ✅ **Config** (optional): `webdriver.ini.local` - your credentials
- ✅ **Logs**: `CreateMissingWorkItems.log` - execution log (recreated each session)

You can copy this entire directory to another location and it will work independently.

## Overview

This client processes a list of workitem specifications (MVA, DamageType, CorrectionAction) and:
1. Authenticates with the Compass application
2. For each MVA in the list:
   - Enters the MVA
   - Navigates to the WorkItem tab
   - Captures all existing workitems
   - Checks if a matching damage type already exists
   - Creates a new workitem if none exists
   - Logs all actions and results

## Features

✅ **Find Existing Workitems**: Searches for workitems matching damage type and correction action  
✅ **Create Missing Workitems**: Automatically creates workitems that don't exist  
✅ **Session Logging**: Creates fresh log file (`CreateMissingWorkItems.log`) for each run  
✅ **Comprehensive Summary**: Reports found, created, and failed workitems  
✅ **Error Recovery**: Attempts to continue processing even after failures  

## Usage

### Quick Start (Uses Local Sample)
```powershell
# Navigate to client folder
cd clients\create_missing_workitems

# Run with included sample data
python CreateMissingWorkItems.py
```
Uses the included `create_missing_workitems_sample.csv` by default.

### Custom Input File
```powershell
# Specify custom workitem list
python CreateMissingWorkItems.py --input my_workitems.csv
```

### Additional Options
```powershell
# Run in headless mode (no visible browser)
python CreateMissingWorkItems.py --headless

# Force fresh login with incognito mode
python CreateMissingWorkItems.py --incognito

# Enable verbose logging
python CreateMissingWorkItems.py --verbose
```

## Input CSV Format

The input CSV must have the following columns:

```csv
MVA,DamageType,CorrectionAction
50227203,PM,Regular maintenance required
12345678,Glass,Repair front windshield
```

### Column Descriptions

- **MVA**: Vehicle identifier (8 digits, will be normalized if shorter)
- **DamageType**: Category of damage (e.g., "PM", "Glass", "Tires", "Keys", "Body")
- **CorrectionAction**: Description of the work to be performed

**Damage Type Categories**: The damage type should match one of the application's workitem categories. Common types include:
- **PM**: Preventive Maintenance
- **Glass**: Windshield/window damage
- **Tires**: Tire-related issues
- **Keys**: Key/lock issues
- **Body**: Body damage

The system uses partial matching, so "PM" will match "PM Gas", "PM Oil", etc.

### CSV Rules

- Header row required (column names are case-insensitive)
- Comment lines starting with `#` are ignored
- Empty rows are skipped
- MVAs are automatically normalized to 8 digits (zero-padded if shorter)

## Configuration

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

See `../../webdriver.ini` for the complete configuration template.

## Output & Logging

### Log File: `CreateMissingWorkItems.log`

- **Recreated each session** (previous log is deleted)
- Contains detailed execution trace with timestamps
- Includes all actions, errors, and summary

### Console Output

Real-time progress with:
- Authentication status
- Per-MVA processing details
- Found/created/failed counts
- Final summary

### Exit Codes

- `0`: Success (all workitems processed)
- `1`: Failures occurred (check log for details)

## Example Session

```
============================================================
Create Missing WorkItems Client
Session started: 2026-01-20 14:30:00
============================================================
Loading configuration from: ../../webdriver.ini.local
Reading workitem list from: ../../data/create_missing_workitems_sample.csv
Found 5 workitems to process
Initializing browser...
Performing authentication...
✓ Authentication successful

Processing 5 workitems...

[1/5] Processing MVA: 50227203
  Damage Type: PM Gas
  Correction: Regular maintenance required
  ✓ Workitem already exists (Status: Open)

[2/5] Processing MVA: 12345678
  Damage Type: Body Damage
  Correction: Repair front bumper
  → Creating new workitem...
  ✓ Workitem created successfully

...

============================================================
SUMMARY
============================================================
Total Processed: 5
  Found Existing: 2
  Created New:    2
  Failed:         1
============================================================
```

## Troubleshooting

### Common Issues

**Login Fails**
- Verify credentials in `webdriver.ini.local`
- Try using `--incognito` to force fresh authentication

**Workitem Creation Fails**
- Check damage type matches application values exactly
- Verify MVA exists in the system
- Review log file for detailed error messages

**CSV Parse Errors**
- Ensure CSV has required columns: MVA, DamageType, CorrectionAction
- Check for proper UTF-8 encoding
- Verify no special characters in headers

## Framework Integration

This client uses the following Compass Framework components:

- **`StandardDriverManager`**: WebDriver lifecycle management
- **`SeleniumNavigator`**: Page navigation
- **`SmartLoginFlow`**: SSO authentication with cache detection
- **`SeleniumPmActions`**: Workitem find/create operations
- **`SeleniumVehicleDataActions`**: MVA entry and verification
- **`read_workitem_list()`**: CSV parsing with normalization

## Development

To modify or extend this client:

1. **Framework Changes**: Update protocols/implementations in `src/compass_core/`
2. **Test Framework**: Run `python run_tests.py all` from repo root
3. **Client Updates**: Modify `CreateMissingWorkItems.py`
4. **Validation**: Test with sample data before production use

## Related Files

- Sample data: `../../data/create_missing_workitems_sample.csv`
- Configuration template: `../../webdriver.ini`
- Framework docs: `../../docs/README.md`
