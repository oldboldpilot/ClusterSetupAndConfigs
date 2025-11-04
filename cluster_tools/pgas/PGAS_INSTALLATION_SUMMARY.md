# PGAS Installation Summary
**Date**: November 3, 2025
**Cluster**: 4-node HPC cluster (master + 3 workers)

## Installed Components

### GASNet-EX 2025.8.0
- **Location**: `/home/linuxbrew/.linuxbrew/gasnet`
- **Source**: `~/cluster_build_sources/GASNet-2025.8.0`
- **Conduits Enabled**:
  - SMP (shared memory) - single-node parallelism
  - UDP (sockets) - multi-node over TCP/IP
  - MPI (via OpenMPI 5.0.8) - multi-node via MPI
- **Libraries**: 9 total (3 conduits × 3 modes: seq/par/parsync)
- **Configuration**: 
  ```bash
  CFLAGS="-O3 -Wno-incompatible-pointer-types" \
  ./configure --prefix=/home/linuxbrew/.linuxbrew/gasnet \
    --enable-mpi --enable-smp --enable-udp \
    --with-mpicc=/home/linuxbrew/.linuxbrew/bin/mpicc \
    --disable-seq --enable-par
  ```

### UPC++ 2025.10.0
- **Location**: `/home/linuxbrew/.linuxbrew/upcxx`
- **Source**: `~/cluster_build_sources/upcxx-2025.10.0`
- **Compiler**: `/home/linuxbrew/.linuxbrew/bin/upcxx`
- **Runtime**: `/home/linuxbrew/.linuxbrew/bin/upcxx-run`
- **Default Network**: UDP
- **Available Networks**: SMP, UDP, MPI
- **Configuration**:
  ```bash
  ./configure --prefix=/home/linuxbrew/.linuxbrew/upcxx \
    --with-gasnet=$HOME/cluster_build_sources/GASNet-2025.8.0 \
    --with-cc=/home/linuxbrew/.linuxbrew/bin/mpicc \
    --with-cxx=/home/linuxbrew/.linuxbrew/bin/mpicxx \
    --with-ldflags="-L/home/linuxbrew/.linuxbrew/Cellar/glibc/2.35_2/lib \
                    -Wl,-rpath,/home/linuxbrew/.linuxbrew/Cellar/glibc/2.35_2/lib -lm"
  ```

## Required System Libraries

### GNU Binutils 2.45 (Homebrew)
- **Purpose**: Modern assembler with `.base64` directive support
- **Symlinks**: 
  - `/usr/local/bin/as` → `/home/linuxbrew/.linuxbrew/opt/binutils/bin/as`
  - `/usr/local/bin/ld` → `/home/linuxbrew/.linuxbrew/opt/binutils/bin/ld`
  - `/usr/local/bin/ar` → `/home/linuxbrew/.linuxbrew/opt/binutils/bin/ar`
  - `/usr/local/bin/ranlib` → `/home/linuxbrew/.linuxbrew/opt/binutils/bin/ranlib`

### GLIBC 2.35 (Homebrew)
- **Location**: `/home/linuxbrew/.linuxbrew/Cellar/glibc/2.35_2/lib`
- **Purpose**: Provides modern GLIBC symbols (log2@GLIBC_2.29, fesetround@GLIBC_2.2.5, etc.)
- **Linked via**: `-L${glibc_lib} -Wl,-rpath,${glibc_lib} -lm`

### Python 3.14 (Homebrew)
- **Symlinks**:
  - `/usr/local/bin/python3` → `/home/linuxbrew/.linuxbrew/bin/python3`
  - `/usr/local/bin/pip3` → `/home/linuxbrew/.linuxbrew/bin/pip3`

## Build Issues Resolved

1. **GLIBC Version Mismatch**:
   - Error: Missing libm.so.6, undefined references to GLIBC_2.29 symbols
   - Solution: Link against Homebrew GLIBC 2.35 with explicit rpath

2. **Assembler .base64 Directive**:
   - Error: "unknown pseudo-op: `.base64`" (binutils < 2.38)
   - Solution: Use Homebrew binutils 2.45 via symlinks in /usr/local/bin

3. **GCC 15 Compatibility**:
   - Warning: Incompatible pointer types in GASNet
   - Solution: Added `-Wno-incompatible-pointer-types` to CFLAGS

## Cluster Distribution

All installations distributed via rsync to:
- Master node: 192.168.1.147 (WSL2, 32 threads)
- Worker1: 192.168.1.139 (Ubuntu, 16 threads)
- Worker2: 192.168.1.96 (Ubuntu, 16 threads)
- Worker3: 192.168.1.136 (Red Hat, 88 threads) [build node]

## Testing

Single-node test (SMP conduit):
```bash
upcxx hello.cpp -o hello
GASNET_PSHM_NODES=4 upcxx-run -n 4 -shared-heap 128M ./hello
```

Multi-node test (UDP conduit):
```bash
export GASNET_SSH_SERVERS="node1,node2,node3,node4"
upcxx-run -n 16 ./hello
```

## Next Steps

1. Install OpenSHMEM 1.5.2 (Sandia implementation)
2. Test multi-node UPC++ applications
3. Benchmark PGAS performance vs MPI
4. Document application migration guide
