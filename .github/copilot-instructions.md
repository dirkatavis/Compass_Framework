# Compass Framework - AI Coding Agent Instructions

## Project Overview

Compass Framework is a protocol-based Python framework extracted from the monolithic DevCompass codebase. Built as a pip-installable package with setuptools, it emphasizes clean interfaces, dependency injection, and comprehensive testing. The framework is 75% complete in its refactoring journey.

## Architecture Philosophy

- **Protocol-First Design**: All major components implement Python `@runtime_checkable` protocols  
- **Dependency Injection Ready**: No hard-coded dependencies between components
- **Optional Dependencies**: Features gracefully degrade when dependencies unavailable
- **Comprehensive Testing**: 128+ tests covering protocols, implementations, and edge cases

## Core Architecture

### Package Structure (`src/` layout)
```
src/compass_core/
├── __init__.py              # Public API with conditional imports
├── engine.py                # Core CompassRunner class  
├── [protocol].py           # Interface definitions
├── [implementation].py     # Concrete protocol implementations
tests/
├── test_[protocol]_interface.py    # Protocol compliance tests
├── test_[implementation].py        # Implementation-specific tests  
└── test_meta.py                    # Import validation meta-tests
```

### Current Protocol Implementations (3/4 Complete)
1. **Navigation**: `Navigator` → `SeleniumNavigator` (11 tests)
2. **Configuration**: `Configuration` → `JsonConfiguration` (22 tests) 
3. **Version Checking**: `VersionChecker` → `BrowserVersionChecker` (53 tests)
4. **Logging**: `Logger`/`LoggerFactory` → *Not yet implemented* (remaining work)

## Essential Framework Entry Points

### CompassRunner (Core Engine)
```python
from compass_core import CompassRunner
runner = CompassRunner()
runner.run()  # Outputs version info and activation status
```

### Protocol-Based Components (Main Usage Patterns)
```python
# Configuration management with validation
from compass_core import JsonConfiguration
config = JsonConfiguration()
data = config.load("settings.json")
config.validate()  # Returns validation results with warnings

# Browser/driver version compatibility checking  
from compass_core import BrowserVersionChecker  # Windows only
checker = BrowserVersionChecker()
compatibility = checker.check_compatibility("chrome")

# Web navigation with Selenium (optional dependency)
from compass_core import SeleniumNavigator
navigator = SeleniumNavigator(webdriver_instance)
result = navigator.navigate_to("https://example.com", verify=True)
```

## Critical Development Workflows

### Testing Strategy (TDD Protocol Pattern)
```powershell
# Run all tests frequently during development
python -m unittest discover tests -v

# Target test categories for new protocols:
# 1. Interface compliance (5-7 tests)
# 2. Core functionality (8-15 tests)  
# 3. Edge cases & error handling (5-10 tests)
```

### Protocol Implementation Pattern
1. **Define Protocol Interface** in `[name].py` with `@runtime_checkable`
2. **Create Implementation** in `[name]_[type].py` (e.g., `json_configuration.py`)
3. **Write Interface Tests** in `test_[name]_interface.py` first
4. **Write Implementation Tests** in `test_[name]_[type].py` 
5. **Add Conditional Import** to `__init__.py` with graceful fallback

### Version Synchronization (Critical)
Always update both locations when changing versions:
- [`pyproject.toml`](pyproject.toml) line 7: `version = "0.1.0"`  
- [`engine.py`](src/compass_core/engine.py) line 3: `self.version = "0.1.0"`

## Protocol Design Patterns (Framework Core)

### @runtime_checkable Protocol Definition
```python
from typing import Protocol, runtime_checkable, Dict, Any

@runtime_checkable
class YourProtocol(Protocol):
    """Protocol documentation with usage examples"""
    def required_method(self, param: str) -> Dict[str, Any]: ...
```

### Implementation Pattern (Follow Existing Examples)
- **Study**: [`JsonConfiguration`](src/compass_core/json_configuration.py) - Clean config implementation
- **Study**: [`BrowserVersionChecker`](src/compass_core/browser_version_checker.py) - Complex implementation with fallbacks  
- **Study**: [`SeleniumNavigator`](src/compass_core/selenium_navigator.py) - Optional dependency handling

### Conditional Import Pattern (Essential)
```python
# In __init__.py - graceful fallbacks for missing dependencies
__all__ = ['CompassRunner', 'JsonConfiguration']  # Core API always available

try:
    from .selenium_navigator import SeleniumNavigator
    __all__.append('SeleniumNavigator')
except ImportError:
    pass  # selenium not installed - feature unavailable
```

### Testing Protocol Compliance
```python
# Essential test pattern for all protocols
def test_protocol_compliance(self):
    """Test implementation satisfies protocol interface"""
    self.assertIsInstance(self.implementation, YourProtocol)
    
    # Verify required methods exist
    self.assertTrue(hasattr(self.implementation, 'required_method'))
    self.assertTrue(callable(self.implementation.required_method))
```

## Build & Package Management

### Installation & Development
```powershell
# Development installation (most common)
pip install -e .

# With optional dependencies
pip install -e .[selenium]  # Adds Selenium for navigation features
pip install -e .[web]       # Alias for selenium extras

# Build distribution
python -m build

# Clean build artifacts (per .gitignore)
Remove-Item -Recurse -Force build/, dist/, *.egg-info/, __pycache__/
```

### Package Organization
- **Source Layout**: All code in `src/compass_core/` (not root level)
- **Public API Control**: Only export essentials via `__init__.py.__all__`
- **Optional Dependencies**: Use `pyproject.toml[project.optional-dependencies]`

## Common Development Scenarios

### Adding a New Protocol
```python
# 1. Define Protocol interface
@runtime_checkable
class NewFeature(Protocol):
    def do_something(self) -> Dict[str, Any]: ...

# 2. Create implementation 
class ConcreteNewFeature(NewFeature):
    def do_something(self) -> Dict[str, Any]:
        return {"status": "success"}

# 3. Add conditional import to __init__.py
try:
    from .concrete_new_feature import ConcreteNewFeature  
    __all__.append('ConcreteNewFeature')
except ImportError:
    pass  # Optional dependency not available
```

### Testing New Features (TDD Pattern)
```python
# Write tests FIRST, then implement
class TestNewFeatureInterface(unittest.TestCase):
    def test_protocol_compliance(self):
        implementation = ConcreteNewFeature()
        self.assertIsInstance(implementation, NewFeature)
    
    def test_core_functionality(self):
        result = implementation.do_something() 
        self.assertEqual(result["status"], "success")
```

### Browser/Driver Version Compatibility (Windows Only)
Critical for Selenium automation - use [`BrowserVersionChecker`](src/compass_core/browser_version_checker.py):
```python
from compass_core import BrowserVersionChecker
checker = BrowserVersionChecker()

# Check compatibility before automation
compatibility = checker.check_compatibility("chrome") 
if not compatibility["compatible"]:
    print(f"⚠️  {compatibility['recommendation']}")
    # Update drivers before running tests
```

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