# Template-Based Configuration System

## Overview

This document describes the template-based configuration management system implemented for the HPC cluster. The system uses Jinja2 templates to generate all configuration files, ensuring consistency and maintainability.

## Directory Structure

```
ClusterSetupAndConfigs/
├── templates/
│   ├── mpi/
│   │   ├── mca-params.conf.j2      # OpenMPI MCA parameters
│   │   └── hostfile.j2              # MPI hostfile
│   ├── ssh/
│   │   └── config.j2                # SSH configuration
│   ├── slurm/
│   │   └── slurm.conf.j2            # Slurm cluster config
│   └── benchmarks/
│       ├── openmp/
│       ├── mpi/
│       ├── hybrid/
│       ├── openshmem/
│       └── upcxx/
├── docs/
│   ├── configuration/
│   │   └── PGAS_CONFIGURATION.md
│   ├── troubleshooting/
│   │   ├── MPI_NETWORK_FIX.md
│   │   └── MULTI_NODE_BENCHMARK_STATUS.md
│   └── benchmarks/
│       ├── openmp/
│       ├── mpi/
│       ├── hybrid/
│       ├── openshmem/
│       └── upcxx/
└── cluster_modules/
    ├── config_template_manager.py   # Main template manager
    ├── mpi_network_config.py        # MPI network configuration
    └── multi_node_runner.py         # Multi-node benchmark orchestration
```

## Key Components

### 1. ConfigTemplateManager

Located in `cluster_modules/config_template_manager.py`, this is the central component for template-based configuration management.

**Features:**
- Loads cluster configuration from `cluster_config_actual.yaml`
- Generates configuration files from Jinja2 templates
- Deploys configurations to all cluster nodes
- Validates deployment

**Usage:**

```bash
# Show cluster summary
uv run python cluster_modules/config_template_manager.py summary

# Generate MPI MCA configuration
uv run python cluster_modules/config_template_manager.py generate mpi-mca

# Deploy MPI configuration to all nodes
uv run python cluster_modules/config_template_manager.py deploy mpi-mca

# Generate MPI hostfile
uv run python cluster_modules/config_template_manager.py generate mpi-hostfile --output hostfile

# Generate SSH configuration
uv run python cluster_modules/config_template_manager.py generate ssh --output ~/.ssh/config

# Generate Slurm configuration
uv run python cluster_modules/config_template_manager.py generate slurm --output slurm.conf
```

### 2. MPI Network Configuration Template

**Template:** `templates/mpi/mca-params.conf.j2`

Generates `~/.openmpi/mca-params.conf` with:
- BTL (Byte Transfer Layer) TCP configuration
- Network interface selection (192.168.1.0/24 subnet)
- OpenMPI installation paths
- Port configuration (50000-50200)
- Debug options (configurable)
- TCP optimization parameters

**Key Variables:**
- `cluster_subnet`: Network subnet (e.g., "192.168.1.0/24")
- `cluster_ips`: List of all cluster node IPs
- `openmpi_version`: OpenMPI version installed
- `homebrew_prefix`: Homebrew installation directory
- `btl_port_min`: Minimum BTL TCP port (default: 50000)
- `oob_port_range`: OOB port range (default: "50100-50200")
- `enable_debug`: Enable verbose debugging

**Solution to "Unable to find reachable pairing" Error:**

The template automatically:
1. Uses subnet notation (`192.168.1.0/24`) to include only cluster IPs
2. Excludes virtual interfaces (Docker, libvirt, WSL) automatically
3. Configures both BTL and OOB interfaces consistently
4. Sets proper OpenMPI prefixes for remote node execution

### 3. MPI Hostfile Template

**Template:** `templates/mpi/hostfile.j2`

Generates hostfile for `mpirun` with proper slot allocation.

**Slot Modes:**
- `max`: Use all available CPUs on each node
- `optimal`: Use 1 slot per node (for distributed computing)
- Integer: Use specific number of slots per node

**Example Output:**
```
# MPI Hostfile
# Auto-generated from template: templates/mpi/hostfile.j2
# Generated: 2025-11-04 18:34:33
# Cluster: hpc_cluster

192.168.1.136 slots=88  # oluwasanmiredhatserver (all cores)
192.168.1.139 slots=16  # muyiwadroexperiments (all cores)
192.168.1.96 slots=16   # olubuuntul1 (all cores)
192.168.1.147 slots=32  # DESKTOP-3SON9JT (all cores)

# Total slots: 152
```

### 4. SSH Configuration Template

**Template:** `templates/ssh/config.j2`

Generates `~/.ssh/config` with:
- Connection multiplexing (ControlMaster)
- Keep-alive settings
- Compression enabled
- Optimized timeouts
- Per-node configuration

**Benefits:**
- Faster repeated SSH connections
- Connection reuse reduces overhead
- Persistent connections for 10 minutes

### 5. Slurm Configuration Template

**Template:** `templates/slurm/slurm.conf.j2`

Generates `/etc/slurm/slurm.conf` with:
- Cluster-wide settings
- Node definitions (master + workers)
- Partition definitions (all, compute, debug)
- MPI integration (PMI2/PMIx)
- Resource limits
- Logging configuration

## Configuration File Format

### cluster_config_actual.yaml

```yaml
master:
  - ip: 192.168.1.136
    os: redhat
    name: oluwasanmiredhatserver

workers:
  - ip: 192.168.1.139
    os: ubuntu
    name: muyiwadroexperiments
  - ip: 192.168.1.96
    os: ubuntu
    name: olubuuntul1
  - ip: 192.168.1.147
    os: ubuntu wsl2
    name: DESKTOP-3SON9JT

username: muyiwa

threads:
  192.168.1.136: 88
  192.168.1.139: 16
  192.168.1.96: 16
  192.168.1.147: 32
```

## Workflow

### Initial Setup

1. **Update Configuration:**
   ```bash
   vim cluster_config_actual.yaml
   # Edit master and worker nodes
   ```

2. **Deploy MPI Configuration:**
   ```bash
   uv run python cluster_modules/config_template_manager.py deploy mpi-mca
   ```

3. **Generate Hostfile:**
   ```bash
   uv run python cluster_modules/config_template_manager.py generate mpi-hostfile \
     --output ~/cluster_build_sources/benchmarks/hostfile
   ```

4. **Test Configuration:**
   ```bash
   cd ~/cluster_build_sources/benchmarks
   mpirun -np 4 --hostfile hostfile --map-by ppr:1:node hostname
   ```

### Adding a New Node

1. Add to `cluster_config_actual.yaml`:
   ```yaml
   workers:
     - ip: 192.168.1.200
       os: ubuntu
       name: newworker
   
   threads:
     192.168.1.200: 32
   ```

2. Regenerate and redeploy:
   ```bash
   uv run python cluster_modules/config_template_manager.py deploy mpi-mca
   uv run python cluster_modules/config_template_manager.py generate mpi-hostfile \
     --output ~/cluster_build_sources/benchmarks/hostfile
   ```

### Troubleshooting

#### Check Cluster Status
```bash
uv run python cluster_modules/config_template_manager.py summary
```

#### Verify Deployment
```bash
uv run python cluster_modules/config_template_manager.py deploy mpi-mca
# Check output for ✓ or ✗ for each node
```

#### Clean Stuck Processes
```bash
pdsh -w 192.168.1.136,192.168.1.147,192.168.1.139,192.168.1.96 \
  "pkill -9 -f 'mpi_latency|prterun|prted|orted'"
```

#### Enable Debug Mode
```bash
# Generate MPI config with debugging
uv run python cluster_modules/config_template_manager.py generate mpi-mca --debug \
  > /tmp/mca-debug.conf
  
# Deploy debug config
uv run python cluster_modules/config_template_manager.py deploy mpi-mca
```

## Benefits of Template System

1. **Consistency:** All nodes get identical configuration
2. **Maintainability:** Single source of truth for cluster setup
3. **Automation:** No manual editing of configuration files
4. **Version Control:** Templates are tracked in git
5. **Documentation:** Generated configs include timestamps and comments
6. **Flexibility:** Easy to add new nodes or change settings
7. **Testing:** Can generate configs without deploying

## Known Issues and Solutions

### Issue 1: MPI "Unable to find reachable pairing"

**Solution:** Template automatically configures subnet-based interface selection, excluding virtual interfaces.

### Issue 2: Stuck MPI Processes

**Solution:** Use cleanup script:
```bash
pdsh -w all_nodes "pkill -9 -f 'mpi_latency|prterun|prted'"
```

### Issue 3: WSL Node Connectivity

**Requirements:**
- WSL mirrored networking mode enabled in `.wslconfig`
- Windows Firewall configured for ports 50000-50200
- See `docs/troubleshooting/MPI_NETWORK_FIX.md`

## Future Enhancements

1. **Benchmark Templates:** Add templates for benchmark source files
2. **Job Submission Templates:** Slurm job scripts
3. **Monitoring Templates:** Prometheus/Grafana configurations
4. **Backup Templates:** Automated backup scripts
5. **Testing Framework:** Automated validation of deployed configs

## References

- **MPI Network Fix:** `docs/troubleshooting/MPI_NETWORK_FIX.md`
- **PGAS Configuration:** `docs/configuration/PGAS_CONFIGURATION.md`
- **Multi-Node Status:** `docs/troubleshooting/MULTI_NODE_BENCHMARK_STATUS.md`
- **OpenMPI Documentation:** https://docs.open-mpi.org/
- **Jinja2 Documentation:** https://jinja.palletsprojects.com/
