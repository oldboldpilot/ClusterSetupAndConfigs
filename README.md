# ClusterSetupAndConfigs

Automated cluster setup and configuration scripts for Slurm and OpenMPI on Ubuntu/WSL and Red Hat systems using Python 3.14 and uv.

## Features

- **Pure Python Implementation**: Written entirely in Python 3.14 for easy customization and maintenance
- **Comprehensive Parallel Programming Support**:
  - **OpenMPI 5.0.8**: Message Passing Interface for distributed computing
  - **OpenMP (libomp)**: Shared-memory thread-level parallelism
  - **UPC++ (Berkeley)**: Partitioned Global Address Space (PGAS) programming in C++
  - **GASNet**: High-performance communication system for PGAS languages
  - **OpenSHMEM**: Symmetric memory access for parallel programming
- **Automated Installation**: Installs and configures Homebrew, Slurm, and all parallel libraries
- **Cluster-Ready**: Configures master and worker nodes for distributed computing
- **Run from Any Node**: Setup entire cluster from master OR any worker node - automatic detection
- **Multi-OS Support**: Works on Ubuntu Linux, WSL with Ubuntu, Red Hat, CentOS, and Fedora
- **Smart Package Manager Detection**: Automatically uses apt-get (Ubuntu/Debian) or dnf (Red Hat/CentOS/Fedora)
- **Homebrew-Based**: All parallel libraries installed via Homebrew for consistency

## Requirements

- Python 3.14+ (installed via Homebrew)
- Ubuntu Linux, WSL with Ubuntu, Red Hat, CentOS, or Fedora
- uv package manager
- Sudo access on all nodes
- Network connectivity between all cluster nodes

## For AI Agents / Developers

If you're an AI agent (Claude, Copilot, etc.) or a developer working on this project, please read:
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive instructions for Claude AI agents
- **[copilot-instructions.md](copilot-instructions.md)** - Quick reference for GitHub Copilot

These files contain critical information about:
- WSL symlink issues and solutions
- uv setup with Python 3.14
- Environment variable requirements
- Common pitfalls and solutions

## Installation

### Prerequisites

1. **Supported Operating Systems**:
   - Ubuntu/Debian (uses apt-get)
   - Red Hat Enterprise Linux (RHEL)
   - CentOS
   - Fedora
   - (dnf-based distributions)
   - WSL2 with any of the above
   
   The script automatically detects your OS and uses the correct package manager.

2. **Install Python 3.14 via Homebrew**:
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.14
brew install python@3.14
```

3. **Install uv package manager**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
cd ClusterSetupAndConfigs

# IMPORTANT: On WSL, the Windows filesystem (/mnt/z, /mnt/c, etc.) doesn't support symlinks
# uv needs to store the virtual environment in your Linux home directory

# Set environment variable to use home directory for venv
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Sync dependencies (this will create the venv and install packages)
uv sync

# To run scripts with this environment
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --help
```

**Add to your shell profile for persistence** (optional but recommended):
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup' >> ~/.bashrc
source ~/.bashrc
```

### Alternative: Using venv directly

### Important: Run from ANY Node (Master or Worker)

**The script can run from ANY node in your cluster!** It automatically detects which node it's running on and sets up all other nodes:

- **Running from master:** Sets up all worker nodes
- **Running from worker:** Sets up master AND all other workers
- **Automatic Detection:** Uses IP address matching to identify current node

**How Node Detection Works:**
```bash
# The script checks all local network interfaces
ip addr show | grep "inet "

# Compares found IPs against master_ip and worker_ips in config
# Automatically identifies: "I'm the master" or "I'm worker node X"
# Then sets up all OTHER nodes
```

**Example:**
- Your cluster: master=10.0.0.10, workers=[10.0.0.11, 10.0.0.12, 10.0.0.13]
- You SSH to worker 10.0.0.13 and run the script
- Script detects: "I'm on worker 13"
- Script will setup: master 10.0.0.10, worker 11, worker 12 (all nodes EXCEPT 13)

If you encounter issues with uv on WSL:

```bash
# Ensure Python 3.14 is available
python3.14 --version

# Create a virtual environment in home directory (avoids WSL symlink issues)
python3.14 -m venv --copies ~/.venv/cluster-setup

# Activate the environment
source ~/.venv/cluster-setup/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the script
python cluster_setup.py --help
```

### Troubleshooting WSL/uv Issues

**Problem**: `Operation not permitted (os error 1)` when creating venv

**Problem**: WSL can't create symlinks on Windows filesystems. Always use:
- `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup` before running `uv sync`
- Or create venv in Linux home directory with `python3.14 -m venv --copies`

**Problem**: `python3.14` not found

**Solution**: 
```bash
# Check if Python 3.14 is installed via Homebrew
/home/linuxbrew/.linuxbrew/bin/python3.14 --version

# Add Homebrew to PATH
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

# Or use full path
uv python pin /home/linuxbrew/.linuxbrew/bin/python3.14
```

## Usage

### 📖 Complete Documentation

For detailed deployment instructions, troubleshooting, and best practices, see:
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Comprehensive deployment and usage guide

### ✨ Run from ANY Node

**The script can be executed from ANY node in your cluster** - master or worker. The script automatically:
- Detects which node it's running on by checking local IP addresses
- Detects the operating system (Ubuntu/Debian or Red Hat/CentOS/Fedora)
- Selects the appropriate package manager (apt-get or dnf)
- Sets up the current node first
- Then sets up all other nodes in the cluster via SSH (when using --password flag)

**Running from any node example:**
```bash
# SSH to ANY node in your cluster
ssh user@192.168.1.11  # Could be master or any worker

# Clone and setup entire cluster from this one node
git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
cd ClusterSetupAndConfigs
python cluster_setup.py --config cluster_config.yaml --password
# The script will detect this node and setup all others automatically
```

**Verify your current node:**
```bash
# See all your local IP addresses
ip addr show | grep "inet "
# The script will detect which node you're on automatically
```

### Configuration File

The script requires a YAML configuration file containing cluster node information. The script supports **two formats**: simple (IP strings) and extended (with OS and hostname information).

#### Simple Format (Backward Compatible)

Create a configuration file (e.g., `cluster_config.yaml`):

```yaml
master: 192.168.1.10
workers:
  - 192.168.1.11
  - 192.168.1.12
username: ubuntu  # optional

# OpenMP thread configuration (optional)
# Maximum threads available per node - use 'nproc' to determine
threads:
  192.168.1.10: 32  # master node
  192.168.1.11: 16  # worker1
  192.168.1.12: 16  # worker2
```

#### Extended Format (With OS and Hostname Information)

For better documentation and multi-OS support:

```yaml
master:
  ip: 192.168.1.10
  os: ubuntu wsl2
  name: master-node  # optional

workers:
  - ip: 192.168.1.11
    os: ubuntu
    name: worker1  # optional
  - ip: 192.168.1.12
    os: ubuntu
    name: worker2  # optional
  - ip: 192.168.1.13
    os: redhat
    name: worker3  # optional

username: ubuntu  # optional

# OpenMP thread configuration (optional)
threads:
  192.168.1.10: 32  # master: 16 cores × 2 threads/core
  192.168.1.11: 16  # worker1: 8 cores × 2 threads/core
  192.168.1.12: 16  # worker2: 8 cores × 2 threads/core
  192.168.1.13: 88  # worker3: 44 cores × 2 threads/core
```

**Note:** 
- The `threads` section is optional but recommended for hybrid MPI+OpenMP programs. It documents the maximum thread count available on each node.
- The `os` and `name` fields in the extended format are optional and used for documentation purposes.
- Both formats work identically - the script automatically detects and handles both.

### Automatic Full Cluster Setup (Recommended)

The easiest way to setup your entire cluster is to run the script **once** on the master node with the `--password` flag:

```bash
python cluster_setup.py --config cluster_config.yaml --password
```

You'll be prompted to enter the password for the worker nodes. The script will then:
1. Setup the master node completely
2. Generate and copy SSH keys to all worker nodes
3. **Automatically connect to each worker node via SSH**
4. **Run the full setup on each worker node remotely**
5. **Distribute SSH keys between ALL nodes** (so any node can SSH to any other)
6. **Distribute OpenMPI MCA configuration to all nodes** (for consistent MPI settings)
7. Configure the entire cluster end-to-end

This means you **only need to run the command once** on the master node, and the entire cluster will be configured automatically!

**Key Features**:
- ✅ **Cross-node SSH**: All nodes can SSH to each other without passwords (required for MPI from any node)
- ✅ **Multi-IP Support**: Automatically detects and configures SSH keys for nodes with multiple network interfaces
- ✅ **Full SSH Mesh**: Every node can connect to every other node via any of their IP addresses
- ✅ **Consistent MPI Settings**: OpenMPI MCA parameters distributed to all nodes automatically
- ✅ **MPICH Detection**: Automatically removes MPICH if found (incompatible with OpenMPI)
- ✅ **OpenMPI Linking**: Ensures OpenMPI is properly linked on all nodes

#### How to Know When Setup is Complete

**Command Line:**
- The script will print a final summary with "CLUSTER SETUP SUMMARY"
- Look for: `✓ Master node setup completed` and `✓ All worker nodes setup completed automatically`
- The script will return to the command prompt when done

**UI (cluster_setup_ui.py):**
- A notification will appear: "✓ Cluster setup completed!"
- The log will show: `✓ SETUP PROCESS COMPLETED` with a banner
- The "Setup Cluster" button will be re-enabled
- You'll see a message: "The cluster setup script has finished executing"

### Manual Setup (Alternative Method)

If you prefer to setup each node manually, or if automatic setup fails:

```bash
# On master node
python cluster_setup.py --config cluster_config.yaml

# Then manually on each worker node
python cluster_setup.py --config cluster_config.yaml
```

### Command-Line Options

```bash
# View all available options
python cluster_setup.py --help

# Required:
--config, -c           Path to YAML configuration file

# Optional:
--password, -p         Prompt for password to automatically setup the entire cluster
                       (copies SSH keys + runs setup on all worker nodes remotely)

--non-interactive      Run in non-interactive mode (skip confirmation prompts)
                       Automatically used for worker nodes during remote setup
```

### Complete Example

For a cluster with:
- Master node: 192.168.1.10 (Ubuntu)
- Worker nodes: 192.168.1.11 (Ubuntu), 192.168.1.12 (Red Hat)
- Username: ubuntu

**You can run from ANY node - the script auto-detects:**
```bash
# Check which node you're on
ip addr show | grep "inet "
# The script will automatically detect your node and setup all others
```

2. Create `cluster_config.yaml` (recommended extended format for multi-OS):

**Extended Format (Recommended for Multi-OS):**
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
    os: redhat  # Red Hat automatically uses dnf instead of apt-get
    name: worker2-redhat
username: ubuntu
```

**Or Simple Format (Still Works):**
```yaml
master: 192.168.1.10
workers:
  - 192.168.1.11
  - 192.168.1.12
username: ubuntu
# Note: Script will auto-detect OS on each node
```

3. Run from ANY node with automatic full cluster setup:
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --config cluster_config.yaml --password
# Enter password when prompted
# The script will automatically:
#   - Detect you're on the master node
#   - Setup the master node completely
#   - Copy SSH keys to workers
#   - Setup all worker nodes remotely
#   - Configure the entire cluster
```

3. Verify the setup:
```bash
# Test Slurm
sinfo

# Test OpenMPI (local only)
mpirun -np 2 hostname

# Test parallel execution across cluster with pdsh
brew install pdsh
pdsh -w 10.0.0.[10,11,12] hostname
```

## What the Script Does

The cluster setup script performs the following operations:

1. **Node Detection**: Automatically detects which node it's running on by checking all network interfaces against master/worker IPs in config
2. **OS Detection**: Automatically identifies Ubuntu/Debian (apt-get) or Red Hat/CentOS/Fedora (dnf) and uses appropriate package manager
3. **Homebrew Installation**: Installs Homebrew package manager on Ubuntu/WSL or Red Hat systems
4. **SSH Setup**:
   - Installs OpenSSH client and server
   - Generates SSH keys for passwordless authentication
   - Automatically copies SSH keys to worker nodes (with `--password` flag)
   - Uses secure password handling via stdin piping (no command-line exposure)
5. **Automatic Other-Node Setup** (with `--password` flag):
   - When run from master: Sets up all workers
   - When run from worker: Sets up master AND all other workers
   - Creates wrapper scripts for sudo password handling
   - Copies setup script and config to each node via SSH
   - Remotely executes full setup on all other nodes
   - Monitors progress and reports any errors
6. **Hosts File Configuration**: Updates `/etc/hosts` with all cluster node information
7. **Slurm Installation**: 
   - Ubuntu: Installs `slurm-wlm` via Homebrew
   - Red Hat: Installs `slurm` via Homebrew
8. **OpenMPI Installation**: 
   - Installs GCC 15.2.0 from Homebrew for C/C++23 compilation
   - Installs CMake (latest version from Homebrew) for build automation
   - Creates gcc-11 symlinks pointing to gcc-15 (OpenMPI's prebuilt bottles expect gcc-11)
   - Installs `openmpi` for distributed memory parallel computing
   - Sets compiler environment variables (CC, CXX, FC, OMPI_CC, OMPI_CXX, OMPI_FC) to use Homebrew GCC
   - Configures .bashrc and .ssh/environment to always use Homebrew compilers
   - Verifies mpicc can find and use the Homebrew GCC compiler
9. **OpenMP Installation**: Installs OpenMP (libomp) for shared memory parallel computing
   - Provides compiler support for `-fopenmp` flag
   - Enables thread-level parallelism within a single node
10. **UPC++ and PGAS Libraries Installation**: Installs PGAS programming models from source
   - **Build Directory**: `~/cluster_build_sources` on each node for source code and builds
   - **GASNet-EX**: Communication layer with MPI, SMP, and UDP conduits
   - **UPC++**: Berkeley's Unified Parallel C++ library for PGAS programming
   - **OpenSHMEM**: Sandia's Symmetric Hierarchical Memory library
   - **Installation**: `/home/linuxbrew/.linuxbrew/gasnet`, `/home/linuxbrew/.linuxbrew/upcxx`
   - Compiler wrapper: `/home/linuxbrew/.linuxbrew/bin/upcxx`
   - **Cluster-Wide Distribution**: Automatically copies binaries to all nodes with `--password` flag
   - Supports multiple conduits: SMP (single-node), MPI (multi-node via OpenMPI), UDP
   - Documentation: https://upcxx.lbl.gov/docs/html/guide.html
11. **Firewall Configuration**: Automatically configures firewall for MPI communication
   - **Ubuntu/Debian**: Configures UFW (if active) to allow ports 50000-50200
   - **Red Hat/CentOS/Fedora**: Configures firewalld (if active) to allow ports 50000-50200
   - **WSL**: Displays instructions for Windows Firewall configuration
   - Ports: BTL TCP (50000+), OOB TCP (50100-50200) for PRRTE daemon communication
12. **Slurm Configuration**:
   - Creates necessary directories (`/var/spool/slurm`, `/var/log/slurm`, etc.)
   - Generates `slurm.conf` with cluster topology
   - Configures cgroup support
   - Starts Slurm services (slurmctld on master, slurmd on all nodes)
13. **OpenMPI Configuration**:
    - **Installation**: OpenMPI installed via Homebrew at `/home/linuxbrew/.linuxbrew/`
    - **Binary Path**: `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8/bin/mpirun`
    - **Prefix**: `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8`
    - Creates **three MPI hostfiles** with all cluster nodes (see [OpenMPI Hostfiles](#openmpi-hostfiles))
    - Configures MCA parameters for cross-cluster communication
    - Sets up network interface parameters
    - **Usage**: Use `--prefix` flag with mpirun for consistent execution:
      ```bash
      mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
             --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal ./my_program
      ```
14. **Verification**: Tests all installed components

## Post-Installation Steps

After running the script on all nodes:

1. **Verify SSH connectivity**:
```bash
ssh worker1  # Should connect without password
```

2. **Check Slurm status**:
```bash
sinfo          # View node status
scontrol show nodes  # Detailed node information
```

3. **Test MPI**:
```bash
mpirun -np 4 -hostfile ~/.openmpi/hostfile hostname
```

4. **Submit a test Slurm job**:
```bash
srun -N 2 hostname
```

## Configuration Files

The script creates and manages the following configuration files:

- `/etc/hosts` - Cluster node hostnames and IPs
- `/etc/slurm/slurm.conf` - Slurm cluster configuration
- `/etc/slurm/cgroup.conf` - Cgroup configuration for Slurm
- `~/.openmpi/mca-params.conf` - OpenMPI parameters
- `~/.openmpi/hostfile*` - Three MPI hostfiles for different use cases

### OpenMPI Installation Details

**Homebrew Installation Path**: `/home/linuxbrew/.linuxbrew/`

**OpenMPI Version**: 5.0.8 (or latest available)

**Key Binaries**:
- `mpirun` / `mpiexec`: `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8/bin/mpirun`
- `mpicc` / `mpic++`: MPI compiler wrappers
- Libraries: `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8/lib/`

**Using the Prefix Flag**:
The `--prefix` flag ensures all nodes use the same OpenMPI installation:
```bash
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal ./program
```

**Why Prefix is Important**:
- Ensures consistent MPI library versions across heterogeneous nodes
- Prevents MPICH/OpenMPI conflicts
- Required when multiple MPI implementations exist on the system
- Avoids "orted" daemon version mismatches
- `~/.ssh/config` - SSH client configuration

### OpenMPI Hostfiles

The setup script automatically creates **three different hostfiles** for different use cases:

#### 1. `~/.openmpi/hostfile` - Standard (4 slots per node)
For running multiple MPI processes per node:
```
10.0.0.11 slots=4
10.0.0.12 slots=4
10.0.0.13 slots=4
10.0.0.10 slots=4
```

**Usage:**
```bash
# Run 12 MPI processes distributed across 4 nodes (3 per node)
mpirun --map-by node -np 12 --hostfile ~/.openmpi/hostfile ./my_program
```

#### 2. `~/.openmpi/hostfile_optimal` - Optimal (1 slot per node) ⭐ **RECOMMENDED**
For optimal MPI+OpenMP hybrid parallelism:
```
10.0.0.11 slots=1
10.0.0.12 slots=1
10.0.0.13 slots=1
10.0.0.10 slots=1
```

**Usage:**
```bash
# Run 1 MPI process per node with maximum OpenMP threads
# This is the RECOMMENDED configuration for most workloads
unset OMP_NUM_THREADS  # Let OpenMP auto-detect max threads
mpirun --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal ./my_program
```

**Benefits:**
- ✅ Minimizes expensive MPI communication overhead
- ✅ Maximizes efficient shared-memory parallelism via OpenMP
- ✅ Automatically uses all available threads on each node
- ✅ Simplifies process mapping and load balancing
- ✅ Best performance for most HPC applications

#### 3. `~/.openmpi/hostfile_max` - Maximum (auto-detected cores per node)
For maximum MPI parallelism (cores detected automatically):
```
10.0.0.11 slots=16
10.0.0.12 slots=16
10.0.0.13 slots=88
10.0.0.10 slots=32
```

**Usage:**
```bash
# Run maximum MPI processes based on available cores
# Total: 16+16+88+32 = 152 processes
mpirun --map-by node -np 152 --hostfile ~/.openmpi/hostfile_max ./my_program
```

**When to use:** When your application requires fine-grained MPI parallelism and minimal per-process memory usage.

### Choosing the Right Hostfile

| Hostfile | Use Case | MPI Processes | OpenMP Threads | Best For |
|----------|----------|---------------|----------------|----------|
| `hostfile` | Standard | 4 per node | Manual config | Balanced MPI/OpenMP |
| `hostfile_optimal` ⭐ | **Recommended** | 1 per node | All available | Most applications |
| `hostfile_max` | Maximum MPI | All cores | Minimal/None | Pure MPI codes |

**Quick Recommendation:**
- **New to hybrid MPI+OpenMP?** Use `hostfile_optimal`
- **Need domain decomposition?** Use `hostfile_optimal` (1 domain per node)
- **Pure MPI application?** Use `hostfile_max`
- **Custom requirements?** Use `hostfile` and adjust slots

## Troubleshooting

### Node Detection Issues

**Problem**: Script says "Current node is: WORKER" when you expected MASTER

**Cause**: Local IP addresses don't match the `master_ip` in config

**Solution**:
```bash
# Check what the script detects
ip addr show | grep "inet "

# Look for debug output in script:
# DEBUG: hostname='...', local_ip='...', master_ip='...'
# DEBUG: Found IPs on interfaces: [...]

# If your master IP isn't listed, either:
# 1. Update the config file with correct master_ip
# 2. Run the script from the actual master node
```

### MPI Processes Only Running on One Node

**Problem**: All MPI processes run on the head node even with a hostfile or `--host` flag

**Symptoms**:
```bash
# You run this:
mpirun -np 12 --hostfile ~/.openmpi/hostfile ./my_program

# But all 12 processes run on the master node only
# Expected: Processes distributed across all nodes in hostfile
```

**Root Cause**: OpenMPI 5.x default behavior changed - it fills each node sequentially instead of round-robin

**Solution**: **ALWAYS use `--map-by node` flag** for cross-cluster distribution:

```bash
# CORRECT - Distributes processes across nodes:
mpirun -np 12 --map-by node --hostfile ~/.openmpi/hostfile ./my_program

# WRONG - All processes run on first node:
mpirun -np 12 --hostfile ~/.openmpi/hostfile ./my_program
```

**How it works:**
- **Without `--map-by node`**: OpenMPI fills slots on each node completely before moving to next
  - Example with 3 nodes (4 slots each), 12 processes:
    - Node 1: Gets 4 processes
    - Node 2: Gets 4 processes  
    - Node 3: Gets 4 processes
    - BUT if Node 1 has more detected cores, it may get ALL 12!

- **With `--map-by node`**: Round-robin distribution across nodes
  - Example with 3 nodes, 12 processes:
    - Node 1: Gets processes 0, 3, 6, 9
    - Node 2: Gets processes 1, 4, 7, 10
    - Node 3: Gets processes 2, 5, 8, 11

**Verification:**
```bash
# Add hostname output to see distribution:
mpirun -np 12 --map-by node --hostfile ~/.openmpi/hostfile hostname

# Should show a mix of all hostnames, not just one
```

**Alternative**: Use `--map-by ppr:N:node` to specify exact processes per node:
```bash
# 4 processes per node:
mpirun -np 12 --map-by ppr:4:node --hostfile ~/.openmpi/hostfile ./my_program
```

### Optimal MPI + OpenMP Distribution Strategy

**Recommended Approach**: Use **one MPI process per node** with **maximum OpenMP threads per node**

This strategy maximizes performance by:
- Minimizing expensive MPI communication overhead
- Maximizing shared-memory parallelism via OpenMP
- Avoiding memory contention between MPI processes
- Simplifying process mapping

**Example Configuration**:

For a 4-node cluster with varying core counts:
- Node 1: 16 cores (32 threads with hyperthreading)
- Node 2: 16 cores (32 threads)
- Node 3: 44 cores (88 threads)
- Node 4: 16 cores (32 threads)

```bash
# Create hostfile with 1 slot per node
cat > hostfile << EOF
10.0.0.11 slots=1
10.0.0.12 slots=1
10.0.0.13 slots=1
10.0.0.10 slots=1
EOF

# Run with 1 MPI process per node, max OpenMP threads
export OMP_NUM_THREADS=32  # Or set per-node in script

# 4 MPI processes total (1 per node), each with max threads
mpirun --map-by node \
       -np 4 \
       --hostfile hostfile \
       -x OMP_NUM_THREADS=32 \
       ./my_hybrid_program

# For per-node thread control:
mpirun --map-by node -np 4 --hostfile hostfile \
       --host 10.0.0.11 -x OMP_NUM_THREADS=32 : \
       --host 10.0.0.12 -x OMP_NUM_THREADS=32 : \
       --host 10.0.0.13 -x OMP_NUM_THREADS=88 : \
       --host 10.0.0.10 -x OMP_NUM_THREADS=32 \
       ./my_hybrid_program
```

**When to Use Multiple MPI Processes Per Node**:
- Application requires more MPI parallelism
- Working with distributed data that doesn't fit in single node memory
- Benchmarking different MPI/OpenMP ratios

```bash
# Example: 2 MPI processes per node, half threads each
cat > hostfile << EOF
10.0.0.11 slots=2
10.0.0.12 slots=2
10.0.0.13 slots=2
10.0.0.10 slots=2
EOF

export OMP_NUM_THREADS=16  # Half the cores for each MPI process
mpirun --map-by node -np 8 --hostfile hostfile ./my_program
```

**Verification**:
```bash
# Test distribution with the test program
export OMP_NUM_THREADS=32
mpirun --map-by node -np 4 --hostfile hostfile /tmp/test_mpi_omp

# Should see:
# - 4 MPI ranks (0-3), one per hostname
# - Each rank showing many OpenMP threads (up to max cores)
```

### SSH Issues

If passwordless SSH is not working:
```bash
# Ensure the public key is in authorized_keys on all nodes
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test SSH manually
ssh -v worker1  # -v for verbose debugging
```

### Sudo Password Issues

**Problem**: `sudo: no password was provided` or lock file errors

**Solution**: The script now uses secure stdin piping. If issues persist:
```bash
# Verify sudo access
sudo -l

# Wait for other apt processes
sudo fuser /var/lib/dpkg/lock-frontend
# If process found, wait for it to complete
```

### Slurm Service Issues

**Problem**: Slurm services fail to start with errors like:
- `Incorrect permissions on state save loc: /var/spool/slurm/ctld`
- `The option "CgroupAutomount" is defunct`
- `Unable to determine this slurmd's NodeName`

**Solution**:

1. **Fix deprecated CgroupAutomount option** (Slurm 24.11+):
```bash
# Remove the deprecated option from cgroup.conf
sudo sed -i '/CgroupAutomount/d' /etc/slurm/cgroup.conf
```

2. **Fix directory permissions** (must be owned by slurm user):
```bash
sudo chown -R slurm:slurm /var/spool/slurm/ctld
sudo chown -R slurm:slurm /var/spool/slurm/d
sudo chown -R slurm:slurm /var/log/slurm
```

3. **Fix hostname mismatch** (slurm.conf must use actual hostname):
```bash
# Check your actual hostname
hostname

# Update slurm.conf to use actual hostname instead of "master"
# Edit /etc/slurm/slurm.conf and replace:
#   NodeName=master -> NodeName=ACTUAL-HOSTNAME
#   SlurmctldHost=master -> SlurmctldHost=ACTUAL-HOSTNAME
```

4. **Restart Slurm services**:
```bash
sudo systemctl restart slurmctld  # On master only
sudo systemctl restart slurmd     # On all nodes

# Check status
systemctl status slurmctld
systemctl status slurmd

# Test
sinfo
```

**Note**: The latest version of the script (as of October 2025) automatically handles these issues on both master and worker nodes. When workers are set up automatically via SSH, they receive the same configuration fixes.

**Worker Node Setup**: When using the `--password` flag on the master, worker nodes automatically receive:
- Correct master hostname in slurm.conf (fetched via SSH from master)
- Fixed cgroup.conf without deprecated options
- Proper directory permissions for Slurm services
- Systemctl service management

### MPI Cross-Cluster Execution Limitations on WSL

**Known Issue**: Both OpenMPI 5.x and MPICH 4.x have difficulty executing across remote nodes in WSL environments.

**Symptoms**:
- `mpirun` with `--host` or `--hostfile` hangs after SSH connection
- Works fine locally (single node) but fails across nodes
- SSH connectivity works, but MPI programs don't execute
- Socket write errors: "Bad file descriptor" or "write error"

**Root Cause**: This is a **fundamental WSL networking limitation** affecting MPI process managers:
- **OpenMPI 5.x** uses PRRTE (PMIx Reference Runtime Environment) for process management
- **MPICH 4.x** uses Hydra process manager
- Both require bidirectional network communication between all nodes
- Both require multiple TCP ports for daemon communication (not just SSH port 22)
- WSL's network architecture blocks these process manager communications

**Testing Results**:
- ✅ **Local execution works**: Both OpenMPI and MPICH can run multiple processes on a single node
- ✅ **SSH connectivity works**: Can SSH to remote nodes without issues
- ❌ **Cross-cluster MPI fails**: Process managers fail to establish socket connections between nodes
- ❌ **Windows Firewall scripts insufficient**: Even with firewall rules configured, socket communication fails

**What is PRRTE?**
- PRRTE is the runtime daemon system used by OpenMPI 5.x (replaces the older ORTE)
- Commands: `prte` (start DVM), `prted` (daemon), `prun` (run programs in DVM)
- Requires ports for PMIx and OOB TCP communication between nodes
- Installed automatically with OpenMPI 5.x via Homebrew

**What is Hydra?**
- Hydra is the process manager used by MPICH
- Uses PMI (Process Management Interface) for communication
- Similar socket-based communication requirements as PRRTE
- Exhibits same cross-cluster failures on WSL

### MPI Implementation Compatibility

**CRITICAL**: All nodes in the cluster MUST use the same MPI implementation.

**Problem**: MPICH and OpenMPI are incompatible - they cannot communicate with each other in a cluster.

**Symptoms**:
- `PRTE has lost communication with a remote daemon`
- MPI jobs hang or fail immediately when trying to use multiple nodes
- Error messages about unknown MPI commands or options
- `mpirun` behaves differently on different nodes

**Root Cause**: 
- Homebrew may install MPICH by default on some systems
- OpenMPI and MPICH have different internal protocols and cannot interoperate
- Even with same version numbers, they use completely different communication mechanisms

**Solution** (Automated):
The setup script now automatically:
1. Checks for MPICH installation on each node
2. Uninstalls MPICH if found
3. Installs and links OpenMPI
4. Verifies all nodes have OpenMPI 5.0.8

**Manual Check**:
```bash
# Check which MPI implementation is installed
ls -la /home/linuxbrew/.linuxbrew/bin/mpirun

# Should show: -> ../Cellar/open-mpi/5.0.8/bin/mpirun
# NOT: -> ../Cellar/mpich/4.3.2/bin/mpirun

# If you see MPICH, uninstall it and link OpenMPI:
brew uninstall mpich
brew link open-mpi
```

### Multi-Interface Network Nodes

**Problem**: Nodes with multiple network interfaces on the same subnet cause MPI communication failures.

**Symptoms**:
- `PRTE has lost communication with a remote daemon`
- MPI works locally but fails when trying to communicate with remote nodes
- Debug output shows daemon trying to connect to multiple IP addresses
- Error: "Unable to connect to remote daemon"

**Root Cause**:
- OpenMPI's PRTE daemon advertises all available IP addresses
- When a node has multiple interfaces (e.g., ens1f0 and ens1f1) on the same subnet
- Remote nodes get confused about which IP to connect back to
- The daemon may listen on one interface but advertise both IPs

**Detection**:
```bash
# Check if a node has multiple interfaces on the same subnet
ip addr show | grep "inet " | grep -v 127.0.0.1

# Example problematic output:
#   inet 10.0.0.13/24 ... ens1f0
#   inet 10.0.0.15/24 ... ens1f1  <- Multiple IPs on same subnet!
```

**Solution**:
Configure OpenMPI to use only one specific interface by editing `~/.openmpi/mca-params.conf`:

```conf
# Specify which interface to use
oob_tcp_if_include = ens1f0  # Use your primary interface name
btl_tcp_if_include = ens1f0

# Or use IP/netmask notation:
oob_tcp_if_include = 10.0.0.13/32  # Specific IP
btl_tcp_if_include = 10.0.0.13/32
```

Find your primary interface:
```bash
# Show default route to determine primary interface
ip route show default

# Output example:
# default via 10.0.0.1 dev ens1f0 proto dhcp src 10.0.0.13 metric 100
#                               ^^^^^^ This is your primary interface

# Check interface speeds to choose highest throughput
ethtool ens1f0 | grep Speed
ethtool ens1f1 | grep Speed

# Example output:
#   Speed: 10000Mb/s  <- ens1f0 is 10 Gbps
#   Speed: 1000Mb/s   <- ens1f1 is 1 Gbps

# Or check all interfaces:
for iface in $(ls /sys/class/net/ | grep -v lo); do
    echo -n "$iface: "
    ethtool $iface 2>/dev/null | grep Speed || echo "N/A"
done
```

**Performance Tip**: When multiple interfaces are available, **always configure OpenMPI to use the highest throughput interface** for MPI communication:
- **10 Gbps** (10000 Mb/s) is preferred over 1 Gbps for inter-node MPI traffic
- Use faster interface for `oob_tcp_if_include` and `btl_tcp_if_include`
- Slower interfaces can be used for SSH/management traffic
- This significantly improves MPI message passing performance

**Automatic Multi-IP Detection**:

The setup script (as of November 2025) automatically:
- Detects all IP addresses on each node during setup
- Distributes SSH keys that work for all detected IPs
- Creates a full mesh where any node can SSH to any IP of any other node

When running with `--password`, you'll see:
```
Detecting all IP addresses on 10.0.0.13...
  Found IPs: 10.0.0.13, 10.0.0.15
Distributing 10.0.0.11's key to 10.0.0.13 (all 2 IP(s))...
  ✓ Added 10.0.0.11's key to 10.0.0.13
    This key will work for all IPs: 10.0.0.13, 10.0.0.15
```

**Note**: While SSH keys are distributed for all IPs, you still need to configure MCA parameters to specify which interface OpenMPI should use for communication.

**Port Requirements for OpenMPI**:
The script now configures the following ports in `~/.openmpi/mca-params.conf`:
- **BTL TCP ports**: Starting from port 50000 (`btl_tcp_port_min_v4 = 50000`)
- **OOB TCP port range**: 50100-50200 (`oob_tcp_port_range = 50100-50200`)

**Firewall Configuration**:

For **Linux/Ubuntu** with ufw:
```bash
# If ufw is enabled
sudo ufw allow 50000:50200/tcp comment 'OpenMPI PRRTE'
```

For **WSL** - **CRITICAL CONFIGURATION REQUIRED**:

Windows Firewall and WSL Hyper-V VM settings block MPI communication by default. Additionally, **WSL must be configured to use mirrored mode networking** for the cluster to function properly.

**Step 1: Enable WSL Mirrored Mode Networking**

Create or edit `.wslconfig` in your Windows home directory (`C:\Users\<YourUsername>\.wslconfig`):

```ini
[wsl2]
networkingMode = mirrored
```

After creating/editing this file, restart WSL:
```powershell
wsl --shutdown
```

**Why mirrored mode is required**: 
- In default NAT mode, WSL uses an internal IP address that's not accessible from other cluster nodes
- Mirrored mode gives your WSL instance the same IP address as your Windows host
- This allows other nodes in your cluster to communicate with the WSL node directly
- Without mirrored mode, the cluster cannot route MPI traffic to/from the WSL node

**Step 2: Configure Firewall Rules**

We provide PowerShell scripts to configure Windows Firewall and WSL Hyper-V settings:

```powershell
# Open PowerShell as Administrator on Windows, navigate to project directory
cd Z:\PycharmProjects\ClusterSetupAndConfigs

# REQUIRED: Configure WSL Hyper-V firewall and Windows Firewall rules
.\configure_wsl_firewall.ps1
```

**What this script does:**
1. **Sets WSL Hyper-V VM firewall to allow inbound connections** (CRITICAL!)
   - Runs: `Set-NetFirewallHyperVVMSetting -Name <VM> -DefaultInboundAction Allow`
   - Reference: [Microsoft WSL Networking Docs](https://learn.microsoft.com/en-us/windows/wsl/networking)
   - Without this, MPI daemon communication will fail even with mirrored mode
2. Creates Windows Firewall rules for MPI port ranges (50000-50200)
3. Configures both inbound and outbound rules

**Manual configuration (alternative to script):**
```powershell
# Get your WSL VM ID
Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore

# Enable inbound connections (use the VM Name from above)
Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow -PolicyStore ActiveStore

# Verify
Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore
# Should show: DefaultInboundAction : Allow
```

The cluster setup script automatically detects WSL and displays these instructions.

**Network Interface Configuration Fixed**: The script originally hardcoded `btl_tcp_if_include = eth0`, but:
- eth0 is often DOWN on many systems
- The actual cluster network is typically on eth1 or other interfaces
- **Solution**: Script now auto-detects the correct network interface and uses IP ranges (e.g., `10.0.0.0/24`) instead of interface names for better reliability

**Workaround - Use pdsh for Parallel Execution**:

```bash
# Install pdsh
brew install pdsh

# Run commands across all nodes
pdsh -w 10.0.0.[10,11,12] hostname

# Execute Python scripts in parallel
pdsh -w 10.0.0.[10,11,12] 'python3 /path/to/script.py'

# Run with custom SSH options
pdsh -R exec -w 10.0.0.[11,12] command
```

**pdsh Benefits**:
- ✅ Simple and reliable parallel execution
- ✅ Works immediately with existing SSH setup
- ✅ No complex daemon or network requirements
- ✅ Perfect for embarrassingly parallel tasks

**Verifying PRRTE Installation**:
```bash
# Check PRRTE is installed
prte --version
prun --version

# View configured MPI ports
cat ~/.openmpi/mca-params.conf
```

**Recommended Solutions for WSL Cross-Cluster Execution**:

1. **Use OpenMPI with Correct Flags** (✅ WORKS - Verified on WSL master + Native Linux workers):

   **The solution that works:**
   ```bash
   mpirun -np 6 \
     --host 192.168.1.10,192.168.1.11,192.168.1.12 \
     --oversubscribe \
     --map-by node \
     --mca btl_tcp_if_include 192.168.1.0/24 \
     your_program
   ```

   **Required flags:**
   - `--oversubscribe` - Allows running more processes than detected slots
   - `--map-by node` - Forces round-robin distribution across nodes (critical!)
   - `--mca btl_tcp_if_include 192.168.1.0/24` - Specifies correct network interface/subnet

   **Example commands:**
   ```bash
   # Simple hostname test (verified working)
   mpirun -np 6 --host 192.168.1.10,192.168.1.11,192.168.1.12 \
     --oversubscribe --map-by node --mca btl_tcp_if_include 192.168.1.0/24 \
     hostname

   # Python script
   mpirun -np 6 --host 192.168.1.10,192.168.1.11,192.168.1.12 \
     --oversubscribe --map-by node --mca btl_tcp_if_include 192.168.1.0/24 \
     python3 my_script.py
   ```

   **Prerequisites:**
   1. **WSL with mirrored networking mode enabled**
      - Create/edit `C:\Users\YourUsername\.wslconfig`:
        ```ini
        [wsl2]
        networkingMode=mirrored
        ```
      - Restart WSL: `wsl --shutdown`

   2. **WSL Hyper-V VM firewall configured** (CRITICAL!)
      - Run PowerShell as Administrator:
        ```powershell
        Set-NetFirewallHyperVVMSetting -Name '{YOUR-VM-ID}' -DefaultInboundAction Allow
        ```
      - Or use the provided script: `.\configure_wsl_firewall.ps1`
      - Reference: [Microsoft WSL Networking](https://learn.microsoft.com/en-us/windows/wsl/networking)

   3. **OpenMPI 5.x installed on all nodes**
      - `brew install open-mpi`

   4. **SSH keys configured for passwordless access**
      - `ssh-keygen` + `ssh-copy-id`

   **Verified working configuration:**
   - Master: WSL Ubuntu with mirrored mode + Hyper-V firewall configured (192.168.1.10)
   - Worker 1: Native Ubuntu Linux (192.168.1.11)
   - Worker 2: Native Ubuntu Linux (192.168.1.12)

2. **Use pdsh for embarrassingly parallel tasks** (RECOMMENDED - Works NOW, no WSL changes needed):
   ```bash
   # Install pdsh
   brew install pdsh

   # Run commands across all nodes
   pdsh -w 192.168.1.[147,137,96] 'python3 script.py'
   pdsh -w 192.168.1.[147,137,96] hostname

   # Verified working - uses only SSH (port 22)
   ```

3. **Use Slurm's `srun`** (For true MPI programs, requires Slurm setup):
   ```bash
   # Slurm handles process management without MPI daemons
   srun -N 2 -n 6 hostname
   srun -N 3 python my_mpi_program.py
   ```

4. **Use Native Linux** (Not WSL):
   - If mirrored mode doesn't work or isn't available
   - OpenMPI and MPICH work properly on native Linux with correct firewall configuration

**Important MPI Configuration Notes**:

**What DOESN'T work (without correct flags):**
- ❌ Default `mpirun` without `--map-by node` - Runs all processes on master only
- ❌ MPICH - Socket communication failures even with correct configuration
- ❌ WSL without mirrored networking mode - NAT breaks daemon communication

**Critical flags discovered:**
- ✅ `--map-by node` is **essential** for distributing processes across nodes
- ✅ `--oversubscribe` allows flexible process allocation
- ✅ `--mca btl_tcp_if_include` with correct subnet ensures proper network interface selection

**Note:** OpenMPI 5.x WORKS on hybrid WSL+Linux clusters when:
1. WSL is configured with mirrored networking mode
2. Correct mpirun flags are used (`--map-by node` is critical)
3. Network interface is explicitly specified via MCA parameter

### Using OpenMP for Shared Memory Parallelism

OpenMP is automatically installed by the cluster setup script and provides thread-level parallelism within a single node.

**Basic OpenMP Example (C/C++):**
```c
#include <omp.h>
#include <stdio.h>

int main() {
    #pragma omp parallel
    {
        printf("Hello from thread %d of %d\n",
               omp_get_thread_num(), omp_get_num_threads());
    }
    return 0;
}
```

**Compile and run:**
```bash
# Compile with OpenMP support
gcc -fopenmp hello_openmp.c -o hello_openmp

# Run with specified number of threads
export OMP_NUM_THREADS=4
./hello_openmp
```

**Python with OpenMP (via NumPy/SciPy):**
Many Python scientific libraries (NumPy, SciPy, scikit-learn) automatically use OpenMP for parallelization. You can control thread count:

```python
import os
os.environ['OMP_NUM_THREADS'] = '4'  # Set before importing numpy
import numpy as np

# NumPy operations will use OpenMP threading
result = np.dot(large_matrix_a, large_matrix_b)
```

**Finding Maximum Thread Count:**

Determine the optimal number of threads for each node:

```bash
# Get number of CPU cores/threads on current node
nproc

# Detailed CPU information
lscpu | grep -E "^CPU\(s\)|Thread|Core"

# Check all nodes
pdsh -w 192.168.1.[147,139,96] "nproc"

# For OpenMP programs, also check at runtime
export OMP_NUM_THREADS=$(nproc)
```

**Your cluster configuration:**
- Master (192.168.1.10): 32 threads (16 cores × 2 threads/core)
- Worker 1 (192.168.1.11): 16 threads
- Worker 2 (192.168.1.12): 16 threads

**Combining OpenMP + OpenMPI (Hybrid Parallelism):**

Hybrid parallelism uses MPI for inter-node communication and OpenMP for intra-node threading. This maximizes resource utilization.

**Strategy 1: Maximum threads per MPI process**
```bash
# 1 MPI process per node, all cores as OpenMP threads
# Total: 3 MPI processes × their respective thread counts
export OMP_NUM_THREADS=32  # On master
mpirun -np 3 --host 192.168.1.10,192.168.1.11,192.168.1.12 \
  --oversubscribe --map-by node \
  --mca btl_tcp_if_include 192.168.1.0/24 \
  --bind-to none \
  ./my_hybrid_program

# Workers will use their available cores (16 each)
```

**Strategy 2: Balanced MPI processes with OpenMP threads**
```bash
# 2 MPI processes per node, each with 8 threads (for 16-core nodes)
# Master: 2 processes × 16 threads = 32 threads
# Workers: 2 processes × 8 threads = 16 threads each
export OMP_NUM_THREADS=8
mpirun -np 6 --host 192.168.1.10,192.168.1.11,192.168.1.12 \
  --oversubscribe --map-by node \
  --mca btl_tcp_if_include 192.168.1.0/24 \
  --bind-to none \
  ./my_hybrid_program
```

**Strategy 3: Per-node thread configuration**
```bash
# Set different thread counts per node using rankfile
# Create a rankfile specifying MPI ranks and thread bindings

# Or use environment variable per execution
# Master with 16 threads per process, workers with 8
OMP_NUM_THREADS=16 mpirun -np 1 --host 192.168.1.10 \
  --mca btl_tcp_if_include 192.168.1.0/24 \
  ./program : \
  -np 2 --host 192.168.1.11,192.168.1.12 \
  bash -c 'OMP_NUM_THREADS=8 ./program'
```

**Important flags for hybrid parallelism:**
- `--bind-to none` - Allows OpenMP to manage thread binding instead of MPI
- `OMP_NUM_THREADS` - Sets OpenMP thread count
- Consider setting `OMP_PROC_BIND=true` for thread affinity
- Use `OMP_PLACES=cores` or `OMP_PLACES=threads` for fine-grained control

**Example hybrid program (C):**
```c
#include <mpi.h>
#include <omp.h>
#include <stdio.h>

int main(int argc, char** argv) {
    int rank, size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        int nthreads = omp_get_num_threads();
        #pragma omp critical
        printf("MPI rank %d/%d, OpenMP thread %d/%d\n",
               rank, size, tid, nthreads);
    }

    MPI_Finalize();
    return 0;
}
```

**Compile and run:**
```bash
# Compile with both MPI and OpenMP support
mpicc -fopenmp hybrid_program.c -o hybrid_program

# Run with 6 MPI processes, 8 OpenMP threads each
export OMP_NUM_THREADS=8
mpirun -np 6 --host 192.168.1.10,192.168.1.11,192.168.1.12 \
  --oversubscribe --map-by node \
  --mca btl_tcp_if_include 192.168.1.0/24 \
  --bind-to none \
  ./hybrid_program
```

**Verify OpenMP installation:**
```bash
# Check if compiler supports OpenMP
echo | gcc -fopenmp -x c - -o /tmp/test_omp && echo "OpenMP supported"

# Check libomp installation
brew list libomp

# Runtime verification
OMP_NUM_THREADS=4 ./openmp_program
```

### For Detailed Troubleshooting

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive troubleshooting steps

## UPC++ and PGAS Programming

### Overview

The cluster supports **Partitioned Global Address Space (PGAS)** programming models through Berkeley UPC++, providing an alternative to traditional MPI programming with potentially simpler code for distributed memory operations.

**Installed Libraries**:
- **UPC++**: Berkeley's C++ library for PGAS programming
- **GASNet**: Communication layer supporting multiple network conduits
- **OpenSHMEM**: Symmetric memory access library for PGAS

**Key Features**:
- One-sided communication (direct remote memory access)
- Asynchronous operations with futures/promises
- Global pointer abstraction for distributed data
- Efficient for irregular communication patterns
- Simpler than MPI for certain algorithms

### Installation Paths

- **Build Directory**: `~/cluster_build_sources` (source code and build artifacts on each node)
- **GASNet-EX**: `/home/linuxbrew/.linuxbrew/gasnet` (version 2025.8.0)
- **UPC++ Installation**: `/home/linuxbrew/.linuxbrew/upcxx` (version 2025.10.0)
- **OpenSHMEM**: `/home/linuxbrew/.linuxbrew/openshmem`
- **UPC++ Compiler**: `/home/linuxbrew/.linuxbrew/bin/upcxx`
- **UPC++ Runtime**: `/home/linuxbrew/.linuxbrew/bin/upcxx-run`
- **Documentation**: https://upcxx.lbl.gov/docs/html/guide.html

### Required System Libraries

The PGAS installation requires specific system libraries from Homebrew to ensure compatibility:

- **GNU Binutils 2.45**: Modern assembler and linker tools
  - Symlinked to `/usr/local/bin/{as,ld,ar,ranlib}`
  - Required for `.base64` assembler directive support in GASNet
  
- **GLIBC 2.35**: C library with newer GLIBC symbols
  - Location: `/home/linuxbrew/.linuxbrew/Cellar/glibc/2.35_2/lib`
  - Required for math functions (log2@GLIBC_2.29, fesetround@GLIBC_2.2.5, etc.)
  - Linked with `-L/home/linuxbrew/.linuxbrew/Cellar/glibc/2.35_2/lib -Wl,-rpath,/home/linuxbrew/.linuxbrew/Cellar/glibc/2.35_2/lib -lm`

- **Python 3.14**: Latest Homebrew Python
  - Symlinked to `/usr/local/bin/python3` and `/usr/local/bin/pip3`
  - Required for build scripts and configuration tools

These libraries are automatically configured by the cluster setup script and distributed to all nodes.

### Cluster-Wide Installation

When running with the `--password` flag, the setup script automatically:
1. Builds PGAS libraries from source in `~/cluster_build_sources` on the first node
2. Distributes compiled binaries to all other cluster nodes via rsync
3. Updates environment variables on all nodes
4. Creates symbolic links for easy access cluster-wide

This ensures all nodes have identical PGAS installations without requiring each node to compile from source separately.

### UPC++ Quick Start

**Simple Hello World:**
```cpp
#include <upcxx/upcxx.hpp>
#include <iostream>

int main() {
    upcxx::init();
    
    std::cout << "Hello from rank " << upcxx::rank_me() 
              << " of " << upcxx::rank_n() << std::endl;
    
    upcxx::finalize();
    return 0;
}
```

**Compile and Run:**
```bash
# Compile UPC++ program
/home/linuxbrew/.linuxbrew/bin/upcxx -O3 hello.cpp -o hello_upcxx

# Run on single node (SMP conduit)
/home/linuxbrew/.linuxbrew/bin/upcxx-run -n 4 ./hello_upcxx

# Run across cluster (MPI conduit via SSH)
/home/linuxbrew/.linuxbrew/bin/upcxx-run -ssh-servers node1,node2,node3 -n 12 ./hello_upcxx
```

### Available Conduits

1. **SMP Conduit** (default): Single-node shared memory
   ```bash
   upcxx-run -n 4 ./program
   ```

2. **MPI Conduit**: Multi-node via OpenMPI
   ```bash
   upcxx-run -ssh-servers 192.168.1.139,192.168.1.96,192.168.1.136 -n 12 ./program
   ```

3. **UDP Conduit**: Multi-node via UDP sockets (no MPI required)
   ```bash
   export GASNET_SPAWNFN=S
   upcxx-run -n 12 ./program
   ```

### UPC++ Example: Remote Memory Access

```cpp
#include <upcxx/upcxx.hpp>

int main() {
    upcxx::init();
    
    // Allocate distributed array
    upcxx::global_ptr<int> data = nullptr;
    if (upcxx::rank_me() == 0) {
        data = upcxx::new_array<int>(100);
    }
    
    // Broadcast pointer to all ranks
    data = upcxx::broadcast(data, 0).wait();
    
    // Remote write to rank 0's memory
    if (upcxx::rank_me() != 0) {
        upcxx::rput(upcxx::rank_me(), data + upcxx::rank_me()).wait();
    }
    
    upcxx::barrier();
    
    if (upcxx::rank_me() == 0) {
        upcxx::delete_array(data);
    }
    
    upcxx::finalize();
    return 0;
}
```

### When to Use UPC++ vs MPI

**Use UPC++ when:**
- You need one-sided communication (remote memory access)
- Communication patterns are irregular or unpredictable
- You want asynchronous operations with futures
- Global data structures simplify your algorithm

**Use MPI when:**
- Collective operations dominate (allreduce, allgather, etc.)
- Regular structured communication patterns
- Maximum portability is required
- Using existing MPI libraries

**Hybrid Approach:**
UPC++ can coexist with MPI - use MPI for collectives and UPC++ for irregular communication.

### Performance Considerations

- **SMP conduit**: Best for shared-memory systems, zero-copy operations
- **MPI conduit**: Leverages existing OpenMPI infrastructure, good for clusters
- **Network Performance**: GASNet can utilize high-performance networks (10+ Gbps)
- **Asynchronous Operations**: Use futures to overlap communication and computation

### Troubleshooting UPC++

**Check Installation:**
```bash
/home/linuxbrew/.linuxbrew/bin/upcxx --version
/home/linuxbrew/.linuxbrew/bin/upcxx -show
```

**Verify Conduits:**
```bash
# List available conduits
/home/linuxbrew/.linuxbrew/bin/upcxx -show 2>&1 | grep -i conduit
```

**Debug Mode:**
```bash
# Compile with debug symbols
upcxx -g myprogram.cpp -o myprogram

# Run with verbose output
GASNET_VERBOSEENV=1 upcxx-run -n 4 ./myprogram
```

## Architecture

```
Master Node (192.168.1.10)
├── slurmctld (Slurm controller)
├── slurmd (Slurm daemon)
└── OpenMPI

Worker Node 1 (192.168.1.11)
├── slurmd (Slurm daemon)
└── OpenMPI

Worker Node 2 (192.168.1.12)
├── slurmd (Slurm daemon)
└── OpenMPI
```

## Validation and Testing

### Production Cluster Test Results (November 2025)

#### Test 1: Multi-Process Distribution (16 MPI Processes)

Successfully validated full 4-node heterogeneous cluster with all critical fixes:

**Test Configuration**:
- **Node 1**: 192.168.1.139 (Ubuntu 24.04, single NIC) - 4 MPI ranks
- **Node 2**: 192.168.1.96 (Ubuntu 24.04, single NIC) - 4 MPI ranks  
- **Node 3**: 192.168.1.136 (Red Hat 9.5, dual NIC) - 4 MPI ranks
- **Node 4**: 192.168.1.147 (Ubuntu 24.04 WSL2) - 4 MPI ranks

**Test Command**:
```bash
export OMP_NUM_THREADS=2
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node \
       -np 16 \
       --hostfile /tmp/hostfile \
       /tmp/test_mpi_omp
```

**Results**: ✅ **All 16 MPI processes perfectly distributed** with round-robin mapping across all 4 nodes, OpenMP threads active, full cross-cluster communication working.

#### Test 2: Optimal MPI+OpenMP Distribution ⭐ **RECOMMENDED**

**Test Configuration**:
- **Node 1**: 192.168.1.139 (Ubuntu 24.04) - 16 threads available
- **Node 2**: 192.168.1.96 (Ubuntu 24.04) - 16 threads available  
- **Node 3**: 192.168.1.136 (Red Hat 9.5, dual NIC) - 44 threads available
- **Node 4**: 192.168.1.147 (Ubuntu 24.04 WSL2) - 32 threads available

**Test Command**:
```bash
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node \
       -np 4 \
       --hostfile ~/.openmpi/hostfile_optimal \
       /tmp/test_mpi_omp
```

**Distribution Results**:
```
MPI Rank 0: muyiwadroexperiments       → 16 OpenMP threads
MPI Rank 1: oluubuntul1                → 16 OpenMP threads  
MPI Rank 2: oluwasanmiredhatserver     → 44 OpenMP threads
MPI Rank 3: DESKTOP-3SON9JT            → 32 OpenMP threads
```

**Results**: ✅ **Optimal distribution achieved**
- Total: 4 MPI processes using 108 threads (16+16+44+32)
- 1 MPI process per node minimizes inter-node communication
- Each process uses ALL available threads on its node
- Maximizes shared-memory parallelism within each node
- Perfect for heterogeneous clusters with varying core counts

**Performance Benefits**:
- ✓ Minimal MPI message passing overhead
- ✓ Maximum OpenMP parallel efficiency  
- ✓ Optimal for applications with large shared-memory regions
- ✓ Scales perfectly across heterogeneous hardware

**Validated Features**:
1. ✅ MPICH detection and automatic removal
2. ✅ OpenMPI 5.0.8 with --prefix flag on all nodes
3. ✅ Full SSH key mesh distribution (all nodes ↔ all nodes)
4. ✅ Multi-IP SSH support (dual-NIC Red Hat node)
5. ✅ MCA configuration distributed to all nodes
6. ✅ Multi-interface network handling (10 Gbps + 1 Gbps)
7. ✅ Three hostfiles created automatically (standard, optimal, max)
8. ✅ `--map-by node` ensuring even process distribution
9. ✅ WSL node successfully participating in cluster
10. ✅ Heterogeneous OS mix (Ubuntu + Red Hat + WSL)
11. ✅ Optimal MPI+OpenMP configuration validated

**Performance**: Process distribution completed successfully with no PRTE daemon communication failures or routing issues.

### Test Your Cluster

After setup, verify your cluster with the provided C++23 MPI+OpenMP test:

```bash
# Compile test program (done automatically by setup script)
# Or manually:
mpic++ -std=c++23 -fopenmp -o /tmp/test_mpi_omp mpi_test.cpp

# Run on full cluster (always use --map-by node!)
export OMP_NUM_THREADS=4
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node \
       -np 12 \
       --hostfile /tmp/hostfile \
       /tmp/test_mpi_omp

# Verify distribution (should show round-robin across nodes)
mpirun --map-by node -np 12 --hostfile /tmp/hostfile hostname
```

**Expected Output**: You should see MPI ranks distributed evenly across all nodes with OpenMP threads running on each.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.