"""
PGAS Library Configuration Module

Centralized configuration for PGAS library paths and compiler settings.
This module provides a single source of truth for all PGAS-related paths,
making it easy to update versions and locations.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

from pathlib import Path
from typing import Dict, Optional
import subprocess


class PGASConfig:
    """Centralized PGAS library configuration"""
    
    # Base installation paths
    HOMEBREW_PREFIX = Path("/home/linuxbrew/.linuxbrew")
    BUILD_DIR = Path.home() / "cluster_build_sources"
    
    # PGAS Library Versions
    GASNET_VERSION = "2025.8.0"
    UPCXX_VERSION = "2025.10.0"
    OPENSHMEM_VERSION = "1.5.3"
    BERKELEY_UPC_VERSION = "2024.8.0"
    
    # Installation Directories
    GASNET_INSTALL = HOMEBREW_PREFIX / "gasnet"
    UPCXX_INSTALL = HOMEBREW_PREFIX / "upcxx"
    OPENSHMEM_INSTALL = HOMEBREW_PREFIX / "openshmem"
    BERKELEY_UPC_INSTALL = HOMEBREW_PREFIX / "bupc"
    
    # Compiler Binaries
    UPCXX_COMPILER = HOMEBREW_PREFIX / "bin" / "upcxx"
    UPCXX_RUN = HOMEBREW_PREFIX / "bin" / "upcxx-run"
    OSHCC = HOMEBREW_PREFIX / "bin" / "oshcc"
    OSHCXX = HOMEBREW_PREFIX / "bin" / "oshc++"
    OSHRUN = HOMEBREW_PREFIX / "bin" / "oshrun"
    BUPC_COMPILER = HOMEBREW_PREFIX / "bin" / "upcc"
    BUPC_RUN = HOMEBREW_PREFIX / "bin" / "upcrun"
    
    # Build Source Directories
    GASNET_SOURCE = BUILD_DIR / f"GASNet-{GASNET_VERSION}"
    UPCXX_SOURCE = BUILD_DIR / f"upcxx-{UPCXX_VERSION}"
    OPENSHMEM_SOURCE = Path.home() / "openshmem_build" / f"SOS-{OPENSHMEM_VERSION}"
    BERKELEY_UPC_SOURCE = BUILD_DIR / f"berkeley_upc-{BERKELEY_UPC_VERSION}"
    
    @classmethod
    def get_upcxx_flags(cls) -> Dict[str, str]:
        """Get UPC++ compilation flags"""
        return {
            'UPCXX': str(cls.UPCXX_COMPILER),
            'UPCXX_RUN': str(cls.UPCXX_RUN),
            'UPCXX_FLAGS': '-O3 -std=c++23',
        }
    
    @classmethod
    def get_openshmem_flags(cls) -> Dict[str, str]:
        """Get OpenSHMEM compilation flags"""
        return {
            'OSHCC': str(cls.OSHCC),
            'OSHCXX': str(cls.OSHCXX),
            'OSHRUN': str(cls.OSHRUN),
            'OSHCC_FLAGS': '-std=c++23 -O3',
        }
    
    @classmethod
    def get_berkeley_upc_flags(cls) -> Dict[str, str]:
        """Get Berkeley UPC compilation flags"""
        return {
            'UPCC': str(cls.BUPC_COMPILER),
            'UPCRUN': str(cls.BUPC_RUN),
            'UPCC_FLAGS': '-O3',
        }
    
    @classmethod
    def check_installation(cls) -> Dict[str, bool]:
        """Check which PGAS libraries are installed"""
        return {
            'GASNet': cls.GASNET_INSTALL.exists(),
            'UPC++': cls.UPCXX_COMPILER.exists(),
            'OpenSHMEM': cls.OSHCC.exists(),
            'Berkeley UPC': cls.BUPC_COMPILER.exists(),
        }
    
    @classmethod
    def get_library_info(cls, library: str) -> Optional[Dict[str, str]]:
        """Get detailed information about a PGAS library"""
        info_map = {
            'upcxx': {
                'name': 'UPC++',
                'version': cls.UPCXX_VERSION,
                'install_dir': str(cls.UPCXX_INSTALL),
                'compiler': str(cls.UPCXX_COMPILER),
                'runtime': str(cls.UPCXX_RUN),
            },
            'openshmem': {
                'name': 'OpenSHMEM (SOS)',
                'version': cls.OPENSHMEM_VERSION,
                'install_dir': str(cls.OPENSHMEM_INSTALL),
                'compiler': str(cls.OSHCC),
                'runtime': str(cls.OSHRUN),
            },
            'gasnet': {
                'name': 'GASNet-EX',
                'version': cls.GASNET_VERSION,
                'install_dir': str(cls.GASNET_INSTALL),
            },
            'berkeley_upc': {
                'name': 'Berkeley UPC',
                'version': cls.BERKELEY_UPC_VERSION,
                'install_dir': str(cls.BERKELEY_UPC_INSTALL),
                'compiler': str(cls.BUPC_COMPILER),
                'runtime': str(cls.BUPC_RUN),
            }
        }
        return info_map.get(library.lower())
    
    @classmethod
    def get_all_compilers(cls) -> Dict[str, Path]:
        """Get all PGAS compiler paths"""
        return {
            'upcxx': cls.UPCXX_COMPILER,
            'oshcc': cls.OSHCC,
            'oshc++': cls.OSHCXX,
            'upcc': cls.BUPC_COMPILER,
        }
    
    @classmethod
    def get_env_vars(cls) -> Dict[str, str]:
        """Get environment variables for PGAS libraries"""
        env = {}
        
        if cls.UPCXX_INSTALL.exists():
            env['UPCXX_INSTALL'] = str(cls.UPCXX_INSTALL)
            env['PATH'] = f"{cls.UPCXX_INSTALL / 'bin'}:$PATH"
        
        if cls.OPENSHMEM_INSTALL.exists():
            env['OPENSHMEM_INSTALL'] = str(cls.OPENSHMEM_INSTALL)
            env['LD_LIBRARY_PATH'] = f"{cls.OPENSHMEM_INSTALL / 'lib'}:$LD_LIBRARY_PATH"
        
        if cls.GASNET_INSTALL.exists():
            env['GASNET_INSTALL'] = str(cls.GASNET_INSTALL)
        
        return env


if __name__ == '__main__':
    print("PGAS Library Configuration")
    print("=" * 60)
    
    # Check installations
    print("\nInstallation Status:")
    for lib, installed in PGASConfig.check_installation().items():
        status = "✓ Installed" if installed else "✗ Not installed"
        print(f"  {lib:20s} {status}")
    
    # Show UPC++ info
    print("\nUPC++ Configuration:")
    upcxx_info = PGASConfig.get_library_info('upcxx')
    if upcxx_info:
        for key, value in upcxx_info.items():
            print(f"  {key:15s}: {value}")
    
    # Show OpenSHMEM info
    print("\nOpenSHMEM Configuration:")
    oshmem_info = PGASConfig.get_library_info('openshmem')
    if oshmem_info:
        for key, value in oshmem_info.items():
            print(f"  {key:15s}: {value}")
