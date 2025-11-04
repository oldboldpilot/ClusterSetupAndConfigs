"""
PDSH Manager Module for HPC Cluster Setup

This module handles pdsh (Parallel Distributed Shell) installation and configuration:
- pdsh installation via Homebrew and system package managers
- Cluster-wide pdsh deployment
- pdsh configuration and testing
- Host file management for pdsh

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import subprocess
from pathlib import Path
from typing import List, Optional


class PDSHManager:
    """
    Manages pdsh installation and configuration across the cluster.
    
    pdsh (Parallel Distributed Shell) enables parallel command execution across multiple nodes,
    significantly speeding up cluster-wide operations compared to sequential SSH.
    
    Attributes:
        username (str): Username for cluster nodes
        password (str): Password for authentication (never hardcoded)
        master_ip (str): Master node IP address
        worker_ips (List[str]): List of worker node IP addresses
        all_ips (List[str]): All cluster node IPs
    """
    
    def __init__(self, username: str, password: str, master_ip: str, worker_ips: List[str]):
        """
        Initialize PDSH manager.
        
        Args:
            username: Username for cluster nodes
            password: Password for authentication
            master_ip: Master node IP address
            worker_ips: List of worker node IP addresses
        """
        self.username = username
        self.password = password
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
    
    def is_pdsh_installed(self) -> bool:
        """
        Check if pdsh is installed on the local system.
        
        Returns:
            bool: True if pdsh is installed, False otherwise
        """
        try:
            result = subprocess.run(['which', 'pdsh'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def install_pdsh_local(self) -> bool:
        """
        Install pdsh on the local machine using Homebrew or system package manager.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        print("\n=== Installing pdsh Locally ===")
        
        if self.is_pdsh_installed():
            print("✓ pdsh is already installed")
            return True
        
        # Try Homebrew first (works on macOS and Linux)
        if self._is_homebrew_available():
            return self._install_pdsh_homebrew()
        
        # Try system package manager
        return self._install_pdsh_system()
    
    def _is_homebrew_available(self) -> bool:
        """
        Check if Homebrew is available.
        
        Returns:
            bool: True if Homebrew is installed
        """
        try:
            result = subprocess.run(['which', 'brew'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
    
    def _install_pdsh_homebrew(self) -> bool:
        """
        Install pdsh using Homebrew.
        
        Returns:
            bool: True if installation successful
        """
        print("Installing pdsh via Homebrew...")
        
        try:
            result = subprocess.run(
                ['brew', 'install', 'pdsh'],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print("✓ pdsh installed via Homebrew")
                return True
            else:
                print(f"✗ Homebrew installation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Installation timed out")
            return False
        except Exception as e:
            print(f"✗ Error installing via Homebrew: {e}")
            return False
    
    def _install_pdsh_system(self) -> bool:
        """
        Install pdsh using system package manager (apt, yum, dnf).
        
        Returns:
            bool: True if installation successful
        """
        print("Installing pdsh via system package manager...")
        
        # Detect package manager
        pkg_managers = [
            (['apt-get', 'install', '-y', 'pdsh'], 'apt-get'),
            (['yum', 'install', '-y', 'pdsh'], 'yum'),
            (['dnf', 'install', '-y', 'pdsh'], 'dnf'),
            (['zypper', 'install', '-y', 'pdsh'], 'zypper')
        ]
        
        for cmd, name in pkg_managers:
            # Check if package manager exists
            check_result = subprocess.run(
                ['which', cmd[0]], 
                capture_output=True
            )
            
            if check_result.returncode == 0:
                print(f"Using {name}...")
                try:
                    result = subprocess.run(
                        ['sudo'] + cmd,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    
                    if result.returncode == 0:
                        print(f"✓ pdsh installed via {name}")
                        return True
                    else:
                        print(f"✗ {name} installation failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    print(f"✗ {name} installation timed out")
                except Exception as e:
                    print(f"✗ Error with {name}: {e}")
        
        print("✗ No supported package manager found")
        return False
    
    def install_pdsh_cluster_sequential(self) -> bool:
        """
        Install pdsh on all cluster nodes sequentially using SSH.
        Use this method for initial cluster setup before pdsh is available.
        
        Returns:
            bool: True if installation successful on all nodes, False otherwise
        """
        print("\n=== Installing pdsh on Cluster (Sequential) ===")
        
        success = True
        
        for ip in self.all_ips:
            print(f"\nInstalling on {ip}...")
            
            try:
                # Check if Homebrew is available
                check_brew = subprocess.run(
                    ['ssh', f'{self.username}@{ip}', 'which brew'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if check_brew.returncode == 0:
                    # Install via Homebrew
                    cmd = ['ssh', f'{self.username}@{ip}', 'brew install pdsh']
                else:
                    # Try system package manager (requires sudo)
                    cmd = ['ssh', f'{self.username}@{ip}', 
                          'sudo apt-get install -y pdsh || sudo yum install -y pdsh || sudo dnf install -y pdsh']
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode == 0:
                    print(f"✓ Installed pdsh on {ip}")
                else:
                    print(f"✗ Failed to install pdsh on {ip}")
                    print(f"  Error: {result.stderr}")
                    success = False
                    
            except subprocess.TimeoutExpired:
                print(f"✗ Installation timed out on {ip}")
                success = False
            except Exception as e:
                print(f"✗ Error installing on {ip}: {e}")
                success = False
        
        return success
    
    def create_hostfile(self, hostfile_path: Optional[Path] = None) -> bool:
        """
        Create a hostfile for pdsh with all cluster nodes.
        
        Args:
            hostfile_path: Optional custom path for hostfile. 
                          Defaults to ~/.pdsh/machines
        
        Returns:
            bool: True if hostfile created successfully, False otherwise
        """
        print("\n=== Creating PDSH Hostfile ===")
        
        if hostfile_path is None:
            hostfile_path = Path.home() / ".pdsh" / "machines"
        
        try:
            hostfile_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write all node IPs to hostfile
            with hostfile_path.open('w') as f:
                for ip in self.all_ips:
                    f.write(f"{ip}\n")
            
            print(f"✓ Created pdsh hostfile: {hostfile_path}")
            print(f"  Nodes: {len(self.all_ips)}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating hostfile: {e}")
            return False
    
    def test_pdsh_connectivity(self) -> bool:
        """
        Test pdsh connectivity to all cluster nodes.
        
        Returns:
            bool: True if pdsh can reach all nodes, False otherwise
        """
        print("\n=== Testing PDSH Connectivity ===")
        
        if not self.is_pdsh_installed():
            print("✗ pdsh is not installed")
            return False
        
        try:
            hosts = ','.join(self.all_ips)
            
            result = subprocess.run(
                ['pdsh', '-w', hosts, 'hostname'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✓ pdsh connectivity test passed")
                print(f"  Output:\n{result.stdout}")
                return True
            else:
                print(f"✗ pdsh connectivity test failed")
                print(f"  Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ pdsh connectivity test timed out")
            return False
        except Exception as e:
            print(f"✗ Error testing pdsh: {e}")
            return False
    
    def run_pdsh_command(self, command: str, hosts: Optional[List[str]] = None) -> Optional[str]:
        """
        Run a command on multiple hosts using pdsh.
        
        Args:
            command: Command to execute on remote hosts
            hosts: Optional list of host IPs. Uses all_ips if not provided.
        
        Returns:
            Optional[str]: Command output if successful, None otherwise
        """
        if hosts is None:
            hosts = self.all_ips
        
        if not self.is_pdsh_installed():
            print("✗ pdsh is not installed")
            return None
        
        try:
            hosts_str = ','.join(hosts)
            
            result = subprocess.run(
                ['pdsh', '-w', hosts_str, command],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"✗ pdsh command failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("✗ pdsh command timed out")
            return None
        except Exception as e:
            print(f"✗ Error running pdsh command: {e}")
            return None
    
    def configure_pdsh_environment(self) -> bool:
        """
        Configure pdsh environment variables for optimal operation.
        
        Sets PDSH_RCMD_TYPE=ssh for SSH-based connections.
        
        Returns:
            bool: True if configuration successful
        """
        print("\n=== Configuring PDSH Environment ===")
        
        try:
            # Check if PDSH_RCMD_TYPE is already set
            current_env = subprocess.run(
                ['bash', '-c', 'echo $PDSH_RCMD_TYPE'],
                capture_output=True,
                text=True
            )
            
            if current_env.stdout.strip() == 'ssh':
                print("✓ PDSH_RCMD_TYPE already set to ssh")
                return True
            
            # Add to shell profile
            shell_profile = Path.home() / ".bashrc"
            export_line = "export PDSH_RCMD_TYPE=ssh\n"
            
            with shell_profile.open('a') as f:
                f.write(f"\n# pdsh configuration\n{export_line}")
            
            print(f"✓ Added PDSH_RCMD_TYPE=ssh to {shell_profile}")
            print("  Note: Restart shell or run: source ~/.bashrc")
            return True
            
        except Exception as e:
            print(f"✗ Error configuring pdsh environment: {e}")
            return False
    
    def install_and_configure_cluster(self) -> bool:
        """
        Complete installation and configuration of pdsh across the cluster.
        
        This is the main method to call for full pdsh setup:
        1. Install pdsh locally
        2. Install pdsh on all cluster nodes
        3. Create hostfile
        4. Configure environment
        5. Test connectivity
        
        Returns:
            bool: True if all steps successful, False otherwise
        """
        print("\n=== Complete PDSH Cluster Setup ===")
        
        steps = [
            ("Installing pdsh locally", self.install_pdsh_local),
            ("Installing pdsh on cluster", self.install_pdsh_cluster_sequential),
            ("Creating hostfile", self.create_hostfile),
            ("Configuring environment", self.configure_pdsh_environment),
            ("Testing connectivity", self.test_pdsh_connectivity)
        ]
        
        for step_name, step_func in steps:
            print(f"\n--- {step_name} ---")
            if not step_func():
                print(f"\n✗ Failed at step: {step_name}")
                return False
        
        print("\n✓ PDSH cluster setup completed successfully!")
        return True
