# Claude AI Agent Instructions for ClusterSetupAndConfigs

## Project Overview

This is a Python 3.13 project using **uv** as the package manager. The project runs on **WSL (Windows Subsystem for Linux)** where the code is stored on a Windows filesystem mount (`/mnt/z/PycharmProjects/ClusterSetupAndConfigs`).

## Critical Setup Information

### Python Version
- **Required**: Python 3.13 (installed via Homebrew)
- **Location**: `/home/linuxbrew/.linuxbrew/bin/python3.13`
- **Check**: `python3.13 --version` or `/home/linuxbrew/.linuxbrew/bin/python3.13 --version`

### Package Manager: uv

**uv** is a fast Python package installer and resolver, similar to pip but much faster.

#### Installation
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### THE CRITICAL WSL PROBLEM

⚠️ **MOST IMPORTANT**: On WSL, Windows filesystem mounts (`/mnt/z`, `/mnt/c`, etc.) **DO NOT support symlinks**. This causes `uv` and `venv` to fail with:

```
error: failed to symlink file from ... to ... : Operation not permitted (os error 1)
```

### THE SOLUTION

**Always** set the virtual environment location to the Linux home directory before running any uv commands:

```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
```

This environment variable tells uv to create the virtual environment in `~/.venv/cluster-setup` (which is on the Linux filesystem) instead of `./.venv` (which would be on the Windows filesystem).

## Standard Workflow for Development

### Initial Setup
```bash
# 1. Ensure Python 3.13 is available
python3.13 --version

# 2. Set the environment variable
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# 3. Sync dependencies (creates venv and installs packages)
uv sync
```

### Running Scripts
```bash
# Set environment variable
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Run with uv
uv run python cluster_setup.py --help
uv run python cluster_setup_ui.py
```

### Adding Dependencies
```bash
# Set environment variable first
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Sync after manual pyproject.toml edits
uv sync
```

### Running Tests
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run pytest
```

## Project Dependencies

Current dependencies in `pyproject.toml`:
- **PyYAML>=6.0**: For YAML configuration file parsing
- **textual>=0.47.0**: For terminal UI

## Common Commands You'll Need

### Check Python Version
```bash
python3.13 --version
# or
/home/linuxbrew/.linuxbrew/bin/python3.13 --version
```

### List Available Python Versions (uv)
```bash
uv python list
```

### Check Current Environment
```bash
echo $UV_PROJECT_ENVIRONMENT
# Should output: /home/muyiwa/.venv/cluster-setup
```

### List Installed Packages
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv pip list
```

### Install Specific Python Version (uv)
```bash
uv python install 3.13
```

## Alternative: Using venv Directly

If uv continues to have issues, use Python's built-in venv:

```bash
# Create venv with copies (no symlinks) in home directory
python3.13 -m venv --copies ~/.venv/cluster-setup

# Activate
source ~/.venv/cluster-setup/bin/activate

# Install dependencies
pip install PyYAML textual

# Run scripts
python cluster_setup.py --help
python cluster_setup_ui.py
```

## Troubleshooting Guide

### Issue: "Operation not permitted" when creating venv
**Cause**: Trying to create symlinks on Windows filesystem  
**Solution**: Always use `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup`

### Issue: "python3.13: command not found"
**Cause**: Homebrew not in PATH  
**Solution**: 
```bash
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
# or use full path
/home/linuxbrew/.linuxbrew/bin/python3.13 --version
```

### Issue: "Package not found" after adding to pyproject.toml
**Cause**: Need to sync dependencies  
**Solution**:
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv sync
```

### Issue: UV using wrong Python version
**Solution**:
```bash
uv python pin /home/linuxbrew/.linuxbrew/bin/python3.13
```

### Issue: Import errors when running scripts
**Cause**: Dependencies not installed or wrong environment  
**Solution**:
```bash
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv sync
uv run python script.py
```

## Recent Improvements (October 2025)

### Node Detection System
The script now automatically detects if it's running on the master or worker node by:
- Checking all local network interfaces using `ip addr` command
- Comparing found IPs with the `master_ip` from config file
- Providing debug output showing hostname, detected IPs, and master IP
- Warning users if script is not running on master node

### Secure Sudo Password Handling
Improved security for sudo operations:
- Uses `subprocess.Popen` with stdin piping instead of command-line exposure
- Password never appears in process list or error messages
- Supports both local and remote sudo execution via wrapper scripts

### Troubleshooting Node Detection
If script shows "Current node is: WORKER" when you expected MASTER:
```bash
# Check what IPs the script detects
ip addr show | grep "inet "

# Script will output debug info:
# DEBUG: hostname='...', local_ip='...', master_ip='...'
# DEBUG: Found IPs on interfaces: [...]

# Ensure master_ip from config matches one of the detected IPs
```

## Best Practices for AI Agents

1. **Always check** if `UV_PROJECT_ENVIRONMENT` is set before running uv commands
2. **Always use** `export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup` in commands
3. **Never** try to create `.venv` in the project directory on WSL with Windows mounts
4. **Use** `uv run python script.py` instead of just `python script.py`
5. **Check** Python version with `python3.13 --version` before assuming it's available
6. **Suggest** adding the export to `~/.bashrc` for persistence
7. **Fall back** to standard venv if uv continues to have issues
8. **Always** run `uv sync` after modifying `pyproject.toml`
9. **Remind users** to run the script from the master node for full automation
10. **Check** DEPLOYMENT_GUIDE.md for comprehensive deployment instructions

## Project Structure

```
ClusterSetupAndConfigs/
├── cluster_setup.py          # Main CLI script
├── cluster_setup_ui.py       # Textual UI for setup
├── cluster_config.yaml        # Example config
├── cluster_config_actual.yaml # Actual config (not in git)
├── pyproject.toml            # Project metadata and dependencies
├── uv.lock                   # Lock file for exact dependency versions
├── README.md                 # User documentation
├── CLAUDE.md                 # This file (AI agent instructions)
└── test_cluster_setup.py     # Tests
```

## Configuration Format

The project uses YAML configuration files with the following format:

```yaml
master_ip: "192.168.1.147"
worker_ips:
  - "192.168.1.137"
  - "192.168.1.96"
username: "myuser"  # optional, defaults to current user
```

**Important**: The script MUST be run from the node with IP matching `master_ip` for automatic worker setup to occur.

## Key Scripts

### cluster_setup.py
Main command-line tool for cluster setup. Usage:
```bash
uv run python cluster_setup.py --config cluster_config.yaml --password
```

### cluster_setup_ui.py
Interactive terminal UI. Usage:
```bash
uv run python cluster_setup_ui.py
```

## When Making Code Changes

1. Verify types are correct (project uses type hints)
2. Run `uv sync` after dependency changes
3. Test with `uv run python script.py`
4. Update this documentation if adding new dependencies or changing setup process

## Remember

- This is a WSL environment with Windows filesystem mounts
- Virtual environments MUST be in Linux home directory
- Always set `UV_PROJECT_ENVIRONMENT` before uv commands
- Python 3.13 from Homebrew is required
- Use `uv run` to execute scripts with the correct environment
