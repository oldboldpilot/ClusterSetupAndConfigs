"""
Core cluster functionality - base class and utilities

Provides:
- OS detection (Ubuntu, Red Hat, WSL)
- Command execution (local and remote with sudo)
- Node identification and hostname resolution
- Package manager detection
"""

import subprocess
import os
import socket
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any


class ClusterCore:
    """Core cluster functionality and utilities"""
    
    def __init__(self, master_ip: str, worker_ips: List[str], 
                 username: Optional[str] = None, password: Optional[str] = None):
        """
        Initialize cluster core
        
        Args:
            master_ip: IP address of master node
            worker_ips: List of worker node IP addresses
            username: SSH username (default: current user)
            password: Password for sudo and SSH operations
        """
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
        self.username = username or os.getenv('USER', 'ubuntu')
        self.password = password
        self.os_type = self._detect_os()
        self.pkg_manager = 'dnf' if self.os_type == 'redhat' else 'apt-get'
        self.is_master = self._is_current_node_master()
        self.master_hostname = self._get_master_hostname()
    
    def _detect_os(self) -> str:
        """Detect operating system type
        
        Returns:
            'ubuntu' for Debian/Ubuntu, 'redhat' for RHEL/Fedora/CentOS
        """
        try:
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'red hat' in content or 'rhel' in content or \
                       'fedora' in content or 'centos' in content:
                        return 'redhat'
                    elif 'ubuntu' in content or 'debian' in content:
                        return 'ubuntu'
            
            # Fallback: check for package managers
            if shutil.which('dnf'):
                return 'redhat'
            elif shutil.which('apt-get'):
                return 'ubuntu'
        except Exception as e:
            print(f"DEBUG: Error detecting OS: {e}")
        
        return 'ubuntu'  # Default
    
    def _is_wsl(self) -> bool:
        """Check if running on Windows Subsystem for Linux"""
        try:
            with open('/proc/version', 'r') as f:
                version = f.read().lower()
                return 'microsoft' in version or 'wsl' in version
        except:
            return False
    
    def _is_current_node_master(self) -> bool:
        """Check if current node is the master node"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Check if local IP matches master IP
            if local_ip == self.master_ip:
                return True
            
            # Check all network interfaces
            result = subprocess.run(['ip', 'addr'], capture_output=True, 
                                   text=True, check=False)
            if result.returncode == 0:
                import re
                local_ips = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                if self.master_ip in local_ips:
                    return True
            
            return False
        except Exception as e:
            print(f"DEBUG: Error detecting if master: {e}")
            return False
    
    def _get_master_hostname(self) -> str:
        """Get hostname of master node
        
        Returns:
            Hostname string or master IP if cannot resolve
        """
        if self.is_master:
            return socket.gethostname()
        
        # Try to get hostname from master node via SSH
        if self.password:
            try:
                result = self.run_remote_command(
                    self.master_ip, "hostname", check=False
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
        
        return self.master_ip
    
    def get_local_ips(self) -> List[str]:
        """Get all local IP addresses of current node
        
        Returns:
            List of IP addresses
        """
        try:
            result = subprocess.run(['ip', 'addr'], capture_output=True,
                                   text=True, check=False)
            if result.returncode == 0:
                import re
                return re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
        except:
            pass
        
        return []
    
    def run_command(self, command: str, check: bool = True, 
                   shell: bool = True) -> subprocess.CompletedProcess:
        """Execute command locally
        
        Args:
            command: Shell command to execute
            check: Raise exception on non-zero exit code
            shell: Execute through shell
            
        Returns:
            CompletedProcess instance with stdout, stderr, returncode
        """
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return subprocess.CompletedProcess(
                args=e.cmd,
                returncode=e.returncode,
                stdout=e.stdout or '',
                stderr=e.stderr or ''
            )
    
    def run_sudo_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Execute command with sudo privileges
        
        Args:
            command: Command to execute with sudo
            check: Raise exception on non-zero exit code
            
        Returns:
            CompletedProcess instance
        """
        if self.password:
            # Use sudo -S to read password from stdin
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
                print(f"Error executing: {sudo_cmd}")
                print(f"Error output: {stderr}")
                raise subprocess.CalledProcessError(
                    result.returncode, sudo_cmd, stdout, stderr
                )
            
            return result
        else:
            # Try without password (may prompt user)
            if 'SUDO_ASKPASS' in os.environ and os.path.exists(os.environ['SUDO_ASKPASS']):
                return self.run_command(f"sudo -A {command}", check=check)
            else:
                return self.run_command(f"sudo {command}", check=check)
    
    def run_remote_command(self, node_ip: str, command: str, 
                          check: bool = True) -> subprocess.CompletedProcess:
        """Execute command on remote node via SSH
        
        Args:
            node_ip: IP address of remote node
            command: Command to execute
            check: Raise exception on non-zero exit code
            
        Returns:
            CompletedProcess instance
        """
        if self.password:
            ssh_cmd = (
                f"sshpass -p '{self.password}' ssh -o StrictHostKeyChecking=no "
                f"{self.username}@{node_ip} '{command}'"
            )
        else:
            ssh_cmd = f"ssh -o StrictHostKeyChecking=no {self.username}@{node_ip} '{command}'"
        
        return self.run_command(ssh_cmd, check=check)
    
    def run_remote_sudo_command(self, node_ip: str, command: str,
                               check: bool = True) -> subprocess.CompletedProcess:
        """Execute sudo command on remote node
        
        Args:
            node_ip: IP address of remote node
            command: Command to execute with sudo
            check: Raise exception on non-zero exit code
            
        Returns:
            CompletedProcess instance
        """
        if self.password:
            # Pipe password to sudo on remote node
            remote_cmd = f"echo '{self.password}' | sudo -S {command}"
            return self.run_remote_command(node_ip, remote_cmd, check=check)
        else:
            return self.run_remote_command(node_ip, f"sudo {command}", check=check)
    
    def check_sudo_access(self) -> bool:
        """Check if user has sudo access without password
        
        Returns:
            True if passwordless sudo is configured
        """
        result = self.run_command("sudo -n true", check=False)
        return result.returncode == 0
    
    def get_node_info(self) -> Dict[str, Any]:
        """Get information about current node
        
        Returns:
            Dictionary with node information
        """
        return {
            'hostname': socket.gethostname(),
            'os_type': self.os_type,
            'pkg_manager': self.pkg_manager,
            'is_master': self.is_master,
            'is_wsl': self._is_wsl(),
            'local_ips': self.get_local_ips(),
        }
