# Cluster Tools Module

Utilities and helper scripts for HPC cluster management, PGAS configuration, and distributed computing workflows.

## Contents

### `configure_pgas.py`

Post-installation configuration tool for PGAS (Partitioned Global Address Space) libraries across the cluster.

**Features:**
- Configures passwordless sudo for cluster operations
- Distributes system symlinks (binutils 2.45, Python 3.14, UPC++)
- Tests multi-node UPC++ execution across all cluster nodes
- Installs and distributes OpenSHMEM 1.5.2
- Creates PGAS vs MPI benchmark suite

**Usage:**

```bash
# Using uv (recommended)
cd /home/muyiwa/Development/ClusterSetupAndConfigs
uv run python cluster_tools/configure_pgas.py

# Direct execution
python3 cluster_tools/configure_pgas.py

# With virtual environment
source .venv/bin/activate
python cluster_tools/configure_pgas.py
```

**Requirements:**
- Password for cluster nodes (prompted interactively, never hardcoded)
- Cluster configuration must match IPs in the script
- PGAS libraries (UPC++, GASNet-EX) already installed on build node
- Homebrew binutils, glibc, Python already installed

**What it does:**

1. **Passwordless Sudo**: Creates `/etc/sudoers.d/cluster-ops` on all nodes
2. **System Symlinks**: Distributes binutils/Python tools to `/usr/local/bin`
3. **UPC++ Testing**: Validates SMP, UDP, and MPI conduits across cluster
4. **OpenSHMEM**: Compiles and installs Sandia OpenSHMEM 1.5.2
5. **Benchmarks**: Creates point-to-point latency benchmarks (UPC++ vs MPI)

## Module Structure

```
cluster_tools/
├── __init__.py           # Package initialization
├── configure_pgas.py     # PGAS configuration tool
└── README.md            # This file
```

## Future Additions

Planned tools for this module:
- `benchmark_runner.py` - Automated benchmark execution and reporting
- `cluster_monitor.py` - Real-time cluster resource monitoring
- `deployment_manager.py` - Application deployment across cluster
- `health_check.py` - Cluster health verification and diagnostics

## Integration with cluster_setup.py

This module uses methods from the main `cluster_setup.py`:
- `configure_passwordless_sudo_cluster()`
- `distribute_system_symlinks_cluster()`
- `test_multinode_upcxx()`
- `install_openshmem_cluster()`
- `create_pgas_benchmark_suite()`

## Notes

- All operations require cluster password (provided via interactive prompt)
- Password is never hardcoded in any files
- Uses `self.password` from ClusterSetup instance
- Safe to run multiple times (operations are idempotent)
