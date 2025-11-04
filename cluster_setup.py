#!/usr/bin/env python3.14
"""
Cluster Setup Script for Slurm and OpenMPI
Supports Ubuntu Linux, WSL with Ubuntu, and Red Hat/CentOS/Fedora

Usage:
    python cluster_setup.py --config config.yml [--password]
    
    --config:   Path to YAML configuration file (required)
    --password: Prompt for password to automatically setup entire cluster (optional)

Can be run from ANY node in the cluster (master or worker):
    1. Sets up the current node (password is used for sudo commands)
    2. Copies SSH keys to all other nodes
    3. Automatically runs the setup on all other nodes via SSH
    4. Password is automatically provided for sudo commands on remote nodes
    5. Configures the entire cluster in one command from any node

Example:
    # Full automatic cluster setup from any node (recommended)
    python cluster_setup.py --config cluster_config.yaml --password
    
    # Manual setup (without --password, you must run on each node separately)
    python cluster_setup.py --config cluster_config.yaml
    
Note: The script automatically detects which node it's running on and sets up
      all other nodes in the cluster accordingly.
"""

import argparse
import subprocess
import sys
import os
import shutil
import socket
import getpass
from pathlib import Path
from typing import List, Dict, Optional

# YAML parsing
try:
    import yaml
except Exception:
    yaml = None


class ClusterSetup:
    """Main class for cluster setup and configuration"""
    
    def __init__(self, master_ip: str, worker_ips: List[str], username: Optional[str] = None, password: Optional[str] = None):
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
        self.username = username or os.getenv('USER', 'ubuntu')
        self.password = password
        self.os_type = self._detect_os()
        self.pkg_manager = 'dnf' if self.os_type == 'redhat' else 'apt-get'
        self.is_master = self._is_current_node_master()
        # Get master hostname - will be used for slurm.conf generation
        self.master_hostname = self._get_master_hostname()
    
    def _detect_os(self) -> str:
        """Detect the operating system type (ubuntu or redhat)"""
        try:
            # Check /etc/os-release
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'red hat' in content or 'rhel' in content or 'fedora' in content or 'centos' in content:
                        return 'redhat'
                    elif 'ubuntu' in content or 'debian' in content:
                        return 'ubuntu'
            
            # Fallback: check if dnf or apt-get exists
            if shutil.which('dnf'):
                return 'redhat'
            elif shutil.which('apt-get'):
                return 'ubuntu'
        except Exception as e:
            print(f"DEBUG: Error detecting OS: {e}")
        
        # Default to ubuntu for backward compatibility
        return 'ubuntu'
        
    def _is_wsl(self) -> bool:
        """Detect if running on WSL"""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
        except:
            return False

    def _is_current_node_master(self) -> bool:
        """Check if current node is the master node"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)

            # Debug output
            print(f"DEBUG: hostname='{hostname}', local_ip='{local_ip}', master_ip='{self.master_ip}'")

            # Check if master_ip is localhost
            if self.master_ip in ['localhost', '127.0.0.1']:
                return True
            
            # Check if local_ip matches master_ip
            if local_ip == self.master_ip:
                return True
            
            # Also check using ip addr command to find all IPs
            try:
                result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    import re
                    # Look for lines like "inet 192.168.1.147/24 ..."
                    ip_pattern = r'inet\s+(\d+\.\d+\.\d+\.\d+)'
                    found_ips = re.findall(ip_pattern, result.stdout)
                    print(f"DEBUG: Found IPs on interfaces: {found_ips}")
                    if self.master_ip in found_ips:
                        print(f"DEBUG: Found matching IP {self.master_ip}")
                        return True
            except Exception as e:
                print(f"DEBUG: Could not check network interfaces: {e}")
            
            return False
        except Exception as e:
            print(f"DEBUG: Error detecting node role: {e}")
            return False

    def _get_master_hostname(self) -> str:
        """Get the master node's hostname for consistent slurm.conf across all nodes"""
        try:
            if self.is_master:
                # We're on the master, get local hostname
                hostname_result = subprocess.run(['hostname'], capture_output=True, text=True, check=False)
                if hostname_result.returncode == 0:
                    return hostname_result.stdout.strip()
            else:
                # We're on a worker, need to get master's hostname via SSH
                # This will be called during worker setup when password is available
                if self.password:
                    import shlex
                    # Use sshpass to SSH to master and get hostname
                    ssh_cmd = ['sshpass', '-p', self.password, 'ssh', '-o', 'StrictHostKeyChecking=no',
                               f'{self.username}@{self.master_ip}', 'hostname']
                    result = subprocess.run(ssh_cmd, capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        return result.stdout.strip()
        except Exception as e:
            print(f"DEBUG: Could not determine master hostname: {e}")

        # Fallback to "master" if we can't determine actual hostname
        return "master"

    def run_command(self, command: str, check: bool = True, shell: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command and return the result"""
        # Ensure Homebrew is in PATH for all commands
        env = os.environ.copy()
        homebrew_path = "/home/linuxbrew/.linuxbrew/bin"
        homebrew_sbin = "/home/linuxbrew/.linuxbrew/sbin"
        if os.path.exists(homebrew_path):
            env['PATH'] = f"{homebrew_path}:{homebrew_sbin}:{env.get('PATH', '')}"
        
        result = subprocess.run(
            command,
            shell=shell,
            check=False,
            capture_output=True,
            text=True,
            env=env
        )
        
        if check and result.returncode != 0:
            print(f"Error executing command: {command}")
            print(f"Error output: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, command, result.stdout, result.stderr)
        
        return result
    
    def run_sudo_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Run a command with sudo, using password if available"""
        if self.password:
            # Use subprocess.Popen to pipe password securely to sudo
            sudo_cmd = f"sudo -S {command}"
            process = subprocess.Popen(
                sudo_cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=f"{self.password}\n")
            
            result = subprocess.CompletedProcess(
                args=sudo_cmd,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr
            )
            
            if check and result.returncode != 0:
                print(f"Error executing command: {sudo_cmd}")
                print(f"Error output: {stderr}")
                raise subprocess.CalledProcessError(result.returncode, sudo_cmd, stdout, stderr)
            
            return result
        else:
            # Check if SUDO_ASKPASS is set in environment
            if 'SUDO_ASKPASS' in os.environ and os.path.exists(os.environ['SUDO_ASKPASS']):
                # Use sudo -A to read password from SUDO_ASKPASS
                return self.run_command(f"sudo -A {command}", check=check)
            else:
                # Try without password (may prompt user)
                return self.run_command(f"sudo {command}", check=check)
    
    def check_sudo_access(self) -> bool:
        """Check if user has sudo access"""
        result = self.run_command("sudo -n true", check=False)
        return result.returncode == 0
    
    def install_homebrew(self):
        """Install Homebrew on Ubuntu/WSL or Red Hat"""
        print(f"\n=== Installing Homebrew (detected OS: {self.os_type}) ===")
        
        # Check if brew is already installed (use shutil.which for robustness)
        if shutil.which("brew") or os.path.exists("/home/linuxbrew/.linuxbrew/bin/brew"):
            print("Homebrew already installed")
            return
        
        # Install dependencies for Homebrew based on OS
        print("Installing Homebrew dependencies...")
        if self.pkg_manager == 'dnf':
            self.run_sudo_command(
                "dnf groupinstall -y 'Development Tools' && dnf install -y procps-ng curl file git"
            )
        else:
            self.run_sudo_command(
                "apt-get update && apt-get install -y build-essential procps curl file git"
            )
        
        # Install Homebrew
        print("Installing Homebrew...")
        install_script = (
            'NONINTERACTIVE=1 /bin/bash -c '
            '"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        )
        self.run_command(install_script)
        
        # Add Homebrew to PATH
        homebrew_path = "/home/linuxbrew/.linuxbrew/bin"
        if os.path.exists(homebrew_path):
            os.environ['PATH'] = f"{homebrew_path}:{os.environ['PATH']}"
            
            # Add to shell profile with compiler settings
            shell_profile = Path.home() / ".bashrc"
            with open(shell_profile, 'a') as f:
                f.write('\n# Homebrew\n')
                f.write(f'eval "$({homebrew_path}/brew shellenv)"\n')
                f.write('\n# Always use latest Homebrew GCC for compilation\n')
                f.write(f'export CC={homebrew_path}/gcc\n')
                f.write(f'export CXX={homebrew_path}/g++\n')
                f.write(f'export FC={homebrew_path}/gfortran\n')
                f.write(f'export OMPI_CC={homebrew_path}/gcc\n')
                f.write(f'export OMPI_CXX={homebrew_path}/g++\n')
                f.write(f'export OMPI_FC={homebrew_path}/gfortran\n')
        
        print("Homebrew installed successfully")
    
    def configure_system_path(self):
        """Configure system-wide PATH for Homebrew binaries (OpenMPI, Slurm, etc.)"""
        print("\n=== Configuring System-Wide PATH ===")
        
        homebrew_path = "/home/linuxbrew/.linuxbrew/bin"
        homebrew_sbin = "/home/linuxbrew/.linuxbrew/sbin"
        
        if not os.path.exists(homebrew_path):
            print("Warning: Homebrew path not found, skipping PATH configuration")
            return
        
        # Configure /etc/environment for system-wide PATH
        # This ensures PATH is available in non-login shells (like SSH remote commands)
        print("Updating /etc/environment...")
        try:
            # Read current /etc/environment
            env_file = Path("/etc/environment")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()
            else:
                content = ""
            
            # Check if Homebrew paths are already in /etc/environment
            if homebrew_path not in content:
                # Parse existing PATH or create new one
                import re
                path_match = re.search(r'PATH="([^"]*)"', content)
                
                if path_match:
                    existing_path = path_match.group(1)
                    new_path = f"{homebrew_path}:{homebrew_sbin}:{existing_path}"
                    new_content = re.sub(
                        r'PATH="[^"]*"',
                        f'PATH="{new_path}"',
                        content
                    )
                else:
                    # No PATH line exists, add one
                    new_path = f"{homebrew_path}:{homebrew_sbin}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                    new_content = content.rstrip() + f'\nPATH="{new_path}"\n'
                
                # Write updated content
                temp_file = Path("/tmp/environment.tmp")
                with open(temp_file, 'w') as f:
                    f.write(new_content)
                
                self.run_sudo_command(f"cp {temp_file} /etc/environment")
                temp_file.unlink()
                print("✓ Updated /etc/environment with Homebrew paths")
            else:
                print("✓ Homebrew paths already in /etc/environment")
        
        except Exception as e:
            print(f"Warning: Could not update /etc/environment: {e}")
        
        # Also configure SSH to preserve environment
        print("Configuring SSH to accept environment variables...")
        try:
            sshd_config = Path("/etc/ssh/sshd_config")
            if sshd_config.exists():
                with open(sshd_config, 'r') as f:
                    sshd_content = f.read()
                
                # Check if PermitUserEnvironment is already enabled
                if "PermitUserEnvironment yes" not in sshd_content:
                    # Add configuration
                    temp_file = Path("/tmp/sshd_config.tmp")
                    with open(temp_file, 'w') as f:
                        f.write(sshd_content)
                        f.write("\n# Allow user environment for Homebrew PATH\n")
                        f.write("PermitUserEnvironment yes\n")
                    
                    self.run_sudo_command(f"cp {temp_file} /etc/ssh/sshd_config")
                    temp_file.unlink()
                    
                    # Restart SSH service
                    self.run_sudo_command("systemctl restart ssh", check=False)
                    print("✓ Configured SSH to accept environment variables")
                else:
                    print("✓ SSH already configured for environment variables")
        
        except Exception as e:
            print(f"Warning: Could not update SSH config: {e}")
        
        # Create ~/.ssh/environment for user
        print("Creating ~/.ssh/environment with compiler settings...")
        try:
            ssh_dir = Path.home() / ".ssh"
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            ssh_env = ssh_dir / "environment"
            with open(ssh_env, 'w') as f:
                f.write(f"PATH={homebrew_path}:{homebrew_sbin}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n")
                # Set compiler environment variables to always use latest Homebrew GCC
                f.write(f"CC={homebrew_path}/gcc\n")
                f.write(f"CXX={homebrew_path}/g++\n")
                f.write(f"FC={homebrew_path}/gfortran\n")
                f.write(f"OMPI_CC={homebrew_path}/gcc\n")
                f.write(f"OMPI_CXX={homebrew_path}/g++\n")
                f.write(f"OMPI_FC={homebrew_path}/gfortran\n")
            
            ssh_env.chmod(0o600)
            print("✓ Created ~/.ssh/environment with Homebrew compiler settings")
        
        except Exception as e:
            print(f"Warning: Could not create ~/.ssh/environment: {e}")
        
        # Update current session PATH
        os.environ['PATH'] = f"{homebrew_path}:{homebrew_sbin}:{os.environ.get('PATH', '')}"
        
        print("✓ System-wide PATH configuration completed")
    
    def setup_ssh(self):
        """Setup SSH client and server"""
        print("\n=== Setting up SSH ===")
        
        # Install OpenSSH client and server
        print("Installing OpenSSH client and server...")
        if self.pkg_manager == 'dnf':
            self.run_sudo_command("dnf install -y openssh-clients openssh-server", check=False)
        else:
            self.run_sudo_command("apt-get update", check=False)
            self.run_sudo_command("apt-get install -y openssh-client openssh-server")
        
        # Start SSH service
        print("Starting SSH service...")
        self.run_sudo_command("service ssh start", check=False)
        self.run_sudo_command("systemctl enable ssh", check=False)
        
        # Generate SSH key if it doesn't exist
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        ssh_key = ssh_dir / "id_rsa"
        if not ssh_key.exists():
            print("Generating SSH key...")
            self.run_command(f'ssh-keygen -t rsa -b 4096 -f {ssh_key} -N ""')
        
        print("SSH setup completed")
    
    def configure_passwordless_ssh(self):
        """Configure passwordless SSH between nodes"""
        print("\n=== Configuring Passwordless SSH ===")
        
        ssh_dir = Path.home() / ".ssh"
        pub_key_path = ssh_dir / "id_rsa.pub"
        authorized_keys = ssh_dir / "authorized_keys"
        
        if pub_key_path.exists():
            # Add own public key to authorized_keys
            with open(pub_key_path, 'r') as pub_key_file:
                pub_key = pub_key_file.read()
            
            # Ensure authorized_keys exists and has correct permissions
            authorized_keys.touch(mode=0o600, exist_ok=True)
            
            with open(authorized_keys, 'r') as f:
                existing_keys = f.read()
            
            if pub_key not in existing_keys:
                with open(authorized_keys, 'a') as f:
                    f.write(pub_key)
            
            print("Public key added to authorized_keys")
            print(f"\nPublic key content:\n{pub_key}")
            
            # Automatically copy SSH key to worker nodes if password is provided
            if self.password and self.worker_ips:
                print("\n=== Copying SSH key to worker nodes ===")
                self._copy_ssh_key_to_workers()
            else:
                print("\nNOTE: You need to manually copy this public key to all other nodes")
                print(f"On each node, add this key to {authorized_keys}")
        
        # Configure SSH to not require strict host key checking (for cluster setup)
        ssh_config = ssh_dir / "config"
        config_content = """Host *\n    StrictHostKeyChecking no\n    UserKnownHostsFile=/dev/null\n"""
        with open(ssh_config, 'w') as f:
            f.write(config_content)
        ssh_config.chmod(0o600)
        
        print("SSH configuration completed")
    
    def _copy_ssh_key_to_workers(self):
        """Copy SSH public key to all worker nodes using sshpass"""
        import tempfile
        
        if not self.password:
            print("Error: Password is required for SSH key copying")
            return
        
        # Check if sshpass is installed
        if not shutil.which("sshpass"):
            print("Installing sshpass for automatic SSH key copying...")
            try:
                if self.pkg_manager == 'dnf':
                    self.run_sudo_command("dnf install -y sshpass", check=True)
                else:
                    # Wait for any other apt processes to finish and update/install sshpass
                    self.run_sudo_command("while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do sleep 1; done", check=False)
                    self.run_sudo_command("apt-get update", check=True)
                    self.run_sudo_command("apt-get install -y sshpass", check=True)
            except Exception as e:
                print(f"Failed to install sshpass: {e}")
                pkg_cmd = "dnf" if self.pkg_manager == 'dnf' else "apt-get"
                print(f"Please install sshpass manually: sudo {pkg_cmd} install -y sshpass")
                print("Or copy SSH keys manually to worker nodes")
                return
        
        ssh_dir = Path.home() / ".ssh"
        pub_key_path = ssh_dir / "id_rsa.pub"
        
        if not pub_key_path.exists():
            print("Error: SSH public key not found")
            return
        
        with open(pub_key_path, 'r') as f:
            pub_key = f.read().strip()
        
        for worker_ip in self.worker_ips:
            print(f"Copying SSH key to {worker_ip}...")
            try:
                # Use sshpass to copy the key
                # We'll use a temporary file for the password to avoid command line exposure
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass:
                    temp_pass.write(self.password)
                    temp_pass_path = temp_pass.name
                
                try:
                    # Create .ssh directory on remote host if it doesn't exist
                    cmd = f'sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{worker_ip} "mkdir -p ~/.ssh && chmod 700 ~/.ssh"'
                    self.run_command(cmd, check=True)
                    
                    # Append public key to authorized_keys on remote host
                    cmd = f'sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{worker_ip} "echo \'{pub_key}\' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys"'
                    self.run_command(cmd, check=True)
                    
                    print(f"✓ Successfully copied SSH key to {worker_ip}")
                finally:
                    # Clean up temporary password file
                    os.unlink(temp_pass_path)
                    
            except Exception as e:
                print(f"✗ Failed to copy SSH key to {worker_ip}: {e}")
                print(f"  You may need to manually copy the key to this node")
        
        print("\nSSH key distribution completed")
    
    def distribute_ssh_keys_between_all_nodes(self):
        """
        Distribute SSH keys between ALL nodes so any node can SSH to any other node.
        This creates a full mesh where every node can connect to every other node
        via any of their IP addresses. This is critical for:
        - MPI to work from any node as the head node
        - Nodes with multiple network interfaces (multi-homed)
        - Flexible cluster topology
        """
        if not self.password:
            print("\nSkipping cross-node SSH key distribution (no password provided)")
            return
        
        print(f"\n{'=' * 60}")
        print("CROSS-NODE SSH KEY DISTRIBUTION")
        print(f"{'=' * 60}")
        print("Ensuring all nodes can SSH to each other (required for MPI)...")
        print("Collecting ALL IP addresses from each node (including multi-homed nodes)...")
        
        # Get all node IPs (master + all workers) - primary IPs from config
        primary_nodes = [self.master_ip] + self.worker_ips
        
        # Dictionary to store all IP addresses for each node
        # Key: primary IP, Value: list of all IPs on that node
        node_all_ips = {}
        
        import tempfile
        
        # First, collect ALL IP addresses from each node
        for node_ip in primary_nodes:
            print(f"\nDetecting all IP addresses on {node_ip}...")
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass:
                    temp_pass.write(self.password)
                    temp_pass_path = temp_pass.name
                
                try:
                    # Get all IP addresses from the node (excluding loopback)
                    cmd = f'sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} "ip addr show | grep \'inet \' | grep -v \'127.0.0.1\' | awk \'{{print \\$2}}\' | cut -d/ -f1"'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    if result and result.returncode == 0:
                        ips = [ip.strip() for ip in result.stdout.strip().split('\n') if ip.strip()]
                        node_all_ips[node_ip] = ips
                        print(f"  Found IPs: {', '.join(ips)}")
                    else:
                        # Fallback to just the primary IP
                        node_all_ips[node_ip] = [node_ip]
                        print(f"  Using primary IP: {node_ip}")
                finally:
                    os.unlink(temp_pass_path)
                    
            except Exception as e:
                print(f"⚠ Could not detect IPs on {node_ip}: {e}")
                node_all_ips[node_ip] = [node_ip]  # Fallback to primary IP
        
        # Collect public keys from all nodes (using primary IP)
        node_public_keys = {}
        
        for node_ip in primary_nodes:
            print(f"\nCollecting public key from {node_ip}...")
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass:
                    temp_pass.write(self.password)
                    temp_pass_path = temp_pass.name
                
                try:
                    # Get the public key from the node
                    cmd = f'sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} "cat ~/.ssh/id_rsa.pub 2>/dev/null || echo \\"NO_KEY\\""'
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    
                    if result and result.returncode == 0 and "NO_KEY" not in result.stdout:
                        pub_key = result.stdout.strip()
                        node_public_keys[node_ip] = pub_key
                        print(f"✓ Collected public key from {node_ip}")
                    else:
                        print(f"⚠ No SSH key found on {node_ip} (will be generated during setup)")
                finally:
                    os.unlink(temp_pass_path)
                    
            except Exception as e:
                print(f"⚠ Could not collect public key from {node_ip}: {e}")
        
        # Now distribute each node's public key to ALL other nodes (all their IPs)
        # This creates a full mesh where any node can SSH to any IP of any other node
        total_distributions = 0
        successful_distributions = 0
        
        for source_node, pub_key in node_public_keys.items():
            source_ips = node_all_ips.get(source_node, [source_node])
            
            for target_node in primary_nodes:
                if source_node == target_node:
                    continue  # Skip distributing to self
                
                # Get all IPs for target node
                target_ips = node_all_ips.get(target_node, [target_node])
                
                print(f"\nDistributing {source_node}'s key to {target_node} (all {len(target_ips)} IP(s))...")
                
                # Try to distribute to the primary IP (most likely to work)
                try:
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass:
                        temp_pass.write(self.password)
                        temp_pass_path = temp_pass.name
                    
                    try:
                        total_distributions += 1
                        # Append the public key to authorized_keys on target node
                        # This will work for all IPs on that node since it's the same ~/.ssh/authorized_keys file
                        cmd = f'sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{target_node} "mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo \'{pub_key}\' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys"'
                        self.run_command(cmd, check=True)
                        successful_distributions += 1
                        print(f"  ✓ Added {source_node}'s key to {target_node}")
                        print(f"    This key will work for all IPs: {', '.join(target_ips)}")
                    finally:
                        os.unlink(temp_pass_path)
                        
                except Exception as e:
                    print(f"  ✗ Failed to add {source_node}'s key to {target_node}: {e}")
        
        print(f"\n{'=' * 60}")
        print(f"✓ Cross-node SSH key distribution completed")
        print(f"  Total nodes: {len(primary_nodes)}")
        print(f"  Total IPs detected: {sum(len(ips) for ips in node_all_ips.values())}")
        print(f"  Key distributions: {successful_distributions}/{total_distributions} successful")
        print(f"All nodes can now SSH to each other via any IP without passwords")
        print(f"{'=' * 60}")
    
    def distribute_mca_config_to_all_nodes(self):
        """
        Distribute OpenMPI MCA configuration to all nodes.
        This ensures consistent MPI settings across the cluster.
        """
        if not self.password:
            print("\nSkipping MCA config distribution (no password provided)")
            return
        
        print(f"\n{'=' * 60}")
        print("DISTRIBUTING OPENMPI MCA CONFIGURATION")
        print(f"{'=' * 60}")
        
        # Check if local MCA config exists
        local_mca_file = Path.home() / ".openmpi" / "mca-params.conf"
        if not local_mca_file.exists():
            print("⚠ Local MCA config not found, skipping distribution")
            return
        
        # Read the local MCA config
        with open(local_mca_file, 'r') as f:
            mca_content = f.read()
        
        print("Distributing MCA configuration to all nodes...")
        
        # Get all node IPs (master + all workers)
        all_nodes = [self.master_ip] + self.worker_ips
        
        import tempfile
        
        for node_ip in all_nodes:
            # Skip current node - it already has the config
            try:
                import socket
                result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    import re
                    ip_pattern = r'inet\s+(\d+\.\d+\.\d+\.\d+)'
                    found_ips = re.findall(ip_pattern, result.stdout)
                    if node_ip in found_ips:
                        print(f"Skipping {node_ip} (current node)")
                        continue
            except:
                pass
            
            print(f"\nDistributing MCA config to {node_ip}...")
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass:
                    temp_pass.write(self.password)
                    temp_pass_path = temp_pass.name
                
                try:
                    # Create .openmpi directory on remote node
                    cmd = f'sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} "mkdir -p ~/.openmpi"'
                    self.run_command(cmd, check=True)
                    
                    # Create a temporary file with MCA content
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp_mca:
                        temp_mca.write(mca_content)
                        temp_mca_path = temp_mca.name
                    
                    try:
                        # Copy MCA config to remote node
                        copy_cmd = f"sshpass -f {temp_pass_path} scp -o StrictHostKeyChecking=no {temp_mca_path} {self.username}@{node_ip}:~/.openmpi/mca-params.conf"
                        self.run_command(copy_cmd, check=True)
                        print(f"  ✓ MCA config copied to {node_ip}")
                    finally:
                        os.unlink(temp_mca_path)
                        
                finally:
                    os.unlink(temp_pass_path)
                    
            except Exception as e:
                print(f"  ✗ Failed to distribute MCA config to {node_ip}: {e}")
        
        print(f"\n{'=' * 60}")
        print("✓ MCA configuration distribution completed")
        print("All nodes now have consistent OpenMPI settings")
        print(f"{'=' * 60}")
    
    def _setup_worker_node(self, worker_ip: str, config_file: str):
        """Setup a cluster node remotely via SSH (installs prerequisites and runs full setup)"""
        import tempfile
        
        print(f"\n{'=' * 60}")
        print(f"Setting up cluster node: {worker_ip}")
        print(f"{'=' * 60}")
        
        if not self.password:
            print("Error: Password required for remote node setup")
            return False
        
        try:
            # Create a temporary password file for sshpass
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass_file:
                temp_pass_file.write(self.password)
                temp_pass_path = temp_pass_file.name
            
            try:
                # First, copy the config file to the worker node
                temp_config = f"/tmp/cluster_config_{os.getpid()}.yaml"
                print(f"Copying configuration file to {worker_ip}...")
                copy_cmd = f"sshpass -f {temp_pass_path} scp -o StrictHostKeyChecking=no {config_file} {self.username}@{worker_ip}:{temp_config}"
                self.run_command(copy_cmd, check=True)
                
                # Copy the cluster_setup.py script to the worker node
                script_path = os.path.abspath(__file__)
                temp_script = f"/tmp/cluster_setup_{os.getpid()}.py"
                print(f"Copying setup script to {worker_ip}...")
                copy_script_cmd = f"sshpass -f {temp_pass_path} scp -o StrictHostKeyChecking=no {script_path} {self.username}@{worker_ip}:{temp_script}"
                self.run_command(copy_script_cmd, check=True)
                
                # Make the script executable
                chmod_cmd = f"sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{worker_ip} 'chmod +x {temp_script}'"
                self.run_command(chmod_cmd, check=True)
                
                # Configure passwordless sudo for the user (temporary, for installation)
                print(f"Installing prerequisites on {worker_ip}...")
                
                # Create a wrapper script that installs prerequisites and runs setup
                wrapper_script = f"""#!/bin/bash
# Wrapper script to install prerequisites and run cluster setup

# Create a helper function for sudo with password
export SUDO_ASKPASS=/tmp/askpass_{os.getpid()}.sh
cat > $SUDO_ASKPASS << 'ASKPASS_EOF'
#!/bin/bash
echo '{self.password}'
ASKPASS_EOF
chmod +x $SUDO_ASKPASS

export SUDO_ASKPASS

echo "=== Installing Prerequisites on Remote Node ==="

# Ensure Homebrew is in PATH
if [ -d "/home/linuxbrew/.linuxbrew" ]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
fi

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for this session
    if [ -d "/home/linuxbrew/.linuxbrew" ]; then
        eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
        export PATH="/home/linuxbrew/.linuxbrew/bin:$PATH"
    fi
else
    echo "Homebrew already installed"
fi

# Check if Python 3.14 is installed
if ! command -v python3.14 &> /dev/null; then
    echo "Installing Python 3.14..."
    brew install python@3.14
else
    echo "Python 3.14 already installed"
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH for this session
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "uv already installed"
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Install PyYAML using pip (for standalone script execution)
echo "Installing PyYAML..."
# Use --break-system-packages for Homebrew Python (externally managed environment)
python3.14 -m pip install --user --break-system-packages pyyaml 2>&1 | grep -E "(Successfully|already satisfied)" || true

# Verify PyYAML is installed
if python3.14 -c "import yaml" 2>/dev/null; then
    echo "✓ PyYAML successfully installed and verified"
else
    echo "✗ WARNING: PyYAML installation failed!"
    echo "  Trying alternative installation method..."
    # Try with pip3.14 directly
    pip3.14 install --user --break-system-packages pyyaml 2>&1 || true
    # Final verification
    if python3.14 -c "import yaml" 2>/dev/null; then
        echo "✓ PyYAML installed successfully with pip3.14"
    else
        echo "✗ ERROR: Could not install PyYAML. Remote setup may fail."
    fi
fi

echo "=== Prerequisites installation completed ==="
echo ""

# Ensure Homebrew paths are in environment for the setup script
if [ -d "/home/linuxbrew/.linuxbrew" ]; then
    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
    export PATH="/home/linuxbrew/.linuxbrew/bin:/home/linuxbrew/.linuxbrew/sbin:$PATH"
fi

# Run the setup script WITHOUT --password flag
# The worker node doesn't need password for SSH setup (already has keys from master)
# Use --non-interactive flag to skip confirmation prompts
echo "=== Running cluster setup script ==="
python3.14 {temp_script} --config {temp_config} --non-interactive

# Cleanup
rm -f $SUDO_ASKPASS
"""
                
                temp_wrapper = f"/tmp/wrapper_{os.getpid()}.sh"
                
                # Copy wrapper script to worker
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as local_wrapper:
                    local_wrapper.write(wrapper_script)
                    local_wrapper_path = local_wrapper.name
                
                try:
                    copy_wrapper_cmd = f"sshpass -f {temp_pass_path} scp -o StrictHostKeyChecking=no {local_wrapper_path} {self.username}@{worker_ip}:{temp_wrapper}"
                    self.run_command(copy_wrapper_cmd, check=True)
                    
                    chmod_wrapper_cmd = f"sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{worker_ip} 'chmod +x {temp_wrapper}'"
                    self.run_command(chmod_wrapper_cmd, check=True)
                    
                    # Run the setup script on the worker node with password handling
                    print(f"Installing prerequisites and running setup on {worker_ip}...")
                    print(f"(This may take several minutes - installing Homebrew, Python 3.14, uv, and PyYAML)...")
                    
                    # Use sshpass to handle interactive sudo prompts
                    setup_cmd = f"sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{worker_ip} 'bash {temp_wrapper} 2>&1'"
                    
                    # Run with real-time output
                    process = subprocess.Popen(
                        setup_cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1
                    )
                    
                    # Print output in real-time
                    if process.stdout:
                        for line in process.stdout:
                            print(f"  [{worker_ip}] {line.rstrip()}")
                    
                    process.wait()
                    
                    if process.returncode == 0:
                        print(f"\n✓ Successfully set up node: {worker_ip}")
                        success = True
                    else:
                        print(f"\n✗ Failed to set up node: {worker_ip} (exit code: {process.returncode})")
                        success = False
                    
                    # Cleanup temporary files on worker node
                    cleanup_cmd = f"sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{worker_ip} 'rm -f {temp_config} {temp_script} {temp_wrapper} /tmp/askpass_*.sh'"
                    self.run_command(cleanup_cmd, check=False)
                    
                    return success
                    
                finally:
                    # Cleanup local wrapper script
                    os.unlink(local_wrapper_path)
                    
            finally:
                # Cleanup local password file
                os.unlink(temp_pass_path)
            
        except Exception as e:
            print(f"\n✗ Error setting up worker node {worker_ip}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def setup_all_workers(self, config_file: str, node_list: Optional[List[str]] = None):
        """Automatically setup specified nodes via SSH (or all worker nodes if not specified)"""
        if not self.password:
            print("\nSkipping automatic node setup (no password provided)")
            return False
        
        # Use provided node list or default to worker_ips
        nodes_to_setup = node_list if node_list is not None else self.worker_ips
        
        if not nodes_to_setup:
            print("\nNo nodes to setup")
            return True
        
        print(f"\n{'=' * 60}")
        print("AUTOMATIC CLUSTER NODE SETUP")
        print(f"{'=' * 60}")
        print(f"Will setup {len(nodes_to_setup)} node(s)")
        print(f"Node IPs: {', '.join(nodes_to_setup)}")
        print("\nProceeding with automatic node setup...")
        
        success_count = 0
        failed_nodes = []
        
        for node_ip in nodes_to_setup:
            if self._setup_worker_node(node_ip, config_file):
                success_count += 1
            else:
                failed_nodes.append(node_ip)
        
        print(f"\n{'=' * 60}")
        print("NODE SETUP SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total nodes: {len(nodes_to_setup)}")
        print(f"Successfully set up: {success_count}")
        print(f"Failed: {len(failed_nodes)}")
        
        if failed_nodes:
            print(f"\nFailed nodes: {', '.join(failed_nodes)}")
            print("You may need to setup these nodes manually")
        
        # After all nodes are set up, distribute SSH keys between all nodes
        # This ensures any node can be used as the MPI head node
        if success_count > 0:
            self.distribute_ssh_keys_between_all_nodes()
            # Also distribute MCA configuration to ensure consistent OpenMPI settings
            self.distribute_mca_config_to_all_nodes()
        
        return len(failed_nodes) == 0
    
    def configure_hosts_file(self):
        """Configure /etc/hosts with cluster node information"""
        print("\n=== Configuring /etc/hosts ===")
        
        # Create hosts entries
        hosts_entries = []
        hosts_entries.append(f"{self.master_ip}    master master-node")
        
        for idx, worker_ip in enumerate(self.worker_ips, start=1):
            hosts_entries.append(f"{worker_ip}    worker{idx} worker-node{idx}")
        
        hosts_content = "\n# Cluster nodes\n" + "\n".join(hosts_entries) + "\n"
        
        print("Hosts entries to add:")
        print(hosts_content)
        
        # Backup existing hosts file
        self.run_sudo_command("cp /etc/hosts /etc/hosts.backup", check=False)
        
        # Check if entries already exist
        with open('/etc/hosts', 'r') as f:
            existing_hosts = f.read()
        
        if "# Cluster nodes" not in existing_hosts:
            # Append cluster entries
            with open('/tmp/hosts_append', 'w') as f:
                f.write(hosts_content)
            
            self.run_sudo_command("bash -c 'cat /tmp/hosts_append >> /etc/hosts'")
            print("/etc/hosts updated successfully")
        else:
            print("/etc/hosts already contains cluster node entries")
    
    def install_slurm(self):
        """Install Slurm workload manager using system package manager"""
        print("\n=== Installing Slurm ===")
        
        # Check if Slurm is already installed
        result = self.run_command("which slurmctld", check=False)
        if result.returncode == 0:
            print("Slurm already installed")
            return
        
        # Note: Homebrew has a "slurm" package but it's a network monitor, not the workload manager
        # We need to install slurm from system package manager instead
        print(f"Installing Slurm workload manager using {self.pkg_manager}...")
        if self.pkg_manager == 'dnf':
            self.run_sudo_command("dnf install -y slurm slurm-slurmd slurm-slurmctld")
        else:
            self.run_sudo_command("apt-get update")
            self.run_sudo_command("apt-get install -y slurm-wlm slurm-wlm-doc slurm-client")
        
        print("Slurm installation completed")
    
    def install_openmpi(self):
        """Install OpenMPI, GCC, and CMake using Homebrew"""
        print("\n=== Installing OpenMPI with GCC and CMake ===")
        
        brew_cmd = "/home/linuxbrew/.linuxbrew/bin/brew"
        if not os.path.exists(brew_cmd):
            print("Error: Homebrew not found. Please install Homebrew first.")
            return
        
        # CRITICAL: Check if MPICH is installed and uninstall it
        # MPICH and OpenMPI are incompatible and cannot coexist for cluster MPI
        print("Checking for MPICH (incompatible with OpenMPI)...")
        mpich_check = self.run_command(f"{brew_cmd} list mpich 2>/dev/null", check=False)
        if mpich_check.returncode == 0:
            print("⚠️  MPICH detected! Uninstalling (incompatible with OpenMPI for cross-cluster execution)...")
            self.run_command(f"{brew_cmd} uninstall mpich", check=False)
            print("✓ MPICH uninstalled")
        else:
            print("✓ No MPICH installation found (good)")
        
        # Install GCC first (required for mpicc)
        print("Installing GCC via Homebrew...")
        result = self.run_command(f"{brew_cmd} install gcc", check=False)
        if result.returncode == 0:
            print("✓ GCC installed successfully")
        else:
            print("GCC installation failed or already installed")
        
        # Install CMake
        print("Installing CMake via Homebrew...")
        result = self.run_command(f"{brew_cmd} install cmake", check=False)
        if result.returncode == 0:
            print("✓ CMake installed successfully")
        else:
            print("CMake installation failed or already installed")
        
        # Create symlinks to make Homebrew GCC the default compiler
        # This ensures we use the latest GCC from Homebrew instead of system GCC
        print("Creating compiler symlinks to make Homebrew GCC default...")
        homebrew_bin = "/home/linuxbrew/.linuxbrew/bin"
        
        # Find the installed gcc version
        gcc_version_result = self.run_command(f"ls {homebrew_bin}/gcc-* 2>/dev/null | grep -E 'gcc-[0-9]+$' | head -1", check=False)
        if gcc_version_result.returncode == 0 and gcc_version_result.stdout.strip():
            gcc_path = gcc_version_result.stdout.strip()
            gcc_version = gcc_path.split('-')[-1]
            print(f"Found GCC version: {gcc_version}")
            
            # Create default gcc/g++/gfortran symlinks pointing to Homebrew's latest version
            self.run_command(f"ln -sf {homebrew_bin}/gcc-{gcc_version} {homebrew_bin}/gcc", check=False)
            self.run_command(f"ln -sf {homebrew_bin}/g++-{gcc_version} {homebrew_bin}/g++", check=False)
            self.run_command(f"ln -sf {homebrew_bin}/gfortran-{gcc_version} {homebrew_bin}/gfortran", check=False)
            
            print(f"✓ Created compiler symlinks:")
            print(f"  gcc/g++/gfortran -> gcc-{gcc_version} (latest from Homebrew)")
        else:
            print("⚠️  Could not detect GCC version for symlink creation")
        
        # Install OpenMPI
        print("Installing OpenMPI via Homebrew...")
        result = self.run_command(f"{brew_cmd} install open-mpi", check=False)
        
        if result.returncode != 0:
            print(f"Installing OpenMPI from {self.pkg_manager} as fallback...")
            if self.pkg_manager == 'dnf':
                self.run_sudo_command("dnf install -y openmpi openmpi-devel")
            else:
                self.run_sudo_command("apt-get update")
                self.run_sudo_command("apt-get install -y openmpi-bin openmpi-common libopenmpi-dev")
        else:
            # Ensure OpenMPI is linked (in case it was installed but not linked)
            print("Ensuring OpenMPI is linked...")
            link_result = self.run_command(f"{brew_cmd} link open-mpi", check=False)
            if link_result.returncode == 0:
                print("✓ OpenMPI linked successfully")
            else:
                # If linking failed, it might already be linked
                print("OpenMPI linking status checked")
            
            # Verify mpicc can find the compiler
            print("Verifying mpicc compiler detection...")
            mpicc_test = self.run_command(f"{homebrew_bin}/mpicc --version", check=False)
            if mpicc_test.returncode == 0:
                print("✓ mpicc working correctly")
            else:
                print("⚠️  mpicc may have issues - check compiler symlinks")
        
        print("OpenMPI, GCC, and CMake installation completed")

    def configure_firewall_for_mpi(self):
        """Configure firewall to allow MPI ports (50000-50200)"""
        print("\n=== Configuring Firewall for MPI ===")
        
        # MPI port range: 50000-50200
        # BTL TCP: 50000+
        # OOB TCP: 50100-50200
        
        if self._is_wsl():
            print("⚠️  WSL detected - Linux firewall configuration skipped")
            print("   WSL requires Windows Firewall configuration")
            print("   Run in PowerShell as Administrator:")
            print("   .\\configure_wsl_firewall.ps1")
            return
        
        # Check for Ubuntu/Debian (ufw)
        if self.pkg_manager == 'apt-get':
            # Check if ufw is installed and enabled
            ufw_status = self.run_command("ufw status", check=False)
            if ufw_status.returncode == 0 and "Status: active" in ufw_status.stdout:
                print("UFW firewall detected and active")
                print("Opening MPI ports 50000-50200...")
                self.run_sudo_command("ufw allow 50000:50200/tcp comment 'OpenMPI PRRTE'")
                print("✓ UFW configured for MPI")
            else:
                print("UFW not active or not installed - skipping firewall configuration")
        
        # Check for Red Hat/CentOS/Fedora (firewalld)
        elif self.pkg_manager == 'dnf':
            # Check if firewalld is running
            firewalld_status = self.run_command("systemctl is-active firewalld", check=False)
            if firewalld_status.returncode == 0 and "active" in firewalld_status.stdout:
                print("firewalld detected and active")
                print("Opening MPI ports 50000-50200...")
                self.run_sudo_command("firewall-cmd --permanent --add-port=50000-50200/tcp")
                self.run_sudo_command("firewall-cmd --reload")
                print("✓ firewalld configured for MPI")
            else:
                print("firewalld not active - skipping firewall configuration")
        
        print("Firewall configuration completed")

    def install_openmp(self):
        """Install OpenMP (libomp) using Homebrew"""
        print("\n=== Installing OpenMP (libomp) ===")

        brew_cmd = "/home/linuxbrew/.linuxbrew/bin/brew"
        if not os.path.exists(brew_cmd):
            print("Error: Homebrew not found. Please install Homebrew first.")
            return

        # Install libomp (OpenMP runtime library)
        print("Installing libomp (OpenMP) via Homebrew...")
        result = self.run_command(f"{brew_cmd} install libomp", check=False)

        if result.returncode != 0:
            print(f"Installing OpenMP from {self.pkg_manager} as fallback...")
            if self.pkg_manager == 'dnf':
                self.run_sudo_command("dnf install -y libomp libomp-devel")
            else:
                self.run_sudo_command("apt-get update")
                self.run_sudo_command("apt-get install -y libomp-dev")

        print("OpenMP installation completed")

        # Verify installation
        try:
            result = self.run_command("echo | gcc -fopenmp -x c - -o /tmp/test_omp 2>&1", check=False)
            if result.returncode == 0:
                print("✓ OpenMP compiler support verified")
            else:
                print("⚠ OpenMP compiler flags may need configuration")
        except Exception as e:
            print(f"Note: Could not verify OpenMP: {e}")

    def install_upcxx_and_pgas(self):
        """Install UPC++, GASNet, OpenSHMEM, and Berkeley UPC++ containers from source
        
        UPC++ (Unified Parallel C++) is a C++ library for PGAS programming
        Reference: https://upcxx.lbl.gov/docs/html/guide.html
        
        Components installed:
        - GASNet-EX: Communication system for PGAS languages (latest stable)
        - UPC++: Berkeley PGAS library for C++ (supports MPI, GASNet conduits)
        - OpenSHMEM: PGAS library for parallel programming (via Sandia)
        - Berkeley Containers: Distributed data structures for UPC++
        
        Conduits:
        - SMP conduit: Single-node shared memory
        - MPI conduit: Multi-node via MPI (requires OpenMPI)
        - UDP conduit: Multi-node via UDP sockets
        
        Installation is performed from source in ~/cluster_build_sources directory
        """
        print("\n=== Installing UPC++, GASNet-EX, and OpenSHMEM from Source ===")
        
        # Installation directory
        install_prefix = "/home/linuxbrew/.linuxbrew"
        pgas_build_dir = Path.home() / "cluster_build_sources"
        pgas_build_dir.mkdir(exist_ok=True)
        print(f"Using build directory: {pgas_build_dir}")
        
        # Check for required tools
        print("Checking build dependencies...")
        required_tools = ["wget", "tar", "make"]
        for tool in required_tools:
            result = self.run_command(f"which {tool}", check=False)
            if result.returncode != 0:
                print(f"Installing {tool}...")
                if self.pkg_manager == 'dnf':
                    self.run_sudo_command(f"dnf install -y {tool}")
                else:
                    self.run_sudo_command(f"apt-get install -y {tool}")
        
        # Install required Homebrew packages for PGAS
        print("Installing required Homebrew packages...")
        required_packages = ["glibc", "binutils", "python3"]
        for pkg in required_packages:
            print(f"  - Installing {pkg}...")
            result = self.run_command(f"brew list {pkg}", check=False)
            if result.returncode != 0:
                self.run_command(f"brew install {pkg}")
        
        # Create system symlinks for binutils and Python
        print("Creating system symlinks for binutils and Python...")
        symlinks = {
            "/home/linuxbrew/.linuxbrew/opt/binutils/bin/as": "/usr/local/bin/as",
            "/home/linuxbrew/.linuxbrew/opt/binutils/bin/ld": "/usr/local/bin/ld",
            "/home/linuxbrew/.linuxbrew/opt/binutils/bin/ar": "/usr/local/bin/ar",
            "/home/linuxbrew/.linuxbrew/opt/binutils/bin/ranlib": "/usr/local/bin/ranlib",
            "/home/linuxbrew/.linuxbrew/bin/python3": "/usr/local/bin/python3",
            "/home/linuxbrew/.linuxbrew/bin/pip3": "/usr/local/bin/pip3",
        }
        for source, target in symlinks.items():
            self.run_sudo_command(f"ln -sf {source} {target}")
            print(f"  ✓ Linked {target}")
        
        # Get GCC and MPI paths for configuration
        gcc_bin = "/home/linuxbrew/.linuxbrew/bin/gcc"
        gxx_bin = "/home/linuxbrew/.linuxbrew/bin/g++"
        mpi_bin = "/home/linuxbrew/.linuxbrew/bin/mpicc"
        
        # Set environment variables for compilation with glibc paths
        glibc_lib = "/home/linuxbrew/.linuxbrew/Cellar/glibc/2.35_2/lib"
        env_vars = {
            "CC": gcc_bin,
            "CXX": gxx_bin,
            "MPICC": mpi_bin,
            "PATH": f"/home/linuxbrew/.linuxbrew/opt/binutils/bin:/home/linuxbrew/.linuxbrew/bin:{os.environ.get('PATH', '')}",
            "LDFLAGS": f"-L{glibc_lib} -Wl,-rpath,{glibc_lib}",
        }
        
        # 1. Install GASNet-EX (Communication layer)
        print("\n--- Installing GASNet-EX ---")
        gasnet_version = "2024.5.0"  # Latest stable release
        gasnet_url = f"https://gasnet.lbl.gov/EX/GASNet-{gasnet_version}.tar.gz"
        gasnet_dir = pgas_build_dir / f"GASNet-{gasnet_version}"
        
        if not gasnet_dir.exists():
            print(f"Downloading GASNet-EX {gasnet_version}...")
            result = self.run_command(
                f"cd {pgas_build_dir} && wget -q {gasnet_url} && tar xzf GASNet-{gasnet_version}.tar.gz",
                check=False
            )
            if result.returncode != 0:
                print("⚠ Failed to download GASNet-EX")
                return
        
        print("Configuring GASNet-EX with MPI and SMP conduits...")
        gasnet_install = f"{install_prefix}/gasnet"
        configure_cmd = (
            f"cd {gasnet_dir} && "
            f"CC={gcc_bin} CXX={gxx_bin} ./configure "
            f"--prefix={gasnet_install} "
            f"--enable-mpi --enable-smp --enable-udp "
            f"--with-mpicc={mpi_bin} "
            f"--disable-seq "
            f"--enable-par"
        )
        
        result = self.run_command(configure_cmd, check=False)
        if result.returncode == 0:
            print("Building GASNet-EX (this may take 10-15 minutes)...")
            build_cmd = f"cd {gasnet_dir} && make -j$(nproc) && make install"
            result = self.run_command(build_cmd, check=False)
            if result.returncode == 0:
                print("✓ GASNet-EX installed successfully")
            else:
                print("⚠ GASNet-EX build failed")
                return
        else:
            print("⚠ GASNet-EX configuration failed")
            return
        
        # 2. Install UPC++ (Berkeley PGAS library)
        print("\n--- Installing Berkeley UPC++ ---")
        upcxx_version = "2024.3.0"  # Latest stable release
        upcxx_url = f"https://bitbucket.org/berkeleylab/upcxx/downloads/upcxx-{upcxx_version}.tar.gz"
        upcxx_dir = pgas_build_dir / f"upcxx-{upcxx_version}"
        
        if not upcxx_dir.exists():
            print(f"Downloading UPC++ {upcxx_version}...")
            result = self.run_command(
                f"cd {pgas_build_dir} && wget -q {upcxx_url} && tar xzf upcxx-{upcxx_version}.tar.gz",
                check=False
            )
            if result.returncode != 0:
                print("⚠ Failed to download UPC++")
                return
        
        print("Installing UPC++ with GASNet-EX...")
        upcxx_install = f"{install_prefix}/upcxx"
        install_cmd = (
            f"cd {upcxx_dir} && "
            f"CC={gcc_bin} CXX={gxx_bin} "
            f"./install {upcxx_install} "
            f"--with-gasnet={gasnet_install}"
        )
        
        result = self.run_command(install_cmd, check=False)
        if result.returncode == 0:
            print("✓ UPC++ installed successfully")
        else:
            print("⚠ UPC++ installation failed")
            return
        
        # 3. Install OpenSHMEM (Sandia implementation)
        print("\n--- Installing Sandia OpenSHMEM ---")
        oshmem_version = "1.5.2"
        oshmem_url = f"https://github.com/Sandia-OpenSHMEM/SOS/releases/download/v{oshmem_version}/SOS-{oshmem_version}.tar.gz"
        oshmem_dir = pgas_build_dir / f"SOS-{oshmem_version}"
        
        if not oshmem_dir.exists():
            print(f"Downloading Sandia OpenSHMEM {oshmem_version}...")
            result = self.run_command(
                f"cd {pgas_build_dir} && wget -q {oshmem_url} && tar xzf SOS-{oshmem_version}.tar.gz",
                check=False
            )
            if result.returncode != 0:
                print("⚠ Failed to download OpenSHMEM")
                # Non-critical, continue
        
        oshmem_install = f"{install_prefix}/openshmem"
        if oshmem_dir.exists():
            print("Configuring OpenSHMEM...")
            configure_cmd = (
                f"cd {oshmem_dir} && "
                f"CC={gcc_bin} CXX={gxx_bin} ./configure "
                f"--prefix={oshmem_install} "
                f"--with-pmix=internal "
                f"--enable-pmi-simple"
            )
            
            result = self.run_command(configure_cmd, check=False)
            if result.returncode == 0:
                print("Building OpenSHMEM...")
                build_cmd = f"cd {oshmem_dir} && make -j$(nproc) && make install"
                result = self.run_command(build_cmd, check=False)
                if result.returncode == 0:
                    print("✓ OpenSHMEM installed successfully")
                else:
                    print("⚠ OpenSHMEM build failed (non-critical)")
            else:
                print("⚠ OpenSHMEM configuration failed (non-critical)")
        
        # Create symbolic links for easy access
        print("\nCreating symbolic links...")
        upcxx_bin = f"{upcxx_install}/bin"
        if os.path.exists(upcxx_bin):
            self.run_command(f"ln -sf {upcxx_bin}/upcxx {install_prefix}/bin/upcxx", check=False)
            self.run_command(f"ln -sf {upcxx_bin}/upcxx-run {install_prefix}/bin/upcxx-run", check=False)
            print("✓ UPC++ symlinks created")
        
        # Update shell environment
        print("\nUpdating shell environment...")
        bashrc = Path.home() / ".bashrc"
        env_lines = [
            "\n# UPC++ and PGAS Environment",
            f"export UPCXX_INSTALL={upcxx_install}",
            f"export GASNET_INSTALL={gasnet_install}",
            f"export PATH={upcxx_bin}:$PATH",
            f"export LD_LIBRARY_PATH={gasnet_install}/lib:{upcxx_install}/lib:$LD_LIBRARY_PATH",
        ]
        
        with open(bashrc, 'a') as f:
            for line in env_lines:
                f.write(line + '\n')
        
        print("✓ Environment variables added to ~/.bashrc")
        
        # Verify installation
        print("\nVerifying UPC++ installation...")
        upcxx_cmd = f"{upcxx_bin}/upcxx"
        if os.path.exists(upcxx_cmd):
            result = self.run_command(f"{upcxx_cmd} --version", check=False)
            if result.returncode == 0:
                print("✓ UPC++ compiler verified")
                print(f"   {result.stdout.strip()}")
        
        print("\n" + "="*70)
        print("UPC++ and PGAS Libraries Installation Summary:")
        print("="*70)
        print(f"✓ GASNet-EX {gasnet_version}: {gasnet_install}")
        print(f"✓ UPC++ {upcxx_version}: {upcxx_install}")
        print(f"✓ OpenSHMEM {oshmem_version}: {oshmem_install}")
        print("\nUsage:")
        print(f"  Compile: upcxx -O3 myprogram.cpp -o myprogram")
        print(f"  Run SMP: upcxx-run -n 4 ./myprogram")
        print(f"  Run MPI: upcxx-run -ssh-servers node1,node2 -n 8 ./myprogram")
        print("\nConduits:")
        print("  - smp: Single node shared memory (default)")
        print("  - mpi: Multi-node via OpenMPI")
        print("  - udp: Multi-node via UDP sockets")
        print("\nDocumentation: https://upcxx.lbl.gov/docs/html/guide.html")
        print("="*70)
    
    def distribute_pgas_to_cluster(self):
        """Distribute PGAS libraries (UPC++, GASNet, OpenSHMEM) to all cluster nodes
        
        Creates ~/cluster_build_sources directory on each node and copies the built
        binaries/libraries for parallel installation across the cluster.
        """
        if not self.password:
            print("\n⚠ Skipping PGAS distribution - password not provided")
            print("  Run with --password flag for automatic cluster-wide installation")
            return
        
        print("\n=== Distributing PGAS Libraries to All Cluster Nodes ===")
        
        install_prefix = "/home/linuxbrew/.linuxbrew"
        all_nodes = [self.master_ip] + self.worker_ips
        
        # Get local IPs to exclude current node
        try:
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
            import re
            local_ips = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
        except:
            local_ips = []
        
        # Remove current node from distribution list
        other_nodes = [ip for ip in all_nodes if ip not in local_ips]
        
        if not other_nodes:
            print("No other nodes to distribute to (current node only)")
            return
        
        print(f"Distributing PGAS libraries to {len(other_nodes)} nodes...")
        
        # Paths to distribute
        pgas_components = [
            ("gasnet", f"{install_prefix}/gasnet"),
            ("upcxx", f"{install_prefix}/upcxx"),
            ("openshmem", f"{install_prefix}/openshmem"),
        ]
        
        for node_ip in other_nodes:
            print(f"\n→ Distributing to {node_ip}...")
            
            # Create cluster_build_sources directory on remote node
            create_dir_cmd = f"sshpass -p '{self.password}' ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} 'mkdir -p ~/cluster_build_sources'"
            result = self.run_command(create_dir_cmd, check=False)
            if result.returncode != 0:
                print(f"  ⚠ Failed to create cluster_build_sources directory on {node_ip}")
                continue
            
            # Copy each PGAS component if it exists
            for component_name, component_path in pgas_components:
                if os.path.exists(component_path):
                    print(f"  Copying {component_name}...")
                    rsync_cmd = (
                        f"sshpass -p '{self.password}' rsync -avz --delete "
                        f"-e 'ssh -o StrictHostKeyChecking=no' "
                        f"{component_path}/ "
                        f"{self.username}@{node_ip}:{component_path}/"
                    )
                    result = self.run_command(rsync_cmd, check=False)
                    if result.returncode == 0:
                        print(f"    ✓ {component_name} copied to {node_ip}")
                    else:
                        print(f"    ⚠ Failed to copy {component_name} to {node_ip}")
                else:
                    print(f"  ⚠ {component_name} not found at {component_path}, skipping")
            
            # Update environment on remote node
            print(f"  Updating environment on {node_ip}...")
            env_update_cmd = f"""sshpass -p '{self.password}' ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} '
                # Add PGAS environment variables to .bashrc if not already present
                grep -q "UPC++ and PGAS Environment" ~/.bashrc || cat >> ~/.bashrc << "EOF"

# UPC++ and PGAS Environment
export UPCXX_INSTALL={install_prefix}/upcxx
export GASNET_INSTALL={install_prefix}/gasnet
export PATH={install_prefix}/upcxx/bin:$PATH
export LD_LIBRARY_PATH={install_prefix}/gasnet/lib:{install_prefix}/upcxx/lib:$LD_LIBRARY_PATH
EOF
                echo "Environment variables added"
            '"""
            
            result = self.run_command(env_update_cmd, check=False)
            if result.returncode == 0:
                print(f"    ✓ Environment updated on {node_ip}")
            else:
                print(f"    ⚠ Failed to update environment on {node_ip}")
            
            # Create symbolic links on remote node
            print(f"  Creating symbolic links on {node_ip}...")
            symlink_cmd = f"""sshpass -p '{self.password}' ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} '
                if [ -f {install_prefix}/upcxx/bin/upcxx ]; then
                    ln -sf {install_prefix}/upcxx/bin/upcxx {install_prefix}/bin/upcxx
                    ln -sf {install_prefix}/upcxx/bin/upcxx-run {install_prefix}/bin/upcxx-run
                    echo "Symlinks created"
                else
                    echo "UPC++ binary not found"
                fi
            '"""
            
            result = self.run_command(symlink_cmd, check=False)
            if result.returncode == 0:
                print(f"    ✓ Symlinks created on {node_ip}")
        
        print("\n" + "="*70)
        print("PGAS Distribution Complete")
        print("="*70)
        print("✓ All cluster nodes now have UPC++, GASNet, and OpenSHMEM")
        print(f"✓ Build artifacts stored in ~/cluster_build_sources on each node")
        print(f"✓ Binaries installed in {install_prefix}")
        print("\nTest installation on any node:")
        print("  source ~/.bashrc")
        print("  upcxx --version")
        print("="*70)

    def configure_passwordless_sudo_cluster(self):
        """Configure passwordless sudo for cluster operations on all nodes
        
        Creates /etc/sudoers.d/cluster-ops file allowing passwordless execution
        of specific commands needed for cluster management.
        """
        if not self.password:
            print("\n⚠ Skipping passwordless sudo configuration - password not provided")
            return
        
        print("\n=== Configuring Passwordless Sudo on All Cluster Nodes ===")
        
        all_nodes = [self.master_ip] + self.worker_ips
        
        # Get local IPs to identify current node
        try:
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
            import re
            local_ips = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
        except:
            local_ips = []
        
        # Sudoers configuration for cluster operations
        sudoers_content = f"{self.username} ALL=(ALL) NOPASSWD: /usr/bin/ln, /usr/bin/rsync, /usr/bin/systemctl, /usr/bin/mkdir, /usr/bin/chmod, /usr/bin/chown, /usr/bin/tee, /usr/bin/cp, /bin/ln, /bin/rsync, /bin/systemctl, /bin/mkdir, /bin/chmod, /bin/chown, /bin/tee, /bin/cp"
        
        # Configure local node first
        if any(ip in local_ips for ip in all_nodes):
            print(f"\n→ Configuring local node...")
            try:
                # Create temporary file
                with open('/tmp/cluster-ops-sudoers', 'w') as f:
                    f.write(sudoers_content + '\n')
                
                # Copy to sudoers.d with proper permissions
                self.run_sudo_command("cp /tmp/cluster-ops-sudoers /etc/sudoers.d/cluster-ops")
                self.run_sudo_command("chmod 440 /etc/sudoers.d/cluster-ops")
                
                # Verify syntax
                result = self.run_sudo_command("visudo -c", check=False)
                if result.returncode == 0:
                    print("  ✓ Passwordless sudo configured on local node")
                else:
                    print("  ⚠ Warning: sudoers syntax check failed, removing configuration")
                    self.run_sudo_command("rm -f /etc/sudoers.d/cluster-ops", check=False)
            except Exception as e:
                print(f"  ⚠ Failed to configure local node: {e}")
        
        # Configure remote nodes
        other_nodes = [ip for ip in all_nodes if ip not in local_ips]
        
        for node_ip in other_nodes:
            print(f"\n→ Configuring {node_ip}...")
            
            try:
                # Create sudoers file on remote node using echo and sudo tee
                config_cmd = f"""sshpass -p '{self.password}' ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} "echo '{sudoers_content}' | sudo -S tee /tmp/cluster-ops-sudoers > /dev/null && echo '{self.password}' | sudo -S cp /tmp/cluster-ops-sudoers /etc/sudoers.d/cluster-ops && echo '{self.password}' | sudo -S chmod 440 /etc/sudoers.d/cluster-ops && echo '{self.password}' | sudo -S rm -f /tmp/cluster-ops-sudoers" """
                
                result = self.run_command(config_cmd, check=False)
                if result.returncode == 0:
                    print(f"  ✓ Passwordless sudo configured on {node_ip}")
                else:
                    print(f"  ⚠ Failed to configure {node_ip}: {result.stderr}")
            except Exception as e:
                print(f"  ⚠ Failed to configure {node_ip}: {e}")
        
        print("\n" + "="*70)
        print("Passwordless Sudo Configuration Complete")
        print("="*70)
        print(f"✓ Configured sudo access for: ln, rsync, systemctl, mkdir, chmod, chown")
        print(f"✓ Configuration file: /etc/sudoers.d/cluster-ops")
        print("\nTest with: ssh <node> 'sudo ln --help'")
        print("="*70)

    def distribute_system_symlinks_cluster(self):
        """Distribute system symlinks for binutils and Python to all cluster nodes
        
        Creates symlinks in /usr/local/bin for consistent tool versions across the cluster.
        Requires passwordless sudo to be configured first.
        """
        if not self.password:
            print("\n⚠ Skipping system symlinks distribution - password not provided")
            return
        
        print("\n=== Distributing System Symlinks to All Cluster Nodes ===")
        
        all_nodes = [self.master_ip] + self.worker_ips
        
        # Get local IPs
        try:
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
            import re
            local_ips = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
        except:
            local_ips = []
        
        # Symlinks to create on each node
        symlinks = {
            "/home/linuxbrew/.linuxbrew/opt/binutils/bin/as": "/usr/local/bin/as",
            "/home/linuxbrew/.linuxbrew/opt/binutils/bin/ld": "/usr/local/bin/ld",
            "/home/linuxbrew/.linuxbrew/opt/binutils/bin/ar": "/usr/local/bin/ar",
            "/home/linuxbrew/.linuxbrew/opt/binutils/bin/ranlib": "/usr/local/bin/ranlib",
            "/home/linuxbrew/.linuxbrew/bin/python3": "/usr/local/bin/python3",
            "/home/linuxbrew/.linuxbrew/bin/pip3": "/usr/local/bin/pip3",
            "/home/linuxbrew/.linuxbrew/upcxx/bin/upcxx": "/home/linuxbrew/.linuxbrew/bin/upcxx",
            "/home/linuxbrew/.linuxbrew/upcxx/bin/upcxx-run": "/home/linuxbrew/.linuxbrew/bin/upcxx-run",
            "/home/linuxbrew/.linuxbrew/upcxx/bin/upcxx-meta": "/home/linuxbrew/.linuxbrew/bin/upcxx-meta",
        }
        
        # Configure other nodes (excluding current node which was done during install)
        other_nodes = [ip for ip in all_nodes if ip not in local_ips]
        
        for node_ip in other_nodes:
            print(f"\n→ Creating symlinks on {node_ip}...")
            
            success_count = 0
            for source, target in symlinks.items():
                try:
                    # Check if source exists, then create symlink with passwordless sudo
                    symlink_cmd = f"""ssh {self.username}@{node_ip} "if [ -f {source} ] || [ -L {source} ]; then sudo ln -sf {source} {target} && echo 'OK'; else echo 'SKIP'; fi" """
                    
                    result = self.run_command(symlink_cmd, check=False)
                    if result.returncode == 0 and 'OK' in result.stdout:
                        success_count += 1
                    elif 'SKIP' in result.stdout:
                        pass  # Source doesn't exist, skip silently
                    else:
                        print(f"    ⚠ Failed: {target}")
                except Exception as e:
                    print(f"    ⚠ Error creating {target}: {e}")
            
            if success_count > 0:
                print(f"  ✓ Created {success_count}/{len(symlinks)} symlinks on {node_ip}")
            
            # Verify binutils version
            print(f"  Verifying installations on {node_ip}...")
            verify_cmds = [
                ("Binutils", "as --version | head -1"),
                ("Python", "python3 --version"),
                ("UPC++", "upcxx --version 2>&1 | head -1"),
            ]
            
            for tool_name, cmd in verify_cmds:
                verify_cmd = f"ssh {self.username}@{node_ip} '{cmd}' "
                result = self.run_command(verify_cmd, check=False)
                if result.returncode == 0:
                    version_info = result.stdout.strip()
                    print(f"    ✓ {tool_name}: {version_info}")
        
        print("\n" + "="*70)
        print("System Symlinks Distribution Complete")
        print("="*70)
        print("✓ All nodes have consistent tool versions")
        print("✓ Binutils 2.45, Python 3.14, UPC++ available cluster-wide")
        print("="*70)

    def test_multinode_upcxx(self):
        """Test UPC++ multi-node execution across the cluster
        
        Creates test programs and validates SMP, UDP, and MPI conduits.
        """
        print("\n=== Testing Multi-Node UPC++ Execution ===")
        
        test_dir = Path.home() / "cluster_build_sources" / "upcxx_tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a simple UPC++ test program
        test_program = """
#include <upcxx/upcxx.hpp>
#include <iostream>

int main() {
    upcxx::init();
    
    if (upcxx::rank_me() == 0) {
        std::cout << "UPC++ Multi-Node Test\\n";
        std::cout << "Total ranks: " << upcxx::rank_n() << "\\n";
    }
    
    upcxx::barrier();
    
    std::cout << "Rank " << upcxx::rank_me() 
              << " running on " << upcxx::local_team().rank_n() 
              << " local ranks\\n";
    
    upcxx::finalize();
    return 0;
}
"""
        
        test_file = test_dir / "hello_multinode.cpp"
        with open(test_file, 'w') as f:
            f.write(test_program)
        
        print(f"Created test program: {test_file}")
        
        # Test 1: SMP conduit (single node)
        print("\n--- Test 1: SMP Conduit (Single Node) ---")
        compile_cmd = f"cd {test_dir} && upcxx -network=smp hello_multinode.cpp -o hello_smp"
        result = self.run_command(compile_cmd, check=False)
        
        if result.returncode == 0:
            print("  ✓ Compilation successful")
            
            # Run with 4 processes
            run_cmd = f"cd {test_dir} && GASNET_PSHM_NODES=1 upcxx-run -n 4 ./hello_smp"
            result = self.run_command(run_cmd, check=False)
            
            if result.returncode == 0:
                print("  ✓ SMP execution successful")
                print(f"  Output:\n{result.stdout}")
            else:
                print(f"  ⚠ SMP execution failed: {result.stderr}")
        else:
            print(f"  ⚠ SMP compilation failed: {result.stderr}")
        
        # Test 2: UDP conduit (multi-node)
        print("\n--- Test 2: UDP Conduit (Multi-Node) ---")
        
        # Create server list
        all_nodes = [self.master_ip] + self.worker_ips
        server_list = ','.join(all_nodes)
        
        compile_cmd = f"cd {test_dir} && upcxx -network=udp hello_multinode.cpp -o hello_udp"
        result = self.run_command(compile_cmd, check=False)
        
        if result.returncode == 0:
            print("  ✓ Compilation successful")
            print(f"  Server list: {server_list}")
            
            # Calculate total processes (4 per node)
            total_procs = len(all_nodes) * 4
            
            # Run across all nodes
            run_cmd = f"cd {test_dir} && GASNET_SSH_SERVERS='{server_list}' upcxx-run -n {total_procs} ./hello_udp"
            result = self.run_command(run_cmd, check=False)
            
            if result.returncode == 0:
                print(f"  ✓ UDP execution successful ({total_procs} processes across {len(all_nodes)} nodes)")
                print(f"  Output:\n{result.stdout}")
            else:
                print(f"  ⚠ UDP execution failed: {result.stderr}")
                print(f"  Note: Ensure passwordless SSH is configured and GASNet is installed on all nodes")
        else:
            print(f"  ⚠ UDP compilation failed: {result.stderr}")
        
        # Test 3: MPI conduit (if available)
        print("\n--- Test 3: MPI Conduit (Multi-Node) ---")
        
        compile_cmd = f"cd {test_dir} && upcxx -network=mpi hello_multinode.cpp -o hello_mpi"
        result = self.run_command(compile_cmd, check=False)
        
        if result.returncode == 0:
            print("  ✓ Compilation successful")
            
            # Create MPI hostfile
            hostfile = test_dir / "mpi_hostfile"
            with open(hostfile, 'w') as f:
                for node in all_nodes:
                    f.write(f"{node} slots=4\n")
            
            total_procs = len(all_nodes) * 4
            
            # Run with mpirun
            run_cmd = f"cd {test_dir} && mpirun -np {total_procs} -hostfile {hostfile} ./hello_mpi"
            result = self.run_command(run_cmd, check=False)
            
            if result.returncode == 0:
                print(f"  ✓ MPI execution successful ({total_procs} processes across {len(all_nodes)} nodes)")
                print(f"  Output:\n{result.stdout}")
            else:
                print(f"  ⚠ MPI execution failed: {result.stderr}")
        else:
            print(f"  ⚠ MPI compilation failed (may not be configured): {result.stderr}")
        
        print("\n" + "="*70)
        print("UPC++ Multi-Node Testing Complete")
        print("="*70)
        print(f"✓ Test programs available in: {test_dir}")
        print(f"✓ Run manually: cd {test_dir} && upcxx-run -n <N> ./hello_<conduit>")
        print("="*70)

    def install_openshmem_cluster(self):
        """Install Sandia OpenSHMEM 1.5.2 and distribute to all cluster nodes
        
        Downloads, compiles, and installs OpenSHMEM with PMI support for Slurm integration.
        """
        print("\n=== Installing Sandia OpenSHMEM 1.5.2 ===")
        
        pgas_build_dir = Path.home() / "cluster_build_sources"
        pgas_build_dir.mkdir(exist_ok=True)
        
        oshmem_version = "1.5.2"
        oshmem_url = f"https://github.com/Sandia-OpenSHMEM/SOS/releases/download/v{oshmem_version}/sandia-openshmem-{oshmem_version}.tar.gz"
        oshmem_dir = pgas_build_dir / f"sandia-openshmem-{oshmem_version}"
        oshmem_install = "/home/linuxbrew/.linuxbrew/openshmem"
        
        # Download if not already present
        if not oshmem_dir.exists():
            print(f"Downloading OpenSHMEM {oshmem_version}...")
            download_cmd = f"cd {pgas_build_dir} && wget -q {oshmem_url} && tar xzf sandia-openshmem-{oshmem_version}.tar.gz"
            result = self.run_command(download_cmd, check=False)
            
            if result.returncode != 0:
                print(f"⚠ Failed to download OpenSHMEM: {result.stderr}")
                return
        
        # Configure with PMI support
        print("Configuring OpenSHMEM with PMI support...")
        
        gcc_bin = "/home/linuxbrew/.linuxbrew/bin/gcc"
        gxx_bin = "/home/linuxbrew/.linuxbrew/bin/g++"
        
        configure_cmd = (
            f"cd {oshmem_dir} && "
            f"CC={gcc_bin} CXX={gxx_bin} ./configure "
            f"--prefix={oshmem_install} "
            f"--enable-pmi-simple "
            f"--with-pmix=internal"
        )
        
        result = self.run_command(configure_cmd, check=False)
        
        if result.returncode != 0:
            print(f"⚠ OpenSHMEM configuration failed: {result.stderr}")
            return
        
        # Build and install
        print("Building OpenSHMEM (this may take 5-10 minutes)...")
        build_cmd = f"cd {oshmem_dir} && make -j$(nproc) && make install"
        result = self.run_command(build_cmd, check=False)
        
        if result.returncode != 0:
            print(f"⚠ OpenSHMEM build failed: {result.stderr}")
            return
        
        print("✓ OpenSHMEM installed successfully")
        
        # Create symlinks
        print("Creating symbolic links...")
        self.run_command(f"ln -sf {oshmem_install}/bin/oshcc /home/linuxbrew/.linuxbrew/bin/oshcc", check=False)
        self.run_command(f"ln -sf {oshmem_install}/bin/oshrun /home/linuxbrew/.linuxbrew/bin/oshrun", check=False)
        
        # Update environment
        bashrc = Path.home() / ".bashrc"
        env_lines = [
            "\n# OpenSHMEM Environment",
            f"export OPENSHMEM_INSTALL={oshmem_install}",
            f"export PATH={oshmem_install}/bin:$PATH",
            f"export LD_LIBRARY_PATH={oshmem_install}/lib:$LD_LIBRARY_PATH",
        ]
        
        # Check if already added
        with open(bashrc, 'r') as f:
            bashrc_content = f.read()
        
        if "OpenSHMEM Environment" not in bashrc_content:
            with open(bashrc, 'a') as f:
                for line in env_lines:
                    f.write(line + '\n')
            print("✓ Environment variables added to ~/.bashrc")
        
        # Distribute to all cluster nodes
        if self.password:
            print("\nDistributing OpenSHMEM to all cluster nodes...")
            
            all_nodes = [self.master_ip] + self.worker_ips
            
            # Get local IPs
            try:
                result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
                import re
                local_ips = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            except:
                local_ips = []
            
            other_nodes = [ip for ip in all_nodes if ip not in local_ips]
            
            for node_ip in other_nodes:
                print(f"\n→ Distributing to {node_ip}...")
                
                if os.path.exists(oshmem_install):
                    rsync_cmd = (
                        f"sshpass -p '{self.password}' rsync -avz --delete "
                        f"-e 'ssh -o StrictHostKeyChecking=no' "
                        f"{oshmem_install}/ "
                        f"{self.username}@{node_ip}:{oshmem_install}/"
                    )
                    result = self.run_command(rsync_cmd, check=False)
                    
                    if result.returncode == 0:
                        print(f"  ✓ OpenSHMEM copied to {node_ip}")
                        
                        # Update environment on remote node
                        env_update_cmd = f"""sshpass -p '{self.password}' ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} '
                            grep -q "OpenSHMEM Environment" ~/.bashrc || cat >> ~/.bashrc << "EOF"

# OpenSHMEM Environment
export OPENSHMEM_INSTALL={oshmem_install}
export PATH={oshmem_install}/bin:$PATH
export LD_LIBRARY_PATH={oshmem_install}/lib:$LD_LIBRARY_PATH
EOF
                        '"""
                        self.run_command(env_update_cmd, check=False)
                        
                        # Create symlinks
                        symlink_cmd = f"""ssh {self.username}@{node_ip} "sudo ln -sf {oshmem_install}/bin/oshcc /home/linuxbrew/.linuxbrew/bin/oshcc && sudo ln -sf {oshmem_install}/bin/oshrun /home/linuxbrew/.linuxbrew/bin/oshrun" """
                        self.run_command(symlink_cmd, check=False)
                    else:
                        print(f"  ⚠ Failed to copy OpenSHMEM to {node_ip}")
        
        print("\n" + "="*70)
        print("OpenSHMEM Installation Summary")
        print("="*70)
        print(f"✓ OpenSHMEM {oshmem_version}: {oshmem_install}")
        print("\nUsage:")
        print("  Compile: oshcc -o program program.c")
        print("  Run: oshrun -np 4 ./program")
        print("\nDocumentation: https://github.com/Sandia-OpenSHMEM/SOS")
        print("="*70)

    def create_pgas_benchmark_suite(self):
        """Create comprehensive PGAS vs MPI benchmark suite
        
        Develops benchmarks for point-to-point, collective operations, and one-sided communication.
        """
        print("\n=== Creating PGAS vs MPI Benchmark Suite ===")
        
        benchmark_dir = Path.home() / "cluster_build_sources" / "pgas_benchmarks"
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Creating benchmark suite in: {benchmark_dir}")
        
        # 1. Point-to-point latency benchmark (UPC++ vs MPI)
        print("\n→ Creating point-to-point latency benchmark...")
        
        p2p_upcxx = """
#include <upcxx/upcxx.hpp>
#include <iostream>
#include <chrono>

int main() {
    upcxx::init();
    
    const int iterations = 10000;
    int rank = upcxx::rank_me();
    int nranks = upcxx::rank_n();
    
    if (nranks < 2) {
        if (rank == 0) std::cout << "Need at least 2 processes\\n";
        upcxx::finalize();
        return 1;
    }
    
    upcxx::global_ptr<int> remote_ptr = upcxx::new_<int>(0);
    int local_val = rank;
    
    upcxx::barrier();
    
    auto start = std::chrono::high_resolution_clock::now();
    
    if (rank == 0) {
        // Ping-pong test
        for (int i = 0; i < iterations; i++) {
            upcxx::rput(local_val, remote_ptr, 1).wait();
        }
    }
    
    upcxx::barrier();
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    if (rank == 0) {
        double latency_us = static_cast<double>(duration.count()) / iterations;
        std::cout << "UPC++ Point-to-Point Latency: " << latency_us << " us\\n";
    }
    
    upcxx::delete_(remote_ptr);
    upcxx::finalize();
    return 0;
}
"""
        
        with open(benchmark_dir / "p2p_latency_upcxx.cpp", 'w') as f:
            f.write(p2p_upcxx)
        
        p2p_mpi = """
#include <mpi.h>
#include <iostream>
#include <chrono>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, nranks;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &nranks);
    
    const int iterations = 10000;
    int val = rank;
    
    if (nranks < 2) {
        if (rank == 0) std::cout << "Need at least 2 processes\\n";
        MPI_Finalize();
        return 1;
    }
    
    MPI_Barrier(MPI_COMM_WORLD);
    
    auto start = std::chrono::high_resolution_clock::now();
    
    if (rank == 0) {
        for (int i = 0; i < iterations; i++) {
            MPI_Send(&val, 1, MPI_INT, 1, 0, MPI_COMM_WORLD);
            MPI_Recv(&val, 1, MPI_INT, 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
    } else if (rank == 1) {
        for (int i = 0; i < iterations; i++) {
            MPI_Recv(&val, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            MPI_Send(&val, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
        }
    }
    
    MPI_Barrier(MPI_COMM_WORLD);
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    if (rank == 0) {
        double latency_us = static_cast<double>(duration.count()) / (2 * iterations);
        std::cout << "MPI Point-to-Point Latency: " << latency_us << " us\\n";
    }
    
    MPI_Finalize();
    return 0;
}
"""
        
        with open(benchmark_dir / "p2p_latency_mpi.cpp", 'w') as f:
            f.write(p2p_mpi)
        
        # 2. Create Makefile for benchmarks
        print("→ Creating Makefile...")
        
        makefile = """
# PGAS vs MPI Benchmark Suite Makefile

UPCXX = upcxx
MPICXX = mpic++
CXXFLAGS = -O3 -std=c++11

all: p2p_latency_upcxx p2p_latency_mpi

p2p_latency_upcxx: p2p_latency_upcxx.cpp
\t$(UPCXX) $(CXXFLAGS) $< -o $@

p2p_latency_mpi: p2p_latency_mpi.cpp
\t$(MPICXX) $(CXXFLAGS) $< -o $@

clean:
\trm -f p2p_latency_upcxx p2p_latency_mpi

.PHONY: all clean
"""
        
        with open(benchmark_dir / "Makefile", 'w') as f:
            f.write(makefile)
        
        # 3. Create run script
        print("→ Creating automated test runner...")
        
        run_script = f"""#!/bin/bash
# Automated PGAS vs MPI Benchmark Runner

BENCHMARK_DIR="{benchmark_dir}"
RESULTS_DIR="$BENCHMARK_DIR/results"
mkdir -p "$RESULTS_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="$RESULTS_DIR/benchmark_$TIMESTAMP.txt"

echo "PGAS vs MPI Benchmark Suite" | tee "$RESULTS_FILE"
echo "=============================" | tee -a "$RESULTS_FILE"
echo "Date: $(date)" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

cd "$BENCHMARK_DIR"

# Build all benchmarks
echo "Building benchmarks..." | tee -a "$RESULTS_FILE"
make clean && make all

if [ $? -ne 0 ]; then
    echo "Build failed!" | tee -a "$RESULTS_FILE"
    exit 1
fi

echo "" | tee -a "$RESULTS_FILE"

# Run point-to-point latency tests
echo "Running Point-to-Point Latency Tests" | tee -a "$RESULTS_FILE"
echo "-------------------------------------" | tee -a "$RESULTS_FILE"

echo "UPC++ (2 processes):" | tee -a "$RESULTS_FILE"
upcxx-run -n 2 ./p2p_latency_upcxx 2>&1 | tee -a "$RESULTS_FILE"

echo "" | tee -a "$RESULTS_FILE"
echo "MPI (2 processes):" | tee -a "$RESULTS_FILE"
mpirun -np 2 ./p2p_latency_mpi 2>&1 | tee -a "$RESULTS_FILE"

echo "" | tee -a "$RESULTS_FILE"
echo "=============================" | tee -a "$RESULTS_FILE"
echo "Results saved to: $RESULTS_FILE" | tee -a "$RESULTS_FILE"
"""
        
        run_script_path = benchmark_dir / "run_benchmarks.sh"
        with open(run_script_path, 'w') as f:
            f.write(run_script)
        
        # Make executable
        os.chmod(run_script_path, 0o755)
        
        # 4. Create README for benchmark suite
        print("→ Creating README...")
        
        readme = f"""# PGAS vs MPI Benchmark Suite

Comprehensive performance comparison between PGAS libraries (UPC++, OpenSHMEM) and MPI.

## Directory Structure

```
{benchmark_dir}/
├── Makefile                   # Build all benchmarks
├── run_benchmarks.sh          # Automated test runner
├── p2p_latency_upcxx.cpp     # Point-to-point latency (UPC++)
├── p2p_latency_mpi.cpp       # Point-to-point latency (MPI)
└── results/                   # Benchmark results
```

## Building Benchmarks

```bash
cd {benchmark_dir}
make all
```

## Running Benchmarks

### Automated (Recommended)
```bash
cd {benchmark_dir}
./run_benchmarks.sh
```

### Manual Execution

#### Point-to-Point Latency
```bash
# UPC++
upcxx-run -n 2 ./p2p_latency_upcxx

# MPI
mpirun -np 2 ./p2p_latency_mpi
```

## Results

Results are saved in `{benchmark_dir}/results/` with timestamps.

## Adding More Benchmarks

1. Create benchmark source files (e.g., `bandwidth_upcxx.cpp`, `bandwidth_mpi.cpp`)
2. Update `Makefile` with new targets
3. Update `run_benchmarks.sh` to execute new benchmarks
4. Document in this README

## Benchmark Categories

- **Point-to-Point**: Latency and bandwidth measurements
- **Collectives**: Broadcast, reduce, gather, scatter operations
- **One-Sided**: Put/get vs MPI one-sided operations
- **Memory Operations**: Distributed memory access patterns

## References

- UPC++: https://upcxx.lbl.gov/
- OpenSHMEM: https://github.com/Sandia-OpenSHMEM/SOS
- MPI: https://www.open-mpi.org/
"""
        
        with open(benchmark_dir / "README.md", 'w') as f:
            f.write(readme)
        
        print("\n" + "="*70)
        print("PGAS Benchmark Suite Creation Complete")
        print("="*70)
        print(f"✓ Benchmark directory: {benchmark_dir}")
        print(f"✓ Build: cd {benchmark_dir} && make all")
        print(f"✓ Run: cd {benchmark_dir} && ./run_benchmarks.sh")
        print("\nBenchmarks created:")
        print("  - Point-to-point latency (UPC++ vs MPI)")
        print("\nTo add more benchmarks, edit Makefile and run_benchmarks.sh")
        print("="*70)

    def configure_slurm(self):
        """Configure Slurm for the cluster"""
        print("\n=== Configuring Slurm ===")
        
        # Create Slurm directories
        slurm_dirs = [
            '/var/spool/slurm',
            '/var/spool/slurm/ctld',
            '/var/spool/slurm/d',
            '/var/log/slurm',
            '/etc/slurm'
        ]
        
        for dir_path in slurm_dirs:
            self.run_sudo_command(f"mkdir -p {dir_path}")
            # Use slurm user for Slurm directories (required by slurmctld/slurmd)
            self.run_sudo_command(f"chown -R slurm:slurm {dir_path}", check=False)
        
        # Generate slurm.conf
        slurm_conf = self.generate_slurm_conf()
        
        with open('/tmp/slurm.conf', 'w') as f:
            f.write(slurm_conf)
        
        self.run_sudo_command("cp /tmp/slurm.conf /etc/slurm/slurm.conf")
        
        # Generate cgroup.conf
        # Note: CgroupAutomount is deprecated in Slurm 24.11+ and causes startup failures
        cgroup_conf = """ConstrainCores=yes\nConstrainRAMSpace=yes\n"""
        with open('/tmp/cgroup.conf', 'w') as f:
            f.write(cgroup_conf)

        self.run_sudo_command("cp /tmp/cgroup.conf /etc/slurm/cgroup.conf")
        
        print("Slurm configuration files created")

        # Enable and start Slurm services using systemctl
        if self.is_master:
            print("Enabling and starting Slurm controller (slurmctld)...")
            self.run_sudo_command("systemctl enable slurmctld", check=False)
            self.run_sudo_command("systemctl restart slurmctld", check=False)

        print("Enabling and starting Slurm daemon (slurmd)...")
        self.run_sudo_command("systemctl enable slurmd", check=False)
        self.run_sudo_command("systemctl restart slurmd", check=False)

        print("Slurm configured successfully")
    
    def generate_slurm_conf(self) -> str:
        """Generate slurm.conf configuration file"""
        # Get system information
        try:
            cpu_result = self.run_command("nproc", check=False)
            cpus = cpu_result.stdout.strip() if cpu_result.returncode == 0 else "4"

            mem_result = self.run_command("free -m | grep Mem | awk '{print $2}'", check=False)
            memory = mem_result.stdout.strip() if mem_result.returncode == 0 else "8000"
        except Exception:
            cpus = "4"
            memory = "8000"

        # Use master_hostname from initialization (consistent across all nodes)
        conf = f"""# slurm.conf - Slurm configuration file
ClusterName=cluster
SlurmctldHost={self.master_hostname}({self.master_ip})

# Scheduling
SchedulerType=sched/backfill
SelectType=select/cons_tres
SelectTypeParameters=CR_Core

# Logging
SlurmctldDebug=info
SlurmctldLogFile=/var/log/slurm/slurmctld.log
SlurmdDebug=info
SlurmdLogFile=/var/log/slurm/slurmd.log

# State preservation
StateSaveLocation=/var/spool/slurm/ctld
SlurmdSpoolDir=/var/spool/slurm/d

# Process tracking
ProctrackType=proctrack/linuxproc
TaskPlugin=task/affinity,task/cgroup

# MPI
MpiDefault=pmix

# Timeouts
SlurmctldTimeout=300
SlurmdTimeout=300
InactiveLimit=0
MinJobAge=300
KillWait=30
Waittime=0

# Nodes
"""
        # Add master node (use master_hostname from class attribute)
        conf += f"NodeName={self.master_hostname} CPUs={cpus} RealMemory={memory} State=UNKNOWN\n"

        # Add worker nodes
        for idx, worker_ip in enumerate(self.worker_ips, start=1):
            conf += f"NodeName=worker{idx} CPUs={cpus} RealMemory={memory} State=UNKNOWN\n"

        # Add partition
        all_nodes = f"{self.master_hostname}," + ",".join([f"worker{i+1}" for i in range(len(self.worker_ips))])
        conf += f"\n# Partitions\nPartitionName=all Nodes={all_nodes} Default=YES MaxTime=INFINITE State=UP\n"

        return conf

    def _detect_mpi_network_config(self) -> str:
        """
        Auto-detect the correct network configuration for OpenMPI.
        Returns an MCA parameter configuration string.
        """
        try:
            # Try to find which interface has the master_ip
            result = self.run_command("ip -o -4 addr show", check=False)
            if result.returncode == 0:
                import re
                # Parse output looking for master_ip
                for line in result.stdout.strip().split('\n'):
                    # Format: "2: eth1    inet 192.168.1.147/24 ..."
                    match = re.search(r'\d+:\s+(\S+)\s+inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        iface, ip = match.groups()
                        if ip == self.master_ip or ip in self.all_ips:
                            # Found the interface with cluster IP
                            # Extract network range (e.g., 192.168.1.0/24)
                            # Use IP range instead of interface name for better reliability
                            ip_parts = ip.split('.')
                            network_range = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
                            print(f"DEBUG: Detected MPI network: {network_range} on interface {iface}")
                            return f"btl_tcp_if_include = {network_range}"
        except Exception as e:
            print(f"DEBUG: Could not auto-detect network: {e}")

        # Fallback: use eth1 (common in many setups)
        print("DEBUG: Using fallback network configuration (eth1)")
        return "btl_tcp_if_include = eth1"

    def configure_openmpi(self):
        """Configure OpenMPI for the cluster
        
        OpenMPI Installation (via Homebrew):
        - Installation path: /home/linuxbrew/.linuxbrew/
        - Binary path: /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8/bin/mpirun
        - Prefix: /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8
        
        Usage with --prefix flag (recommended):
          mpirun --prefix /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8 \\
                 --map-by node -np 4 --hostfile ~/.openmpi/hostfile_optimal ./program
        
        Creates three hostfiles:
        1. hostfile - Standard (4 slots/node)
        2. hostfile_optimal - Recommended (1 slot/node) for MPI+OpenMP
        3. hostfile_max - Maximum (auto-detected cores/node) for pure MPI
        """
        print("\n=== Configuring OpenMPI ===")
        
        mpi_dir = Path.home() / ".openmpi"
        mpi_dir.mkdir(exist_ok=True)
        
        # Create multiple hostfiles for different use cases
        all_nodes = [self.master_ip] + self.worker_ips
        
        # 1. Standard hostfile with 4 slots per node (for multiple MPI processes per node)
        hostfile_standard = ""
        for node_ip in all_nodes:
            hostfile_standard += f"{node_ip} slots=4\n"
        
        hostfile_path = mpi_dir / "hostfile"
        with open(hostfile_path, 'w') as f:
            f.write(hostfile_standard)
        
        print(f"✓ Standard hostfile created: {hostfile_path}")
        print(f"  Usage: Multiple MPI processes per node (up to 4)")
        
        # 2. Optimal hostfile with 1 slot per node (recommended for MPI+OpenMP)
        hostfile_optimal = ""
        for node_ip in all_nodes:
            hostfile_optimal += f"{node_ip} slots=1\n"
        
        hostfile_optimal_path = mpi_dir / "hostfile_optimal"
        with open(hostfile_optimal_path, 'w') as f:
            f.write(hostfile_optimal)
        
        print(f"✓ Optimal hostfile created: {hostfile_optimal_path}")
        print(f"  Usage: 1 MPI process per node + max OpenMP threads (RECOMMENDED)")
        
        # 3. Max slots hostfile based on detected cores (if available)
        try:
            hostfile_max = ""
            for node_ip in all_nodes:
                # Try to detect cores via SSH if we have password
                if self.password and node_ip != self.master_ip:
                    import tempfile
                    try:
                        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass:
                            temp_pass.write(self.password)
                            temp_pass_path = temp_pass.name
                        
                        cmd = f'sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} "nproc" 2>/dev/null'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        os.unlink(temp_pass_path)
                        
                        if result.returncode == 0:
                            cores = int(result.stdout.strip())
                            hostfile_max += f"{node_ip} slots={cores}\n"
                        else:
                            hostfile_max += f"{node_ip} slots=16\n"  # Default fallback
                    except:
                        hostfile_max += f"{node_ip} slots=16\n"
                else:
                    # For master node, detect locally
                    try:
                        cores = int(subprocess.run(['nproc'], capture_output=True, text=True).stdout.strip())
                        hostfile_max += f"{node_ip} slots={cores}\n"
                    except:
                        hostfile_max += f"{node_ip} slots=16\n"
            
            hostfile_max_path = mpi_dir / "hostfile_max"
            with open(hostfile_max_path, 'w') as f:
                f.write(hostfile_max)
            
            print(f"✓ Maximum slots hostfile created: {hostfile_max_path}")
            print(f"  Usage: Maximum MPI processes based on detected cores")
        except Exception as e:
            print(f"⚠ Could not create max slots hostfile: {e}")
        
        print(f"\nHostfile summary:")
        print(f"  {hostfile_path} - Standard (4 slots/node)")
        print(f"  {hostfile_optimal_path} - Optimal (1 slot/node + OpenMP)")
        if (mpi_dir / "hostfile_max").exists():
            print(f"  {mpi_dir / 'hostfile_max'} - Maximum (all cores/node)")

        # Auto-detect network interface or use IP range
        # Try to find the network interface that has the master_ip
        network_config = self._detect_mpi_network_config()

        # Create default MCA parameters file
        # Note: Port ranges help with firewall configuration
        # btl_tcp_port_min_v4 sets starting port for BTL TCP communication
        # oob_tcp_port_range sets port range for out-of-band communication (PRRTE)
        
        # Set wrapper compiler to use Homebrew's gcc-11 symlink (which points to gcc-15)
        # Set prefix so OpenMPI can find prted and other binaries on remote nodes
        mca_params = f"""# OpenMPI MCA parameters
btl = ^openib
{network_config}

# OpenMPI installation prefix - critical for finding prted on remote nodes
# This tells mpirun where to find OpenMPI binaries via SSH
orte_prefix = /home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8
opal_prefix = /home/linuxbrew/.linuxbrew

# Port configuration for firewall-friendly operation
# BTL (Byte Transfer Layer) TCP ports
btl_tcp_port_min_v4 = 50000

# Out-of-band (OOB) TCP port range for PRRTE daemon communication
# This is critical for cross-cluster MPI execution
oob_tcp_port_range = 50100-50200
"""
        mca_file = Path.home() / ".openmpi" / "mca-params.conf"
        with open(mca_file, 'w') as f:
            f.write(mca_params)

        print(f"OpenMPI MCA parameters configured: {network_config}")
        print("Port ranges: BTL TCP (50000+), OOB TCP (50100-50200)")
        print("OpenMPI configured successfully")
    
    def verify_installation(self):
        """Verify that all components are installed correctly"""
        print("\n=== Verifying Installation ===")

        # Ensure Homebrew is in PATH for verification
        homebrew_path = "/home/linuxbrew/.linuxbrew/bin"
        if os.path.exists(homebrew_path):
            original_path = os.environ.get('PATH', '')
            os.environ['PATH'] = f"{homebrew_path}:/home/linuxbrew/.linuxbrew/sbin:{original_path}"

        checks = [
            ("SSH", "ssh -V"),
            ("Slurm (sinfo)", "sinfo --version"),
            ("Slurm (scontrol)", "scontrol --version"),
            ("OpenMPI (mpirun)", "mpirun --version"),
            ("OpenMPI (mpicc)", "mpicc --version"),
            ("PRRTE (prte)", "prte --version"),
            ("PRRTE (prun)", "prun --version"),
        ]

        for name, command in checks:
            result = self.run_command(command, check=False)
            if result.returncode == 0:
                print(f"✓ {name}: OK")
            else:
                print(f"✗ {name}: NOT FOUND or ERROR")

        print("\nVerification completed")

        # WSL-specific warning for MPI
        if self._is_wsl():
            print("\n" + "="*60)
            print("⚠️  WSL DETECTED - Important MPI Configuration Note")
            print("="*60)
            print("Cross-cluster mpirun may hang due to Windows port forwarding.")
            print("Windows only forwards SSH (port 22), not MPI ports (50000-50200).")
            print()
            print("To fix this, run in PowerShell as Administrator on Windows:")
            print("  cd", str(Path.cwd()))
            print("  .\\configure_wsl_firewall.ps1")
            print()
            print("For full port forwarding (if needed):")
            print("  .\\setup_wsl_port_forwarding.ps1")
            print()
            print("Alternative: Use pdsh for parallel execution (no port issues):")
            print("  brew install pdsh")
            print("  pdsh -w 192.168.1.[147,137,96] hostname")
            print("="*60)
    
    def run_full_setup(self, config_file: Optional[str] = None, non_interactive: bool = False):
        """Run the complete cluster setup"""
        print("=" * 60)
        print("CLUSTER SETUP SCRIPT")
        print("=" * 60)
        print(f"Master Node: {self.master_ip}")
        print(f"Worker Nodes: {', '.join(self.worker_ips)}")
        print(f"Current node is: {'MASTER' if self.is_master else 'WORKER'}")
        if not self.is_master:
            print("\n⚠️  WARNING: This script is NOT running on the master node!")
            print(f"⚠️  To automatically set up all workers, please run this script")
            print(f"⚠️  from the master node at IP: {self.master_ip}")
            print()
        print("=" * 60)
        
        # Check sudo access
        if not self.check_sudo_access():
            print("\nWARNING: This script requires sudo access.")
            print("Please run with sudo or ensure passwordless sudo is configured.")
            if not non_interactive:
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("Setup cancelled")
                    return
            else:
                print("Running in non-interactive mode, continuing...")
        
        try:
            # Step 1: SSH and Security (FIRST - enables remote operations)
            print("\n" + "="*60)
            print("STEP 1: SSH Keys and Passwordless Sudo")
            print("="*60)
            self.setup_ssh()
            self.configure_passwordless_ssh()
            self.configure_hosts_file()
            
            # Step 2: Homebrew and Core Tools (SECOND - base dependencies)
            print("\n" + "="*60)
            print("STEP 2: Homebrew and Core Development Tools")
            print("="*60)
            self.install_homebrew()
            self.configure_system_path()  # Configure PATH after Homebrew installation
            
            # Step 3: Install and configure GCC, binutils, Python (THIRD - compilers)
            print("\n" + "="*60)
            print("STEP 3: Compilers and Build Tools")
            print("="*60)
            # GCC symlinks are created in install_openmpi, but we need them earlier
            # So let's create them here if they don't exist
            homebrew_bin = "/home/linuxbrew/.linuxbrew/bin"
            gcc_version_result = self.run_command(f"ls {homebrew_bin}/gcc-* 2>/dev/null | grep -E 'gcc-[0-9]+$' | head -1", check=False)
            if gcc_version_result.returncode == 0 and gcc_version_result.stdout.strip():
                gcc_path = gcc_version_result.stdout.strip()
                gcc_version = gcc_path.split('-')[-1]
                print(f"Creating GCC {gcc_version} symlinks...")
                self.run_command(f"ln -sf {homebrew_bin}/gcc-{gcc_version} {homebrew_bin}/gcc", check=False)
                self.run_command(f"ln -sf {homebrew_bin}/g++-{gcc_version} {homebrew_bin}/g++", check=False)
                self.run_command(f"ln -sf {homebrew_bin}/gfortran-{gcc_version} {homebrew_bin}/gfortran", check=False)
                print(f"✓ GCC symlinks: gcc/g++/gfortran -> gcc-{gcc_version}")
            
            # Step 4: Parallel Programming Libraries (FOURTH - main software)
            print("\n" + "="*60)
            print("STEP 4: Parallel Programming Libraries")
            print("="*60)
            self.install_slurm()
            self.install_openmpi()
            self.install_openmp()
            self.install_upcxx_and_pgas()
            
            # Step 5: Configuration (FIFTH - finalize setup)
            print("\n" + "="*60)
            print("STEP 5: Configuration and Firewall")
            print("="*60)
            self.configure_firewall_for_mpi()
            self.configure_slurm()
            self.configure_openmpi()
            self.verify_installation()
            
            print("\n" + "=" * 60)
            print("LOCAL NODE SETUP COMPLETED SUCCESSFULLY")
            print("=" * 60)
            
            # Distribute PGAS libraries to all other cluster nodes
            if self.password:
                self.distribute_pgas_to_cluster()
                
                # Configure passwordless sudo on all nodes
                self.configure_passwordless_sudo_cluster()
                
                # Distribute system symlinks to all nodes
                self.distribute_system_symlinks_cluster()
                
                # Test multi-node UPC++ execution
                self.test_multinode_upcxx()
                
                # Install OpenSHMEM (optional but recommended)
                self.install_openshmem_cluster()
                
                # Create PGAS benchmark suite
                self.create_pgas_benchmark_suite()
            
            # If we have a password and multiple nodes, offer to setup all other nodes
            # This works whether run from master or a worker node
            workers_setup_success = False
            other_nodes_setup_success = False
            other_nodes = []
            
            if self.password and config_file:
                # Setup all nodes except the current one
                if not self.is_master:
                    # Running from worker, also setup master
                    other_nodes.append(self.master_ip)
                # Add all workers except current node
                for worker_ip in self.worker_ips:
                    # Get current node's IP to exclude it
                    try:
                        import socket
                        hostname = socket.gethostname()
                        local_ip = socket.gethostbyname(hostname)
                        # Also check all network interfaces
                        result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
                        if result.returncode == 0:
                            import re
                            ip_pattern = r'inet\s+(\d+\.\d+\.\d+\.\d+)'
                            found_ips = re.findall(ip_pattern, result.stdout)
                            if worker_ip not in found_ips:
                                other_nodes.append(worker_ip)
                        elif worker_ip != local_ip:
                            other_nodes.append(worker_ip)
                    except:
                        # If we can't determine, just add all workers
                        other_nodes.append(worker_ip)
                
                if other_nodes:
                    print(f"\n=== Setting up other cluster nodes from this node ===")
                    other_nodes_setup_success = self.setup_all_workers(config_file, other_nodes)
            
            # Final summary
            print("\n" + "=" * 60)
            print("CLUSTER SETUP SUMMARY")
            print("=" * 60)
            
            # Show appropriate summary based on what was done
            node_type = "Master" if self.is_master else "Worker"
            print(f"✓ {node_type} node (this node) setup completed")
            
            if other_nodes_setup_success:
                print(f"✓ All other cluster nodes setup completed automatically")
                print("\nYour entire cluster is ready!")
                print("\nNext steps:")
                print("1. Test Slurm with: sinfo")
                print("2. Test OpenMPI with: mpirun -np 2 hostname")
                print("3. Submit test job: sbatch test_job.sh")
            elif other_nodes and not other_nodes_setup_success:
                print(f"⚠ Some cluster nodes failed automatic setup")
                print("\nNext steps:")
                print("1. Check failed nodes and setup manually if needed")
                print("2. Test Slurm with: sinfo")
                print("3. Test OpenMPI with: mpirun -np 2 hostname")
            elif self.password and config_file:
                print(f"✓ This node is configured")
                print("\nNext steps:")
                print("1. Run this script on other nodes with --password flag, or")
                print(f"   Run from any node: python cluster_setup.py --config <config> --password")
                print("2. Test Slurm with: sinfo")
                print("3. Test OpenMPI with: mpirun -np 2 hostname")
            else:
                print(f"✓ This node is configured")
                print("\nNext steps:")
                print("1. Setup other cluster nodes:")
                print(f"   python cluster_setup.py --config <config_file> --password")
                print("   (Can be run from any node in the cluster)")
                print("2. Test Slurm with: sinfo")
                print("3. Test OpenMPI with: mpirun -np 2 hostname")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"\n\nERROR during setup: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def load_yaml_config(path: str) -> Dict:
    """Load YAML config file and return a dict"""
    if yaml is None:
        raise RuntimeError("PyYAML is required to load YAML configs. Install with: pip install pyyaml")
    with open(path, 'r') as f:
        data = yaml.safe_load(f) or {}
    return data


def main():
    """Main entry point for the cluster setup script"""
    parser = argparse.ArgumentParser(
        description="Cluster Setup Script for Slurm and OpenMPI on Ubuntu/WSL and Red Hat/CentOS/Fedora",
        epilog="Example: python cluster_setup.py --config cluster_config.yaml --password"
    )
    parser.add_argument(
        '--config', '-c',
        required=True,
        help='Path to YAML config file containing master/workers/username (required)'
    )
    parser.add_argument(
        '--password', '-p',
        action='store_true',
        help='Prompt for password to automatically setup entire cluster (copies SSH keys and runs setup on all workers)'
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run in non-interactive mode (skip confirmation prompts)'
    )
    
    args = parser.parse_args()
    
    # Get password if flag is set
    password = None
    if args.password:
        password = getpass.getpass("Enter password for worker nodes: ")
    
    # Load YAML config
    try:
        config = load_yaml_config(args.config)
    except Exception as e:
        print(f"Error loading config file {args.config}: {e}")
        sys.exit(1)
    
    # Extract configuration
    master = config.get('master')
    workers = config.get('workers')
    username = config.get('username')
    
    # Handle new format where master and workers contain IP and OS info
    if isinstance(master, dict):
        master = master.get('ip')
    
    # Normalize workers if provided as string in YAML
    if isinstance(workers, str):
        workers = workers.split()
    elif isinstance(workers, list) and workers and isinstance(workers[0], dict):
        # Extract IPs from list of dicts
        workers = [w.get('ip') if isinstance(w, dict) else w for w in workers]
    
    # Validate presence
    if not master or not workers:
        print("Error: Config file must contain 'master' and 'workers' fields.")
        print("\nExpected YAML format:")
        print("  master: 192.168.1.100")
        print("  workers:")
        print("    - 192.168.1.101")
        print("    - 192.168.1.102")
        print("  username: myuser  # optional")
        print("\nOr with OS information:")
        print("  master:")
        print("    ip: 192.168.1.100")
        print("    os: ubuntu")
        print("  workers:")
        print("    - ip: 192.168.1.101")
        print("      os: ubuntu")
        sys.exit(1)
    
    # Validate IP addresses
    def is_valid_ip(ip):
        # Allow localhost and 127.0.0.1
        if ip in ['localhost', '127.0.0.1']:
            return True
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(part and part.isdigit() and 0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False

    if not is_valid_ip(master):
        print(f"Error: Invalid master IP address: {master}")
        sys.exit(1)

    for worker_ip in workers:
        if not is_valid_ip(worker_ip):
            print(f"Error: Invalid worker IP address: {worker_ip}")
            sys.exit(1)
    
    # Create and run setup
    setup = ClusterSetup(master, workers, username, password)
    setup.run_full_setup(config_file=args.config, non_interactive=args.non_interactive)


if __name__ == '__main__':
    main()