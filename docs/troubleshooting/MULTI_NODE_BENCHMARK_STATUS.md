# Multi-Node Benchmark Status

## Date: November 4, 2025
## Cluster: 4 nodes, 152 cores total

---

## ✅ WORKING BENCHMARKS

### 1. OpenMP Parallel (ALL NODES) - **FULLY FUNCTIONAL**
- **Command**: `pdsh -w node_list "cd benchmarks && bin/openmp_parallel"`
- **Status**: ✅ Working perfectly on all 4 nodes simultaneously
- **Results**:
  - Node 192.168.1.136 (88 cores): Tests 1, 2, 4, 8, 16, 32, 64, 88 threads
  - Node 192.168.1.147 (32 cores): Tests 1, 2, 4, 8, 16, 32 threads
  - Node 192.168.1.139 (16 cores): Tests 1, 2, 4, 8, 16 threads
  - Node 192.168.1.96 (16 cores): Tests 1, 2, 4, 8, 16 threads
- **Performance**: Best efficiency at 2-4 threads (~50%), scales reasonably to all cores
- **C++23 Compliance**: ✅ Uses trailing return type syntax

---

## 🔄 PARTIAL/BLOCKED BENCHMARKS

### 2. MPI Latency (MULTI-NODE) - **NETWORK ISSUES**
- **Command**: `mpirun -np 4 --hostfile hostfile --mca btl tcp,self --mca pml ob1 bin/mpi_latency`
- **Status**: ❌ Network interface pairing failures
- **Error**: "Unable to find reachable pairing between local and remote interfaces"
- **Root Cause**: 
  - Nodes cannot establish TCP connections for MPI communication
  - Possible firewall blocking between nodes
  - Different network interface names (eth0 vs others)
  - May need explicit IP/subnet specification
- **Next Steps**:
  1. Check firewall rules: `sudo firewall-cmd --list-all` on each node
  2. Verify network connectivity: `ping` between all node pairs
  3. Use `--mca btl_tcp_if_exclude lo` to exclude loopback
  4. Try `--mca oob_tcp_if_include <subnet>` to specify network range

### 3. Hybrid MPI+OpenMP - **SAME AS MPI**
- **Command**: `mpirun -np 4 -x OMP_NUM_THREADS=38 --hostfile hostfile bin/hybrid_mpi_openmp`
- **Status**: ❌ Same network pairing issues as MPI
- **Configuration**: 4 MPI processes × 38 OpenMP threads = 152 total parallelism
- **Issue**: MPI component fails before OpenMP can execute
- **C++23 Compliance**: ✅ Uses trailing return type syntax

### 4. OpenSHMEM Latency - **PMI CONFIGURATION**
- **Command**: `oshrun -np 4 --hostfile hostfile --mca btl tcp,self bin/openshmem_latency 100`
- **Status**: ❌ PMI reports only 1 PE instead of N PEs
- **Symptoms**:
  ```
  $ oshrun -np 2 bin/openshmem_latency
  PE 0 of 1
  PE 0 of 1  # Should be "PE 0 of 2" and "PE 1 of 2"
  ```
- **Root Cause**: PMI (Process Management Interface) not properly initializing PE counts
- **Dependencies**:
  - libfabric 2.3.1 (OFI transport) - ✅ Installed
  - OpenSHMEM 1.5.3 built with `--enable-pmi-simple` - ✅ Built
  - Open MPI 5.0.8 - ✅ Installed
- **Possible Solutions**:
  1. Rebuild OpenSHMEM with PMIx instead of PMI-simple
  2. Configure Open MPI with PMI support: `ompi_info | grep pmi`
  3. Use Slurm's PMI2 interface once Slurm is fully configured
  4. Check if munge is running (required for some PMI implementations)
- **libfabric Issues**: 
  - ❌ Needs passwordless sudo to create system-wide symlinks
  - Currently `/usr/lib64/libfabric.so.1` not found by oshrun
- **C++23 Compliance**: ✅ Uses trailing return type syntax

### 5. UPC++ Latency (GASNet) - **NETWORK ROUTING**
- **Command**: `GASNET_SSH_SERVERS=node_list upcxx-run -n 4 bin/upcxx_latency`
- **Status**: ❌ GASNet connection failures
- **Error**: "No route to host (113)" and "connection closed on recv()"
- **Root Cause**:
  - GASNet SSH spawning cannot establish connections
  - Possible firewall blocking GASNet ports
  - May need explicit GASNet conduit configuration
- **Configuration**:
  - GASNet-EX 2025.8.0 installed
  - Using SSH spawning method
  - GASNET_SSH_SERVERS set correctly
- **Next Steps**:
  1. Test GASNet with `upcxx-run -n 2` locally first
  2. Configure GASNet conduit: UDP vs MPI vs IBV
  3. Check if GASNet ports (default: random high ports) are open
  4. Try `GASNET_SPAWN_SSH_OPTIONS="-v"` for debugging
- **C++23 Compliance**: ✅ Uses trailing return type syntax

---

## 📊 INFRASTRUCTURE STATUS

### PGAS Libraries Installed
| Library | Version | Status | Location |
|---------|---------|--------|----------|
| UPC++ | 2025.10.0 | ✅ Installed | `/home/linuxbrew/.linuxbrew/upcxx` |
| OpenSHMEM (SOS) | 1.5.3 | ✅ Installed | `/home/linuxbrew/.linuxbrew/openshmem` |
| GASNet-EX | 2025.8.0 | ✅ Installed | `/home/linuxbrew/.linuxbrew/gasnet` |
| libfabric (OFI) | 2.3.1 | ⚠️ Partial | Needs system symlinks |

### Cluster Configuration
| Node | Hostname | IP | CPUs | Memory | Status |
|------|----------|-----|------|--------|--------|
| Master | oluwasanmiredhatserver | 192.168.1.136 | 88 | 257 GB | ✅ Online |
| Worker 1 | DESKTOP-3SON9JT | 192.168.1.147 | 32 | 64 GB | ✅ Online |
| Worker 2 | muyiwadroexperiments | 192.168.1.139 | 16 | 32 GB | ✅ Online |
| Worker 3 | oluubuntul1 | 192.168.1.96 | 16 | 32 GB | ✅ Online |

### Slurm Status
- **Version**: 22.05.9
- **Controller (slurmctld)**: ❌ Not running (munge/cluster name issues)
- **Daemons (slurmd)**: ✅ Installed on all nodes
- **Configuration**: Updated but requires munge authentication
- **Next Steps**: Configure munge for authentication, resolve cluster name mismatch

### Compilers
| Compiler | Version | Status |
|----------|---------|--------|
| GCC | 15.2.0 (Homebrew) | ✅ Working |
| G++ | 15.2.0 (Homebrew) | ✅ Working |
| OpenMPI mpicc/mpicxx | 5.0.8 | ✅ Working |
| oshcc/oshc++ | 1.5.3 (wraps GCC 15.2.0) | ✅ Working |
| upcxx | 2025.10.0 | ✅ Working |

---

## 🔧 REQUIRED FIXES

### Critical (Blocking Multi-Node Execution)

1. **Fix MPI Network Connectivity**
   - Check firewall rules on all nodes
   - Ensure TCP connections allowed between all node pairs
   - Verify network interface configuration
   - Test with: `mpirun -np 2 -H node1,node2 hostname`

2. **Configure Passwordless Sudo for System Libraries**
   - Needed for libfabric symlinks: `/usr/lib64/libfabric.so.1`
   - Needed for Slurm configuration distribution
   - Alternative: Use LD_LIBRARY_PATH in all benchmark scripts

3. **Fix OpenSHMEM PMI Integration**
   - Option A: Rebuild OpenSHMEM with PMIx
   - Option B: Configure munge for PMI authentication
   - Option C: Use Slurm's PMI2 once Slurm is running
   - Test with: `ompi_info | grep pmi` to verify PMI support

### High Priority (Improves Functionality)

4. **Configure Slurm Cluster**
   - Install and configure munge on all nodes
   - Start munge service: `systemctl start munge`
   - Clear old Slurm state files
   - Start slurmctld on master node
   - Start slurmd on all worker nodes
   - Verify with: `sinfo -Nel`

5. **GASNet Network Configuration**
   - Determine which GASNet conduit to use (UDP, MPI, SMP)
   - Configure firewall to allow GASNet ports
   - Test SSH spawning works: `upcxx-run -n 2 hostname`
   - Consider using MPI conduit instead of SSH

### Medium Priority (Optimization)

6. **Network Performance Tuning**
   - Increase TCP buffer sizes for large messages
   - Disable TCP Nagle algorithm for low latency
   - Configure RDMA if InfiniBand available
   - Use `--mca btl_tcp_eager_limit` and `--mca btl_tcp_rndv_eager_limit`

7. **Benchmark Enhancement**
   - Add Berkeley UPC benchmarks
   - Create Slurm job scripts for automated submission
   - Add performance visualization/plotting
   - Implement comprehensive logging and result storage

---

## 📝 TESTING COMMANDS

### OpenMP (Working)
```bash
pdsh -w 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136 \
  "cd ~/cluster_build_sources/benchmarks && bin/openmp_parallel"
```

### MPI (Needs Fixing)
```bash
cd ~/cluster_build_sources/benchmarks
mpirun -np 4 --hostfile hostfile \
  --mca btl tcp,self --mca pml ob1 --map-by node \
  bin/mpi_latency
```

### Hybrid MPI+OpenMP (Needs Fixing)
```bash
cd ~/cluster_build_sources/benchmarks
mpirun -np 4 --hostfile hostfile \
  --mca btl tcp,self --mca pml ob1 --map-by node \
  -x OMP_NUM_THREADS=38 -x OMP_PROC_BIND=close \
  bin/hybrid_mpi_openmp
```

### OpenSHMEM (Needs Fixing)
```bash
cd ~/cluster_build_sources/benchmarks
oshrun -np 4 --hostfile hostfile \
  --mca btl tcp,self --mca pml ob1 --map-by node \
  bin/openshmem_latency 100
```

### UPC++ (Needs Fixing)
```bash
cd ~/cluster_build_sources/benchmarks
export GASNET_SSH_SERVERS="192.168.1.136,192.168.1.147,192.168.1.139,192.168.1.96"
upcxx-run -n 4 bin/upcxx_latency
```

---

## 🎯 NEXT STEPS

1. **Immediate**: Fix MPI network connectivity (highest priority)
   - Debug with verbose MPI output: `--mca btl_base_verbose 100`
   - Test simple hostname exchange first
   - Check firewall rules and network routing

2. **Short Term**: Configure passwordless sudo or LD_LIBRARY_PATH
   - Enables libfabric to load properly
   - Allows system-wide configuration changes
   - Alternative: Update all scripts to export LD_LIBRARY_PATH

3. **Medium Term**: Fix OpenSHMEM PMI and UPC++ GASNet
   - Both depend on proper multi-node communication
   - May require Slurm PMI2 to be working
   - Consider PMIx as modern replacement for PMI

4. **Long Term**: Full Slurm integration
   - Enables job queue management
   - Provides resource allocation and accounting
   - Allows fair sharing among multiple users

---

## 📚 REFERENCES

- [Open MPI FAQ - TCP BTL](https://www.open-mpi.org/faq/?category=tcp)
- [OpenSHMEM Specification 1.5](http://openshmem.org/)
- [UPC++ Documentation](https://upcxx.lbl.gov/)
- [GASNet-EX Documentation](https://gasnet.lbl.gov/)
- [Slurm Configuration](https://slurm.schedmd.com/configurator.html)

---

**Generated**: November 4, 2025  
**Cluster**: 4 nodes, 152 cores, GCC 15.2.0, OpenMPI 5.0.8  
**Status**: OpenMP fully working, MPI/PGAS debugging in progress
