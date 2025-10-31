# GitHub Copilot Instructions for ClusterSetupAndConfigs

## Environment Context

- **OS**: WSL (Windows Subsystem for Linux) on Ubuntu
- **Python Version**: 3.13 (via Homebrew at `/home/linuxbrew/.linuxbrew/bin/python3.13`)
- **Package Manager**: uv (fast Python package manager)
- **Filesystem**: Code is on Windows mount (`/mnt/z/...`)
- **Critical Issue**: Windows mounts don't support symlinks

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

### When suggesting Python code:
1. Use Python 3.13 features and syntax
2. Include type hints (project uses typing)
3. Follow existing code style

### When modifying dependencies:
1. Edit `pyproject.toml` 
2. Always follow with: `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv sync`

## Project Dependencies

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "PyYAML>=6.0",
    "textual>=0.47.0"
]
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
```yaml
master_ip: "192.168.1.x"
worker_ips:
  - "192.168.1.y"
  - "192.168.1.z"
username: "user"  # optional
```

**Important**: Script must be run from the node with IP matching `master_ip` for automatic worker setup.

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

## Recent Updates (October 2025)

### Node Detection
- Script automatically detects if running on master or worker node
- Compares local IPs (via `ip addr`) with `master_ip` from config
- Shows debug output: `DEBUG: Found IPs on interfaces: [...]`
- Warns if not running on master node

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
```

## Quick Fixes for Common Issues

| Issue | Quick Fix |
|-------|-----------|
| "Operation not permitted" | `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup` |
| "python3.13 not found" | `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"` |
| "Module not found" | `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup && uv sync` |
| "Wrong Python version" | `uv python pin 3.13` |
| Import errors | Use `uv run python script.py` |
| "Current node is: WORKER" | Run script from master node (check with `ip addr`) |
| "sudo: no password provided" | Script now handles this automatically via stdin piping |
| Slurm commands not found | `eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"` |

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
