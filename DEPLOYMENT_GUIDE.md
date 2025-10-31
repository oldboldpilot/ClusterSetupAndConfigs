# Cluster Setup Deployment Guide

## Overview

This script automates the setup of a Slurm/OpenMPI cluster across multiple nodes. It can configure both the master node and all worker nodes automatically with a single command.

## Prerequisites

- **Python 3.13** (via Homebrew)
- **uv** package manager
- **Network access** to all cluster nodes
- **Sudo access** on all nodes (with password)
- **YAML configuration file** with cluster topology

## Critical Requirements

### 1. Run from the Master Node

**The script MUST be executed from the master node specified in your YAML configuration.**

The script automatically detects which node it's running on by checking local IP addresses against the `master_ip` in the config file.

- ✅ **If run from master**: Automatically sets up all worker nodes via SSH
- ⚠️ **If run from worker**: Only configures the local worker node

### 2. Verify Your Node

Before running the script, verify you're on the correct node:

```bash
# Check your local IP addresses
ip addr show | grep "inet "

# Example output:
#   inet 127.0.0.1/8 scope host lo
#   inet 192.168.1.147/24 brd 192.168.1.255 scope global eth0
```

Compare the output with the `master_ip` in your configuration file. You should see the master IP in the list.

## Quick Start

### 1. Setup uv Environment (One-time setup)

```bash
# Navigate to project directory
cd /path/to/ClusterSetupAndConfigs

# Set environment variable for WSL
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Sync dependencies
uv sync
```

### 2. Create Configuration File

Create a YAML file (e.g., `cluster_config.yaml`):

```yaml
master_ip: "192.168.1.147"
worker_ips:
  - "192.168.1.137"
  - "192.168.1.96"
username: "your_username"
```

### 3. Run the Setup

#### Option A: Command Line Interface

```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --config cluster_config.yaml --password
```

You'll be prompted to enter the password for worker nodes. The script will:

1. Install Homebrew (if needed)
2. Configure SSH
3. Copy SSH keys to all worker nodes
4. Install Slurm and OpenMPI on master
5. Configure Slurm and OpenMPI on master
6. **Automatically SSH to each worker and run the same setup remotely**
   - Worker nodes run in non-interactive mode (no prompts)
   - Password is securely piped via temporary files
   - Real-time output shows progress on each worker
7. Verify installations

#### Option B: Terminal UI

```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup_ui.py
```

The UI will:
- Let you browse and select the YAML config file
- Prompt for the password (masked input)
- Show real-time logs of the setup process
- Display a completion banner when finished

## What the Script Does

### On Master Node

1. **Homebrew Installation**: Installs package manager if not present
2. **SSH Setup**: Configures SSH server and client
3. **SSH Key Distribution**: Generates keys and copies to all workers using sshpass
4. **Hosts File**: Updates `/etc/hosts` with cluster node names
5. **Slurm Installation**: Installs via Homebrew
6. **OpenMPI Installation**: Installs via Homebrew
7. **Slurm Configuration**: Creates slurm.conf, slurmdbd.conf, cgroup.conf
8. **OpenMPI Configuration**: Creates hostfile with all nodes
9. **Worker Setup**: SSHs to each worker and runs complete setup remotely

### On Worker Nodes (Automatic)

When run from master, the script automatically:

1. Copies the setup script and config to each worker
2. Creates a wrapper script for sudo password handling
3. SSHs to the worker and executes the full setup remotely in non-interactive mode
4. Monitors progress and reports any errors in real-time

Each worker receives:
- Homebrew installation
- SSH configuration (with `--non-interactive` flag to skip prompts)
- Slurm worker configuration
- OpenMPI configuration
- Hosts file updates
- Automatic confirmation of sudo access requirements

## Completion Indicators

### Command Line

When complete, you'll see:

```
============================================================
LOCAL NODE SETUP COMPLETED SUCCESSFULLY
============================================================
Setup completed for master node
Worker node setup completed
All operations completed successfully
```

### Terminal UI

The UI will display:
- Green "SUCCESS" banner
- "Setup completed successfully!" message
- Enabled "Start Setup" button (for re-running if needed)
- "Exit" button to close the application

## Troubleshooting

### Issue: Script detects WORKER instead of MASTER

**Symptom**: Output shows "Current node is: WORKER" when you expected MASTER

**Cause**: The local IP addresses don't include the master_ip from config

**Solution**:
1. Check your current IPs: `ip addr show | grep inet`
2. Verify the master_ip in your YAML config matches one of them
3. Update the config or run from the correct node

**Debug Output**: The script will show:
```
DEBUG: hostname='...', local_ip='...', master_ip='...'
DEBUG: Found IPs on interfaces: [...]
```

### Issue: sudo permission errors

**Symptom**: `E: Could not open lock file` or `sudo: no password was provided`

**Solution**: The script now uses secure password piping to sudo. If issues persist:
1. Ensure your user has sudo privileges: `sudo -l`
2. Check if another apt/dpkg process is running: `ps aux | grep apt`
3. Wait for other processes to finish and retry

### Issue: Slurm commands not found after installation

**Symptom**: `sinfo: command not found`

**Solution**: Add Homebrew to PATH:
```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"' >> ~/.bashrc
```

### Issue: Slurm services fail to start (24.11+)

**Symptoms**:
- `Incorrect permissions on state save loc: /var/spool/slurm/ctld`
- `The option "CgroupAutomount" is defunct`
- `Unable to determine this slurmd's NodeName`
- `sinfo` returns "Unable to contact slurm controller"

**Cause**: Slurm 24.11+ has breaking changes with deprecated options and stricter permission requirements.

**Solution**: The latest version of the script (October 2025+) automatically handles these issues:
- ✅ Removes deprecated `CgroupAutomount` from cgroup.conf
- ✅ Uses actual system hostname instead of hardcoded "master"
- ✅ Sets proper directory ownership to `slurm:slurm` user/group
- ✅ Uses systemctl to manage services
- ✅ Worker nodes automatically receive the same fixes via SSH

If you installed before these fixes, manually apply them:
```bash
# Fix cgroup.conf
sudo sed -i '/CgroupAutomount/d' /etc/slurm/cgroup.conf

# Fix directory permissions
sudo chown -R slurm:slurm /var/spool/slurm/ctld
sudo chown -R slurm:slurm /var/spool/slurm/d
sudo chown -R slurm:slurm /var/log/slurm

# Update hostname in slurm.conf (replace ACTUAL-HOSTNAME with output of `hostname`)
hostname
sudo nano /etc/slurm/slurm.conf  # Update NodeName and SlurmctldHost

# Restart services
sudo systemctl restart slurmctld  # Master only
sudo systemctl restart slurmd     # All nodes
```

### Issue: WSL symlink errors with uv

**Symptom**: `Operation not permitted (os error 1)`

**Solution**: Always set the environment variable before using uv:
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
```

This places the venv in your Linux home directory instead of the Windows filesystem.

## Testing the Cluster

After setup completes, verify the cluster is working:

### Test SSH

```bash
# From master, SSH to workers without password
ssh worker1
ssh worker2
```

### Test Slurm

```bash
# Add Homebrew to PATH
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"

# Check cluster status
sinfo

# Run a test job
srun -N2 hostname
```

### Test OpenMPI

```bash
# Run MPI hello world across nodes
mpirun -np 4 --hostfile ~/.openmpi/hostfile hostname
```

## Advanced Usage

### Re-running Setup

It's safe to re-run the setup script. It will:
- Skip already installed components
- Update configuration files
- Reconfigure services

### Manual Worker Setup

If automatic worker setup fails, you can:

1. Copy the script to a worker:
   ```bash
   scp cluster_setup.py worker1:~/
   scp cluster_config.yaml worker1:~/
   ```

2. SSH to the worker and run locally:
   ```bash
   ssh worker1
   python cluster_setup.py --config cluster_config.yaml --password
   ```

### Debugging

Enable detailed output by checking the debug messages:

```python
# In cluster_setup.py, the script outputs:
# DEBUG: hostname='...', local_ip='...', master_ip='...'
# DEBUG: Found IPs on interfaces: [...]
```

## File Locations

After setup, key files are located at:

- **Slurm configs**: `~/.slurm/slurm.conf`, `~/.slurm/slurmdbd.conf`
- **OpenMPI hostfile**: `~/.openmpi/hostfile`
- **SSH keys**: `~/.ssh/id_rsa`, `~/.ssh/id_rsa.pub`
- **Cluster scripts**: `/usr/local/bin/start-slurm.sh` (with sudo)

## Security Notes

- Passwords are handled securely via getpass (not echoed to terminal)
- SSH keys provide passwordless access after initial setup
- sudo commands use stdin piping to avoid command-line exposure
- Temporary password files are created securely and cleaned up

## For AI Agents

See `CLAUDE.md` and `copilot-instructions.md` for detailed instructions on:
- WSL-specific issues and solutions
- uv package manager configuration
- Python 3.13 requirements
- Common troubleshooting scenarios
