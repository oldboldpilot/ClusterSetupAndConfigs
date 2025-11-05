"""
Cluster Setup and Configuration Modules

Modular components for HPC cluster setup, configuration, and management.
"""

__version__ = "3.0.0"
__author__ = "Olumuyiwa Oluwasanmi"

# Core modules
from .homebrew_manager import HomebrewManager
from .ssh_manager import SSHManager
from .sudo_manager import SudoManager
from .mpi_manager import MPIManager
from .openmp_manager import OpenMPManager
from .openshmem_manager import OpenSHMEMManager
from .berkeley_upc_manager import BerkeleyUPCManager
from .pgas_manager import PGASManager
from .benchmark_manager import BenchmarkManager
from .cluster_cleanup import ClusterCleanup
from .slurm_manager import SlurmManager
from .network_manager import NetworkManager
from .pdsh_manager import PDSHManager

__all__ = [
    'HomebrewManager',
    'SSHManager',
    'SudoManager',
    'MPIManager',
    'OpenMPManager',
    'OpenSHMEMManager',
    'BerkeleyUPCManager',
    'PGASManager',
    'BenchmarkManager',
    'SlurmManager',
    'NetworkManager',
    'PDSHManager',
]
