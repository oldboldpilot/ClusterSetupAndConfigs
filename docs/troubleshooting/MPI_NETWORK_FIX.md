# MPI Network Interface Configuration Fix

## Problem Analysis

### Root Cause
The MPI "Unable to find reachable pairing between local and remote interfaces" error occurs because:

1. **Multiple Network Interfaces**: Each node has multiple IP addresses:
   - Node 192.168.1.147 (WSL2): Has 192.168.1.147, 10.255.255.254, 172.17.0.1 (Docker), 10.1.96.192
   - Node 192.168.1.139: Has 192.168.1.139, 192.168.1.137, 192.168.122.1 (libvirt), 10.1.0.14
   - Node 192.168.1.96: Has 192.168.1.96, 192.168.1.97
   - Node 192.168.1.136: Has 192.168.1.136, 192.168.1.138

2. **OpenMPI Confusion**: OpenMPI tries to find matching network interfaces across nodes and gets confused by:
   - Virtual interfaces (Docker bridge 172.17.0.1, libvirt 192.168.122.1)
   - WSL-specific interfaces (10.255.255.254, 10.1.96.192)
   - Secondary physical IPs
   - Different interface names across OS types (RHEL vs Ubuntu vs WSL)

3. **PRRTE Requirements**: OpenMPI 5.x uses PRRTE which needs:
   - Bidirectional TCP communication on ports 50000-50200
   - Consistent network interface selection across all nodes
   - Firewall rules allowing these ports

### From Documentation Research

**OpenMPI Documentation** (docs.open-mpi.org):
- OpenMPI assumes all interfaces with same address family are routable
- Uses graph theory to select "best" connections
- Gets confused with private networks on different subnets (10.x, 172.x, 192.168.x)
- Requires explicit interface selection via `btl_tcp_if_include`

**Project DEPLOYMENT_GUIDE.md**:
- Documents PRRTE port requirements (50000-50200)
- Shows MCA parameter configuration in `~/.openmpi/mca-params.conf`
- Explains WSL mirrored networking requirement
- Provides firewall configuration scripts

**Sandia OpenSHMEM Wiki**:
- OpenSHMEM uses OpenMPI's PRRTE for process management
- PMI (Process Management Interface) needs proper MPI initialization
- `oshrun` wraps `mpirun` - inherits all MPI network issues

## Solution: Use Only Cluster IPs from Configuration

### Strategy
Configure OpenMPI to **ONLY** use the specific IP addresses defined in `cluster_config_actual.yaml`:
- 192.168.1.147 (master)
- 192.168.1.139 (worker)
- 192.168.1.96 (worker)
- 192.168.1.136 (worker)

Ignore all virtual interfaces, Docker bridges, libvirt networks, and secondary IPs.

## Implementation

### Step 1: Update MPI Configuration on All Nodes

The current `~/.openmpi/mca-params.conf` uses subnet notation `192.168.1.0/24`, which includes ALL interfaces in that subnet (including secondary IPs like .137, .138, .97). We need to be MORE specific.

**Current config (TOO BROAD)**:
```
btl_tcp_if_include = 192.168.1.0/24
```

**Fixed config (EXACT IPs only)**:
```
btl_tcp_if_include = 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136
oob_tcp_if_include = 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136
```

**Why this works**:
- `btl_tcp_if_include`: Restricts Byte Transfer Layer (data communication) to only these IPs
- `oob_tcp_if_include`: Restricts Out-of-Band (PRRTE control) to only these IPs
- OpenMPI will ignore all Docker, libvirt, WSL virtual, and secondary interfaces
- Forces consistent interface selection across all nodes

### Step 2: Verify Network Interfaces Match

Before applying fix, verify each node has exactly ONE of the specified IPs:

```bash
# Check on all nodes
pdsh -w 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136 \
  "ip addr show | grep -E '192.168.1.(147|139|96|136)' | grep -v grep"
```

Expected output: Each node should have exactly ONE match showing its assigned IP.

### Step 3: Apply Configuration to All Nodes

```bash
# Create the updated MCA configuration
cat > /tmp/mca-params.conf << 'EOF'
# OpenMPI MCA parameters
btl = ^openib
btl_tcp_if_include = 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136
oob_tcp_if_include = 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136

# OpenMPI installation prefix - critical for finding prted on remote nodes
orte_prefix = /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8
opal_prefix = /home/linuxbrew/.linuxbrew

# Port configuration for firewall-friendly operation
btl_tcp_port_min_v4 = 50000
oob_tcp_port_range = 50100-50200
EOF

# Distribute to all nodes
for node in 192.168.1.147 192.168.1.139 192.168.1.96 192.168.1.136; do
  echo "Updating $node..."
  ssh $node "mkdir -p ~/.openmpi"
  scp /tmp/mca-params.conf $node:~/.openmpi/mca-params.conf
done
```

### Step 4: Update Environment Variables (OpenSHMEM)

OpenSHMEM also needs to know which libfabric provider to use:

```bash
# Add to ~/.bashrc on all nodes
cat >> ~/.bashrc << 'EOF'

# PGAS Library Configuration
export FI_PROVIDER=tcp
export LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/Cellar/libfabric/2.3.1/lib:$LD_LIBRARY_PATH
EOF

# Source on all nodes
pdsh -w 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136 "source ~/.bashrc"
```

### Step 5: Verify Firewall Rules (All Nodes)

```bash
# Check firewall status on all nodes
pdsh -w 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136 \
  "sudo firewall-cmd --list-all 2>/dev/null || sudo ufw status"

# For Ubuntu nodes (139, 96):
ssh 192.168.1.139 "sudo ufw allow from 192.168.1.0/24 to any port 50000:50200 proto tcp"
ssh 192.168.1.96 "sudo ufw allow from 192.168.1.0/24 to any port 50000:50200 proto tcp"

# For RedHat node (136):
ssh 192.168.1.136 "sudo firewall-cmd --permanent --add-port=50000-50200/tcp && sudo firewall-cmd --reload"

# For WSL node (147) - needs Windows firewall configuration
# On Windows (as Administrator in PowerShell):
# cd Z:\PycharmProjects\ClusterSetupAndConfigs
# .\configure_wsl_firewall.ps1
```

### Step 6: Test the Fix

#### Test 1: Simple MPI Hostname
```bash
cd ~/cluster_build_sources/benchmarks

# Test with explicit debugging
mpirun -np 4 --hostfile hostfile \
  --mca btl_base_verbose 10 \
  --mca oob_base_verbose 10 \
  hostname
```

**Expected**: Should show hostname from each node without "Unable to find reachable pairing" errors.

#### Test 2: MPI Latency Benchmark
```bash
mpirun -np 4 --hostfile hostfile bin/mpi_latency
```

**Expected**: Should complete successfully with latency measurements.

#### Test 3: OpenSHMEM with Explicit Config
```bash
# Test locally first (2 PEs on same node)
oshrun -np 2 bin/openshmem_latency 50

# If local works, test multi-node
oshrun -np 4 --hostfile hostfile bin/openshmem_latency 100
```

**Expected**: Should report "PE 0 of 4", "PE 1 of 4", etc., not "PE 0 of 1".

## Additional Fixes for OpenSHMEM PMI Issue

The OpenSHMEM "PE 0 of 1" problem is separate from network interface issues. It's caused by PMI not properly initializing.

### Option A: Use Slurm's PMI2 (Recommended)
Once Slurm is configured and running:
```bash
srun -n 4 bin/openshmem_latency 100
```

### Option B: Rebuild OpenSHMEM with PMIx
```bash
cd ~/openshmem_build/SOS-1.5.3
./configure --prefix=/home/linuxbrew/.linuxbrew/openshmem \
            --with-ofi=$(brew --prefix libfabric) \
            --enable-pmi-simple \
            --with-pmix=/path/to/pmix \
            CC=/home/linuxbrew/.linuxbrew/bin/gcc \
            CXX=/home/linuxbrew/.linuxbrew/bin/g++
make -j$(nproc) && make install
```

### Option C: Use MPI Directly for Multi-Process
Instead of `oshrun`, use `mpirun` with PMI:
```bash
mpirun -np 4 --hostfile hostfile \
  --mca pmi_base_verbose 10 \
  bin/openshmem_latency 100
```

## WSL-Specific Requirements

For node 192.168.1.147 (WSL2), additional steps required:

### 1. Enable Mirrored Networking (CRITICAL)

Edit `C:\Users\<YourUsername>\.wslconfig`:
```ini
[wsl2]
networkingMode = mirrored
```

Restart WSL:
```powershell
wsl --shutdown
```

**Why**: WSL default NAT mode gives internal IP (172.x) not accessible from other nodes. Mirrored mode gives WSL the same IP as Windows host.

### 2. Configure Windows Firewall

Run as Administrator in PowerShell:
```powershell
cd Z:\PycharmProjects\ClusterSetupAndConfigs
.\configure_wsl_firewall.ps1
```

## Verification Checklist

- [ ] `~/.openmpi/mca-params.conf` updated on all 4 nodes with exact IPs
- [ ] Each node can ping all other nodes: `ping -c 2 <node_ip>`
- [ ] SSH works to all nodes: `ssh <node_ip> hostname`
- [ ] Firewall rules allow ports 50000-50200 on all nodes
- [ ] WSL node has mirrored networking enabled
- [ ] Environment variables set (FI_PROVIDER, LD_LIBRARY_PATH)
- [ ] `mpirun -np 4 --hostfile hostfile hostname` works without errors
- [ ] MPI benchmark runs successfully across all nodes
- [ ] OpenSHMEM local test works (2 PEs on same node)

## Expected Results After Fix

### Before Fix
```
[DESKTOP-3SON9JT] Unable to find reachable pairing between local and remote interfaces
Process 1 on DESKTOP-3SON9JT cannot reach Process 0 on oluwasanmiredhatserver
BTLs attempted: self tcp
```

### After Fix
```
$ mpirun -np 4 --hostfile hostfile hostname
DESKTOP-3SON9JT
muyiwadroexperiments
olubuuntul1
oluwasanmiredhatserver

$ mpirun -np 4 --hostfile hostfile bin/mpi_latency
Rank 0 of 4 on oluwasanmiredhatserver
Rank 1 of 4 on DESKTOP-3SON9JT
Rank 2 of 4 on muyiwadroexperiments
Rank 3 of 4 on olubuuntul1
Average latency: X.XX microseconds
```

## Troubleshooting

### Issue: Still getting "reachable pairing" error
- Verify MCA config applied: `cat ~/.openmpi/mca-params.conf`
- Check OpenMPI actually reads it: `ompi_info --param btl tcp --level 9 | grep if_include`
- Test with explicit override: `mpirun --mca btl_tcp_if_include 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136 ...`

### Issue: Connection timeouts
- Check firewall: `sudo firewall-cmd --list-all` or `sudo ufw status`
- Verify port listening: `ss -tlnp | grep 50`
- Test direct connection: `telnet <node_ip> 50100`

### Issue: OpenSHMEM still shows 1 PE
- This is a separate PMI issue, not fixed by network configuration
- Use Slurm's `srun` instead of `oshrun`
- Or rebuild OpenSHMEM with PMIx support

## References

- **OpenMPI 5.x TCP Documentation**: https://docs.open-mpi.org/en/v5.0.x/tuning-apps/networking/tcp.html
- **Project DEPLOYMENT_GUIDE.md**: PRRTE troubleshooting section
- **Project WSL_FIREWALL_SETUP.md**: Windows firewall configuration
- **Sandia OpenSHMEM**: https://github.com/Sandia-OpenSHMEM/SOS/wiki
- **cluster_config_actual.yaml**: Authoritative source for cluster IPs

## Next Steps After Network Fix

1. **Test MPI thoroughly** - Ensure all 4 nodes can communicate
2. **Configure Slurm with munge** - Enable Slurm PMI2 for OpenSHMEM
3. **Test OpenSHMEM via Slurm** - Use `srun` instead of `oshrun`
4. **Fix UPC++ GASNet routing** - Similar network interface specification needed
5. **Create Slurm job scripts** - Automate benchmark submission
6. **Performance tuning** - Optimize after functionality confirmed
