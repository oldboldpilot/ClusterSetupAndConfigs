# WSL Firewall and Port Forwarding Setup for OpenMPI

This guide explains how to configure Windows Firewall and port forwarding to enable OpenMPI cross-cluster execution on WSL.

## The Problem

OpenMPI 5.x uses PRRTE (PMIx Reference Runtime Environment) which requires bidirectional TCP communication between nodes on ports 50000-50200. By default:

- Windows only forwards SSH (port 22) to WSL
- Windows Firewall may block the MPI ports
- WSL uses NAT mode networking, which isolates it from other cluster nodes
- This causes `mpirun` to hang when trying to execute across cluster nodes

## The Solution

### Step 0: Enable WSL Mirrored Mode Networking (REQUIRED FIRST)

**Critical**: Before configuring firewall rules, you must enable mirrored mode networking in WSL.

Create or edit `.wslconfig` in your Windows home directory (`C:\Users\<YourUsername>\.wslconfig`):

```ini
[wsl2]
networkingMode = mirrored
```

After creating/editing this file, restart WSL:
```powershell
wsl --shutdown
```

**Why this is required**:
- In default NAT mode, WSL uses an internal IP address (e.g., 172.x.x.x) that's not accessible from other cluster nodes
- Mirrored mode gives your WSL instance the same IP address as your Windows host on the physical network
- This allows other nodes in your cluster to communicate with the WSL node directly via its mirrored IP
- Without mirrored mode, firewall rules alone won't help - other nodes simply cannot route to WSL

### Step 1: PowerShell Scripts

We provide two PowerShell scripts for firewall configuration:

#### 1. configure_wsl_firewall.ps1 (REQUIRED)

**What it does**:
- Creates Windows Firewall rules to allow MPI ports 50000-50200
- Configures both inbound and outbound rules
- Rules persist across Windows reboots

**How to run**:
```powershell
# Open PowerShell as Administrator
cd Z:\PycharmProjects\ClusterSetupAndConfigs
.\configure_wsl_firewall.ps1
```

**Output**: Creates firewall rules named `WSL2-OpenMPI-BTL-TCP` and `WSL2-OpenMPI-OOB-TCP`

#### 2. setup_wsl_port_forwarding.ps1 (OPTIONAL)

**What it does**:
- Sets up Windows netsh port forwarding for ports 50000-50200
- Only needed if external machines need to access your WSL cluster
- Creates 201 port forwarding rules

**How to run**:
```powershell
# Open PowerShell as Administrator
cd Z:\PycharmProjects\ClusterSetupAndConfigs
.\setup_wsl_port_forwarding.ps1

# To remove port forwarding rules
.\setup_wsl_port_forwarding.ps1 -Remove
```

**Important**: Port forwarding rules are cleared when Windows restarts and must be re-run if the WSL IP address changes.

## Quick Start

For most WSL clusters (nodes within the same network), follow these steps:

1. **Enable mirrored networking** (see Step 0 above - REQUIRED)
   - Edit `C:\Users\<YourUsername>\.wslconfig`
   - Add `networkingMode = mirrored` under `[wsl2]`
   - Run `wsl --shutdown` to restart WSL

2. **Run firewall configuration as Administrator in PowerShell**:
   ```powershell
   cd Z:\PycharmProjects\ClusterSetupAndConfigs
   .\configure_wsl_firewall.ps1
   ```

3. **Test in WSL**:
   ```bash
   # Test cross-cluster MPI
   mpirun -np 6 --hostfile ~/.openmpi/hostfile hostname
   ```

## Verification

### Check Firewall Rules (PowerShell):
```powershell
Get-NetFirewallRule -DisplayName "WSL2-OpenMPI*" | Format-Table DisplayName, Enabled, Direction
```

### Check Port Forwarding (PowerShell):
```powershell
netsh interface portproxy show all | Select-String -Pattern "50"
```

### Check MPI Configuration (WSL):
```bash
# View configured ports
cat ~/.openmpi/mca-params.conf

# Should show:
# btl_tcp_port_min_v4 = 50000
# oob_tcp_port_range = 50100-50200
```

## Troubleshooting

### Firewall script says "Access Denied"
- You must run PowerShell as Administrator
- Right-click PowerShell icon → "Run as Administrator"

### MPI still hangs after running scripts
1. Verify firewall rules are created (see Verification above)
2. Check if WSL IP changed: `wsl hostname -I`
3. Re-run port forwarding script if IP changed
4. Try with debug flags:
   ```bash
   mpirun -np 2 --host master,worker1 \
     --mca btl_base_verbose 20 \
     --mca oob_base_verbose 10 \
     hostname
   ```

### Port forwarding stopped working after Windows restart
- Port forwarding rules must be re-run after each Windows restart
- Firewall rules persist automatically

### Alternative if PowerShell solution doesn't work
- Use Slurm's `srun` instead of `mpirun`
- Use pdsh for embarrassingly parallel tasks

## Technical Details

### Port Allocation
- **50000-50100**: BTL (Byte Transfer Layer) TCP communication
- **50100-50200**: OOB (Out-of-Band) TCP for PRRTE daemon communication

### Why Two Scripts?
1. **Firewall rules**: Allow traffic within Windows and to/from WSL (required)
2. **Port forwarding**: Forward external traffic to WSL (optional, only for external access)

### Security Considerations
- These rules allow inbound/outbound traffic on the specified ports
- Only apply if you need MPI across multiple machines
- For local-only development, consider using Slurm's srun or pdsh instead

## Additional Resources

- [OpenMPI 5.x Documentation](https://docs.open-mpi.org/en/v5.0.x/)
- [PRRTE Documentation](https://docs.prrte.org/)
- See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive troubleshooting
- See [README.md](README.md) for cluster setup instructions
