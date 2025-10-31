#!/usr/bin/env python3
"""
Cluster Setup Script for Slurm and OpenMPI
Supports Ubuntu Linux and WSL with Ubuntu

Usage:
    python cluster_setup.py --config config.yml [--password]
    
    --config:   Path to YAML configuration file (required)
    --password: Prompt for password to automatically setup entire cluster (optional)

When run with --password on the master node:
    1. Sets up the master node (password is used for sudo commands)
    2. Copies SSH keys to all worker nodes
    3. Automatically runs the setup on each worker node via SSH
    4. Password is automatically provided for sudo commands on worker nodes
    5. Configures the entire cluster in one command without manual intervention

Example:
    # Full automatic cluster setup (recommended)
    python cluster_setup.py --config cluster_config.yaml --password
    
    # Manual setup (without --password, you must run on each node separately)
    python cluster_setup.py --config cluster_config.yaml
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
        self.is_master = self._is_current_node_master()
        # Get master hostname - will be used for slurm.conf generation
        self.master_hostname = self._get_master_hostname()
        
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
        result = subprocess.run(
            command,
            shell=shell,
            check=False,
            capture_output=True,
            text=True
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
        """Install Homebrew on Ubuntu/WSL"""
        print("\n=== Installing Homebrew ===")
        
        # Check if brew is already installed (use shutil.which for robustness)
        if shutil.which("brew") or os.path.exists("/home/linuxbrew/.linuxbrew/bin/brew"):
            print("Homebrew already installed")
            return
        
        # Install dependencies for Homebrew
        print("Installing Homebrew dependencies...")
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
            
            # Add to shell profile
            shell_profile = Path.home() / ".bashrc"
            with open(shell_profile, 'a') as f:
                f.write('\n# Homebrew\n')
                f.write(f'eval "$({homebrew_path}/brew shellenv)"\n')
        
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
        print("Creating ~/.ssh/environment...")
        try:
            ssh_dir = Path.home() / ".ssh"
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            ssh_env = ssh_dir / "environment"
            with open(ssh_env, 'w') as f:
                f.write(f"PATH={homebrew_path}:{homebrew_sbin}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n")
            
            ssh_env.chmod(0o600)
            print("✓ Created ~/.ssh/environment")
        
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
                # Wait for any other apt processes to finish and update/install sshpass
                self.run_sudo_command("while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do sleep 1; done", check=False)
                self.run_sudo_command("apt-get update", check=True)
                self.run_sudo_command("apt-get install -y sshpass", check=True)
            except Exception as e:
                print(f"Failed to install sshpass: {e}")
                print("Please install sshpass manually: sudo apt-get install -y sshpass")
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
    
    def _setup_worker_node(self, worker_ip: str, config_file: str):
        """Setup a worker node remotely via SSH"""
        import tempfile
        
        print(f"\n{'=' * 60}")
        print(f"Setting up worker node: {worker_ip}")
        print(f"{'=' * 60}")
        
        if not self.password:
            print("Error: Password required for worker setup")
            return False
        
        try:
            # First, copy the config file to the worker node
            temp_config = f"/tmp/cluster_config_{os.getpid()}.yaml"
            print(f"Copying configuration file to {worker_ip}...")
            copy_cmd = f"scp -o StrictHostKeyChecking=no {config_file} {self.username}@{worker_ip}:{temp_config}"
            self.run_command(copy_cmd, check=True)
            
            # Copy the cluster_setup.py script to the worker node
            script_path = os.path.abspath(__file__)
            temp_script = f"/tmp/cluster_setup_{os.getpid()}.py"
            print(f"Copying setup script to {worker_ip}...")
            copy_script_cmd = f"scp -o StrictHostKeyChecking=no {script_path} {self.username}@{worker_ip}:{temp_script}"
            self.run_command(copy_script_cmd, check=True)
            
            # Make the script executable
            chmod_cmd = f"ssh -o StrictHostKeyChecking=no {self.username}@{worker_ip} 'chmod +x {temp_script}'"
            self.run_command(chmod_cmd, check=True)
            
            # Create a temporary password file for sudo
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass_file:
                temp_pass_file.write(self.password)
                temp_pass_path = temp_pass_file.name
            
            try:
                # Configure passwordless sudo for the user (temporary, for installation)
                print(f"Configuring sudo access on {worker_ip}...")
                
                # Create a wrapper script that handles sudo with password
                wrapper_script = f"""#!/bin/bash
# Wrapper script to run cluster setup with sudo password handling

# Create a helper function for sudo with password
export SUDO_ASKPASS=/tmp/askpass_{os.getpid()}.sh
cat > $SUDO_ASKPASS << 'ASKPASS_EOF'
#!/bin/bash
echo '{self.password}'
ASKPASS_EOF
chmod +x $SUDO_ASKPASS

# Run the setup script WITHOUT --password flag
# The worker node doesn't need password for SSH setup (already has keys from master)
# Use --non-interactive flag to skip confirmation prompts
export SUDO_ASKPASS
python3 {temp_script} --config {temp_config} --non-interactive

# Cleanup
rm -f $SUDO_ASKPASS
"""
                
                temp_wrapper = f"/tmp/wrapper_{os.getpid()}.sh"
                
                # Copy wrapper script to worker
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as local_wrapper:
                    local_wrapper.write(wrapper_script)
                    local_wrapper_path = local_wrapper.name
                
                try:
                    copy_wrapper_cmd = f"scp -o StrictHostKeyChecking=no {local_wrapper_path} {self.username}@{worker_ip}:{temp_wrapper}"
                    self.run_command(copy_wrapper_cmd, check=True)
                    
                    chmod_wrapper_cmd = f"ssh -o StrictHostKeyChecking=no {self.username}@{worker_ip} 'chmod +x {temp_wrapper}'"
                    self.run_command(chmod_wrapper_cmd, check=True)
                    
                    # Run the setup script on the worker node with password handling
                    print(f"Running setup on {worker_ip} (this may take several minutes)...")
                    
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
                        print(f"\n✓ Successfully set up worker node: {worker_ip}")
                        success = True
                    else:
                        print(f"\n✗ Failed to set up worker node: {worker_ip} (exit code: {process.returncode})")
                        success = False
                    
                    # Cleanup temporary files on worker node
                    cleanup_cmd = f"ssh -o StrictHostKeyChecking=no {self.username}@{worker_ip} 'rm -f {temp_config} {temp_script} {temp_wrapper} /tmp/askpass_*.sh'"
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
    
    def setup_all_workers(self, config_file: str):
        """Automatically setup all worker nodes via SSH"""
        if not self.password:
            print("\nSkipping automatic worker setup (no password provided)")
            return False
        
        if not self.worker_ips:
            print("\nNo worker nodes to setup")
            return True
        
        print(f"\n{'=' * 60}")
        print("AUTOMATIC WORKER NODE SETUP")
        print(f"{'=' * 60}")
        print(f"Will setup {len(self.worker_ips)} worker node(s)")
        print(f"Worker IPs: {', '.join(self.worker_ips)}")
        print("\nProceeding with automatic worker setup...")
        
        success_count = 0
        failed_nodes = []
        
        for worker_ip in self.worker_ips:
            if self._setup_worker_node(worker_ip, config_file):
                success_count += 1
            else:
                failed_nodes.append(worker_ip)
        
        print(f"\n{'=' * 60}")
        print("WORKER SETUP SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total workers: {len(self.worker_ips)}")
        print(f"Successfully set up: {success_count}")
        print(f"Failed: {len(failed_nodes)}")
        
        if failed_nodes:
            print(f"\nFailed nodes: {', '.join(failed_nodes)}")
            print("You may need to setup these nodes manually")
        
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
        """Install Slurm workload manager using apt"""
        print("\n=== Installing Slurm ===")
        
        # Check if Slurm is already installed
        result = self.run_command("which slurmctld", check=False)
        if result.returncode == 0:
            print("Slurm already installed")
            return
        
        # Note: Homebrew has a "slurm" package but it's a network monitor, not the workload manager
        # We need to install slurm-wlm from apt instead
        print("Installing Slurm workload manager from apt...")
        self.run_sudo_command("apt-get update")
        self.run_sudo_command("apt-get install -y slurm-wlm slurm-wlm-doc slurm-client")
        
        print("Slurm installation completed")
    
    def install_openmpi(self):
        """Install OpenMPI using Homebrew"""
        print("\n=== Installing OpenMPI ===")
        
        brew_cmd = "/home/linuxbrew/.linuxbrew/bin/brew"
        if not os.path.exists(brew_cmd):
            print("Error: Homebrew not found. Please install Homebrew first.")
            return
        
        # Install OpenMPI
        print("Installing OpenMPI via Homebrew...")
        result = self.run_command(f"{brew_cmd} install open-mpi", check=False)
        
        if result.returncode != 0:
            print("Installing OpenMPI from apt as fallback...")
            self.run_sudo_command("apt-get update")
            self.run_sudo_command("apt-get install -y openmpi-bin openmpi-common libopenmpi-dev")
        
        print("OpenMPI installation completed")
    
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
        """Configure OpenMPI for the cluster"""
        print("\n=== Configuring OpenMPI ===")
        
        # Create hostfile for MPI
        hostfile_content = f"{self.master_ip} slots=4\n"
        for worker_ip in self.worker_ips:
            hostfile_content += f"{worker_ip} slots=4\n"
        
        mpi_dir = Path.home() / ".openmpi"
        mpi_dir.mkdir(exist_ok=True)
        
        hostfile_path = mpi_dir / "hostfile"
        with open(hostfile_path, 'w') as f:
            f.write(hostfile_content)
        
        print(f"OpenMPI hostfile created at {hostfile_path}")
        print(f"Content:\n{hostfile_content}")

        # Auto-detect network interface or use IP range
        # Try to find the network interface that has the master_ip
        network_config = self._detect_mpi_network_config()

        # Create default MCA parameters file
        # Note: Port ranges help with firewall configuration
        # btl_tcp_port_min_v4 sets starting port for BTL TCP communication
        # oob_tcp_port_range sets port range for out-of-band communication (PRRTE)
        mca_params = f"""# OpenMPI MCA parameters
btl = ^openib
{network_config}

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
            # Setup steps for current node
            self.install_homebrew()
            self.configure_system_path()  # Configure PATH after Homebrew installation
            self.setup_ssh()
            self.configure_passwordless_ssh()
            self.configure_hosts_file()
            self.install_slurm()
            self.install_openmpi()
            self.configure_slurm()
            self.configure_openmpi()
            self.verify_installation()
            
            print("\n" + "=" * 60)
            print("LOCAL NODE SETUP COMPLETED SUCCESSFULLY")
            print("=" * 60)
            
            # If this is the master node and we have a password, offer to setup workers
            workers_setup_success = False
            if self.is_master and self.password and config_file and self.worker_ips:
                workers_setup_success = self.setup_all_workers(config_file)
            
            # Final summary
            print("\n" + "=" * 60)
            print("CLUSTER SETUP SUMMARY")
            print("=" * 60)
            
            if self.is_master:
                if workers_setup_success:
                    print("✓ Master node setup completed")
                    print("✓ All worker nodes setup completed automatically")
                    print("\nYour cluster is ready!")
                    print("\nNext steps:")
                    print("1. Test Slurm with: sinfo")
                    print("2. Test OpenMPI with: mpirun -np 2 hostname")
                elif self.password and config_file and self.worker_ips:
                    print("✓ Master node setup completed")
                    print("⚠ Some worker nodes failed automatic setup")
                    print("\nNext steps:")
                    print("1. Manually setup failed worker nodes")
                    print("2. Test Slurm with: sinfo")
                    print("3. Test OpenMPI with: mpirun -np 2 hostname")
                elif self.password:
                    print("✓ Master node setup completed")
                    print("✓ SSH keys copied to worker nodes")
                    print("\nNext steps:")
                    print("1. Run this script on each worker node:")
                    print(f"   python cluster_setup.py --config <config_file>")
                    print("2. Test Slurm with: sinfo")
                    print("3. Test OpenMPI with: mpirun -np 2 hostname")
                else:
                    print("✓ Master node setup completed")
                    print("\nNext steps:")
                    print("1. Copy SSH keys to worker nodes manually, or")
                    print("   Re-run with --password flag for automatic setup")
                    print("2. Run this script on each worker node")
                    print("3. Test Slurm with: sinfo")
                    print("4. Test OpenMPI with: mpirun -np 2 hostname")
            else:
                print("✓ Worker node setup completed")
                print("\nThis worker is now part of the cluster")
            
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
        description="Cluster Setup Script for Slurm and OpenMPI on Ubuntu/WSL",
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
    
    # Normalize workers if provided as string in YAML
    if isinstance(workers, str):
        workers = workers.split()
    
    # Validate presence
    if not master or not workers:
        print("Error: Config file must contain 'master' and 'workers' fields.")
        print("\nExpected YAML format:")
        print("  master: 192.168.1.100")
        print("  workers:")
        print("    - 192.168.1.101")
        print("    - 192.168.1.102")
        print("  username: myuser  # optional")
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