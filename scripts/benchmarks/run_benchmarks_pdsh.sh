#!/bin/bash
# Run benchmarks across the entire cluster using pdsh
# This distributes benchmarks to all nodes for parallel execution

set -e

HOSTFILE="$HOME/.openmpi/hostfile_optimal"
BENCHMARK_DIR="$HOME/cluster_build_sources/benchmarks"
RESULTS_DIR="$HOME/cluster_benchmark_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=================================================="
echo "Cluster-Wide Benchmark Distribution"
echo "=================================================="
echo -e "${NC}"

# Get list of nodes from hostfile
if [ ! -f "$HOSTFILE" ]; then
    echo "Error: Hostfile not found: $HOSTFILE"
    exit 1
fi

# Extract IP addresses from hostfile
NODES=$(awk '{print $1}' "$HOSTFILE" | tr '\n' ',' | sed 's/,$//')
echo "Target nodes: $NODES"
echo ""

# Check if benchmarks exist
if [ ! -d "$BENCHMARK_DIR/bin" ]; then
    echo "Error: Benchmark binaries not found in $BENCHMARK_DIR/bin"
    echo "Please run: cd $BENCHMARK_DIR && make all"
    exit 1
fi

echo -e "${YELLOW}Syncing benchmarks to all cluster nodes...${NC}"

# Sync benchmarks to all nodes using pdsh
pdsh -w "$NODES" "mkdir -p $BENCHMARK_DIR/bin" 2>/dev/null || true

# Use rsync to distribute binaries to all nodes
for node in $(echo $NODES | tr ',' ' '); do
    echo "Syncing to $node..."
    rsync -avz --progress "$BENCHMARK_DIR/bin/" "$node:$BENCHMARK_DIR/bin/" 2>/dev/null || \
        echo "Warning: Could not sync to $node"
done

echo ""
echo -e "${GREEN}✓ Benchmarks synced to all nodes${NC}"
echo ""

# Run local benchmarks on each node using pdsh
echo -e "${BLUE}Running OpenMP benchmark on all nodes in parallel...${NC}"
pdsh -w "$NODES" "cd $BENCHMARK_DIR && bin/openmp_parallel 2>&1" | tee "$RESULTS_DIR/openmp_all_nodes_${TIMESTAMP}.txt"

echo ""
echo -e "${GREEN}✓ Cluster-wide benchmark distribution complete${NC}"
echo ""
echo "Results saved to: $RESULTS_DIR/openmp_all_nodes_${TIMESTAMP}.txt"
echo ""
echo "To run MPI benchmarks across cluster, use: ./run_all_benchmarks.sh"
