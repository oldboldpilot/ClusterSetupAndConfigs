# Usage Examples for Cluster Setup Script

## Important: Run from ANY Node!

**The script can run from ANY node in your cluster** - master or any worker! It automatically detects which node it's running on and sets up all OTHER nodes.

### How Node Detection Works

```bash
# Check your local IP addresses
ip addr show | grep "inet "

# Example output on worker node 192.168.1.136:
#   inet 127.0.0.1/8 scope host lo
#   inet 192.168.1.136/24 brd 192.168.1.255 scope global eth0
#   inet 192.168.1.138/24 brd 192.168.1.255 scope global eth1
```

When you run the script, it will show:
```
DEBUG: hostname='worker-node', local_ip='192.168.1.138', master_ip='192.168.1.147'
DEBUG: Found IPs on interfaces: ['127.0.0.1', '192.168.1.136', '192.168.1.138']
Current node is: WORKER (192.168.1.136)
Will setup these other nodes: ['192.168.1.147', '192.168.1.139', '192.168.1.96']
              ← Script detects it's on worker and will setup master + other workers
```

### Run from Master vs Worker

**From Master Node:**
- Detects: "I'm the master"
- Sets up: All worker nodes

**From Worker Node:**
- Detects: "I'm worker X"
- Sets up: Master node AND all other workers (excluding itself)

## Basic Setup

### Example 1: Simple 3-Node Cluster

Create a configuration file `cluster_config.yaml` (either format works):

**Simple Format:**
```yaml
master: 192.168.1.10
workers:
  - 192.168.1.11
  - 192.168.1.12
username: myuser  # optional, defaults to current user
```

**Extended Format (with OS information - Recommended):**
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
    os: redhat  # Red Hat worker - will use dnf
    name: worker2-redhat
username: myuser
```

**Run from ANY node** with automatic setup:
```bash
# SSH to ANY node (master or any worker)
ssh myuser@192.168.1.11  # Could be 10, 11, or 12

export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --config cluster_config.yaml --password
# Enter password when prompted - script will:
# 1. Detect which node it's on
# 2. Setup all OTHER nodes automatically
# 3. Use apt-get on Ubuntu nodes, dnf on Red Hat nodes
```

### Example 2: Larger Cluster with 5 Workers

Configuration file `large_cluster.yaml`:

**Simple Format:**
```yaml
master: 10.0.0.10
workers:
  - 10.0.0.11
  - 10.0.0.12
  - 10.0.0.13
  - 10.0.0.14
  - 10.0.0.15
username: admin
```

**Extended Format (Multi-OS Cluster):**
```yaml
master:
  ip: 10.0.0.10
  os: ubuntu wsl2
  name: master-node
workers:
  - ip: 10.0.0.11
    os: ubuntu
    name: worker1-ubuntu
  - ip: 10.0.0.12
    os: ubuntu
    name: worker2-ubuntu
  - ip: 10.0.0.13
    os: redhat  # Red Hat workers
    name: worker3-redhat
  - ip: 10.0.0.14
    os: redhat
    name: worker4-redhat
  - ip: 10.0.0.15
    os: ubuntu
    name: worker5-ubuntu
username: admin
```

**Note:** Script automatically detects OS on each node and uses:
- Ubuntu/Debian nodes: `apt-get` for packages
- Red Hat/CentOS/Fedora nodes: `dnf` for packages
```

```bash
# Can be run from ANY node (master or any worker)
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --config large_cluster.yaml --password

# Example: Run from worker3-redhat (10.0.0.13)
# Script will detect it's on worker3 and setup: master + worker1,2,4,5
```

### Example 3: Local Testing with Localhost

Configuration file `local_test.yaml`:

**Simple Format:**
```yaml
master: localhost
workers:
  - 127.0.0.2
  - 127.0.0.3
username: testuser
```

**Extended Format:**
```yaml
master:
  ip: localhost
  os: ubuntu wsl2
  name: test-master
workers:
  - ip: 127.0.0.2
    os: ubuntu
    name: test-worker1
  - ip: 127.0.0.3
    os: ubuntu
    name: test-worker2
username: testuser
```

```bash
# For single-machine testing
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --config local_test.yaml
```

### Example 4: Running from Worker Node

You can run the setup from ANY worker node, and it will setup master + all other workers:

```bash
# SSH to any worker (e.g., 192.168.1.12)
ssh myuser@192.168.1.12

# Clone the repo on this worker
git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
cd ClusterSetupAndConfigs

# Run the setup - it will detect it's on worker2 and setup master + worker1
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --config cluster_config.yaml --password

# Output will show:
# Current node is: WORKER (192.168.1.12)
# Will setup these other nodes: ['192.168.1.10', '192.168.1.11']
```

### Example 5: Manual Setup (Without Automatic Other-Node Setup)

If you prefer to setup each node manually without providing a password:

```bash
# On any node - run without --password flag
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --config cluster_config.yaml
# This will only setup the current node, not other nodes

# Then manually on each other node
ssh next-node
cd /path/to/ClusterSetupAndConfigs
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --config cluster_config.yaml
```

## Step-by-Step Workflow

### 1. Prepare Your Cluster Nodes

Ensure all nodes have:
- **Supported OS**: Ubuntu/Debian OR Red Hat/CentOS/Fedora (WSL2 supported)
- Network connectivity
- Same username on all nodes
- Sudo access
- Script automatically detects OS and uses apt-get or dnf

### 2. Create Configuration File

Create `cluster_config.yaml`:

```yaml
master: 192.168.1.10
workers:
  - 192.168.1.11
  - 192.168.1.12
username: myuser
```

### 3. Run Automatic Setup (Recommended)

```bash
# SSH into master node
ssh user@192.168.1.10

# Clone the repository
git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
cd ClusterSetupAndConfigs

# Run the setup script with --password flag for automatic full cluster setup
python cluster_setup.py --config cluster_config.yaml --password
# Enter password when prompted
```

The script will **automatically**:
1. Install Homebrew on master
2. Install and configure SSH on master
3. Generate SSH keys on master
4. **Copy SSH keys to all worker nodes**
5. **Connect to each worker via SSH**
6. **Run full setup on each worker remotely**
7. Configure /etc/hosts on all nodes
8. Install Slurm and OpenMPI on all nodes
9. Start Slurm controller (slurmctld) on master
10. Start Slurm daemon (slurmd) on all nodes
11. Create OpenMPI configuration on all nodes

**That's it!** Your entire cluster is now configured with a single command.

### 3b. Manual Setup (Alternative)

If automatic setup is not desired or fails:

```bash
# On master node
python cluster_setup.py --config cluster_config.yaml

# Manually copy SSH key to workers
# Then on each worker node:
python cluster_setup.py --config cluster_config.yaml
```

### 4. Verify Setup

On the master node:

```bash
# Check Slurm cluster status
sinfo

# Should show output like:
# PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST
# all*      up     infinite       3   idle master,worker1,worker2

# Check detailed node information
scontrol show nodes

# Test SSH connectivity
ssh worker1 hostname
ssh worker2 hostname

# Test MPI
mpirun -np 4 -hostfile ~/.openmpi/hostfile hostname
```

### 5. Submit Test Jobs

#### Slurm Job Examples

```bash
# Simple command
srun -N 2 hostname

# Interactive job
salloc -N 2

# Batch job
cat > test_job.sh << 'EOF'
#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=2
#SBATCH --time=00:10:00
#SBATCH --job-name=test_job

echo "Running on nodes:"
srun hostname
EOF

sbatch test_job.sh
```

#### OpenMPI Job Examples

```bash
# Simple hostname test
mpirun -np 4 -hostfile ~/.openmpi/hostfile hostname

# MPI Hello World (if you have one compiled)
mpirun -np 8 -hostfile ~/.openmpi/hostfile ./mpi_hello_world

# Using specific hosts
mpirun -np 4 -host master,worker1,worker2 hostname
```

## Advanced Configurations

### Custom Slurm Configuration

After initial setup, you can customize `/etc/slurm/slurm.conf`:

```bash
sudo nano /etc/slurm/slurm.conf

# Make your changes, then restart Slurm
sudo killall slurmctld slurmd
sudo slurmctld  # On master
sudo slurmd     # On all nodes
```

### Custom OpenMPI Hostfile

Edit `~/.openmpi/hostfile` to adjust slots per node:

```bash
192.168.1.10 slots=8 max_slots=16
192.168.1.11 slots=8 max_slots=16
192.168.1.12 slots=8 max_slots=16
```

### Adding New Nodes

To add a new worker node:

1. Update `/etc/hosts` on all existing nodes
2. Run the setup script on the new node
3. Update `/etc/slurm/slurm.conf` on all nodes
4. Update `~/.openmpi/hostfile` on all nodes
5. Restart Slurm services

```bash
# Update cluster_config.yaml to include the new worker:
# master: 192.168.1.10
# workers:
#   - 192.168.1.11
#   - 192.168.1.12
#   - 192.168.1.13

# On master node, re-run setup to update configuration:
python cluster_setup.py --config cluster_config.yaml --password

# Or manually on the new node:
python cluster_setup.py --config cluster_config.yaml

# Then restart Slurm services:
sudo scontrol reconfigure
```

## Troubleshooting Common Issues

### Issue: Slurm nodes show as "down"

```bash
# Check Slurm daemon is running
ps aux | grep slurmd

# Check logs
tail -f /var/log/slurm/slurmd.log

# Restart daemon
sudo killall slurmd
sudo slurmd
```

### Issue: SSH asks for password

```bash
# Verify key is in authorized_keys
cat ~/.ssh/authorized_keys | grep $(cat ~/.ssh/id_rsa.pub | cut -d' ' -f2)

# Check permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Issue: MPI jobs hang

```bash
# Check network connectivity
ping worker1

# Test SSH without password
ssh worker1 'echo test'

# Try with verbose output
mpirun --mca btl_base_verbose 30 -np 2 hostname
```

### Issue: Homebrew installation fails

```bash
# Install from apt instead
sudo apt-get update
sudo apt-get install -y slurm-wlm openmpi-bin

# The script will fall back to apt automatically
```

### Issue: Script detects WORKER instead of MASTER

**Symptom**: Output shows "Current node is: WORKER" when you're on the master node

**Diagnosis**:
```bash
# Check the debug output from the script:
# DEBUG: hostname='...', local_ip='...', master_ip='...'
# DEBUG: Found IPs on interfaces: [...]

# Manually check your IPs
ip addr show | grep "inet "
```

**Solution**:
1. Verify the master IP in your config file matches one of your local IPs
2. If IPs don't match, update the config file with the correct master IP
3. If you're not on the master node, SSH to the correct node and run from there

**Example**:
```bash
# Config says master IP: "192.168.1.10"
# But your IPs are: ['127.0.0.1', '172.25.40.179', '10.1.96.192']
# → master IP not found in local IPs

# Solution: Either update config or run from 192.168.1.10
ssh 192.168.1.10
cd /path/to/ClusterSetupAndConfigs
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_setup.py --config cluster_config.yaml --password
```

### Issue: sudo password errors

**Symptom**: `sudo: no password was provided` or permission denied

**Solution**: The script now handles this automatically via secure stdin piping. If issues persist:
```bash
# Verify sudo access
sudo -l

# Check if another package manager process is running
ps aux | grep -E 'apt|dpkg'

# Wait for other processes to complete, then retry
```

## Performance Tuning

### For CPU-bound workloads:

1. Adjust slots in OpenMPI hostfile to match CPU cores
2. Configure Slurm with appropriate CPUs per node
3. Use `--cpus-per-task` in Slurm submissions

### For memory-bound workloads:

1. Set appropriate memory limits in Slurm
2. Use `--mem` or `--mem-per-cpu` in job submissions

### For I/O-intensive workloads:

1. Consider NFS or shared filesystem
2. Use local scratch directories
3. Optimize data locality

## Security Considerations

1. **Firewall**: Ensure required ports are open:
   - SSH: 22
   - Slurm: 6817 (slurmctld), 6818 (slurmd)
   - MPI: Various (typically high ports)

2. **SSH Keys**: Protect private keys with passphrases in production

3. **User Isolation**: Configure proper user permissions and cgroups

4. **Network**: Use private network for cluster communication

## References

- [Slurm Documentation](https://slurm.schedmd.com/)
- [OpenMPI Documentation](https://www.open-mpi.org/doc/)
- [Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux)
