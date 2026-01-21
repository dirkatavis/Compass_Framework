# Compass Framework - Client Scripts

This folder contains client scripts that use the Compass Framework to automate vehicle data workflows.

## Client Projects

### vehicle_lookup/
Retrieves glass information (MVA, VIN, Description) for lists of MVAs and exports to CSV.

**Status:** Active development  
**Framework Version:** 0.1.0+

### create_missing_workitems/
Finds or creates workitems from CSV specifications (MVA, DamageType, CorrectionAction).

**Status:** Active development  
**Framework Version:** 0.1.0+

## Setup

All clients use the framework's virtual environment:

```powershell
# From repository root
.\.venv-1\Scripts\Activate.ps1

# Navigate to client folder
cd clients/vehicle_lookup

# Run client script
python main.py
```

## Development Workflow

1. **Framework First:** Implement features in `src/compass_core/`
2. **Test Framework:** Add tests in `tests/`
3. **Client Usage:** Use client scripts to validate real-world workflows
4. **Gap Discovery:** Client failures reveal missing framework features
5. **Iterate:** Return to step 1

## Configuration

Clients share framework configuration:
- **Credentials:** `webdriver.ini.local` (gitignored)
- **Test Data:** `data/vehicle_lookup_sample.csv` and `data/create_missing_workitems_sample.csv`
- **Drivers:** `drivers.local/` (gitignored)

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
