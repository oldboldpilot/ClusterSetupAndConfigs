#!/usr/bin/env bash
#
# Comprehensive Cluster Network Setup Script
# 
# This script performs complete cluster network configuration:
# 1. Deploys MPI MCA configuration to all nodes
# 2. Generates and deploys hostfile
# 3. Configures firewalls on all nodes
# 4. Verifies configuration
# 5. Runs basic MPI connectivity tests
#
# Usage: ./scripts/setup_cluster_network.sh [--skip-firewall] [--skip-test]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_MANAGER="$PROJECT_DIR/cluster_modules/config_template_manager.py"
BENCHMARK_DIR="$HOME/cluster_build_sources/benchmarks"
HOSTFILE="$BENCHMARK_DIR/hostfile"

# Flags
SKIP_FIREWALL=false
SKIP_TEST=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-firewall)
            SKIP_FIREWALL=true
            shift
            ;;
        --skip-test)
            SKIP_TEST=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-firewall   Skip firewall configuration"
            echo "  --skip-test       Skip MPI connectivity tests"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

section_header() {
    echo ""
    echo "=============================================================================="
    echo -e "${BLUE}$1${NC}"
    echo "=============================================================================="
    echo ""
}

# Check prerequisites
check_prerequisites() {
    section_header "Checking Prerequisites"
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed. Please install it first."
        exit 1
    fi
    log_success "uv is installed"
    
    # Check if config manager exists
    if [ ! -f "$CONFIG_MANAGER" ]; then
        log_error "Config manager not found: $CONFIG_MANAGER"
        exit 1
    fi
    log_success "Config manager found"
    
    # Check if cluster_config_actual.yaml exists
    if [ ! -f "$PROJECT_DIR/cluster_config_actual.yaml" ]; then
        log_error "Cluster configuration not found: cluster_config_actual.yaml"
        exit 1
    fi
    log_success "Cluster configuration found"
    
    # Check if benchmark directory exists
    if [ ! -d "$BENCHMARK_DIR" ]; then
        log_warning "Benchmark directory not found: $BENCHMARK_DIR"
        log_info "Creating benchmark directory..."
        mkdir -p "$BENCHMARK_DIR"
    fi
    log_success "Benchmark directory ready"
}

# Display cluster summary
show_cluster_summary() {
    section_header "Cluster Configuration Summary"
    cd "$PROJECT_DIR"
    uv run python "$CONFIG_MANAGER" summary
}

# Deploy MPI MCA configuration
deploy_mpi_config() {
    section_header "Deploying MPI MCA Configuration"
    log_info "Deploying OpenMPI configuration to all nodes..."
    
    cd "$PROJECT_DIR"
    if uv run python "$CONFIG_MANAGER" deploy mpi-mca; then
        log_success "MPI MCA configuration deployed successfully"
    else
        log_error "Failed to deploy MPI MCA configuration"
        return 1
    fi
}

# Generate hostfile
generate_hostfile() {
    section_header "Generating MPI Hostfile"
    log_info "Generating hostfile with optimal slot allocation..."
    
    cd "$PROJECT_DIR"
    if uv run python "$CONFIG_MANAGER" generate mpi-hostfile --output "$HOSTFILE"; then
        log_success "Hostfile generated: $HOSTFILE"
        log_info "Hostfile contents:"
        cat "$HOSTFILE"
    else
        log_error "Failed to generate hostfile"
        return 1
    fi
}

# Configure firewalls
configure_firewalls() {
    if [ "$SKIP_FIREWALL" = true ]; then
        log_warning "Skipping firewall configuration (--skip-firewall)"
        return 0
    fi
    
    section_header "Configuring Firewalls"
    log_info "Opening MPI ports (50000-50200) on all nodes..."
    
    cd "$PROJECT_DIR"
    if uv run python "$CONFIG_MANAGER" firewall configure; then
        log_success "Firewall configuration completed"
    else
        log_warning "Firewall configuration had some errors (may require manual setup)"
    fi
    
    # Verify firewall configuration
    log_info "Verifying firewall configuration..."
    uv run python "$CONFIG_MANAGER" firewall verify
}

# Verify MPI configuration
verify_mpi_config() {
    section_header "Verifying MPI Configuration"
    
    # Check MCA config on all nodes
    log_info "Checking MCA configuration on all nodes..."
    if pdsh -w 192.168.1.136,192.168.1.139,192.168.1.96,192.168.1.147 \
        "test -f ~/.openmpi/mca-params.conf && echo 'OK' || echo 'MISSING'"; then
        log_success "MCA configuration files present on all nodes"
    else
        log_warning "Some nodes may be missing MCA configuration"
    fi
    
    # Check network interfaces
    log_info "Checking network interfaces on all nodes..."
    pdsh -w 192.168.1.136,192.168.1.139,192.168.1.96,192.168.1.147 \
        "hostname && ip addr show | grep 'inet 192.168.1' | head -1"
}

# Test MPI connectivity
test_mpi_connectivity() {
    if [ "$SKIP_TEST" = true ]; then
        log_warning "Skipping MPI connectivity tests (--skip-test)"
        return 0
    fi
    
    section_header "Testing MPI Connectivity"
    
    # Clean up any stuck processes first
    log_info "Cleaning up any stuck MPI processes..."
    pdsh -w 192.168.1.136,192.168.1.139,192.168.1.96,192.168.1.147 \
        "pkill -9 -f 'mpi_|prte|orted' 2>/dev/null || true" &>/dev/null
    sleep 2
    
    # Test 1: MPI hostname test (4 processes, 1 per node)
    log_info "Test 1: MPI hostname across all nodes (4 processes)..."
    cd "$BENCHMARK_DIR"
    if timeout 15 mpirun -np 4 --hostfile "$HOSTFILE" --map-by ppr:1:node hostname; then
        log_success "✓ MPI hostname test PASSED"
    else
        log_error "✗ MPI hostname test FAILED"
        return 1
    fi
    
    # Test 2: MPI with 2 nodes
    log_info "Test 2: MPI between master and first worker (2 processes)..."
    if timeout 15 mpirun -np 2 --host 192.168.1.136:1,192.168.1.139:1 hostname; then
        log_success "✓ 2-node MPI test PASSED"
    else
        log_warning "✗ 2-node MPI test FAILED (may be normal if slots not configured)"
    fi
    
    # Test 3: MPI hello world (if binary exists)
    if [ -f "$BENCHMARK_DIR/bin/mpi_hello" ]; then
        log_info "Test 3: MPI hello world test..."
        if timeout 15 mpirun -np 4 --hostfile "$HOSTFILE" --map-by ppr:1:node \
            "$BENCHMARK_DIR/bin/mpi_hello"; then
            log_success "✓ MPI hello world PASSED"
        else
            log_warning "✗ MPI hello world FAILED"
        fi
    else
        log_info "Test 3: Skipped (mpi_hello binary not found)"
    fi
}

# Test MPI latency benchmark
test_mpi_latency() {
    if [ "$SKIP_TEST" = true ]; then
        return 0
    fi
    
    section_header "Testing MPI Latency Benchmark"
    
    if [ ! -f "$BENCHMARK_DIR/bin/mpi_latency" ]; then
        log_warning "MPI latency benchmark not found, skipping"
        return 0
    fi
    
    log_info "Running MPI latency benchmark (2 processes, timeout 30s)..."
    cd "$BENCHMARK_DIR"
    
    if timeout 30 mpirun -np 2 --hostfile "$HOSTFILE" --map-by ppr:1:node \
        bin/mpi_latency; then
        log_success "✓ MPI latency benchmark COMPLETED"
    else
        log_warning "✗ MPI latency benchmark FAILED or TIMEOUT"
        log_info "This may indicate firewall issues or MPI configuration problems"
        log_info "Check docs/troubleshooting/MPI_BENCHMARK_DEBUGGING.md for help"
    fi
}

# Print summary and next steps
print_summary() {
    section_header "Setup Complete - Summary"
    
    echo "Configuration Status:"
    echo "  ✓ MPI MCA configuration deployed"
    echo "  ✓ Hostfile generated: $HOSTFILE"
    
    if [ "$SKIP_FIREWALL" = false ]; then
        echo "  • Firewall configuration attempted (check output above)"
    else
        echo "  - Firewall configuration skipped"
    fi
    
    if [ "$SKIP_TEST" = false ]; then
        echo "  • MPI connectivity tests completed (check results above)"
    else
        echo "  - MPI tests skipped"
    fi
    
    echo ""
    echo "Next Steps:"
    echo "  1. If firewall configuration failed on some nodes:"
    echo "     - Configure passwordless sudo on Ubuntu nodes"
    echo "     - Or manually run: sudo ufw allow 50000-50200/tcp"
    echo ""
    echo "  2. For WSL nodes, configure Windows Firewall:"
    echo "     - See: docs/troubleshooting/WSL_FIREWALL_SETUP.md"
    echo ""
    echo "  3. Test MPI benchmarks:"
    echo "     cd $BENCHMARK_DIR"
    echo "     mpirun -np 4 --hostfile hostfile --map-by ppr:1:node bin/mpi_latency"
    echo ""
    echo "  4. For troubleshooting, see:"
    echo "     - docs/troubleshooting/MPI_BENCHMARK_DEBUGGING.md"
    echo "     - docs/troubleshooting/MULTI_HOMED_NODE_FIX.md"
    echo "     - docs/configuration/FIREWALL_SETUP.md"
    echo ""
}

# Main execution
main() {
    echo "=============================================================================="
    echo "        Cluster Network Setup Script"
    echo "=============================================================================="
    
    check_prerequisites
    show_cluster_summary
    
    # Deploy configurations
    deploy_mpi_config || exit 1
    generate_hostfile || exit 1
    configure_firewalls
    
    # Verify and test
    verify_mpi_config
    test_mpi_connectivity
    test_mpi_latency
    
    print_summary
}

# Run main function
main "$@"
