# PGAS Configuration and Tools

**Partitioned Global Address Space (PGAS)** programming model support for the HPC cluster.

## Contents

### Documentation

- **[PGAS_INSTALLATION_SUMMARY.md](PGAS_INSTALLATION_SUMMARY.md)** - Complete installation record of UPC++, GASNet-EX, and OpenSHMEM
- **[PGAS_STATUS.md](PGAS_STATUS.md)** - Current status and configuration of PGAS libraries
- **[PGAS_TESTING_GUIDE.md](PGAS_TESTING_GUIDE.md)** - Comprehensive testing guide for PGAS installations

### Scripts

- **[execute_pgas_config.py](execute_pgas_config.py)** - Legacy PGAS configuration script (deprecated, use `../configure_pgas.py`)

## PGAS Libraries Installed

### 1. UPC++ 2025.10.0
- **Location**: `/home/linuxbrew/.linuxbrew/upcxx`
- **Compiler**: `/home/linuxbrew/.linuxbrew/bin/upcxx`
- **Runtime**: `/home/linuxbrew/.linuxbrew/bin/upcxx-run`
- **Documentation**: https://upcxx.lbl.gov/

### 2. GASNet-EX 2025.8.0
- **Location**: `/home/linuxbrew/.linuxbrew/gasnet`
- **Conduits**: SMP (shared memory), UDP (sockets), MPI (via OpenMPI)
- **Libraries**: 9 libraries (3 conduits × 3 modes: seq/par/parsync)

### 3. OpenSHMEM 1.5.2
- **Location**: `/home/linuxbrew/.linuxbrew/openshmem`
- **Compiler**: `/home/linuxbrew/.linuxbrew/bin/oshcc`
- **Runtime**: `/home/linuxbrew/.linuxbrew/bin/oshrun`
- **Implementation**: Sandia OpenSHMEM (SOS)

## System Requirements

### Required Libraries (Homebrew)
- **GNU Binutils 2.45** - Modern assembler supporting `.base64` directive
- **GLIBC 2.35** - Provides required GLIBC_2.29+ symbols
- **Python 3.14** - Build tools and scripts

### System Symlinks
Created in `/usr/local/bin/` for cluster-wide consistency:
```
as -> /home/linuxbrew/.linuxbrew/opt/binutils/bin/as
ld -> /home/linuxbrew/.linuxbrew/opt/binutils/bin/ld
ar -> /home/linuxbrew/.linuxbrew/opt/binutils/bin/ar
ranlib -> /home/linuxbrew/.linuxbrew/opt/binutils/bin/ranlib
python3 -> /home/linuxbrew/.linuxbrew/bin/python3
pip3 -> /home/linuxbrew/.linuxbrew/bin/pip3
```

## Quick Start

### 1. Configure PGAS Cluster-Wide
```bash
cd /home/muyiwa/Development/ClusterSetupAndConfigs
python3 cluster_tools/configure_pgas.py
```

This will:
- Configure passwordless sudo
- Distribute system symlinks
- Test multi-node UPC++
- Install OpenSHMEM
- Create benchmark suite

### 2. Test UPC++ Single Node (SMP)
```bash
cd ~/cluster_build_sources/upcxx_tests
upcxx hello_multinode.cpp -o hello_smp
GASNET_PSHM_NODES=1 upcxx-run -n 4 ./hello_smp
```

### 3. Test UPC++ Multi-Node (UDP)
```bash
export GASNET_SSH_SERVERS='192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136'
upcxx -network=udp hello_multinode.cpp -o hello_udp
upcxx-run -n 16 ./hello_udp
```

### 4. Test OpenSHMEM
```bash
oshcc -o test test.c
oshrun -np 4 ./test
```

### 5. Run Benchmarks
```bash
cd ~/cluster_build_sources/pgas_benchmarks
./run_benchmarks.sh
```

## Cluster Configuration

### 4-Node HPC Cluster
- **Master**: 192.168.1.147 (WSL2, 32 threads)
- **Worker1**: 192.168.1.139 (Ubuntu, 16 threads)
- **Worker2**: 192.168.1.96 (Ubuntu, 16 threads)
- **Worker3**: 192.168.1.136 (Red Hat, 88 threads) - Build node

### Passwordless Sudo
Configured via `/etc/sudoers.d/cluster-ops` for operations:
- ln, rsync, systemctl, mkdir, chmod, chown, tee, cp

## Environment Variables

Add to `~/.bashrc`:
```bash
# UPC++ and PGAS Environment
export UPCXX_INSTALL=/home/linuxbrew/.linuxbrew/upcxx
export GASNET_INSTALL=/home/linuxbrew/.linuxbrew/gasnet
export OPENSHMEM_INSTALL=/home/linuxbrew/.linuxbrew/openshmem
export PATH=$UPCXX_INSTALL/bin:$OPENSHMEM_INSTALL/bin:$PATH
export LD_LIBRARY_PATH=$GASNET_INSTALL/lib:$UPCXX_INSTALL/lib:$OPENSHMEM_INSTALL/lib:$LD_LIBRARY_PATH
export GASNET_SSH_SERVERS='192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136'
```

## Benchmarking

### PGAS vs MPI Performance Comparison
Located in `~/cluster_build_sources/pgas_benchmarks/`

**Benchmarks:**
- Point-to-point latency (UPC++ vs MPI)
- Point-to-point bandwidth (planned)
- Collective operations (planned)
- One-sided operations (planned)

**Running:**
```bash
cd ~/cluster_build_sources/pgas_benchmarks
make all
./run_benchmarks.sh
```

**Results:** Stored in `~/cluster_build_sources/pgas_benchmarks/results/`

## Troubleshooting

### Issue: GASNET_SSH_SERVERS missing
**Solution**: Set environment variable before running
```bash
export GASNET_SSH_SERVERS='192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136'
```

### Issue: Sudo password required
**Solution**: Run configure_pgas.py to setup passwordless sudo
```bash
python3 cluster_tools/configure_pgas.py
```

### Issue: Binary not found
**Solution**: Source bashrc or add to PATH
```bash
source ~/.bashrc
# or
export PATH=/home/linuxbrew/.linuxbrew/upcxx/bin:$PATH
```

### Issue: Library not found at runtime
**Solution**: Add to LD_LIBRARY_PATH
```bash
export LD_LIBRARY_PATH=/home/linuxbrew/.linuxbrew/gasnet/lib:$LD_LIBRARY_PATH
```

## References

- **UPC++ Documentation**: https://upcxx.lbl.gov/docs/html/guide.html
- **GASNet-EX**: https://gasnet.lbl.gov/
- **OpenSHMEM**: https://github.com/Sandia-OpenSHMEM/SOS
- **PGAS Programming**: https://en.wikipedia.org/wiki/Partitioned_global_address_space

## Migration Notes

**Old location**: Repository root  
**New location**: `cluster_tools/pgas/`  
**Migration date**: November 4, 2025

All PGAS-related files have been consolidated into this module for better organization.
