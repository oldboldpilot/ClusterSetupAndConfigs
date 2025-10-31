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
master_ip: "192.168.1.147"
worker_ips:
  - "192.168.1.137"
  - "192.168.1.96"
username: "muyiwa"
```

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
--config, -c    Path to YAML configuration file

# Optional:
--password, -p  Prompt for password to automatically setup the entire cluster
                (copies SSH keys + runs setup on all worker nodes remotely)
```

### Complete Example

For a cluster with:
- Master node: 192.168.1.147
- Worker nodes: 192.168.1.137, 192.168.1.96
- Username: muyiwa

1. **Verify you're on the master node**:
```bash
ip addr show | grep "inet " | grep 192.168.1.147
# Should see output if you're on the master node
```

2. Create `cluster_config.yaml`:
```yaml
master_ip: "192.168.1.147"
worker_ips:
  - "192.168.1.137"
  - "192.168.1.96"
username: "muyiwa"
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

# Test OpenMPI
mpirun -np 2 hostname
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
7. **OpenMPI Installation**: Installs OpenMPI for parallel computing
8. **Slurm Configuration**: 
   - Creates necessary directories (`/var/spool/slurm`, `/var/log/slurm`, etc.)
   - Generates `slurm.conf` with cluster topology
   - Configures cgroup support
   - Starts Slurm services (slurmctld on master, slurmd on all nodes)
9. **OpenMPI Configuration**: 
   - Creates MPI hostfile with all cluster nodes
   - Configures MCA parameters
10. **Verification**: Tests all installed components

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

```bash
# Add Homebrew to PATH
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

# Restart Slurm services
sudo killall slurmctld slurmd
sudo slurmctld  # On master only
sudo slurmd     # On all nodes
```

### OpenMPI Issues

```bash
# Test MPI locally first
mpirun -np 2 hostname

# Check network connectivity
ping worker1
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