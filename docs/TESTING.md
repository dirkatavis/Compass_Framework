# Compass Framework Test Organization

> Purpose: How to run and organize tests for the framework. Audience: developers executing unit, integration, and E2E tests. Out of scope: project status, refactoring plans, and completion summaries.

Related docs: [PROJECT_STATUS.md](PROJECT_STATUS.md), [COMPLETION_PLAN.md](COMPLETION_PLAN.md)

## Test Structure

```
tests/
├── unit/              # Individual component tests (218 tests)
│   ├── test_*_interface.py     # Protocol compliance tests
│   ├── test_*.py              # Implementation tests
│   └── __init__.py
├── integration/       # Multi-component tests (7 tests) 
│   ├── test_integration.py    # Cross-protocol interactions
│   └── __init__.py
├── e2e/              # End-to-end tests (4 tests)
│   ├── test_e2e.py           # Real browser automation  
│   └── __init__.py
└── __init__.py
```

## Running Tests

### Using the Test Runner (Recommended)

```bash
# Run specific test categories
python run_tests.py unit          # Unit tests only (218 tests)
python run_tests.py integration   # Integration tests only (7 tests)  
python run_tests.py e2e           # E2E tests only (4 tests)
python run_tests.py all           # All tests (E2E skipped by default)

# Enable E2E tests (requires WebDriver setup)
python run_tests.py --enable-e2e all
python run_tests.py --enable-e2e e2e

# Verbose output
python run_tests.py -v unit
```

### Using unittest directly

```bash
# All tests with E2E skipped
python -m unittest discover tests -v

# Unit tests only
python -m unittest discover tests/unit -v

# Integration tests only  
python -m unittest discover tests/integration -v

# E2E tests (will fail without WebDriver setup)
python -m unittest discover tests/e2e -v
```

## Test Categories

### Unit Tests (218 tests)
**Location**: `tests/unit/`  
**Purpose**: Test individual components in isolation  
**Dependencies**: Mocked external dependencies  
**Speed**: Fast (~0.4s)

- **Protocol Interface Tests**: Verify protocol compliance
- **Implementation Tests**: Test concrete implementations  
- **Edge Cases**: Error handling and boundary conditions
 - **SSO/Redirect Verification**: Domain-based URL match tests in navigator

### Integration Tests (7 tests)
**Location**: `tests/integration/`  
**Purpose**: Test multi-protocol interactions  
**Dependencies**: Mock external dependencies  
**Speed**: Fast (~0.03s)

- **Service Composition**: How protocols work together
- **Configuration Integration**: Config-driven behavior
- **Error Propagation**: Cross-component error handling

### End-to-End Tests (4 tests)
**Location**: `tests/e2e/`  
**Purpose**: Complete workflow validation  
**Dependencies**: Real WebDriver, actual websites  
**Speed**: Slow (requires browser automation)

- **Real Browser Automation**: Full WebDriver workflows
- **Configuration-Driven Navigation**: End-to-end config usage
- **Redirect Handling**: Real-world URL redirections  

**Note**: E2E tests are skipped by default and require:
1. WebDriver setup (msedgedriver.exe)
2. Explicit enabling: `unittest._e2e_enabled = True` or `--enable-e2e` flag

## Development Workflow

### Daily Development
```bash
python run_tests.py unit          # Quick feedback during development
python run_tests.py integration   # Verify multi-component interactions
```

### Pre-commit Validation  
```bash
python run_tests.py all           # Full suite (E2E skipped)
```

### Release Validation
```bash
python run_tests.py --enable-e2e all   # Complete validation including E2E
```


## Adding New Tests

### Unit Tests
- Add to `tests/unit/test_<component>.py`
- Follow existing patterns (protocol compliance + implementation)
- Mock external dependencies

### Integration Tests
- Add to `tests/integration/test_integration.py`  
- Test protocol interactions without real dependencies
- Focus on data flow between components

### E2E Tests
- Add to `tests/e2e/test_e2e.py`
- Use real browser automation
- Test complete user workflows
- Include proper `@unittest.skipIf` decorators

## Test Philosophy

**Unit → Integration → E2E**: Complete testing spectrum from isolated components to full workflows.

**Default Safety**: E2E tests skipped by default to prevent failures in development environments without WebDriver setup.

**Developer Productivity**: Fast unit and integration tests for rapid development feedback.