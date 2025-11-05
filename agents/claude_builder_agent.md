# Claude Builder Agent - Automated HPC Cluster Build Instructions

## Purpose

This document provides **step-by-step executable instructions** for any AI agent (Claude, Copilot, or future AI) to **automatically build and configure** a complete HPC cluster from scratch. Every command is provided, every decision is explained.

**Goal:** Enable an AI agent to respond to "Build me an HPC cluster" with full autonomous execution.

---

## Prerequisites Checklist

Before starting, verify these requirements:

### Hardware/Network Requirements
- [ ] Multiple Linux nodes (minimum 2: 1 master + 1 worker)
- [ ] All nodes on same subnet (e.g., 192.168.1.x)
- [ ] Network connectivity between all nodes
- [ ] Static IP addresses assigned to all nodes

### Operating System Requirements
- [ ] Ubuntu 20.04+ OR Red Hat 8+ OR Fedora 35+ (or derivative)
- [ ] Python 3.10+ available (Python 3.14 will be installed via Homebrew)
- [ ] sudo access on all nodes
- [ ] At least 20GB free disk space per node

### User Requirements
- [ ] Same username exists on all nodes
- [ ] User has sudo privileges on all nodes
- [ ] Password available for sudo operations
- [ ] SSH access to all nodes

### Special: WSL Requirements (if master/worker is WSL)
- [ ] Windows 11 with WSL2
- [ ] Mirrored networking mode configured (see Step 0-WSL below)
- [ ] Windows Firewall configured for MPI ports

---

## Build Process Overview

The build happens in **3 phases**:

1. **Phase 0: Pre-Setup** (Node information gathering, WSL config if needed)
2. **Phase 1: Local Setup** (Install on master/current node)
3. **Phase 2: Cluster Distribution** (Distribute to all other nodes)

**Total Time:** 30-60 minutes (depending on network speed and node count)

---

## Phase 0: Pre-Setup and Configuration

### Step 0.1: Gather Cluster Information

**AI Agent Action:** Ask user for or detect:

```bash
# Information needed:
# 1. Master node IP
# 2. Worker node IPs (comma-separated)
# 3. Username (same on all nodes)
# 4. OS type per node (ubuntu/redhat) - will be auto-detected
```

**Example interaction:**
```
Agent: "I'll help you build an HPC cluster. Please provide:
        1. Master node IP address: "
User: "192.168.1.10"

Agent: "2. Worker node IP addresses (comma-separated): "
User: "192.168.1.11,192.168.1.12,192.168.1.13"

Agent: "3. Username (same on all nodes): "
User: "muyiwa"

Agent: "4. Do any nodes run on WSL (Windows Subsystem for Linux)? (yes/no): "
User: "yes, the master node"
```

### Step 0.2: Create Configuration File

**AI Agent Action:** Generate `cluster_config_actual.yaml`

```bash
# Agent executes:
cd /home/muyiwa/cluster_build_sources/config/ClusterSetupAndConfigs

# Create config file (use cat or python)
cat > cluster_config_actual.yaml << 'EOF'
master:
  ip: 192.168.1.10
  os: ubuntu wsl2
  name: master-node

workers:
  - ip: 192.168.1.11
    os: ubuntu
    name: worker1
  - ip: 192.168.1.12
    os: ubuntu
    name: worker2
  - ip: 192.168.1.13
    os: redhat
    name: worker3

username: muyiwa
EOF

# Verify config created:
cat cluster_config_actual.yaml
```

### Step 0.3: WSL Configuration (If Applicable)

**AI Agent Action:** If ANY node is WSL, execute this:

```bash
# Detect if current node is WSL:
if grep -qi microsoft /proc/version; then
  echo "WSL detected - checking networking mode..."

  # Check if mirrored mode is configured:
  if [ -f /mnt/c/Users/*/\.wslconfig ]; then
    if grep -q "networkingMode.*mirrored" /mnt/c/Users/*/.wslconfig; then
      echo "✓ Mirrored networking already configured"
    else
      echo "⚠️  Mirrored networking NOT configured"
      echo "Required action:"
      echo "1. On Windows, create C:\Users\<Username>\.wslconfig with:"
      echo "   [wsl2]"
      echo "   networkingMode = mirrored"
      echo "2. Run 'wsl --shutdown' in PowerShell"
      echo "3. Restart WSL"
      read -p "Have you completed these steps? (yes/no): " response
    fi
  fi
fi
```

**If user hasn't configured WSL networking:**

Agent should guide:
```
Agent: "WSL requires mirrored networking for MPI to work across nodes.

        Please execute these commands in Windows PowerShell (as Administrator):

        1. Create .wslconfig file:
           notepad C:\Users\<YourUsername>\.wslconfig

        2. Add these lines:
           [wsl2]
           networkingMode = mirrored

        3. Shutdown WSL:
           wsl --shutdown

        4. Restart WSL and reconnect

        Type 'done' when ready to continue: "
```

### Step 0.4: Install Prerequisites on Current Node

**AI Agent Action:** Install git, curl, wget on current node

```bash
# Detect OS type:
if [ -f /etc/redhat-release ]; then
  PKG_MGR="sudo dnf"
elif [ -f /etc/debian_version ]; then
  PKG_MGR="sudo apt-get"
else
  echo "⚠️  Unknown OS, defaulting to apt-get"
  PKG_MGR="sudo apt-get"
fi

# Install prerequisites:
echo "Installing prerequisites..."
$PKG_MGR update -y
$PKG_MGR install -y git curl wget build-essential python3 python3-pip

# Verify installations:
which git && echo "✓ git installed"
which curl && echo "✓ curl installed"
which wget && echo "✓ wget installed"
```

### Step 0.5: Clone Repository

**AI Agent Action:** Clone or navigate to project directory

```bash
# If repository doesn't exist locally:
if [ ! -d "$HOME/cluster_build_sources/config/ClusterSetupAndConfigs" ]; then
  echo "Cloning repository..."
  mkdir -p "$HOME/cluster_build_sources/config"
  cd "$HOME/cluster_build_sources/config"
  git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
else
  echo "Repository already exists"
  cd "$HOME/cluster_build_sources/config/ClusterSetupAndConfigs"
  git pull origin master  # Update to latest
fi

cd "$HOME/cluster_build_sources/config/ClusterSetupAndConfigs"
pwd  # Confirm location
```

### Step 0.6: Install uv Package Manager

**AI Agent Action:** Install uv for Python package management

```bash
# Check if uv is already installed:
if ! command -v uv &> /dev/null; then
  echo "Installing uv package manager..."
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Source uv environment:
  export PATH="$HOME/.cargo/bin:$PATH"

  # Verify installation:
  uv --version && echo "✓ uv installed successfully"
else
  echo "✓ uv already installed"
  uv --version
fi
```

### Step 0.7: Configure uv Environment (WSL Critical!)

**AI Agent Action:** Set UV_PROJECT_ENVIRONMENT

```bash
# CRITICAL for WSL: Virtual environment must be in Linux home directory
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Add to shell profile for persistence:
if ! grep -q "UV_PROJECT_ENVIRONMENT" ~/.bashrc; then
  echo 'export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup' >> ~/.bashrc
  echo "✓ UV_PROJECT_ENVIRONMENT added to ~/.bashrc"
fi

# Create virtual environment and install dependencies:
echo "Setting up Python environment with uv..."
cd "$HOME/cluster_build_sources/config/ClusterSetupAndConfigs"
uv sync

echo "✓ Python environment ready"
```

---

## Phase 1: Local Node Setup

### Step 1.1: Verify Configuration

**AI Agent Action:** Display config and confirm

```bash
cd "$HOME/cluster_build_sources/config/ClusterSetupAndConfigs"

echo "Configuration to be used:"
cat cluster_config_actual.yaml

echo ""
echo "Current node IP addresses:"
ip addr show | grep "inet 192.168" || ip addr show | grep "inet 10."

echo ""
read -p "Configuration looks correct? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
  echo "Please edit cluster_config_actual.yaml and run again"
  exit 1
fi
```

### Step 1.2: Run Cluster Setup (Interactive Mode)

**AI Agent Action:** Execute main setup script

```bash
cd "$HOME/cluster_build_sources/config/ClusterSetupAndConfigs"

# Ensure environment is set:
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

echo ""
echo "=========================================="
echo "STARTING CLUSTER SETUP"
echo "=========================================="
echo ""
echo "You will be prompted for your password ONCE."
echo "This password is used to:"
echo "  1. Configure passwordless sudo (Step 0)"
echo "  2. Setup SSH keys between all nodes"
echo "  3. Install packages on all nodes"
echo ""
echo "After Step 0, no more password prompts will occur."
echo ""

# Run setup with password prompt:
uv run python cluster_setup.py \
  --config cluster_config_actual.yaml \
  --password

# Note: --password flag enables automatic cluster-wide setup
# User will be prompted to enter password once
```

**Expected Output Flow:**
```
Enter cluster password: [user types password]

======================================================================
INITIALIZING MODULAR MANAGERS
======================================================================
✓ All managers initialized

======================================================================
MODULAR CLUSTER SETUP
======================================================================
Master Node: 192.168.1.10
Worker Nodes: 192.168.1.11, 192.168.1.12, 192.168.1.13
Current node is: MASTER
OS Type: ubuntu
Package Manager: apt-get
======================================================================

======================================================================
STEP 0: Configure Passwordless Sudo (CRITICAL - must be first)
======================================================================
[... sudo configuration output ...]
✓ Passwordless sudo configured - no more password prompts needed

======================================================================
STEP 1: SSH Keys and Passwordless SSH
======================================================================
[... SSH key generation and distribution ...]
✓ SSH keys distributed to all nodes

======================================================================
STEP 2: Homebrew, GCC, and Binutils
======================================================================
[... Homebrew installation ...]
[... GCC 15.2.0 installation ...]
[... Binutils 2.45 installation ...]
✓ Homebrew and compilers installed

======================================================================
STEP 3: System Configuration
======================================================================
[... /etc/hosts updates ...]
✓ System configuration complete

======================================================================
STEP 4: Parallel Programming Infrastructure
======================================================================
[... Slurm installation ...]
[... pdsh installation ...]
✓ Infrastructure ready

======================================================================
STEP 5: MPI and Parallel Libraries
======================================================================
[... OpenMPI 5.0.8 installation ...]
[... OpenMP installation ...]
✓ MPI libraries installed

======================================================================
STEP 6: PGAS Libraries
======================================================================
[... GASNet-EX 2024.5.0 compilation ...]
[... UPC++ 2024.3.0 compilation ...]
[... OpenSHMEM 1.5.2 compilation ...]
✓ PGAS libraries installed

======================================================================
STEP 7: Network Configuration
======================================================================
[... Firewall configuration ...]
✓ Network configured

======================================================================
STEP 8: Benchmark Generation
======================================================================
[... Creating benchmark files ...]
✓ Benchmarks generated

======================================================================
STEP 9: Final Configuration and Verification
======================================================================
[... Verification checks ...]
✓ Verification complete

======================================================================
✓ LOCAL NODE SETUP COMPLETED SUCCESSFULLY
======================================================================

======================================================================
CLUSTER SETUP SUMMARY
======================================================================
✓ Master node (this node) setup completed
✓ Automatic cluster-wide setup enabled

Your entire cluster is ready!

Next steps:
1. Test Slurm: sinfo
2. Test OpenMPI: mpirun -np 2 hostname
3. Test pdsh: pdsh -w 192.168.1.11,192.168.1.12 hostname
4. Generate benchmarks using BenchmarkManager
======================================================================
```

### Step 1.3: Verify Local Installation

**AI Agent Action:** Run verification checks

```bash
echo ""
echo "=========================================="
echo "VERIFICATION CHECKS"
echo "=========================================="
echo ""

# 1. Check GCC:
echo "1. Checking GCC..."
/home/linuxbrew/.linuxbrew/bin/gcc --version | head -n1

# 2. Check OpenMPI:
echo "2. Checking OpenMPI..."
mpicc --version | head -n1

# 3. Check Python 3.14:
echo "3. Checking Python..."
/home/linuxbrew/.linuxbrew/bin/python3.14 --version

# 4. Check UPC++:
echo "4. Checking UPC++..."
/home/linuxbrew/.linuxbrew/bin/upcxx --version 2>&1 | head -n1 || echo "UPC++ not in PATH yet (requires shell reload)"

# 5. Check Slurm:
echo "5. Checking Slurm..."
sinfo --version

# 6. Check SSH keys:
echo "6. Checking SSH keys..."
ls -l ~/.ssh/id_rsa ~/.ssh/id_ed25519 2>/dev/null | wc -l | xargs -I {} echo "{} SSH keys found"

# 7. Check passwordless sudo:
echo "7. Checking passwordless sudo..."
sudo -n true && echo "✓ Passwordless sudo working" || echo "✗ Passwordless sudo NOT working"

echo ""
echo "✓ Local node verification complete"
```

---

## Phase 2: Cluster Distribution (Automatic)

**Note:** If `--password` flag was used in Step 1.2, cluster-wide setup happens **automatically**. This phase is for manual distribution if needed.

### Step 2.1: Verify SSH Connectivity to All Nodes

**AI Agent Action:** Test SSH to all workers

```bash
echo ""
echo "=========================================="
echo "TESTING SSH CONNECTIVITY"
echo "=========================================="
echo ""

# Read worker IPs from config:
WORKERS=(192.168.1.11 192.168.1.12 192.168.1.13)
USERNAME="muyiwa"

for worker in "${WORKERS[@]}"; do
  echo "Testing SSH to $worker..."
  if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$USERNAME@$worker" "echo '✓ Connected'" 2>/dev/null; then
    echo "  ✓ $worker reachable"
  else
    echo "  ✗ $worker NOT reachable - check network/firewall"
  fi
done

echo ""
```

### Step 2.2: Distribute Configurations to All Nodes

**AI Agent Action:** Use pdsh or SSH loop

```bash
echo ""
echo "=========================================="
echo "DISTRIBUTING CONFIGURATIONS"
echo "=========================================="
echo ""

USERNAME="muyiwa"
MASTER_IP="192.168.1.10"
WORKERS=(192.168.1.11 192.168.1.12 192.168.1.13)

# Method 1: Using pdsh (if available):
if command -v pdsh &> /dev/null; then
  echo "Using pdsh for parallel distribution..."

  WORKER_LIST=$(IFS=,; echo "${WORKERS[*]}")

  # Distribute MCA config:
  echo "1. Distributing MPI MCA configuration..."
  pdsh -w "$WORKER_LIST" "mkdir -p ~/.openmpi"
  for worker in "${WORKERS[@]}"; do
    scp ~/.openmpi/mca-params.conf "$USERNAME@$worker:~/.openmpi/"
  done

  # Distribute hostfiles:
  echo "2. Distributing MPI hostfiles..."
  for worker in "${WORKERS[@]}"; do
    scp ~/.openmpi/hostfile* "$USERNAME@$worker:~/.openmpi/"
  done

  echo "✓ Configurations distributed via pdsh"

else
  # Method 2: Sequential SSH (fallback):
  echo "Using sequential SSH for distribution..."

  for worker in "${WORKERS[@]}"; do
    echo "Distributing to $worker..."

    ssh "$USERNAME@$worker" "mkdir -p ~/.openmpi"
    scp ~/.openmpi/mca-params.conf "$USERNAME@$worker:~/.openmpi/"
    scp ~/.openmpi/hostfile* "$USERNAME@$worker:~/.openmpi/" 2>/dev/null

    echo "  ✓ $worker configured"
  done

  echo "✓ Configurations distributed via SSH"
fi
```

### Step 2.3: Verify Cluster-Wide Installation

**AI Agent Action:** Test all nodes have required software

```bash
echo ""
echo "=========================================="
echo "CLUSTER-WIDE VERIFICATION"
echo "=========================================="
echo ""

USERNAME="muyiwa"
WORKERS=(192.168.1.11 192.168.1.12 192.168.1.13)

# Test GCC on all nodes:
echo "1. Checking GCC on all worker nodes..."
for worker in "${WORKERS[@]}"; do
  ssh "$USERNAME@$worker" "/home/linuxbrew/.linuxbrew/bin/gcc --version" 2>/dev/null | head -n1 | xargs -I {} echo "  $worker: {}"
done

# Test OpenMPI on all nodes:
echo ""
echo "2. Checking OpenMPI on all worker nodes..."
for worker in "${WORKERS[@]}"; do
  ssh "$USERNAME@$worker" "mpicc --version" 2>/dev/null | head -n1 | xargs -I {} echo "  $worker: {}"
done

# Test MCA config on all nodes:
echo ""
echo "3. Checking MPI MCA config on all worker nodes..."
for worker in "${WORKERS[@]}"; do
  echo "  $worker MCA config:"
  ssh "$USERNAME@$worker" "cat ~/.openmpi/mca-params.conf 2>/dev/null | grep -E '(btl_tcp|oob_tcp|orte_prefix)' | head -n3"
done

echo ""
echo "✓ Cluster-wide verification complete"
```

---

## Phase 3: Testing and Validation

### Step 3.1: Test Slurm Cluster

**AI Agent Action:** Verify Slurm sees all nodes

```bash
echo ""
echo "=========================================="
echo "TESTING SLURM"
echo "=========================================="
echo ""

# Check Slurm node status:
echo "Slurm node status:"
sinfo

echo ""
echo "Slurm node details:"
sinfo -N -l

# If nodes show "down", try restarting Slurm:
if sinfo | grep -q "down"; then
  echo ""
  echo "Some nodes are down, attempting to restart Slurm..."
  sudo systemctl restart slurmctld
  sleep 3
  USERNAME="muyiwa"
  WORKERS=(192.168.1.11 192.168.1.12 192.168.1.13)
  for worker in "${WORKERS[@]}"; do
    ssh "$USERNAME@$worker" "sudo systemctl restart slurmd"
  done
  sleep 3
  sinfo
fi
```

### Step 3.2: Test pdsh Parallel Execution

**AI Agent Action:** Run hostname on all nodes

```bash
echo ""
echo "=========================================="
echo "TESTING PDSH (PARALLEL SHELL)"
echo "=========================================="
echo ""

WORKERS=(192.168.1.11 192.168.1.12 192.168.1.13)
WORKER_LIST=$(IFS=,; echo "${WORKERS[*]}")

if command -v pdsh &> /dev/null; then
  echo "Running 'hostname' on all worker nodes in parallel:"
  pdsh -w "$WORKER_LIST" "hostname && echo 'OpenMPI version:' && mpicc --version | head -n1"
  echo ""
  echo "✓ pdsh working correctly"
else
  echo "⚠️  pdsh not available, using sequential SSH:"
  for worker in "${WORKERS[@]}"; do
    echo "Node $worker:"
    ssh "$USERNAME@$worker" "hostname && echo 'OpenMPI version:' && mpicc --version | head -n1"
    echo ""
  done
fi
```

### Step 3.3: Test OpenMPI Cross-Node Communication

**AI Agent Action:** Run MPI hello world across nodes

```bash
echo ""
echo "=========================================="
echo "TESTING OPENMPI CROSS-NODE COMMUNICATION"
echo "=========================================="
echo ""

# Test 1: Hostname distribution (should show all nodes):
echo "Test 1: Running hostname on 4 processes across nodes..."
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node \
       -np 4 \
       --hostfile ~/.openmpi/hostfile_optimal \
       hostname

echo ""

# Test 2: MPI rank distribution:
echo "Test 2: Checking MPI rank distribution..."
cat > /tmp/mpi_test_rank.c << 'EOF'
#include <mpi.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    char hostname[256];

    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    gethostname(hostname, 255);

    printf("Rank %d/%d running on %s\n", rank, size, hostname);

    MPI_Finalize();
    return 0;
}
EOF

# Compile:
mpicc -o /tmp/mpi_test_rank /tmp/mpi_test_rank.c

# Run:
mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \
       --map-by node \
       -np 4 \
       --hostfile ~/.openmpi/hostfile_optimal \
       /tmp/mpi_test_rank

echo ""
echo "Expected: Each rank should be on a different node"
echo "✓ If you see ranks distributed across hostnames, MPI is working!"
```

### Step 3.4: Test PGAS Libraries (UPC++ and OpenSHMEM)

**AI Agent Action:** Compile and run simple PGAS tests

```bash
echo ""
echo "=========================================="
echo "TESTING PGAS LIBRARIES"
echo "=========================================="
echo ""

# Test 1: UPC++ (if installed):
echo "Test 1: UPC++ installation..."
if [ -x "/home/linuxbrew/.linuxbrew/bin/upcxx" ]; then
  echo "✓ UPC++ compiler found"

  # Simple UPC++ hello world:
  cat > /tmp/upcxx_hello.cpp << 'EOF'
#include <upcxx/upcxx.hpp>
#include <iostream>

int main() {
    upcxx::init();
    std::cout << "Hello from UPC++ rank " << upcxx::rank_me()
              << " of " << upcxx::rank_n() << std::endl;
    upcxx::finalize();
    return 0;
}
EOF

  /home/linuxbrew/.linuxbrew/bin/upcxx -o /tmp/upcxx_hello /tmp/upcxx_hello.cpp
  echo "Running UPC++ hello world on 4 processes:"
  /home/linuxbrew/.linuxbrew/bin/upcxx-run -n 4 /tmp/upcxx_hello
  echo "✓ UPC++ working"
else
  echo "⚠️  UPC++ not found at /home/linuxbrew/.linuxbrew/bin/upcxx"
fi

echo ""

# Test 2: OpenSHMEM (if installed):
echo "Test 2: OpenSHMEM installation..."
if [ -x "/home/linuxbrew/.linuxbrew/bin/oshcc" ]; then
  echo "✓ OpenSHMEM compiler found"

  # Simple OpenSHMEM hello world:
  cat > /tmp/oshmem_hello.c << 'EOF'
#include <shmem.h>
#include <stdio.h>

int main(void) {
    shmem_init();
    int me = shmem_my_pe();
    int npes = shmem_n_pes();
    printf("Hello from OpenSHMEM PE %d of %d\n", me, npes);
    shmem_finalize();
    return 0;
}
EOF

  /home/linuxbrew/.linuxbrew/bin/oshcc -o /tmp/oshmem_hello /tmp/oshmem_hello.c
  echo "Running OpenSHMEM hello world on 4 processes:"
  /home/linuxbrew/.linuxbrew/bin/oshrun -n 4 /tmp/oshmem_hello
  echo "✓ OpenSHMEM working"
else
  echo "⚠️  OpenSHMEM not found at /home/linuxbrew/.linuxbrew/bin/oshcc"
fi
```

### Step 3.5: Generate and Run Benchmarks

**AI Agent Action:** Compile and execute benchmark suite

```bash
echo ""
echo "=========================================="
echo "GENERATING AND RUNNING BENCHMARKS"
echo "=========================================="
echo ""

cd ~/cluster_build_sources/benchmarks

# Benchmarks should already be generated by setup script
if [ -f "Makefile" ]; then
  echo "✓ Benchmarks already generated"
else
  echo "Generating benchmarks..."
  # Benchmarks are generated during setup (Step 8)
  # If missing, re-run:
  cd ~/cluster_build_sources/config/ClusterSetupAndConfigs
  export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
  uv run python -c "
from cluster_modules import BenchmarkManager
from pathlib import Path

mgr = BenchmarkManager(
    'muyiwa', '', '192.168.1.10',
    ['192.168.1.11', '192.168.1.12', '192.168.1.13'],
    Path.home() / 'cluster_build_sources' / 'benchmarks'
)

mgr.create_benchmark_directory()
mgr.create_mpi_latency_benchmark()
mgr.create_upcxx_latency_benchmark()
mgr.create_openshmem_latency_benchmark()
mgr.create_openmp_parallel_benchmark()
mgr.create_makefile()
mgr.create_run_script(num_procs=4)
"
  cd ~/cluster_build_sources/benchmarks
fi

# Compile benchmarks:
echo "Compiling benchmarks..."
make clean
make -j$(nproc)

echo ""
echo "✓ Benchmarks compiled"
echo ""
echo "Available benchmark binaries:"
ls -lh bin/

echo ""
echo "Running benchmark suite..."
./run_benchmarks.sh

echo ""
echo "✓ Benchmark execution complete"
echo "Results saved to ~/cluster_build_sources/benchmarks/results/"
```

---

## Phase 4: Post-Build Configuration (Optional)

### Step 4.1: Configure Firewall Rules (If Not Auto-Configured)

**AI Agent Action:** Ensure MPI ports are open

```bash
echo ""
echo "=========================================="
echo "VERIFYING FIREWALL CONFIGURATION"
echo "=========================================="
echo ""

cd ~/cluster_build_sources/config/ClusterSetupAndConfigs
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Verify firewall status:
uv run python cluster_modules/config_template_manager.py firewall verify

echo ""
read -p "Do you need to configure firewalls? (yes/no): " need_firewall

if [ "$need_firewall" = "yes" ]; then
  echo "Configuring firewalls on all nodes..."
  uv run python cluster_modules/config_template_manager.py firewall configure

  echo ""
  echo "Verifying firewall configuration..."
  uv run python cluster_modules/config_template_manager.py firewall verify
fi
```

### Step 4.2: Create Cluster Summary

**AI Agent Action:** Generate comprehensive cluster report

```bash
echo ""
echo "=========================================="
echo "CLUSTER BUILD SUMMARY"
echo "=========================================="
echo ""

cd ~/cluster_build_sources/config/ClusterSetupAndConfigs
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Generate summary:
uv run python cluster_modules/config_template_manager.py summary

echo ""
echo "Installed software versions:"
echo "  GCC: $(/home/linuxbrew/.linuxbrew/bin/gcc --version | head -n1)"
echo "  OpenMPI: $(mpicc --version | head -n1)"
echo "  Python: $(/home/linuxbrew/.linuxbrew/bin/python3.14 --version)"
echo "  Slurm: $(sinfo --version)"
echo "  UPC++: $(/home/linuxbrew/.linuxbrew/bin/upcxx --version 2>&1 | head -n1 || echo 'Not in PATH')"

echo ""
echo "Cluster directories:"
echo "  Build sources: ~/cluster_build_sources/"
echo "  Benchmarks: ~/cluster_build_sources/benchmarks/"
echo "  Configuration: ~/cluster_build_sources/config/ClusterSetupAndConfigs/"

echo ""
echo "Quick test commands:"
echo "  Slurm status: sinfo"
echo "  MPI test: mpirun --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal hostname"
echo "  pdsh test: pdsh -w <worker_ips> hostname"
echo "  Run benchmarks: cd ~/cluster_build_sources/benchmarks && ./run_benchmarks.sh"

echo ""
echo "=========================================="
echo "✓✓✓ CLUSTER BUILD COMPLETE ✓✓✓"
echo "=========================================="
```

---

## Error Recovery Procedures

### If Setup Fails at Any Step:

**AI Agent Action:**

```bash
# 1. Check error messages for specific failure
# 2. Run cluster cleanup:
cd ~/cluster_build_sources/config/ClusterSetupAndConfigs
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python cluster_modules/cluster_cleanup.py --config cluster_config_actual.yaml

# 3. Check prerequisites:
echo "Checking prerequisites..."
which git curl wget python3
sudo -n true && echo "✓ Passwordless sudo working" || echo "✗ Need sudo access"

# 4. Check network connectivity:
for worker in 192.168.1.11 192.168.1.12 192.168.1.13; do
  ping -c 1 "$worker" &> /dev/null && echo "✓ $worker reachable" || echo "✗ $worker unreachable"
done

# 5. Re-run setup with --clean-install flag:
uv run python cluster_setup.py \
  --config cluster_config_actual.yaml \
  --password \
  --clean-install
```

### Common Error Scenarios:

#### Error: "Operation not permitted" (WSL symlink issue)
```bash
# Fix: Ensure UV_PROJECT_ENVIRONMENT is set:
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
echo 'export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup' >> ~/.bashrc
```

#### Error: "PRTE has lost communication with remote daemon"
```bash
# Fix: Check MPI configuration:
cat ~/.openmpi/mca-params.conf
# Verify identical config on all nodes:
pdsh -w 192.168.1.11,192.168.1.12 "cat ~/.openmpi/mca-params.conf"
```

#### Error: "Permission denied (publickey)" when SSH to workers
```bash
# Fix: Re-distribute SSH keys:
cd ~/cluster_build_sources/config/ClusterSetupAndConfigs
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python -c "
from cluster_modules import SSHManager, ClusterCore
core = ClusterCore('192.168.1.10', ['192.168.1.11', '192.168.1.12', '192.168.1.13'], 'muyiwa', 'PASSWORD')
mgr = SSHManager(core)
mgr.configure_passwordless_ssh()
"
```

---

## AI Agent Decision Tree for "Build Cluster" Request

```
User says: "Build me an HPC cluster" or "Setup cluster" or similar

├─ Step 1: Gather requirements
│  ├─ Ask for master IP
│  ├─ Ask for worker IPs
│  ├─ Ask for username
│  └─ Ask if WSL is involved
│
├─ Step 2: Verify prerequisites
│  ├─ Check network connectivity
│  ├─ Check sudo access
│  └─ Check OS types
│
├─ Step 3: Create configuration file
│  └─ Generate cluster_config_actual.yaml
│
├─ Step 4: Execute build
│  ├─ Install prerequisites (git, curl, wget)
│  ├─ Clone repository
│  ├─ Install uv
│  ├─ Configure environment
│  └─ Run cluster_setup.py --password
│
├─ Step 5: Verify installation
│  ├─ Test Slurm (sinfo)
│  ├─ Test MPI (mpirun hostname)
│  ├─ Test pdsh
│  └─ Test PGAS (upcxx, openshmem)
│
├─ Step 6: Run benchmarks
│  ├─ Compile benchmarks
│  └─ Execute benchmark suite
│
└─ Step 7: Report results
   ├─ Show cluster summary
   ├─ Show installed versions
   └─ Provide quick test commands
```

---

## Fully Autonomous Build Script

For complete automation, AI agent can generate and execute:

```bash
#!/bin/bash
# autonomous_cluster_build.sh
# Complete autonomous HPC cluster build

set -e  # Exit on error

# Configuration (AI agent fills these):
MASTER_IP="192.168.1.10"
WORKER_IPS=("192.168.1.11" "192.168.1.12" "192.168.1.13")
USERNAME="muyiwa"
PASSWORD="<SECURE_PASSWORD>"  # User provides securely

# Phase 0: Pre-setup
echo "Phase 0: Pre-setup..."
cd "$HOME"
mkdir -p cluster_build_sources/config
cd cluster_build_sources/config

if [ ! -d "ClusterSetupAndConfigs" ]; then
  git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
fi

cd ClusterSetupAndConfigs

# Install uv if needed:
if ! command -v uv &> /dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.cargo/bin:$PATH"
fi

# Configure environment:
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
if ! grep -q "UV_PROJECT_ENVIRONMENT" ~/.bashrc; then
  echo 'export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup' >> ~/.bashrc
fi

# Setup Python environment:
uv sync

# Create config file:
cat > cluster_config_actual.yaml << EOF
master:
  ip: $MASTER_IP
  os: ubuntu
  name: master-node

workers:
$(for i in "${!WORKER_IPS[@]}"; do
  echo "  - ip: ${WORKER_IPS[$i]}"
  echo "    os: ubuntu"
  echo "    name: worker$((i+1))"
done)

username: $USERNAME
EOF

# Phase 1: Run setup
echo "Phase 1: Running cluster setup..."
echo "$PASSWORD" | uv run python cluster_setup.py \
  --config cluster_config_actual.yaml \
  --password \
  --non-interactive

# Phase 2: Verification
echo "Phase 2: Verifying installation..."
sinfo
mpirun --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal hostname

# Phase 3: Benchmarks
echo "Phase 3: Running benchmarks..."
cd ~/cluster_build_sources/benchmarks
make clean && make -j$(nproc)
./run_benchmarks.sh

echo ""
echo "✓✓✓ AUTONOMOUS BUILD COMPLETE ✓✓✓"
```

---

## Final Checklist for AI Agent

Before declaring "cluster build complete", verify:

- [ ] All nodes appear in `sinfo` output
- [ ] `mpirun --map-by node` distributes across all nodes
- [ ] `pdsh -w all_nodes hostname` works
- [ ] GCC 15.2.0 installed on all nodes
- [ ] OpenMPI 5.0.8 installed on all nodes
- [ ] UPC++ and OpenSHMEM available (optional but recommended)
- [ ] Benchmarks compile successfully
- [ ] At least one benchmark runs successfully across nodes
- [ ] Passwordless SSH works between all nodes
- [ ] Passwordless sudo works on all nodes
- [ ] Firewall allows MPI ports (50000-50200)
- [ ] No orphaned MPI processes from testing

---

## Quick Reference Commands for AI Agents

```bash
# Check cluster status:
sinfo && pdsh -w all_nodes "hostname && uptime"

# Test MPI:
mpirun --map-by node -np $(nproc) --hostfile ~/.openmpi/hostfile_optimal hostname

# Run benchmarks:
cd ~/cluster_build_sources/benchmarks && make && ./run_benchmarks.sh

# Cleanup cluster:
uv run python cluster_modules/cluster_cleanup.py --config cluster_config_actual.yaml

# Re-run setup:
cd ~/cluster_build_sources/config/ClusterSetupAndConfigs && \
  uv run python cluster_setup.py --config cluster_config_actual.yaml --password

# Fresh install:
cd ~/cluster_build_sources/config/ClusterSetupAndConfigs && \
  uv run python cluster_setup.py --config cluster_config_actual.yaml --password --clean-install

# Verify firewall:
uv run python cluster_modules/config_template_manager.py firewall verify

# Show cluster summary:
uv run python cluster_modules/config_template_manager.py summary
```

---

**End of Builder Agent Instructions**

**Version:** 1.0.0
**Last Updated:** November 4, 2025
**Compatible with:** ClusterSetupAndConfigs v3.0.0+
**AI Agents Supported:** Claude, GitHub Copilot, any agent with bash execution capability

**Note to AI Agents:** These instructions are designed for full autonomous execution. User intervention should only be required for:
1. Providing cluster IP addresses and credentials
2. Confirming critical actions (optional with --non-interactive)
3. Resolving network/hardware issues outside software scope
