"""
PGAS (Partitioned Global Address Space) Manager

Handles installation and configuration of PGAS libraries:
- GASNet-EX: Communication layer for PGAS languages
- UPC++: Berkeley PGAS library for C++
- OpenSHMEM: Sandia PGAS implementation
- Berkeley UPC: PGAS library for C (via berkeley_upc_manager)

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
from .core import ClusterCore


class PGASManager:
    """Manage PGAS library installation and configuration"""
    
    def __init__(self, core: ClusterCore):
        """
        Initialize PGAS manager
        
        Args:
            core: ClusterCore instance for command execution
        """
        self.core = core
        self.install_prefix = "/home/linuxbrew/.linuxbrew"
        self.build_dir = Path.home() / "cluster_build_sources"
        
    def install_pgas_libraries_local(self):
        """
        Install all PGAS libraries on local node
        
        Installs:
        1. GASNet-EX 2024.5.0 (communication layer)
        2. UPC++ 2024.3.0 (Berkeley PGAS for C++)
        3. OpenSHMEM 1.5.2 (Sandia implementation)
        """
        print("\n=== Installing PGAS Libraries (GASNet-EX, UPC++, OpenSHMEM) ===")
        
        # Create build directory
        self.build_dir.mkdir(exist_ok=True)
        print(f"Build directory: {self.build_dir}")
        
        # Check build dependencies
        self._check_build_dependencies()
        
        # Install required Homebrew packages
        self._install_homebrew_dependencies()
        
        # Create system symlinks for binutils and Python
        self._create_system_symlinks()
        
        # Install PGAS components
        gasnet_install = self._install_gasnet_ex()
        if gasnet_install:
            upcxx_install = self._install_upcxx(gasnet_install)
            if upcxx_install:
                self._create_upcxx_symlinks(upcxx_install)
        
        oshmem_install = self._install_openshmem()
        
        # Update environment
        self._update_shell_environment(gasnet_install, upcxx_install, oshmem_install)
        
        # Verify installation
        self._verify_pgas_installation(upcxx_install)
        
        print("\n✓ PGAS libraries installation completed")
    
    def _check_build_dependencies(self):
        """Check and install required build tools"""
        print("Checking build dependencies...")
        required_tools = ["wget", "tar", "make", "curl"]
        
        for tool in required_tools:
            result = self.core.run_command(f"which {tool}", check=False)
            if result.returncode != 0:
                print(f"  Installing {tool}...")
                if self.core.pkg_manager == 'dnf':
                    self.core.run_sudo_command(f"dnf install -y {tool}")
                else:
                    self.core.run_sudo_command(f"apt-get install -y {tool}")
    
    def _install_homebrew_dependencies(self):
        """Install required Homebrew packages for PGAS"""
        print("Installing required Homebrew packages...")
        brew_cmd = f"{self.install_prefix}/bin/brew"
        required_packages = ["glibc", "binutils", "python3"]
        
        for pkg in required_packages:
            result = self.core.run_command(f"{brew_cmd} list {pkg}", check=False)
            if result.returncode != 0:
                print(f"  Installing {pkg}...")
                self.core.run_command(f"{brew_cmd} install {pkg}")
    
    def _create_system_symlinks(self):
        """Create system symlinks for binutils and Python"""
        print("Creating system symlinks for binutils and Python...")
        
        symlinks = {
            f"{self.install_prefix}/opt/binutils/bin/as": "/usr/local/bin/as",
            f"{self.install_prefix}/opt/binutils/bin/ld": "/usr/local/bin/ld",
            f"{self.install_prefix}/opt/binutils/bin/ar": "/usr/local/bin/ar",
            f"{self.install_prefix}/opt/binutils/bin/ranlib": "/usr/local/bin/ranlib",
            f"{self.install_prefix}/bin/python3": "/usr/local/bin/python3",
            f"{self.install_prefix}/bin/pip3": "/usr/local/bin/pip3",
        }
        
        for source, target in symlinks.items():
            if os.path.exists(source):
                self.core.run_sudo_command(f"ln -sf {source} {target}", check=False)
                print(f"  ✓ {target} → {source}")
    
    def _install_gasnet_ex(self) -> Optional[str]:
        """
        Install GASNet-EX communication layer
        
        Returns:
            Installation path if successful, None otherwise
        """
        print("\n--- Installing GASNet-EX ---")
        
        gasnet_version = "2024.5.0"
        gasnet_url = f"https://gasnet.lbl.gov/EX/GASNet-{gasnet_version}.tar.gz"
        gasnet_dir = self.build_dir / f"GASNet-{gasnet_version}"
        gasnet_install = f"{self.install_prefix}/gasnet"
        
        # Check if already installed
        if os.path.exists(f"{gasnet_install}/bin"):
            print(f"✓ GASNet-EX already installed at {gasnet_install}")
            return gasnet_install
        
        # Download if needed
        if not gasnet_dir.exists():
            print(f"Downloading GASNet-EX {gasnet_version}...")
            download_cmd = (
                f"cd {self.build_dir} && "
                f"wget -q {gasnet_url} && "
                f"tar xzf GASNet-{gasnet_version}.tar.gz"
            )
            result = self.core.run_command(download_cmd, check=False)
            if result.returncode != 0:
                print("⚠️  Failed to download GASNet-EX")
                return None
        
        # Configure with MPI, SMP, and UDP conduits
        print("Configuring GASNet-EX (MPI, SMP, UDP conduits)...")
        gcc_bin = f"{self.install_prefix}/bin/gcc"
        gxx_bin = f"{self.install_prefix}/bin/g++"
        mpi_bin = f"{self.install_prefix}/bin/mpicc"
        
        configure_cmd = (
            f"cd {gasnet_dir} && "
            f"CC={gcc_bin} CXX={gxx_bin} ./configure "
            f"--prefix={gasnet_install} "
            f"--enable-mpi --enable-smp --enable-udp "
            f"--with-mpicc={mpi_bin} "
            f"--disable-seq --enable-par"
        )
        
        result = self.core.run_command(configure_cmd, check=False)
        if result.returncode != 0:
            print("⚠️  GASNet-EX configuration failed")
            return None
        
        # Build and install
        print("Building GASNet-EX (may take 10-15 minutes)...")
        build_cmd = f"cd {gasnet_dir} && make -j$(nproc) && make install"
        result = self.core.run_command(build_cmd, check=False)
        
        if result.returncode == 0:
            print(f"✓ GASNet-EX installed to {gasnet_install}")
            return gasnet_install
        else:
            print("⚠️  GASNet-EX build failed")
            return None
    
    def _install_upcxx(self, gasnet_install: str) -> Optional[str]:
        """
        Install UPC++ PGAS library
        
        Args:
            gasnet_install: Path to GASNet-EX installation
            
        Returns:
            Installation path if successful, None otherwise
        """
        print("\n--- Installing Berkeley UPC++ ---")
        
        upcxx_version = "2024.3.0"
        upcxx_url = f"https://bitbucket.org/berkeleylab/upcxx/downloads/upcxx-{upcxx_version}.tar.gz"
        upcxx_dir = self.build_dir / f"upcxx-{upcxx_version}"
        upcxx_install = f"{self.install_prefix}/upcxx"
        
        # Check if already installed
        if os.path.exists(f"{upcxx_install}/bin/upcxx"):
            print(f"✓ UPC++ already installed at {upcxx_install}")
            return upcxx_install
        
        # Download if needed
        if not upcxx_dir.exists():
            print(f"Downloading UPC++ {upcxx_version}...")
            download_cmd = (
                f"cd {self.build_dir} && "
                f"wget -q {upcxx_url} && "
                f"tar xzf upcxx-{upcxx_version}.tar.gz"
            )
            result = self.core.run_command(download_cmd, check=False)
            if result.returncode != 0:
                print("⚠️  Failed to download UPC++")
                return None
        
        # Install UPC++ with GASNet-EX
        print("Installing UPC++ with GASNet-EX...")
        gcc_bin = f"{self.install_prefix}/bin/gcc"
        gxx_bin = f"{self.install_prefix}/bin/g++"
        
        install_cmd = (
            f"cd {upcxx_dir} && "
            f"CC={gcc_bin} CXX={gxx_bin} "
            f"./install {upcxx_install} "
            f"--with-gasnet={gasnet_install}"
        )
        
        result = self.core.run_command(install_cmd, check=False)
        
        if result.returncode == 0:
            print(f"✓ UPC++ installed to {upcxx_install}")
            return upcxx_install
        else:
            print("⚠️  UPC++ installation failed")
            return None
    
    def _install_openshmem(self) -> Optional[str]:
        """
        Install OpenSHMEM (Sandia implementation)
        
        Returns:
            Installation path if successful, None otherwise
        """
        print("\n--- Installing Sandia OpenSHMEM ---")
        
        oshmem_version = "1.5.2"
        oshmem_url = f"https://github.com/Sandia-OpenSHMEM/SOS/releases/download/v{oshmem_version}/SOS-{oshmem_version}.tar.gz"
        oshmem_dir = self.build_dir / f"SOS-{oshmem_version}"
        oshmem_install = f"{self.install_prefix}/openshmem"
        
        # Check if already installed
        if os.path.exists(f"{oshmem_install}/bin"):
            print(f"✓ OpenSHMEM already installed at {oshmem_install}")
            return oshmem_install
        
        # Download if needed
        if not oshmem_dir.exists():
            print(f"Downloading Sandia OpenSHMEM {oshmem_version}...")
            download_cmd = (
                f"cd {self.build_dir} && "
                f"wget -q {oshmem_url} && "
                f"tar xzf SOS-{oshmem_version}.tar.gz"
            )
            result = self.core.run_command(download_cmd, check=False)
            if result.returncode != 0:
                print("⚠️  Failed to download OpenSHMEM (non-critical)")
                return None
        
        # Configure OpenSHMEM
        print("Configuring OpenSHMEM...")
        gcc_bin = f"{self.install_prefix}/bin/gcc"
        gxx_bin = f"{self.install_prefix}/bin/g++"
        
        configure_cmd = (
            f"cd {oshmem_dir} && "
            f"CC={gcc_bin} CXX={gxx_bin} ./configure "
            f"--prefix={oshmem_install} "
            f"--with-pmix=internal "
            f"--enable-pmi-simple"
        )
        
        result = self.core.run_command(configure_cmd, check=False)
        if result.returncode != 0:
            print("⚠️  OpenSHMEM configuration failed (non-critical)")
            return None
        
        # Build and install
        print("Building OpenSHMEM...")
        build_cmd = f"cd {oshmem_dir} && make -j$(nproc) && make install"
        result = self.core.run_command(build_cmd, check=False)
        
        if result.returncode == 0:
            print(f"✓ OpenSHMEM installed to {oshmem_install}")
            return oshmem_install
        else:
            print("⚠️  OpenSHMEM build failed (non-critical)")
            return None
    
    def _create_upcxx_symlinks(self, upcxx_install: str):
        """Create symlinks for UPC++ binaries"""
        print("Creating UPC++ symlinks...")
        
        upcxx_bin = f"{upcxx_install}/bin"
        if os.path.exists(upcxx_bin):
            symlinks = {
                f"{upcxx_bin}/upcxx": f"{self.install_prefix}/bin/upcxx",
                f"{upcxx_bin}/upcxx-run": f"{self.install_prefix}/bin/upcxx-run",
            }
            
            for source, target in symlinks.items():
                if os.path.exists(source):
                    self.core.run_command(f"ln -sf {source} {target}", check=False)
                    print(f"  ✓ {target} → {source}")
    
    def _update_shell_environment(self, gasnet_install: Optional[str], 
                                  upcxx_install: Optional[str],
                                  oshmem_install: Optional[str]):
        """Update ~/.bashrc with PGAS environment variables"""
        if not upcxx_install:
            return
        
        print("\nUpdating shell environment...")
        bashrc = Path.home() / ".bashrc"
        
        env_lines = [
            "\n# PGAS Environment (UPC++, GASNet-EX, OpenSHMEM)",
        ]
        
        if upcxx_install:
            env_lines.extend([
                f"export UPCXX_INSTALL={upcxx_install}",
                f"export PATH={upcxx_install}/bin:$PATH",
                f"export LD_LIBRARY_PATH={upcxx_install}/lib:$LD_LIBRARY_PATH",
            ])
        
        if gasnet_install:
            env_lines.extend([
                f"export GASNET_INSTALL={gasnet_install}",
                f"export LD_LIBRARY_PATH={gasnet_install}/lib:$LD_LIBRARY_PATH",
            ])
        
        if oshmem_install:
            env_lines.extend([
                f"export OPENSHMEM_INSTALL={oshmem_install}",
                f"export PATH={oshmem_install}/bin:$PATH",
                f"export LD_LIBRARY_PATH={oshmem_install}/lib:$LD_LIBRARY_PATH",
            ])
        
        # Check if already added
        with open(bashrc, 'r') as f:
            existing_content = f.read()
        
        if "# PGAS Environment" not in existing_content:
            with open(bashrc, 'a') as f:
                for line in env_lines:
                    f.write(line + '\n')
            print("✓ Environment variables added to ~/.bashrc")
        else:
            print("✓ Environment variables already in ~/.bashrc")
    
    def _verify_pgas_installation(self, upcxx_install: Optional[str]):
        """Verify PGAS installation"""
        if not upcxx_install:
            return
        
        print("\nVerifying UPC++ installation...")
        upcxx_cmd = f"{upcxx_install}/bin/upcxx"
        
        if os.path.exists(upcxx_cmd):
            result = self.core.run_command(f"{upcxx_cmd} --version", check=False)
            if result.returncode == 0:
                print("✓ UPC++ compiler verified")
                version_output = result.stdout.strip().split('\n')[0] if result.stdout else ""
                if version_output:
                    print(f"  {version_output}")
    
    def distribute_pgas_to_cluster(self):
        """
        Distribute PGAS libraries to all cluster nodes
        
        Uses rsync to copy GASNet-EX, UPC++, and OpenSHMEM to worker nodes
        """
        if not self.core.password:
            print("\n⚠️  Skipping PGAS distribution - password not provided")
            print("   Run with --password flag for cluster-wide installation")
            return
        
        print("\n=== Distributing PGAS Libraries to Cluster ===")
        
        # Get all nodes excluding current node
        all_nodes = [self.core.master_ip] + self.core.worker_ips
        
        try:
            result = subprocess.run(['ip', 'addr'], capture_output=True, text=True, check=False)
            import re
            local_ips = re.findall(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
        except:
            local_ips = []
        
        other_nodes = [ip for ip in all_nodes if ip not in local_ips]
        
        if not other_nodes:
            print("No other nodes to distribute to")
            return
        
        print(f"Distributing to {len(other_nodes)} nodes...")
        
        # PGAS components to distribute
        pgas_components = [
            ("GASNet-EX", f"{self.install_prefix}/gasnet"),
            ("UPC++", f"{self.install_prefix}/upcxx"),
            ("OpenSHMEM", f"{self.install_prefix}/openshmem"),
        ]
        
        for node_ip in other_nodes:
            print(f"\n→ Distributing to {node_ip}...")
            
            # Copy each component
            for component_name, component_path in pgas_components:
                if os.path.exists(component_path):
                    print(f"  Copying {component_name}...")
                    rsync_cmd = (
                        f"sshpass -p '{self.core.password}' rsync -avz --delete "
                        f"-e 'ssh -o StrictHostKeyChecking=no' "
                        f"{component_path}/ "
                        f"{self.core.username}@{node_ip}:{component_path}/"
                    )
                    result = self.core.run_command(rsync_cmd, check=False)
                    if result.returncode == 0:
                        print(f"    ✓ {component_name} copied")
                    else:
                        print(f"    ⚠️  Failed to copy {component_name}")
        
        print("\n✓ PGAS distribution completed")
    
    def print_usage_summary(self):
        """Print PGAS installation summary and usage information"""
        print("\n" + "="*70)
        print("PGAS LIBRARIES INSTALLATION SUMMARY")
        print("="*70)
        print(f"✓ GASNet-EX 2024.5.0: {self.install_prefix}/gasnet")
        print(f"✓ UPC++ 2024.3.0: {self.install_prefix}/upcxx")
        print(f"✓ OpenSHMEM 1.5.2: {self.install_prefix}/openshmem")
        print("\nUsage:")
        print("  Compile: upcxx -O3 myprogram.cpp -o myprogram")
        print("  Run SMP: upcxx-run -n 4 ./myprogram")
        print("  Run MPI: upcxx-run -ssh-servers node1,node2 -n 8 ./myprogram")
        print("\nConduits:")
        print("  - smp: Single node shared memory (default)")
        print("  - mpi: Multi-node via OpenMPI")
        print("  - udp: Multi-node via UDP sockets")
        print("\nDocumentation:")
        print("  UPC++: https://upcxx.lbl.gov/docs/html/guide.html")
        print("  GASNet-EX: https://gasnet.lbl.gov/")
        print("  OpenSHMEM: https://github.com/Sandia-OpenSHMEM/SOS")
        print("="*70)
