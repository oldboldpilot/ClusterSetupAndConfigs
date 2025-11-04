# Cluster Setup Deployment Guide

## Overview

This script automates the setup of a Slurm/OpenMPI cluster across multiple nodes. It can configure both the master node and all worker nodes automatically with a single command.

## Prerequisites

- **Python 3.14** (via Homebrew)
- **uv** package manager
- **Network access** to all cluster nodes
- **Sudo access** on all nodes (with password)
- **YAML configuration file** with cluster topology

## Critical Requirements

### 1. Run from ANY Node (Master or Worker)

**The script can be executed from ANY node in your cluster!**

The script automatically detects which node it's running on by checking all local network interfaces against the master/worker IPs in the config file.

- ✅ **If run from master**: Automatically sets up all worker nodes via SSH
- ✅ **If run from worker**: Automatically sets up master AND all other worker nodes via SSH
- 🔍 **Auto-Detection**: Uses `ip addr` to find all local IPs and match against config

**Node Detection Process:**
1. Script reads master_ip and worker_ips from config
2. Checks all network interfaces with `ip addr show`
3. Compares found IPs: "Am I the master? Or which worker am I?"
4. Creates list of "other nodes" (all nodes EXCEPT current one)
5. Sets up all other nodes automatically

**Example:**
- Cluster: master=192.168.1.147, workers=[192.168.1.139, 192.168.1.96, 192.168.1.136]
- You run from worker 192.168.1.136
- Script detects: "I'm worker 136"
- Script sets up: 192.168.1.147 (master), 192.168.1.139 (worker), 192.168.1.96 (worker)

### 2. Multi-OS Support

**Supported Operating Systems:**
- Ubuntu / Debian → uses `apt-get`
- Red Hat Enterprise Linux (RHEL) → uses `dnf`
- CentOS → uses `dnf`
- Fedora → uses `dnf`
- WSL2 with any of the above

The script automatically detects the OS on each node and uses the appropriate package manager.

### 3. Check Your Node (Optional)

To see which node you're on:

```bash
# Check your local IP addresses
ip addr show | grep "inet "

# Example output:
#   inet 127.0.0.1/8 scope host lo
#   inet 192.168.1.136/24 brd 192.168.1.255 scope global eth0
#   inet 192.168.1.138/24 brd 192.168.1.255 scope global eth1
```

The script will automatically detect your node, but this is useful for verification.

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

Create a YAML file (e.g., `cluster_config.yaml`). The script supports two formats:

**Simple Format:**
```yaml
master: 192.168.1.10
workers:
  - 192.168.1.11
  - 192.168.1.12
username: your_username
```

**Extended Format (with OS information - Recommended for Multi-OS):**
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
    os: redhat  # Red Hat worker - script will use dnf instead of apt-get
    name: worker2-redhat
  - ip: 192.168.1.13
    os: ubuntu
    name: worker3
username: your_username
```

Both formats work identically. The extended format is recommended for:
- Multi-OS clusters (Ubuntu + Red Hat)
- Better documentation
- Easier identification of nodes

**Note:** The `os` field is for documentation only. The script automatically detects the actual OS on each node during setup.

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

### On Current Node (Where You Run It)

1. **Node Detection**: Identifies which node it's running on (master or which worker)
2. **OS Detection**: Identifies Ubuntu/Debian or Red Hat/CentOS/Fedora
3. **Package Manager Selection**: Automatically uses apt-get or dnf
4. **Homebrew Installation**: Installs package manager if not present
5. **SSH Setup**: Configures SSH server and client with OS-appropriate packages
   - Ubuntu: `openssh-client`, `openssh-server`
   - Red Hat: `openssh-clients`, `openssh-server`
6. **SSH Key Distribution**: Generates keys and copies to all OTHER nodes using sshpass
7. **Hosts File**: Updates `/etc/hosts` with cluster node names
8. **Slurm Installation**: Installs via Homebrew with OS-appropriate package
   - Ubuntu: `slurm-wlm`
   - Red Hat: `slurm`
9. **OpenMPI Installation**: Installs via Homebrew
10. **OpenMP Installation**: Installs libomp for thread-level parallelism
11. **Slurm Configuration**: Creates slurm.conf, slurmdbd.conf, cgroup.conf (on master)
12. **OpenMPI Configuration**: Creates **three hostfiles** with all nodes:
    - `~/.openmpi/hostfile` - Standard (4 slots/node)
    - `~/.openmpi/hostfile_optimal` - Recommended (1 slot/node) ⭐
    - `~/.openmpi/hostfile_max` - Maximum (auto-detected cores/node)
13. **Other Node Setup**: SSHs to each other node and runs complete setup remotely

### On Other Nodes (Automatic Remote Setup)

**When run from master:** Sets up all workers
**When run from worker:** Sets up master AND all other workers

The script automatically:

1. Copies the setup script and config to each other node
2. Creates a wrapper script for sudo password handling
3. SSHs to the other node and executes the full setup remotely in non-interactive mode
4. Monitors progress and reports any errors in real-time

Each other node receives:
- OS detection (Ubuntu vs Red Hat)
- Package manager selection (apt-get vs dnf)
- Homebrew installation
- SSH configuration (with `--non-interactive` flag to skip prompts)
- Slurm configuration (master or worker role depending on node)
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
# Test locally (should work)
mpirun -np 4 hostname

# Test across cluster (may hang due to PRRTE/firewall issues)
mpirun -np 4 --hostfile ~/.openmpi/hostfile hostname
```

### OpenMPI 5.x PRRTE Troubleshooting

**If MPI hangs when running across cluster nodes**, this is likely due to PRRTE port/firewall issues.

#### What is PRRTE?

PRRTE (PMIx Reference Runtime Environment) is the process management system used by OpenMPI 5.x:
- Replaces the older ORTE system from OpenMPI 4.x
- Requires bidirectional network communication between nodes
- Uses multiple TCP ports, not just SSH port 22
- Commands: `prte` (start DVM), `prted` (daemon), `prun` (run in DVM)

#### Verify PRRTE Installation

```bash
# Check PRRTE is installed
prte --version  # Should show: prte (PRRTE) 3.0.x
prun --version  # Should show: prun (PRRTE) 3.0.x

# Check OpenMPI MCA configuration
cat ~/.openmpi/mca-params.conf
```

Expected configuration (automatically created by script):
```
btl = ^openib
btl_tcp_if_include = 192.168.1.0/24  # Your network range

# Port configuration for firewall-friendly operation
btl_tcp_port_min_v4 = 50000
oob_tcp_port_range = 50100-50200
```

#### Port Requirements

OpenMPI 5.x + PRRTE requires these ports open on **all nodes**:
- **Port 22**: SSH (for initial connection)
- **Port 50000+**: BTL TCP communication (message passing)
- **Ports 50100-50200**: OOB TCP (out-of-band, for PRRTE daemon communication)

#### Firewall Configuration

If you have ufw enabled:
```bash
# Check firewall status on all nodes
sudo ufw status

# If active, allow MPI ports (on all nodes)
sudo ufw allow 50000:50200/tcp comment 'OpenMPI PRRTE'
sudo ufw reload
```

For WSL specifically:
- WSL port forwarding only forwards SSH (port 22) by default
- Windows Firewall may also need configuration
- This is a known limitation that can prevent cross-cluster MPI

#### Debug MPI Hanging Issues

```bash
# Run with verbose debugging to see where it hangs
timeout 30 mpirun -np 2 --host master,worker1 \
  --mca btl_base_verbose 20 \
  --mca oob_base_verbose 10 \
  hostname 2>&1 | tee mpi_debug.log

# Check if SSH works (should succeed)
ssh worker1 hostname

# Check if prted exists on workers
ssh worker1 "which prted"

# Check network connectivity
ping -c 3 worker1

# Check which ports are listening
ss -tlnp | grep -E '50000|50100'
```

#### Workarounds

If PRRTE-based MPI continues to hang:

**Option 1: Use pdsh for parallel execution** (Recommended for embarrassingly parallel tasks)
```bash
brew install pdsh
pdsh -w 192.168.1.[147,137,96] hostname
pdsh -w worker[1-2] 'python3 my_script.py'
```

**Option 2: Use Slurm's srun** (Best for true MPI programs)
```bash
srun -N2 --mpi=pmix hostname
srun -N2 --mpi=pmix ./my_mpi_program
```

**Option 3: Try OpenMPI 4.x** (Uses older ORTE, less port-dependent)
```bash
brew uninstall open-mpi
brew install open-mpi@4
```

#### WSL-Specific Issues and SOLUTION

**Problem**: Windows port forwarding to WSL only covers port 22 (SSH), not MPI ports (50000-50200), causing PRRTE daemon communication to hang. Additionally, WSL's default NAT mode isolates it from other cluster nodes.

**SOLUTION**:

**Step 0: Enable WSL Mirrored Mode Networking** (REQUIRED FIRST):

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
- Default NAT mode gives WSL an internal IP (e.g., 172.x.x.x) that's not accessible from other nodes
- Mirrored mode gives WSL the same IP as your Windows host on the physical network
- This allows other cluster nodes to communicate with the WSL node directly
- Without mirrored mode, firewall rules alone won't fix cluster communication

**Step 1: Configure Windows Firewall** (Recommended, persists across reboots):
```powershell
# Open PowerShell as Administrator on Windows
cd Z:\PycharmProjects\ClusterSetupAndConfigs
.\configure_wsl_firewall.ps1
```

This creates Windows Firewall rules allowing inbound/outbound traffic on ports 50000-50200.

**Step 2 (Optional): Setup Port Forwarding** (Only if external access needed):
```powershell
# For external machines to access WSL cluster
.\setup_wsl_port_forwarding.ps1

# To remove port forwarding
.\setup_wsl_port_forwarding.ps1 -Remove
```

**Important Notes**:
- Firewall rules persist across reboots
- Port forwarding rules are cleared on Windows restart
- If WSL IP changes, re-run the port forwarding script
- The cluster setup script will automatically detect WSL and display these instructions

**After running the PowerShell scripts**, test MPI:
```bash
# In WSL, test cross-cluster MPI
mpirun -np 6 --hostfile ~/.openmpi/hostfile hostname
```

**Alternative workarounds** (if PowerShell solution not available):
- Use Slurm's srun (best for MPI programs)
- Use pdsh (best for embarrassingly parallel tasks)

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

- **Slurm configs**: `/etc/slurm/slurm.conf`, `/etc/slurm/cgroup.conf`
- **OpenMPI hostfiles**: 
  - `~/.openmpi/hostfile` - Standard (4 slots/node)
  - `~/.openmpi/hostfile_optimal` - Recommended (1 slot/node) ⭐
  - `~/.openmpi/hostfile_max` - Maximum (auto-detected cores/node)
- **OpenMPI MCA params**: `~/.openmpi/mca-params.conf` (includes port configuration)
- **OpenMPI binary**: `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8/bin/mpirun`
- **OpenMPI prefix**: `/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8`
- **SSH keys**: `~/.ssh/id_rsa`, `~/.ssh/id_rsa.pub`
- **Slurm spool**: `/var/spool/slurm/ctld` (master), `/var/spool/slurm/d` (all nodes)
- **Slurm logs**: `/var/log/slurm/`

## Security Notes

- Passwords are handled securely via getpass (not echoed to terminal)
- SSH keys provide passwordless access after initial setup
- sudo commands use stdin piping to avoid command-line exposure
- Temporary password files are created securely and cleaned up

## For AI Agents

See `CLAUDE.md` and `copilot-instructions.md` for detailed instructions on:
- WSL-specific issues and solutions
- uv package manager configuration
- Python 3.14 requirements
- Common troubleshooting scenarios
