"""
PGAS Benchmark Suite Runner

This module provides functionality to create, compile, and run PGAS benchmarks
independently of the main cluster setup.

Usage:
    python -m cluster_tools.benchmarks.run_benchmarks --help
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Dict


class BenchmarkRunner:
    """
    Manages PGAS benchmark suite execution.
    
    This class provides methods to:
    - Create benchmark suite directory structure
    - Generate benchmark source files
    - Compile benchmarks
    - Execute benchmarks and collect results
    - Generate performance reports
    """
    
    def __init__(self, benchmark_dir: Optional[Path] = None, 
                 cluster_ips: Optional[List[str]] = None):
        """
        Initialize benchmark runner.
        
        Args:
            benchmark_dir: Directory for benchmarks (default: ~/pgas_benchmarks)
            cluster_ips: List of cluster node IPs for multi-node benchmarks
        """
        self.benchmark_dir = benchmark_dir or Path.home() / "pgas_benchmarks"
        self.cluster_ips = cluster_ips or []
        self.src_dir = self.benchmark_dir / "src"
        self.bin_dir = self.benchmark_dir / "bin"
        self.results_dir = self.benchmark_dir / "results"
    
    def create_suite(self) -> bool:
        """
        Create complete benchmark suite with all files.
        
        Returns:
            bool: True if suite created successfully
        """
        print("\n=== Creating PGAS Benchmark Suite ===")
        
        # Import the benchmark manager from cluster_modules
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from cluster_modules.benchmark_manager import BenchmarkManager
        
        # Create temporary manager instance (no password needed for local creation)
        manager = BenchmarkManager(
            username="",
            password="",
            master_ip=self.cluster_ips[0] if self.cluster_ips else "127.0.0.1",
            worker_ips=self.cluster_ips[1:] if len(self.cluster_ips) > 1 else []
        )
        
        # Override benchmark directory
        manager.benchmark_dir = self.benchmark_dir
        
        # Create all benchmarks
        success = manager.create_all_benchmarks()
        
        if success:
            print(f"\n✓ Benchmark suite created at: {self.benchmark_dir}")
        
        return success
    
    def compile_all(self) -> bool:
        """
        Compile all benchmarks.
        
        Returns:
            bool: True if compilation successful
        """
        print("\n=== Compiling Benchmarks ===")
        
        if not self.benchmark_dir.exists():
            print(f"✗ Benchmark directory not found: {self.benchmark_dir}")
            print("  Run with --create first to create the benchmark suite")
            return False
        
        makefile = self.benchmark_dir / "Makefile"
        if not makefile.exists():
            print(f"✗ Makefile not found: {makefile}")
            return False
        
        make_cmd = ["make", "-C", str(self.benchmark_dir)]
        
        try:
            result = subprocess.run(make_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✓ All benchmarks compiled successfully")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"✗ Compilation failed:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Compilation timed out")
            return False
        except Exception as e:
            print(f"✗ Error compiling benchmarks: {e}")
            return False
    
    def run_benchmark(self, name: str, num_procs: int = 2) -> Optional[Dict]:
        """
        Run a specific benchmark.
        
        Args:
            name: Benchmark name (e.g., 'upcxx_latency', 'mpi_latency')
            num_procs: Number of processes/ranks to use
            
        Returns:
            Optional[Dict]: Benchmark results or None if failed
        """
        print(f"\n=== Running {name} with {num_procs} processes ===")
        
        binary = self.bin_dir / name
        
        if not binary.exists():
            print(f"✗ Benchmark binary not found: {binary}")
            print("  Run with --compile first")
            return None
        
        # Determine launcher based on benchmark type
        if "upcxx" in name:
            launcher = ["upcxx-run", "-n", str(num_procs)]
            
            # Set GASNET_SSH_SERVERS if cluster IPs provided
            env = {}
            if self.cluster_ips:
                env["GASNET_SSH_SERVERS"] = ",".join(self.cluster_ips)
        elif "mpi" in name:
            launcher = ["mpirun", "-n", str(num_procs)]
            
            # Use hostfile if it exists
            hostfile = Path.home() / "hostfile"
            if hostfile.exists():
                launcher.extend(["--hostfile", str(hostfile)])
            
            env = {}
        elif "osh" in name or "shmem" in name:
            launcher = ["oshrun", "-n", str(num_procs)]
            env = {}
        else:
            # Direct execution
            launcher = []
            env = {}
        
        run_cmd = launcher + [str(binary)]
        
        print(f"Command: {' '.join(run_cmd)}")
        
        try:
            result = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                timeout=60,
                env={**os.environ, **env} if env else None
            )
            
            if result.returncode == 0:
                print("✓ Benchmark completed successfully")
                print("\nOutput:")
                print(result.stdout)
                
                # Save results
                self.results_dir.mkdir(exist_ok=True)
                result_file = self.results_dir / f"{name}_n{num_procs}.txt"
                result_file.write_text(result.stdout)
                print(f"\n✓ Results saved to: {result_file}")
                
                return {
                    "name": name,
                    "num_procs": num_procs,
                    "output": result.stdout,
                    "success": True
                }
            else:
                print(f"✗ Benchmark failed:")
                print(result.stderr)
                return None
                
        except subprocess.TimeoutExpired:
            print("✗ Benchmark timed out")
            return None
        except Exception as e:
            print(f"✗ Error running benchmark: {e}")
            return None
    
    def run_all(self, num_procs: int = 2) -> Dict[str, bool]:
        """
        Run all available benchmarks.
        
        Args:
            num_procs: Number of processes/ranks to use
            
        Returns:
            Dict[str, bool]: Results for each benchmark
        """
        print("\n=== Running All Benchmarks ===")
        
        if not self.bin_dir.exists():
            print(f"✗ Binary directory not found: {self.bin_dir}")
            return {}
        
        results = {}
        benchmarks = list(self.bin_dir.glob("*"))
        
        if not benchmarks:
            print("✗ No compiled benchmarks found")
            print("  Run with --compile first")
            return {}
        
        for binary in benchmarks:
            if binary.is_file():
                result = self.run_benchmark(binary.name, num_procs)
                results[binary.name] = result is not None
        
        # Print summary
        print("\n" + "=" * 70)
        print("BENCHMARK SUITE SUMMARY")
        print("=" * 70)
        print(f"Total benchmarks: {len(results)}")
        print(f"Successful: {sum(results.values())}")
        print(f"Failed: {len(results) - sum(results.values())}")
        print("=" * 70)
        
        return results
    
    def clean(self) -> bool:
        """
        Clean compiled binaries.
        
        Returns:
            bool: True if clean successful
        """
        print("\n=== Cleaning Benchmarks ===")
        
        if not self.benchmark_dir.exists():
            print("✓ Nothing to clean")
            return True
        
        make_cmd = ["make", "-C", str(self.benchmark_dir), "clean"]
        
        try:
            result = subprocess.run(make_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✓ Benchmarks cleaned successfully")
                return True
            else:
                print(f"⚠ Clean had warnings: {result.stderr}")
                return True
                
        except Exception as e:
            print(f"✗ Error cleaning benchmarks: {e}")
            return False


def main():
    """Main entry point for benchmark runner."""
    parser = argparse.ArgumentParser(
        description="PGAS Benchmark Suite Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create benchmark suite
  python -m cluster_tools.benchmarks.run_benchmarks --create
  
  # Compile all benchmarks
  python -m cluster_tools.benchmarks.run_benchmarks --compile
  
  # Run specific benchmark
  python -m cluster_tools.benchmarks.run_benchmarks --run upcxx_latency -n 4
  
  # Run all benchmarks
  python -m cluster_tools.benchmarks.run_benchmarks --run-all -n 4
  
  # Full workflow: create, compile, and run
  python -m cluster_tools.benchmarks.run_benchmarks --create --compile --run-all
  
  # With cluster IPs for multi-node execution
  python -m cluster_tools.benchmarks.run_benchmarks --run-all --cluster-ips 192.168.1.147,192.168.1.139
        """
    )
    
    parser.add_argument(
        "--benchmark-dir",
        type=Path,
        help="Benchmark directory (default: ~/pgas_benchmarks)"
    )
    
    parser.add_argument(
        "--cluster-ips",
        type=str,
        help="Comma-separated list of cluster node IPs for multi-node execution"
    )
    
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create benchmark suite"
    )
    
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile all benchmarks"
    )
    
    parser.add_argument(
        "--run",
        type=str,
        metavar="BENCHMARK",
        help="Run specific benchmark (e.g., upcxx_latency, mpi_latency)"
    )
    
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run all compiled benchmarks"
    )
    
    parser.add_argument(
        "-n", "--num-procs",
        type=int,
        default=2,
        help="Number of processes/ranks (default: 2)"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean compiled binaries"
    )
    
    args = parser.parse_args()
    
    # Parse cluster IPs
    cluster_ips = []
    if args.cluster_ips:
        cluster_ips = [ip.strip() for ip in args.cluster_ips.split(",")]
    
    # Create runner
    runner = BenchmarkRunner(
        benchmark_dir=args.benchmark_dir,
        cluster_ips=cluster_ips
    )
    
    # Execute requested operations
    success = True
    
    if args.create:
        success = runner.create_suite() and success
    
    if args.compile:
        success = runner.compile_all() and success
    
    if args.run:
        result = runner.run_benchmark(args.run, args.num_procs)
        success = (result is not None) and success
    
    if args.run_all:
        results = runner.run_all(args.num_procs)
        success = all(results.values()) and success
    
    if args.clean:
        success = runner.clean() and success
    
    # If no action specified, show help
    if not any([args.create, args.compile, args.run, args.run_all, args.clean]):
        parser.print_help()
        return 0
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
