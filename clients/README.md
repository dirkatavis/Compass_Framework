# Compass Framework - Client Applications

Self-contained client applications that use the Compass Framework.

## Client Projects

### vehicle_lookup/
Retrieves glass information (MVA, VIN, Description) for lists of MVAs and exports to CSV.

**Self-Contained**: ✅ Script + Sample CSV + Config (optional) + Output  
**Status**: Production ready  

### create_missing_workitems/
Finds or creates workitems from CSV specifications (MVA, DamageType, CorrectionAction).

**Self-Contained**: ✅ Script + Sample CSV + Config (optional) + Logs  
**Status**: Production ready

## Self-Contained Design

Each client directory is **fully portable** and contains:
- Python script (the executable)
- Sample CSV file (example data)
- Optional config file (`webdriver.ini.local` - create locally)
- Generated outputs (results CSV, logs)

**You can copy any client directory elsewhere and it will work independently.**

## Quick Start

```powershell
# Activate framework environment
.\.venv-1\Scripts\Activate.ps1

# Navigate to any client
cd clients/vehicle_lookup

# Run with included sample data
python VehicleLookup.py
```

## Development Workflow

1. **Framework First:** Implement features in `src/compass_core/`
2. **Test Framework:** Add tests in `tests/`
3. **Client Usage:** Use client scripts to validate real-world workflows
4. **Gap Discovery:** Client failures reveal missing framework features
5. **Iterate:** Return to step 1

## Configuration

### Per-Client Config (Recommended)

Create `webdriver.ini.local` in each client directory:
```ini
[credentials]
username = your.email@example.com
password = your_password
login_id = YOUR_WWID

[app]
app_url = https://your-app-url.com
```

### Shared Config (Alternative)

Create `webdriver.ini.local` in project root - all clients will use it if no local config exists.

### Data Files

- **Sample CSVs**: Included in each client directory
- **Custom Data**: Place your CSV files in the client directory or reference from elsewhere
- **Shared Samples**: Also available in `../../data/` as fallback

## Adding New Clients

1. Create folder: `clients/your_client_name/`
2. Add `main.py` with framework imports
3. Add `README.md` with usage instructions
4. Update this file with client description

## Client Independence

Each client can eventually become its own repository:
```
clients/vehicle_lookup/  →  VehicleLookup_Client/ (separate repo)
```

Just add `requirements.txt`:
```
compass-framework @ git+https://github.com/dirkatavis/Compass_Framework.git
```
