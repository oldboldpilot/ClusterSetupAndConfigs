# Quick Reference Guide - Modular Benchmark System

## Project Structure

```
ClusterSetupAndConfigs/
├── cluster_modules/
│   ├── config_template_manager.py    # Configuration & firewall management
│   ├── benchmark_runner.py           # NEW: Modular pdsh-based runner
│   └── benchmark_manager.py          # Template-based PGAS benchmarks
│
├── scripts/
│   ├── setup_cluster_network.sh      # Complete cluster setup automation
│   └── benchmarks/
│       ├── run_all_benchmarks.sh     # Legacy: Comprehensive runner
│       ├── run_benchmarks_pdsh.sh    # Legacy: pdsh distribution
│       └── mpirun_cluster.sh         # Quick MPI launcher
│
├── templates/
│   ├── mpi/                          # MPI configuration templates
│   ├── ssh/                          # SSH configuration templates
│   └── slurm/                        # Slurm configuration templates
│
└── docs/
    ├── configuration/
    │   ├── TEMPLATE_SYSTEM.md
    │   ├── FIREWALL_SETUP.md
    │   └── PGAS_CONFIGURATION.md
    └── troubleshooting/
        ├── MPI_NETWORK_FIX.md
        ├── MULTI_HOMED_NODE_FIX.md
        └── MPI_BENCHMARK_DEBUGGING.md
```

## Common Workflows

### 1. Initial Cluster Setup

```bash
# Complete automated setup
cd /home/muyiwa/Development/ClusterSetupAndConfigs
./scripts/setup_cluster_network.sh

# Or manual step-by-step:
uv run python cluster_modules/config_template_manager.py deploy mpi-mca
uv run python cluster_modules/config_template_manager.py generate mpi-hostfile -o ~/cluster_build_sources/benchmarks/hostfile
uv run python cluster_modules/config_template_manager.py firewall configure
uv run python cluster_modules/config_template_manager.py firewall verify
```

### 2. Running Benchmarks (NEW Modular Way)

```bash
cd /home/muyiwa/Development/ClusterSetupAndConfigs

# List available benchmarks
uv run python cluster_modules/benchmark_runner.py list

# Sync binaries to all nodes
uv run python cluster_modules/benchmark_runner.py sync

# Run single benchmark
uv run python cluster_modules/benchmark_runner.py run mpi_latency --np 4 --timeout 60

# Run all benchmarks
uv run python cluster_modules/benchmark_runner.py run all --np 4

# Clean up stuck processes
uv run python cluster_modules/benchmark_runner.py cleanup
```

### 3. Running Benchmarks (Legacy Shell Scripts)

```bash
cd ~/cluster_build_sources/benchmarks

# Run all benchmarks (comprehensive)
bash ~/Development/ClusterSetupAndConfigs/scripts/benchmarks/run_all_benchmarks.sh

# Distribute benchmarks via pdsh
bash ~/Development/ClusterSetupAndConfigs/scripts/benchmarks/run_benchmarks_pdsh.sh

# Quick MPI launcher
bash ~/Development/ClusterSetupAndConfigs/scripts/benchmarks/mpirun_cluster.sh 4 ./bin/mpi_latency
```

### 4. Configuration Management

```bash
# Show cluster summary
uv run python cluster_modules/config_template_manager.py summary

# Generate configurations
uv run python cluster_modules/config_template_manager.py generate mpi-mca
uv run python cluster_modules/config_template_manager.py generate mpi-hostfile
uv run python cluster_modules/config_template_manager.py generate ssh
uv run python cluster_modules/config_template_manager.py generate slurm

# Deploy configurations
uv run python cluster_modules/config_template_manager.py deploy mpi-mca
uv run python cluster_modules/config_template_manager.py deploy ssh
```

### 5. Firewall Management

```bash
# Verify firewall status
uv run python cluster_modules/config_template_manager.py firewall verify

# Configure firewalls (all nodes)
uv run python cluster_modules/config_template_manager.py firewall configure

# Configure specific nodes
uv run python cluster_modules/config_template_manager.py firewall configure --nodes 192.168.1.136 192.168.1.139

# Custom port range
uv run python cluster_modules/config_template_manager.py firewall configure --ports 50000-51000 --protocol tcp
```

## Quick Commands

### Daily Operations

```bash
# Check cluster status
uv run python cluster_modules/config_template_manager.py summary

# Sync and run benchmarks
uv run python cluster_modules/benchmark_runner.py sync
uv run python cluster_modules/benchmark_runner.py run all --np 4

# Clean up after issues
uv run python cluster_modules/benchmark_runner.py cleanup
pdsh -w all_nodes "pkill -9 -f 'mpi_|prte|orted'"

# Check MPI connectivity
cd ~/cluster_build_sources/benchmarks
mpirun -np 4 --hostfile hostfile --map-by ppr:1:node hostname
```

### Debugging

```bash
# Check MPI configuration on all nodes
pdsh -w 192.168.1.136,192.168.1.139,192.168.1.96,192.168.1.147 \
  "cat ~/.openmpi/mca-params.conf | grep btl_tcp_if_include"

# Check network interfaces
pdsh -w all_nodes "hostname && ip addr show | grep 'inet 192.168.1'"

# Check firewall status
uv run python cluster_modules/config_template_manager.py firewall verify

# Test MPI with verbose output
mpirun -np 2 --hostfile hostfile --map-by ppr:1:node \
  --mca btl_base_verbose 30 hostname
```

### Results Management

```bash
# Benchmark results are saved to:
ls -lht ~/cluster_benchmark_results/

# View latest results
cat ~/cluster_benchmark_results/benchmark_results_*.json | jq .
```

## Tool Comparison

### config_template_manager.py
**Purpose:** Cluster configuration and firewall management  
**Use for:** Deploying configs, managing firewalls, generating templates  
**Scope:** Infrastructure setup

### benchmark_runner.py (NEW)
**Purpose:** Modular benchmark execution with pdsh  
**Use for:** Running benchmarks, syncing binaries, collecting results  
**Scope:** Benchmark orchestration  
**Features:**
- pdsh integration for parallel execution
- Automatic sync to all nodes
- JSON result export
- Process cleanup

### benchmark_manager.py
**Purpose:** Template-based PGAS benchmark generation  
**Use for:** Creating benchmark source code from templates  
**Scope:** Benchmark code generation

### Shell Scripts (scripts/benchmarks/)
**Purpose:** Legacy comprehensive benchmark runners  
**Use for:** Full benchmark suites, one-off testing  
**Scope:** End-to-end benchmark execution

## Key Features

### Modular Benchmark Runner Benefits
- ✅ Cleaner, more Pythonic interface
- ✅ Integrates with cluster configuration
- ✅ Automatic binary distribution
- ✅ Structured result collection
- ✅ Better error handling
- ✅ Process management

### Organized Structure Benefits
- ✅ Clear separation of concerns
- ✅ Easy to find and use scripts
- ✅ Modular components
- ✅ Consistent CLI interface
- ✅ Comprehensive documentation

## Next Steps

1. **Configure passwordless sudo** on Ubuntu nodes for firewall automation
2. **Test benchmark runner** with all benchmark types
3. **Document benchmark results** format and analysis tools
4. **Add more benchmark configurations** to runner
5. **Create result visualization** tools

## Documentation References

- **Template System:** `docs/configuration/TEMPLATE_SYSTEM.md`
- **Firewall Setup:** `docs/configuration/FIREWALL_SETUP.md`
- **MPI Debugging:** `docs/troubleshooting/MPI_BENCHMARK_DEBUGGING.md`
- **Multi-Homed Nodes:** `docs/troubleshooting/MULTI_HOMED_NODE_FIX.md`
