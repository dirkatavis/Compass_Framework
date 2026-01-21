# Compass Framework

Protocol-based Python framework for browser automation and vehicle data lookup. Clean interfaces, optional dependencies, and comprehensive testing.

## Documentation

All documentation is in the [docs/](docs/) folder:

**Getting Started**
- [Usage Guide](docs/USAGE.md) - Complete usage examples and tutorials
- [API Reference](docs/API_REFERENCE.md) - API documentation for all public exports
- [Testing Guide](docs/TESTING.md) - Unit/integration/E2E test workflows

**Project Status**
- [Project Status](docs/PROJECT_STATUS.md) - Current architecture and completion state
- [Gap Analysis](docs/GAP_ANALYSIS.md) - Legacy script migration tracking

**Planning & History**
- [Completion Plan](docs/COMPLETION_PLAN.md) - Refactor project completion summary
- [Roadmap](docs/ROADMAP.md) - Development milestones and planning
- [Browser Cleanup Solution](docs/BROWSER_CLEANUP_SOLUTION.md) - Technical solution documentation

**For Contributors**
- [AI Agent Guide](.github/copilot-instructions.md) - Coding conventions and architecture patterns

## Features

✅ **Authentication Flows**
- `LoginFlow` protocol with SSO support
- `SmartLoginFlow` - automatic SSO cache detection
- Microsoft SSO integration (SeleniumLoginFlow)

✅ **Vehicle Data Lookup**
- `VehicleLookupFlow` - batch MVA processing
- `VehicleDataActions` - property retrieval
- CSV input/output utilities

✅ **Core Protocols**
- `Navigator` - web navigation and verification
- `DriverManager` - WebDriver lifecycle management
- `Configuration` - multi-format config (INI, JSON)
- `Logger` - structured logging

## Quick Start

### Installation
```powershell
# Install in development mode
pip install -e .

# Install with Selenium support (required for vehicle lookup)
pip install -e .[selenium]
```

### Vehicle Lookup Client
```powershell
# Navigate to client directory
cd clients/vehicle_lookup

# Process MVAs from CSV (uses vehicle_lookup_sample.csv by default)
python main.py

# Custom input/output
python main.py --input ../../data/vehicle_lookup_sample.csv --output VehicleLookup_results.csv

# With incognito mode (forces fresh login)
python main.py --incognito

# Verbose logging for debugging
python main.py --verbose
```

### Configuration
Create `webdriver.ini.local` with your credentials:
```ini
[credentials]
username = your.email@example.com
password = your_password
login_id = YOUR_WWID

[app]
app_url = https://your-app-url.com
```

### Testing
```powershell
# Run unit tests
python run_tests.py unit

# Run all tests (E2E skipped by default)
python run_tests.py all

# Enable E2E tests (requires credentials)
python run_tests.py --enable-e2e all
```

For more details on test organization and E2E prerequisites, see [docs/TESTING.md](docs/TESTING.md).

## Development Workflow & Quality Gates
- Always run a complete test pass before starting new development:
	- `python run_tests.py all` (E2E skipped by default)
	- Enable E2E when relevant: `python run_tests.py --enable-e2e all`
- Follow TDD: write failing tests first, then implement protocols/implementations.
- Use PRs via GitHub Copilot; avoid pushing directly to `main`.
- After pulling latest `main`, re-run the full test suite (including E2E when applicable).
- Keep version synchronized in both [pyproject.toml](pyproject.toml) and [src/compass_core/engine.py](src/compass_core/engine.py).
