"""
SSH configuration and key management

Provides:
- SSH key generation and distribution
- Passwordless SSH setup between all nodes
- SSH configuration management
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

from .core import ClusterCore


class SSHManager:
    """Manage SSH configuration and keys across cluster"""
    
    def __init__(self, core: ClusterCore):
        """
        Initialize SSH manager
        
        Args:
            core: ClusterCore instance for command execution
        """
        self.core = core
    
    def setup_ssh(self):
        """Install and configure SSH server"""
        print("\n=== Setting up SSH ===")
        
        # Install SSH if not present
        if not shutil.which("ssh"):
            print("Installing OpenSSH...")
            if self.core.pkg_manager == 'dnf':
                self.core.run_sudo_command(
                    "dnf install -y openssh-clients openssh-server", check=False
                )
            else:
                self.core.run_sudo_command("apt-get update", check=False)
                self.core.run_sudo_command(
                    "apt-get install -y openssh-client openssh-server"
                )
        
        # Start and enable SSH service
        self.core.run_sudo_command("service ssh start", check=False)
        self.core.run_sudo_command("systemctl enable ssh", check=False)
        
        print("SSH service configured")
    
    def configure_passwordless_ssh(self):
        """Configure passwordless SSH for current user"""
        print("\n=== Configuring Passwordless SSH ===")
        
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        # Generate SSH key if it doesn't exist
        id_rsa = ssh_dir / "id_rsa"
        if not id_rsa.exists():
            print("Generating SSH key pair...")
            self.core.run_command(
                f'ssh-keygen -t rsa -b 4096 -f {id_rsa} -N ""'
            )
        
        # Add own public key to authorized_keys
        pub_key_path = ssh_dir / "id_rsa.pub"
        authorized_keys = ssh_dir / "authorized_keys"
        
        if pub_key_path.exists():
            with open(pub_key_path, 'r') as f:
                pub_key = f.read().strip()
            
            # Ensure authorized_keys exists
            authorized_keys.touch(mode=0o600, exist_ok=True)
            
            # Add key if not already present
            with open(authorized_keys, 'r') as f:
                existing_keys = f.read()
            
            if pub_key not in existing_keys:
                with open(authorized_keys, 'a') as f:
                    f.write(pub_key + '\n')
                print("Added public key to authorized_keys")
        
        # Configure SSH client
        ssh_config = ssh_dir / "config"
        ssh_config_content = """Host *
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    ServerAliveInterval 60
    ServerAliveCountMax 3
"""
        with open(ssh_config, 'w') as f:
            f.write(ssh_config_content)
        
        ssh_config.chmod(0o600)
        
        print("SSH configuration completed")
    
    def copy_ssh_keys_to_workers(self):
        """Copy SSH keys to all worker nodes"""
        if not self.core.password:
            print("Error: Password required for SSH key copying")
            return
        
        # Check if sshpass is installed
        if not shutil.which("sshpass"):
            print("Installing sshpass...")
            try:
                if self.core.pkg_manager == 'dnf':
                    self.core.run_sudo_command("dnf install -y sshpass")
                else:
                    self.core.run_sudo_command(
                        "while fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do sleep 1; done",
                        check=False
                    )
                    self.core.run_sudo_command("apt-get update")
                    self.core.run_sudo_command("apt-get install -y sshpass")
            except Exception as e:
                print(f"Failed to install sshpass: {e}")
                return
        
        ssh_dir = Path.home() / ".ssh"
        pub_key_path = ssh_dir / "id_rsa.pub"
        
        if not pub_key_path.exists():
            print("Error: SSH public key not found")
            return
        
        with open(pub_key_path, 'r') as f:
            pub_key = f.read().strip()
        
        for worker_ip in self.core.worker_ips:
            print(f"Copying SSH key to {worker_ip}...")
            try:
                with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_pass:
                    temp_pass.write(self.core.password)
                    temp_pass_path = temp_pass.name
                
                try:
                    # Create .ssh directory on remote host
                    cmd = (
                        f'sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no '
                        f'{self.core.username}@{worker_ip} '
                        f'"mkdir -p ~/.ssh && chmod 700 ~/.ssh"'
                    )
                    self.core.run_command(cmd)
                    
                    # Append public key to authorized_keys
                    cmd = (
                        f'sshpass -f {temp_pass_path} ssh -o StrictHostKeyChecking=no '
                        f'{self.core.username}@{worker_ip} '
                        f'"echo \'{pub_key}\' >> ~/.ssh/authorized_keys && '
                        f'chmod 600 ~/.ssh/authorized_keys && '
                        f'sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys"'
                    )
                    self.core.run_command(cmd)
                    
                    print(f"✓ Successfully copied SSH key to {worker_ip}")
                finally:
                    os.unlink(temp_pass_path)
            except Exception as e:
                print(f"✗ Failed to copy SSH key to {worker_ip}: {e}")
        
        print("\nSSH key distribution completed")
    
    def distribute_ssh_keys_between_all_nodes(self):
        """
        Distribute SSH keys between ALL nodes for full mesh connectivity
        
        Ensures any node can SSH to any other node, required for:
        - MPI to work from any node as head node
        - Multi-homed nodes with multiple network interfaces
        - Flexible cluster topology
        """
        if not self.core.password:
            print("\nSkipping cross-node SSH key distribution (no password)")
            return
        
        print(f"\n{'=' * 60}")
        print("CROSS-NODE SSH KEY DISTRIBUTION")
        print(f"{'=' * 60}")
        print("Ensuring all nodes can SSH to each other...")
        
        # Get all node IPs
        primary_nodes = self.core.all_ips
        node_all_ips = {}
        
        # Collect all IP addresses from each node
        for node_ip in primary_nodes:
            print(f"\nDetecting all IP addresses on {node_ip}...")
            try:
                result = self.core.run_remote_command(
                    node_ip,
                    "ip addr | grep 'inet ' | awk '{print $2}' | cut -d/ -f1",
                    check=False
                )
                
                if result.returncode == 0:
                    ips = [ip.strip() for ip in result.stdout.split('\n') 
                          if ip.strip() and not ip.startswith('127.')]
                    node_all_ips[node_ip] = ips
                    print(f"  Found IPs: {', '.join(ips)}")
                else:
                    node_all_ips[node_ip] = [node_ip]
                    print(f"  Using primary IP: {node_ip}")
            except Exception as e:
                print(f"  Error detecting IPs: {e}")
                node_all_ips[node_ip] = [node_ip]
        
        # Distribute keys from each node to all other nodes
        for source_node in primary_nodes:
            print(f"\n→ Distributing keys FROM {source_node}...")
            
            try:
                # Get public key from source node
                result = self.core.run_remote_command(
                    source_node,
                    "cat ~/.ssh/id_rsa.pub",
                    check=False
                )
                
                if result.returncode != 0 or not result.stdout.strip():
                    print(f"  No public key found, generating...")
                    self.core.run_remote_command(
                        source_node,
                        'ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""',
                        check=False
                    )
                    result = self.core.run_remote_command(
                        source_node,
                        "cat ~/.ssh/id_rsa.pub"
                    )
                
                pub_key = result.stdout.strip()
                
                # Distribute to all other nodes (all their IPs)
                for target_node in primary_nodes:
                    if target_node == source_node:
                        continue
                    
                    target_ips = node_all_ips.get(target_node, [target_node])
                    
                    for target_ip in target_ips:
                        try:
                            # Add key to authorized_keys on target
                            cmd = (
                                f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && "
                                f"echo '{pub_key}' >> ~/.ssh/authorized_keys && "
                                f"chmod 600 ~/.ssh/authorized_keys && "
                                f"sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys"
                            )
                            
                            self.core.run_remote_command(target_ip, cmd, check=False)
                            print(f"  ✓ Key added to {target_ip}")
                        except Exception as e:
                            print(f"  ✗ Failed for {target_ip}: {e}")
            except Exception as e:
                print(f"  ✗ Failed to distribute from {source_node}: {e}")
        
        print(f"\n{'=' * 60}")
        print("Cross-node SSH key distribution completed")
        print(f"{'=' * 60}\n")
