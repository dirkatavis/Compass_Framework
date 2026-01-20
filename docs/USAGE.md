# Compass Framework - Usage Guide

Complete guide for using Compass Framework for browser automation and vehicle data lookup.

---

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Vehicle Lookup](#vehicle-lookup)
- [Protocol Usage](#protocol-usage)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Installation

### Basic Installation
```powershell
# Clone repository
git clone https://github.com/dirkatavis/Compass_Framework.git
cd Compass_Framework

# Install in development mode
pip install -e .
```

### With Selenium Support (Required for Vehicle Lookup)
```powershell
pip install -e .[selenium]
```

### Verify Installation
```powershell
# Run unit tests
python run_tests.py unit

# Check version
python -c "from compass_core import CompassRunner; CompassRunner().run()"
```

---

## Configuration

### Create Local Configuration

Create `webdriver.ini.local` (gitignored) in project root:

```ini
[credentials]
username = your.email@example.com
password = your_password
login_id = YOUR_WWID

[app]
app_url = https://your-compass-url.com
login_url = https://login.microsoftonline.com/

[webdriver]
edge_path = drivers.local/msedgedriver.exe
```

### Environment Variables (Alternative)
```powershell
$env:COMPASS_USERNAME = "your.email@example.com"
$env:COMPASS_PASSWORD = "your_password"
$env:COMPASS_LOGIN_ID = "YOUR_WWID"
```

### Configuration Priority
1. `webdriver.ini.local` (local overrides)
2. Environment variables
3. `webdriver.ini` (template)

---

## Vehicle Lookup

### Quick Start

```powershell
# Navigate to client directory
cd clients/vehicle_lookup

# Process MVAs from default input (data/sample_mva_list.csv)
python main.py

# Custom input/output
python main.py --input ../../data/sample_mva_list.csv --output GlassInfo.csv
```

### Command Line Options

```powershell
# Custom input CSV
python main.py --input path/to/mva_list.csv

# Custom output path
python main.py --output path/to/results.csv

# With incognito mode (forces fresh login)
python main.py --incognito

# Custom configuration file
python main.py --config path/to/webdriver.ini.local

# Verbose logging for debugging
python main.py --verbose

# Headless mode
python main.py --headless
```

### Input CSV Format

```csv
# MVA List for Vehicle Lookup
# One MVA per line, 8 digits recommended
50227203
12345678
98765432
```

- Lines starting with `#` are comments (ignored)
- Empty lines are ignored
- MVAs are automatically normalized

### Output CSV Format

```csv
mva,vin,desc
50227203,1HGBH41JXMN109186,Honda Accord
12345678,N/A,N/A
98765432,5FNRL6H73MB012345,Honda Odyssey
```

### Features

- **Automatic Session Cleanup**: Clears previous output CSV before each run
- **Progress Tracking**: Real-time progress updates with percentage complete
- **Smart Authentication**: Detects and reuses existing SSO sessions
- **Error Handling**: Failed MVAs logged with specific error messages
- **Property Logging**: Detailed INFO-level logging of each property retrieval

---

## Protocol Usage

### 1. Authentication

```python
from compass_core import (
    StandardDriverManager,
    SeleniumNavigator,
    SeleniumLoginFlow,
    SmartLoginFlow,
    StandardLogger
)

# Initialize components
logger = StandardLogger("my_app")
driver_manager = StandardDriverManager()
driver = driver_manager.get_or_create_driver(incognito=True)
navigator = SeleniumNavigator(driver)

# Create login flows
base_login = SeleniumLoginFlow(driver, navigator, logger)
smart_login = SmartLoginFlow(driver, navigator, base_login, logger)

# Authenticate (smart flow detects SSO cache)
result = smart_login.authenticate(
    username="user@example.com",
    password="password",
    url="https://app.example.com",
    login_id="WWID123",
    timeout=30
)

if result['status'] == 'success':
    if result['authenticated']:
        logger.info("Performed login")
    else:
        logger.info("SSO session active, skipped login")
else:
    logger.error(f"Login failed: {result['error']}")
```

### 2. Vehicle Data Actions

```python
from compass_core import SeleniumVehicleDataActions

# Initialize actions
actions = SeleniumVehicleDataActions(driver, logger)

# Enter MVA
result = actions.enter_mva("50227203")
if result['status'] == 'success':
    logger.info(f"Entered MVA: {result['mva']}")

# Verify echo
if actions.verify_mva_echo("50227203", timeout=5):
    logger.info("MVA echo verified")

# Get properties
if actions.wait_for_property_loaded("VIN", timeout=12):
    vin = actions.get_vehicle_property("VIN", timeout=2)
    logger.info(f"VIN: {vin}")

if actions.wait_for_property_loaded("Desc", timeout=12):
    desc = actions.get_vehicle_property("Desc", timeout=2)
    logger.info(f"Description: {desc}")

# Get multiple properties at once
properties = actions.get_vehicle_properties(['VIN', 'Desc', 'Year'], timeout=12)
logger.info(f"Properties: {properties}")
```

### 3. Batch Processing with VehicleLookupFlow

```python
from compass_core import VehicleLookupFlow

# Create workflow
workflow = VehicleLookupFlow(
    driver_manager=driver_manager,
    navigator=navigator,
    login_flow=smart_login,
    vehicle_actions=actions,
    logger=logger
)

# Execute workflow
result = workflow.run({
    'username': 'user@example.com',
    'password': 'password',
    'app_url': 'https://app.example.com',
    'login_id': 'WWID123',
    'input_file': 'data/mva.csv',
    'output_file': 'results.csv',
    'properties': ['VIN', 'Desc'],
    'timeout': 12
})

if result['status'] == 'success':
    logger.info(f"Processed {result['results_count']} MVAs")
    logger.info(f"Successful: {result['success_count']}")
    logger.info(f"Output: {result['output_file']}")
```

### 4. CSV Utilities

```python
from compass_core import read_mva_list, write_results_csv

# Read MVA list
mvas = read_mva_list('data/mva.csv', normalize=True)
logger.info(f"Read {len(mvas)} MVAs")

# Write results
results = [
    {'mva': '50227203', 'vin': '1HGBH41...', 'desc': '2021 Honda'},
    {'mva': '12345678', 'vin': 'N/A', 'desc': 'N/A', 'error': 'Not found'}
]
write_results_csv(results, 'output.csv')
logger.info("Results written")
```

### 5. Configuration Loading

```python
from compass_core import IniConfiguration, JsonConfiguration

# INI configuration
ini_config = IniConfiguration()
ini_config.load('webdriver.ini.local')
username = ini_config.get('credentials.username')
app_url = ini_config.get('app.app_url')

# JSON configuration
json_config = JsonConfiguration()
json_config.load('config.json')
settings = json_config.get('settings.timeout')
```

---

## Examples

### Example 1: Simple Vehicle Lookup

```python
#!/usr/bin/env python3
"""Simple vehicle lookup example."""
from compass_core import (
    StandardDriverManager, SeleniumNavigator,
    SeleniumLoginFlow, SmartLoginFlow,
    SeleniumVehicleDataActions,
    IniConfiguration, StandardLogger
)

# Setup
logger = StandardLogger("vehicle_lookup")
config = IniConfiguration()
config.load('webdriver.ini.local')

# Initialize
driver_manager = StandardDriverManager()
driver = driver_manager.get_or_create_driver(incognito=True)
navigator = SeleniumNavigator(driver)
base_login = SeleniumLoginFlow(driver, navigator, logger)
smart_login = SmartLoginFlow(driver, navigator, base_login, logger)
actions = SeleniumVehicleDataActions(driver, logger)

# Authenticate
auth = smart_login.authenticate(
    username=config.get('credentials.username'),
    password=config.get('credentials.password'),
    url=config.get('app.app_url'),
    login_id=config.get('credentials.login_id')
)

if auth['status'] == 'success':
    # Lookup vehicle
    actions.enter_mva("50227203")
    if actions.wait_for_property_loaded("VIN"):
        vin = actions.get_vehicle_property("VIN")
        logger.info(f"VIN: {vin}")

# Cleanup
driver_manager.quit_driver()
```

### Example 2: Batch Processing

See [scripts/vehicle_lookup_client.py](../scripts/vehicle_lookup_client.py) for full example.

---

## Troubleshooting

### Common Issues

#### 1. ImportError: No module named 'compass_core'
```powershell
# Ensure package is installed
pip install -e .[selenium]
```

#### 2. Selenium not available
```powershell
# Install Selenium dependencies
pip install selenium
```

#### 3. Missing credentials
```
Error: Missing credentials (username/password/app_url)
```
**Solution**: Create `webdriver.ini.local` or set environment variables

#### 4. WebDriver version mismatch
```
Error: Browser compatibility failed
```
**Solution**: Update Edge WebDriver in `drivers.local/` to match browser version

#### 5. Login timeout
```
Error: Login failed - timeout
```
**Solution**: 
- Increase timeout: `--timeout 60`
- Check network connectivity
- Verify credentials

#### 6. Property not loading
```
Warning: Property VIN did not load
```
**Solution**:
- Increase timeout
- Verify MVA is valid
- Check if property exists for this vehicle

### Debug Mode

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Validation

Run tests to verify setup:
```powershell
# Unit tests (no credentials needed)
python run_tests.py unit

# E2E tests (requires credentials)
python run_tests.py --enable-e2e e2e
```

---

## Next Steps

- See [GAP_ANALYSIS.md](../GAP_ANALYSIS.md) for migration from legacy scripts
- See [docs/TESTING.md](../docs/TESTING.md) for testing guide
- See [PROJECT_STATUS.md](../PROJECT_STATUS.md) for architecture overview
- See [.github/copilot-instructions.md](../.github/copilot-instructions.md) for development guidelines
