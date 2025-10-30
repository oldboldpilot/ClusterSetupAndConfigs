# ClusterSetupAndConfigs

Automated cluster setup and configuration scripts for Slurm and OpenMPI on Ubuntu/WSL systems using Python 3.13 and uv.

## Features

- **Pure Python Implementation**: Written entirely in Python 3.13 for easy customization and maintenance
- **Automated Installation**: Installs and configures Homebrew, Slurm, OpenMPI, and OpenSSH
- **Cluster-Ready**: Configures master and worker nodes for distributed computing
- **Ubuntu/WSL Support**: Works on both native Ubuntu Linux and Windows Subsystem for Linux (WSL)

## Requirements

- Python 3.13+
- Ubuntu Linux or WSL with Ubuntu installed
- Sudo access on all nodes
- Network connectivity between all cluster nodes

## Installation

### Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
cd ClusterSetupAndConfigs

# Create a virtual environment and install dependencies
uv venv --python 3.13
source .venv/bin/activate  # On Windows WSL: source .venv/bin/activate
```

### Manual Installation

```bash
# Ensure Python 3.13 is installed
python3.13 --version

# Clone the repository
git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
cd ClusterSetupAndConfigs

# Make the script executable
chmod +x cluster_setup.py
```

## Usage

### Basic Usage

Run the script on each node in your cluster (master and all workers):

```bash
python cluster_setup.py --master <master_ip> --workers <worker_ip1> <worker_ip2> ...
```

### Example

For a cluster with:
- Master node: 192.168.1.10
- Worker nodes: 192.168.1.11, 192.168.1.12

```bash
# Run on master node
python cluster_setup.py --master 192.168.1.10 --workers 192.168.1.11 192.168.1.12

# Run on each worker node
python cluster_setup.py --master 192.168.1.10 --workers 192.168.1.11 192.168.1.12
```

### Advanced Options

```bash
# Specify a custom username
python cluster_setup.py --master 192.168.1.10 --workers 192.168.1.11 192.168.1.12 --username myuser

# View help
python cluster_setup.py --help
```

## What the Script Does

The cluster setup script performs the following operations:

1. **Homebrew Installation**: Installs Homebrew package manager on Ubuntu/WSL
2. **SSH Setup**: 
   - Installs OpenSSH client and server
   - Generates SSH keys for passwordless authentication
   - Configures SSH for cluster communication
3. **Hosts File Configuration**: Updates `/etc/hosts` with all cluster node information
4. **Slurm Installation**: Installs Slurm workload manager via Homebrew or apt
5. **OpenMPI Installation**: Installs OpenMPI for parallel computing
6. **Slurm Configuration**: 
   - Creates necessary directories (`/var/spool/slurm`, `/var/log/slurm`, etc.)
   - Generates `slurm.conf` with cluster topology
   - Configures cgroup support
   - Starts Slurm services (slurmctld on master, slurmd on all nodes)
7. **OpenMPI Configuration**: 
   - Creates MPI hostfile with all cluster nodes
   - Configures MCA parameters
8. **Verification**: Tests all installed components

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

### SSH Issues

If passwordless SSH is not working:
```bash
# Ensure the public key is in authorized_keys on all nodes
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Slurm Service Issues

```bash
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

## API Documentation

The `cluster_setup.py` module provides a comprehensive API for automated cluster configuration. All functions include proper Python type annotations for type safety and better IDE support.

### ClusterSetup Class

Main class for cluster setup and configuration with full type annotations.

#### Constructor

```python
def __init__(
    self, 
    master_ip: str, 
    worker_ips: List[str], 
    username: Optional[str] = None
) -> None
```

**Parameters:**
- `master_ip` (str): IPv4 address of the master node
- `worker_ips` (List[str]): List of IPv4 addresses for worker nodes
- `username` (Optional[str]): Username for cluster operations (defaults to current user)

**Attributes:**
- `master_ip` (str): Master node IP address
- `worker_ips` (List[str]): Worker node IP addresses
- `all_ips` (List[str]): Combined list of all node IPs
- `username` (str): Username for cluster operations
- `is_master` (bool): Whether current node is the master node

#### Core Methods

##### run_command
```python
def run_command(
    self, 
    command: str, 
    check: bool = True, 
    shell: bool = True
) -> subprocess.CompletedProcess
```

Execute a shell command and return the result.

**Parameters:**
- `command` (str): Shell command to execute
- `check` (bool): Whether to raise exception on non-zero exit code (default: True)
- `shell` (bool): Whether to run command through shell (default: True)

**Returns:**
- `subprocess.CompletedProcess`: Command execution result object

**Raises:**
- `CalledProcessError`: If command fails and check=True

**Note:** When check=False, the method always returns a CompletedProcess even on command failure (with non-zero returncode).

##### check_sudo_access
```python
def check_sudo_access(self) -> bool
```

Check if the current user has sudo access.

**Returns:**
- `bool`: True if user has sudo access, False otherwise

#### Installation Methods

##### install_homebrew
```python
def install_homebrew(self) -> None
```

Install Homebrew package manager on Ubuntu/WSL. Checks if Homebrew is already installed and skips installation if present.

**Side Effects:**
- Installs system dependencies (build-essential, procps, curl, file, git)
- Installs Homebrew to `/home/linuxbrew/.linuxbrew`
- Updates PATH environment variable
- Adds Homebrew initialization to `~/.bashrc`

##### setup_ssh
```python
def setup_ssh(self) -> None
```

Setup OpenSSH client and server for cluster communication.

**Side Effects:**
- Installs openssh-client and openssh-server packages
- Starts and enables SSH service
- Generates RSA SSH key pair (4096 bits) if not present
- Creates `~/.ssh` directory with proper permissions (0700)

##### install_slurm
```python
def install_slurm(self) -> None
```

Install Slurm workload manager using Homebrew or apt as fallback.

**Side Effects:**
- Attempts installation via Homebrew first
- Falls back to apt installation if Homebrew fails
- Installs slurm-wlm and slurm-wlm-doc packages

##### install_openmpi
```python
def install_openmpi(self) -> None
```

Install OpenMPI for parallel computing using Homebrew or apt as fallback.

**Side Effects:**
- Attempts installation via Homebrew first
- Falls back to apt installation if Homebrew fails
- Installs openmpi-bin, openmpi-common, and libopenmpi-dev packages

#### Configuration Methods

##### configure_passwordless_ssh
```python
def configure_passwordless_ssh(self) -> None
```

Configure passwordless SSH authentication between cluster nodes.

**Side Effects:**
- Adds public key to `~/.ssh/authorized_keys`
- Creates SSH config file with StrictHostKeyChecking disabled
- Sets proper file permissions (0600)

**Note:** Users must manually copy the public key to all other nodes for full passwordless access.

##### configure_hosts_file
```python
def configure_hosts_file(self) -> None
```

Update `/etc/hosts` with cluster node information.

**Side Effects:**
- Backs up existing `/etc/hosts` to `/etc/hosts.backup`
- Adds entries for master and all worker nodes
- Assigns hostnames: master, worker1, worker2, etc.

**Requires:** Sudo access

##### configure_slurm
```python
def configure_slurm(self) -> None
```

Configure Slurm for the cluster with proper directory structure and configuration files.

**Side Effects:**
- Creates Slurm directories: `/var/spool/slurm`, `/var/log/slurm`, `/etc/slurm`
- Generates `slurm.conf` configuration file
- Generates `cgroup.conf` for resource management
- Starts slurmctld on master node
- Starts slurmd on all nodes

**Requires:** Sudo access

##### generate_slurm_conf
```python
def generate_slurm_conf(self) -> str
```

Generate Slurm configuration file content with cluster topology.

**Returns:**
- `str`: Complete slurm.conf file content

**Configuration includes:**
- Cluster name and controller host
- Scheduler configuration (backfill)
- Resource selection (cons_tres)
- Logging configuration
- Process tracking and task plugins
- MPI settings (pmix)
- Node definitions with CPU and memory specs
- Partition configuration

##### configure_openmpi
```python
def configure_openmpi(self) -> None
```

Configure OpenMPI with hostfile and MCA parameters.

**Side Effects:**
- Creates `~/.openmpi/hostfile` with all cluster nodes (4 slots each)
- Creates `~/.openmpi/mca-params.conf` with network settings
- Configures BTL settings for cluster networking

#### Utility Methods

##### verify_installation
```python
def verify_installation(self) -> None
```

Verify that all cluster components are installed correctly.

**Checks:**
- SSH version
- Slurm commands (sinfo, scontrol)
- OpenMPI commands (mpirun, mpicc)

**Output:** Prints verification status for each component

##### run_full_setup
```python
def run_full_setup(self) -> None
```

Execute the complete cluster setup process in proper sequence.

**Execution Order:**
1. Check sudo access
2. Install Homebrew
3. Setup SSH
4. Configure passwordless SSH
5. Configure hosts file
6. Install Slurm
7. Install OpenMPI
8. Configure Slurm
9. Configure OpenMPI
10. Verify installation

**Raises:**
- `Exception`: Any error during setup process (printed with traceback)

#### Private Methods

##### _is_current_node_master
```python
def _is_current_node_master(self) -> bool
```

Determine if the current node is the master node.

**Returns:**
- `bool`: True if current node is master, False otherwise

**Logic:** Compares local IP with master_ip or checks for localhost/127.0.0.1

### Module-level Functions

#### main
```python
def main() -> None
```

Main entry point for the cluster setup script with argument parsing.

**Command-line Arguments:**
- `--master` (required): IPv4 address of the master node
- `--workers` (required): Space-separated IPv4 addresses of worker nodes
- `--username` (optional): Username for cluster operations

**Validation:**
- Validates all IP addresses are in proper IPv4 format
- Exits with error code 1 if validation fails

**Usage Example:**
```bash
python cluster_setup.py --master 192.168.1.10 --workers 192.168.1.11 192.168.1.12
```

## Type Safety

This project uses comprehensive Python type annotations compatible with:
- **mypy**: Static type checker (verified with `mypy --strict`)
- **Python 3.13**: Latest Python version with enhanced typing features
- **Type hints**: All functions, methods, and parameters are fully typed

### Running Type Checks

```bash
# Install mypy
pip install mypy

# Run type checking
mypy cluster_setup.py --pretty --show-error-codes

# Expected output: Success: no issues found in 1 source file
```

### Imports and Type Annotations

The module uses the following type annotations:
```python
from typing import List, Dict, Optional
```

All code follows PEP 484 type hinting conventions and passes strict type checking without errors.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
