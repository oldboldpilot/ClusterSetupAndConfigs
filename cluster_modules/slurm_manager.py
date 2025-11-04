"""
Slurm Manager Module for HPC Cluster Setup

This module handles Slurm workload manager installation and configuration, including:
- Slurm installation via package manager or Homebrew
- slurm.conf configuration file generation
- Cgroups configuration for resource management
- slurmctld (controller) and slurmd (daemon) service management
- Multi-node Slurm cluster setup

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import subprocess
import socket
from pathlib import Path
from typing import List, Optional, Dict


class SlurmManager:
    """
    Manages Slurm workload manager installation and configuration across the cluster.
    
    Attributes:
        username (str): Username for cluster nodes
        password (str): Password for authentication (never hardcoded)
        master_ip (str): Master node IP address (runs slurmctld)
        worker_ips (List[str]): List of worker node IP addresses (run slurmd)
        all_ips (List[str]): All cluster node IPs
        cluster_name (str): Name of the Slurm cluster
    """
    
    def __init__(self, username: str, password: str, master_ip: str, worker_ips: List[str],
                 cluster_name: str = "hpc_cluster"):
        """
        Initialize Slurm manager.
        
        Args:
            username: Username for cluster nodes
            password: Password for authentication
            master_ip: Master node IP address
            worker_ips: List of worker node IP addresses
            cluster_name: Name of the Slurm cluster
        """
        self.username = username
        self.password = password
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
        self.cluster_name = cluster_name
        self.slurm_conf_path = Path("/etc/slurm/slurm.conf")
        self.slurm_user = "slurm"
    
    def install_slurm_local(self) -> bool:
        """
        Install Slurm on local node.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        print("\n=== Installing Slurm locally ===")
        
        # Check if already installed
        slurmctld_check = subprocess.run(["which", "slurmctld"], capture_output=True)
        slurmd_check = subprocess.run(["which", "slurmd"], capture_output=True)
        
        if slurmctld_check.returncode == 0 and slurmd_check.returncode == 0:
            print("✓ Slurm already installed")
            return True
        
        # Try Homebrew installation first
        print("Attempting Homebrew installation...")
        brew_cmd = ["brew", "install", "slurm"]
        
        try:
            result = subprocess.run(brew_cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print("✓ Slurm installed via Homebrew")
                return True
            else:
                print("⚠ Homebrew installation failed, trying system package manager...")
                
        except Exception as e:
            print(f"⚠ Homebrew installation error: {e}")
        
        # Try system package manager
        os_type = self._detect_os()
        
        if os_type == "ubuntu" or os_type == "debian":
            pkg_cmd = ["sudo", "apt-get", "install", "-y", "slurm-wlm"]
        elif os_type == "redhat" or os_type == "centos":
            pkg_cmd = ["sudo", "yum", "install", "-y", "slurm", "slurm-slurmd", "slurm-slurmctld"]
        else:
            print(f"✗ Unsupported OS: {os_type}")
            return False
        
        print(f"Installing via system package manager ({os_type})...")
        
        try:
            result = subprocess.run(pkg_cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print(f"✓ Slurm installed via {os_type} package manager")
                return True
            else:
                print(f"✗ System package installation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error installing Slurm: {e}")
            return False
    
    def install_slurm_cluster_pdsh(self) -> bool:
        """
        Install Slurm on all cluster nodes using pdsh.
        
        Returns:
            bool: True if installation successful on all nodes, False otherwise
        """
        print("\n=== Installing Slurm cluster-wide with pdsh ===")
        
        # Install locally first
        if not self.install_slurm_local():
            print("Failed to install Slurm locally, aborting cluster installation")
            return False
        
        # Get other nodes
        other_nodes = [ip for ip in self.all_ips if ip != self._get_local_ip()]
        
        if not other_nodes:
            print("No other nodes to install on")
            return True
        
        node_list = ",".join(other_nodes)
        
        # Determine OS type for package command
        os_type = self._detect_os()
        
        if os_type == "ubuntu" or os_type == "debian":
            install_cmd = "sudo apt-get update && sudo apt-get install -y slurm-wlm"
        elif os_type == "redhat" or os_type == "centos":
            install_cmd = "sudo yum install -y slurm slurm-slurmd slurm-slurmctld"
        else:
            install_cmd = "brew install slurm"
        
        pdsh_cmd = [
            "pdsh",
            "-R", "ssh",
            "-w", node_list,
            install_cmd
        ]
        
        print(f"Installing Slurm on nodes: {node_list}")
        
        try:
            result = subprocess.run(pdsh_cmd, capture_output=True, text=True, timeout=900)
            
            if result.returncode == 0:
                print("✓ Slurm installed on all nodes")
                return True
            else:
                print("⚠ pdsh installation had issues, falling back to sequential")
                return self._install_slurm_sequential(other_nodes)
                
        except Exception as e:
            print(f"⚠ pdsh failed ({e}), falling back to sequential")
            return self._install_slurm_sequential(other_nodes)
    
    def _install_slurm_sequential(self, nodes: List[str]) -> bool:
        """
        Install Slurm sequentially on specified nodes.
        
        Args:
            nodes: List of node IPs to install on
            
        Returns:
            bool: True if all installations successful, False otherwise
        """
        os_type = self._detect_os()
        all_success = True
        
        for node_ip in nodes:
            print(f"\nInstalling Slurm on {node_ip}...")
            
            if os_type == "ubuntu" or os_type == "debian":
                install_cmd = "sudo apt-get update && sudo apt-get install -y slurm-wlm"
            elif os_type == "redhat" or os_type == "centos":
                install_cmd = "sudo yum install -y slurm slurm-slurmd slurm-slurmctld"
            else:
                install_cmd = "brew install slurm"
            
            ssh_cmd = [
                "sshpass", "-p", self.password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"{self.username}@{node_ip}",
                install_cmd
            ]
            
            try:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    print(f"✓ Slurm installed on {node_ip}")
                else:
                    print(f"✗ Failed to install on {node_ip}")
                    all_success = False
                    
            except Exception as e:
                print(f"✗ Error installing on {node_ip}: {e}")
                all_success = False
        
        return all_success
    
    def generate_slurm_conf(self, node_info: Dict[str, Dict]) -> str:
        """
        Generate slurm.conf configuration file content.
        
        Args:
            node_info: Dictionary mapping node IPs to their info (hostname, threads, memory)
                      Example: {'192.168.1.147': {'hostname': 'master', 'threads': 32, 'memory': 64000}}
        
        Returns:
            str: Content of slurm.conf file
        """
        print("\n=== Generating slurm.conf ===")
        
        # Get master hostname
        master_hostname = node_info.get(self.master_ip, {}).get('hostname', 'master')
        
        conf_lines = [
            f"# slurm.conf - Generated by ClusterSetup",
            f"# Cluster: {self.cluster_name}",
            "",
            f"ClusterName={self.cluster_name}",
            f"SlurmctldHost={master_hostname}({self.master_ip})",
            "",
            "# Authentication",
            "AuthType=auth/munge",
            "CryptoType=crypto/munge",
            "",
            "# Scheduling",
            "SchedulerType=sched/backfill",
            "SelectType=select/cons_tres",
            "SelectTypeParameters=CR_Core_Memory",
            "",
            "# Logging",
            "SlurmctldDebug=info",
            "SlurmctldLogFile=/var/log/slurm/slurmctld.log",
            "SlurmdDebug=info",
            "SlurmdLogFile=/var/log/slurm/slurmd.log",
            "",
            "# Process tracking",
            "ProctrackType=proctrack/cgroup",
            "TaskPlugin=task/cgroup",
            "",
            "# State preservation",
            "StateSaveLocation=/var/spool/slurm/ctld",
            "SlurmdSpoolDir=/var/spool/slurm/d",
            "",
            "# Return to service",
            "ReturnToService=1",
            "",
            "# MPI support",
            "MpiDefault=pmix",
            "",
            "# Node definitions",
        ]
        
        # Add node definitions
        for ip, info in node_info.items():
            hostname = info.get('hostname', ip.replace('.', '-'))
            threads = info.get('threads', 1)
            memory = info.get('memory', 1000)  # MB
            
            conf_lines.append(
                f"NodeName={hostname} NodeAddr={ip} CPUs={threads} "
                f"RealMemory={memory} State=UNKNOWN"
            )
        
        conf_lines.extend([
            "",
            "# Partition definitions",
            f"PartitionName=all Nodes=ALL Default=YES MaxTime=INFINITE State=UP",
        ])
        
        return "\n".join(conf_lines)
    
    def write_slurm_conf(self, node_info: Dict[str, Dict]) -> bool:
        """
        Generate and write slurm.conf to /etc/slurm/.
        
        Args:
            node_info: Dictionary mapping node IPs to their info
            
        Returns:
            bool: True if configuration written successfully, False otherwise
        """
        print("\n=== Writing slurm.conf ===")
        
        conf_content = self.generate_slurm_conf(node_info)
        
        # Create /etc/slurm directory if it doesn't exist
        slurm_etc_dir = self.slurm_conf_path.parent
        
        mkdir_cmd = ["sudo", "mkdir", "-p", str(slurm_etc_dir)]
        subprocess.run(mkdir_cmd, capture_output=True)
        
        # Write configuration file
        temp_conf = Path("/tmp/slurm.conf")
        temp_conf.write_text(conf_content)
        
        copy_cmd = ["sudo", "cp", str(temp_conf), str(self.slurm_conf_path)]
        
        try:
            result = subprocess.run(copy_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✓ slurm.conf written to {self.slurm_conf_path}")
                
                # Set permissions
                chmod_cmd = ["sudo", "chmod", "644", str(self.slurm_conf_path)]
                subprocess.run(chmod_cmd, capture_output=True)
                
                return True
            else:
                print(f"✗ Failed to write slurm.conf: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error writing slurm.conf: {e}")
            return False
    
    def distribute_slurm_conf_pdsh(self) -> bool:
        """
        Distribute slurm.conf to all cluster nodes using pdsh.
        
        Returns:
            bool: True if distribution successful, False otherwise
        """
        print("\n=== Distributing slurm.conf cluster-wide ===")
        
        if not self.slurm_conf_path.exists():
            print(f"✗ slurm.conf not found at {self.slurm_conf_path}")
            return False
        
        other_nodes = [ip for ip in self.all_ips if ip != self._get_local_ip()]
        
        if not other_nodes:
            print("No other nodes to distribute to")
            return True
        
        all_success = True
        
        for node_ip in other_nodes:
            print(f"\nDistributing slurm.conf to {node_ip}...")
            
            # Create /etc/slurm directory on remote node
            mkdir_cmd = [
                "sshpass", "-p", self.password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"{self.username}@{node_ip}",
                "sudo mkdir -p /etc/slurm"
            ]
            
            subprocess.run(mkdir_cmd, capture_output=True)
            
            # Copy slurm.conf
            scp_cmd = [
                "sshpass", "-p", self.password,
                "scp", "-o", "StrictHostKeyChecking=no",
                str(self.slurm_conf_path),
                f"{self.username}@{node_ip}:/tmp/slurm.conf"
            ]
            
            result = subprocess.run(scp_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Move to /etc/slurm with sudo
                move_cmd = [
                    "sshpass", "-p", self.password,
                    "ssh", "-o", "StrictHostKeyChecking=no",
                    f"{self.username}@{node_ip}",
                    "sudo mv /tmp/slurm.conf /etc/slurm/slurm.conf && sudo chmod 644 /etc/slurm/slurm.conf"
                ]
                
                move_result = subprocess.run(move_cmd, capture_output=True, text=True)
                
                if move_result.returncode == 0:
                    print(f"✓ slurm.conf distributed to {node_ip}")
                else:
                    print(f"✗ Failed to move slurm.conf on {node_ip}")
                    all_success = False
            else:
                print(f"✗ Failed to copy slurm.conf to {node_ip}")
                all_success = False
        
        return all_success
    
    def start_slurmctld(self) -> bool:
        """
        Start slurmctld service on master node.
        
        Returns:
            bool: True if service started successfully, False otherwise
        """
        print("\n=== Starting slurmctld service ===")
        
        # Check if systemctl is available
        systemctl_check = subprocess.run(["which", "systemctl"], capture_output=True)
        
        if systemctl_check.returncode == 0:
            start_cmd = ["sudo", "systemctl", "start", "slurmctld"]
            enable_cmd = ["sudo", "systemctl", "enable", "slurmctld"]
            
            try:
                # Start service
                result = subprocess.run(start_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✓ slurmctld started")
                    
                    # Enable on boot
                    subprocess.run(enable_cmd, capture_output=True)
                    print("✓ slurmctld enabled on boot")
                    return True
                else:
                    print(f"✗ Failed to start slurmctld: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"✗ Error starting slurmctld: {e}")
                return False
        else:
            print("⚠ systemctl not available, start slurmctld manually")
            return False
    
    def start_slurmd_cluster_pdsh(self) -> bool:
        """
        Start slurmd service on all worker nodes using pdsh.
        
        Returns:
            bool: True if service started on all nodes, False otherwise
        """
        print("\n=== Starting slurmd on all nodes ===")
        
        all_success = True
        
        for node_ip in self.all_ips:
            print(f"\nStarting slurmd on {node_ip}...")
            
            if node_ip == self._get_local_ip():
                # Local node
                start_cmd = ["sudo", "systemctl", "start", "slurmd"]
                enable_cmd = ["sudo", "systemctl", "enable", "slurmd"]
                
                result = subprocess.run(start_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✓ slurmd started on local node")
                    subprocess.run(enable_cmd, capture_output=True)
                else:
                    print(f"✗ Failed to start slurmd on local node")
                    all_success = False
            else:
                # Remote node
                ssh_cmd = [
                    "sshpass", "-p", self.password,
                    "ssh", "-o", "StrictHostKeyChecking=no",
                    f"{self.username}@{node_ip}",
                    "sudo systemctl start slurmd && sudo systemctl enable slurmd"
                ]
                
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print(f"✓ slurmd started on {node_ip}")
                else:
                    print(f"✗ Failed to start slurmd on {node_ip}")
                    all_success = False
        
        return all_success
    
    def test_slurm_cluster(self) -> bool:
        """
        Test Slurm cluster by running sinfo and squeue.
        
        Returns:
            bool: True if tests successful, False otherwise
        """
        print("\n=== Testing Slurm Cluster ===")
        
        # Test sinfo
        sinfo_cmd = ["sinfo"]
        
        print("Running sinfo...")
        result = subprocess.run(sinfo_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ sinfo successful:")
            print(result.stdout)
        else:
            print(f"✗ sinfo failed: {result.stderr}")
            return False
        
        # Test squeue
        squeue_cmd = ["squeue"]
        
        print("\nRunning squeue...")
        result = subprocess.run(squeue_cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✓ squeue successful:")
            print(result.stdout)
            return True
        else:
            print(f"✗ squeue failed: {result.stderr}")
            return False
    
    def _detect_os(self) -> str:
        """
        Detect operating system type.
        
        Returns:
            str: OS type ('ubuntu', 'debian', 'redhat', 'centos', or 'unknown')
        """
        try:
            if Path("/etc/os-release").exists():
                with open("/etc/os-release") as f:
                    content = f.read().lower()
                    if "ubuntu" in content:
                        return "ubuntu"
                    elif "debian" in content:
                        return "debian"
                    elif "red hat" in content or "rhel" in content:
                        return "redhat"
                    elif "centos" in content:
                        return "centos"
            
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def _get_local_ip(self) -> Optional[str]:
        """
        Get local node IP address.
        
        Returns:
            Optional[str]: Local IP address or None if not found
        """
        try:
            hostname_result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
            if hostname_result.returncode == 0:
                local_ips = hostname_result.stdout.strip().split()
                for ip in local_ips:
                    if ip in self.all_ips:
                        return ip
            return self.master_ip
        except Exception:
            return self.master_ip


if __name__ == "__main__":
    print("Slurm Manager Module")
    print("Import this module to use SlurmManager class")
