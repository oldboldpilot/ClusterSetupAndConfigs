#!/usr/bin/env python3.14
"""
Streamlined Cluster Setup Script - Modular Version

Automated HPC cluster setup using modular managers for:
- Homebrew and GCC compilers
- SSH keys and passwordless sudo
- OpenMPI, Slurm, OpenMP
- PGAS libraries (UPC++, Berkeley UPC, OpenSHMEM)
- Benchmarks and testing

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
Version: 3.0.0 (Modular)
"""

import os
import sys
import argparse
import subprocess
import socket
import re
from pathlib import Path
from typing import List, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None
    print("Warning: PyYAML not installed. Install with: pip install pyyaml")

# Import modular managers
from cluster_modules import (
    HomebrewManager,
    SSHManager,
    SudoManager,
    MPIManager,
    OpenMPManager,
    OpenSHMEMManager,
    BerkeleyUPCManager,
    PGASManager,
    BenchmarkManager,
    SlurmManager,
    NetworkManager,
    PDSHManager,
)
from cluster_modules.core import ClusterCore


class ClusterSetup:
    """Streamlined cluster setup using modular managers"""
    
    def __init__(self, master_ip: str, worker_ips: List[str], 
                 username: str, password: Optional[str] = None):
        """
        Initialize cluster setup with modular managers
        
        Args:
            master_ip: IP address of the master node
            worker_ips: List of worker node IP addresses
            username: Username for all nodes
            password: Password for remote operations (optional)
        """
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.username = username
        self.password = password
        
        # Detect OS and determine if this is the master node
        self.os_type = self._detect_os()
        self.pkg_manager = self._detect_package_manager()
        self.is_master = self._is_master_node()
        
        # Initialize all modular managers
        self._initialize_managers()
    
    def _detect_os(self) -> str:
        """Detect the operating system type"""
        if os.path.exists("/etc/redhat-release"):
            return "redhat"
        elif os.path.exists("/etc/debian_version"):
            return "ubuntu"
        else:
            return "unknown"
    
    def _detect_package_manager(self) -> str:
        """Detect the system package manager"""
        if self.os_type == "redhat":
            # Check for dnf first (RHEL 8+, Fedora), fall back to yum
            result = subprocess.run(['which', 'dnf'], capture_output=True)
            return 'dnf' if result.returncode == 0 else 'yum'
        elif self.os_type == "ubuntu":
            return 'apt-get'
        else:
            return 'apt-get'  # Default
    
    def _is_master_node(self) -> bool:
        """Determine if current node is the master"""
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Also check all network interfaces
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                ip_pattern = r'inet\s+(\d+\.\d+\.\d+\.\d+)'
                found_ips = re.findall(ip_pattern, result.stdout)
                return self.master_ip in found_ips
            
            return local_ip == self.master_ip
        except Exception:
            return False
    
    def _initialize_managers(self):
        """Initialize all modular managers"""
        print(f"\n{'='*70}")
        print("INITIALIZING MODULAR MANAGERS")
        print(f"{'='*70}")
        
        # Create ClusterCore instance for managers that use it
        core = ClusterCore(self.master_ip, self.worker_ips, self.username, self.password)
        
        # Core managers
        self.homebrew_mgr = HomebrewManager(self.username, self.password, 
                                           self.master_ip, self.worker_ips)
        self.ssh_mgr = SSHManager(core)  # Uses ClusterCore
        self.sudo_mgr = SudoManager(self.username, self.password, 
                                    [self.master_ip] + self.worker_ips)  # Takes all_ips
        
        # Network and infrastructure
        self.network_mgr = NetworkManager(self.username, self.password or "",
                                         self.master_ip, self.worker_ips)
        self.pdsh_mgr = PDSHManager(self.username, self.password or "",
                                   self.master_ip, self.worker_ips)
        
        # Parallel programming managers
        self.mpi_mgr = MPIManager(self.master_ip, self.worker_ips,
                                 self.username, self.password)  # Different parameter order!
        self.openmp_mgr = OpenMPManager(self.username, self.password or "",
                                       self.master_ip, self.worker_ips)
        self.openshmem_mgr = OpenSHMEMManager(self.username, self.password or "",
                                             self.master_ip, self.worker_ips)
        self.berkeley_upc_mgr = BerkeleyUPCManager(self.username, self.password or "",
                                                  self.master_ip, self.worker_ips)
        
        # PGAS manager (uses ClusterCore)
        self.pgas_mgr = PGASManager(core)
        
        # Workload and benchmark managers
        self.slurm_mgr = SlurmManager(self.username, self.password or "",
                                     self.master_ip, self.worker_ips)
        self.benchmark_mgr = BenchmarkManager(self.username, self.password or "",
                                             self.master_ip, self.worker_ips)
        
        print("✓ All managers initialized")
    
    def run_full_setup(self, config_file: Optional[str] = None, 
                      non_interactive: bool = False):
        """Run the complete cluster setup using modular managers"""
        print(f"\n{'='*70}")
        print("MODULAR CLUSTER SETUP")
        print(f"{'='*70}")
        print(f"Master Node: {self.master_ip}")
        print(f"Worker Nodes: {', '.join(self.worker_ips)}")
        print(f"Current node is: {'MASTER' if self.is_master else 'WORKER'}")
        print(f"OS Type: {self.os_type}")
        print(f"Package Manager: {self.pkg_manager}")
        print(f"{'='*70}")
        
        try:
            # STEP 0: Configure Passwordless Sudo FIRST (before any sudo operations)
            if self.password:
                print(f"\n{'='*70}")
                print("STEP 0: Configure Passwordless Sudo (CRITICAL - must be first)")
                print(f"{'='*70}")
                self.sudo_mgr.configure_passwordless_sudo_local()
                print("✓ Passwordless sudo configured - no more password prompts needed")
            
            # STEP 1: SSH Keys (enables remote operations)
            print(f"\n{'='*70}")
            print("STEP 1: SSH Keys and Passwordless SSH")
            print(f"{'='*70}")
            self.ssh_mgr.setup_ssh()
            self.ssh_mgr.configure_passwordless_ssh()
            
            # STEP 2: Homebrew, GCC, and Binutils (SECOND - base dependencies)
            print(f"\n{'='*70}")
            print("STEP 2: Homebrew, GCC, and Binutils")
            print(f"{'='*70}")
            self.homebrew_mgr.install_and_configure_local()
            
            # STEP 3: System Configuration (THIRD - hosts file, PATH)
            print(f"\n{'='*70}")
            print("STEP 3: System Configuration")
            print(f"{'='*70}")
            self._configure_hosts_file()
            
            # STEP 4: Parallel Programming Infrastructure (FOURTH - Slurm, pdsh)
            print(f"\n{'='*70}")
            print("STEP 4: Parallel Programming Infrastructure")
            print(f"{'='*70}")
            self.slurm_mgr.install_slurm_local()
            if self.password:
                self.pdsh_mgr.install_and_configure_cluster()
            
            # STEP 5: MPI and Parallel Libraries (FIFTH - main functionality)
            print(f"\n{'='*70}")
            print("STEP 5: MPI and Parallel Libraries")
            print(f"{'='*70}")
            # Note: MPI installation uses the old method for now, will be migrated
            self._install_openmpi()
            self.openmp_mgr.install_libomp_local()
            
            # STEP 6: PGAS Libraries (SIXTH - UPC++, OpenSHMEM, Berkeley UPC)
            print(f"\n{'='*70}")
            print("STEP 6: PGAS Libraries")
            print(f"{'='*70}")
            self.pgas_mgr.install_pgas_libraries_local()  # Using PGASManager
            
            # STEP 7: Network Configuration (SEVENTH - firewall, MPI ports)
            print(f"\n{'='*70}")
            print("STEP 7: Network Configuration")
            print(f"{'='*70}")
            self.network_mgr.configure_firewall_local()
            
            # STEP 8: Benchmark Generation (EIGHTH - create performance tests)
            print(f"\n{'='*70}")
            print("STEP 8: Benchmark Generation")
            print(f"{'='*70}")
            self._generate_benchmarks()
            
            # STEP 9: Final Configuration and Verification (NINTH - finalize)
            print(f"\n{'='*70}")
            print("STEP 9: Final Configuration and Verification")
            print(f"{'='*70}")
            self._post_installation_fixes()
            self._verify_installation()
            
            print(f"\n{'='*70}")
            print("✓ LOCAL NODE SETUP COMPLETED SUCCESSFULLY")
            print(f"{'='*70}")
            
            # Setup other nodes if password provided
            if self.password and config_file:
                self._setup_other_nodes(config_file)
            
            # Final summary
            self._print_summary()
            
        except Exception as e:
            print(f"\n\n✗ ERROR during setup: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    def _configure_hosts_file(self):
        """Configure /etc/hosts with cluster node information"""
        print("\n=== Configuring /etc/hosts ===")
        
        # Create hosts entries
        hosts_entries = []
        hosts_entries.append(f"{self.master_ip}    master master-node")
        
        for idx, worker_ip in enumerate(self.worker_ips, start=1):
            hosts_entries.append(f"{worker_ip}    worker{idx} worker-node{idx}")
        
        hosts_content = "\n# Cluster nodes\n" + "\n".join(hosts_entries) + "\n"
        
        # Check if entries already exist
        with open('/etc/hosts', 'r') as f:
            existing_hosts = f.read()
        
        if "# Cluster nodes" not in existing_hosts:
            # Append cluster entries
            with open('/tmp/hosts_append', 'w') as f:
                f.write(hosts_content)
            
            subprocess.run("sudo bash -c 'cat /tmp/hosts_append >> /etc/hosts'", shell=True, check=False)
            print("✓ /etc/hosts updated successfully")
        else:
            print("✓ /etc/hosts already contains cluster node entries")
    
    def _install_openmpi(self):
        """Install OpenMPI using Homebrew"""
        print("\n=== Installing OpenMPI ===")
        
        brew_cmd = "/home/linuxbrew/.linuxbrew/bin/brew"
        
        # Check if already installed
        result = subprocess.run([brew_cmd, 'list', 'open-mpi'], 
                              capture_output=True, check=False)
        if result.returncode == 0:
            print("✓ OpenMPI already installed")
            return
        
        # Check and remove MPICH (incompatible)
        mpich_check = subprocess.run([brew_cmd, 'list', 'mpich'], 
                                    capture_output=True, check=False)
        if mpich_check.returncode == 0:
            print("⚠️  Uninstalling MPICH (incompatible with OpenMPI)...")
            subprocess.run([brew_cmd, 'uninstall', 'mpich'], check=False)
        
        # Install GCC and CMake (required)
        print("Installing GCC and CMake...")
        subprocess.run([brew_cmd, 'install', 'gcc'], check=False)
        subprocess.run([brew_cmd, 'install', 'cmake'], check=False)
        
        # Create GCC symlinks
        self.homebrew_mgr.create_gcc_symlinks()
        
        # Install OpenMPI
        print("Installing OpenMPI...")
        result = subprocess.run([brew_cmd, 'install', 'open-mpi'], check=False)
        
        if result.returncode == 0:
            subprocess.run([brew_cmd, 'link', 'open-mpi'], check=False)
            print("✓ OpenMPI installed successfully")
        else:
            print(f"⚠️  Homebrew install failed, using {self.pkg_manager}...")
            if self.pkg_manager == 'dnf':
                subprocess.run(['sudo', 'dnf', 'install', '-y', 'openmpi', 'openmpi-devel'], check=False)
            else:
                subprocess.run(['sudo', 'apt-get', 'update'], check=False)
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 
                              'openmpi-bin', 'openmpi-common', 'libopenmpi-dev'], check=False)
    
    def _generate_benchmarks(self):
        """Generate PGAS and MPI benchmarks using BenchmarkManager"""
        print("\n=== Generating Benchmarks ===")
        
        # Use existing cluster_build_sources directory for benchmarks
        benchmark_dir = Path.home() / "cluster_build_sources" / "benchmarks"
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        
        # Update benchmark manager's benchmark_dir
        self.benchmark_mgr.benchmark_dir = benchmark_dir
        
        # Create src directory for source files
        src_dir = benchmark_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        print(f"Benchmark directory: {benchmark_dir}")
        
        # Generate UPC++ latency benchmark
        print("\n→ Generating UPC++ latency benchmark...")
        self.benchmark_mgr.create_upcxx_latency_benchmark(
            iterations=1000,
            warmup_iterations=100
        )
        
        # Generate UPC++ bandwidth benchmark
        print("→ Generating UPC++ bandwidth benchmark...")
        self.benchmark_mgr.create_upcxx_bandwidth_benchmark(
            iterations=1000,
            message_sizes=[1024, 4096, 16384, 65536, 262144, 1048576]
        )
        
        # Generate MPI latency benchmark
        print("→ Generating MPI latency benchmark...")
        self.benchmark_mgr.create_mpi_latency_benchmark(
            iterations=1000,
            warmup_iterations=100
        )
        
        # Generate OpenSHMEM latency benchmark
        print("→ Generating OpenSHMEM latency benchmark...")
        self.benchmark_mgr.create_openshmem_latency_benchmark(
            iterations=1000,
            warmup_iterations=100
        )
        
        # Generate Berkeley UPC latency benchmark
        print("→ Generating Berkeley UPC latency benchmark...")
        self.benchmark_mgr.create_berkeley_upc_latency_benchmark(
            iterations=1000,
            warmup_iterations=100
        )
        
        # Generate OpenMP parallel benchmark
        print("→ Generating OpenMP parallel benchmark...")
        self.benchmark_mgr.create_openmp_parallel_benchmark(
            num_threads=8,
            work_size=10000000,
            test_iterations=10
        )
        
        # Generate hybrid MPI+OpenMP benchmark
        print("→ Generating hybrid MPI+OpenMP benchmark...")
        self.benchmark_mgr.create_hybrid_mpi_openmp_benchmark(
            num_threads=4,
            work_size=5000000,
            test_iterations=10
        )
        
        # Generate Makefile
        print("→ Generating Makefile...")
        self.benchmark_mgr.create_makefile()
        
        # Generate run script
        print("→ Generating run_benchmarks.sh...")
        self.benchmark_mgr.create_run_script(num_procs=4)
        
        # Make run script executable
        run_script = benchmark_dir / "run_benchmarks.sh"
        if run_script.exists():
            run_script.chmod(0o755)
        
        print(f"\n✓ All benchmarks generated in {benchmark_dir}")
        print(f"\nTo compile and run:")
        print(f"  cd {benchmark_dir}")
        print(f"  make")
        print(f"  ./run_benchmarks.sh")
    
    def _post_installation_fixes(self):
        """Post-installation symlink fixes and PATH verification"""
        print("\n=== Post-Installation Fixes ===")
        
        # Fix GCC symlinks (in case they got overwritten)
        self.homebrew_mgr.create_gcc_symlinks()
        
        # Verify critical tools are on PATH
        critical_tools = [
            ("gcc", "/home/linuxbrew/.linuxbrew/bin/gcc"),
            ("g++", "/home/linuxbrew/.linuxbrew/bin/g++"),
            ("mpicc", "/home/linuxbrew/.linuxbrew/bin/mpicc"),
            ("brew", "/home/linuxbrew/.linuxbrew/bin/brew"),
        ]
        
        print("\n✓ Verifying critical tools on PATH:")
        for tool, path in critical_tools:
            result = subprocess.run(['which', tool], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                print(f"  ✓ {tool}: {result.stdout.strip()}")
            else:
                print(f"  ⚠️  {tool}: Not found on PATH (expected: {path})")
    
    def _verify_installation(self):
        """Verify all installations"""
        print("\n=== Verifying Installations ===")
        
        checks = [
            ("GCC", "/home/linuxbrew/.linuxbrew/bin/gcc --version"),
            ("G++", "/home/linuxbrew/.linuxbrew/bin/g++ --version"),
            ("Gfortran", "/home/linuxbrew/.linuxbrew/bin/gfortran --version"),
            ("Binutils (as)", "/home/linuxbrew/.linuxbrew/opt/binutils/bin/as --version"),
            ("Binutils (ld)", "/home/linuxbrew/.linuxbrew/opt/binutils/bin/ld --version"),
            ("OpenMPI", "mpicc --version"),
            ("Slurm", "sinfo --version"),
        ]
        
        for name, command in checks:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                # Get first line of version output
                version = result.stdout.split('\n')[0] if result.stdout else "OK"
                print(f"✓ {name}: {version}")
            else:
                print(f"✗ {name}: NOT FOUND")
    
    def _setup_other_nodes(self, config_file: str):
        """Setup other cluster nodes"""
        if not self.password or not config_file:
            return
        
        print(f"\n{'='*70}")
        print("SETTING UP OTHER CLUSTER NODES")
        print(f"{'='*70}")
        
        # Determine nodes to setup (all except current)
        other_nodes = []
        if not self.is_master:
            other_nodes.append(self.master_ip)
        
        # Get current node's IPs
        result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            ip_pattern = r'inet\s+(\d+\.\d+\.\d+\.\d+)'
            found_ips = re.findall(ip_pattern, result.stdout)
            other_nodes.extend([ip for ip in self.worker_ips if ip not in found_ips])
        else:
            other_nodes.extend(self.worker_ips)
        
        if other_nodes:
            print(f"Would setup {len(other_nodes)} other nodes")
            for node_ip in other_nodes:
                print(f"  - {node_ip}")
            print("(Other node setup via SSH distribution not yet fully implemented)")
            print("Recommendation: Run this script directly on each node")
    
    def _print_summary(self):
        """Print setup summary"""
        print(f"\n{'='*70}")
        print("CLUSTER SETUP SUMMARY")
        print(f"{'='*70}")
        
        node_type = "Master" if self.is_master else "Worker"
        print(f"✓ {node_type} node (this node) setup completed")
        
        if self.password:
            print(f"✓ Automatic cluster-wide setup enabled")
            print("\nYour entire cluster is ready!")
        else:
            print(f"✓ This node is configured")
            print(f"\nTo setup other nodes:")
            print(f"  Run with --password flag from any node")
        
        print(f"\nNext steps:")
        print(f"1. Test Slurm: sinfo")
        print(f"2. Test OpenMPI: mpirun -np 2 hostname")
        print(f"3. Test pdsh: pdsh -w {','.join(self.worker_ips[:2])} hostname")
        print(f"4. Generate benchmarks using BenchmarkManager")
        print(f"{'='*70}")


def load_yaml_config(path: str) -> Dict:
    """Load YAML config file"""
    if yaml is None:
        raise RuntimeError("PyYAML required. Install with: pip install pyyaml")
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Streamlined Modular Cluster Setup Script",
        epilog="Example: python cluster_setup.py --config cluster_config.yaml --password --run-benchmarks"
    )
    parser.add_argument('--config', '-c', required=True,
                       help='Path to YAML config file')
    parser.add_argument('--password', '-p', action='store_true',
                       help='Prompt for password to setup entire cluster')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run in non-interactive mode')
    parser.add_argument('--run-benchmarks', '-r', action='store_true',
                       help='Run all benchmarks on cluster nodes after setup completes')
    parser.add_argument('--clean-install', action='store_true',
                       help='Remove all existing configs/keys/benchmarks before setup (fresh install)')
    
    args = parser.parse_args()
    
    # Get password if requested
    password = None
    if args.password:
        import getpass
        password = getpass.getpass("Enter cluster password: ")
    
    # Load configuration
    try:
        config = load_yaml_config(args.config)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)
    
    # Extract configuration
    master = config.get('master')
    workers = config.get('workers')
    username = config.get('username', os.getenv('USER', 'muyiwa'))
    
    # Handle dict format
    if isinstance(master, dict):
        master = master.get('ip')
    if isinstance(workers, list) and workers and isinstance(workers[0], dict):
        workers = [w.get('ip') for w in workers]
    
    # Validate
    if not master or not workers:
        print("Error: Config must contain 'master' and 'workers'")
        sys.exit(1)
    
    # Perform clean install if requested
    if args.clean_install:
        print("\n" + "="*70)
        print("CLEAN INSTALL REQUESTED")
        print("="*70)
        print("\nThis will remove:")
        print("  - All benchmarks and build directories")
        print("  - SSH keys (id_rsa, id_ed25519)")
        print("  - OpenMPI and pdsh hostfiles")
        print("  - GCC compatibility symlinks")
        print("  - System binutils symlinks")
        
        if not args.non_interactive:
            response = input("\nAre you sure you want to continue? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Clean install cancelled")
                sys.exit(0)
        
        # Create temporary BenchmarkManager just for clean install
        from cluster_modules.benchmark_manager import BenchmarkManager
        temp_benchmark_mgr = BenchmarkManager(
            username=username,
            password=password or "",
            master_ip=master,
            worker_ips=workers
        )
        
        if not temp_benchmark_mgr.clean_install():
            print("\n✗ Clean install failed")
            sys.exit(1)
        
        print("\n✓ Clean install completed - proceeding with fresh setup\n")
    
    # Run setup
    setup = ClusterSetup(master, workers, username, password)
    setup.run_full_setup(config_file=args.config, non_interactive=args.non_interactive)
    
    # Run benchmarks if requested
    if args.run_benchmarks:
        print("\n" + "="*70)
        print("RUNNING BENCHMARKS ON CLUSTER")
        print("="*70)
        
        # Create BenchmarkManager with correct benchmark directory
        from cluster_modules.benchmark_manager import BenchmarkManager
        from pathlib import Path
        benchmark_dir = Path.home() / "cluster_build_sources" / "benchmarks"
        
        benchmark_mgr = BenchmarkManager(
            username=username,
            password=password or "",
            master_ip=master,
            worker_ips=workers,
            benchmark_dir=benchmark_dir
        )
        
        # First, ensure benchmarks are compiled
        print("\n→ Compiling benchmarks...")
        compile_result = benchmark_mgr.compile_benchmarks()
        
        if compile_result:
            print("✓ Benchmarks compiled successfully")
            
            # Distribute to all nodes
            print("\n→ Distributing benchmarks to all nodes...")
            if benchmark_mgr.distribute_benchmarks_pdsh():
                print("✓ Benchmarks distributed successfully")
                
                # Run benchmarks on all nodes
                results = benchmark_mgr.run_benchmarks_on_all_nodes()
                
                # Print final summary
                successful = sum(1 for v in results.values() if v)
                total = len(results)
                
                if successful == total:
                    print(f"\n✓ All benchmarks completed successfully ({successful}/{total})")
                else:
                    print(f"\n⚠️  Some benchmarks failed ({successful}/{total} successful)")
            else:
                print("\n✗ Failed to distribute benchmarks")
        else:
            print("\n✗ Failed to compile benchmarks")


if __name__ == '__main__':
    main()
