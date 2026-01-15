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

# Run all tests
python -m unittest discover tests -v

# Run specific test file
python -m unittest tests.test_compass_runner -v

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

### Testing Framework
- **Test Structure**: Comprehensive test suite in [`tests/`](tests/) directory
- **Test Categories**: Unit tests, interface tests, meta-tests for import validation
- **Run Tests**: `python -m unittest discover tests -v` (11 tests currently passing)
- **TDD Approach**: Write tests first, then implement features
- **Meta-Tests**: [`test_meta.py`](tests/test_meta.py) validates all imports work to prevent broken test suites

### Test Files
- [`test_compass_runner.py`](tests/test_compass_runner.py) - Tests for core CompassRunner functionality
- [`test_version_checker_interface.py`](tests/test_version_checker_interface.py) - Interface contract tests
- [`test_navigator_interface.py`](tests/test_navigator_interface.py) - Navigation protocol tests  
- [`test_meta.py`](tests/test_meta.py) - Import validation and test discovery validation

## Interfaces & Protocols

The framework follows **interface-first design** using Python Protocols:

### Current Interfaces
- [`VersionChecker`](src/compass_core/version_checker.py) - Browser/driver version detection protocol
- [`Navigator`](src/compass_core/navigation.py) - Web navigation and page verification protocol

### Interface Design Patterns
- **@runtime_checkable** protocols for runtime type validation
- **Dependency injection** ready - no hard-coded dependencies  
- **Method signature testing** to ensure protocol compliance
- **Return type specifications** using typed dictionaries and generics


The Best Practice: Only expose what is necessary in the top-level __init__.py.

Why: If your team adds 50 files to src/compass_core/, the client shouldn't have to know which file a class lives in. They should just do from compass_core import CompassRunner.

Action: Keep your internal logic deep in the submodules, and "promote" the main classes to the __init__.py.

2. Dependency Management (The "Lightweight" Rule)
The biggest mistake in framework design is forcing every client to install libraries they don't need.

The Best Practice: Use Optional Dependencies (Extras).

Why: If only 10% of your scripts need to connect to SQL Server, don't make the other 90% install heavy drivers.

Implementation: In your pyproject.toml, you can define "extras":

Ini, TOML

[project.optional-dependencies]
sql = ["pyodbc>=4.0"]
api = ["requests>=2.28"]
Clients can then install exactly what they need: pip install -e .[sql].

3. Use Type Hinting (The C# Safety Net)
Python is dynamically typed, which can be terrifying for a C# team.

The Best Practice: Use Type Hints and Pydantic or dataclasses.

Why: It provides IntelliSense in VS Code/PyCharm, making the framework feel "discoverable."

Example:

Python

def process_data(self, record_id: int, metadata: dict[str, str]) -> bool:
    # VS Code will now warn the dev if they pass a string to record_id
    ...
4. Semantic Versioning (The "Contract")
Since you are using a shared framework, a change you make today could break a script someone else wrote six months ago.

The Best Practice: Follow SemVer (Major.Minor.Patch).

Patch (0.1.1): Bug fixes (safe to update).

Minor (0.2.0): New features, no breaking changes (usually safe).

Major (1.0.0): Breaking changes (Client must rewrite code).

Action: Ensure your pyproject.toml version is updated before pushing major changes.

5. Automated Testing (The "Don't Break the Client" Rule)
In a decoupled setup, you need to be certain that a change in the Framework repository doesn't break the Client repository.

The Best Practice: Place a tests/ folder in your Framework root (outside src).

Why: It allows you to run unit tests against the framework logic in isolation.

Action: Encourage the team to write at least one test for every new feature added to the engine.

## Client Integration Workflow

This framework is designed for **framework/client separation** with proper integration testing:

### Repository Structure
```
C:\Temp\Code\
├── Compass_Framework/          # Framework repo (this project)
│   ├── src/compass_core/       # Framework source code
│   ├── tests/                  # Framework unit tests 
│   └── pyproject.toml         # Framework package definition
└── Compass_Clients/           # Client projects repo
    └── project_alpha/         # Integration test project
```

### Development Integration Testing
From any client project directory (e.g., `Compass_Clients/project_alpha/`):

```powershell
# Install framework in development mode from client directory
pip install -e ../../Compass_Framework

# Test framework changes against real client usage
python main.py  # Run client integration tests
```

### Framework Development Rules
- **Never push to main** without verifying client integration tests pass
- Framework unit tests (`python -m unittest discover tests -v`) must pass first  
- Then verify `project_alpha` (or other client projects) still work
- This prevents breaking changes from reaching production

Summary Checklist for the TeamCategoryGoalImportsClients should only import from the package root, not deep subfiles.VisibilityUse _single_leading_underscore for methods that are "Private."EnvironmentNever commit a .venv folder; always use .gitignore.StabilityNever push to main without verifying it doesn't break the project_alpha test script.