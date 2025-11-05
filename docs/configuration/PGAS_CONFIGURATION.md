# PGAS Library Configuration Guide

## Overview
This document describes the modular PGAS (Partitioned Global Address Space) configuration system implemented for the cluster. All PGAS libraries use **C++23 standard with trailing return type syntax** for consistency.

## Installed PGAS Libraries

### 1. UPC++ (2025.10.0)
- **Installation Path**: `/home/linuxbrew/.linuxbrew/upcxx`
- **Compiler**: `upcxx` (C++23 compiler wrapper)
- **Runtime**: `upcxx-run` (job launcher)
- **Status**: ✅ Installed and tested on all nodes
- **Backend**: GASNet-EX 2025.8.0

### 2. OpenSHMEM (1.5.3 - Sandia OpenSHMEM)
- **Installation Path**: `/home/linuxbrew/.linuxbrew/openshmem`
- **Compilers**:
  - `oshcc` - C compiler wrapper
  - `oshc++` - C++ compiler wrapper (use for C++23 code)
  - `oshfort` - Fortran compiler wrapper
- **Runtime**: `oshrun` (based on Open MPI 5.0.8)
- **Status**: ✅ Installed on all nodes, PMI configuration pending
- **Transport**: OFI (libfabric 2.3.1)
- **Features**: Thread support, hwloc support, PMI-simple enabled

### 3. GASNet-EX (2025.8.0)
- **Installation Path**: `/home/linuxbrew/.linuxbrew/gasnet`
- **Status**: ✅ Installed (UPC++ dependency)
- **Purpose**: Communication substrate for UPC++

### 4. Berkeley UPC (Future)
- **Status**: ❌ Not yet installed
- **Planned Installation**: `/home/linuxbrew/.linuxbrew/bupc`

## Configuration Module

### Location
`cluster_modules/pgas_config.py`

### Usage
```python
from cluster_modules.pgas_config import PGASConfig

# Check installation status
status = PGASConfig.check_installation()
# Returns: {'GASNet': True, 'UPC++': True, 'OpenSHMEM': True, 'Berkeley UPC': False}

# Get compiler flags
upcxx_flags = PGASConfig.get_upcxx_flags()
openshmem_flags = PGASConfig.get_openshmem_flags()

# Get library information
upcxx_info = PGASConfig.get_library_info('upcxx')
openshmem_info = PGASConfig.get_library_info('openshmem')

# Get environment variables
env_vars = PGASConfig.get_env_vars()
```

### Key Features
1. **Centralized Version Management**: All library versions in one place
2. **Path Abstraction**: No hardcoded paths in application code
3. **Compiler Discovery**: Automatic compiler path resolution
4. **Environment Setup**: Automated PATH and LD_LIBRARY_PATH configuration
5. **Installation Verification**: Check which libraries are available

## Cluster Distribution

### Distribution Status (4 nodes, 152 cores total)

| Node | IP | Cores | OpenSHMEM | libfabric | Symlinks | Status |
|------|-----|-------|-----------|-----------|----------|--------|
| oluwasanmiredhatserver | 192.168.1.136 | 88 | ✅ | ✅ | ✅ | Master |
| DESKTOP-3SON9JT | 192.168.1.147 | 32 | ✅ | ✅ | ✅ | Worker |
| muyiwadroexperiments | 192.168.1.139 | 16 | ✅ | ✅ | ✅ | Worker |
| oluubuntul1 | 192.168.1.96 | 16 | ✅ | ✅ | ✅ | Worker |

### Distribution Commands Used
```bash
# OpenSHMEM installation (~11.5MB per node)
for node in 192.168.1.147 192.168.1.139 192.168.1.96; do
    rsync -avz /home/linuxbrew/.linuxbrew/openshmem/ $node:/home/linuxbrew/.linuxbrew/openshmem/
done

# libfabric OFI transport (~5.4MB per node)
for node in 192.168.1.147 192.168.1.139 192.168.1.96; do
    rsync -avz /home/linuxbrew/.linuxbrew/Cellar/libfabric/ $node:/home/linuxbrew/.linuxbrew/Cellar/libfabric/
done

# Create symlinks on all nodes
for node in 192.168.1.147 192.168.1.139 192.168.1.96; do
    ssh $node "cd /home/linuxbrew/.linuxbrew/bin && \
        ln -sf ../openshmem/bin/oshcc oshcc && \
        ln -sf ../openshmem/bin/oshc++ oshc++ && \
        ln -sf ../openshmem/bin/oshfort oshfort && \
        ln -sf ../openshmem/bin/oshrun oshrun"
done
```

## C++23 Compliance

### All Benchmarks Use Trailing Return Type Syntax

✅ **Compliant Benchmarks:**
- `openmp_parallel.cpp` - `auto compute_work(...) -> double`
- `hybrid_mpi_openmp.cpp` - `auto compute_hybrid_work(...) -> double`
- `mpi_latency.cpp` - `auto measure_latency(...) -> void`
- `openshmem_latency.cpp` - `auto measure_latency(...) -> void`
- `upcxx_latency.cpp` - `auto ping_response() -> int`, `auto measure_latency(...) -> void`
- `upcxx_bandwidth.cpp` - `auto measure_bandwidth(...) -> void`

### Makefile Configuration
```makefile
# C++23 flags for all PGAS compilers
UPCXX_FLAGS = -std=c++23 -O3
OSHCC_FLAGS = -std=c++23 -O3
OPENMP_FLAGS = -std=c++23 -O3 -fopenmp
MPICXX_FLAGS = -std=c++23 -O3
```

## Known Issues and Solutions

### Issue 1: OpenSHMEM Multi-PE Execution
**Problem**: `oshrun -np 2` launches 2 processes but OpenSHMEM reports `shmem_n_pes() == 1`

**Root Cause**: PMI (Process Management Interface) not properly configured for multi-node/multi-PE communication

**Symptoms**:
```bash
$ oshrun -np 2 bin/openshmem_latency
PE 0 of 1
PE 0 of 1  # Should be "PE 0 of 2" and "PE 1 of 2"
```

**Potential Solutions** (to be tested):

1. **Use PMIx instead of PMI-simple**:
   ```bash
   # Rebuild OpenSHMEM with PMIx support
   ./configure --prefix=/home/linuxbrew/.linuxbrew/openshmem \
               --with-ofi=$(brew --prefix libfabric) \
               --with-pmix=/path/to/pmix \
               CC=/home/linuxbrew/.linuxbrew/bin/gcc
   ```

2. **Explicitly set OFI environment variables**:
   ```bash
   export FI_PROVIDER=tcp  # or sockets
   export SHMEM_SYMMETRIC_SIZE=1G
   oshrun -np 2 bin/openshmem_latency
   ```

3. **Use TCP BTL for better multi-node support**:
   ```bash
   oshrun -np 2 --mca btl self,tcp --mca btl_tcp_if_include eth0 bin/openshmem_latency
   ```

4. **Check if PMI is available in OpenMPI**:
   ```bash
   ompi_info | grep pmi
   ```

**Status**: 🔄 Investigation ongoing

### Issue 2: MPI Multi-Node Communication
**Problem**: MPI processes cannot communicate across nodes (BTL configuration)

**Status**: 🔄 Requires BTL parameter tuning or alternate transport configuration

## Benchmark Compilation

### Build All Benchmarks
```bash
cd ~/cluster_build_sources/benchmarks
make all
```

### Build Individual Benchmarks
```bash
make upcxx_latency      # UPC++ latency test
make upcxx_bandwidth    # UPC++ bandwidth test
make openshmem_latency  # OpenSHMEM latency test
make mpi_latency        # MPI latency test
make openmp_parallel    # OpenMP scaling test
make hybrid_mpi_openmp  # Hybrid MPI+OpenMP test
```

### Distribute Benchmarks to All Nodes
```bash
for node in 192.168.1.147 192.168.1.139 192.168.1.96; do
    rsync -avz ~/cluster_build_sources/benchmarks/bin/ $node:~/cluster_build_sources/benchmarks/bin/
done
```

## Testing Multi-Node PGAS Applications

### UPC++ Multi-Node Execution
```bash
export GASNET_SSH_SERVERS="192.168.1.136,192.168.1.147,192.168.1.139,192.168.1.96"
upcxx-run -n 4 bin/upcxx_latency
```

### OpenSHMEM Multi-Node Execution (when fixed)
```bash
# Create hostfile
cat > ~/.openmpi/hostfile << EOF
192.168.1.136 slots=88
192.168.1.147 slots=32
192.168.1.139 slots=16
192.168.1.96 slots=16
EOF

# Run across nodes
oshrun -np 4 --hostfile ~/.openmpi/hostfile bin/openshmem_latency
```

### OpenMP Multi-Node Execution (Already Working)
```bash
# Run on all nodes simultaneously
pdsh -w 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136 \
     "cd ~/cluster_build_sources/benchmarks && bin/openmp_parallel"
```

## Environment Setup

### Add to ~/.bashrc
```bash
# PGAS Library Configuration
export UPCXX_INSTALL=/home/linuxbrew/.linuxbrew/upcxx
export OPENSHMEM_INSTALL=/home/linuxbrew/.linuxbrew/openshmem
export GASNET_INSTALL=/home/linuxbrew/.linuxbrew/gasnet

export PATH=$UPCXX_INSTALL/bin:$OPENSHMEM_INSTALL/bin:$PATH
export LD_LIBRARY_PATH=$OPENSHMEM_INSTALL/lib:$GASNET_INSTALL/lib:$LD_LIBRARY_PATH

# GASNet configuration for multi-node
export GASNET_SSH_SERVERS="192.168.1.136,192.168.1.147,192.168.1.139,192.168.1.96"
```

## Future Enhancements

1. **PMIx Integration**: Replace PMI-simple with PMIx for better process management
2. **Berkeley UPC Installation**: Add BUPC to complete PGAS library suite
3. **Automated Testing**: Create comprehensive multi-node test suite
4. **Performance Profiling**: Add detailed performance analysis for each PGAS model
5. **Fault Tolerance**: Implement checkpoint/restart capabilities
6. **Dynamic Configuration**: Runtime selection of PGAS transport mechanisms

## References

- [OpenSHMEM Documentation](http://openshmem.org/)
- [UPC++ Documentation](https://upcxx.lbl.gov/)
- [GASNet-EX](https://gasnet.lbl.gov/)
- [Open MPI PMI Support](https://www.open-mpi.org/)
- [libfabric OFI](https://ofiwg.github.io/libfabric/)

---

**Last Updated**: November 4, 2025  
**Cluster Configuration**: 4 nodes, 152 cores total  
**Compiler Stack**: GCC 15.2.0, Open MPI 5.0.8  
**PGAS Standards**: C++23 with trailing return types
