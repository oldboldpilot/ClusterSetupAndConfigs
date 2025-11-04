# Cluster Modules Documentation

This directory contains modular components for HPC cluster setup, configuration, and management.

## Module Overview

### Core Infrastructure Modules

#### `ssh_manager.py` - SSH Configuration
Manages SSH key distribution and passwordless SSH setup across the cluster.

**Key Features:**
- SSH key pair generation
- Public key distribution to all nodes
- Cross-node SSH mesh configuration
- SSH config file management

**Usage:**
```python
from cluster_modules import SSHManager

ssh_mgr = SSHManager(username, password, master_ip, worker_ips)
ssh_mgr.setup_ssh()
ssh_mgr.test_ssh_connectivity()
```

#### `sudo_manager.py` - Passwordless Sudo
Configures passwordless sudo for cluster operations using pdsh for parallel execution.

**Key Features:**
- Creates `/etc/sudoers.d/cluster-ops` configuration
- Allows passwordless: ln, rsync, systemctl, mkdir, chmod, chown, tee, cp
- pdsh-based parallel configuration with sequential fallback
- Per-node sudo access testing

**Usage:**
```python
from cluster_modules import SudoManager

sudo_mgr = SudoManager(username, password, all_ips)
sudo_mgr.configure_passwordless_sudo_cluster_pdsh()
sudo_mgr.test_passwordless_sudo(node_ip)
```

#### `network_manager.py` - Network & Firewall
Manages network configuration and firewall rules across the cluster.

**Key Features:**
- UFW configuration (Ubuntu/Debian)
- firewalld configuration (Red Hat/CentOS)
- Opens ports for MPI (50000-50200), Slurm (6817-6819), SSH (22)
- `/etc/hosts` file management
- Network connectivity testing

**Usage:**
```python
from cluster_modules import NetworkManager

net_mgr = NetworkManager(username, password, master_ip, worker_ips, node_hostnames)
net_mgr.configure_firewall_cluster_pdsh()
net_mgr.update_hosts_file_cluster_pdsh()
net_mgr.test_network_connectivity()
```

### Parallel Programming Modules

#### `mpi_manager.py` - OpenMPI Configuration
Handles OpenMPI installation, hostfile creation, and MCA parameters.

**Key Features:**
- Creates three hostfile variants:
  - `hostfile` - balanced distribution
  - `hostfile_optimal` - optimized for total throughput
  - `hostfile_max` - maximum parallelism
- MCA parameters configuration
- Multi-node MPI testing

**Usage:**
```python
from cluster_modules import MPIManager

mpi_mgr = MPIManager(master_ip, worker_ips)
mpi_mgr.install_and_configure()
mpi_mgr.test_mpi_multinode()
```

#### `openmp_manager.py` - OpenMP Configuration
Manages OpenMP (libomp) installation and thread-level parallelism.

**Key Features:**
- libomp installation via Homebrew
- Compiler flag configuration (-fopenmp)
- Thread-level parallelism testing
- Cluster-wide distribution with pdsh

**Usage:**
```python
from cluster_modules import OpenMPManager

openmp_mgr = OpenMPManager(username, password, master_ip, worker_ips)
openmp_mgr.install_libomp_cluster_pdsh()
openmp_mgr.test_openmp_cluster(num_threads=4)
```

#### `openshmem_manager.py` - OpenSHMEM Configuration
Handles Sandia OpenSHMEM 1.5.2 installation and distribution.

**Key Features:**
- Downloads and compiles Sandia OpenSHMEM
- PMI support configuration
- Cluster-wide distribution via rsync + pdsh
- Creates oshcc/oshrun wrapper symlinks
- Multi-node testing

**Usage:**
```python
from cluster_modules import OpenSHMEMManager

openshmem_mgr = OpenSHMEMManager(
    username, password, master_ip, worker_ips,
    build_node_ip="192.168.1.136",
    openshmem_version="1.5.2"
)

# Full installation workflow
openshmem_mgr.download_openshmem()
openshmem_mgr.extract_openshmem()
openshmem_mgr.configure_openshmem()
openshmem_mgr.build_openshmem(num_jobs=8)
openshmem_mgr.install_openshmem()
openshmem_mgr.distribute_openshmem_pdsh()
openshmem_mgr.create_wrapper_symlinks()
openshmem_mgr.test_openshmem_local()
```

#### `berkeley_upc_manager.py` - Berkeley UPC Configuration
Manages Berkeley UPC (Unified Parallel C) installation and configuration.

**Key Features:**
- Downloads and compiles Berkeley UPC from official sources
- GASNet network conduit configuration (MPI, UDP, SMP, IB)
- POSIX threads support
- Static and dynamic thread modes
- Cluster-wide distribution via rsync + pdsh
- Creates upcc/upcrun wrapper symlinks
- Comprehensive testing with shared memory examples

**Usage:**
```python
from cluster_modules import BerkeleyUPCManager

bupc_mgr = BerkeleyUPCManager(
    username, password, master_ip, worker_ips,
    berkeley_upc_version="2023.9.0",
    gasnet_conduit="mpi",
    enable_pthreads=True
)

# Full installation workflow
bupc_mgr.install_full_workflow(num_jobs=8)

# Or step by step
bupc_mgr.download_berkeley_upc()
bupc_mgr.extract_berkeley_upc()
bupc_mgr.configure_berkeley_upc()
bupc_mgr.build_berkeley_upc(num_jobs=8)
bupc_mgr.install_berkeley_upc()
bupc_mgr.distribute_berkeley_upc_pdsh()
bupc_mgr.create_wrapper_scripts()
bupc_mgr.test_berkeley_upc_local()

# Get version information
version_info = bupc_mgr.get_berkeley_upc_version_info()
print(f"Berkeley UPC {version_info['version']}")
print(f"GASNet conduit: {version_info['gasnet_conduit']}")
```

### Performance & Workload Management

#### `benchmark_manager.py` - PGAS Benchmarks
Creates and manages PGAS benchmark suite (UPC++, MPI, OpenSHMEM, Berkeley UPC) using Jinja2 templates.

**Key Features:**
- **Jinja2-Based Code Generation**: Dynamic benchmark generation from templates
- Configurable iterations, warmup iterations, and message sizes
- Point-to-point latency benchmarks (UPC++, MPI, OpenSHMEM, Berkeley UPC)
- Bandwidth benchmarks (UPC++)
- Template-based Makefile and run script generation
- Customizable compiler flags and options
- Multi-node execution support
- Parallel distribution via pdsh

**Template System:**
Located in `cluster_modules/templates/`:
- `upcxx_latency.cpp.j2` - UPC++ RPC-based latency
- `mpi_latency.cpp.j2` - MPI Send/Recv latency
- `upcxx_bandwidth.cpp.j2` - UPC++ bandwidth testing
- `openshmem_latency.cpp.j2` - OpenSHMEM latency
- `berkeley_upc_latency.c.j2` - Berkeley UPC latency
- `Makefile.j2` - Compilation makefile
- `run_benchmarks.sh.j2` - Execution script

**Usage:**
```python
from cluster_modules import BenchmarkManager

bench_mgr = BenchmarkManager(username, password, master_ip, worker_ips)

# Create benchmarks with custom parameters
bench_mgr.create_upcxx_latency_benchmark(iterations=2000, warmup_iterations=200)
bench_mgr.create_mpi_latency_benchmark(iterations=2000, warmup_iterations=200, message_size=8)
bench_mgr.create_upcxx_bandwidth_benchmark(iterations=1000, message_sizes=[1024, 4096, 16384])

# Or create all with defaults
bench_mgr.create_all_benchmarks()

# Compile and distribute
bench_mgr.compile_benchmarks()
bench_mgr.distribute_benchmarks_pdsh()
```

**Note:** For standalone benchmark execution, use:
```bash
python -m cluster_tools.benchmarks.run_benchmarks --help
```

#### `slurm_manager.py` - Slurm Workload Manager
Manages Slurm installation and configuration for job scheduling.

**Key Features:**
- Slurm installation via Homebrew or system package manager
- `slurm.conf` generation with node definitions
- Cgroups configuration for resource management
- slurmctld (controller) and slurmd (daemon) service management
- Cluster-wide configuration distribution

**Usage:**
```python
from cluster_modules import SlurmManager

slurm_mgr = SlurmManager(
    username, password, master_ip, worker_ips,
    cluster_name="hpc_cluster"
)

slurm_mgr.install_slurm_cluster_pdsh()

node_info = {
    "192.168.1.147": {"hostname": "master", "threads": 32, "memory": 64000},
    "192.168.1.139": {"hostname": "worker1", "threads": 16, "memory": 32000},
    # ...
}

slurm_mgr.write_slurm_conf(node_info)
slurm_mgr.distribute_slurm_conf_pdsh()
slurm_mgr.start_slurmctld()  # On master
slurm_mgr.start_slurmd_cluster_pdsh()  # On all nodes
slurm_mgr.test_slurm_cluster()
```

#### `pdsh_manager.py` - Parallel Distributed Shell
Manages pdsh installation and configuration for parallel command execution.

**Key Features:**
- Multi-OS installation support (Homebrew, apt, yum, dnf, zypper)
- Automatic package manager detection
- Hostfile management (`~/.pdsh/machines`)
- Environment configuration (`PDSH_RCMD_TYPE=ssh`)
- Connectivity testing
- Parallel command execution across cluster

**Usage:**
```python
from cluster_modules import PDSHManager

pdsh_mgr = PDSHManager(username, password, master_ip, worker_ips)

# Full installation and configuration
pdsh_mgr.install_and_configure_cluster()

# Or step by step
pdsh_mgr.install_pdsh_local()
pdsh_mgr.install_pdsh_cluster_sequential()
pdsh_mgr.create_hostfile()
pdsh_mgr.configure_pdsh_environment()
pdsh_mgr.test_pdsh_connectivity()

# Execute commands in parallel
pdsh_mgr.run_pdsh_command("hostname", hosts="192.168.1.2,192.168.1.3")
```

## Common Patterns

### Parallel Execution with pdsh
Most managers support pdsh-based parallel execution across the cluster for performance:

```python
# SSH keys distributed in parallel
ssh_mgr.distribute_keys_pdsh()

# Sudo configured in parallel
sudo_mgr.configure_passwordless_sudo_cluster_pdsh()

# Firewall configured in parallel
net_mgr.configure_firewall_cluster_pdsh()
```

All pdsh methods automatically fall back to sequential execution if pdsh fails.

### Password Handling
**CRITICAL**: Passwords are NEVER hardcoded. They are always passed as parameters:

```python
# Correct: Password from command-line argument or prompt
import getpass
password = getpass.getpass("Enter cluster password: ")
manager = SomeManager(username, password, ...)

# WRONG: Never do this
password = "hardcoded_password"  # ❌ NEVER
```

### Error Handling
All managers return boolean success indicators:

```python
if ssh_mgr.setup_ssh():
    print("✓ SSH setup successful")
else:
    print("✗ SSH setup failed")
    # Handle error
```

## Integration with cluster_setup.py

The main `cluster_setup.py` acts as an orchestrator that uses these modules:

```python
from cluster_modules import (
    SSHManager, SudoManager, MPIManager,
    OpenMPManager, OpenSHMEMManager, BenchmarkManager,
    SlurmManager, NetworkManager
)

class ClusterSetup:
    def __init__(self, master_ip, worker_ips, username, password):
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.username = username
        self.password = password
        self.all_ips = [master_ip] + worker_ips
        
        # Initialize managers
        self.ssh_mgr = SSHManager(username, password, master_ip, worker_ips)
        self.sudo_mgr = SudoManager(username, password, self.all_ips)
        self.mpi_mgr = MPIManager(master_ip, worker_ips)
        # ... more managers
    
    def run_full_setup(self):
        """Orchestrate complete cluster setup"""
        self.ssh_mgr.setup_ssh()
        self.sudo_mgr.configure_passwordless_sudo_cluster_pdsh()
        self.mpi_mgr.install_and_configure()
        # ... more setup steps
```

## Testing

Each module has corresponding tests in the `tests/` directory:

- `tests/test_ssh.py` - SSH manager tests
- `tests/test_sudo.py` - Sudo manager tests
- `tests/test_openmpi.py` - OpenMPI tests
- `tests/test_openmp.py` - OpenMP tests
- `tests/test_openshmem.py` - OpenSHMEM tests
- `tests/test_berkeley_upc.py` - Berkeley UPC tests
- `tests/test_benchmarks.py` - Benchmark tests

Run all tests:
```bash
python3 tests/run_tests.py
```

## Module Dependencies

```
cluster_modules/
├── core.py                  # Base functionality (if exists)
├── installer_base.py        # Base installer class (if exists)
├── ssh_manager.py           # No dependencies
├── sudo_manager.py          # No dependencies
├── network_manager.py       # No dependencies
├── mpi_manager.py           # Depends on: ssh_manager
├── openmp_manager.py        # Depends on: Homebrew
├── openshmem_manager.py     # Depends on: ssh_manager, GCC
├── berkeley_upc_manager.py  # Depends on: ssh_manager, GCC, GASNet
├── benchmark_manager.py     # Depends on: mpi_manager, UPC++, OpenSHMEM, Berkeley UPC
└── slurm_manager.py         # Depends on: ssh_manager, sudo_manager
```

## Best Practices

1. **Always use pdsh methods when available** - Significantly faster for cluster-wide operations
2. **Never hardcode passwords** - Always pass as parameters or use getpass
3. **Check return values** - All methods return boolean success indicators
4. **Use proper IPs** - Get cluster IPs from configuration, never hardcode
5. **Test after changes** - Run test suite after modifications
6. **Log operations** - All managers print progress and status
7. **Handle errors gracefully** - Check return values and provide fallbacks

## Environment Requirements

- **Python 3.7+**
- **pdsh** - Parallel distributed shell (recommended)
- **sshpass** - Non-interactive SSH password authentication
- **rsync** - File synchronization
- **Homebrew** - For libomp, GCC, etc. (on Linux)
- **GCC 15** - C/C++ compiler
- **OpenMPI 5.0.8** - MPI implementation
- **UPC++ 2025.10.0** - PGAS library (for benchmarks)
- **Berkeley UPC 2023.9.0** - Unified Parallel C implementation (optional)
- **GASNet** - Network communication library (bundled with Berkeley UPC)

## Version History

- **2.0.1** (November 4, 2025) - Added Berkeley UPC support
  - Added berkeley_upc_manager.py module
  - Berkeley UPC installation and configuration
  - GASNet conduit support (MPI, UDP, SMP, IB)
  - Comprehensive Berkeley UPC tests
  - Updated documentation

- **2.0.0** (November 4, 2025) - Complete modularization
  - Separated monolithic cluster_setup.py into 8 manager modules
  - Added pdsh support for parallel execution
  - Created comprehensive test suite
  - Added standalone benchmark runner

- **1.0.0** - Original monolithic implementation

## Contributing

When adding new modules:

1. Follow the existing naming convention: `*_manager.py`
2. Create corresponding test file in `tests/test_*.py`
3. Add module to `cluster_modules/__init__.py`
4. Update this README
5. Document all public methods
6. Support pdsh for cluster-wide operations
7. Never hardcode passwords or IPs

## License

See repository LICENSE file.
