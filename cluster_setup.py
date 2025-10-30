#!/usr/bin/env python3
"""
Cluster Setup Script for Slurm and OpenMPI
Supports Ubuntu Linux and WSL with Ubuntu

Usage:
    python cluster_setup.py --master <master_ip> --workers <worker_ip1> <worker_ip2> ...
    python cluster_setup.py --config config.yml
"""

import argparse
import subprocess
import sys
import os
import shutil
import socket
from pathlib import Path
from typing import List, Dict, Optional

# YAML parsing
try:
    import yaml
except Exception:
    yaml = None


class ClusterSetup:
    """Main class for cluster setup and configuration"""
    
    def __init__(self, master_ip: str, worker_ips: List[str], username: Optional[str] = None):
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
        self.username = username or os.getenv('USER', 'ubuntu')
        self.is_master = self._is_current_node_master()
        
    def _is_current_node_master(self) -> bool:
        """Check if current node is the master node"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip == self.master_ip or self.master_ip in ['localhost', '127.0.0.1']
        except Exception:
            return False
    
    def run_command(self, command: str, check: bool = True, shell: bool = True) -> subprocess.CompletedProcess:
        """Run a shell command and return the result"""
        try:
            result = subprocess.run(
                command,
                shell=shell,
                check=check,
                capture_output=True,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {command}")
            print(f"Error output: {e.stderr}")
            if check:
                raise
            return e
    
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
        self.run_command(
            "sudo apt-get update && sudo apt-get install -y build-essential procps curl file git"
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
                f.write('eval "$({homebrew_path}/brew shellenv)"\n')
        
        print("Homebrew installed successfully")
    
    def setup_ssh(self):
        """Setup SSH client and server"""
        print("\n=== Setting up SSH ===")
        
        # Install OpenSSH client and server
        print("Installing OpenSSH client and server...")
        self.run_command("sudo apt-get update", check=False)
        self.run_command("sudo apt-get install -y openssh-client openssh-server")
        
        # Start SSH service
        print("Starting SSH service...")
        self.run_command("sudo service ssh start", check=False)
        self.run_command("sudo systemctl enable ssh", check=False)
        
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
            print("\nNOTE: You need to manually copy this public key to all other nodes")
            print(f"On each node, add this key to {authorized_keys}")
        
        # Configure SSH to not require strict host key checking (for cluster setup)
        ssh_config = ssh_dir / "config"
        config_content = """Host *\n    StrictHostKeyChecking no\n    UserKnownHostsFile=/dev/null\n"""
        with open(ssh_config, 'w') as f:
            f.write(config_content)
        ssh_config.chmod(0o600)
        
        print("SSH configuration completed")
    
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
        self.run_command("sudo cp /etc/hosts /etc/hosts.backup", check=False)
        
        # Check if entries already exist
        with open('/etc/hosts', 'r') as f:
            existing_hosts = f.read()
        
        if "# Cluster nodes" not in existing_hosts:
            # Append cluster entries
            with open('/tmp/hosts_append', 'w') as f:
                f.write(hosts_content)
            
            self.run_command("sudo bash -c 'cat /tmp/hosts_append >> /etc/hosts'")
            print("/etc/hosts updated successfully")
        else:
            print("/etc/hosts already contains cluster node entries")
    
    def install_slurm(self):
        """Install Slurm using Homebrew"""
        print("\n=== Installing Slurm ===")
        
        # Ensure brew is in PATH
        self.run_command("eval \"$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)\"", check=False)
        
        brew_cmd = "/home/linuxbrew/.linuxbrew/bin/brew"
        if not os.path.exists(brew_cmd):
            print("Error: Homebrew not found. Please install Homebrew first.")
            return
        
        # Install Slurm
        print("Installing Slurm via Homebrew...")
        result = self.run_command(f"{brew_cmd} install slurm", check=False)
        
        if result.returncode != 0:
            print("Note: Slurm might not be available in Homebrew. Installing from apt...")
            self.run_command("sudo apt-get update")
            self.run_command("sudo apt-get install -y slurm-wlm slurm-wlm-doc")
        
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
            self.run_command("sudo apt-get update")
            self.run_command("sudo apt-get install -y openmpi-bin openmpi-common libopenmpi-dev")
        
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
            self.run_command(f"sudo mkdir -p {dir_path}")
            self.run_command(f"sudo chown -R {self.username}:{self.username} {dir_path}", check=False)
        
        # Generate slurm.conf
        slurm_conf = self.generate_slurm_conf()
        
        with open('/tmp/slurm.conf', 'w') as f:
            f.write(slurm_conf)
        
        self.run_command("sudo cp /tmp/slurm.conf /etc/slurm/slurm.conf")
        
        # Generate cgroup.conf
        cgroup_conf = """CgroupAutomount=yes\nConstrainCores=yes\nConstrainRAMSpace=yes\n"""
        with open('/tmp/cgroup.conf', 'w') as f:
            f.write(cgroup_conf)
        
        self.run_command("sudo cp /tmp/cgroup.conf /etc/slurm/cgroup.conf")
        
        print("Slurm configuration files created")
        
        # Start Slurm services
        if self.is_master:
            print("Starting Slurm controller (slurmctld)...")
            self.run_command("sudo slurmctld", check=False)
        
        print("Starting Slurm daemon (slurmd)...")
        self.run_command("sudo slurmd", check=False)
        
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
        
        conf = f"""# slurm.conf - Slurm configuration file\nClusterName=cluster\nSlurmctldHost=master({self.master_ip})\n\n# Scheduling\nSchedulerType=sched/backfill\nSelectType=select/cons_tres\nSelectTypeParameters=CR_Core\n\n# Logging\nSlurmctldDebug=info\nSlurmctldLogFile=/var/log/slurm/slurmctld.log\nSlurmdDebug=info\nSlurmdLogFile=/var/log/slurm/slurmd.log\n\n# State preservation\nStateSaveLocation=/var/spool/slurm/ctld\nSlurmdSpoolDir=/var/spool/slurm/d\n\n# Process tracking\nProctrackType=proctrack/linuxproc\nTaskPlugin=task/affinity,task/cgroup\n\n# MPI\nMpiDefault=pmix\n\n# Timeouts\nSlurmctldTimeout=300\nSlurmdTimeout=300\nInactiveLimit=0\nMinJobAge=300\nKillWait=30\nWaittime=0\n\n# Nodes\n"""
        # Add master node
        conf += f"NodeName=master CPUs={{cpus}} RealMemory={{memory}} State=UNKNOWN\n"
        
        # Add worker nodes
        for idx, worker_ip in enumerate(self.worker_ips, start=1):
            conf += f"NodeName=worker{{idx}} CPUs={{cpus}} RealMemory={{memory}} State=UNKNOWN\n"
        
        # Add partition
        all_nodes = "master," + ",".join([f"worker{{i+1}}" for i in range(len(self.worker_ips))])
        conf += f"\n# Partitions\nPartitionName=all Nodes={{all_nodes}} Default=YES MaxTime=INFINITE State=UP\n"
        
        return conf
    
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
        
        # Create default MCA parameters file
        mca_params = """# OpenMPI MCA parameters\nbtl = ^openib\nbtl_tcp_if_include = eth0\n"""
        mca_file = Path.home() / ".openmpi" / "mca-params.conf"
        with open(mca_file, 'w') as f:
            f.write(mca_params)
        
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
        ]
        
        for name, command in checks:
            result = self.run_command(command, check=False)
            if result.returncode == 0:
                print(f"✓ {{name}}: OK")
            else:
                print(f"✗ {{name}}: NOT FOUND or ERROR")
        
        print("\nVerification completed")
    
    def run_full_setup(self):
        """Run the complete cluster setup"""
        print("=" * 60)
        print("CLUSTER SETUP SCRIPT")
        print("=" * 60)
        print(f"Master Node: {{self.master_ip}}")
        print(f"Worker Nodes: {{', '.join(self.worker_ips)}}")
        print(f"Current node is: {{'MASTER' if self.is_master else 'WORKER'}}")
        print("=" * 60)
        
        # Check sudo access
        if not self.check_sudo_access():
            print("\nWARNING: This script requires sudo access.")
            print("Please run with sudo or ensure passwordless sudo is configured.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("Setup cancelled")
                return
        
        try:
            # Setup steps
            self.install_homebrew()
            self.setup_ssh()
            self.configure_passwordless_ssh()
            self.configure_hosts_file()
            self.install_slurm()
            self.install_openmpi()
            self.configure_slurm()
            self.configure_openmpi()
            self.verify_installation()
            
            print("\n" + "=" * 60)
            print("CLUSTER SETUP COMPLETED SUCCESSFULLY")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Ensure passwordless SSH is configured between all nodes")
            print("2. Copy the public key to all worker nodes")
            print("3. Run this script on all worker nodes")
            print("4. Test Slurm with: sinfo")
            print("5. Test OpenMPI with: mpirun -np 2 hostname")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n\nERROR during setup: {{e}}")
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
        description="Cluster Setup Script for Slurm and OpenMPI on Ubuntu/WSL"
    )
    parser.add_argument(
        '--config', '-c',
        help='Path to YAML config file containing master/workers/username',
        default=None
    )
    parser.add_argument(
        '--master',
        help='IPv4 address of the master node (overrides config file)'
    )
    parser.add_argument(
        '--workers',
        nargs='+',
        help='IPv4 addresses of worker nodes (space-separated; overrides config file)'
    )
    parser.add_argument(
        '--username',
        default=None,
        help='Username for cluster operations (default: current user)'
    )
    
    args = parser.parse_args()
    
    config = {}
    if args.config:
        try:
            config = load_yaml_config(args.config)
        except Exception as e:
            print(f"Error loading config file {{args.config}}: {{e}}")
            sys.exit(1)
    
    # Merge CLI args over YAML config (CLI overrides YAML)
    master = args.master or config.get('master')
    workers = args.workers or config.get('workers')
    username = args.username or config.get('username')
    
    # Normalize workers if provided as string in YAML
    if isinstance(workers, str):
        workers = workers.split()
    
    # Validate presence
    if not master or not workers:
        print("Error: master and workers must be provided either via CLI or --config YAML file.")
        parser.print_help()
        sys.exit(1)
    
    # Validate IP addresses
    def is_valid_ip(ip):
        # Allow localhost and 127.0.0.1
        if ip in ['localhost', '127.0.0.1']:
            return True
        parts = ip.split('.');
        if len(parts) != 4:
            return False;
        try:
            return all(part and part.isdigit() and 0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False
    
    if not is_valid_ip(master):
        print(f"Error: Invalid master IP address: {{master}}")
        sys.exit(1)
    
    for worker_ip in workers:
        if not is_valid_ip(worker_ip):
            print(f"Error: Invalid worker IP address: {{worker_ip}}")
            sys.exit(1)
    
    # Create and run setup
    setup = ClusterSetup(master, workers, username)
    setup.run_full_setup()


if __name__ == '__main__':
    main()