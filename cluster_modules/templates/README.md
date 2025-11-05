# Benchmark Templates

## Purpose
This directory contains **benchmark-related templates** used by `benchmark_manager.py` to generate HPC benchmarks. This includes source code templates, runtime configuration templates, and build system templates for multiple parallel programming frameworks.

**For cluster infrastructure configuration templates** (SSH, MPI hostfile, Slurm), see `templates/` in the project root.

## Directory Structure

```
cluster_modules/templates/
├── benchmarks/              # Benchmark source code templates
│   ├── upcxx/               # UPC++ PGAS framework
│   │   ├── upcxx_latency.cpp.j2
│   │   └── upcxx_bandwidth.cpp.j2
│   ├── mpi/                 # Message Passing Interface
│   │   └── mpi_latency.cpp.j2
│   ├── openshmem/           # OpenSHMEM PGAS framework
│   │   └── openshmem_latency.cpp.j2
│   ├── berkeley_upc/        # Berkeley UPC framework
│   │   └── berkeley_upc_latency.c.j2
│   ├── openmp/              # OpenMP shared memory
│   │   └── openmp_parallel.cpp.j2
│   └── hybrid/              # Hybrid MPI+OpenMP
│       └── hybrid_mpi_openmp.cpp.j2
├── configs/                 # Runtime configuration templates
│   └── benchmarks/          # Benchmark runtime environment configs
│       ├── mpi/
│       │   └── benchmark_config.j2
│       ├── openmp/
│       │   └── benchmark_config.j2
│       ├── openshmem/
│       │   └── benchmark_config.j2
│       ├── upcxx/
│       │   └── benchmark_config.j2
│       └── hybrid/
│           └── benchmark_config.j2
├── build/                   # Build system templates
│   ├── Makefile.j2          # Makefile for compiling benchmarks
│   └── run_benchmarks.sh.j2 # Script for running all benchmarks
└── README.md                # This file
```

## Framework Categories

### UPC++ (`benchmarks/upcxx/`)
**Framework:** UPC++ (Unified Parallel C++)  
**Language:** C++  
**Paradigm:** PGAS (Partitioned Global Address Space)

**Benchmarks:**
- `upcxx_latency.cpp.j2` - Point-to-point latency measurement
- `upcxx_bandwidth.cpp.j2` - Bandwidth measurement with various message sizes

**Compiler:** `upcxx` (UPC++ compiler wrapper)

### MPI (`benchmarks/mpi/`)
**Framework:** MPI (Message Passing Interface)  
**Language:** C++  
**Paradigm:** Distributed memory message passing

**Benchmarks:**
- `mpi_latency.cpp.j2` - Point-to-point latency using MPI_Send/MPI_Recv

**Compiler:** `mpicxx` (MPI C++ compiler wrapper)

### OpenSHMEM (`benchmarks/openshmem/`)
**Framework:** OpenSHMEM  
**Language:** C++  
**Paradigm:** PGAS with one-sided communication

**Benchmarks:**
- `openshmem_latency.cpp.j2` - PUT/GET latency measurement

**Compiler:** `oshc++` (OpenSHMEM C++ compiler wrapper)

### Berkeley UPC (`benchmarks/berkeley_upc/`)
**Framework:** Berkeley UPC (Unified Parallel C)  
**Language:** C (with UPC extensions)  
**Paradigm:** PGAS with shared pointer extensions

**Benchmarks:**
- `berkeley_upc_latency.c.j2` - Shared memory access latency

**Compiler:** `upcc` (Berkeley UPC compiler)  
**Launcher:** `upcc-run`

### OpenMP (`benchmarks/openmp/`)
**Framework:** OpenMP  
**Language:** C++  
**Paradigm:** Shared memory threading

**Benchmarks:**
- `openmp_parallel.cpp.j2` - Parallel region timing and thread scaling

**Compiler:** `g++` with `-fopenmp`

### Hybrid (`benchmarks/hybrid/`)
**Framework:** MPI + OpenMP  
**Language:** C++  
**Paradigm:** Multi-level parallelism (distributed + shared memory)

**Benchmarks:**
- `hybrid_mpi_openmp.cpp.j2` - Combined MPI and OpenMP parallelism

**Compiler:** `mpicxx` with `-fopenmp`

## Runtime Configuration Templates (`configs/benchmarks/`)

### Purpose
Runtime environment configuration templates for benchmark execution. These generate scripts that set environment variables, configure threading, and tune framework-specific parameters before running benchmarks.

### MPI (`configs/benchmarks/mpi/benchmark_config.j2`)
**Variables Set:**
- `OMPI_MCA_*` - OpenMPI MCA parameters
- `MPICH_*` - MPICH-specific settings
- Network interface binding
- Process affinity
- Communication protocol selection

**Template Variables:**
- `num_procs` - Number of MPI processes
- `ppn` - Processes per node
- `network_interface` - Network device for MPI communication

### OpenMP (`configs/benchmarks/openmp/benchmark_config.j2`)
**Variables Set:**
- `OMP_NUM_THREADS` - Number of OpenMP threads
- `OMP_PROC_BIND` - Thread affinity policy
- `OMP_PLACES` - Thread placement
- `OMP_SCHEDULE` - Loop scheduling policy

**Template Variables:**
- `num_threads` - Number of threads
- `thread_affinity` - Binding policy (close, spread, master)

### OpenSHMEM (`configs/benchmarks/openshmem/benchmark_config.j2`)
**Variables Set:**
- `SHMEM_SYMMETRIC_SIZE` - Symmetric heap size
- `SMA_SYMMETRIC_SIZE` - Alternative heap size variable
- `SHMEM_DEBUG` - Debug level
- Process placement

**Template Variables:**
- `num_pes` - Number of processing elements
- `heap_size` - Symmetric heap size (e.g., "512M")

### UPC++ (`configs/benchmarks/upcxx/benchmark_config.j2`)
**Variables Set:**
- `GASNET_*` - GASNet communication layer settings
- `UPCXX_SEGMENT_MB` - Shared segment size
- Network conduit configuration
- Communication buffer sizes

**Template Variables:**
- `num_ranks` - Number of UPC++ ranks
- `segment_size` - Shared memory segment size
- `conduit` - GASNet conduit (udp, ibv, mpi, etc.)

### Hybrid (`configs/benchmarks/hybrid/benchmark_config.j2`)
**Variables Set:**
- Combined MPI and OpenMP settings
- Process-thread affinity coordination
- Resource allocation per MPI rank

**Template Variables:**
- `num_procs` - Number of MPI processes
- `threads_per_proc` - OpenMP threads per MPI process
- `total_threads` - Total parallelism (procs × threads)

## Build System Templates (`build/`)

### Makefile.j2
**Purpose:** Generate Makefile for compiling all benchmarks  
**Features:**
- Automatic compiler detection
- Framework-specific compilation flags
- Parallel build support (`make -j`)
- Clean targets

**Template Variables:**
- `upcxx_compiler` - UPC++ compiler path (default: upcxx)
- `mpi_compiler` - MPI C++ compiler (default: mpicxx)
- `openshmem_compiler` - OpenSHMEM compiler (default: oshc++)
- `berkeley_upc_compiler` - Berkeley UPC compiler (default: upcc)
- `cxx_compiler` - C++ compiler (default: g++)
- `optimization_flags` - Compiler optimization (default: -O3)

### run_benchmarks.sh.j2
**Purpose:** Generate shell script to execute all benchmarks  
**Features:**
- Sequential benchmark execution
- Automatic launcher selection per framework
- Result collection
- Error handling

**Template Variables:**
- `num_procs` - Number of MPI processes
- `benchmark_dir` - Directory containing binaries
- `benchmarks` - List of benchmark configurations

## Usage

### From Python (benchmark_manager.py)

```python
from cluster_modules.benchmark_manager import BenchmarkManager

# Initialize manager
mgr = BenchmarkManager(
    username="muyiwa",
    password="",
    master_ip="192.168.1.136",
    worker_ips=["192.168.1.139", "192.168.1.96", "192.168.1.147"]
)

# Create directory structure
mgr.create_benchmark_directory()

# Generate benchmarks from templates
mgr.create_upcxx_latency_benchmark(iterations=1000)
mgr.create_mpi_latency_benchmark(iterations=1000)
mgr.create_openshmem_latency_benchmark(iterations=1000)
mgr.create_berkeley_upc_latency_benchmark(iterations=1000)
mgr.create_openmp_benchmark(array_size=10000000)
mgr.create_hybrid_benchmark(array_size=10000000)

# Generate build system
mgr.create_makefile()
mgr.create_run_script(num_procs=4)
```

### Building Benchmarks

```bash
cd ~/pgas_benchmarks
make -j$(nproc)  # Parallel build
```

### Running Benchmarks

```bash
cd ~/pgas_benchmarks
./run_benchmarks.sh
```

## Template Parameters

### Common Parameters (All Benchmarks)
- `iterations` (int) - Number of measurement iterations
- `warmup_iterations` (int) - Warmup iterations before measurement
- `message_size` (int) - Message/data size in bytes

### UPC++ Specific
- `message_sizes` (list) - Multiple message sizes for bandwidth tests

### OpenMP/Hybrid Specific
- `array_size` (int) - Size of arrays for computation
- `num_threads` (int) - Number of OpenMP threads (optional, defaults to OMP_NUM_THREADS)

## Adding New Benchmark Templates

### 1. Create Template File
```bash
# Example: Adding a new MPI broadcast benchmark
touch cluster_modules/templates/benchmarks/mpi/mpi_broadcast.cpp.j2
```

### 2. Template Content Structure
```cpp
// mpi_broadcast.cpp.j2
#include <mpi.h>
#include <iostream>
#include <chrono>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    
    const int iterations = {{ iterations }};
    const int data_size = {{ data_size }};
    
    // Benchmark code here
    
    MPI_Finalize();
    return 0;
}
```

### 3. Add Method to benchmark_manager.py
```python
def create_mpi_broadcast_benchmark(self, iterations: int = 1000, 
                                   data_size: int = 1024) -> bool:
    """Create MPI broadcast benchmark from template."""
    try:
        template = self.jinja_env.get_template("benchmarks/mpi/mpi_broadcast.cpp.j2")
        code = template.render(
            iterations=iterations,
            data_size=data_size
        )
        
        benchmark_file = self.benchmark_dir / "src" / "mpi_broadcast.cpp"
        benchmark_file.write_text(code)
        print(f"✓ Created MPI broadcast benchmark: {benchmark_file}")
        return True
    except Exception as e:
        print(f"✗ Error creating MPI broadcast benchmark: {e}")
        return False
```

### 4. Update Makefile Template
Add build rule in `build/Makefile.j2`:
```makefile
$(BIN_DIR)/mpi_broadcast: $(SRC_DIR)/mpi_broadcast.cpp
	$(MPI_COMPILER) $(CXXFLAGS) $< -o $@
```

### 5. Update Run Script Template
Add to benchmark list in `build/run_benchmarks.sh.j2`:
```bash
run_benchmark "MPI Broadcast" "mpirun -np {{ num_procs }} ./bin/mpi_broadcast"
```

## Template Best Practices

### 1. Use Descriptive Variable Names
```jinja
{# Good #}
{% set num_iterations = iterations | default(1000) %}
{% set warmup_count = warmup_iterations | default(100) %}

{# Avoid #}
{% set n = iterations | default(1000) %}
{% set w = warmup | default(100) %}
```

### 2. Provide Sensible Defaults
```jinja
{% set iterations = iterations | default(1000) %}
{% set warmup_iterations = warmup_iterations | default(100) %}
{% set message_size = message_size | default(8) %}
```

### 3. Add Comments
```cpp
// {{ iterations }} measurement iterations
// {{ warmup_iterations }} warmup iterations
for (int i = 0; i < {{ iterations }}; i++) {
    // Measurement code
}
```

### 4. Include Error Handling
```cpp
if (rank < 0 || rank >= size) {
    std::cerr << "Error: Invalid rank " << rank << std::endl;
    MPI_Abort(MPI_COMM_WORLD, 1);
}
```

### 5. Output Consistent Results
```cpp
if (rank == 0) {
    std::cout << "Benchmark: {{ benchmark_name }}" << std::endl;
    std::cout << "Message Size: {{ message_size }} bytes" << std::endl;
    std::cout << "Latency: " << latency_us << " microseconds" << std::endl;
}
```

## Testing Templates

### 1. Generate Benchmark
```python
mgr.create_mpi_latency_benchmark(iterations=100)
```

### 2. Verify Generated Code
```bash
cat ~/pgas_benchmarks/src/mpi_latency.cpp
```

### 3. Test Compilation
```bash
cd ~/pgas_benchmarks
make mpi_latency
```

### 4. Test Execution
```bash
mpirun -np 2 ./bin/mpi_latency
```

## Related Files
- `../benchmark_manager.py` - Template manager class
- `../../templates/README.md` - Configuration templates guide
- `../../docs/configuration/PGAS_CONFIGURATION.md` - PGAS setup guide
