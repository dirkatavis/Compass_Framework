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
