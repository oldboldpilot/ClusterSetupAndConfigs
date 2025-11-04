"""
PGAS (Partitioned Global Address Space) Configuration Module

This module contains all PGAS-related configuration, installation, 
testing, and benchmarking tools for the HPC cluster.
"""

__version__ = "1.0.0"

# PGAS libraries supported
SUPPORTED_LIBRARIES = [
    "UPC++ 2025.10.0",
    "GASNet-EX 2025.8.0", 
    "OpenSHMEM 1.5.2",
]

# Conduits available
GASNET_CONDUITS = ["smp", "udp", "mpi"]
