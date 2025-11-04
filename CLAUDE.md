# Claude AI Agent Instructions for ClusterSetupAndConfigs

## Project Overview

This is a Python 3.14 project using **uv** as the package manager. The project automates Slurm/OpenMPI cluster setup across multiple nodes and supports:
- **Multi-OS**: Ubuntu/Debian (apt-get) and Red Hat/CentOS/Fedora (dnf)
- **Run from Any Node**: Can run from master or any worker node - automatic detection
- **WSL Support**: Works on WSL (Windows Subsystem for Linux) with proper configuration
  - **CRITICAL**: WSL requires mirrored mode networking (`networkingMode = mirrored` in `.wslconfig`)
  - Without mirrored mode, WSL uses NAT with internal IP that's not accessible from other cluster nodes
  - See "WSL Configuration Requirements" section below for detailed setup

## Critical Setup Information

### Python Version
- **Required**: Python 3.14 (installed via Homebrew)
- **Location**: `/home/linuxbrew/.linuxbrew/bin/python3.14`
- **Check**: `python3.14 --version` or `/home/linuxbrew/.linuxbrew/bin/python3.14 --version`

### Package Manager: uv

**uv** is a fast Python package installer and resolver, similar to pip but much faster.

#### Installation
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### THE CRITICAL WSL PROBLEM

⚠️ **MOST IMPORTANT**: On WSL, Windows filesystem mounts (`/mnt/z`, `/mnt/c`, etc.) **DO NOT support symlinks**. This causes `uv` and `venv` to fail with:

```
error: failed to symlink file from ... to ... : Operation not permitted (os error 1)
```

### THE SOLUTION

**Always** set the virtual environment location to the Linux home directory before running any uv commands:

```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
```

This environment variable tells uv to create the virtual environment in `~/.venv/cluster-setup` (which is on the Linux filesystem) instead of `./.venv` (which would be on the Windows filesystem).

## Standard Workflow for Development

### Initial Setup
```bash
```bash
# First ensure Python 3.14 is available
uv python install 3.14
# OR if you want to use the system Python
uv python pin /home/linuxbrew/.linuxbrew/bin/python3.14
```

### Running Scripts
```bash
# Set environment variable
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Run with uv
uv run python cluster_setup.py --help
uv run python cluster_setup_ui.py
```

### Adding Dependencies
```bash
# Set environment variable first
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Sync after manual pyproject.toml edits
uv sync
```

### Running Tests
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run pytest
```

## Project Dependencies

Current dependencies in `pyproject.toml`:
- **PyYAML>=6.0**: For YAML configuration file parsing
- **textual>=0.47.0**: For terminal UI

## Common Commands You'll Need

### Check Python Version
```bash
**Check**:
```bash
python3.14 --version
# OR
/home/linuxbrew/.linuxbrew/bin/python3.14 --version
```
```

### List Available Python Versions (uv)
```bash
uv python list
```

### Check Current Environment
```bash
echo $UV_PROJECT_ENVIRONMENT
# Should output: /home/ubuntu/.venv/cluster-setup
```

### List Installed Packages
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv pip list
```

### Install Specific Python Version (uv)
```bash
uv python install 3.13
```

## Alternative: Using venv Directly

If uv continues to have issues, use Python's built-in venv:

```bash
```bash
# Create virtual environment in home directory (not in project directory!)
python3.14 -m venv --copies ~/.venv/cluster-setup

# Activate
source ~/.venv/cluster-setup/bin/activate

# Install dependencies
pip install PyYAML textual

# Run scripts
python cluster_setup.py --help
python cluster_setup_ui.py
```

## WSL Configuration Requirements

### Mirrored Mode Networking (CRITICAL for Cluster Operation)

**Required for cluster to function**: Create or edit `.wslconfig` in Windows home directory (`C:\Users\<YourUsername>\.wslconfig`):

```ini
[wsl2]
networkingMode = mirrored
```

After creating/editing this file, restart WSL:
```powershell
wsl --shutdown
```

**Why this is required**:
- Default NAT mode: WSL gets internal IP (172.x.x.x) not accessible from other cluster nodes
- Mirrored mode: WSL gets the same IP as Windows host on physical network
- Without mirrored mode: Other nodes cannot route MPI traffic to/from WSL node
- This must be configured before running cluster setup

### Windows Firewall Configuration

After enabling mirrored mode, configure firewall rules (run in PowerShell as Administrator):
```powershell
cd Z:\PycharmProjects\ClusterSetupAndConfigs
.\configure_wsl_firewall.ps1
```

## Troubleshooting Guide

### Issue: "Operation not permitted" when creating venv
**Cause**: Trying to create symlinks on Windows filesystem  
**Solution**: Always use `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup`

### Issue: Cluster nodes cannot connect to WSL node
**Cause**: WSL using default NAT mode instead of mirrored mode  
**Solution**: 
1. Edit `C:\Users\<YourUsername>\.wslconfig` to add `networkingMode = mirrored`
2. Run `wsl --shutdown` to restart WSL
3. Run firewall configuration script in PowerShell as Administrator

### Issue: "python3.14: command not found"
**Cause**: Homebrew not in PATH  
**Solution**: 
```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
# or use full path
```

### Issue: "Package not found" after adding to pyproject.toml
**Cause**: Need to sync dependencies  
**Solution**:
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv sync
```

### Issue: UV using wrong Python version
**Solution**:
```bash
uv python pin /home/linuxbrew/.linuxbrew/bin/python3.14
```

### Issue: Import errors when running scripts
**Cause**: Dependencies not installed or wrong environment  
**Solution**:
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv sync
uv run python script.py
```

## Recent Improvements (2025)

### Run from Any Node (Latest - Jan 2025)
The script can now run from ANY node (master or worker):
- **Automatic Node Detection**: Uses `ip addr` to check all network interfaces
- **Smart Setup**: If run from worker, sets up master AND all other workers
- **Excludes Current Node**: Never tries to remotely setup the node it's running on
- **Debug Output**: Shows which node detected and which nodes will be setup

### Multi-OS Support (Latest - Jan 2025)
Added full support for Red Hat-based distributions:
- **OS Detection**: Reads `/etc/os-release` to identify Ubuntu vs Red Hat
- **Package Manager Selection**: Automatically uses `apt-get` or `dnf`
- **Package Mapping**: Different package names for Ubuntu vs Red Hat
  - SSH: `openssh-client` vs `openssh-clients`
  - Slurm: `slurm-wlm` vs `slurm`
- **Fallback Detection**: Uses command existence if `/etc/os-release` unavailable

### Node Detection System (Oct 2025)
The script automatically detects which node it's running on:
- Checks all local network interfaces using `ip addr` command
- Compares found IPs with master_ip and worker_ips from config file
- Provides debug output showing hostname, detected IPs, and node role
- Creates list of "other nodes" to setup remotely

### Secure Sudo Password Handling
Improved security for sudo operations:
- Uses `subprocess.Popen` with stdin piping instead of command-line exposure
- Password never appears in process list or error messages
- Supports both local and remote sudo execution via wrapper scripts

### Slurm Configuration Fixes (Latest)
Fixed issues with Slurm 24.11+ compatibility:
- **Removed deprecated CgroupAutomount**: No longer included in cgroup.conf (causes startup failures in 24.11+)
- **Automatic hostname detection**: Uses actual system hostname instead of hardcoded "master" in slurm.conf
- **Proper directory ownership**: Sets Slurm directories to `slurm:slurm` user/group (required by daemons)
- **Systemctl integration**: Uses `systemctl restart` instead of calling daemons directly
- **Service enablement**: Ensures services start automatically on boot

### Troubleshooting Node Detection
If script shows "Current node is: WORKER" when you expected MASTER:
```bash
# Check what IPs the script detects
ip addr show | grep "inet "

# Script will output debug info:
# DEBUG: hostname='...', local_ip='...', master_ip='...'
# DEBUG: Found IPs on interfaces: [...]

# Ensure master IP from config matches one of the detected IPs
```

## Best Practices for AI Agents

1. **Always check** if `UV_PROJECT_ENVIRONMENT` is set before running uv commands
2. **Always use** `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup` in commands
3. **Never** try to create `.venv` in the project directory on WSL with Windows mounts
4. **Use** `uv run python script.py` instead of just `python script.py`
5. **Check** Python version with `python3.14 --version` before assuming it's available
6. **Suggest** adding the export to `~/.bashrc` for persistence
7. **Fall back** to standard venv if uv continues to have issues
8. **Always** run `uv sync` after modifying `pyproject.toml`
9. **Remember** script can run from ANY node (master or worker) - automatic detection
10. **Multi-OS**: Script automatically detects Ubuntu vs Red Hat and uses apt-get or dnf
11. **Check** DEPLOYMENT_GUIDE.md for comprehensive deployment instructions

## Project Structure

```
ClusterSetupAndConfigs/
├── cluster_setup.py          # Main CLI script
├── cluster_setup_ui.py       # Textual UI for setup
├── cluster_config.yaml        # Example config
├── cluster_config_actual.yaml # Actual config (not in git)
├── pyproject.toml            # Project metadata and dependencies
├── uv.lock                   # Lock file for exact dependency versions
├── README.md                 # User documentation
├── CLAUDE.md                 # This file (AI agent instructions)
└── test_cluster_setup.py     # Tests
```

## OpenMPI Installation and Binary Locations

**Homebrew Installation Path**: `/home/linuxbrew/.linuxbrew/`

**OpenMPI Version**: 5.0.8 (installed via Homebrew)

**Key Binary Locations**:
- **mpirun/mpiexec**: `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8/bin/mpirun`
- **Compiler Wrappers**: `mpicc`, `mpic++`, `mpif90`
- **Libraries**: `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8/lib/`
- **Prefix**: `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8`

**Critical Usage Pattern**:
Always use the `--prefix` flag to ensure all nodes use the same OpenMPI installation:
```bash
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal ./program
```

**Why --prefix is Essential**:
1. Ensures consistent MPI library versions across nodes
2. Prevents MPICH/OpenMPI conflicts on heterogeneous systems
3. Avoids "orted" daemon version mismatches
4. Required when multiple MPI implementations exist
5. Critical for Red Hat + Ubuntu + WSL mixed clusters

## Configuration Format

The project uses YAML configuration files. Two formats are supported:

**Simple Format (backward compatible):**
```yaml
master: 192.168.1.10
workers:
  - 192.168.1.11
  - 192.168.1.12
username: myuser  # optional
```

**Extended Format (with OS and hostname - Recommended for Multi-OS):**
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
    os: redhat  # Red Hat worker - script will use dnf
    name: worker2-redhat
username: myuser  # optional
```

**Simple Format (still supported):**
```yaml
master: 192.168.1.10
  os: ubuntu wsl2
  name: master-node  # optional
workers:
  - ip: 192.168.1.11
    os: ubuntu
    name: worker1  # optional
  - ip: 192.168.1.12
    os: ubuntu
    name: worker2  # optional
username: myuser  # optional
```

Both formats work identically. The script automatically detects and extracts IP addresses from either format. The `os` and `name` fields are optional and used for documentation.

**Important**: The script MUST be run from the node with IP matching the master IP for automatic worker setup to occur.

## Key Scripts

### cluster_setup.py
Main command-line tool for cluster setup. Usage:
```bash
# Interactive mode (prompts for confirmation)
uv run python cluster_setup.py --config cluster_config.yaml --password

# Non-interactive mode (auto-confirms, used internally for worker setup)
uv run python cluster_setup.py --config cluster_config.yaml --password --non-interactive
```

Command-line flags:
- `--config, -c`: YAML configuration file (required)
- `--password, -p`: Prompt for password and enable automatic worker setup
- `--non-interactive`: Skip confirmation prompts (automatically used on workers)

### cluster_setup_ui.py
Interactive terminal UI. Usage:
```bash
uv run python cluster_setup_ui.py
```

## When Making Code Changes

1. Verify types are correct (project uses type hints)
2. Run `uv sync` after dependency changes
3. Test with `uv run python script.py`
4. Update this documentation if adding new dependencies or changing setup process

## MPI Cluster Critical Fixes (Nov 2025)

### Problem 1: MPICH vs OpenMPI Incompatibility

**Root Cause**: Homebrew may install different MPI implementations on different systems. MPICH and OpenMPI use completely different protocols and cannot communicate.

**Symptoms**:
```
PRTE has lost communication with remote daemon
[prterun-hostname-12345@0,2] on node 192.168.1.X
```

**Detection**:
```bash
# Check MPI implementation on each node
ls -la /home/linuxbrew/.linuxbrew/bin/mpirun
# Should show: ../Cellar/open-mpi/5.0.8/bin/mpirun (not mpich!)
```

**Solution Implemented**:
```python
# In install_openmpi() method:
mpich_check = self.run_command(f"{brew_cmd} list mpich 2>/dev/null", check=False)
if mpich_check.returncode == 0:
    print("⚠️  MPICH detected! Uninstalling (incompatible with OpenMPI)...")
    self.run_command(f"{brew_cmd} uninstall mpich", check=False)
    
# Ensure OpenMPI is linked
self.run_command(f"{brew_cmd} link open-mpi", check=False)
```

**Key Insight**: All nodes MUST use the same MPI implementation (OpenMPI 5.0.8 in our case).

### Problem 2: Incomplete SSH Key Distribution

**Root Cause**: Original implementation only distributed SSH keys from the running node to other nodes. MPI requires full mesh connectivity - ANY node must be able to SSH to ANY other node.

**Why It Matters**: 
- MPI head node needs to SSH to workers to launch PRTE daemons
- Workers may need to SSH back for certain operations
- Allows running MPI jobs from any node as head

**Solution Implemented**:
```python
def distribute_ssh_keys_between_all_nodes(self):
    """
    Distributes SSH keys between ALL nodes (master + workers).
    Creates a full mesh where any node can SSH to any other node.
    """
    all_nodes = [self.master_ip] + self.worker_ips
    node_public_keys = {}
    
    # Collect public key from each node
    for node_ip in all_nodes:
        cmd = f'sshpass -f {temp_pass_path} ssh ... "cat ~/.ssh/id_rsa.pub"'
        node_public_keys[node_ip] = pub_key
    
    # Distribute each node's key to all OTHER nodes
    for source_node, pub_key in node_public_keys.items():
        for target_node in all_nodes:
            if source_node != target_node:
                # Add to authorized_keys and deduplicate
                cmd = f'sshpass ... ssh ... "echo \'{pub_key}\' >> ~/.ssh/authorized_keys && sort -u ..."'
```

**Called Automatically**: After all nodes are configured in `setup_all_workers()`.

### Problem 3: Inconsistent MCA Configuration

**Root Cause**: MCA (Modular Component Architecture) configuration only created on node running setup script. Remote nodes lacked critical OpenMPI settings for:
- Port ranges (firewall-friendly)
- Network interface selection (multi-NIC nodes)
- Installation prefix paths

**Solution Implemented**:
```python
def distribute_mca_config_to_all_nodes(self):
    """
    Distributes OpenMPI MCA configuration to all cluster nodes.
    Ensures consistent port ranges, network settings, etc.
    """
    local_mca_file = Path.home() / ".openmpi" / "mca-params.conf"
    
    for node_ip in all_nodes:
        # Create .openmpi directory remotely
        # Copy MCA config via scp
        copy_cmd = f"sshpass ... scp ... {temp_mca_path} {username}@{node_ip}:~/.openmpi/mca-params.conf"
```

**Critical MCA Parameters**:
```bash
# ~/.openmpi/mca-params.conf
btl_tcp_port_min_v4 = 50000
oob_tcp_port_range = 50100-50200      # PRTE daemon communication
oob_tcp_if_include = ens1f0           # Multi-NIC nodes only
orte_prefix = /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8
```

### Problem 4: Multi-Interface Network Nodes

**Root Cause**: Nodes with multiple NICs on the same subnet advertise multiple IP addresses. PRTE daemons get confused about routing, leading to communication failures.

**Detection**:
```bash
# Check for multiple interfaces on same subnet
ip addr show | grep "inet 192.168.1"

# Check routing table
ip route show
```

**Solution**: Specify exact interface in MCA config:
```bash
# ~/.openmpi/mca-params.conf
oob_tcp_if_include = ens1f0  # Primary interface only
btl_tcp_if_include = ens1f0
```

**Example Case**: Red Hat node with dual NICs:
- ens1f0: 192.168.1.136 (primary, 10 Gbps)
- ens1f1: 192.168.1.138 (secondary, 1 Gbps)

Without `oob_tcp_if_include`, OpenMPI advertises both IPs and routing fails.

**Performance Consideration**: When choosing which interface to use with `oob_tcp_if_include`:
1. Check interface speeds with `ethtool <interface> | grep Speed`
2. **Always bias towards the highest throughput interface** (e.g., 10 Gbps over 1 Gbps)
3. MPI message passing performance scales directly with network bandwidth
4. Configure both `oob_tcp_if_include` and `btl_tcp_if_include` to use the fastest interface

```bash
# Check interface speeds
ethtool ens1f0 | grep Speed  # 10000Mb/s (10 Gbps)
ethtool ens1f1 | grep Speed  # 1000Mb/s (1 Gbps)

# Configure MCA to use fastest interface
echo "oob_tcp_if_include = ens1f0" >> ~/.openmpi/mca-params.conf
echo "btl_tcp_if_include = ens1f0" >> ~/.openmpi/mca-params.conf
```

### Problem 5: Process Distribution (--map-by node)

**Root Cause**: OpenMPI 5.x changed default process mapping from round-robin to sequential fill. Without explicit mapping, all processes run on the first node.

**Symptoms**:
```bash
# Without --map-by node: All 12 processes on 192.168.1.139
mpirun -np 12 --hostfile /tmp/hosts ./program

# With --map-by node: 4 processes each on 3 nodes
mpirun --map-by node -np 12 --hostfile /tmp/hosts ./program
```

**Solution**: **ALWAYS** use `--map-by node` flag:
```bash
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node \
       -np 16 \
       --hostfile /tmp/hosts \
       ./program
```

**Verification**:
```bash
# Run with hostname to see distribution
mpirun --map-by node -np 12 --hostfile /tmp/hosts hostname

# Should show round-robin distribution across nodes
```

### Validation Test Results (Nov 2025)

**4-Node Cluster Test**: Successfully ran 16 MPI processes across all 4 nodes:

**Cluster Configuration**:
- Node 1: 192.168.1.139 (Ubuntu, single NIC) - Ranks 0, 4, 8, 12
- Node 2: 192.168.1.96 (Ubuntu, single NIC) - Ranks 1, 5, 9, 13
- Node 3: 192.168.1.136 (Red Hat, dual NIC) - Ranks 2, 6, 10, 14
- Node 4: 192.168.1.147 (Ubuntu WSL2) - Ranks 3, 7, 11, 15

**Test Command**:
```bash
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node \
       -np 16 \
       --hostfile /tmp/hostfile_full_cluster \
       /tmp/test_mpi_omp
```

**Results**: ✅ Perfect round-robin distribution, all nodes communicating, OpenMP threads active

**Validated Fixes**:
1. ✅ MPICH removal and OpenMPI linking on all nodes
2. ✅ Full SSH key mesh distribution (all nodes → all nodes)
3. ✅ MCA configuration distributed cluster-wide
4. ✅ Multi-interface configuration (Red Hat dual-NIC node working)
5. ✅ `--map-by node` ensuring even process distribution
6. ✅ WSL node successfully participating in cluster

### MPI Hostfiles Created by Setup Script

The `cluster_setup.py` script automatically creates **three different hostfiles** at `~/.openmpi/`:

1. **`hostfile`** - Standard configuration (4 slots per node)
   - Balanced for general MPI use
   - Fixed 4 processes per node maximum

2. **`hostfile_optimal`** - Recommended for hybrid MPI+OpenMP ⭐
   - 1 MPI process per node (1 slot)
   - Allows maximum OpenMP threads per process
   - **Best choice for most applications**
   - Minimizes MPI communication overhead

3. **`hostfile_max`** - Maximum MPI processes (auto-detected cores)
   - Uses all available cores for pure MPI
   - Detected via `nproc` on each node
   - For codes that don't use OpenMP threading

**Usage Examples**:
```bash
# Using optimal hostfile (recommended)
mpirun --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal ./my_program

# Using max MPI processes
mpirun --map-by node -np 152 --hostfile ~/.openmpi/hostfile_max ./my_program

# Using standard hostfile
mpirun --map-by node -np 12 --hostfile ~/.openmpi/hostfile ./my_program
```

**Recommendation**: Use `hostfile_optimal` for hybrid MPI+OpenMP codes to achieve best performance on heterogeneous clusters.

### UPC++ and PGAS Libraries

The cluster setup now includes **Berkeley UPC++** and PGAS (Partitioned Global Address Space) programming support built from source:

**Build Directory**: `~/cluster_sources` on each node (source code and compilation artifacts)

**Installed Components**:
- **GASNet-EX 2024.5.0**: `/home/linuxbrew/.linuxbrew/gasnet` - Communication layer
- **UPC++ 2024.3.0**: `/home/linuxbrew/.linuxbrew/upcxx` - Berkeley C++ PGAS library  
- **OpenSHMEM 1.5.2**: `/home/linuxbrew/.linuxbrew/openshmem` - Sandia SHMEM library
- **Compiler Wrapper**: `/home/linuxbrew/.linuxbrew/bin/upcxx`

**Quick Usage**:
```bash
# Compile UPC++ program
/home/linuxbrew/.linuxbrew/bin/upcxx -O3 myprogram.cpp -o myprogram

# Run on single node (SMP conduit)
/home/linuxbrew/.linuxbrew/bin/upcxx-run -n 4 ./myprogram

# Run across cluster (MPI conduit)
/home/linuxbrew/.linuxbrew/bin/upcxx-run -ssh-servers 192.168.1.139,192.168.1.96,192.168.1.136 -n 12 ./myprogram
```

**Available Conduits**:
- **SMP**: Shared memory (single node, best performance)
- **MPI**: Multi-node via OpenMPI (cluster-ready)
- **UDP**: Multi-node via UDP sockets (no MPI dependency)

**When to Use UPC++**:
- One-sided remote memory operations (rput/rget)
- Irregular communication patterns
- Asynchronous operations with futures
- Global distributed data structures

**Documentation**: https://upcxx.lbl.gov/docs/html/guide.html

**Key Advantages over MPI**:
- Simpler code for remote memory access
- Built-in asynchronous operations
- Global pointer abstraction
- Good for dynamic/irregular algorithms

## Remember

- This is a WSL environment with Windows filesystem mounts
- Virtual environments MUST be in Linux home directory
- Always set `UV_PROJECT_ENVIRONMENT` before uv commands
- Python 3.14 from Homebrew is required
- Use `uv run` to execute scripts with the correct environment
- **CRITICAL MPI**: All nodes must use same MPI implementation (OpenMPI 5.0.8)
- **CRITICAL MPI**: Always use `--map-by node` for cross-cluster distribution
- **CRITICAL MPI**: Multi-NIC nodes need `oob_tcp_if_include` in MCA config
- **CRITICAL MPI**: Full SSH key mesh required for any-node-as-head capability
