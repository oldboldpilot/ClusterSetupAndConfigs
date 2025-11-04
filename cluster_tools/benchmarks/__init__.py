"""
PGAS Benchmarks Module

Standalone benchmark suite for PGAS libraries (UPC++, OpenSHMEM, MPI).

Usage:
    python -m cluster_tools.benchmarks.run_benchmarks --help
"""

__version__ = "1.0.0"

from .run_benchmarks import BenchmarkRunner

__all__ = ['BenchmarkRunner']
