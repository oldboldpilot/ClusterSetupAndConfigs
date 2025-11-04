"""
Sudo Manager Module

Handles passwordless sudo configuration across the cluster.
Uses pdsh for parallel execution across all nodes.
"""

import subprocess
from pathlib import Path
from typing import List, Optional
import re


class SudoManager:
    """Manages sudo configuration for cluster operations"""
    
    def __init__(self, username: str, password: Optional[str] = None, 
                 all_ips: Optional[List[str]] = None):
        """
        Initialize sudo manager
        
        Args:
            username: Username for sudo operations
            password: Password for sudo authentication
            all_ips: List of all cluster node IPs
        """
        self.username = username
        self.password = password
        self.all_ips = all_ips or []
    
    def _get_local_ips(self) -> List[str]:
        """Get all local IP addresses"""
        try:
            result = subprocess.run(
                ['ip', 'addr'], 
                capture_output=True, 
                text=True, 
                check=False
            )
            return re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
        except Exception:
            return []
    
    def _get_other_nodes(self) -> List[str]:
        """Get list of other nodes (excluding current node)"""
        local_ips = self._get_local_ips()
        return [ip for ip in self.all_ips if ip not in local_ips]
    
    def configure_passwordless_sudo_local(self) -> bool:
        """
        Configure passwordless sudo on local node
        
        Returns:
            bool: True if successful, False otherwise
        """
        print("→ Configuring passwordless sudo on local node...")
        
        # Commands that need passwordless sudo
        commands = [
            '/usr/bin/ln', '/bin/ln',
            '/usr/bin/rsync', '/bin/rsync',
            '/usr/bin/systemctl', '/bin/systemctl',
            '/usr/bin/mkdir', '/bin/mkdir',
            '/usr/bin/chmod', '/bin/chmod',
            '/usr/bin/chown', '/bin/chown',
            '/usr/bin/tee', '/bin/tee',
            '/usr/bin/cp', '/bin/cp',
        ]
        
        sudoers_content = f"{self.username} ALL=(ALL) NOPASSWD: {', '.join(commands)}"
        
        try:
            # Create temporary file
            with open('/tmp/cluster-ops-sudoers', 'w') as f:
                f.write(sudoers_content + '\n')
            
            # Copy to sudoers.d with proper permissions
            if self.password:
                sudo_cmd = f"echo '{self.password}' | sudo -S cp /tmp/cluster-ops-sudoers /etc/sudoers.d/cluster-ops"
                subprocess.run(sudo_cmd, shell=True, check=True)
                
                sudo_cmd = f"echo '{self.password}' | sudo -S chmod 440 /etc/sudoers.d/cluster-ops"
                subprocess.run(sudo_cmd, shell=True, check=True)
            else:
                subprocess.run(['sudo', 'cp', '/tmp/cluster-ops-sudoers', '/etc/sudoers.d/cluster-ops'], 
                             check=True)
                subprocess.run(['sudo', 'chmod', '440', '/etc/sudoers.d/cluster-ops'], 
                             check=True)
            
            # Verify syntax
            result = subprocess.run(['sudo', 'visudo', '-c'], capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✓ Passwordless sudo configured on local node")
                return True
            else:
                print("  ⚠ Warning: sudoers syntax check failed, removing configuration")
                subprocess.run(['sudo', 'rm', '-f', '/etc/sudoers.d/cluster-ops'], check=False)
                return False
                
        except Exception as e:
            print(f"  ⚠ Failed to configure local node: {e}")
            return False
    
    def configure_passwordless_sudo_remote(self, node_ip: str) -> bool:
        """
        Configure passwordless sudo on a remote node
        
        Args:
            node_ip: IP address of remote node
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.password:
            print(f"  ⚠ Password required for remote configuration of {node_ip}")
            return False
        
        commands = [
            '/usr/bin/ln', '/bin/ln',
            '/usr/bin/rsync', '/bin/rsync',
            '/usr/bin/systemctl', '/bin/systemctl',
            '/usr/bin/mkdir', '/bin/mkdir',
            '/usr/bin/chmod', '/bin/chmod',
            '/usr/bin/chown', '/bin/chown',
            '/usr/bin/tee', '/bin/tee',
            '/usr/bin/cp', '/bin/cp',
        ]
        
        sudoers_content = f"{self.username} ALL=(ALL) NOPASSWD: {', '.join(commands)}"
        
        try:
            config_cmd = f"""sshpass -p '{self.password}' ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} "echo '{sudoers_content}' | sudo -S tee /tmp/cluster-ops-sudoers > /dev/null && echo '{self.password}' | sudo -S cp /tmp/cluster-ops-sudoers /etc/sudoers.d/cluster-ops && echo '{self.password}' | sudo -S chmod 440 /etc/sudoers.d/cluster-ops && echo '{self.password}' | sudo -S rm -f /tmp/cluster-ops-sudoers" """
            
            result = subprocess.run(config_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✓ Passwordless sudo configured on {node_ip}")
                return True
            else:
                print(f"  ⚠ Failed to configure {node_ip}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ⚠ Failed to configure {node_ip}: {e}")
            return False
    
    def configure_passwordless_sudo_cluster_pdsh(self) -> bool:
        """
        Configure passwordless sudo on all nodes using pdsh for parallel execution
        
        Returns:
            bool: True if all nodes configured successfully
        """
        if not self.password:
            print("⚠ Password required for cluster-wide sudo configuration")
            return False
        
        print("\n=== Configuring Passwordless Sudo on All Cluster Nodes (using pdsh) ===")
        
        # Configure local node first
        local_success = self.configure_passwordless_sudo_local()
        
        # Get other nodes
        other_nodes = self._get_other_nodes()
        
        if not other_nodes:
            print("No other nodes to configure")
            return local_success
        
        # Use pdsh for parallel configuration
        print(f"\n→ Configuring {len(other_nodes)} remote nodes in parallel with pdsh...")
        
        node_list = ','.join(other_nodes)
        
        commands = [
            '/usr/bin/ln', '/bin/ln',
            '/usr/bin/rsync', '/bin/rsync',
            '/usr/bin/systemctl', '/bin/systemctl',
            '/usr/bin/mkdir', '/bin/mkdir',
            '/usr/bin/chmod', '/bin/chmod',
            '/usr/bin/chown', '/bin/chown',
            '/usr/bin/tee', '/bin/tee',
            '/usr/bin/cp', '/bin/cp',
        ]
        
        sudoers_content = f"{self.username} ALL=(ALL) NOPASSWD: {', '.join(commands)}"
        
        # Create sudoers file on all nodes using pdsh
        pdsh_cmd = f"""export PDSH_SSH_ARGS_APPEND="-o StrictHostKeyChecking=no"; pdsh -R ssh -w {node_list} "echo '{self.password}' | sudo -S bash -c 'echo \\"{sudoers_content}\\" > /tmp/cluster-ops-sudoers && cp /tmp/cluster-ops-sudoers /etc/sudoers.d/cluster-ops && chmod 440 /etc/sudoers.d/cluster-ops && rm -f /tmp/cluster-ops-sudoers'" """
        
        try:
            result = subprocess.run(pdsh_cmd, shell=True, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"  ✓ Passwordless sudo configured on all {len(other_nodes)} remote nodes")
                print("\n" + "="*70)
                print("Passwordless Sudo Configuration Complete")
                print("="*70)
                print(f"✓ Configured sudo access for cluster operations")
                print(f"✓ Configuration file: /etc/sudoers.d/cluster-ops")
                print("\nTest with: ssh <node> 'sudo ln --help'")
                print("="*70)
                return True
            else:
                print(f"  ⚠ Some nodes may have failed: {result.stderr}")
                # Fall back to individual configuration
                print("  → Falling back to sequential configuration...")
                success_count = 0
                for node_ip in other_nodes:
                    if self.configure_passwordless_sudo_remote(node_ip):
                        success_count += 1
                
                return success_count == len(other_nodes)
                
        except subprocess.TimeoutExpired:
            print("  ⚠ pdsh command timed out, falling back to sequential configuration")
            success_count = 0
            for node_ip in other_nodes:
                if self.configure_passwordless_sudo_remote(node_ip):
                    success_count += 1
            return success_count == len(other_nodes)
            
        except Exception as e:
            print(f"  ⚠ Error using pdsh: {e}")
            print("  → Falling back to sequential configuration...")
            success_count = 0
            for node_ip in other_nodes:
                if self.configure_passwordless_sudo_remote(node_ip):
                    success_count += 1
            return success_count == len(other_nodes)
    
    def test_passwordless_sudo(self, node_ip: Optional[str] = None) -> bool:
        """
        Test passwordless sudo on a node
        
        Args:
            node_ip: IP address of node to test (None for local)
            
        Returns:
            bool: True if passwordless sudo works
        """
        if node_ip:
            cmd = f"ssh {self.username}@{node_ip} 'sudo -n ln --help > /dev/null 2>&1'"
        else:
            cmd = "sudo -n ln --help > /dev/null 2>&1"
        
        result = subprocess.run(cmd, shell=True, capture_output=True)
        return result.returncode == 0
