# Compass Framework

Protocol-based Python framework with clean interfaces, optional dependencies, and comprehensive testing.

## Documentation Index
- **Project Status**: snapshot and completion summary — see [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Completion Plan**: earlier planning notes — see [COMPLETION_PLAN.md](COMPLETION_PLAN.md)
- **Browser Cleanup Solution**: proposed approach for cleanup — see [BROWSER_CLEANUP_SOLUTION.md](BROWSER_CLEANUP_SOLUTION.md)
- **Testing Guide**: unit/integration/E2E workflows — see [docs/TESTING.md](docs/TESTING.md)
- **AI Agent Guide**: conventions for coding agents — see [.github/copilot-instructions.md](.github/copilot-instructions.md)

## Quick Start
```powershell
# Install in development mode
pip install -e .

# Run unit tests
python run_tests.py unit
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

## SSO & Redirect Handling
- **Domain match verification**: Use `Navigator.verify_page(match='domain')` to tolerate SSO/multipass redirects while ensuring you’re on the expected host.
- **Examples**:
	- Verify Microsoft login host: `navigator.verify_page(url="https://login.microsoftonline.com", match="domain")`
	- Verify Foundry workspace host: `navigator.verify_page(url="https://avisbudget.palantirfoundry.com", match="domain")`

## Incognito Mode
- **Edge InPrivate**: `StandardDriverManager.get_or_create_driver(incognito=True)` adds `--inprivate` for privacy-sensitive runs.
- Combine with headless: `get_or_create_driver(headless=True, incognito=True)` (note: headless can alter auth flows).

## UI Flow Sample
Demonstration script to launch Edge, navigate/login, and optionally enter an MVA.

```powershell
# Provide credentials via environment variables
$env:UI_SAMPLE_USERNAME = "you@example.com"
$env:UI_SAMPLE_PASSWORD = "yourPassword"

# Microsoft login page (incognito)
python scripts/ui_flow_sample.py --url https://login.microsoftonline.com/ --incognito

# Foundry workspace (domain verification, incognito)
python scripts/ui_flow_sample.py --url https://avisbudget.palantirfoundry.com/workspace/fleet-operations-pwa/health --incognito

# Optional MVA entry (supports css=... or xpath=...)
python scripts/ui_flow_sample.py --url https://example.com \
	--mva MVA12345 --mva-locator xpath=//input[@name='search'] --incognito
```

Notes:
- The script detects Microsoft login automatically and performs login when credentials are provided.
- Post-run, the script pauses briefly for inspection and then closes the browser.
