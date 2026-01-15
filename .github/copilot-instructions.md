# Compass Framework - AI Coding Agent Instructions

## Project Overview

Compass Framework is a minimal Python framework built as a pip-installable package using setuptools. The core architecture follows a simple modular design with a single main component: the `CompassRunner` class.

## Architecture

- **Package Structure**: Uses `src/` layout for clean separation between source and build artifacts
- **Entry Point**: [`src/compass_core/__init__.py`](src/compass_core/__init__.py) exports the main `CompassRunner` class
- **Core Engine**: [`src/compass_core/engine.py`](src/compass_core/engine.py) contains the primary framework logic

## Key Components

### CompassRunner Class
Located in [`engine.py`](src/compass_core/engine.py), this is the main framework interface:
```python
from compass_core import CompassRunner
runner = CompassRunner()
runner.run()  # Outputs version info and activation status
```

## Build & Development Workflow

### Package Configuration
- **Build System**: Uses modern `pyproject.toml` with setuptools backend
- **Package Discovery**: Automatically finds packages in `src/` directory
- **Versioning**: Currently hardcoded in both `pyproject.toml` and `engine.py` (keep in sync)

### Installation & Testing
```powershell
# Install in development mode
pip install -e .

# Build distribution packages
python -m build

# Clean build artifacts (as per .gitignore)
Remove-Item -Recurse -Force build/, dist/, *.egg-info/, __pycache__/
```

## Project Conventions

### File Organization
- All source code lives under `src/compass_core/`
- Build artifacts are gitignored (build/, dist/, *.egg-info/, __pycache__/)
- No separate requirements.txt - dependencies should be declared in `pyproject.toml`

### Code Patterns
- **Single Responsibility**: Each class has one clear purpose (CompassRunner = framework activation)
- **Version Management**: Version string appears in both `pyproject.toml` and `CompassRunner.__init__()`
- **Import Pattern**: Clean public API through `__init__.py` re-exports

## Development Notes

### Version Synchronization
When updating versions, modify both:
1. `pyproject.toml` - line 7: `version = "0.1.0"`
2. `engine.py` - line 3: `self.version = "0.1.0"`

### Adding Features
- New classes should follow the pattern in `engine.py`
- Export public APIs through `__init__.py` imports
- Keep the framework lightweight and focused on its core purpose

### No Testing Framework
Currently no test structure exists - consider adding `tests/` directory if implementing test coverage.