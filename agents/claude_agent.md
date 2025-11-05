# Claude Agent Instructions for ClusterSetupAndConfigs

## Project Identity & Context

**Project:** ClusterSetupAndConfigs
**Version:** 3.0.0 (Modular Architecture)
**Purpose:** Automated HPC cluster setup for Slurm/OpenMPI/PGAS systems
**Primary Language:** Python 3.14
**Package Manager:** uv (fast Python package manager)
**Author:** Olumuyiwa Oluwasanmi
**Last Major Refactor:** November 4, 2025

## Core Philosophy

This project underwent a **massive 84% code reduction** (2,951 lines → 474 lines) through complete modularization. The architecture prioritizes:

1. **Modular Design**: 12 specialized manager classes, each with single responsibility
2. **Multi-OS Support**: Works on Ubuntu, Debian, Red Hat, CentOS, Fedora, and WSL2
3. **Any-Node Execution**: Can run from master OR any worker node with automatic detection
4. **Passwordless Flow**: Single password entry configures entire cluster
5. **Template-Based Generation**: Jinja2 templates for configuration and benchmarks

## Project Evolution (Key Commits)

### Recent Major Changes (Nov 2025)
- **a5aa3cc**: Updated test results with Slurm job submission completion
- **bb775c1**: Added 647-line comprehensive Slurm job submission guide
- **b2d90ee**: MAJOR - Complete Slurm job submission system (2,378 lines)
  * SlurmJobManager class for MPI/OpenMP/UPC++/OpenSHMEM/Hybrid jobs
  * SlurmSetupHelper for Munge authentication and cluster setup
  * 5 Jinja2 job templates with automatic resource allocation
  * setup_slurm.py and test_slurm_jobs.py utilities
  * Reads cluster config, auto-detects 168 cores across 5 nodes
- **73cac25**: Fixed UPC++ 2025.10.0 API compatibility and OpenSHMEM linker
- **5f1bab3**: Added comprehensive AI agent documentation (v2.0.0 builder agent)
- **1ab2326**: Comprehensive test results for directory consolidation
- **1b6bad5**: Added cluster cleanup module to kill orphaned processes
- **99ae6fc**: Consolidated all directories under `cluster_build_sources`
- **858fcdb**: Separated configuration and benchmark templates
- **28c9dc9**: Completed modularization with PGASManager and passwordless sudo
- **2345f36**: Added HomebrewManager and streamlined architecture
- **31ddd26**: Major refactoring with Jinja2 templates and pdsh manager

### Breakthrough Features (Oct-Nov 2025)
- **b550fb5**: Added Berkeley UPC++, GASNet-EX, and OpenSHMEM with cluster distribution
- **05331ce**: Multi-hostfile creation, MPI prefix documentation, optimal distribution
- **81d0c66**: BREAKTHROUGH - OpenMPI working on WSL+Linux with correct flags
- **7a62092**: WSL mirrored networking mode as recommended MPI solution

### Foundation (Sep-Oct 2025)
- **f4ac5a9**: Auto worker setup, secure sudo handling, node detection
- **896911b**: Slurm 24.11+ compatibility fixes
- **86171ee**: Initial cluster setup with YAML config support

## Architecture Overview

### Directory Structure

```
ClusterSetupAndConfigs/
├── cluster_setup.py              # Main entry point (474 lines, down from 2,951!)
├── cluster_setup_ui.py           # Textual UI for interactive setup
├── cluster_config.yaml           # Example configuration
├── cluster_config_actual.yaml    # Active config (gitignored)
│
├── cluster_modules/              # Modular managers (NEW v3.0)
│   ├── __init__.py              # Exports all managers
│   ├── core.py                  # ClusterCore base class
│   │
│   ├── # Core Infrastructure
│   ├── homebrew_manager.py      # GCC 15.2.0, binutils 2.45, Python 3.14
│   ├── ssh_manager.py           # SSH keys, passwordless auth (uses ClusterCore)
│   ├── sudo_manager.py          # Passwordless sudo configuration
│   ├── network_manager.py       # Firewall, port configuration
│   ├── pdsh_manager.py          # Parallel distributed shell
│   │
│   ├── # Parallel Programming
│   ├── mpi_manager.py           # OpenMPI 5.0.8 installation
│   ├── openmp_manager.py        # OpenMP (libomp) installation
│   ├── slurm_manager.py         # Slurm workload manager installation
│   │
│   ├── # Slurm Job Submission (NEW Nov 5, 2025)
│   ├── slurm_job_manager.py     # Job generation & submission (563 lines)
│   ├── slurm_setup_helper.py    # Munge authentication setup (359 lines)
│   │
│   ├── # PGAS Libraries
│   ├── pgas_manager.py          # Unified PGAS installer (NEW v3.0)
│   ├── berkeley_upc_manager.py  # Berkeley UPC specific
│   ├── openshmem_manager.py     # OpenSHMEM specific
│   │
│   ├── # Testing & Benchmarking
│   ├── benchmark_manager.py     # Jinja2-based benchmark generation
│   ├── benchmark_runner.py      # Modular pdsh-based execution
│   ├── cluster_cleanup.py       # Kill orphaned processes
│   │
│   ├── # Configuration
│   ├── config_template_manager.py  # Template rendering & deployment
│   ├── mpi_network_config.py       # MPI network optimization
│   ├── multi_node_runner.py        # Multi-node execution utilities
│   │
│   └── templates/               # Jinja2 templates
│       ├── benchmarks/          # UPC++, MPI, OpenSHMEM, Berkeley UPC
│       ├── build/               # Makefiles, run scripts
│       ├── configs/             # MPI MCA, hostfiles, Slurm configs
│       └── slurm_jobs/          # Slurm job templates (NEW Nov 5)
│           ├── mpi_job.sh.j2
│           ├── openmp_job.sh.j2
│           ├── hybrid_job.sh.j2
│           ├── upcxx_job.sh.j2
│           └── openshmem_job.sh.j2
│
├── templates/                   # System configuration templates
│   ├── mpi/                     # MPI configuration (mca-params.conf, hostfiles)
│   ├── slurm/                   # Slurm configuration (slurm.conf)
│   └── ssh/                     # SSH configuration
│
├── docs/                        # Comprehensive documentation
│   ├── configuration/
│   │   ├── PGAS_CONFIGURATION.md
│   │   ├── TEMPLATE_SYSTEM.md
│   │   └── FIREWALL_SETUP.md
│   ├── troubleshooting/
│   │   ├── MPI_NETWORK_FIX.md
│   │   ├── MULTI_HOMED_NODE_FIX.md
│   │   └── MPI_BENCHMARK_DEBUGGING.md
│   └── benchmarks/              # Benchmark-specific documentation
│
├── scripts/                     # Shell utilities
│   ├── setup_cluster_network.sh
│   └── benchmarks/
│       ├── run_all_benchmarks.sh
│       └── mpirun_cluster.sh
│
└── CLAUDE.md                    # Primary AI agent instructions (23KB+)
```

### The 12 Modular Managers

#### 1. **ClusterCore** (core.py)
- Base class providing common functionality
- OS detection (Ubuntu/Red Hat/WSL)
- Package manager detection (apt-get/dnf/yum)
- Command execution (local, remote, sudo)
- Node identification and IP resolution

#### 2. **HomebrewManager** (homebrew_manager.py)
- Installs Homebrew if not present
- Installs GCC 15.2.0, binutils 2.45, Python 3.14
- Creates version-specific symlinks (gcc → gcc-15)
- Manages system PATH configuration
- Post-installation symlink verification

#### 3. **SSHManager** (ssh_manager.py)
- Generates SSH key pairs (RSA and Ed25519)
- Distributes keys between ALL nodes (full mesh)
- Configures passwordless SSH authentication
- Uses ClusterCore for command execution

#### 4. **SudoManager** (sudo_manager.py)
- Configures passwordless sudo (Step 0 - CRITICAL!)
- Creates sudoers.d configuration files
- Validates sudo access
- Single password entry for entire cluster setup

#### 5. **NetworkManager** (network_manager.py)
- Configures firewalld/ufw on all nodes
- Opens MPI ports (50000-50200)
- Handles multi-NIC node configuration
- Verifies firewall rules

#### 6. **PDSHManager** (pdsh_manager.py)
- Installs pdsh (parallel distributed shell)
- Configures WCOLL hostfile
- Provides cluster-wide parallel execution
- Fallback to sequential SSH if pdsh unavailable

#### 7. **MPIManager** (mpi_manager.py)
- Installs OpenMPI 5.0.8 via Homebrew
- Detects and removes MPICH (incompatible!)
- Creates MCA configuration (~/.openmpi/mca-params.conf)
- Generates 3 hostfiles: standard, optimal, max
- Distributes configs to all nodes
- Handles multi-NIC interface selection

#### 8. **OpenMPManager** (openmp_manager.py)
- Installs libomp (OpenMP runtime)
- Configures thread environment variables
- Enables hybrid MPI+OpenMP setups

#### 9. **SlurmManager** (slurm_manager.py)
- Installs Slurm workload manager
- Generates slurm.conf with actual hostnames
- Configures slurmctld (master) and slurmd (workers)
- Fixed for Slurm 24.11+ compatibility

#### 10. **PGASManager** (pgas_manager.py) - **NEW v3.0**
- **Unified PGAS library installer**
- Installs GASNet-EX 2024.5.0 (communication layer)
- Installs UPC++ 2024.3.0 (Berkeley PGAS for C++)
- Installs OpenSHMEM 1.5.2 (Sandia implementation)
- Creates symlinks: upcxx, upcxx-run, oshcc, oshrun
- Configures conduits: MPI, SMP, UDP
- Updates PATH and LD_LIBRARY_PATH

#### 11. **BenchmarkManager** (benchmark_manager.py)
- Generates benchmarks from Jinja2 templates
- Creates UPC++, MPI, OpenSHMEM, Berkeley UPC latency/bandwidth tests
- Generates Makefiles and run scripts
- Compiles with C++23 standard (-std=c++23 -O3)
- Distributes to all nodes via pdsh/rsync
- Executes cluster-wide benchmark runs

#### 12. **ClusterCleanup** (cluster_cleanup.py)
- Kills orphaned MPI processes (prterun, orted, mpirun)
- Cleans up stale lock files
- Runs automatically before each setup
- Prevents port conflicts and process zombies

#### 13. **SlurmJobManager** (slurm_job_manager.py) - **NEW Nov 5, 2025**
- Template-based Slurm job script generation using Jinja2
- Supports 5 parallel programming frameworks:
  * MPI (OpenMPI 5.0.8 with srun --mpi=pmix)
  * OpenMP (thread-level on single node)
  * Hybrid MPI+OpenMP (combined parallelism)
  * UPC++ (PGAS with GASNet-EX)
  * OpenSHMEM (symmetric memory)
- Automatic resource allocation from cluster_config_actual.yaml
- Job lifecycle: submit, monitor, cancel, retrieve output
- Detects 168 cores across 5 nodes
- Generated jobs: `~/cluster_build_sources/slurm_jobs/`
- Results: `~/cluster_build_sources/slurm_results/`

#### 14. **SlurmSetupHelper** (slurm_setup_helper.py) - **NEW Nov 5, 2025**
- Munge authentication key generation (1024-byte random)
- Munge key distribution to all worker nodes
- Multi-OS support (Ubuntu, Debian, Red Hat, CentOS, Fedora)
- Munge service configuration and startup
- Slurm partition configuration
- Service restart orchestration
- Cluster verification (munge, sinfo tests)

## Setup Flow (9 Steps)

When `cluster_setup.py` runs, it executes in this order:

### Step 0: Passwordless Sudo (CRITICAL - First!)
```python
self.sudo_mgr.configure_passwordless_sudo_local()
```
- **Why first?** All subsequent steps need sudo access
- User enters password ONCE
- Creates `/etc/sudoers.d/cluster-setup-nopasswd`
- No more password prompts for entire setup

### Step 1: SSH Keys and Passwordless SSH
```python
self.ssh_mgr.setup_ssh()
self.ssh_mgr.configure_passwordless_ssh()
```
- Generates RSA and Ed25519 keys
- Distributes to ALL nodes (full mesh connectivity)
- Any node can SSH to any other node

### Step 2: Homebrew, GCC, and Binutils
```python
self.homebrew_mgr.install_and_configure_local()
```
- Installs Homebrew at `/home/linuxbrew/.linuxbrew`
- Installs GCC 15.2.0, binutils 2.45, Python 3.14
- Creates symlinks: gcc → gcc-15, g++ → g++-15
- Updates PATH in ~/.bashrc

### Step 3: System Configuration
```python
self._configure_hosts_file()
```
- Appends cluster nodes to `/etc/hosts`
- Format: `192.168.1.10 master master-node`
- Enables hostname-based communication

### Step 4: Parallel Programming Infrastructure
```python
self.slurm_mgr.install_slurm_local()
self.pdsh_mgr.install_and_configure_cluster()
```
- Installs Slurm with systemd integration
- Installs pdsh for parallel execution
- Configures WCOLL hostfile

### Step 5: MPI and Parallel Libraries
```python
self._install_openmpi()  # Legacy method, to be migrated to MPIManager
self.openmp_mgr.install_libomp_local()
```
- Removes MPICH if found (incompatible!)
- Installs OpenMPI 5.0.8
- Installs OpenMP (libomp)
- Creates MCA params and hostfiles

### Step 6: PGAS Libraries
```python
self.pgas_mgr.install_pgas_libraries_local()
```
- Downloads and compiles GASNet-EX from source
- Downloads and compiles UPC++ from source
- Downloads and compiles OpenSHMEM from source
- All installed to `/home/linuxbrew/.linuxbrew/`
- Build artifacts in `~/cluster_build_sources/`

### Step 7: Network Configuration
```python
self.network_mgr.configure_firewall_local()
```
- Opens TCP ports 50000-50200 (OpenMPI)
- Configures firewalld (Red Hat) or ufw (Ubuntu)
- Handles multi-NIC nodes

### Step 8: Benchmark Generation
```python
self._generate_benchmarks()
```
- Creates `~/cluster_build_sources/benchmarks/`
- Generates 7 benchmarks from Jinja2 templates:
  - upcxx_latency.cpp
  - upcxx_bandwidth.cpp
  - mpi_latency.cpp
  - openshmem_latency.cpp
  - berkeley_upc_latency.upc
  - openmp_parallel.cpp
  - hybrid_mpi_openmp.cpp
- Creates Makefile and run_benchmarks.sh

### Step 9: Final Verification
```python
self._post_installation_fixes()
self._verify_installation()
```
- Re-creates GCC symlinks (in case overwritten)
- Verifies PATH for critical tools
- Runs version checks: gcc, mpicc, sinfo

## Critical Configuration Files

### 1. cluster_config.yaml
```yaml
master:
  ip: 192.168.1.10
  os: ubuntu wsl2
  name: master-node

workers:
  - ip: 192.168.1.11
    os: ubuntu
    name: worker1
  - ip: 192.168.1.12
    os: redhat
    name: worker2

username: muyiwa  # optional, defaults to $USER
```

**Both formats supported:**
- Simple: `master: 192.168.1.10` (IP only)
- Extended: `master: {ip: 192.168.1.10, os: ubuntu, name: master-node}`

### 2. ~/.openmpi/mca-params.conf
```bash
# OpenMPI MCA (Modular Component Architecture) configuration
btl_tcp_port_min_v4 = 50000
btl_tcp_port_max_v4 = 50200
oob_tcp_port_range = 50100-50200
orte_prefix = /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8

# For multi-NIC nodes ONLY (detected automatically):
oob_tcp_if_include = ens1f0  # Primary interface
btl_tcp_if_include = ens1f0
```

**Critical:** All nodes must have identical MCA configuration for MPI to work!

### 3. ~/.openmpi/hostfile_optimal (Recommended)
```
192.168.1.10 slots=1
192.168.1.11 slots=1
192.168.1.12 slots=1
192.168.1.13 slots=1
```
**Why slots=1?** Best for hybrid MPI+OpenMP (1 MPI process per node, max OpenMP threads)

### 4. ~/cluster_build_sources/benchmarks/Makefile
Auto-generated with C++23 standard:
```makefile
CXX = /home/linuxbrew/.linuxbrew/bin/g++
CXXFLAGS = -std=c++23 -O3 -Wall -fopenmp
UPCXX = /home/linuxbrew/.linuxbrew/bin/upcxx
MPICC = mpicc
```

## Command-Line Interface

### Main Script Usage
```bash
# Basic setup (local node only)
uv run python cluster_setup.py --config cluster_config.yaml

# Full cluster setup (all nodes automatically)
uv run python cluster_setup.py --config cluster_config.yaml --password

# With benchmark execution
uv run python cluster_setup.py --config cluster_config.yaml --password --run-benchmarks

# Fresh install (removes all existing configs/keys)
uv run python cluster_setup.py --config cluster_config.yaml --password --clean-install

# Non-interactive mode (for scripts)
uv run python cluster_setup.py --config cluster_config.yaml --password --non-interactive
```

### Cluster Cleanup (Run Before Setup)
```bash
# Cleanup is now AUTOMATIC before every setup
# But can be run manually:
uv run python cluster_modules/cluster_cleanup.py --config cluster_config_actual.yaml
```

### Benchmark Runner (Modular Approach)
```bash
# List available benchmarks
uv run python cluster_modules/benchmark_runner.py list

# Sync binaries to all nodes
uv run python cluster_modules/benchmark_runner.py sync

# Run specific benchmark
uv run python cluster_modules/benchmark_runner.py run mpi_latency --np 4 --timeout 60

# Run all benchmarks
uv run python cluster_modules/benchmark_runner.py run all --np 4

# Clean up processes
uv run python cluster_modules/benchmark_runner.py cleanup
```

### Configuration Management
```bash
# Show cluster summary
uv run python cluster_modules/config_template_manager.py summary

# Generate and deploy MPI configuration
uv run python cluster_modules/config_template_manager.py deploy mpi-mca

# Configure firewalls on all nodes
uv run python cluster_modules/config_template_manager.py firewall configure

# Verify firewall rules
uv run python cluster_modules/config_template_manager.py firewall verify
```

## Critical MPI Knowledge

### The MPICH vs OpenMPI Incompatibility Problem
**NEVER mix MPICH and OpenMPI on the same cluster!**

Detection and fix (automatic in setup):
```python
# Check for MPICH
mpich_check = subprocess.run(['brew', 'list', 'mpich'], check=False)
if mpich_check.returncode == 0:
    print("⚠️  Uninstalling MPICH (incompatible with OpenMPI)...")
    subprocess.run(['brew', 'uninstall', 'mpich'])
```

**Why?** MPICH and OpenMPI use completely different wire protocols. Mixing them causes:
```
PRTE has lost communication with remote daemon
[prterun-hostname-12345@0,2] on node 192.168.1.X
```

### Multi-NIC Node Configuration
If a node has multiple network interfaces on the same subnet:
```bash
# Node has:
# ens1f0: 192.168.1.136 (10 Gbps) ← Use this one!
# ens1f1: 192.168.1.138 (1 Gbps)

# MCA config must specify:
oob_tcp_if_include = ens1f0
btl_tcp_if_include = ens1f0
```

**Auto-detection in network_manager.py:**
```python
def detect_primary_interface(self):
    # Checks ethtool for speed, selects fastest interface
    # Bias towards highest throughput (10 Gbps > 1 Gbps)
```

### The --map-by node Flag (CRITICAL!)
OpenMPI 5.x changed default mapping to sequential. Always use:
```bash
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node \  # ← CRITICAL: Round-robin across nodes
       -np 16 \
       --hostfile ~/.openmpi/hostfile_optimal \
       ./program
```

**Without --map-by node:** All processes run on first node
**With --map-by node:** Processes distributed evenly across all nodes

### The --prefix Flag (Also Critical!)
Always specify OpenMPI installation path:
```bash
--prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8
```

**Why?**
1. Ensures consistent MPI version across nodes
2. Prevents PATH issues
3. Avoids mixing system MPI with Homebrew MPI
4. Required for heterogeneous clusters (Ubuntu + Red Hat + WSL)

## WSL-Specific Considerations

### Mirrored Mode Networking (CRITICAL!)
WSL MUST use mirrored networking mode for cluster participation.

**Windows config:** `C:\Users\<Username>\.wslconfig`
```ini
[wsl2]
networkingMode = mirrored
```

**After creating this file:**
```powershell
wsl --shutdown
```

**Why mirrored mode is required:**
- **Default NAT mode:** WSL gets internal IP (172.x.x.x) unreachable from cluster
- **Mirrored mode:** WSL gets same IP as Windows host on physical network
- **Without mirrored mode:** Other nodes cannot route MPI traffic to/from WSL

### Windows Firewall Configuration
After enabling mirrored mode, run (PowerShell as Administrator):
```powershell
cd Z:\PycharmProjects\ClusterSetupAndConfigs
.\configure_wsl_firewall.ps1
```

This opens TCP ports 50000-50200 for OpenMPI communication.

### WSL Symlink Issue (uv Virtual Environments)
**CRITICAL:** Windows filesystem mounts (`/mnt/c`, `/mnt/z`) **DO NOT support symlinks**.

**Problem:** `uv` tries to create symlinked venv in project directory:
```
error: failed to symlink file from ... to ... : Operation not permitted (os error 1)
```

**Solution:** Always set venv location to Linux home:
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
```

**Add to ~/.bashrc for persistence:**
```bash
echo 'export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup' >> ~/.bashrc
```

## Common Troubleshooting Scenarios

### 1. "Permission denied" errors during setup
**Cause:** Passwordless sudo not configured
**Fix:**
```bash
# Run Step 0 manually:
echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/cluster-setup-nopasswd
sudo chmod 0440 /etc/sudoers.d/cluster-setup-nopasswd
```

### 2. MPI processes not distributing across nodes
**Cause:** Missing `--map-by node` flag
**Fix:**
```bash
# Always use:
mpirun --map-by node -np 16 --hostfile ~/.openmpi/hostfile_optimal ./program
```

### 3. "PRTE has lost communication with remote daemon"
**Causes:**
1. MPICH/OpenMPI mixing → Run cleanup, reinstall OpenMPI
2. Multi-NIC without interface specification → Add `oob_tcp_if_include`
3. Firewall blocking ports → Run firewall configuration
4. MCA config not distributed → Re-run setup with `--password`

**Debug:**
```bash
# Check MCA config on all nodes:
pdsh -w all_nodes "cat ~/.openmpi/mca-params.conf"

# Check for MPICH:
pdsh -w all_nodes "which mpicc"  # Should be /home/linuxbrew/.linuxbrew/bin/mpicc

# Check firewall:
uv run python cluster_modules/config_template_manager.py firewall verify
```

### 4. Benchmarks fail to compile
**Cause:** GCC symlinks missing or wrong version
**Fix:**
```bash
# Check GCC version:
gcc --version  # Should show gcc-15

# Re-create symlinks:
uv run python -c "from cluster_modules import HomebrewManager; \
  mgr = HomebrewManager('muyiwa', None, '192.168.1.10', []); \
  mgr.create_gcc_symlinks()"
```

### 5. UPC++/OpenSHMEM not found
**Cause:** PATH not updated or PGAS installation incomplete
**Fix:**
```bash
# Check PATH:
echo $PATH | grep linuxbrew

# Check installations:
ls -l /home/linuxbrew/.linuxbrew/{upcxx,openshmem,gasnet}

# Re-run PGAS installation:
# (from cluster_setup.py, Step 6 will re-install if missing)
```

### 6. Cluster nodes cannot SSH to each other
**Cause:** SSH keys not distributed or incorrect permissions
**Fix:**
```bash
# Check key permissions:
ls -l ~/.ssh/id_rsa*  # Should be 600 (private) and 644 (public)

# Re-run SSH setup:
uv run python -c "from cluster_modules import SSHManager, ClusterCore; \
  core = ClusterCore('192.168.1.10', ['192.168.1.11', '192.168.1.12'], 'muyiwa', 'password'); \
  mgr = SSHManager(core); \
  mgr.configure_passwordless_ssh()"
```

## Testing and Validation

### Unit Tests (118 tests total)
```bash
# Run all tests:
uv run pytest

# Test specific module:
uv run pytest tests/test_benchmark_manager.py

# Current status: 102 passing, 16 expected failures (uninstalled components)
```

### Manual Cluster Verification
```bash
# 1. Check Slurm:
sinfo
squeue

# 2. Test SSH mesh:
pdsh -w all_nodes "hostname"

# 3. Test OpenMPI:
mpirun --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal hostname

# 4. Test UPC++:
/home/linuxbrew/.linuxbrew/bin/upcxx-run -n 4 ./bin/upcxx_latency

# 5. Test OpenSHMEM:
oshrun -n 4 ./bin/openshmem_latency

# 6. Run benchmarks:
cd ~/cluster_build_sources/benchmarks
make
./run_benchmarks.sh
```

## Best Practices for AI Agents

### When Modifying Code:
1. **Always read CLAUDE.md first** - Contains critical WSL/uv/Python 3.14 info
2. **Check cluster_modules/README.md** - Manager architecture documentation
3. **Run tests after changes:** `uv run pytest`
4. **Update version in __init__.py** if architecture changes
5. **Document in commit message** which manager(s) were modified

### When Adding New Features:
1. **Create a new manager** in `cluster_modules/` if it's a distinct responsibility
2. **Use ClusterCore** for command execution if new manager needs remote operations
3. **Add to __init__.py** exports: `from .new_manager import NewManager`
4. **Create Jinja2 template** in `cluster_modules/templates/` if generating configs
5. **Write tests** in `tests/test_new_manager.py`

### When Debugging Setup Issues:
1. **Check Step 0 first** - Passwordless sudo is prerequisite for everything
2. **Verify OS detection** - Run `python -c "from cluster_modules.core import ClusterCore; print(ClusterCore('x',[],'y').os_type)"`
3. **Check MPI version consistency** - `pdsh -w all_nodes "mpicc --version"`
4. **Verify firewall** - `uv run python cluster_modules/config_template_manager.py firewall verify`
5. **Check logs** - Setup prints detailed debug output to stdout

### When User Reports MPI Issues:
1. **Check for MPICH** - `brew list mpich` should return error
2. **Verify --map-by node** - User must include this flag
3. **Check MCA config** - `cat ~/.openmpi/mca-params.conf`
4. **Check multi-NIC** - `ip addr | grep 'inet 192.168.1'` - if multiple IPs, need `oob_tcp_if_include`
5. **Run cluster cleanup** - `uv run python cluster_modules/cluster_cleanup.py`

## Important File Paths

### Homebrew Paths
- **Homebrew root:** `/home/linuxbrew/.linuxbrew/`
- **GCC:** `/home/linuxbrew/.linuxbrew/bin/gcc` → `gcc-15`
- **OpenMPI:** `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8/`
- **Python:** `/home/linuxbrew/.linuxbrew/bin/python3.14`

### User Directories
- **Build sources:** `~/cluster_build_sources/` (GASNet, UPC++, OpenSHMEM sources)
- **Benchmarks:** `~/cluster_build_sources/benchmarks/`
- **SSH config:** `~/.ssh/` (id_rsa, id_ed25519, authorized_keys)
- **OpenMPI config:** `~/.openmpi/` (mca-params.conf, hostfiles)
- **Slurm config:** `/etc/slurm/` (slurm.conf, cgroup.conf)

### System Directories
- **Sudoers:** `/etc/sudoers.d/cluster-setup-nopasswd`
- **Hosts:** `/etc/hosts` (cluster node entries appended)
- **Firewall:** `/etc/firewalld/` or `/etc/ufw/`

## Environment Variables

### Required for uv (WSL)
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
```

### Set by Homebrew
```bash
export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
export MANPATH="/home/linuxbrew/.linuxbrew/share/man:$MANPATH"
export INFOPATH="/home/linuxbrew/.linuxbrew/share/info:$INFOPATH"
```

### Set by PGAS Installer
```bash
export PATH="/home/linuxbrew/.linuxbrew/upcxx/bin:$PATH"
export PATH="/home/linuxbrew/.linuxbrew/openshmem/bin:$PATH"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/gasnet/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/upcxx/lib:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/openshmem/lib:$LD_LIBRARY_PATH"
```

### OpenMP Thread Configuration (Optional)
```bash
export OMP_NUM_THREADS=16  # Or per-node value from config
export OMP_PROC_BIND=close
export OMP_PLACES=cores
```

## Quick Command Reference

### Daily Operations
```bash
# Setup cluster from scratch:
uv run python cluster_setup.py --config cluster_config_actual.yaml --password

# Run benchmarks:
uv run python cluster_modules/benchmark_runner.py sync
uv run python cluster_modules/benchmark_runner.py run all --np 4

# Check cluster health:
sinfo
pdsh -w all_nodes "hostname && uptime"

# Clean up orphaned processes:
uv run python cluster_modules/cluster_cleanup.py
```

### Development Workflow
```bash
# Run tests:
uv run pytest

# Add dependency:
uv add package-name

# Update dependencies:
uv sync

# Check code style:
uv run pylint cluster_modules/*.py

# Run specific manager locally:
uv run python -c "from cluster_modules import HomebrewManager; \
  mgr = HomebrewManager('user', None, '192.168.1.10', []); \
  mgr.create_gcc_symlinks()"
```

## Key Design Patterns

### 1. Manager Pattern
Each manager is self-contained with:
- Constructor accepting cluster config
- Install/configure methods for local node
- Distribute/deploy methods for cluster-wide operations
- Verification methods

Example:
```python
class NewManager:
    def __init__(self, username, password, master_ip, worker_ips):
        self.username = username
        # ...

    def install_local(self):
        """Install on current node"""
        pass

    def distribute_to_cluster(self):
        """Deploy to all other nodes"""
        pass

    def verify(self):
        """Verify installation"""
        pass
```

### 2. ClusterCore Inheritance
Managers needing remote execution use ClusterCore:
```python
from .core import ClusterCore

class PGASManager:
    def __init__(self, core: ClusterCore):
        self.core = core

    def _run_on_all_nodes(self, command):
        for ip in self.core.all_ips:
            self.core.run_remote_command(ip, command)
```

### 3. Template Rendering
Jinja2 for configuration generation:
```python
from jinja2 import Environment, FileSystemLoader

template_dir = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

template = jinja_env.get_template("benchmarks/upcxx/upcxx_latency.cpp.j2")
code = template.render(iterations=1000, warmup_iterations=100)
```

### 4. Passwordless Sudo Pattern
Step 0 - Configure once, use everywhere:
```python
# Step 0 (first thing in run_full_setup):
if self.password:
    self.sudo_mgr.configure_passwordless_sudo_local()

# All subsequent steps can use sudo without password:
subprocess.run("sudo apt-get install ...", shell=True)
```

## Dependencies (pyproject.toml)

```toml
[project]
name = "cluster-setup-configs"
version = "3.0.0"
requires-python = ">=3.14"
dependencies = [
    "pyyaml>=6.0",      # YAML config parsing
    "textual>=0.47.0",  # Terminal UI
    "jinja2>=3.1.2",    # Template rendering
]

[tool.uv]
dev-dependencies = [
    "pytest>=7.4.0",
    "pylint>=2.17.0",
]
```

## Documentation Hierarchy

1. **CLAUDE.md** (23KB) - Primary instructions, WSL setup, Python 3.14, uv
2. **README.md** (76KB) - User-facing documentation, quick start, features
3. **DEPLOYMENT_GUIDE.md** - Step-by-step deployment for production
4. **USAGE_EXAMPLES.md** - Example commands and workflows
5. **QUICK_REFERENCE.md** - Command cheat sheet
6. **cluster_modules/REFACTORING_DOCUMENTATION.md** - Modularization details
7. **docs/** - Specialized topics (PGAS, firewalls, troubleshooting)

## When to Read Which Doc:
- **User asks about setup:** DEPLOYMENT_GUIDE.md
- **User asks about Python/uv/WSL:** CLAUDE.md
- **User asks about MPI issues:** docs/troubleshooting/MPI_NETWORK_FIX.md
- **User asks about benchmarks:** QUICK_REFERENCE.md + benchmark_runner.py
- **User asks about architecture:** cluster_modules/REFACTORING_DOCUMENTATION.md
- **You need to modify code:** This file (claude_agent.md) + CLAUDE.md

## Final Notes for AI Agents

1. **This is a living project** - User actively develops and modifies it daily
2. **Test after changes** - 118 tests should pass (except 16 expected failures)
3. **Multi-OS is real** - Code must work on Ubuntu AND Red Hat
4. **WSL is first-class** - Many design decisions are WSL-specific (symlinks, mirrored networking)
5. **MPI is fragile** - Small config errors cause hard-to-debug communication failures
6. **PGAS is cutting-edge** - UPC++, OpenSHMEM are research-grade tools
7. **Modularization is sacred** - Don't revert to monolithic design
8. **Python 3.14 is required** - Don't suggest downgrades
9. **uv is mandatory** - Don't suggest pip/venv unless uv fails
10. **Read git history** - Commit messages explain "why" behind each change

---

**Last Updated:** November 5, 2025
**Latest Feature:** Comprehensive Slurm job submission system (commits b2d90ee, bb775c1, a5aa3cc)
**For Latest Updates:** Check git log and CLAUDE.md
**Questions?** Reference docs/ folder or ask user for clarification
