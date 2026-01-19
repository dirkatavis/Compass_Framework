# E2E Testing Guide

End-to-end tests validate complete workflows against the real Compass application.

## Configuration Required

### 1. Credentials
Create `webdriver.ini.local` with your credentials:

```ini
[credentials]
username = your.email@example.com
password = YourPassword
login_id = tenant-id-or-alias

[app]
login_url = https://login.microsoftonline.com/
app_url = https://your-compass-instance.com/
```

**OR** use environment variables:
```bash
set COMPASS_USERNAME=your.email@example.com
set COMPASS_PASSWORD=YourPassword
set COMPASS_LOGIN_ID=tenant-id
```

### 2. Test MVA
Configure test MVA (optional):
```bash
set TEST_MVA=50227203
set TEST_MVAS=50227203,12345678,98765432
```

## Running E2E Tests

### All E2E Tests (Existing + New)
```bash
python run_tests.py --enable-e2e e2e
```

### Vehicle Lookup Tests Only
```bash
python -m unittest tests.e2e.test_vehicle_lookup -v
# Must set unittest._e2e_enabled = True or use run_tests.py
```

### Single Test
```bash
python tests/e2e/test_vehicle_lookup.py
# (Sets _e2e_enabled automatically)
```

## Test Coverage

### test_vehicle_lookup.py (NEW - Requires Credentials)
- **test_login_flow_authentication**: Validates LoginFlow with Microsoft SSO
- **test_vehicle_data_actions_mva_lookup**: Single MVA → VIN + Desc retrieval
- **test_batch_mva_lookup_workflow**: VehicleLookupFlow with multiple MVAs

### test_e2e.py (Existing - No Credentials Needed)
- **test_basic_web_navigation**: Example.com navigation
- **test_configuration_driven_navigation**: Config-based navigation
- **test_driver_lifecycle_management**: Driver create/reuse/quit
- **test_palantir_redirect_handling**: SSO redirect handling

## Skip Behavior

Tests automatically skip if:
- E2E mode not enabled (`unittest._e2e_enabled` not set)
- Credentials not configured (webdriver.ini.local missing + no env vars)
- Driver not compatible with browser

## Security Notes

- **Never commit `webdriver.ini.local`** - it's gitignored
- **Use environment variables in CI/CD**
- **Rotate credentials regularly**
- **Use test accounts, not production accounts**

## Troubleshooting

**"Credentials not configured"**
- Check `webdriver.ini.local` exists with `[credentials]` section
- OR set `COMPASS_USERNAME`, `COMPASS_PASSWORD`, `COMPASS_LOGIN_ID` env vars

**"E2E tests disabled"**
- Use `python run_tests.py --enable-e2e e2e`
- OR set `unittest._e2e_enabled = True` in test runner

**"Authentication failed"**
- Verify credentials are correct
- Check `login_url` points to correct SSO provider
- Ensure network access to login URL

**"MVA input field not found"**
- Verify `app_url` navigates to correct page with MVA input
- Check selectors in `SeleniumVehicleDataActions` match your app version
- Application may have changed - update selectors

## Example Run

```bash
# Configure credentials
echo [credentials] > webdriver.ini.local
echo username = test.user@example.com >> webdriver.ini.local
echo password = TestPass123 >> webdriver.ini.local
echo login_id = common >> webdriver.ini.local

# Run vehicle lookup tests
python run_tests.py --enable-e2e e2e

# Expected output:
# test_login_flow_authentication ... ok
# test_vehicle_data_actions_mva_lookup ... ok
# test_batch_mva_lookup_workflow ... ok
# Ran 7 tests in 85.234s
# OK
```
