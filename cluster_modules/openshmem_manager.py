"""
OpenSHMEM Manager Module for HPC Cluster Setup

This module handles OpenSHMEM installation and configuration across the cluster, including:
- Sandia OpenSHMEM 1.5.2 download and compilation
- PMI support configuration
- Distribution to all cluster nodes
- oshcc/oshrun symlinks creation
- Multi-node testing

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import subprocess
import re
from pathlib import Path
from typing import Optional, List


class OpenSHMEMManager:
    """
    Manages OpenSHMEM installation and configuration across the cluster.
    
    Attributes:
        username (str): Username for cluster nodes
        password (str): Password for authentication (never hardcoded)
        master_ip (str): Master node IP address
        worker_ips (List[str]): List of worker node IP addresses
        all_ips (List[str]): All cluster node IPs
        build_node_ip (str): IP of the node used for building OpenSHMEM
        openshmem_version (str): Version of OpenSHMEM to install
        install_prefix (str): Installation directory for OpenSHMEM
    """
    
    def __init__(self, username: str, password: str, master_ip: str, worker_ips: List[str],
                 build_node_ip: Optional[str] = None, openshmem_version: str = "1.5.2"):
        """
        Initialize OpenSHMEM manager.
        
        Args:
            username: Username for cluster nodes
            password: Password for authentication
            master_ip: Master node IP address
            worker_ips: List of worker node IP addresses
            build_node_ip: IP of build node (defaults to master if None)
            openshmem_version: Version of OpenSHMEM to install
        """
        self.username = username
        self.password = password
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
        self.build_node_ip = build_node_ip or master_ip
        self.openshmem_version = openshmem_version
        self.install_prefix = f"/home/linuxbrew/.linuxbrew/openshmem-{openshmem_version}"
    
    def download_openshmem(self) -> bool:
        """
        Download Sandia OpenSHMEM source tarball.
        
        Returns:
            bool: True if download successful, False otherwise
        """
        print(f"\n=== Downloading OpenSHMEM {self.openshmem_version} ===")
        
        download_url = f"https://github.com/Sandia-OpenSHMEM/SOS/releases/download/v{self.openshmem_version}/sandia-openshmem-{self.openshmem_version}.tar.gz"
        
        download_dir = Path.home() / "openshmem_build"
        download_dir.mkdir(exist_ok=True)
        
        tarball_path = download_dir / f"sandia-openshmem-{self.openshmem_version}.tar.gz"
        
        if tarball_path.exists():
            print(f"✓ Tarball already exists at {tarball_path}")
            return True
        
        print(f"Downloading from {download_url}...")
        
        wget_cmd = ["wget", "-O", str(tarball_path), download_url]
        
        try:
            result = subprocess.run(wget_cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                print(f"✓ Downloaded OpenSHMEM {self.openshmem_version}")
                return True
            else:
                print(f"✗ Download failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Download timed out")
            return False
        except Exception as e:
            print(f"✗ Error downloading OpenSHMEM: {e}")
            return False
    
    def extract_openshmem(self) -> bool:
        """
        Extract OpenSHMEM tarball.
        
        Returns:
            bool: True if extraction successful, False otherwise
        """
        print("\n=== Extracting OpenSHMEM ===")
        
        download_dir = Path.home() / "openshmem_build"
        tarball_path = download_dir / f"sandia-openshmem-{self.openshmem_version}.tar.gz"
        
        if not tarball_path.exists():
            print(f"✗ Tarball not found at {tarball_path}")
            return False
        
        extract_dir = download_dir / f"sandia-openshmem-{self.openshmem_version}"
        
        if extract_dir.exists():
            print(f"✓ Already extracted at {extract_dir}")
            return True
        
        print(f"Extracting {tarball_path}...")
        
        tar_cmd = ["tar", "-xzf", str(tarball_path), "-C", str(download_dir)]
        
        try:
            result = subprocess.run(tar_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✓ Extracted to {extract_dir}")
                return True
            else:
                print(f"✗ Extraction failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error extracting OpenSHMEM: {e}")
            return False
    
    def configure_openshmem(self) -> bool:
        """
        Configure OpenSHMEM with PMI support.
        
        Returns:
            bool: True if configuration successful, False otherwise
        """
        print("\n=== Configuring OpenSHMEM ===")
        
        source_dir = Path.home() / "openshmem_build" / f"sandia-openshmem-{self.openshmem_version}"
        
        if not source_dir.exists():
            print(f"✗ Source directory not found: {source_dir}")
            return False
        
        # Get compiler paths from Homebrew
        gcc_path = subprocess.run(
            ["which", "gcc"],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        gxx_path = subprocess.run(
            ["which", "g++"],
            capture_output=True,
            text=True
        ).stdout.strip()
        
        configure_cmd = [
            "./configure",
            f"--prefix={self.install_prefix}",
            f"CC={gcc_path}",
            f"CXX={gxx_path}",
            "--enable-pmi-simple",
            "--with-pmix=/usr",
            "--enable-static",
            "--enable-shared"
        ]
        
        print(f"Configuring with prefix: {self.install_prefix}")
        print(f"Command: {' '.join(configure_cmd)}")
        
        try:
            result = subprocess.run(
                configure_cmd,
                cwd=source_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✓ Configuration successful")
                return True
            else:
                print(f"✗ Configuration failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error configuring OpenSHMEM: {e}")
            return False
    
    def build_openshmem(self, num_jobs: int = 8) -> bool:
        """
        Build OpenSHMEM using make.
        
        Args:
            num_jobs: Number of parallel build jobs
            
        Returns:
            bool: True if build successful, False otherwise
        """
        print(f"\n=== Building OpenSHMEM (using {num_jobs} jobs) ===")
        
        source_dir = Path.home() / "openshmem_build" / f"sandia-openshmem-{self.openshmem_version}"
        
        if not source_dir.exists():
            print(f"✗ Source directory not found: {source_dir}")
            return False
        
        make_cmd = ["make", f"-j{num_jobs}"]
        
        print("Building... (this may take several minutes)")
        
        try:
            result = subprocess.run(
                make_cmd,
                cwd=source_dir,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode == 0:
                print("✓ Build successful")
                return True
            else:
                print(f"✗ Build failed: {result.stderr[-1000:]}")  # Last 1000 chars
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Build timed out")
            return False
        except Exception as e:
            print(f"✗ Error building OpenSHMEM: {e}")
            return False
    
    def install_openshmem(self) -> bool:
        """
        Install OpenSHMEM to prefix directory.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        print("\n=== Installing OpenSHMEM ===")
        
        source_dir = Path.home() / "openshmem_build" / f"sandia-openshmem-{self.openshmem_version}"
        
        if not source_dir.exists():
            print(f"✗ Source directory not found: {source_dir}")
            return False
        
        make_install_cmd = ["make", "install"]
        
        try:
            result = subprocess.run(
                make_install_cmd,
                cwd=source_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print(f"✓ Installed to {self.install_prefix}")
                return True
            else:
                print(f"✗ Installation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error installing OpenSHMEM: {e}")
            return False
    
    def distribute_openshmem_pdsh(self) -> bool:
        """
        Distribute OpenSHMEM installation to all nodes using pdsh and rsync.
        
        Returns:
            bool: True if distribution successful, False otherwise
        """
        print("\n=== Distributing OpenSHMEM cluster-wide with pdsh ===")
        
        install_path = Path(self.install_prefix)
        
        if not install_path.exists():
            print(f"✗ Installation directory not found: {install_path}")
            return False
        
        # Get nodes to distribute to (exclude build node)
        target_nodes = [ip for ip in self.all_ips if ip != self.build_node_ip]
        
        if not target_nodes:
            print("No other nodes to distribute to")
            return True
        
        node_list = ",".join(target_nodes)
        
        # Use pdsh with rsync
        pdsh_cmd = [
            "pdsh",
            "-R", "ssh",
            "-w", node_list,
            f"mkdir -p {install_path.parent}"
        ]
        
        print(f"Creating installation directories on nodes: {node_list}")
        
        try:
            result = subprocess.run(pdsh_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"⚠ Failed to create directories via pdsh, falling back to sequential")
                return self._distribute_openshmem_sequential(target_nodes)
            
        except Exception as e:
            print(f"⚠ pdsh failed ({e}), falling back to sequential")
            return self._distribute_openshmem_sequential(target_nodes)
        
        # Distribute with rsync
        print(f"Distributing OpenSHMEM installation...")
        
        for node_ip in target_nodes:
            rsync_cmd = [
                "rsync", "-avz", "--delete",
                f"{install_path}/",
                f"{self.username}@{node_ip}:{install_path}/"
            ]
            
            try:
                result = subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✓ Distributed to {node_ip}")
                else:
                    print(f"✗ Failed to distribute to {node_ip}: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"✗ Error distributing to {node_ip}: {e}")
                return False
        
        print("✓ OpenSHMEM distributed to all nodes")
        return True
    
    def _distribute_openshmem_sequential(self, nodes: List[str]) -> bool:
        """
        Distribute OpenSHMEM sequentially to specified nodes.
        
        Args:
            nodes: List of node IPs to distribute to
            
        Returns:
            bool: True if all distributions successful, False otherwise
        """
        install_path = Path(self.install_prefix)
        all_success = True
        
        for node_ip in nodes:
            print(f"\nDistributing OpenSHMEM to {node_ip}...")
            
            # Create directory
            mkdir_cmd = [
                "sshpass", "-p", self.password,
                "ssh", "-o", "StrictHostKeyChecking=no",
                f"{self.username}@{node_ip}",
                f"mkdir -p {install_path.parent}"
            ]
            
            subprocess.run(mkdir_cmd, capture_output=True)
            
            # Rsync installation
            rsync_cmd = [
                "rsync", "-avz", "--delete",
                "-e", f"sshpass -p {self.password} ssh -o StrictHostKeyChecking=no",
                f"{install_path}/",
                f"{self.username}@{node_ip}:{install_path}/"
            ]
            
            try:
                result = subprocess.run(rsync_cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print(f"✓ Distributed to {node_ip}")
                else:
                    print(f"✗ Failed to distribute to {node_ip}")
                    all_success = False
                    
            except Exception as e:
                print(f"✗ Error distributing to {node_ip}: {e}")
                all_success = False
        
        return all_success
    
    def create_wrapper_symlinks(self) -> bool:
        """
        Create oshcc and oshrun symlinks in /usr/local/bin.
        
        Returns:
            bool: True if symlinks created successfully, False otherwise
        """
        print("\n=== Creating OpenSHMEM wrapper symlinks ===")
        
        install_path = Path(self.install_prefix)
        oshcc_binary = install_path / "bin" / "oshcc"
        oshrun_binary = install_path / "bin" / "oshrun"
        
        if not oshcc_binary.exists():
            print(f"✗ oshcc not found at {oshcc_binary}")
            return False
        
        if not oshrun_binary.exists():
            print(f"✗ oshrun not found at {oshrun_binary}")
            return False
        
        symlinks = [
            (oshcc_binary, "/usr/local/bin/oshcc"),
            (oshrun_binary, "/usr/local/bin/oshrun")
        ]
        
        for source, target in symlinks:
            print(f"Creating symlink: {target} -> {source}")
            
            ln_cmd = ["sudo", "ln", "-sf", str(source), target]
            
            try:
                result = subprocess.run(ln_cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print(f"✓ Created {target}")
                else:
                    print(f"✗ Failed to create {target}: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"✗ Error creating symlink: {e}")
                return False
        
        return True
    
    def test_openshmem_local(self) -> bool:
        """
        Test OpenSHMEM installation on local node.
        
        Returns:
            bool: True if test successful, False otherwise
        """
        print("\n=== Testing OpenSHMEM locally ===")
        
        # Create simple test program
        test_code = """
#include <shmem.h>
#include <stdio.h>

int main(void) {
    shmem_init();
    int me = shmem_my_pe();
    int npes = shmem_n_pes();
    printf("PE %d of %d\\n", me, npes);
    shmem_finalize();
    return 0;
}
"""
        
        test_dir = Path.home() / "openshmem_test"
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test_openshmem.c"
        test_file.write_text(test_code)
        
        # Compile
        oshcc_path = Path(self.install_prefix) / "bin" / "oshcc"
        compile_cmd = [
            str(oshcc_path),
            str(test_file),
            "-o", str(test_dir / "test_openshmem")
        ]
        
        print("Compiling OpenSHMEM test program...")
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"✗ Compilation failed: {result.stderr}")
            return False
        
        print("✓ Compilation successful")
        
        # Run
        oshrun_path = Path(self.install_prefix) / "bin" / "oshrun"
        run_cmd = [str(oshrun_path), "-n", "2", str(test_dir / "test_openshmem")]
        
        print("Running OpenSHMEM test program...")
        result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print(f"✗ Execution failed: {result.stderr}")
            return False
        
        print("✓ OpenSHMEM test successful")
        print(result.stdout)
        return True


if __name__ == "__main__":
    # Example usage
    print("OpenSHMEM Manager Module")
    print("Import this module to use OpenSHMEMManager class")
