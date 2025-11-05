"""
Slurm Setup Helper Module

Handles Munge authentication setup and Slurm service configuration
across the cluster for proper job submission.

Author: Olumuyiwa Oluwasanmi
Date: November 5, 2025
"""

import subprocess
import shlex
from pathlib import Path
from typing import List, Optional
import secrets


class SlurmSetupHelper:
    """
    Helper class for Slurm and Munge configuration.
    
    Handles:
    - Munge key generation and distribution
    - Munge service setup on all nodes
    - Slurm service configuration
    - Partition and node configuration
    """
    
    def __init__(self, username: str, password: str, master_ip: str, worker_ips: List[str]):
        """
        Initialize Slurm Setup Helper.
        
        Args:
            username: Username for cluster nodes
            password: Password for authentication
            master_ip: Master node IP
            worker_ips: List of worker IPs
        """
        self.username = username
        self.password = password
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
        self.munge_key_path = Path("/etc/munge/munge.key")
    
    def setup_munge_master(self) -> bool:
        """
        Setup Munge authentication on master node.
        
        Returns:
            bool: True if successful
        """
        print("\n=== Setting up Munge on Master Node ===")
        
        # Install munge if not present
        if not self._is_munge_installed():
            print("Installing Munge...")
            if not self._install_munge():
                return False
        
        # Generate munge key if doesn't exist
        if not self.munge_key_path.exists():
            print("Generating Munge key...")
            if not self._generate_munge_key():
                return False
        else:
            print("✓ Munge key already exists")
        
        # Set proper permissions
        self._fix_munge_permissions()
        
        # Start munge service
        print("Starting Munge service...")
        if not self._start_munge_service():
            return False
        
        print("✓ Munge setup complete on master")
        return True
    
    def distribute_munge_key(self) -> bool:
        """
        Distribute munge key to all worker nodes.
        
        Returns:
            bool: True if successful
        """
        print("\n=== Distributing Munge Key to Workers ===")
        
        if not self.munge_key_path.exists():
            print("✗ Munge key does not exist on master")
            return False
        
        for worker_ip in self.worker_ips:
            print(f"Distributing to {worker_ip}...")
            
            # Create munge directory on worker
            ssh_cmd = f"ssh {self.username}@{worker_ip} 'sudo mkdir -p /etc/munge && sudo chown munge:munge /etc/munge'"
            if not self._run_command(ssh_cmd):
                print(f"  ⚠ Failed to create munge directory on {worker_ip}")
                continue
            
            # Copy munge key
            scp_cmd = f"sudo scp {self.munge_key_path} {self.username}@{worker_ip}:/tmp/munge.key"
            if not self._run_command(scp_cmd):
                print(f"  ✗ Failed to copy munge key to {worker_ip}")
                continue
            
            # Move to proper location and fix permissions
            move_cmd = f"ssh {self.username}@{worker_ip} 'sudo mv /tmp/munge.key /etc/munge/munge.key && sudo chown munge:munge /etc/munge/munge.key && sudo chmod 400 /etc/munge/munge.key'"
            if not self._run_command(move_cmd):
                print(f"  ✗ Failed to setup munge key on {worker_ip}")
                continue
            
            # Start munge service on worker
            start_cmd = f"ssh {self.username}@{worker_ip} 'sudo systemctl enable munge && sudo systemctl restart munge'"
            if not self._run_command(start_cmd):
                print(f"  ⚠ Failed to start munge on {worker_ip}")
            else:
                print(f"  ✓ Munge configured on {worker_ip}")
        
        print("✓ Munge key distribution complete")
        return True
    
    def configure_slurm_partition(self, partition_name: str = "normal", node_info: dict = None) -> bool:
        """
        Configure Slurm partition in slurm.conf.
        
        Args:
            partition_name: Name of partition
            node_info: Dictionary mapping node names to core counts
            
        Returns:
            bool: True if successful
        """
        print(f"\n=== Configuring Slurm Partition '{partition_name}' ===")
        
        slurm_conf = Path("/etc/slurm/slurm.conf")
        
        if not slurm_conf.exists():
            print(f"✗ {slurm_conf} does not exist")
            return False
        
        # Check if partition already exists
        content = slurm_conf.read_text()
        
        if f"PartitionName={partition_name}" in content:
            print(f"✓ Partition '{partition_name}' already configured")
            return True
        
        # Add partition configuration
        # This is a simplified version - in production, use proper node detection
        partition_line = f"\nPartitionName={partition_name} Nodes=ALL Default=YES MaxTime=INFINITE State=UP\n"
        
        try:
            # Backup original
            backup = slurm_conf.with_suffix('.conf.backup')
            slurm_conf.rename(backup)
            
            # Write new config
            new_content = content + partition_line
            slurm_conf.write_text(new_content)
            
            print(f"✓ Added partition '{partition_name}' to slurm.conf")
            
            # Restart slurmctld to apply changes
            self._run_command("sudo systemctl restart slurmctld")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to configure partition: {e}")
            # Restore backup if it exists
            if backup.exists():
                backup.rename(slurm_conf)
            return False
    
    def restart_slurm_services(self) -> bool:
        """
        Restart Slurm services on all nodes.
        
        Returns:
            bool: True if successful
        """
        print("\n=== Restarting Slurm Services ===")
        
        # Restart controller on master
        print("Restarting slurmctld on master...")
        if not self._run_command("sudo systemctl restart slurmctld"):
            print("  ⚠ Failed to restart slurmctld")
        else:
            print("  ✓ slurmctld restarted")
        
        # Restart slurmd on all nodes (including master if it runs slurmd)
        for node_ip in self.all_ips:
            print(f"Restarting slurmd on {node_ip}...")
            cmd = f"ssh {self.username}@{node_ip} 'sudo systemctl restart slurmd'"
            if not self._run_command(cmd):
                print(f"  ⚠ Failed to restart slurmd on {node_ip}")
            else:
                print(f"  ✓ slurmd restarted on {node_ip}")
        
        print("✓ Slurm services restarted")
        return True
    
    def verify_slurm_cluster(self) -> bool:
        """
        Verify Slurm cluster is operational.
        
        Returns:
            bool: True if cluster is working
        """
        print("\n=== Verifying Slurm Cluster ===")
        
        # Check munge authentication
        print("Testing Munge authentication...")
        result = subprocess.run(
            ["munge", "-n"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Try to unmunge the output
            unmunge = subprocess.run(
                ["unmunge"],
                input=result.stdout,
                capture_output=True,
                text=True
            )
            if unmunge.returncode == 0:
                print("✓ Munge authentication working")
            else:
                print("✗ Munge unmunge failed")
                return False
        else:
            print("✗ Munge encode failed")
            return False
        
        # Check sinfo
        print("Checking cluster status with sinfo...")
        result = subprocess.run(
            ["sinfo"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Slurm cluster operational")
            print("\nCluster Status:")
            print(result.stdout)
            return True
        else:
            print("✗ sinfo failed:")
            print(result.stderr)
            return False
    
    def _is_munge_installed(self) -> bool:
        """Check if Munge is installed."""
        result = subprocess.run(["which", "munged"], capture_output=True)
        return result.returncode == 0
    
    def _install_munge(self) -> bool:
        """Install Munge via package manager."""
        # Detect OS
        if Path("/etc/redhat-release").exists():
            cmd = ["sudo", "dnf", "install", "-y", "munge", "munge-libs"]
        elif Path("/etc/debian_version").exists():
            cmd = ["sudo", "apt-get", "install", "-y", "munge"]
        else:
            print("✗ Unsupported OS for automatic Munge installation")
            return False
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Munge installed")
            return True
        else:
            print(f"✗ Munge installation failed: {result.stderr}")
            return False
    
    def _generate_munge_key(self) -> bool:
        """Generate Munge key."""
        try:
            # Ensure munge directory exists
            self._run_command("sudo mkdir -p /etc/munge")
            
            # Generate random key in temp location
            import tempfile
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as tmp:
                key = secrets.token_bytes(1024)
                tmp.write(key)
                tmp_path = tmp.name
            
            # Move to proper location with sudo
            cmd = f"sudo mv {tmp_path} /etc/munge/munge.key"
            if not self._run_command(cmd):
                raise Exception("Failed to move munge key")
            
            print("✓ Munge key generated")
            return True
            
        except Exception as e:
            print(f"✗ Failed to generate munge key: {e}")
            return False
    
    def _fix_munge_permissions(self) -> None:
        """Fix Munge file permissions."""
        commands = [
            "sudo chown -R munge:munge /etc/munge /var/lib/munge /var/log/munge /run/munge",
            "sudo chmod 0700 /etc/munge /var/lib/munge /var/log/munge",
            "sudo chmod 0755 /run/munge",
            "sudo chmod 0400 /etc/munge/munge.key"
        ]
        
        for cmd in commands:
            self._run_command(cmd)
    
    def _start_munge_service(self) -> bool:
        """Start and enable Munge service."""
        commands = [
            "sudo systemctl enable munge",
            "sudo systemctl restart munge"
        ]
        
        for cmd in commands:
            if not self._run_command(cmd):
                return False
        
        # Verify service is running
        result = subprocess.run(
            ["sudo", "systemctl", "is-active", "munge"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip() == "active":
            print("✓ Munge service is running")
            return True
        else:
            print("✗ Munge service failed to start")
            return False
    
    def _run_command(self, command: str) -> bool:
        """
        Run a shell command.
        
        Args:
            command: Command string to execute
            
        Returns:
            bool: True if successful
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception:
            return False
