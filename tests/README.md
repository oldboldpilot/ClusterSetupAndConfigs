# Test Suite Documentation

Comprehensive test suite for the modular HPC cluster setup system.

## Quick Start

Run all tests:
```bash
cd /home/muyiwa/Development/ClusterSetupAndConfigs
python3 tests/run_tests.py

# Using uv
uv run python tests/run_tests.py
```

Run with pytest for detailed output:
```bash
pytest tests/ -v
```

Run specific test module:
```bash
python3 -m pytest tests/test_openmp.py -v
python3 -m pytest tests/test_ssh.py -v
python3 tests/test_benchmarks.py  # Direct execution
```

## Test Modules Overview

### Infrastructure Tests

#### `test_ssh.py` - SSH Configuration Tests (8 tests)
Tests SSH key distribution and passwordless SSH setup.

**Test Classes:**
- `TestSSHManager` (7 tests):
  - SSH directory existence and permissions (700)
  - SSH key pair existence (id_rsa, id_rsa.pub)
  - Private key permissions (600)
  - authorized_keys and known_hosts configuration
  
- `TestSSHConnectivity` (1 test):
  - Localhost SSH connection test

**Usage:**
```bash
python3 -m pytest tests/test_ssh.py -v
python3 -m pytest tests/test_ssh.py::TestSSHManager::test_ssh_directory_exists -v
```

#### `test_sudo.py` - Passwordless Sudo Tests (7 tests)
Tests sudo configuration for cluster operations.

**Test Classes:**
- `TestSudoManager` (4 tests):
  - `/etc/sudoers.d/cluster-ops` file existence
  - Sudoers file permissions (440)
  - Individual command sudo access (ln, rsync)
  
- `TestSudoCommands` (4 tests):
  - Command availability tests
  - Non-interactive sudo flag (`sudo -n`)

**Usage:**
```bash
python3 -m pytest tests/test_sudo.py -v
python3 -m pytest tests/test_sudo.py::TestSudoCommands::test_sudo_non_interactive_flag -v
```

### Parallel Programming Tests

#### `test_openmpi.py` - OpenMPI Tests (8 tests)
Tests MPI installation, configuration, and multi-node execution.

**Test Classes:**
- `TestMPIBasic` (5 tests):
  - OpenMPI installation via Homebrew
  - mpicc/mpirun availability
  - Compilation and execution
  
- `TestMPIHostfiles` (3 tests):
  - Hostfile creation (standard, optimal, max)
  - Hostfile content validation

**Usage:**
```bash
python3 -m pytest tests/test_openmpi.py -v
python3 -m unittest tests.test_openmpi.TestMPIHostfiles
```

#### `test_openmp.py` - OpenMP Tests (7 tests)
Tests OpenMP (libomp) installation and thread-level parallelism.

**Test Classes:**
- `TestOpenMP` (5 tests):
  - libomp installation via Homebrew
  - omp.h header file existence
  - GCC OpenMP support (-fopenmp flag)
  - Compilation with OpenMP
  
- `TestOpenMPAdvanced` (2 tests):
  - Parallel region execution
  - OMP_NUM_THREADS environment variable

**Usage:**
```bash
python3 -m pytest tests/test_openmp.py -v
python3 -m pytest tests/test_openmp.py::TestOpenMPAdvanced -v
```

#### `test_openshmem.py` - OpenSHMEM Tests (8 tests)
Tests Sandia OpenSHMEM installation and functionality.

**Test Classes:**
- `TestOpenSHMEM` (5 tests):
  - OpenSHMEM installation directory
  - oshcc/oshrun existence
  - Wrapper symlinks
  
- `TestOpenSHMEMAdvanced` (3 tests):
  - Simple OpenSHMEM compilation
  - Hello World execution test
  - Multi-PE program testing

**Usage:**
```bash
python3 -m pytest tests/test_openshmem.py -v
python3 -m unittest tests.test_openshmem.TestOpenSHMEMAdvanced.test_simple_openshmem_compilation
```

#### `test_berkeley_upc.py` - Berkeley UPC Tests (13 tests)
Tests Berkeley UPC (Unified Parallel C) installation and functionality.

**Test Classes:**
- `TestBerkeleyUPC` (5 tests):
  - Berkeley UPC installation directory
  - upcc/upcrun existence
  - Version information
  - GASNet conduit configuration
  
- `TestBerkeleyUPCAdvanced` (7 tests):
  - Simple UPC program compilation
  - UPC Hello World execution
  - Shared memory allocation and access
  - Collective operations (barrier, broadcast)
  - Static threads mode
  - Pthreads runtime mode
  - Pointer-to-shared functionality
  
- `TestBerkeleyUPCIntegration` (4 tests):
  - upcc/upcrun in PATH
  - Berkeley UPC libraries
  - GASNet libraries

**Usage:**
```bash
python3 -m pytest tests/test_berkeley_upc.py -v
python3 -m pytest tests/test_berkeley_upc.py::TestBerkeleyUPCAdvanced -v
python3 -m unittest tests.test_berkeley_upc.TestBerkeleyUPCAdvanced.test_upc_shared_memory
```

### Performance Tests

#### `test_benchmarks.py` - Benchmark Suite Tests (15 tests)
Tests PGAS benchmark suite creation and execution.

**Test Classes:**
- `TestBenchmarkSuite` (6 tests):
  - Benchmark directory structure (src/, bin/, results/)
  - Makefile existence
  - Run script generation
  
- `TestBenchmarkSourceFiles` (3 tests):
  - Source file existence (upcxx_latency, mpi_latency, bandwidth)
  - Source code validation
  
- `TestBenchmarkCompilation` (3 tests):
  - Makefile functionality
  - Compiler detection (upcxx, mpicxx)
  - Clean target

#### `test_benchmark_templates.py` - Jinja2 Template Tests (24 tests)
Tests Jinja2-based benchmark code generation system.

**Test Classes:**
- `TestBenchmarkTemplateGeneration` (8 tests):
  - Template directory existence
  - Individual template file existence:
    * upcxx_latency.cpp.j2
    * mpi_latency.cpp.j2
    * upcxx_bandwidth.cpp.j2
    * openshmem_latency.cpp.j2
    * berkeley_upc_latency.c.j2
    * Makefile.j2
    * run_benchmarks.sh.j2

- `TestBenchmarkManagerJinja2` (10 tests):
  - BenchmarkManager import and initialization
  - Jinja2 Environment configuration
  - Template rendering for all benchmark types
  - create_all_benchmarks() functionality
  - Configurable parameters (iterations, message_sizes)
  
- `TestBenchmarkTemplateContent` (6 tests):
  - Generated C++ code syntax validation
  - Makefile syntax verification
  - Run script bash syntax checking
  - Template variable substitution

**Usage:**
```bash
python3 -m pytest tests/test_benchmark_templates.py -v
python3 -m unittest tests.test_benchmark_templates.TestBenchmarkTemplateContent.test_upcxx_latency_syntax
```

#### `test_pdsh.py` - PDSH Manager Tests (19 tests)
Tests parallel distributed shell installation and operations.

**Test Classes:**
- `TestPDSHInstallation` (4 tests):
  - PDSHManager import
  - Initialization
  - pdsh availability check
  - Homebrew detection
  
- `TestPDSHHostfile` (2 tests):
  - Hostfile creation (`~/.pdsh/machines`)
  - Hostfile permissions and content
  
- `TestPDSHEnvironment` (1 test):
  - PDSH_RCMD_TYPE environment variable
  
- `TestPDSHCommands` (4 tests):
  - pdsh command existence
  - pdsh --version functionality
  - pdsh --help output
  - Command execution syntax
  
- `TestPDSHAdvanced` (2 tests):
  - Localhost command execution
  - Multi-host syntax validation
  
- `TestPDSHIntegration` (3 tests):
  - SSH configuration compatibility
  - known_hosts file interaction
  - Manager method integration
  
- `TestPDSHConfiguration` (3 tests):
  - ~/.pdsh directory structure
  - Configuration methods
  - Environment setup

**Usage:**
```bash
python3 -m pytest tests/test_pdsh.py -v
python3 -m unittest tests.test_pdsh.TestPDSHCommands
```
  
- `TestBenchmarkExecution` (2 tests):
  - Run script syntax validation
  - Binary existence after compilation

**Usage:**
```bash
python3 -m pytest tests/test_benchmarks.py -v
python3 -m pytest tests/test_benchmarks.py::TestBenchmarkCompilation -v
```

### System Tests

#### `test_cluster_setup.py` - Cluster Setup Tests
Tests overall cluster configuration and orchestration.

**Coverage:**
- YAML configuration loading
- Node connectivity
- Basic setup workflow

**Usage:**
```bash
python3 tests/test_cluster_setup.py
python3 -m unittest tests.test_cluster_setup.TestClusterSetupCore
```

#### `test_pgas.py` - PGAS Library Tests
Tests UPC++ and PGAS runtime configuration.

**Coverage:**
- UPC++ installation
- Library linking
- Multi-node PGAS execution

**Usage:**
```bash
python3 tests/test_pgas.py
python3 -m unittest tests.test_pgas.TestPGASConfiguration
```

## Test Statistics

**Total Test Coverage:**
- **11 Test Modules**
- **62+ Test Methods**
- **Coverage Areas:**
  - SSH configuration (8 tests)
  - Sudo configuration (7 tests)
  - OpenMPI functionality (8 tests)
  - OpenMP functionality (7 tests)
  - OpenSHMEM functionality (8 tests)
  - Berkeley UPC functionality (13 tests)
  - Benchmark suite (15 tests)
  - Jinja2 template system (24 tests)
  - PDSH manager (19 tests)
  - Cluster setup (multiple tests)
  - PGAS libraries (multiple tests)

## Advanced Usage

### Run Specific Test Patterns
```bash
# All OpenMP tests
pytest tests/ -k "openmp" -v

# All installation tests
pytest tests/ -k "installation" -v

# All "Advanced" test classes
pytest tests/ -k "Advanced" -v
```

### Run with Coverage
```bash
pytest tests/ --cov=cluster_modules --cov-report=html
open htmlcov/index.html
```

### Verbose Output with Debugging
```bash
# Show all output including print statements
python3 -m pytest tests/test_module.py -v -s

# Stop on first failure
python3 -m pytest tests/ -x

# Show local variables on failure
python3 -m pytest tests/ -l

# Run only previously failed tests
python3 -m pytest tests/ --lf
```

## Test Environment Requirements

### Software Dependencies
- **Python 3.7+**
- **pytest** (optional, recommended for advanced features)
- **pdsh** (for cluster-wide parallel execution tests)
- **sshpass** (for SSH authentication tests)
- **Homebrew** (on Linux, for package management)
- **GCC 15** (for compilation tests)
- **OpenMPI 5.0.8** (for MPI tests)
- **UPC++ 2025.10.0** (for PGAS tests)

### Cluster Configuration
Tests assume:
- Master node + worker nodes reachable
- SSH connectivity between nodes
- Passwordless sudo configured (for sudo tests)
- Shared home directory or rsync availability
- Proper firewall configuration

## Writing New Tests

### Test File Template
```python
import unittest
import subprocess
import os
from pathlib import Path

class TestYourModule(unittest.TestCase):
    """Test description for your module"""
    
    def setUp(self):
        """Setup before each test"""
        self.test_dir = Path(__file__).parent
        self.cluster_dir = self.test_dir.parent
    
    def tearDown(self):
        """Cleanup after each test"""
        pass
    
    def test_feature_name(self):
        """Test specific feature with descriptive name"""
        result = subprocess.run(['command', 'args'],
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, 
                        f"Command failed: {result.stderr}")
    
    def test_file_exists(self):
        """Test that required file exists"""
        file_path = Path("/path/to/file")
        self.assertTrue(file_path.exists(), 
                       f"{file_path} does not exist")

if __name__ == '__main__':
    unittest.main()
```

### Best Practices
1. **Name conventions**:
   - Test files: `test_*.py`
   - Test methods: `test_*`
   - Descriptive names: `test_ssh_key_permissions` not `test1`

2. **Test structure**:
   - One assertion per test (when possible)
   - Use setUp/tearDown for common initialization
   - Test both success and failure cases
   - Document expected behavior in docstrings

3. **Assertions**:
   - Use descriptive failure messages
   - Test specific conditions, not general state
   - Prefer `assertEqual` over `assertTrue` for comparisons

4. **Mocking**:
   - Mock external dependencies when appropriate
   - Test in isolation when possible
   - Use real integration tests for end-to-end validation

### Adding New Test Module

1. Create test file: `tests/test_newmodule.py`
2. Import and add to `tests/run_tests.py`:
   ```python
   from tests import test_newmodule
   suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_newmodule))
   ```
3. Update this README with:
   - Module description
   - Test classes and methods
   - Usage examples
4. Run tests to verify:
   ```bash
   python3 tests/run_tests.py
   ```

## Common Test Patterns

### Testing Command Execution
```python
def test_command_exists(self):
    """Verify command is installed and accessible"""
    result = subprocess.run(['which', 'command'], 
                          capture_output=True, text=True)
    self.assertEqual(result.returncode, 0, 
                    "Command not found in PATH")
```

### Testing File Existence and Permissions
```python
def test_file_permissions(self):
    """Verify file has correct permissions"""
    file_path = Path("/path/to/file")
    self.assertTrue(file_path.exists(), 
                   f"{file_path} does not exist")
    perms = oct(file_path.stat().st_mode)[-3:]
    self.assertEqual(perms, "600", 
                    f"Wrong permissions: {perms} (expected 600)")
```

### Testing Compilation
```python
def test_program_compilation(self):
    """Test that program compiles without errors"""
    result = subprocess.run(
        ['gcc', 'test.c', '-o', 'test', '-fopenmp'],
        capture_output=True, text=True
    )
    self.assertEqual(result.returncode, 0, 
                    f"Compilation failed:\n{result.stderr}")
    self.assertTrue(Path('test').exists(), 
                   "Binary not created")
```

### Testing Program Execution
```python
def test_program_execution(self):
    """Test that compiled program runs successfully"""
    result = subprocess.run(['./test'], 
                          capture_output=True, text=True,
                          timeout=10)
    self.assertEqual(result.returncode, 0, 
                    f"Execution failed:\n{result.stderr}")
    self.assertIn("expected output", result.stdout,
                 "Output did not contain expected text")
```

## Skipping Tests Conditionally

Use decorators to skip tests when prerequisites aren't met:

```python
import unittest
import os

class TestFeature(unittest.TestCase):
    
    @unittest.skipIf(not os.path.exists('/usr/bin/mpicc'), 
                     "MPI not installed")
    def test_mpi_feature(self):
        """Test requires MPI to be installed"""
        pass
    
    @unittest.skipUnless(os.getenv('RUN_CLUSTER_TESTS'), 
                        "Cluster not configured")
    def test_cluster_feature(self):
        """Test requires cluster to be set up"""
        pass
```

## Troubleshooting Failed Tests

### Common Issues and Solutions

**Issue: Tests fail with "command not found"**
```
Solution: Install missing dependencies
  sudo apt-get install gcc openmpi-bin pdsh sshpass  # Ubuntu/Debian
  brew install gcc open-mpi pdsh                      # macOS/Homebrew
```

**Issue: Permission denied errors**
```
Solution: Check file permissions
  chmod 700 ~/.ssh
  chmod 600 ~/.ssh/id_rsa
  sudo visudo  # For /etc/sudoers.d/ files
```

**Issue: SSH tests fail**
```
Solution: Verify SSH configuration
  ssh-keygen -t rsa -b 4096  # Generate keys if missing
  ssh-copy-id localhost      # Add to authorized_keys
  ssh localhost echo "OK"    # Test connection
```

**Issue: Network tests fail**
```
Solution: Verify cluster connectivity
  ping 192.168.1.147        # Test master
  ping 192.168.1.139        # Test workers
  pdsh -w ^hostfile uptime  # Test pdsh
```

**Issue: Compilation tests fail**
```
Solution: Verify compiler installation
  which gcc mpicc upcxx     # Check PATH
  gcc --version             # Verify version
  brew list gcc open-mpi    # Check Homebrew installs
```

**Issue: pdsh tests fail**
```
Solution: Install or skip pdsh tests
  brew install pdsh                              # Install
  export SKIP_PDSH_TESTS=1                      # Or skip
  python3 -m pytest tests/ -k "not pdsh" -v    # Skip in pytest
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Run Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install pytest pytest-cov
          sudo apt-get update
          sudo apt-get install -y gcc openmpi-bin pdsh
      
      - name: Run tests
        run: |
          pytest tests/ --cov=cluster_modules --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Test Maintenance

### Regular Tasks
- ✅ Run full test suite after code changes
- ✅ Update tests when modules are modified
- ✅ Add tests for new features before implementation (TDD)
- ✅ Remove or update tests for deprecated features
- ✅ Keep test documentation current
- ✅ Review test coverage reports monthly
- ✅ Refactor tests to reduce duplication

### Code Coverage Goals
- **Target: >80% coverage** for all modules
- **Critical paths: 100% coverage** (SSH, sudo, security)
- **Error conditions: Well tested** (network failures, missing dependencies)
- **Edge cases: Covered** (empty files, invalid inputs)

## Performance Benchmarks

Track test execution time:

```bash
# Time full test suite
time python3 tests/run_tests.py

# Show slowest tests
pytest tests/ --durations=10

# Profile test execution
python3 -m cProfile -o tests.prof tests/run_tests.py
python3 -m pstats tests.prof
```

## Contributing

When contributing tests:

1. **Follow existing patterns** - Use similar structure to existing tests
2. **Add comprehensive docstrings** - Explain what each test verifies
3. **Test success and failure paths** - Include negative test cases
4. **Update this README** - Document new test modules/classes
5. **Ensure all tests pass** - Run full suite before submitting PR
6. **Add usage examples** - Show how to run new tests
7. **Consider edge cases** - Test boundary conditions

### Pull Request Checklist
- [ ] All new code has corresponding tests
- [ ] All tests pass locally
- [ ] Test coverage hasn't decreased
- [ ] README updated with new test documentation
- [ ] Test docstrings are clear and complete
- [ ] No hardcoded passwords or IPs in tests

## Resources

- [unittest documentation](https://docs.python.org/3/library/unittest.html)
- [pytest documentation](https://docs.pytest.org/)
- [Python testing best practices](https://docs.python-guide.org/writing/tests/)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

## License

See repository LICENSE file.
