# Compass Framework - API Reference

Quick reference for all public APIs exported by `compass_core`.

---

## Core Components

### CompassRunner
```python
from compass_core import CompassRunner
runner = CompassRunner()
runner.run()  # Display version and status
```

---

## Configuration

### IniConfiguration
```python
from compass_core import IniConfiguration

config = IniConfiguration()
config.load('webdriver.ini.local')
username = config.get('credentials.username')
password = config.get('credentials.password', default='default_value')
```

### JsonConfiguration
```python
from compass_core import JsonConfiguration

config = JsonConfiguration()
config.load('config.json')
setting = config.get('app.setting')
```

---

## Logging

### StandardLogger
```python
from compass_core import StandardLogger

logger = StandardLogger("my_app")
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
logger.debug("Debug message")
```

### StandardLoggerFactory
```python
from compass_core import StandardLoggerFactory

factory = StandardLoggerFactory()
logger = factory.create_logger("component_name")
```

---

## Authentication

### LoginFlow (Protocol)
```python
from compass_core import LoginFlow

# Protocol - implement or use concrete implementations
result = flow.authenticate(
    username="user@example.com",
    password="password",
    url="https://app.example.com",
    login_id="WWID",
    timeout=30
)
# Returns: {'status': 'success'|'error', 'message': str, 'authenticated': bool}
```

### SeleniumLoginFlow
```python
from compass_core import SeleniumLoginFlow, SeleniumNavigator, StandardLogger

logger = StandardLogger("login")
driver = ...  # WebDriver instance
navigator = SeleniumNavigator(driver)
login_flow = SeleniumLoginFlow(driver, navigator, logger)

result = login_flow.authenticate(
    username="user@example.com",
    password="password",
    url="https://login.microsoftonline.com/",
    login_id="WWID123",
    timeout=30
)
```

### SmartLoginFlow (SSO-Aware)
```python
from compass_core import SmartLoginFlow, SeleniumLoginFlow, SeleniumNavigator

base_flow = SeleniumLoginFlow(driver, navigator, logger)
smart_flow = SmartLoginFlow(driver, navigator, base_flow, logger)

result = smart_flow.authenticate(
    username="user@example.com",
    password="password",
    url="https://app.example.com",  # App URL, not login URL
    login_id="WWID123"
)
# Returns authenticated=True if login performed, False if SSO cache hit
```

---

## Navigation

### SeleniumNavigator
```python
from compass_core import SeleniumNavigator

navigator = SeleniumNavigator(driver)

# Navigate to URL
result = navigator.navigate_to(
    url="https://example.com",
    label="Example Site",
    verify=True,
    timeout=10
)

# Verify page loaded
verification = navigator.verify_page(
    url="https://example.com",
    check_locator=('css', '.page-loaded'),
    timeout=10
)
```

---

## Driver Management

### StandardDriverManager
```python
from compass_core import StandardDriverManager

manager = StandardDriverManager()

# Create driver
driver = manager.get_or_create_driver(
    incognito=True,
    headless=False
)

# Check if active
if manager.is_driver_active():
    print("Driver is running")

# Cleanup
manager.quit_driver()
```

---

## Vehicle Data Actions

### SeleniumVehicleDataActions
```python
from compass_core import SeleniumVehicleDataActions, StandardLogger

logger = StandardLogger("vehicle_actions")
actions = SeleniumVehicleDataActions(driver, logger, timeout=10)

# Enter MVA
result = actions.enter_mva("50227203", clear_existing=True)
# Returns: {'status': 'success'|'error', 'mva': str, 'error': str (if error)}

# Verify MVA echo
is_verified = actions.verify_mva_echo("50227203", timeout=5)
# Returns: bool

# Wait for property page
is_loaded = actions.wait_for_property_page_loaded("50227203", timeout=15)
# Returns: bool

# Wait for property
is_loaded = actions.wait_for_property_loaded("VIN", timeout=12)
# Returns: bool

# Get property value
vin = actions.get_vehicle_property("VIN", timeout=5)
# Returns: str | None

# Get multiple properties
properties = actions.get_vehicle_properties(['VIN', 'Desc', 'Year'], timeout=12)
# Returns: dict[str, str] with 'N/A' for missing properties
```

---

## Data Collection

### MvaCollection
```python
from compass_core import MvaCollection

# Create from list
collection = MvaCollection.from_list(['50227203', '12345678', '98765432'])

# Iterate and process
for idx, item in enumerate(collection, start=1):
    print(f"[{idx}/{len(collection)}] Processing MVA: {item.mva}")
    item.mark_processing()
    
    try:
        # ... process MVA ...
        result = {'vin': 'ABC123', 'desc': 'Ford Explorer'}
        item.mark_completed(result)
    except Exception as e:
        item.mark_failed({'error': str(e)})

# Progress tracking
print(f"Progress: {collection.progress_percentage:.1f}%")
print(f"Completed: {len(collection.get_completed())}/{collection.total_count}")
print(f"Failed: {len(collection.get_failed())}")

# Export results to CSV format
results = collection.to_results_list()
# Returns: [{'mva': '...', 'vin': '...', 'desc': '...'}, ...]
```

### CSV Utilities
```python
from compass_core import read_mva_list, write_results_csv

# Read MVA list from CSV
mvas = read_mva_list('data/vehicle_lookup_sample.csv')
print(f"Found {len(mvas)} MVAs")
# Returns: ['50227203', '12345678', ...]

# Write results to CSV
results = [
    {'mva': '50227203', 'vin': '1HGBH41JXMN109186', 'desc': 'Honda Accord'},
    {'mva': '12345678', 'vin': 'N/A', 'desc': 'N/A'},
]
write_results_csv(results, 'output.csv')
# Creates CSV with headers: mva,vin,desc
```

---

## Workflows

### VehicleLookupFlow
```python
from compass_core import VehicleLookupFlow

workflow = VehicleLookupFlow(
    driver_manager=driver_manager,
    navigator=navigator,
    login_flow=smart_login_flow,
    vehicle_actions=vehicle_actions,
    logger=logger
)

# Get workflow ID
workflow_id = workflow.id()  # Returns: "vehicle_lookup_flow"

# Get execution plan
plan = workflow.plan()
# Returns: [{'name': str, 'description': str}, ...]

# Execute workflow
result = workflow.run({
    'username': 'user@example.com',
    'password': 'password',
    'app_url': 'https://app.example.com',
    'login_id': 'WWID123',
    'input_file': 'data/mva.csv',  # OR 'mva_list': ['50227203', '12345678']
    'output_file': 'results.csv',
    'properties': ['VIN', 'Desc'],  # Optional, default: ['VIN', 'Desc']
    'timeout': 12  # Optional, default: 12
})
# Returns: {
#   'status': 'success'|'error',
#   'summary': str,
#   'results_count': int,
#   'success_count': int,
#   'output_file': str,
#   'error': str (if error)
# }
```

---

## CSV Utilities

### read_mva_list
```python
from compass_core import read_mva_list

# Read and normalize MVAs
mvas = read_mva_list('data/mva.csv', normalize=True)
# Returns: ['50227203', '12345678', ...]

# Read without normalization
mvas_raw = read_mva_list('data/mva.csv', normalize=False)
```

**CSV Format**:
```csv
# Header comment (skipped)
50227203
12345678
# Comment (skipped)
```

### write_results_csv
```python
from compass_core import write_results_csv

results = [
    {'mva': '50227203', 'vin': '1HGBH41...', 'desc': '2021 Honda'},
    {'mva': '12345678', 'vin': 'N/A', 'desc': 'N/A', 'error': 'Not found'}
]
write_results_csv(results, 'output.csv')
```

**Output Format**:
```csv
MVA,VIN,Desc,Error
50227203,1HGBH41...,2021 Honda,
12345678,N/A,N/A,Not found
```

---

## Version Checking (Windows Only)

### BrowserVersionChecker
```python
from compass_core import BrowserVersionChecker

checker = BrowserVersionChecker()

# Check compatibility
result = checker.check_compatibility(
    browser="edge",
    driver_path="drivers.local/msedgedriver.exe"
)
# Returns: {
#   'compatible': bool,
#   'browser_version': str,
#   'driver_version': str,
#   'message': str
# }
```

---

## Workflow Manager

### StandardWorkflowManager
```python
from compass_core import StandardWorkflowManager

manager = StandardWorkflowManager()

# Register workflow
manager.register("vehicle_lookup", workflow_instance)

# Execute workflow
result = manager.execute("vehicle_lookup", params={...})
```

---

## PM Actions (Optional)

### SeleniumPmActions
```python
from compass_core import SeleniumPmActions

actions = SeleniumPmActions(driver, logger)
# PM-specific actions implementation
```

---

## Error Handling

All APIs return structured dicts with `status` field:

```python
result = some_api_call()

if result['status'] == 'success':
    # Handle success
    data = result['data']
elif result['status'] == 'error':
    # Handle error
    error_msg = result.get('error', 'Unknown error')
    logger.error(f"Operation failed: {error_msg}")
```

---

## Type Hints

All protocols use proper type hints:

```python
from typing import Dict, Any, List

def authenticate(
    self,
    username: str,
    password: str,
    url: str,
    **kwargs
) -> Dict[str, Any]:
    ...
```

---

## Constants

### Timeout Constants
```python
# From selenium_navigator.py, selenium_login_flow.py, etc.
DEFAULT_WAIT_TIMEOUT = 10  # seconds
DEFAULT_POLL_FREQUENCY = 0.5  # seconds
```

---

## See Also

- [docs/USAGE.md](USAGE.md) - Complete usage guide with examples
- [GAP_ANALYSIS.md](../GAP_ANALYSIS.md) - Migration from legacy scripts
- [docs/TESTING.md](TESTING.md) - Testing guide
- [PROJECT_STATUS.md](../PROJECT_STATUS.md) - Architecture overview
