# PGAS Benchmarks Module

This module provides standalone benchmark suite creation and execution for PGAS libraries.

## Features

- **Benchmark Creation**: Automatically generates benchmark source files for:
  - UPC++ point-to-point latency
  - MPI point-to-point latency
  - UPC++ bandwidth
  - OpenSHMEM operations (coming soon)

- **Compilation**: Automated compilation using Makefile generation

- **Execution**: Run benchmarks individually or as a suite

- **Results Collection**: Automatic result saving and reporting

## Usage

### Quick Start

```bash
# Create benchmark suite
python -m cluster_tools.benchmarks.run_benchmarks --create

# Compile all benchmarks
python -m cluster_tools.benchmarks.run_benchmarks --compile

# Run all benchmarks with 4 processes
python -m cluster_tools.benchmarks.run_benchmarks --run-all -n 4

# Full workflow
python -m cluster_tools.benchmarks.run_benchmarks --create --compile --run-all
```

### Individual Benchmarks

```bash
# Run specific benchmark
python -m cluster_tools.benchmarks.run_benchmarks --run upcxx_latency -n 2
python -m cluster_tools.benchmarks.run_benchmarks --run mpi_latency -n 2
python -m cluster_tools.benchmarks.run_benchmarks --run upcxx_bandwidth -n 2
```

### Multi-Node Execution

```bash
# Specify cluster IPs for multi-node execution
python -m cluster_tools.benchmarks.run_benchmarks \
    --run-all \
    --cluster-ips 192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136 \
    -n 4
```

### Custom Benchmark Directory

```bash
# Use custom directory
python -m cluster_tools.benchmarks.run_benchmarks \
    --benchmark-dir /custom/path/benchmarks \
    --create --compile --run-all
```

### Cleaning

```bash
# Clean compiled binaries
python -m cluster_tools.benchmarks.run_benchmarks --clean
```

## Benchmark Suite Structure

```
~/pgas_benchmarks/
├── src/                    # Source files
│   ├── upcxx_latency.cpp
│   ├── mpi_latency.c
│   └── upcxx_bandwidth.cpp
├── bin/                    # Compiled binaries
│   ├── upcxx_latency
│   ├── mpi_latency
│   └── upcxx_bandwidth
├── results/                # Benchmark results
│   ├── upcxx_latency_n2.txt
│   ├── mpi_latency_n2.txt
│   └── upcxx_bandwidth_n2.txt
├── Makefile               # Build configuration
└── run_benchmarks.sh      # Shell script runner
```

## Available Benchmarks

### UPC++ Latency
Measures point-to-point RPC latency between two processes.

### MPI Latency
Measures point-to-point send/recv latency between two processes.

### UPC++ Bandwidth
Measures data transfer bandwidth for various message sizes.

## Requirements

- **UPC++**: Installed and available in PATH
- **MPI**: OpenMPI or other MPI implementation
- **OpenSHMEM**: (Optional) For OpenSHMEM benchmarks
- **GCC**: For compilation
- **Python 3.7+**: For benchmark runner

## Programmatic Usage

```python
from cluster_tools.benchmarks import BenchmarkRunner

# Create runner
runner = BenchmarkRunner(
    benchmark_dir=Path("~/my_benchmarks"),
    cluster_ips=["192.168.1.147", "192.168.1.139"]
)

# Create suite
runner.create_suite()

# Compile
runner.compile_all()

# Run specific benchmark
result = runner.run_benchmark("upcxx_latency", num_procs=4)

# Run all benchmarks
results = runner.run_all(num_procs=4)
```

## Integration with Cluster Setup

This module is designed to work standalone but integrates seamlessly with the cluster setup system:

```python
from cluster_setup import ClusterSetup
from cluster_tools.benchmarks import BenchmarkRunner

# Use cluster configuration
cluster = ClusterSetup(master_ip, worker_ips, username, password)
runner = BenchmarkRunner(cluster_ips=cluster.all_ips)

runner.create_suite()
runner.compile_all()
runner.run_all()
```

## Notes

- Benchmarks are automatically saved to `results/` directory
- Multi-node execution requires properly configured passwordless SSH
- GASNET_SSH_SERVERS is automatically configured for UPC++ benchmarks
- MPI benchmarks use hostfile if available at `~/hostfile`
