# PGAS Cluster Testing and Benchmarking Guide

## Overview
This guide covers testing and benchmarking the PGAS (Partitioned Global Address Space) cluster with UPC++ 2025.10.0 and GASNet-EX 2025.8.0.

## Test Programs

### 1. UPC++ Cluster Test (`upcxx_cluster_test`)
**Purpose**: Validate multi-node UPC++ functionality
- Tests distributed memory access with `upcxx::global_ptr`
- Demonstrates PGAS programming model
- Verifies cluster connectivity

**Usage**:
```bash
# Single-node test (localhost)
cd ~/cluster_build_sources
upcxx-run -localhost -n 4 -shared-heap 128M ./upcxx_cluster_test

# Multi-node test (requires configuration)
export GASNET_SSH_SERVERS="192.168.1.136,192.168.1.147,192.168.1.139,192.168.1.96"
upcxx-run -n 16 -shared-heap 1G ./upcxx_cluster_test
```

**Expected Output**:
```
Rank 0 of 4 running on oluwasanmiredhatserver
Rank 1 of 4 running on oluwasanmiredhatserver
...
=== Testing distributed memory access ===
Master (rank 0) created global pointer with value 42
All ranks can now access this memory!
✓ UPC++ cluster test completed successfully!
```

### 2. PGAS Performance Benchmark (`pgas_benchmark`)
**Purpose**: Measure UPC++ performance for common operations
- Barrier synchronization
- Remote PUT (1M integers)
- Remote GET (1M integers)
- RPC round-trip
- Broadcast operations

**Usage**:
```bash
# Single-node (localhost)
upcxx-run -localhost -n 4 -shared-heap 1G ./pgas_benchmark

# Multi-node
export GASNET_SSH_SERVERS="192.168.1.136,192.168.1.147,192.168.1.139,192.168.1.96"
upcxx-run -n 16 -shared-heap 1G ./pgas_benchmark
```

**Output Format**:
```
╔══════════════════════════════════════════════════════════════╗
║          UPC++ Performance Benchmark Suite                   ║
╚══════════════════════════════════════════════════════════════╝

Results:
────────────────────────────────────────────────────────────────
Barrier synchronization              Avg: 0.123 ms  Min: 0.089 ms  Max: 0.234 ms
Remote PUT (1M integers)             Avg: 12.456 ms Min: 11.234 ms Max: 14.567 ms
...
```

### 3. MPI Performance Benchmark (`mpi_benchmark`)
**Purpose**: Baseline comparison for PGAS vs MPI
- Barrier synchronization
- Send/Recv (1M integers)
- Broadcast (1M integers)
- Reduce SUM (1M integers)
- Allreduce SUM (1M integers)

**Usage**:
```bash
# Single-node
mpirun -np 4 ./mpi_benchmark

# Multi-node (requires hostfile)
mpirun -np 16 --hostfile hostfile ./mpi_benchmark
```

## Cluster Configuration

### Prerequisites
Before running multi-node tests, configure the cluster:

```bash
cd ~/cluster_build_sources
./configure_pgas_cluster.sh --password <cluster_password>
```

This script will:
1. ✓ Configure passwordless sudo for cluster operations
2. ✓ Setup binutils, Python, and UPC++ symlinks on all nodes
3. ✓ Add environment variables to ~/.bashrc
4. ✓ Test connectivity (upcxx --version on each node)
5. ✓ Create MPI hostfile with slot counts

### Environment Variables
After configuration, the following are set in ~/.bashrc:

```bash
# Homebrew and UPC++ paths
export PATH="/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/upcxx/bin:$PATH"
export LD_LIBRARY_PATH="/home/linuxbrew/.linuxbrew/lib:$LD_LIBRARY_PATH"

# GASNet SSH configuration
export GASNET_SSH_SERVERS="192.168.1.136,192.168.1.147,192.168.1.139,192.168.1.96"
export GASNET_VERBOSEENV=1  # Enable for debugging
```

### MPI Hostfile
Location: `~/cluster_build_sources/hostfile`

```
192.168.1.136 slots=88
192.168.1.147 slots=32
192.168.1.139 slots=16
192.168.1.96 slots=16
```

## Comprehensive Benchmark Suite

### Running All Benchmarks
Use the automated benchmark script:

```bash
cd ~/cluster_build_sources
./run_benchmarks.sh --password <cluster_password>
```

This runs benchmarks with multiple configurations:
- **4 processes** (single-node): Baseline performance
- **16 processes** (multi-node-small): 4 nodes × 4 processes
- **32 processes** (multi-node-medium): Full capacity
- **64 processes** (multi-node-large): Oversubscribed

Results are saved to: `~/cluster_build_sources/benchmark_results/`

### Analyzing Results
```bash
# Quick summary
grep 'Avg:' ~/cluster_build_sources/benchmark_results/*.log

# Compare UPC++ vs MPI for specific test
diff <(grep "Barrier" benchmark_results/upcxx_single-node_*) \
     <(grep "Barrier" benchmark_results/mpi_single-node_*)
```

## Troubleshooting

### Issue: GASNET_SSH_SERVERS missing
**Error**: `*** GASNET ERROR: Environment variable GASNET_SSH_SERVERS is missing.`

**Solution**:
```bash
# For single-node testing, use -localhost flag
upcxx-run -localhost -n 4 ./program

# For multi-node, export GASNET_SSH_SERVERS
export GASNET_SSH_SERVERS="192.168.1.136,192.168.1.147,192.168.1.139,192.168.1.96"
```

### Issue: SSH authentication failures
**Error**: `*** GASNET ERROR: SSH connection failed`

**Solution**:
```bash
# Verify SSH key authentication
ssh 192.168.1.147 hostname  # Should work without password

# Regenerate SSH keys if needed
cd ~/cluster_build_sources
./configure_cluster_sudo.sh --password <password>
```

### Issue: Different hostnames in output
**Expected**: This is normal! UPC++ distributes processes across nodes.
```
Rank 0 running on oluwasanmiredhatserver
Rank 4 running on wsl2-master
Rank 8 running on ubuntu-worker1
Rank 12 running on ubuntu-worker2
```

### Issue: Slow performance on multi-node
**Debugging**:
```bash
# Enable GASNet verbose output
export GASNET_VERBOSEENV=1
upcxx-run -n 16 ./program

# Check network conduit
upcxx-meta GASNET_CONDUIT  # Should show 'udp' or 'mpi'

# Test with MPI conduit (if slower with UDP)
export UPCXX_NETWORK=mpi
upcxx-run -n 16 ./program
```

## Performance Expectations

### Single-Node (SMP/UDP)
- **Barrier**: < 1 ms (4 processes)
- **PUT/GET (1M ints)**: 10-50 ms (depends on memory bandwidth)
- **RPC**: < 0.1 ms (local memory)

### Multi-Node (UDP)
- **Barrier**: 1-10 ms (network latency dominant)
- **PUT/GET (1M ints)**: 50-200 ms (gigabit ethernet)
- **RPC**: 0.1-1 ms (network round-trip)

### PGAS Advantages
- **Irregular communication patterns**: PGAS typically 2-5x faster
- **One-sided operations**: No receiver involvement needed
- **Fine-grained access**: Direct memory reads without message overhead
- **Asynchronous operations**: Overlap computation and communication

### MPI Advantages
- **Large collective operations**: Optimized algorithms (broadcast, reduce)
- **Structured communication**: Well-defined message passing
- **Mature ecosystem**: More libraries and tools available

## Next Steps

### 1. OpenSHMEM Installation (Optional)
```bash
cd ~/cluster_build_sources
wget https://github.com/Sandia-OpenSHMEM/SOS/releases/download/v1.5.2/sandia-openshmem-1.5.2.tar.gz
tar xzf sandia-openshmem-1.5.2.tar.gz && cd sandia-openshmem-1.5.2
./configure --prefix=/home/linuxbrew/.linuxbrew/openshmem
make -j$(nproc) && make install

# Distribute to cluster
pdsh -w 192.168.1.147,192.168.1.139,192.168.1.96 \
  "rsync -avz 192.168.1.136:/home/linuxbrew/.linuxbrew/openshmem/ /home/linuxbrew/.linuxbrew/openshmem/"
```

### 2. Application Development
Create your own PGAS applications:
```cpp
#include <upcxx/upcxx.hpp>

int main() {
    upcxx::init();
    
    // Your PGAS code here
    // - Use upcxx::global_ptr for distributed arrays
    // - Use upcxx::rpc() for remote function calls
    // - Use upcxx::rput()/rget() for one-sided operations
    // - Use upcxx::barrier() for synchronization
    
    upcxx::finalize();
    return 0;
}
```

Compile: `upcxx -O3 myapp.cpp -o myapp`
Run: `upcxx-run -n 16 -shared-heap 2G ./myapp`

### 3. Integration with cluster_setup.py
Add PGAS testing to your cluster setup:
```python
# In cluster_setup.py
def test_pgas_cluster(nodes, password):
    """Test PGAS functionality across cluster"""
    os.system(f"cd ~/cluster_build_sources && ./configure_pgas_cluster.sh --password {password}")
    os.system("cd ~/cluster_build_sources && upcxx-run -n 16 ./upcxx_cluster_test")
```

## References
- UPC++ Documentation: https://upcxx.lbl.gov/
- GASNet-EX: https://gasnet.lbl.gov/
- PGAS Tutorial: https://pgas.org/
- UPC++ Programmer's Guide: https://bitbucket.org/berkeleylab/upcxx/wiki/docs
