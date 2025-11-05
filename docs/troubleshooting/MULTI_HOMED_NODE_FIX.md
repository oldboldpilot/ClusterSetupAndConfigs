# Multi-Homed Node Configuration for OpenMPI

## Problem Description

### Symptoms
- MPI benchmark hangs after initialization
- `hostname` test works but actual MPI communication fails
- Debug logs show connections to secondary IP addresses

### Root Cause
Several nodes in the cluster have **multiple network interfaces with IPs in the same subnet**:

- **192.168.1.136** (oluwasanmiredhatserver): 
  - Primary: 192.168.1.136 (ens1f0)
  - Secondary: 192.168.1.138 (ens1f1)

- **192.168.1.139** (muyiwadroexperiments):
  - Primary: 192.168.1.139 (enp1s0)
  - Secondary: 192.168.1.137 (enp2s0)
  - Virtual: 192.168.122.1 (virbr0 - libvirt)

- **192.168.1.96** (oluubuntul1):
  - Primary: 192.168.1.96 (enp1s0)
  - Secondary: 192.168.1.97 (enp2s0)

- **192.168.1.147** (DESKTOP-3SON9JT - WSL):
  - Primary: 192.168.1.147 (eth1)
  - No secondary physical IPs (good!)

### Detected Behavior
When using subnet notation (`192.168.1.0/24`), OpenMPI:
1. Discovers ALL interfaces in the subnet (including secondary IPs)
2. Attempts to use secondary interfaces for communication
3. Connections fail because remote nodes expect primary IPs
4. Debug output shows:
   ```
   [node:pid] btl: tcp: attempting to connect() to [[job,rank]] address 192.168.1.138 on port 50000
   [node:pid] btl: tcp: Match incoming connection from [[job,rank]] 192.168.1.138 with locally known IP 192.168.1.136 failed!
   ```

## Solution

### Approach 1: Exact IP with /32 CIDR Notation (IMPLEMENTED)

Configure OpenMPI to use **only** the primary IP address of each node with /32 CIDR notation:

**Template:** `templates/mpi/mca-params.conf.j2`
```jinja
btl_tcp_if_include = 192.168.1.136/32,192.168.1.139/32,192.168.1.96/32,192.168.1.147/32
oob_tcp_if_include = 192.168.1.136/32,192.168.1.139/32,192.168.1.96/32,192.168.1.147/32
```

This tells OpenMPI to **only** use these specific IP addresses, ignoring any secondary interfaces.

### Approach 2: Disable Secondary Interfaces (ALTERNATIVE)

If secondary interfaces aren't needed, disable them:

```bash
# Temporarily disable secondary interface
sudo ip link set enp2s0 down

# Permanently disable (add to /etc/network/interfaces or netplan)
```

### Approach 3: Interface Name Selection (ALTERNATIVE)

Use interface names instead of IPs:

```bash
btl_tcp_if_include = ens1f0,enp1s0  # Primary interfaces only
oob_tcp_if_include = ens1f0,enp1s0
```

**Note:** This requires consistent interface naming across nodes.

## Implementation

### 1. Check Node Network Configuration

```bash
# Check all IPs in cluster subnet on each node
pdsh -w all_nodes "hostname && ip addr show | grep 'inet 192.168.1'"
```

### 2. Update cluster_config_actual.yaml

Ensure only primary IPs are listed:

```yaml
master:
  - ip: 192.168.1.136  # Primary IP only
    os: redhat
    name: oluwasanmiredhatserver

workers:
  - ip: 192.168.1.139  # Primary IP only
    os: ubuntu
    name: muyiwadroexperiments
  # ...
```

### 3. Generate and Deploy Configuration

```bash
cd /home/muyiwa/Development/ClusterSetupAndConfigs

# Generate MPI MCA config with exact IP matching
uv run python cluster_modules/config_template_manager.py generate mpi-mca

# Verify configuration shows /32 CIDR notation
# Should see: btl_tcp_if_include = 192.168.1.136/32,192.168.1.139/32,...

# Deploy to all nodes
uv run python cluster_modules/config_template_manager.py deploy mpi-mca
```

### 4. Verify Deployment

```bash
# Check configuration on all nodes
pdsh -w all_nodes "cat ~/.openmpi/mca-params.conf | grep btl_tcp_if_include"

# Test MPI hostname (simple test)
cd ~/cluster_build_sources/benchmarks
mpirun -np 4 --hostfile hostfile --map-by ppr:1:node hostname
```

### 5. Test Benchmarks

```bash
# Test MPI latency
timeout 30 mpirun -np 2 --hostfile hostfile --map-by ppr:1:node bin/mpi_latency

# Test with verbose debugging if needed
mpirun -np 2 --hostfile hostfile --map-by ppr:1:node \
  --mca btl_base_verbose 100 \
  bin/mpi_latency 2>&1 | tee /tmp/mpi_debug.log
```

## Remaining Issues

### Firewall Configuration

Even with exact IP matching, firewalls may block MPI data transfer:

**Symptoms:**
- MPI accepts connections but processes cannot find peers
- Error: "server accept cannot find guid"
- Timeout during actual communication

**Solution:** Ensure ports 50000-50200 are open on all nodes

#### RedHat/Rocky Linux (firewalld):
```bash
sudo firewall-cmd --permanent --add-port=50000-50200/tcp
sudo firewall-cmd --reload
```

#### Ubuntu (ufw):
```bash
sudo ufw allow 50000:50200/tcp
sudo ufw reload
```

#### WSL/Windows:
See `WSL_FIREWALL_SETUP.md` for Windows Firewall configuration.

### Process Cleanup

If benchmarks hang, kill stuck processes:

```bash
pdsh -w all_nodes "pkill -9 -f 'mpi_latency|prterun|prted|orted'"

# Verify cleanup
pdsh -w all_nodes "ps aux | grep -E 'mpi|prte' | grep -v grep"
```

## Testing Results

### Working Tests
✅ MPI hostname test: `mpirun -np 4 --hostfile hostfile --map-by ppr:1:node hostname`  
✅ Configuration deployment: All 4 nodes configured successfully  
✅ Network interface selection: Exact IPs with /32 CIDR working  
✅ Process cleanup: Stuck processes killed successfully  

### Failing Tests
❌ MPI latency benchmark: Still hangs during execution  
❌ MPI bandwidth benchmark: Not yet tested  

### Known Issues
⚠️ Firewall may be blocking MPI data transfer  
⚠️ Process matching errors suggest authentication/GUID issues  
⚠️ Secondary interfaces still enabled on nodes  

## Verification Commands

```bash
# Comprehensive diagnostic
cat > /tmp/multi_homed_diagnostic.sh << 'EOF'
#!/bin/bash
echo "=== Network Interfaces on Each Node ==="
pdsh -w all_nodes "hostname && ip addr show | grep 'inet 192.168.1'"

echo -e "\n=== MPI MCA Configuration ==="
pdsh -w all_nodes "grep -E 'btl_tcp_if|oob_tcp_if' ~/.openmpi/mca-params.conf"

echo -e "\n=== Test MPI Hostname ==="
cd ~/cluster_build_sources/benchmarks
mpirun -np 4 --hostfile hostfile --map-by ppr:1:node hostname

echo -e "\n=== Test MPI with Verbose BTL ==="
timeout 10 mpirun -np 2 --hostfile hostfile --map-by ppr:1:node \
  --mca btl_base_verbose 30 \
  bin/mpi_latency 2>&1 | head -100
EOF

chmod +x /tmp/multi_homed_diagnostic.sh
/tmp/multi_homed_diagnostic.sh
```

## References

- **OpenMPI BTL TCP Documentation:** https://docs.open-mpi.org/en/v5.0.x/tuning-apps/networking/tcp.html
- **MPI Network Fix:** `MPI_NETWORK_FIX.md`
- **MPI Benchmark Debugging:** `MPI_BENCHMARK_DEBUGGING.md`
- **Template System:** `../configuration/TEMPLATE_SYSTEM.md`

## Next Steps

1. **Configure Firewall:** Open ports 50000-50200 on all nodes
2. **Test Incrementally:** Start with 2 nodes, then add more
3. **Consider Disabling Secondary Interfaces:** If not needed for failover/bonding
4. **Monitor Connections:** Use `ss -tnp` during benchmark execution
5. **Try Alternative Benchmarks:** Test with OSU Micro-Benchmarks

## Additional Notes

- **Primary IP Selection:** Always use the first IP (`enp1s0`, `ens1f0`) as primary
- **Secondary Interface Purpose:** May be for link aggregation, failover, or separate networks
- **Check with Network Admin:** Understand why nodes have multiple IPs
- **Performance Impact:** Secondary interfaces may affect routing and latency
