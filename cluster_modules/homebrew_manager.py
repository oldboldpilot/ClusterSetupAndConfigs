"""
Homebrew and GCC Compiler Manager

Handles Homebrew installation, GCC compiler setup, and symlink management
for the cluster environment.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Callable


class HomebrewManager:
    """Manages Homebrew installation and GCC compiler configuration"""
    
    def __init__(self, username: str, password: Optional[str] = None,
                 master_ip: Optional[str] = None, worker_ips: Optional[list] = None):
        """
        Initialize Homebrew Manager
        
        Args:
            username: Username for cluster nodes
            password: Password for remote operations (optional)
            master_ip: Master node IP address (optional)
            worker_ips: List of worker node IP addresses (optional)
        """
        self.username = username
        self.password = password
        self.master_ip = master_ip
        self.worker_ips = worker_ips or []
        self.homebrew_bin = "/home/linuxbrew/.linuxbrew/bin"
        self.homebrew_opt = "/home/linuxbrew/.linuxbrew/opt"
    
    def _run_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Execute a shell command"""
        return subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
    
    def _run_sudo_command(self, command: str, check: bool = True) -> subprocess.CompletedProcess:
        """Execute a command with sudo"""
        sudo_cmd = f"sudo {command}"
        return self._run_command(sudo_cmd, check=check)
    
    def is_homebrew_installed(self) -> bool:
        """Check if Homebrew is installed"""
        result = self._run_command("which brew", check=False)
        return result.returncode == 0
    
    def install_homebrew(self) -> bool:
        """Install Homebrew if not already installed"""
        print("\n=== Installing Homebrew ===")
        
        if self.is_homebrew_installed():
            print("✓ Homebrew already installed")
            return True
        
        print("Installing Homebrew (this may take a while)...")
        
        # Set non-interactive mode
        env = os.environ.copy()
        env['NONINTERACTIVE'] = '1'
        
        install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        result = subprocess.run(
            install_cmd,
            shell=True,
            env=env,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"✗ Homebrew installation failed: {result.stderr}")
            return False
        
        # Add Homebrew to PATH
        homebrew_path = self.homebrew_bin
        shell_profile = Path.home() / ".bashrc"
        
        with open(shell_profile, 'a') as f:
            f.write('\n# Homebrew\n')
            f.write(f'eval "$({homebrew_path}/brew shellenv)"\n')
            f.write('\n# Always use latest Homebrew GCC for compilation\n')
            f.write(f'export CC={homebrew_path}/gcc\n')
            f.write(f'export CXX={homebrew_path}/g++\n')
            f.write(f'export FC={homebrew_path}/gfortran\n')
            f.write(f'export OMPI_CC={homebrew_path}/gcc\n')
            f.write(f'export OMPI_CXX={homebrew_path}/g++\n')
            f.write(f'export OMPI_FC={homebrew_path}/gfortran\n')
        
        print("✓ Homebrew installed successfully")
        return True
    
    def install_gcc(self) -> bool:
        """Install GCC compiler via Homebrew"""
        print("\n=== Installing GCC Compiler ===")
        
        # Check if gcc is already installed
        result = self._run_command(f"{self.homebrew_bin}/brew list gcc", check=False)
        if result.returncode == 0:
            version_result = self._run_command(f"{self.homebrew_bin}/brew list --versions gcc", check=False)
            if version_result.returncode == 0:
                print(f"✓ GCC already installed: {version_result.stdout.strip()}")
                return True
        
        print("Installing GCC via Homebrew...")
        result = self._run_command(f"{self.homebrew_bin}/brew install gcc", check=False)
        
        if result.returncode != 0:
            print(f"✗ GCC installation failed: {result.stderr}")
            return False
        
        print("✓ GCC installed successfully")
        return True
    
    def install_binutils(self) -> bool:
        """Install binutils via Homebrew"""
        print("\n=== Installing Binutils ===")
        
        # Check if binutils is already installed
        result = self._run_command(f"{self.homebrew_bin}/brew list binutils", check=False)
        if result.returncode == 0:
            version_result = self._run_command(f"{self.homebrew_bin}/brew list --versions binutils", check=False)
            if version_result.returncode == 0:
                print(f"✓ Binutils already installed: {version_result.stdout.strip()}")
                return True
        
        print("Installing binutils via Homebrew...")
        result = self._run_command(f"{self.homebrew_bin}/brew install binutils", check=False)
        
        if result.returncode != 0:
            print(f"✗ Binutils installation failed: {result.stderr}")
            return False
        
        print("✓ Binutils installed successfully")
        return True
    
    def create_gcc_symlinks(self) -> bool:
        """Create symlinks for GCC to point to latest version"""
        print("\n=== Creating GCC Symlinks ===")
        
        # Find the installed gcc version
        result = self._run_command(
            f"ls {self.homebrew_bin}/gcc-* 2>/dev/null | grep -E 'gcc-[0-9]+$' | head -1",
            check=False
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            print("⚠️  Could not detect GCC version for symlink creation")
            return False
        
        gcc_path = result.stdout.strip()
        gcc_version = gcc_path.split('-')[-1]
        print(f"Found GCC version: {gcc_version}")
        
        # Create symlinks
        symlinks = [
            (f"gcc-{gcc_version}", "gcc"),
            (f"g++-{gcc_version}", "g++"),
            (f"gfortran-{gcc_version}", "gfortran"),
        ]
        
        for source, target in symlinks:
            cmd = f"ln -sf {self.homebrew_bin}/{source} {self.homebrew_bin}/{target}"
            result = self._run_command(cmd, check=False)
            if result.returncode != 0:
                print(f"⚠️  Failed to create symlink {target} -> {source}")
        
        # Create compatibility symlinks for older GCC versions that PGAS libraries might expect
        # This ensures tools like UPC++ that look for g++-11 will use our latest gcc-15
        # Point directly to the versioned binary to avoid circular references
        compat_versions = ['11', '12', '13', '14']  # Common legacy versions
        for old_version in compat_versions:
            for compiler in ['gcc', 'g++', 'gfortran']:
                # Remove any existing symlink first
                remove_cmd = f"sudo rm -f {self.homebrew_bin}/{compiler}-{old_version}"
                self._run_command(remove_cmd, check=False)
                # Create new symlink pointing to the actual versioned binary
                cmd = f"sudo ln -sf {self.homebrew_bin}/{compiler}-{gcc_version} {self.homebrew_bin}/{compiler}-{old_version}"
                result = self._run_command(cmd, check=False)
                # Silently continue if symlink creation fails (non-critical)
        
        print(f"✓ Created compiler symlinks:")
        print(f"  gcc/g++/gfortran -> gcc-{gcc_version} (latest from Homebrew)")
        print(f"  gcc-11/g++-11/etc -> gcc-{gcc_version} (compatibility for PGAS libraries)")
        return True
    
    def verify_gcc_installation(self) -> bool:
        """Verify GCC installation and symlinks"""
        print("\n=== Verifying GCC Installation ===")
        
        # Check GCC version
        result = self._run_command(f"{self.homebrew_bin}/gcc --version", check=False)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ GCC: {version_line}")
        else:
            print("✗ GCC not found or not working")
            return False
        
        # Check symlink
        result = self._run_command(f"ls -la {self.homebrew_bin}/gcc", check=False)
        if result.returncode == 0:
            symlink_info = result.stdout.strip().split()[-3:]
            print(f"✓ Symlink: {' '.join(symlink_info)}")
        
        return True
    
    def verify_binutils_installation(self) -> bool:
        """Verify binutils installation"""
        print("\n=== Verifying Binutils Installation ===")
        
        binutils_path = f"{self.homebrew_opt}/binutils/bin"
        tools = ['as', 'ld', 'ar', 'ranlib']
        
        all_ok = True
        for tool in tools:
            result = self._run_command(f"{binutils_path}/{tool} --version", check=False)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                print(f"✓ {tool}: {version_line}")
            else:
                print(f"✗ {tool} not found")
                all_ok = False
        
        return all_ok
    
    def configure_system_path(self) -> bool:
        """Configure system-wide PATH for Homebrew binaries"""
        print("\n=== Configuring System-Wide PATH ===")
        
        if not os.path.exists(self.homebrew_bin):
            print("⚠️  Homebrew path not found, skipping PATH configuration")
            return False
        
        # Create SSH environment file with proper PATH
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(mode=0o700, exist_ok=True)
        
        ssh_env = ssh_dir / "environment"
        homebrew_sbin = "/home/linuxbrew/.linuxbrew/sbin"
        binutils_bin = f"{self.homebrew_opt}/binutils/bin"
        
        with open(ssh_env, 'w') as f:
            f.write(f"PATH={binutils_bin}:{self.homebrew_bin}:{homebrew_sbin}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin\n")
            f.write(f"CC={self.homebrew_bin}/gcc\n")
            f.write(f"CXX={self.homebrew_bin}/g++\n")
            f.write(f"FC={self.homebrew_bin}/gfortran\n")
            f.write(f"OMPI_CC={self.homebrew_bin}/gcc\n")
            f.write(f"OMPI_CXX={self.homebrew_bin}/g++\n")
            f.write(f"OMPI_FC={self.homebrew_bin}/gfortran\n")
        
        ssh_env.chmod(0o600)
        print("✓ Created ~/.ssh/environment with Homebrew compiler settings")
        
        # Update sshd_config to permit environment variables
        sshd_config = Path("/etc/ssh/sshd_config")
        if sshd_config.exists():
            # Use sudo to read sshd_config
            result = self._run_command("sudo cat /etc/ssh/sshd_config", check=False)
            config_content = result.stdout if result.returncode == 0 else ""
            
            if "PermitUserEnvironment" not in config_content:
                print("Adding PermitUserEnvironment to sshd_config...")
                self._run_sudo_command(
                    "bash -c 'echo \"PermitUserEnvironment yes\" >> /etc/ssh/sshd_config'",
                    check=False
                )
                self._run_sudo_command("systemctl restart sshd", check=False)
                print("✓ Updated sshd_config")
        
        return True
    
    def install_and_configure_local(self) -> bool:
        """Complete Homebrew, GCC, and binutils setup on local node"""
        print("\n" + "="*70)
        print("HOMEBREW AND COMPILER SETUP")
        print("="*70)
        
        # Install Homebrew
        if not self.install_homebrew():
            return False
        
        # Install GCC
        if not self.install_gcc():
            return False
        
        # Install binutils
        if not self.install_binutils():
            return False
        
        # Create GCC symlinks
        if not self.create_gcc_symlinks():
            print("⚠️  Warning: Failed to create GCC symlinks, but continuing...")
        
        # Configure system PATH
        if not self.configure_system_path():
            print("⚠️  Warning: Failed to configure system PATH, but continuing...")
        
        # Verify installations
        self.verify_gcc_installation()
        self.verify_binutils_installation()
        
        print("\n✓ Homebrew and compiler setup completed successfully")
        return True
