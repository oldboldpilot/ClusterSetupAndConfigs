#!/bin/bash
# Quick MPI launcher script with optimal flags
# Usage: ./mpirun_cluster.sh <num_processes> <program> [args...]

set -e

# Configuration
OMPI_PREFIX="/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8"
HOSTFILE="$HOME/.openmpi/hostfile_optimal"
NETWORK_INTERFACE="eth0"

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <num_processes> <program> [program_args...]"
    echo ""
    echo "Examples:"
    echo "  $0 4 ./my_program"
    echo "  $0 4 ./hybrid_mpi_openmp"
    echo "  $0 8 ./mpi_latency 1000"
    echo ""
    echo "Configuration:"
    echo "  Open MPI prefix: $OMPI_PREFIX"
    echo "  Hostfile: $HOSTFILE"
    echo "  Network interface: $NETWORK_INTERFACE"
    exit 1
fi

NP=$1
PROGRAM=$2
shift 2
PROGRAM_ARGS="$@"

# Verify Open MPI installation
if [ ! -d "$OMPI_PREFIX" ]; then
    echo "Error: Open MPI not found at $OMPI_PREFIX"
    echo "Please update OMPI_PREFIX in this script"
    exit 1
fi

# Verify hostfile exists
if [ ! -f "$HOSTFILE" ]; then
    echo "Error: Hostfile not found at $HOSTFILE"
    echo "Please run cluster setup to generate hostfiles"
    exit 1
fi

# Verify program exists
if [ ! -f "$PROGRAM" ] && [ ! -x "$(command -v $PROGRAM)" ]; then
    echo "Error: Program not found: $PROGRAM"
    exit 1
fi

echo "=================================================="
echo "MPI Cluster Launcher"
echo "=================================================="
echo "Processes:        $NP"
echo "Program:          $PROGRAM"
echo "Arguments:        $PROGRAM_ARGS"
echo "Hostfile:         $HOSTFILE"
echo "Network:          $NETWORK_INTERFACE"
echo "=================================================="
echo ""

# Launch with optimal flags
exec mpirun \
    --prefix "$OMPI_PREFIX" \
    --map-by node \
    -np "$NP" \
    --hostfile "$HOSTFILE" \
    --mca btl_tcp_if_include "$NETWORK_INTERFACE" \
    --mca oob_tcp_if_include "$NETWORK_INTERFACE" \
    "$PROGRAM" $PROGRAM_ARGS
