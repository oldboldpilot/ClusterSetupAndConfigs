#!/bin/bash
# Comprehensive cluster benchmark suite runner
# Runs all benchmarks across the entire cluster with optimal MPI settings

set -e

# Configuration
OMPI_PREFIX="/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8"
HOSTFILE="$HOME/.openmpi/hostfile_optimal"
NETWORK_INTERFACE="eth0"
BENCHMARK_DIR="$HOME/cluster_build_sources/benchmarks"
RESULTS_DIR="$HOME/cluster_benchmark_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create results directory
mkdir -p "$RESULTS_DIR"
RESULTS_FILE="$RESULTS_DIR/benchmark_results_${TIMESTAMP}.txt"

echo -e "${BLUE}=================================================="
echo "Cluster Benchmark Suite"
echo "=================================================="
echo -e "${NC}"
echo "Benchmark directory: $BENCHMARK_DIR"
echo "Results file:        $RESULTS_FILE"
echo "Hostfile:            $HOSTFILE"
echo "Timestamp:           $TIMESTAMP"
echo ""

# Check if benchmark directory exists
if [ ! -d "$BENCHMARK_DIR" ]; then
    echo -e "${RED}Error: Benchmark directory not found: $BENCHMARK_DIR${NC}"
    exit 1
fi

cd "$BENCHMARK_DIR"

# Check if binaries exist
if [ ! -d "bin" ] || [ -z "$(ls -A bin 2>/dev/null)" ]; then
    echo -e "${YELLOW}Warning: No compiled benchmarks found. Compiling...${NC}"
    make all
fi

# Function to run a benchmark
run_benchmark() {
    local name=$1
    local binary=$2
    local np=$3
    local description=$4
    
    echo -e "${BLUE}=================================================="
    echo "Running: $name"
    echo "Description: $description"
    echo "Processes: $np"
    echo -e "==================================================${NC}"
    echo ""
    
    {
        echo "========================================"
        echo "Benchmark: $name"
        echo "Description: $description"
        echo "Timestamp: $(date)"
        echo "Processes: $np"
        echo "========================================"
        echo ""
    } >> "$RESULTS_FILE"
    
    if [ -f "$binary" ]; then
        if mpirun \
            --prefix "$OMPI_PREFIX" \
            --map-by node \
            -np "$np" \
            --hostfile "$HOSTFILE" \
            --mca btl_tcp_if_include "$NETWORK_INTERFACE" \
            --mca oob_tcp_if_include "$NETWORK_INTERFACE" \
            "$binary" 2>&1 | tee -a "$RESULTS_FILE"; then
            echo -e "${GREEN}✓ $name completed successfully${NC}"
        else
            echo -e "${RED}✗ $name failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Skipping $name - binary not found: $binary${NC}"
        echo "SKIPPED - binary not found: $binary" >> "$RESULTS_FILE"
    fi
    
    echo "" >> "$RESULTS_FILE"
    echo ""
}

# Function to run OpenMP benchmark (no MPI)
run_openmp_benchmark() {
    local name=$1
    local binary=$2
    local description=$3
    
    echo -e "${BLUE}=================================================="
    echo "Running: $name (Local OpenMP)"
    echo "Description: $description"
    echo -e "==================================================${NC}"
    echo ""
    
    {
        echo "========================================"
        echo "Benchmark: $name (OpenMP - Local)"
        echo "Description: $description"
        echo "Timestamp: $(date)"
        echo "========================================"
        echo ""
    } >> "$RESULTS_FILE"
    
    if [ -f "$binary" ]; then
        if "$binary" 2>&1 | tee -a "$RESULTS_FILE"; then
            echo -e "${GREEN}✓ $name completed successfully${NC}"
        else
            echo -e "${RED}✗ $name failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Skipping $name - binary not found: $binary${NC}"
        echo "SKIPPED - binary not found: $binary" >> "$RESULTS_FILE"
    fi
    
    echo "" >> "$RESULTS_FILE"
    echo ""
}

# Function to run UPC++ benchmark
run_upcxx_benchmark() {
    local name=$1
    local binary=$2
    local np=$3
    local description=$4
    
    echo -e "${BLUE}=================================================="
    echo "Running: $name (UPC++)"
    echo "Description: $description"
    echo "Processes: $np"
    echo -e "==================================================${NC}"
    echo ""
    
    {
        echo "========================================"
        echo "Benchmark: $name (UPC++)"
        echo "Description: $description"
        echo "Timestamp: $(date)"
        echo "Processes: $np"
        echo "========================================"
        echo ""
    } >> "$RESULTS_FILE"
    
    if [ -f "$binary" ]; then
        # UPC++ needs proper network configuration and may need --prefix
        if GASNET_SPAWNFN=L \
           UPCXX_NETWORK=smp \
           upcxx-run -n "$np" "$binary" 2>&1 | tee -a "$RESULTS_FILE"; then
            echo -e "${GREEN}✓ $name completed successfully${NC}"
        else
            echo -e "${RED}✗ $name failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ Skipping $name - binary not found: $binary${NC}"
        echo "SKIPPED - binary not found: $binary" >> "$RESULTS_FILE"
    fi
    
    echo "" >> "$RESULTS_FILE"
    echo ""
}

# Get number of nodes from hostfile
NUM_NODES=$(wc -l < "$HOSTFILE" 2>/dev/null || echo "4")

echo -e "${GREEN}Starting cluster benchmark suite...${NC}"
echo "Number of cluster nodes: $NUM_NODES"
echo ""
sleep 2

# 1. OpenMP Benchmark (local only)
run_openmp_benchmark \
    "OpenMP Parallel" \
    "bin/openmp_parallel" \
    "Thread-level parallelism and scaling test"

# 2. MPI Latency Benchmark
run_benchmark \
    "MPI Latency" \
    "bin/mpi_latency" \
    "$NUM_NODES" \
    "Point-to-point MPI communication latency"

# 3. Hybrid MPI+OpenMP Benchmark
run_benchmark \
    "Hybrid MPI+OpenMP" \
    "bin/hybrid_mpi_openmp" \
    "$NUM_NODES" \
    "Combined MPI and OpenMP parallelism test"

# 4. UPC++ Latency Benchmark
run_upcxx_benchmark \
    "UPC++ Latency" \
    "bin/upcxx_latency" \
    "$NUM_NODES" \
    "UPC++ RPC latency test"

# 5. UPC++ Bandwidth Benchmark
run_upcxx_benchmark \
    "UPC++ Bandwidth" \
    "bin/upcxx_bandwidth" \
    "$NUM_NODES" \
    "UPC++ large transfer bandwidth test"

# 6. OpenSHMEM Latency Benchmark
run_benchmark \
    "OpenSHMEM Latency" \
    "bin/openshmem_latency" \
    "$NUM_NODES" \
    "OpenSHMEM put/get latency test"

# 7. Berkeley UPC Latency Benchmark
run_benchmark \
    "Berkeley UPC Latency" \
    "bin/berkeley_upc_latency" \
    "$NUM_NODES" \
    "Berkeley UPC shared memory access latency"

echo -e "${BLUE}=================================================="
echo "Benchmark Suite Complete!"
echo "=================================================="
echo -e "${NC}"
echo "Results saved to: $RESULTS_FILE"
echo ""
echo "Summary:"
echo "  OpenMP:           1 benchmark (local)"
echo "  MPI:              2 benchmarks (latency, hybrid)"
echo "  UPC++:            2 benchmarks (latency, bandwidth)"
echo "  OpenSHMEM:        1 benchmark (latency)"
echo "  Berkeley UPC:     1 benchmark (latency)"
echo "  Total:            7 benchmarks"
echo ""
echo -e "${GREEN}View results: cat $RESULTS_FILE${NC}"
