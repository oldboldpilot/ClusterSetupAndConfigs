"""
Network Manager Module for HPC Cluster Setup

This module handles network and firewall configuration across the cluster, including:
- Firewall configuration (UFW for Ubuntu/Debian, firewalld for Red Hat/CentOS)
- Opening ports for MPI, Slurm, SSH, and other cluster services
- /etc/hosts file management for hostname resolution
- Network interface configuration
- DNS settings

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional


class NetworkManager:
    """
    Manages network and firewall configuration across the cluster.
    
    Attributes:
        username (str): Username for cluster nodes
        password (str): Password for authentication (never hardcoded)
        master_ip (str): Master node IP address
        worker_ips (List[str]): List of worker node IP addresses
        all_ips (List[str]): All cluster node IPs
        node_hostnames (Dict[str, str]): Mapping of IPs to hostnames
    """
    
    def __init__(self, username: str, password: str, master_ip: str, worker_ips: List[str],
                 node_hostnames: Optional[Dict[str, str]] = None):
        """
        Initialize Network manager.
        
        Args:
            username: Username for cluster nodes
            password: Password for authentication
            master_ip: Master node IP address
            worker_ips: List of worker node IP addresses
            node_hostnames: Optional mapping of IPs to hostnames
        """
        self.username = username
        self.password = password
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
        self.node_hostnames = node_hostnames or self._generate_default_hostnames()
        
        # Port ranges for different services
        self.mpi_ports = (50000, 50200)
        self.slurm_ports = [6817, 6818, 6819]  # slurmctld, slurmd, slurmdbd
        self.ssh_port = 22
    
    def _generate_default_hostnames(self) -> Dict[str, str]:
        """
        Generate default hostnames for nodes.
        
        Returns:
            Dict[str, str]: Mapping of IPs to hostnames
        """
        hostnames = {}
        hostnames[self.master_ip] = "master"
        
        for i, worker_ip in enumerate(self.worker_ips, 1):
            hostnames[worker_ip] = f"worker{i}"
        
        return hostnames
    
    def detect_firewall_type(self) -> str:
        """
        Detect which firewall system is in use.
        
        Returns:
            str: 'ufw', 'firewalld', or 'none'
        """
        # Check for UFW (Ubuntu/Debian)
        ufw_check = subprocess.run(["which", "ufw"], capture_output=True)
        if ufw_check.returncode == 0:
            return "ufw"
        
        # Check for firewalld (Red Hat/CentOS)
        firewalld_check = subprocess.run(["which", "firewall-cmd"], capture_output=True)
        if firewalld_check.returncode == 0:
            return "firewalld"
        
        return "none"
    
    def configure_firewall_local(self) -> bool:
        """
        Configure firewall on local node to allow cluster traffic.
        
        Returns:
            bool: True if configuration successful, False otherwise
        """
        print("\n=== Configuring Firewall locally ===")
        
        firewall_type = self.detect_firewall_type()
        print(f"Detected firewall: {firewall_type}")
        
        if firewall_type == "ufw":
            return self._configure_ufw_local()
        elif firewall_type == "firewalld":
            return self._configure_firewalld_local()
        else:
            print("⚠ No firewall detected or firewall not supported")
            return True
    
    def _configure_ufw_local(self) -> bool:
        """
        Configure UFW firewall on local node.
        
        Returns:
            bool: True if configuration successful, False otherwise
        """
        print("Configuring UFW...")
        
        commands = [
            # Allow SSH
            ["sudo", "ufw", "allow", str(self.ssh_port)],
            
            # Allow MPI port range
            ["sudo", "ufw", "allow", f"{self.mpi_ports[0]}:{self.mpi_ports[1]}/tcp"],
            ["sudo", "ufw", "allow", f"{self.mpi_ports[0]}:{self.mpi_ports[1]}/udp"],
            
            # Allow Slurm ports
            *[["sudo", "ufw", "allow", str(port)] for port in self.slurm_ports],
            
            # Allow traffic from cluster nodes
            *[["sudo", "ufw", "allow", "from", ip] for ip in self.all_ips],
            
            # Enable UFW
            ["sudo", "ufw", "--force", "enable"],
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    print(f"⚠ Warning: {' '.join(cmd)} failed: {result.stderr}")
            except Exception as e:
                print(f"⚠ Warning configuring UFW: {e}")
        
        # Check UFW status
        status_cmd = ["sudo", "ufw", "status", "verbose"]
        result = subprocess.run(status_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ UFW configured successfully")
            print(result.stdout)
            return True
        else:
            print("✗ Failed to get UFW status")
            return False
    
    def _configure_firewalld_local(self) -> bool:
        """
        Configure firewalld on local node.
        
        Returns:
            bool: True if configuration successful, False otherwise
        """
        print("Configuring firewalld...")
        
        commands = [
            # Start firewalld
            ["sudo", "systemctl", "start", "firewalld"],
            
            # Allow SSH
            ["sudo", "firewall-cmd", "--permanent", "--add-service=ssh"],
            
            # Allow MPI port range
            ["sudo", "firewall-cmd", "--permanent", 
             f"--add-port={self.mpi_ports[0]}-{self.mpi_ports[1]}/tcp"],
            ["sudo", "firewall-cmd", "--permanent",
             f"--add-port={self.mpi_ports[0]}-{self.mpi_ports[1]}/udp"],
            
            # Allow Slurm ports
            *[["sudo", "firewall-cmd", "--permanent", f"--add-port={port}/tcp"] 
              for port in self.slurm_ports],
            
            # Add cluster nodes to trusted zone
            *[["sudo", "firewall-cmd", "--permanent", 
               "--zone=trusted", f"--add-source={ip}"] for ip in self.all_ips],
            
            # Reload firewall
            ["sudo", "firewall-cmd", "--reload"],
        ]
        
        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    print(f"⚠ Warning: {' '.join(cmd)} failed: {result.stderr}")
            except Exception as e:
                print(f"⚠ Warning configuring firewalld: {e}")
        
        # Check firewalld status
        status_cmd = ["sudo", "firewall-cmd", "--list-all"]
        result = subprocess.run(status_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ firewalld configured successfully")
            print(result.stdout)
            return True
        else:
            print("✗ Failed to get firewalld status")
            return False
    
    def configure_firewall_cluster_pdsh(self) -> bool:
        """
        Configure firewall on all cluster nodes using pdsh.
        
        Returns:
            bool: True if configuration successful on all nodes, False otherwise
        """
        print("\n=== Configuring Firewall cluster-wide ===")
        
        # Configure locally first
        if not self.configure_firewall_local():
            print("Failed to configure firewall locally")
            return False
        
        # Get other nodes
        other_nodes = [ip for ip in self.all_ips if ip != self._get_local_ip()]
        
        if not other_nodes:
            print("No other nodes to configure")
            return True
        
        firewall_type = self.detect_firewall_type()
        all_success = True
        
        for node_ip in other_nodes:
            print(f"\nConfiguring firewall on {node_ip}...")
            
            if firewall_type == "ufw":
                config_script = self._generate_ufw_script()
            elif firewall_type == "firewalld":
                config_script = self._generate_firewalld_script()
            else:
                print(f"⚠ Skipping {node_ip} - no firewall support")
                continue
            
            # Execute configuration script on remote node
            ssh_cmd = [
                "sshpass", "-p", self.password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"{self.username}@{node_ip}",
                config_script
            ]
            
            try:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"✓ Firewall configured on {node_ip}")
                else:
                    print(f"✗ Failed to configure firewall on {node_ip}")
                    all_success = False
                    
            except Exception as e:
                print(f"✗ Error configuring firewall on {node_ip}: {e}")
                all_success = False
        
        return all_success
    
    def _generate_ufw_script(self) -> str:
        """
        Generate UFW configuration script.
        
        Returns:
            str: Shell script to configure UFW
        """
        script_lines = [
            "set -e",
            f"sudo ufw allow {self.ssh_port}",
            f"sudo ufw allow {self.mpi_ports[0]}:{self.mpi_ports[1]}/tcp",
            f"sudo ufw allow {self.mpi_ports[0]}:{self.mpi_ports[1]}/udp",
        ]
        
        for port in self.slurm_ports:
            script_lines.append(f"sudo ufw allow {port}")
        
        for ip in self.all_ips:
            script_lines.append(f"sudo ufw allow from {ip}")
        
        script_lines.append("sudo ufw --force enable")
        
        return " && ".join(script_lines)
    
    def _generate_firewalld_script(self) -> str:
        """
        Generate firewalld configuration script.
        
        Returns:
            str: Shell script to configure firewalld
        """
        script_lines = [
            "set -e",
            "sudo systemctl start firewalld",
            "sudo firewall-cmd --permanent --add-service=ssh",
            f"sudo firewall-cmd --permanent --add-port={self.mpi_ports[0]}-{self.mpi_ports[1]}/tcp",
            f"sudo firewall-cmd --permanent --add-port={self.mpi_ports[0]}-{self.mpi_ports[1]}/udp",
        ]
        
        for port in self.slurm_ports:
            script_lines.append(f"sudo firewall-cmd --permanent --add-port={port}/tcp")
        
        for ip in self.all_ips:
            script_lines.append(f"sudo firewall-cmd --permanent --zone=trusted --add-source={ip}")
        
        script_lines.append("sudo firewall-cmd --reload")
        
        return " && ".join(script_lines)
    
    def update_hosts_file_local(self) -> bool:
        """
        Update /etc/hosts file on local node with cluster node entries.
        
        Returns:
            bool: True if update successful, False otherwise
        """
        print("\n=== Updating /etc/hosts locally ===")
        
        hosts_entries = []
        
        for ip, hostname in self.node_hostnames.items():
            hosts_entries.append(f"{ip}\t{hostname}")
        
        # Create temporary hosts file addition
        temp_hosts = Path("/tmp/cluster_hosts")
        temp_hosts.write_text("\n".join(hosts_entries) + "\n")
        
        # Append to /etc/hosts if entries don't already exist
        check_cmd = ["grep", "-q", self.master_ip, "/etc/hosts"]
        check_result = subprocess.run(check_cmd, capture_output=True)
        
        if check_result.returncode != 0:
            # Entries don't exist, append them
            append_cmd = f"sudo sh -c 'cat /tmp/cluster_hosts >> /etc/hosts'"
            
            try:
                result = subprocess.run(append_cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✓ /etc/hosts updated successfully")
                    print(f"Added entries:\n{temp_hosts.read_text()}")
                    return True
                else:
                    print(f"✗ Failed to update /etc/hosts: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"✗ Error updating /etc/hosts: {e}")
                return False
        else:
            print("✓ /etc/hosts already contains cluster entries")
            return True
    
    def update_hosts_file_cluster_pdsh(self) -> bool:
        """
        Update /etc/hosts on all cluster nodes using pdsh.
        
        Returns:
            bool: True if update successful on all nodes, False otherwise
        """
        print("\n=== Updating /etc/hosts cluster-wide ===")
        
        # Update locally first
        if not self.update_hosts_file_local():
            print("Failed to update /etc/hosts locally")
            return False
        
        # Get other nodes
        other_nodes = [ip for ip in self.all_ips if ip != self._get_local_ip()]
        
        if not other_nodes:
            print("No other nodes to update")
            return True
        
        # Create hosts entries content
        hosts_entries = []
        for ip, hostname in self.node_hostnames.items():
            hosts_entries.append(f"{ip}\t{hostname}")
        
        hosts_content = "\n".join(hosts_entries)
        all_success = True
        
        for node_ip in other_nodes:
            print(f"\nUpdating /etc/hosts on {node_ip}...")
            
            # Check if entries already exist
            check_cmd = [
                "sshpass", "-p", self.password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"{self.username}@{node_ip}",
                f"grep -q {self.master_ip} /etc/hosts"
            ]
            
            check_result = subprocess.run(check_cmd, capture_output=True)
            
            if check_result.returncode != 0:
                # Entries don't exist, add them
                update_cmd = [
                    "sshpass", "-p", self.password,
                    "ssh", "-o", "StrictHostKeyChecking=no",
                    f"{self.username}@{node_ip}",
                    f"echo '{hosts_content}' | sudo tee -a /etc/hosts > /dev/null"
                ]
                
                try:
                    result = subprocess.run(update_cmd, capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        print(f"✓ /etc/hosts updated on {node_ip}")
                    else:
                        print(f"✗ Failed to update /etc/hosts on {node_ip}")
                        all_success = False
                        
                except Exception as e:
                    print(f"✗ Error updating /etc/hosts on {node_ip}: {e}")
                    all_success = False
            else:
                print(f"✓ /etc/hosts already contains entries on {node_ip}")
        
        return all_success
    
    def test_network_connectivity(self) -> bool:
        """
        Test network connectivity to all cluster nodes.
        
        Returns:
            bool: True if all nodes reachable, False otherwise
        """
        print("\n=== Testing Network Connectivity ===")
        
        all_reachable = True
        
        for ip in self.all_ips:
            hostname = self.node_hostnames.get(ip, ip)
            print(f"\nPinging {hostname} ({ip})...")
            
            ping_cmd = ["ping", "-c", "3", "-W", "2", ip]
            
            try:
                result = subprocess.run(ping_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    print(f"✓ {hostname} is reachable")
                else:
                    print(f"✗ {hostname} is NOT reachable")
                    all_reachable = False
                    
            except Exception as e:
                print(f"✗ Error pinging {hostname}: {e}")
                all_reachable = False
        
        return all_reachable
    
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
    print("Network Manager Module")
    print("Import this module to use NetworkManager class")
