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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
