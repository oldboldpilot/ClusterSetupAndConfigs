# ClusterSetupAndConfigs

Automated cluster setup and configuration scripts for Slurm and OpenMPI on Ubuntu/WSL systems using Python 3.13 and uv.

## Features

- **Pure Python Implementation**: Written entirely in Python 3.13 for easy customization and maintenance
- **Automated Installation**: Installs and configures Homebrew, Slurm, OpenMPI, and OpenSSH
- **Cluster-Ready**: Configures master and worker nodes for distributed computing
- **Ubuntu/WSL Support**: Works on both native Ubuntu Linux and Windows Subsystem for Linux (WSL)

## Requirements

- Python 3.13+ (installed via Homebrew)
- Ubuntu Linux or WSL with Ubuntu installed
- uv package manager
- Sudo access on all nodes
- Network connectivity between all cluster nodes

## For AI Agents / Developers

If you're an AI agent (Claude, Copilot, etc.) or a developer working on this project, please read:
- **[CLAUDE.md](CLAUDE.md)** - Comprehensive instructions for Claude AI agents
- **[copilot-instructions.md](copilot-instructions.md)** - Quick reference for GitHub Copilot

These files contain critical information about:
- WSL symlink issues and solutions
- uv setup with Python 3.13
- Environment variable requirements
- Common pitfalls and solutions

## Installation

### Prerequisites

1. **Install Python 3.13 via Homebrew**:
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.13
brew install python@3.13
```

2. **Install uv package manager**:
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

### Important: Run from Master Node

**The script MUST be run from the master node** specified in your YAML config file. The script automatically detects which node it's running on by checking local IP addresses.

- If you run from the master node, it will set up all worker nodes automatically
- If you run from a worker node, it will only configure that local worker

Check which node you're on with:
```bash
ip addr show | grep inet
```

Compare the output with your master_ip in the config file.

If you encounter issues with uv on WSL:

```bash
# Ensure Python 3.13 is available
python3.13 --version

# Create a virtual environment in home directory (avoids WSL symlink issues)
python3.13 -m venv --copies ~/.venv/cluster-setup

# Activate the environment
source ~/.venv/cluster-setup/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the script
python cluster_setup.py --help
```

### Troubleshooting WSL/uv Issues

**Problem**: `Operation not permitted (os error 1)` when creating venv

**Solution**: WSL can't create symlinks on Windows filesystems. Always use:
- `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup` before running `uv sync`
- Or create venv in Linux home directory with `python3.13 -m venv --copies`

**Problem**: `python3.13` not found

**Solution**: 
```bash
# Check if Python 3.13 is installed via Homebrew
/home/linuxbrew/.linuxbrew/bin/python3.13 --version

# Add Homebrew to PATH
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

# Or use full path
uv python pin /home/linuxbrew/.linuxbrew/bin/python3.13
```

## Usage

### 📖 Complete Documentation

For detailed deployment instructions, troubleshooting, and best practices, see:
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Comprehensive deployment and usage guide

### ⚠️ Critical Requirement: Run from Master Node

**The script MUST be executed from the master node** specified in your configuration file. The script automatically detects which node it's running on by checking local IP addresses.

Check your current node:
```bash
# See all your local IP addresses
ip addr show | grep "inet "

# The output should include the master_ip from your config file
```

### Configuration File

The script requires a YAML configuration file containing cluster node information.

Create a configuration file (e.g., `cluster_config.yaml`):

```yaml
master_ip: "192.168.1.10"
worker_ips:
  - "192.168.1.11"
  - "192.168.1.12"
username: "ubuntu"

# OpenMP thread configuration (optional)
# Maximum threads available per node - use 'nproc' to determine
threads:
  192.168.1.10: 32  # master node
  192.168.1.11: 16  # worker1
  192.168.1.12: 16   # worker2
```

**Note:** The `threads` section is optional but recommended for hybrid MPI+OpenMP programs. It documents the maximum thread count available on each node.

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
5. Configure the entire cluster end-to-end

This means you **only need to run the command once** on the master node, and the entire cluster will be configured automatically!

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
- Master node: 192.168.1.10
- Worker nodes: 192.168.1.11, 192.168.1.12
- Username: ubuntu

1. **Verify you're on the master node**:
```bash
ip addr show | grep "inet " | grep 192.168.1.10
# Should see output if you're on the master node
```

2. Create `cluster_config.yaml`:
```yaml
master_ip: "192.168.1.10"
worker_ips:
  - "192.168.1.11"
  - "192.168.1.12"
username: "ubuntu"
```

3. Run on master node with automatic full cluster setup:
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
pdsh -w 192.168.1.[147,137,96] hostname
```

## What the Script Does

The cluster setup script performs the following operations:

1. **Node Detection**: Automatically detects if running on master or worker node by comparing local IPs
2. **Homebrew Installation**: Installs Homebrew package manager on Ubuntu/WSL
3. **SSH Setup**:
   - Installs OpenSSH client and server
   - Generates SSH keys for passwordless authentication
   - Automatically copies SSH keys to worker nodes (with `--password` flag)
   - Uses secure password handling via stdin piping (no command-line exposure)
4. **Automatic Worker Setup** (when run from master with `--password`):
   - Creates wrapper scripts for sudo password handling
   - Copies setup script and config to each worker via SSH
   - Remotely executes full setup on all worker nodes
   - Monitors progress and reports any errors
5. **Hosts File Configuration**: Updates `/etc/hosts` with all cluster node information
6. **Slurm Installation**: Installs Slurm workload manager via Homebrew
7. **OpenMPI Installation**: Installs OpenMPI for distributed memory parallel computing
8. **OpenMP Installation**: Installs OpenMP (libomp) for shared memory parallel computing
   - Provides compiler support for `-fopenmp` flag
   - Enables thread-level parallelism within a single node
9. **Slurm Configuration**:
   - Creates necessary directories (`/var/spool/slurm`, `/var/log/slurm`, etc.)
   - Generates `slurm.conf` with cluster topology
   - Configures cgroup support
   - Starts Slurm services (slurmctld on master, slurmd on all nodes)
10. **OpenMPI Configuration**:
    - Creates MPI hostfile with all cluster nodes
    - Configures MCA parameters for cross-cluster communication
    - Sets up network interface parameters
11. **Verification**: Tests all installed components

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
- `~/.openmpi/hostfile` - OpenMPI node list
- `~/.openmpi/mca-params.conf` - OpenMPI parameters
- `~/.ssh/config` - SSH client configuration

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

Windows Firewall and WSL Hyper-V VM settings block MPI communication by default. We provide PowerShell scripts to configure everything:

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
- **Solution**: Script now auto-detects the correct network interface and uses IP ranges (e.g., `192.168.1.0/24`) instead of interface names for better reliability

**Workaround - Use pdsh for Parallel Execution**:

```bash
# Install pdsh
brew install pdsh

# Run commands across all nodes
pdsh -w 192.168.1.[147,137,96] hostname

# Execute Python scripts in parallel
pdsh -w 192.168.1.[147,137,96] 'python3 /path/to/script.py'

# Run with custom SSH options
pdsh -R exec -w 192.168.1.[137,96] command
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.