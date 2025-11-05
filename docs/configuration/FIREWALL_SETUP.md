# Firewall Configuration for HPC Cluster

## Overview

The config_template_manager now includes built-in firewall configuration for all cluster nodes. This ensures MPI communication ports (50000-50200) are open for data transfer.

## Usage

### Verify Current Firewall Status

```bash
cd /home/muyiwa/Development/ClusterSetupAndConfigs
uv run python cluster_modules/config_template_manager.py firewall verify
```

**Example Output:**
```
======================================================================
Firewall Status
======================================================================
oluwasanmiredhatserver (192.168.1.136):
  firewalld: 50000-50200/tcp
muyiwadroexperiments (192.168.1.139):
  ufw: 50000:50200/tcp ALLOW IN
olubuuntul1 (192.168.1.96):
  ufw: 50000:50200/tcp ALLOW IN
DESKTOP-3SON9JT (192.168.1.147):
  No firewall detected
======================================================================
```

### Configure Firewalls on All Nodes

```bash
# Configure MPI ports (50000-50200) on all nodes
uv run python cluster_modules/config_template_manager.py firewall configure

# Configure specific port range
uv run python cluster_modules/config_template_manager.py firewall configure --ports 50000-51000

# Configure specific nodes only
uv run python cluster_modules/config_template_manager.py firewall configure --nodes 192.168.1.136 192.168.1.139

# Configure UDP ports
uv run python cluster_modules/config_template_manager.py firewall configure --protocol udp
```

## Supported Firewall Types

### 1. firewalld (RedHat/Rocky/CentOS)

**Auto-detected command:**
```bash
sudo firewall-cmd --permanent --add-port=50000-50200/tcp
sudo firewall-cmd --reload
```

**Manual configuration:**
```bash
# On RedHat/Rocky Linux nodes
ssh node_ip
sudo firewall-cmd --permanent --add-port=50000-50200/tcp
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-ports
```

### 2. ufw (Ubuntu/Debian)

**Auto-detected command:**
```bash
sudo ufw allow 50000-50200/tcp
sudo ufw reload  # if ufw is active
```

**Manual configuration:**
```bash
# On Ubuntu nodes
ssh node_ip
sudo ufw allow 50000-50200/tcp

# Enable ufw if not already active (optional)
sudo ufw enable

# Verify
sudo ufw status verbose
```

### 3. Windows Firewall (WSL nodes)

WSL nodes require Windows Firewall configuration on the host system.

**PowerShell (Run as Administrator):**
```powershell
# Allow inbound connections on ports 50000-50200
New-NetFirewallRule -DisplayName "MPI Cluster - Inbound" `
  -Direction Inbound `
  -LocalPort 50000-50200 `
  -Protocol TCP `
  -Action Allow

# Allow outbound connections
New-NetFirewallRule -DisplayName "MPI Cluster - Outbound" `
  -Direction Outbound `
  -LocalPort 50000-50200 `
  -Protocol TCP `
  -Action Allow
```

See `WSL_FIREWALL_SETUP.md` for complete WSL firewall configuration.

## Port Requirements

### MPI Communication Ports

| Port Range | Purpose | Protocol |
|------------|---------|----------|
| 50000 | BTL TCP data transfer | TCP |
| 50100-50200 | OOB (PRRTE daemon) | TCP |

### Additional Ports (if using Slurm)

| Port | Purpose | Protocol |
|------|---------|----------|
| 6817-6819 | Slurm controller | TCP |
| 6818 | Slurmd (compute daemon) | TCP |

## Troubleshooting

### Issue: "sudo: a password is required"

Some nodes may require password for sudo commands.

**Solutions:**

1. **Configure passwordless sudo (recommended for automation):**
   ```bash
   # On each node, add user to sudoers with NOPASSWD
   echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/$USER
   sudo chmod 0440 /etc/sudoers.d/$USER
   ```

2. **Manual configuration:**
   Manually configure firewall on nodes that require passwords.

### Issue: "Error configuring firewall"

**Check:**
1. SSH access to the node works
2. User has sudo privileges
3. Firewall service is installed and running

**Debug:**
```bash
# Check which firewall is installed
ssh node_ip "which firewall-cmd ufw iptables"

# Check sudo access
ssh node_ip "sudo -l"

# Test firewall command manually
ssh node_ip "sudo firewall-cmd --list-all"  # firewalld
ssh node_ip "sudo ufw status"  # ufw
```

### Issue: Firewall configured but MPI still fails

**Check:**
1. Verify ports are actually open:
   ```bash
   # From another node, test connectivity
   nc -zv node_ip 50000
   ```

2. Check if SELinux is blocking (RedHat/Rocky):
   ```bash
   ssh node_ip "sudo getenforce"
   # If "Enforcing", may need to configure SELinux
   ```

3. Verify MPI MCA configuration uses correct ports:
   ```bash
   cat ~/.openmpi/mca-params.conf | grep port
   ```

## Integration with Cluster Setup

### Complete Setup Workflow

```bash
cd /home/muyiwa/Development/ClusterSetupAndConfigs

# 1. Update cluster configuration
vim cluster_config_actual.yaml

# 2. Deploy MPI configuration
uv run python cluster_modules/config_template_manager.py deploy mpi-mca

# 3. Generate hostfile
uv run python cluster_modules/config_template_manager.py generate mpi-hostfile \
  --output ~/cluster_build_sources/benchmarks/hostfile

# 4. Configure firewalls
uv run python cluster_modules/config_template_manager.py firewall configure

# 5. Verify setup
uv run python cluster_modules/config_template_manager.py firewall verify

# 6. Test MPI
cd ~/cluster_build_sources/benchmarks
mpirun -np 4 --hostfile hostfile --map-by ppr:1:node hostname
```

## Automated Setup Script

For convenience, a complete setup script is provided:

```bash
# Run complete cluster network setup
./scripts/setup_cluster_network.sh
```

This script:
1. Deploys MPI MCA configuration to all nodes
2. Generates and deploys hostfile
3. Configures firewalls on all nodes
4. Verifies configuration
5. Runs basic MPI connectivity test

## Notes

- **Firewall configuration requires sudo access** on remote nodes
- **WSL nodes** require Windows Firewall configuration on host
- **Configure passwordless sudo** for automated setup
- **Backup** existing firewall rules before modifying
- **Test incrementally**: Configure one node at a time if issues occur

## Related Documentation

- **Template System**: `../configuration/TEMPLATE_SYSTEM.md`
- **MPI Network Fix**: `MPI_NETWORK_FIX.md`
- **Multi-Homed Nodes**: `MULTI_HOMED_NODE_FIX.md`
- **WSL Firewall Setup**: `../../WSL_FIREWALL_SETUP.md`
