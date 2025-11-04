# Test Suite for ClusterSetupAndConfigs

Comprehensive unit and integration tests for the HPC cluster setup and PGAS configuration tools.

## Running Tests

### Run All Tests
```bash
# Using Python directly
python3 tests/run_tests.py

# Using uv
uv run python tests/run_tests.py

# Individual test modules
python3 tests/test_cluster_setup.py
python3 tests/test_pgas.py
```

### Run Specific Test Class
```bash
python3 -m unittest tests.test_cluster_setup.TestClusterSetupCore
python3 -m unittest tests.test_pgas.TestPGASConfiguration
```

### Run Specific Test Method
```bash
python3 -m unittest tests.test_cluster_setup.TestClusterSetupCore.test_os_detection
```

## Test Structure

```
tests/
├── __init__.py              # Package initialization
├── run_tests.py             # Main test runner
├── test_cluster_setup.py    # Core cluster setup tests
└── test_pgas.py             # PGAS configuration tests
```

## Test Coverage

### test_cluster_setup.py

**TestClusterSetupCore**
- `test_cluster_setup_initialization` - Tests ClusterSetup object creation
- `test_os_detection` - Tests OS detection (Ubuntu vs Red Hat)
- `test_run_command` - Tests command execution wrapper
- `test_all_ips_list` - Tests IP list aggregation

**TestYAMLConfig**
- `test_load_simple_config` - Tests simple YAML format loading
- `test_load_extended_config` - Tests extended YAML with OS info

**TestIPValidation**
- `test_valid_ips` - Tests valid IP address formats
- `test_invalid_ips` - Tests invalid IP address detection

### test_pgas.py

**TestPGASConfiguration**
- `test_pgas_methods_exist` - Verifies PGAS methods are defined
- `test_pgas_methods_callable` - Verifies PGAS methods are callable
- `test_pgas_installation_paths` - Tests expected installation paths

**TestPDSHIntegration**
- `test_worker_list_format` - Tests pdsh worker list formatting
- `test_all_nodes_list_format` - Tests pdsh all nodes formatting

## Test Results

```
Ran 13 tests in 18.455s
OK

Tests run: 13
Successes: 13
Failures: 0
Errors: 0
```

## Adding New Tests

1. Create test file in `tests/` directory
2. Import necessary modules:
```python
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from cluster_setup import ClusterSetup
```

3. Create test class extending `unittest.TestCase`
4. Add test methods (must start with `test_`)
5. Update `tests/run_tests.py` to import new module

## Continuous Integration

Tests are designed to:
- Run without requiring actual cluster hardware
- Mock external dependencies (subprocess, network calls)
- Validate configuration logic and data structures
- Ensure methods exist and are properly structured

## Future Tests

Planned test additions:
- SSH configuration tests
- Slurm configuration tests
- OpenMPI configuration tests
- Network firewall tests
- Homebrew installation tests
- pdsh parallel execution tests
- End-to-end integration tests

## Test Requirements

- Python 3.14+
- PyYAML
- unittest (built-in)
- mock/unittest.mock (built-in)

Install test dependencies:
```bash
uv sync  # Installs all dependencies from pyproject.toml
```
