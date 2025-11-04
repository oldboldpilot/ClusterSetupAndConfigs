"""
OpenMP Manager Module for HPC Cluster Setup

This module handles OpenMP configuration across the cluster, including:
- libomp installation via Homebrew
- Compiler flag configuration
- Thread-level parallelism testing
- Environment variable setup

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import subprocess
import os
import re
from pathlib import Path
from typing import Optional, List, Tuple


class OpenMPManager:
    """
    Manages OpenMP configuration and testing across the cluster.
    
    Attributes:
        username (str): Username for cluster nodes
        password (str): Password for authentication (never hardcoded)
        master_ip (str): Master node IP address
        worker_ips (List[str]): List of worker node IP addresses
        all_ips (List[str]): All cluster node IPs
    """
    
    def __init__(self, username: str, password: str, master_ip: str, worker_ips: List[str]):
        """
        Initialize OpenMP manager.
        
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
    
    def install_libomp_local(self) -> bool:
        """
        Install libomp via Homebrew on local node.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        print("Installing libomp via Homebrew...")
        
        try:
            # Check if already installed
            check_cmd = ["brew", "list", "libomp"]
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ libomp already installed")
                return True
            
            # Install libomp
            install_cmd = ["brew", "install", "libomp"]
            result = subprocess.run(install_cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print("✓ libomp installed successfully")
                return True
            else:
                print(f"✗ Failed to install libomp: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ libomp installation timed out")
            return False
        except Exception as e:
            print(f"✗ Error installing libomp: {e}")
            return False
    
    def install_libomp_cluster_pdsh(self) -> bool:
        """
        Install libomp on all cluster nodes using pdsh for parallel execution.
        
        Returns:
            bool: True if installation successful on all nodes, False otherwise
        """
        print("\n=== Installing libomp cluster-wide with pdsh ===")
        
        # Install locally first
        if not self.install_libomp_local():
            print("Failed to install libomp locally, aborting cluster installation")
            return False
        
        # Get other nodes to install on
        other_nodes = [ip for ip in self.all_ips if ip != self._get_local_ip()]
        
        if not other_nodes:
            print("No other nodes to install on")
            return True
        
        # Try pdsh for parallel installation
        node_list = ",".join(other_nodes)
        
        pdsh_cmd = [
            "pdsh",
            "-R", "ssh",
            "-w", node_list,
            "brew install libomp"
        ]
        
        print(f"Installing libomp on nodes: {node_list}")
        
        try:
            result = subprocess.run(pdsh_cmd, capture_output=True, text=True, timeout=900)
            
            if result.returncode == 0:
                print("✓ libomp installed successfully on all nodes")
                return True
            else:
                print(f"⚠ pdsh installation had issues, falling back to sequential")
                return self._install_libomp_sequential(other_nodes)
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            print(f"⚠ pdsh failed ({e}), falling back to sequential installation")
            return self._install_libomp_sequential(other_nodes)
    
    def _install_libomp_sequential(self, nodes: List[str]) -> bool:
        """
        Install libomp sequentially on specified nodes.
        
        Args:
            nodes: List of node IPs to install on
            
        Returns:
            bool: True if all installations successful, False otherwise
        """
        all_success = True
        
        for node_ip in nodes:
            print(f"\nInstalling libomp on {node_ip}...")
            
            ssh_cmd = [
                "sshpass", "-p", self.password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"{self.username}@{node_ip}",
                "brew install libomp"
            ]
            
            try:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    print(f"✓ libomp installed on {node_ip}")
                else:
                    print(f"✗ Failed to install libomp on {node_ip}: {result.stderr}")
                    all_success = False
                    
            except Exception as e:
                print(f"✗ Error installing libomp on {node_ip}: {e}")
                all_success = False
        
        return all_success
    
    def get_openmp_compiler_flags(self) -> Tuple[str, str]:
        """
        Get OpenMP compiler flags for GCC.
        
        Returns:
            Tuple[str, str]: (CFLAGS, LDFLAGS) for OpenMP
        """
        libomp_prefix = subprocess.run(
            ["brew", "--prefix", "libomp"],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        if not libomp_prefix:
            libomp_prefix = "/home/linuxbrew/.linuxbrew/opt/libomp"
        
        cflags = f"-fopenmp -I{libomp_prefix}/include"
        ldflags = f"-L{libomp_prefix}/lib -lomp"
        
        return cflags, ldflags
    
    def test_openmp_local(self, num_threads: int = 4) -> bool:
        """
        Test OpenMP functionality on local node.
        
        Args:
            num_threads: Number of threads to test with
            
        Returns:
            bool: True if test successful, False otherwise
        """
        print(f"\nTesting OpenMP with {num_threads} threads...")
        
        # Create test program
        test_code = """
#include <stdio.h>
#include <omp.h>

int main() {
    #pragma omp parallel
    {
        int thread_id = omp_get_thread_num();
        int total_threads = omp_get_num_threads();
        #pragma omp critical
        printf("Thread %d of %d\\n", thread_id, total_threads);
    }
    return 0;
}
"""
        
        test_dir = Path.home() / "openmp_test"
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test_openmp.c"
        test_file.write_text(test_code)
        
        # Get compiler flags
        cflags, ldflags = self.get_openmp_compiler_flags()
        
        # Compile test program
        compile_cmd = [
            "gcc",
            str(test_file),
            "-o", str(test_dir / "test_openmp"),
            *cflags.split(),
            *ldflags.split()
        ]
        
        print("Compiling OpenMP test program...")
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Compilation failed: {result.stderr}")
            return False
        
        print("✓ Compilation successful")
        
        # Run test program
        env = {"OMP_NUM_THREADS": str(num_threads)}
        run_cmd = [str(test_dir / "test_openmp")]
        
        print("Running OpenMP test program...")
        result = subprocess.run(run_cmd, capture_output=True, text=True, env={**os.environ, **env})
        
        if result.returncode != 0:
            print(f"✗ Execution failed: {result.stderr}")
            return False
        
        # Check output
        output_lines = result.stdout.strip().split('\n')
        thread_count = len(output_lines)
        
        if thread_count == num_threads:
            print(f"✓ OpenMP test successful: {thread_count} threads executed")
            print(result.stdout)
            return True
        else:
            print(f"✗ Expected {num_threads} threads, got {thread_count}")
            return False
    
    def test_openmp_cluster(self, num_threads: int = 4) -> bool:
        """
        Test OpenMP on all cluster nodes.
        
        Args:
            num_threads: Number of threads to test with
            
        Returns:
            bool: True if all tests successful, False otherwise
        """
        print("\n=== Testing OpenMP cluster-wide ===")
        
        all_success = True
        
        for node_ip in self.all_ips:
            print(f"\nTesting OpenMP on {node_ip}...")
            
            # For local node, test directly
            if node_ip == self._get_local_ip():
                if not self.test_openmp_local(num_threads):
                    all_success = False
                continue
            
            # For remote nodes, test via SSH
            test_cmd = f"""
mkdir -p ~/openmp_test
cat > ~/openmp_test/test_openmp.c << 'EOF'
#include <stdio.h>
#include <omp.h>

int main() {{
    #pragma omp parallel
    {{
        int thread_id = omp_get_thread_num();
        int total_threads = omp_get_num_threads();
        #pragma omp critical
        printf("Thread %d of %d\\\\n", thread_id, total_threads);
    }}
    return 0;
}}
EOF

gcc ~/openmp_test/test_openmp.c -o ~/openmp_test/test_openmp -fopenmp -I$(brew --prefix libomp)/include -L$(brew --prefix libomp)/lib -lomp
OMP_NUM_THREADS={num_threads} ~/openmp_test/test_openmp
"""
            
            ssh_cmd = [
                "sshpass", "-p", self.password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"{self.username}@{node_ip}",
                test_cmd
            ]
            
            try:
                result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    output_lines = result.stdout.strip().split('\n')
                    thread_count = len([line for line in output_lines if "Thread" in line])
                    
                    if thread_count == num_threads:
                        print(f"✓ OpenMP test successful on {node_ip}: {thread_count} threads")
                    else:
                        print(f"✗ Expected {num_threads} threads on {node_ip}, got {thread_count}")
                        all_success = False
                else:
                    print(f"✗ OpenMP test failed on {node_ip}: {result.stderr}")
                    all_success = False
                    
            except Exception as e:
                print(f"✗ Error testing OpenMP on {node_ip}: {e}")
                all_success = False
        
        return all_success
    
    def _get_local_ip(self) -> Optional[str]:
        """
        Get local node IP address.
        
        Returns:
            Optional[str]: Local IP address or None if not found
        """
        try:
            # Try to get IP from hostname
            hostname_result = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
            if hostname_result.returncode == 0:
                local_ips = hostname_result.stdout.strip().split()
                # Check if any local IP matches cluster IPs
                for ip in local_ips:
                    if ip in self.all_ips:
                        return ip
            
            # Default to master if can't determine
            return self.master_ip
            
        except Exception:
            return self.master_ip
