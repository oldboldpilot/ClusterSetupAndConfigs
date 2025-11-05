# MPI Benchmark Debugging Guide

## Current Status (2025-11-04)

### Working Components
✅ MPI hostname test across all 4 nodes  
✅ Template-based configuration system  
✅ Network interface selection (192.168.1.0/24 subnet)  
✅ Process cleanup functionality  
✅ Configuration deployment to all nodes  

### Known Issues
❌ MPI latency benchmark hangs during execution  
❌ Benchmark initializes but freezes during MPI_Send/MPI_Recv  
⚠️ New node 192.168.1.48 added but not yet tested  

## Debugging the Hanging Benchmark Issue

### Symptoms
```
$ timeout 30 mpirun -np 2 --hostfile hostfile --map-by ppr:1:node bin/mpi_latency

MPI Point-to-Point Latency Benchmark
=====================================
Number of processes: 2
Iterations per measurement: 1000
Message size: 8 bytes

[HANGS HERE - timeout after 30 seconds]
```

### What Works
- MPI hostname test succeeds: `mpirun -np 4 --hostfile hostfile --map-by ppr:1:node hostname`
- This proves:
  - Network connectivity is working
  - PRRTE daemon communication works
  - Interface selection is correct
  - SSH connections are functional

### What Doesn't Work
- Actual MPI point-to-point communication in benchmarks
- Suggests issue is in MPI data transfer layer, not control plane

### Debugging Steps

#### 1. Test with Verbose MPI Debugging

```bash
cd ~/cluster_build_sources/benchmarks

# Enable verbose BTL and PML debugging
timeout 30 mpirun -np 2 --hostfile hostfile --map-by ppr:1:node \
  --mca btl_base_verbose 30 \
  --mca pml_base_verbose 30 \
  --mca btl_tcp_if_include 192.168.1.0/24 \
  bin/mpi_latency 2>&1 | tee /tmp/mpi_debug.log

# Check the log for connection attempts
grep -i "connect\|error\|fail\|timeout" /tmp/mpi_debug.log
```

#### 2. Check Firewall Status on All Nodes

```bash
# Check firewall on RedHat/Rocky Linux
pdsh -w 192.168.1.136 "sudo firewall-cmd --list-all"

# Check firewall on Ubuntu
pdsh -w 192.168.1.139,192.168.1.96 "sudo ufw status verbose"

# Check Windows Firewall for WSL node
# Run on Windows host:
Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*WSL*" }
```

**Expected:** Ports 50000-50200 should be open for TCP

#### 3. Test Simpler MPI Programs

```bash
# Test MPI hello world
mpirun -np 4 --hostfile hostfile --map-by ppr:1:node \
  sh -c 'echo "Hello from $(hostname) rank $OMPI_COMM_WORLD_RANK"'

# Test MPI bandwidth (may reveal if issue is size-specific)
timeout 30 mpirun -np 2 --hostfile hostfile --map-by ppr:1:node \
  bin/mpi_bandwidth
```

#### 4. Monitor Network Connections During Hang

```bash
# In one terminal, start monitoring
pdsh -w 192.168.1.136,192.168.1.139,192.168.1.96,192.168.1.147 \
  "watch -n 1 'ss -tnp | grep mpi_latency'" &

# In another terminal, run benchmark
timeout 30 mpirun -np 2 --hostfile hostfile --map-by ppr:1:node bin/mpi_latency

# Check if TCP connections are established
```

#### 5. Try Different MPI Transport Layers

```bash
# Force TCP BTL only (default)
mpirun --mca btl tcp,self,vader -np 2 --hostfile hostfile --map-by ppr:1:node bin/mpi_latency

# Try with larger timeout values
mpirun --mca btl_tcp_endpoint_timeout 60 \
  -np 2 --hostfile hostfile --map-by ppr:1:node bin/mpi_latency
```

#### 6. Test Local vs Remote Communication

```bash
# Test on single node (should work)
mpirun -np 2 bin/mpi_latency

# Test between two specific nodes
mpirun -np 2 --host 192.168.1.136:1,192.168.1.139:1 bin/mpi_latency
```

#### 7. Check for Resource Limits

```bash
# Check ulimits on all nodes
pdsh -w all_nodes "ulimit -a"

# Ensure adequate file descriptors
pdsh -w all_nodes "ulimit -n 4096"
```

#### 8. Examine Benchmark Source Code

```bash
# Look for potential deadlocks in benchmark code
cd ~/cluster_build_sources/benchmarks
cat src/mpi_latency.cpp

# Check if benchmark has proper error handling
# Look for MPI_Send/MPI_Recv without timeouts
```

### Potential Root Causes

1. **Firewall Blocking Data Transfer:**
   - Control messages (PRRTE) use different ports than data transfer (BTL TCP)
   - Hostname test may use different mechanism than benchmarks
   - **Solution:** Open ports 50000-50200 on all nodes

2. **MPI Protocol Mismatch:**
   - Different MPI versions on different nodes
   - **Check:** `pdsh -w all_nodes "ompi_info --version"`
   - **Solution:** Ensure identical OpenMPI version on all nodes

3. **TCP Connection Timeout:**
   - Default timeouts may be too short
   - **Solution:** Increase `btl_tcp_endpoint_timeout`

4. **Benchmark Code Issue:**
   - Deadlock in MPI_Send/MPI_Recv pattern
   - **Solution:** Use MPI_Sendrecv or non-blocking operations

5. **Network MTU Mismatch:**
   - Different MTU sizes on different interfaces
   - **Check:** `pdsh -w all_nodes "ip link show | grep mtu"`
   - **Solution:** Set consistent MTU across cluster

6. **Windows Firewall (WSL Node):**
   - Windows Firewall may block WSL network access
   - **Solution:** Configure Windows Firewall rules (see WSL_FIREWALL_SETUP.md)

### Recommended Next Steps

1. **Immediate:** Test with verbose debugging to see where communication fails
   ```bash
   timeout 30 mpirun -np 2 --hostfile hostfile --map-by ppr:1:node \
     --mca btl_base_verbose 100 \
     --mca pml_base_verbose 100 \
     bin/mpi_latency 2>&1 | tee /tmp/mpi_full_debug.log
   ```

2. **Check Firewalls:** Verify ports 50000-50200 are open on all nodes

3. **Test Incrementally:**
   - Start with 2 nodes (master + one worker)
   - If works, add more nodes one by one
   - Identify which node combination fails

4. **Try Alternative Benchmark:**
   - Test with OSU Micro-Benchmarks
   - If they work, issue is in our benchmark code

5. **Recompile Benchmarks:**
   - Rebuild with different optimization levels
   - Add more verbose output to benchmark code

### Quick Diagnostic Commands

```bash
# All-in-one diagnostic
cat > /tmp/mpi_diagnostic.sh << 'EOF'
#!/bin/bash
echo "=== Cluster Status ==="
uv run python cluster_modules/config_template_manager.py summary

echo -e "\n=== OpenMPI Version ==="
pdsh -w all_nodes "ompi_info --version | head -1"

echo -e "\n=== Network Interfaces ==="
pdsh -w all_nodes "ip addr show | grep 'inet 192.168.1'"

echo -e "\n=== Firewall Status ==="
pdsh -w 192.168.1.136 "sudo firewall-cmd --list-all 2>&1 || echo 'firewall-cmd not found'" 
pdsh -w 192.168.1.139,192.168.1.96,192.168.1.147 "sudo ufw status 2>&1 || echo 'ufw not found'"

echo -e "\n=== MPI MCA Config ==="
pdsh -w all_nodes "grep -E 'btl_tcp_if|oob_tcp_if' ~/.openmpi/mca-params.conf"

echo -e "\n=== Test MPI Hostname ==="
mpirun -np 4 --hostfile ~/cluster_build_sources/benchmarks/hostfile --map-by ppr:1:node hostname

echo -e "\n=== Test MPI Latency (timeout 10s) ==="
timeout 10 mpirun -np 2 --hostfile ~/cluster_build_sources/benchmarks/hostfile --map-by ppr:1:node \
  ~/cluster_build_sources/benchmarks/bin/mpi_latency || echo "FAILED or TIMEOUT"
EOF

chmod +x /tmp/mpi_diagnostic.sh
/tmp/mpi_diagnostic.sh
```

### Process Cleanup

If benchmarks hang and leave processes stuck:

```bash
# Kill all MPI-related processes
pdsh -w 192.168.1.136,192.168.1.139,192.168.1.96,192.168.1.147 \
  "pkill -9 -f 'mpi_latency|mpi_bandwidth|prterun|prted|orted'"

# Verify cleanup
pdsh -w all_nodes "ps aux | grep -E 'mpi|prte|orted' | grep -v grep | wc -l"
```

### Reference Configuration

**Working MCA Config** (`~/.openmpi/mca-params.conf`):
```
# BTL Configuration
btl = ^openib
btl_tcp_if_include = 192.168.1.0/24
oob_tcp_if_include = 192.168.1.0/24

# OpenMPI Paths
orte_prefix = /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8
opal_prefix = /home/linuxbrew/.linuxbrew

# Port Configuration
btl_tcp_port_min_v4 = 50000
oob_tcp_port_range = 50100-50200
```

**Working Hostfile**:
```
192.168.1.136 slots=88  # oluwasanmiredhatserver
192.168.1.139 slots=16  # muyiwadroexperiments
192.168.1.96 slots=16   # olubuuntul1
192.168.1.147 slots=32  # DESKTOP-3SON9JT
```

## Related Documentation

- **MPI Network Fix:** `MPI_NETWORK_FIX.md`
- **Template System:** `../configuration/TEMPLATE_SYSTEM.md`
- **WSL Firewall Setup:** `../../WSL_FIREWALL_SETUP.md`
- **Multi-Node Status:** `MULTI_NODE_BENCHMARK_STATUS.md`
