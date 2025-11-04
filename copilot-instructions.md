# GitHub Copilot Instructions for ClusterSetupAndConfigs

## Environment Context

- **OS Support**: Ubuntu/Debian (apt-get) OR Red Hat/CentOS/Fedora (dnf)
- **WSL Support**: Works on WSL with proper configuration
  - **CRITICAL**: Requires mirrored mode networking (`networkingMode = mirrored` in `.wslconfig`)
  - Without mirrored mode, WSL uses NAT with internal IP inaccessible from other cluster nodes
- **Python Version**: 3.14 (via Homebrew at `/home/linuxbrew/.linuxbrew/bin/python3.14`)
- **Package Manager**: uv (fast Python package manager)
- **Run from Any Node**: Script can run from master or any worker - automatic detection
- **Multi-OS Clusters**: Automatic OS detection and package manager selection
- **Critical WSL Issue**: Windows mounts don't support symlinks

## Quick Reference Commands

### Setup Environment (REQUIRED before any uv command)
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
```

### Common Operations
```bash
# Sync dependencies
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv sync

# Run scripts
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv run python cluster_setup.py --help

# Add dependency
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv add package-name

# List packages
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv pip list
```

## The WSL Symlink Problem

**Problem**: Creating virtual environments on Windows filesystem mounts fails:
```
error: failed to symlink file: Operation not permitted (os error 1)
```

**Root Cause**: WSL cannot create symlinks on `/mnt/z`, `/mnt/c`, etc.

**Solution**: Always set virtual environment to Linux home directory:
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
```

## WSL Network Configuration (CRITICAL for Cluster)

**Required for cluster operation**: WSL must use mirrored mode networking.

Create or edit `C:\Users\<YourUsername>\.wslconfig` on Windows:
```ini
[wsl2]
networkingMode = mirrored
```

Then restart WSL:
```powershell
wsl --shutdown
```

**Why this is required**:
- Default NAT mode: WSL gets internal IP (172.x.x.x) not accessible from cluster nodes
- Mirrored mode: WSL gets same IP as Windows host on physical network
- Without mirrored mode: Cluster nodes cannot communicate with WSL node

After enabling mirrored mode, configure Windows Firewall (PowerShell as Administrator):
```powershell
.\configure_wsl_firewall.ps1
```

## Code Generation Guidelines

### When generating shell commands:
1. **Always** include the environment variable:
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv sync
```

2. **Never** suggest creating `.venv` in project directory

3. **Always** use `uv run` for Python scripts:
```bash
uv run python script.py
```

## Code Style Rules

1. Use Python 3.14 features and syntax
2. Add type hints to all functions

### When modifying dependencies:
1. Edit `pyproject.toml` 
2. Always follow with: `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv sync`

## Project Dependencies

```toml
name = "cluster-setup"
version = "0.1.0"
description = "Cluster setup and configuration tools"
requires-python = ">=3.14"
```

## Common Scenarios

### User wants to add a new package
```bash
# Suggest this:
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv add package-name

# NOT this:
uv add package-name  # Missing environment variable!
```

### User has import errors
```bash
# Suggest this:
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv sync
uv run python script.py

# Explain: Dependencies may need to be synced
```

### User wants to run tests
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run pytest
```

### User asks about virtual environment location
- **Correct**: `~/.venv/cluster-setup` (Linux filesystem)
- **Wrong**: `./.venv` (Windows filesystem - will fail)

## Type Checking

Project uses type hints. When generating or modifying code:

```python
# Good
def setup_cluster(config_file: str, password: Optional[str] = None) -> bool:
    pass

# Bad
def setup_cluster(config_file, password=None):
    pass
```

## Error Handling Patterns

```python
# Follow this pattern
try:
    result = self.run_command(cmd, check=True)
    return True
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")
    return False
except Exception as e:
    print(f"Unexpected error: {e}")
    return False
```

## Configuration Files

### YAML Config Format

**Simple Format:**
```yaml
master: 192.168.1.10
workers:
  - 192.168.1.11
  - 192.168.1.12
username: myuser  # optional
```

**Extended Format (with OS and hostname - Recommended for Multi-OS):**
```yaml
master:
  ip: 192.168.1.10
  os: ubuntu wsl2
  name: master-node
workers:
  - ip: 192.168.1.11
    os: ubuntu
    name: worker1
  - ip: 192.168.1.12
    os: redhat  # Red Hat worker - script will use dnf
    name: worker2-redhat
username: myuser  # optional
```

Both formats are supported. The code automatically detects and extracts IPs from either format.

**Important Features:**
- **Run from Any Node**: Script can run from master or any worker node
- **Automatic Detection**: Uses `ip addr` to detect current node
- **Multi-OS Support**: Automatically detects Ubuntu (apt-get) vs Red Hat (dnf)
- **Other-Node Setup**: Sets up all nodes EXCEPT the current one

### Load Config
```python
import yaml

def load_yaml_config(path: str) -> Dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}
```

## Textual UI Patterns

When working with Textual UI:

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, Input

class MyApp(App):
    CSS = """
    /* Include styling */
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        # Components
        yield Footer()
```

## Testing Guidelines

When suggesting test commands:

```bash
# Always include environment setup
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run pytest test_cluster_setup.py -v
```

## Documentation Updates

When modifying functionality:
1. Update docstrings
2. Update README.md if user-facing
3. Update CLAUDE.md if it affects AI agent workflow
4. Update this file if it affects Copilot suggestions

## Command-Line Argument Patterns

Follow existing pattern:

```python
parser = argparse.ArgumentParser(
    description="Description",
    epilog="Example usage"
)
parser.add_argument('--config', '-c', required=True, help='...')
parser.add_argument('--password', '-p', action='store_true', help='...')
parser.add_argument('--non-interactive', action='store_true', help='Skip confirmation prompts')
```

**Note**: The `--non-interactive` flag is used internally when running on worker nodes to avoid prompting for user input during automated setup.

## Subprocess Execution Pattern

```python
def run_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        if check:
            raise
        return e  # Note: Type issue here, consider refactoring
```

## SSH Operations Pattern

```python
# For password-based SSH operations
import tempfile
import os

with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass:
    temp_pass.write(password)
    temp_pass_path = temp_pass.name

try:
    cmd = f'sshpass -f {temp_pass_path} ssh {user}@{host} "command"'
    self.run_command(cmd)
finally:
    os.unlink(temp_pass_path)  # Clean up
```

## File Operations

```python
from pathlib import Path

# Use Path for file operations
ssh_dir = Path.home() / ".ssh"
ssh_dir.mkdir(mode=0o700, exist_ok=True)

config_file = ssh_dir / "config"
with open(config_file, 'w') as f:
    f.write(content)
config_file.chmod(0o600)
```

## Reminder Checklist for Common Tasks

### Adding a dependency:
- [ ] Add to `pyproject.toml` dependencies array
- [ ] Run `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv sync`
- [ ] Test import with `uv run python -c "import package"`

### Running the cluster setup:
- [ ] Config file exists
- [ ] Export UV_PROJECT_ENVIRONMENT
- [ ] Use `uv run python cluster_setup.py --config file.yaml`

### Creating new Python files:
- [ ] Include type hints
- [ ] Add docstrings
- [ ] Follow existing code style
- [ ] Import from typing: Optional, List, Dict, etc.

### Debugging import errors:
- [ ] Check UV_PROJECT_ENVIRONMENT is set
- [ ] Run `uv sync`
- [ ] Verify package in `uv pip list`
- [ ] Use `uv run python` not just `python`

## Recent Updates (2025)

### Run from Any Node (Jan 2025)
- Script can run from master OR any worker node
- Automatically detects current node via `ip addr`
- Sets up all OTHER nodes (excluding current)
- If run from worker: sets up master + all other workers

### Multi-OS Support (Jan 2025)
- Supports Ubuntu/Debian (apt-get) AND Red Hat/CentOS/Fedora (dnf)
- Automatic OS detection via `/etc/os-release`
- Package manager auto-selection (apt-get vs dnf)
- Different package names handled automatically:
  - SSH: `openssh-client` vs `openssh-clients`
  - Slurm: `slurm-wlm` vs `slurm`

### Node Detection (Oct 2025)
- Script automatically detects which node it's running on
- Compares all local IPs (via `ip addr`) with master/worker IPs
- Shows debug output: `DEBUG: Found IPs on interfaces: [...]`
- Creates list of "other nodes" to setup

### MPI Cluster Critical Fixes (Nov 2025)

#### MPICH vs OpenMPI Incompatibility
- **CRITICAL**: MPICH and OpenMPI cannot coexist in a cluster
- PRTE daemons fail with "lost communication" errors
- Script automatically detects and removes MPICH before installing OpenMPI
- All nodes must use same MPI implementation (OpenMPI 5.0.8)
```bash
# Detection in install_openmpi()
brew list mpich 2>/dev/null && brew uninstall mpich
brew link open-mpi
```

#### SSH Key Mesh Distribution
- **CRITICAL**: Full mesh required for any-node-as-head capability
- Not just master → workers, but ALL nodes → ALL nodes
- `distribute_ssh_keys_between_all_nodes()` collects and distributes all keys
- Called automatically after node setup completes
```python
# Collects keys from all nodes (master + workers)
# Distributes each node's key to all other nodes
# Ensures any node can SSH to any other node
```

#### MCA Configuration Distribution
- **CRITICAL**: Consistent OpenMPI settings on all nodes
- Port ranges, network interface selection, prefix paths
- `distribute_mca_config_to_all_nodes()` copies config cluster-wide
- Called automatically after SSH key distribution
```bash
# Critical MCA parameters:
btl_tcp_port_min_v4 = 50000
oob_tcp_port_range = 50100-50200
oob_tcp_if_include = ens1f0  # For multi-NIC nodes
```

#### Multi-Interface Network Handling
- Nodes with multiple NICs on same subnet cause routing confusion
- PRTE daemons advertise multiple IPs, routing fails
- **Solution**: Specify exact interface in MCA config
- **Performance**: ALWAYS bias towards highest throughput interface
```bash
# Detect multi-interface nodes
ip addr show | grep "inet 10.0.0"

# Check interface speeds - choose fastest for MPI
ethtool ens1f0 | grep Speed  # 10000Mb/s (10 Gbps)
ethtool ens1f1 | grep Speed  # 1000Mb/s (1 Gbps)

# Configure in ~/.openmpi/mca-params.conf - use FASTEST interface
oob_tcp_if_include = ens1f0  # 10 Gbps interface for MPI traffic
btl_tcp_if_include = ens1f0  # Same for bulk transfer layer
```

**Key Insight**: MPI performance scales with network bandwidth. A 10 Gbps interface provides 10x better message passing performance than 1 Gbps.

#### --map-by node Requirement (OpenMPI 5.x)
- **CRITICAL**: Without this flag, all processes run on first node
- OpenMPI 5.x changed default behavior from round-robin to sequential
- **ALWAYS** use `--map-by node` for cross-cluster distribution
```bash
# Correct
mpirun --map-by node -np 16 --hostfile /tmp/hosts ./program

# Wrong (all 16 processes on first node!)
mpirun -np 16 --hostfile /tmp/hosts ./program
```

### MPI Hostfiles (Auto-Generated)
The setup script creates **three hostfiles** at `~/.openmpi/`:

1. **`hostfile_optimal`** ⭐ **RECOMMENDED**
   - 1 slot per node (1 MPI process per node)
   - Best for hybrid MPI+OpenMP codes
   - Minimizes communication overhead
   - Allows maximum OpenMP threads per process

2. **`hostfile_max`**
   - Auto-detected cores per node (e.g., 16, 16, 44, 32)
   - Best for pure MPI codes (no OpenMP)
   - Maximum parallel decomposition

3. **`hostfile`** (standard)
   - Fixed 4 slots per node
   - Balanced general-purpose configuration

**Usage**:
```bash
# Optimal (1 process/node, max threads)
export OMP_NUM_THREADS=16  # or auto-detect
mpirun --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal ./program

# Maximum MPI (152 processes total)
mpirun --map-by node -np 152 --hostfile ~/.openmpi/hostfile_max ./program
```

**When to use which**:
- Heterogeneous cluster → `hostfile_optimal`
- Large communication patterns → `hostfile_optimal`
- Embarrassingly parallel → `hostfile_max`

### UPC++ and PGAS Programming

**Berkeley UPC++ Installation**:
```bash
# Compiler wrapper
/home/linuxbrew/.linuxbrew/bin/upcxx

# Runtime launcher
/home/linuxbrew/.linuxbrew/bin/upcxx-run
```

**Quick UPC++ Usage**:
```bash
# Compile
upcxx -O3 myprogram.cpp -o myprogram

# Run single-node (SMP conduit)
upcxx-run -n 4 ./myprogram

# Run multi-node (MPI conduit)
upcxx-run -ssh-servers node1,node2,node3 -n 12 ./myprogram
```

**PGAS Libraries Installed**:
- **UPC++**: C++ PGAS library with global pointers, one-sided communication
- **GASNet**: Communication layer (SMP/MPI/UDP conduits)
- **OpenSHMEM**: Symmetric memory PGAS library

**When to Recommend UPC++**:
- Remote memory access patterns (rput/rget)
- Irregular/dynamic communication
- Asynchronous operations needed
- Simpler than MPI for certain algorithms

**Documentation**: https://upcxx.lbl.gov/docs/html/guide.html

### Secure Sudo Password Handling
- Uses `subprocess.Popen` with stdin piping
- Password never exposed in command line or process list
- Supports both local and remote sudo execution

### Troubleshooting Node Detection
```bash
# Check detected IPs
ip addr show | grep "inet "

# Script outputs:
# DEBUG: hostname='...', local_ip='...', master_ip='...'
# DEBUG: Found IPs on interfaces: [...]
# Current node is: MASTER or WORKER (10.0.0.X)
# Will setup these other nodes: [...]
```

## Quick Fixes for Common Issues

| Issue | Quick Fix |
|-------|-----------|
| "Operation not permitted" | `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup` |
| "python3.14 not found" | `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"` |
| "Dependencies not found" | `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv sync` |
| "Wrong Python version" | `uv python pin 3.14` |
| Import errors | Use `uv run python script.py` |
| "Current node is: WORKER" | Script can run from any node - will setup all others |
| "sudo: no password provided" | Script now handles this automatically via stdin piping |
| Slurm commands not found | `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"` |
| "PRTE lost communication" | Check: same MPI on all nodes, SSH key mesh, MCA config |
| "All MPI ranks on one node" | **ALWAYS** use `mpirun --map-by node` |
| Multiple IPs on one node | Add `oob_tcp_if_include = interface` to MCA config |
| MPICH/OpenMPI conflict | Script auto-detects and removes MPICH |

## Documentation References

- **README.md**: User-facing documentation and basic troubleshooting
- **CLAUDE.md**: Comprehensive AI agent instructions
- **DEPLOYMENT_GUIDE.md**: Complete deployment guide with advanced troubleshooting
- **USAGE_EXAMPLES.md**: Practical usage examples

## Remember

🔴 **NEVER suggest creating .venv in project directory on WSL**
🟢 **ALWAYS set UV_PROJECT_ENVIRONMENT before uv commands**
🟢 **ALWAYS use `uv run` for executing Python scripts**
🟢 **REMIND users to run from master node for full automation**
🟢 **REFER to DEPLOYMENT_GUIDE.md for complex issues**
🟢 **ALWAYS sync after modifying pyproject.toml**
