"""
Berkeley UPC (Unified Parallel C) Manager Module

This module handles the installation, configuration, and testing of Berkeley UPC,
a compiler and runtime implementation of Unified Parallel C (UPC) for parallel programming.

Berkeley UPC Features:
- Partitioned Global Address Space (PGAS) programming model
- C language extensions for parallel programming
- Support for distributed shared memory
- MPI and GASNet network backends
- Static and dynamic thread modes
- Collective operations and synchronization primitives

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import subprocess
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict


class BerkeleyUPCManager:
    """
    Manages Berkeley UPC installation, configuration, and testing across the cluster.
    
    Berkeley UPC provides a C-based PGAS programming model with:
    - Shared memory abstractions across distributed nodes
    - Efficient one-sided communication
    - Integration with MPI and GASNet conduits
    - Static and dynamic thread allocation
    
    Attributes:
        username (str): Cluster username for SSH operations
        password (str): Cluster password (never stored, only passed for operations)
        master_ip (str): IP address of the master node
        worker_ips (List[str]): List of worker node IP addresses
        all_ips (List[str]): Combined list of all node IPs
        berkeley_upc_version (str): Version of Berkeley UPC to install
        install_prefix (str): Installation directory
        gasnet_conduit (str): GASNet conduit (mpi, udp, smp, ibv)
        enable_pthreads (bool): Enable POSIX threads support
    """
    
    def __init__(
        self,
        username: str,
        password: str,
        master_ip: str,
        worker_ips: List[str],
        berkeley_upc_version: str = "2023.9.0",
        install_prefix: str = "/home/linuxbrew/.linuxbrew",
        gasnet_conduit: str = "mpi",
        enable_pthreads: bool = True
    ):
        """
        Initialize Berkeley UPC Manager.
        
        Args:
            username: Cluster username for SSH and remote operations
            password: Cluster password (used only for sshpass, never stored)
            master_ip: IP address of the master node
            worker_ips: List of worker node IP addresses
            berkeley_upc_version: Berkeley UPC version (default: 2023.9.0)
            install_prefix: Installation directory (default: /home/linuxbrew/.linuxbrew)
            gasnet_conduit: GASNet network conduit (default: mpi)
            enable_pthreads: Enable POSIX threads support (default: True)
        """
        self.username = username
        self.password = password
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
        self.berkeley_upc_version = berkeley_upc_version
        self.install_prefix = install_prefix
        self.gasnet_conduit = gasnet_conduit
        self.enable_pthreads = enable_pthreads
        
        # Derived paths
        self.bupc_dir = f"{install_prefix}/berkeley-upc-{berkeley_upc_version}"
        self.bupc_bin = f"{self.bupc_dir}/bin"
        self.source_dir = Path.home() / "bupc_build"
        self.tarball = self.source_dir / f"berkeley_upc-{berkeley_upc_version}.tar.gz"
        
        print(f"[BerkeleyUPCManager] Initialized for Berkeley UPC {berkeley_upc_version}")
        print(f"[BerkeleyUPCManager] Install prefix: {install_prefix}")
        print(f"[BerkeleyUPCManager] GASNet conduit: {gasnet_conduit}")
    
    def download_berkeley_upc(self) -> bool:
        """
        Download Berkeley UPC source tarball from official repository.
        
        Downloads from: https://upc.lbl.gov/download/release/
        
        Returns:
            bool: True if download successful, False otherwise
        """
        print(f"\n[BerkeleyUPCManager] Downloading Berkeley UPC {self.berkeley_upc_version}...")
        
        try:
            # Create build directory
            self.source_dir.mkdir(parents=True, exist_ok=True)
            
            # Berkeley UPC download URL
            download_url = f"https://upc.lbl.gov/download/release/berkeley_upc-{self.berkeley_upc_version}.tar.gz"
            
            print(f"[BerkeleyUPCManager] Download URL: {download_url}")
            print(f"[BerkeleyUPCManager] Target: {self.tarball}")
            
            # Download with wget
            result = subprocess.run(
                ["wget", "-O", str(self.tarball), download_url],
                capture_output=True,
                text=True,
                cwd=str(self.source_dir)
            )
            
            if result.returncode != 0:
                print(f"[BerkeleyUPCManager] ✗ Download failed: {result.stderr}")
                return False
            
            # Verify tarball exists and has content
            if not self.tarball.exists() or self.tarball.stat().st_size == 0:
                print(f"[BerkeleyUPCManager] ✗ Downloaded file is empty or missing")
                return False
            
            size_mb = self.tarball.stat().st_size / (1024 * 1024)
            print(f"[BerkeleyUPCManager] ✓ Downloaded successfully ({size_mb:.2f} MB)")
            return True
            
        except Exception as e:
            print(f"[BerkeleyUPCManager] ✗ Exception during download: {e}")
            return False
    
    def extract_berkeley_upc(self) -> bool:
        """
        Extract Berkeley UPC source tarball.
        
        Returns:
            bool: True if extraction successful, False otherwise
        """
        print(f"\n[BerkeleyUPCManager] Extracting Berkeley UPC tarball...")
        
        try:
            if not self.tarball.exists():
                print(f"[BerkeleyUPCManager] ✗ Tarball not found: {self.tarball}")
                return False
            
            # Extract tarball
            result = subprocess.run(
                ["tar", "-xzf", str(self.tarball)],
                capture_output=True,
                text=True,
                cwd=str(self.source_dir)
            )
            
            if result.returncode != 0:
                print(f"[BerkeleyUPCManager] ✗ Extraction failed: {result.stderr}")
                return False
            
            # Verify extracted directory exists
            extracted_dir = self.source_dir / f"berkeley_upc-{self.berkeley_upc_version}"
            if not extracted_dir.exists():
                print(f"[BerkeleyUPCManager] ✗ Extracted directory not found: {extracted_dir}")
                return False
            
            print(f"[BerkeleyUPCManager] ✓ Extracted to: {extracted_dir}")
            return True
            
        except Exception as e:
            print(f"[BerkeleyUPCManager] ✗ Exception during extraction: {e}")
            return False
    
    def configure_berkeley_upc(self) -> bool:
        """
        Configure Berkeley UPC build with GASNet conduit and options.
        
        Configuration options:
        - --prefix: Installation directory
        - --with-multiconf: Enable multi-configuration build
        - --enable-pthreads: Enable POSIX threads support
        - --with-gasnet-conduit: Network conduit (mpi, udp, smp, ibv)
        - --disable-aligned-segments: More flexible memory layout
        
        Returns:
            bool: True if configuration successful, False otherwise
        """
        print(f"\n[BerkeleyUPCManager] Configuring Berkeley UPC...")
        
        try:
            build_dir = self.source_dir / f"berkeley_upc-{self.berkeley_upc_version}"
            
            if not build_dir.exists():
                print(f"[BerkeleyUPCManager] ✗ Build directory not found: {build_dir}")
                return False
            
            # Build configuration command
            config_cmd = [
                "./configure",
                f"--prefix={self.bupc_dir}",
                "--with-multiconf",
                f"--with-gasnet-conduit={self.gasnet_conduit}",
                "--disable-aligned-segments"
            ]
            
            if self.enable_pthreads:
                config_cmd.append("--enable-pthreads")
            
            # Set CC and CXX to GCC
            env = os.environ.copy()
            env["CC"] = "gcc"
            env["CXX"] = "g++"
            
            print(f"[BerkeleyUPCManager] Configuration command:")
            print(f"  {' '.join(config_cmd)}")
            print(f"[BerkeleyUPCManager] Using CC={env['CC']}, CXX={env['CXX']}")
            
            # Run configure
            result = subprocess.run(
                config_cmd,
                capture_output=True,
                text=True,
                cwd=str(build_dir),
                env=env
            )
            
            if result.returncode != 0:
                print(f"[BerkeleyUPCManager] ✗ Configuration failed:")
                print(result.stderr)
                return False
            
            print(f"[BerkeleyUPCManager] ✓ Configuration successful")
            print(f"[BerkeleyUPCManager]   Prefix: {self.bupc_dir}")
            print(f"[BerkeleyUPCManager]   Conduit: {self.gasnet_conduit}")
            print(f"[BerkeleyUPCManager]   Pthreads: {'enabled' if self.enable_pthreads else 'disabled'}")
            return True
            
        except Exception as e:
            print(f"[BerkeleyUPCManager] ✗ Exception during configuration: {e}")
            return False
    
    def build_berkeley_upc(self, num_jobs: int = 8) -> bool:
        """
        Compile Berkeley UPC using parallel make.
        
        Args:
            num_jobs: Number of parallel make jobs (default: 8)
        
        Returns:
            bool: True if build successful, False otherwise
        """
        print(f"\n[BerkeleyUPCManager] Building Berkeley UPC with {num_jobs} parallel jobs...")
        
        try:
            build_dir = self.source_dir / f"berkeley_upc-{self.berkeley_upc_version}"
            
            if not build_dir.exists():
                print(f"[BerkeleyUPCManager] ✗ Build directory not found: {build_dir}")
                return False
            
            # Run make with parallel jobs
            result = subprocess.run(
                ["make", f"-j{num_jobs}"],
                capture_output=True,
                text=True,
                cwd=str(build_dir)
            )
            
            if result.returncode != 0:
                print(f"[BerkeleyUPCManager] ✗ Build failed:")
                print(result.stderr[-2000:])  # Last 2000 chars of error
                return False
            
            print(f"[BerkeleyUPCManager] ✓ Build successful")
            return True
            
        except Exception as e:
            print(f"[BerkeleyUPCManager] ✗ Exception during build: {e}")
            return False
    
    def install_berkeley_upc(self) -> bool:
        """
        Install Berkeley UPC to the specified prefix.
        
        Returns:
            bool: True if installation successful, False otherwise
        """
        print(f"\n[BerkeleyUPCManager] Installing Berkeley UPC to {self.bupc_dir}...")
        
        try:
            build_dir = self.source_dir / f"berkeley_upc-{self.berkeley_upc_version}"
            
            if not build_dir.exists():
                print(f"[BerkeleyUPCManager] ✗ Build directory not found: {build_dir}")
                return False
            
            # Run make install
            result = subprocess.run(
                ["make", "install"],
                capture_output=True,
                text=True,
                cwd=str(build_dir)
            )
            
            if result.returncode != 0:
                print(f"[BerkeleyUPCManager] ✗ Installation failed:")
                print(result.stderr)
                return False
            
            # Verify installation
            upcc_path = Path(self.bupc_bin) / "upcc"
            upcrun_path = Path(self.bupc_bin) / "upcrun"
            
            if not upcc_path.exists() or not upcrun_path.exists():
                print(f"[BerkeleyUPCManager] ✗ Installation incomplete:")
                print(f"  upcc exists: {upcc_path.exists()}")
                print(f"  upcrun exists: {upcrun_path.exists()}")
                return False
            
            print(f"[BerkeleyUPCManager] ✓ Installation successful")
            print(f"[BerkeleyUPCManager]   upcc: {upcc_path}")
            print(f"[BerkeleyUPCManager]   upcrun: {upcrun_path}")
            return True
            
        except Exception as e:
            print(f"[BerkeleyUPCManager] ✗ Exception during installation: {e}")
            return False
    
    def distribute_berkeley_upc_pdsh(self) -> bool:
        """
        Distribute Berkeley UPC installation to all cluster nodes using pdsh + rsync.
        
        Uses parallel distribution with pdsh for efficiency.
        Falls back to sequential distribution if pdsh fails.
        
        Returns:
            bool: True if distribution successful, False otherwise
        """
        print(f"\n[BerkeleyUPCManager] Distributing Berkeley UPC to cluster nodes...")
        
        try:
            # Verify local installation exists
            if not Path(self.bupc_dir).exists():
                print(f"[BerkeleyUPCManager] ✗ Local installation not found: {self.bupc_dir}")
                return False
            
            # Create hostfile for pdsh
            hostfile = Path.home() / ".cluster_hostfile"
            with open(hostfile, 'w') as f:
                for ip in self.worker_ips:
                    f.write(f"{ip}\n")
            
            print(f"[BerkeleyUPCManager] Using pdsh for parallel distribution...")
            
            # Use pdsh to rsync to all nodes in parallel
            pdsh_cmd = [
                "pdsh",
                "-w", f"^{hostfile}",
                "rsync", "-avz", "--delete",
                f"{self.username}@{self.master_ip}:{self.bupc_dir}/",
                f"{self.bupc_dir}/"
            ]
            
            result = subprocess.run(
                pdsh_cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[BerkeleyUPCManager] ✓ Parallel distribution successful")
                return True
            else:
                print(f"[BerkeleyUPCManager] ⚠ pdsh failed, falling back to sequential distribution")
                return self._distribute_sequential()
                
        except Exception as e:
            print(f"[BerkeleyUPCManager] ⚠ Exception during pdsh distribution: {e}")
            print(f"[BerkeleyUPCManager] Falling back to sequential distribution...")
            return self._distribute_sequential()
    
    def _distribute_sequential(self) -> bool:
        """
        Distribute Berkeley UPC to nodes sequentially using rsync.
        
        Returns:
            bool: True if all distributions successful, False otherwise
        """
        print(f"[BerkeleyUPCManager] Sequential distribution to {len(self.worker_ips)} nodes...")
        
        all_success = True
        for ip in self.worker_ips:
            print(f"[BerkeleyUPCManager] Distributing to {ip}...")
            
            result = subprocess.run(
                [
                    "rsync", "-avz", "--delete",
                    f"{self.bupc_dir}/",
                    f"{self.username}@{ip}:{self.bupc_dir}/"
                ],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[BerkeleyUPCManager] ✓ {ip} - Success")
            else:
                print(f"[BerkeleyUPCManager] ✗ {ip} - Failed: {result.stderr}")
                all_success = False
        
        return all_success
    
    def create_wrapper_scripts(self) -> bool:
        """
        Create wrapper scripts for upcc and upcrun in system PATH.
        
        Creates symlinks in /usr/local/bin pointing to Berkeley UPC binaries.
        
        Returns:
            bool: True if wrapper creation successful, False otherwise
        """
        print(f"\n[BerkeleyUPCManager] Creating wrapper scripts...")
        
        try:
            wrappers = {
                "upcc": f"{self.bupc_bin}/upcc",
                "upcrun": f"{self.bupc_bin}/upcrun"
            }
            
            for wrapper_name, target_path in wrappers.items():
                wrapper_path = f"/usr/local/bin/{wrapper_name}"
                
                # Check if target exists
                if not Path(target_path).exists():
                    print(f"[BerkeleyUPCManager] ✗ Target not found: {target_path}")
                    continue
                
                # Remove existing symlink/file if present
                if Path(wrapper_path).exists():
                    subprocess.run(["sudo", "rm", "-f", wrapper_path], check=True)
                
                # Create symlink
                result = subprocess.run(
                    ["sudo", "ln", "-s", target_path, wrapper_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print(f"[BerkeleyUPCManager] ✓ Created: {wrapper_path} -> {target_path}")
                else:
                    print(f"[BerkeleyUPCManager] ✗ Failed to create {wrapper_name}: {result.stderr}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"[BerkeleyUPCManager] ✗ Exception creating wrappers: {e}")
            return False
    
    def test_berkeley_upc_local(self) -> bool:
        """
        Test Berkeley UPC installation on local node.
        
        Creates, compiles, and runs a simple "Hello World" UPC program.
        
        Returns:
            bool: True if test successful, False otherwise
        """
        print(f"\n[BerkeleyUPCManager] Testing Berkeley UPC on local node...")
        
        try:
            # Create test directory
            test_dir = Path.home() / "bupc_test"
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Create simple UPC test program
            test_program = test_dir / "hello_upc.c"
            test_code = """
#include <upc.h>
#include <stdio.h>

int main() {
    printf("Hello from UPC thread %d of %d\\n", MYTHREAD, THREADS);
    return 0;
}
"""
            test_program.write_text(test_code)
            print(f"[BerkeleyUPCManager] Created test program: {test_program}")
            
            # Compile with upcc
            upcc_path = f"{self.bupc_bin}/upcc"
            compile_result = subprocess.run(
                [upcc_path, "-o", str(test_dir / "hello_upc"), str(test_program)],
                capture_output=True,
                text=True
            )
            
            if compile_result.returncode != 0:
                print(f"[BerkeleyUPCManager] ✗ Compilation failed:")
                print(compile_result.stderr)
                return False
            
            print(f"[BerkeleyUPCManager] ✓ Compilation successful")
            
            # Run with upcrun (2 threads)
            upcrun_path = f"{self.bupc_bin}/upcrun"
            run_result = subprocess.run(
                [upcrun_path, "-n", "2", str(test_dir / "hello_upc")],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if run_result.returncode != 0:
                print(f"[BerkeleyUPCManager] ✗ Execution failed:")
                print(run_result.stderr)
                return False
            
            print(f"[BerkeleyUPCManager] ✓ Execution successful")
            print(f"[BerkeleyUPCManager] Output:")
            for line in run_result.stdout.strip().split('\n'):
                print(f"  {line}")
            
            return True
            
        except Exception as e:
            print(f"[BerkeleyUPCManager] ✗ Exception during testing: {e}")
            return False
    
    def get_berkeley_upc_version_info(self) -> Optional[Dict[str, str]]:
        """
        Get Berkeley UPC version and configuration information.
        
        Returns:
            Optional[Dict[str, str]]: Dictionary with version info, or None if failed
        """
        try:
            upcc_path = f"{self.bupc_bin}/upcc"
            
            if not Path(upcc_path).exists():
                return None
            
            result = subprocess.run(
                [upcc_path, "-V"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return None
            
            # Parse version output
            version_info = {
                "version": "unknown",
                "gasnet_conduit": "unknown",
                "upcc_path": upcc_path
            }
            
            for line in result.stdout.split('\n'):
                if "Berkeley UPC" in line:
                    match = re.search(r'(\d+\.\d+\.\d+)', line)
                    if match:
                        version_info["version"] = match.group(1)
                elif "GASNet conduit" in line:
                    match = re.search(r'conduit:\s*(\w+)', line, re.IGNORECASE)
                    if match:
                        version_info["gasnet_conduit"] = match.group(1)
            
            return version_info
            
        except Exception as e:
            print(f"[BerkeleyUPCManager] Exception getting version info: {e}")
            return None
    
    def install_full_workflow(self, num_jobs: int = 8) -> bool:
        """
        Execute complete Berkeley UPC installation workflow.
        
        Workflow steps:
        1. Download source tarball
        2. Extract tarball
        3. Configure build
        4. Compile with parallel make
        5. Install to prefix
        6. Distribute to cluster nodes
        7. Create wrapper scripts
        8. Test installation
        
        Args:
            num_jobs: Number of parallel make jobs (default: 8)
        
        Returns:
            bool: True if all steps successful, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"Berkeley UPC Full Installation Workflow")
        print(f"{'='*60}\n")
        
        steps = [
            ("Download", lambda: self.download_berkeley_upc()),
            ("Extract", lambda: self.extract_berkeley_upc()),
            ("Configure", lambda: self.configure_berkeley_upc()),
            ("Build", lambda: self.build_berkeley_upc(num_jobs)),
            ("Install", lambda: self.install_berkeley_upc()),
            ("Distribute", lambda: self.distribute_berkeley_upc_pdsh()),
            ("Wrappers", lambda: self.create_wrapper_scripts()),
            ("Test", lambda: self.test_berkeley_upc_local())
        ]
        
        for step_name, step_func in steps:
            print(f"\n[Step: {step_name}]")
            if not step_func():
                print(f"\n{'='*60}")
                print(f"✗ Workflow failed at step: {step_name}")
                print(f"{'='*60}\n")
                return False
        
        print(f"\n{'='*60}")
        print(f"✓ Berkeley UPC installation workflow complete!")
        print(f"{'='*60}\n")
        
        # Display version info
        version_info = self.get_berkeley_upc_version_info()
        if version_info:
            print(f"Installation Summary:")
            print(f"  Version: {version_info['version']}")
            print(f"  GASNet Conduit: {version_info['gasnet_conduit']}")
            print(f"  upcc: {version_info['upcc_path']}")
            print(f"  Installation: {self.bupc_dir}")
        
        return True


# Example usage
if __name__ == "__main__":
    import getpass
    
    # Get cluster configuration
    master_ip = "192.168.1.147"
    worker_ips = ["192.168.1.139", "192.168.1.96", "192.168.1.136"]
    username = "muyiwa"
    password = getpass.getpass("Enter cluster password: ")
    
    # Initialize manager
    bupc_mgr = BerkeleyUPCManager(
        username=username,
        password=password,
        master_ip=master_ip,
        worker_ips=worker_ips,
        berkeley_upc_version="2023.9.0",
        gasnet_conduit="mpi",
        enable_pthreads=True
    )
    
    # Run full installation workflow
    success = bupc_mgr.install_full_workflow(num_jobs=8)
    
    if success:
        print("\n✓ Berkeley UPC ready for use!")
        print(f"\nUsage:")
        print(f"  upcc -o myprogram myprogram.c")
        print(f"  upcrun -n 4 ./myprogram")
    else:
        print("\n✗ Berkeley UPC installation failed")
