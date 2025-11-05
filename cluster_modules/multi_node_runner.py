"""
Multi-Node Benchmark Runner

Coordinates benchmark execution across all cluster nodes and threads simultaneously.
Supports OpenMP, MPI, hybrid MPI+OpenMP, UPC++, and OpenSHMEM benchmarks.
Ensures proper C++23 compliance and comprehensive testing.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class NodeInfo:
    """Information about a cluster node"""
    hostname: str
    ip: str
    cpus: int
    memory_mb: int


class MultiNodeBenchmarkRunner:
    """Runs benchmarks across all cluster nodes simultaneously"""
    
    def __init__(self):
        # Cluster configuration - 152 cores total
        self.nodes = [
            NodeInfo("oluwasanmiredhatserver", "192.168.1.136", 88, 257792),
            NodeInfo("DESKTOP-3SON9JT", "192.168.1.147", 32, 65536),
            NodeInfo("muyiwadroexperiments", "192.168.1.139", 16, 32768),
            NodeInfo("oluubuntul1", "192.168.1.96", 16, 32768),
        ]
        self.total_cpus = sum(node.cpus for node in self.nodes)
        self.benchmark_dir = Path.home() / "cluster_build_sources" / "benchmarks"
        self.results_dir = self.benchmark_dir / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def cleanup_processes(self):
        """Kill any hanging benchmark processes on all nodes"""
        print("Cleaning up any running benchmark processes...")
        node_list = self.get_node_list()
        cmd = f"pdsh -w {node_list} \"pkill -9 -f 'mpi_latency|openshmem_latency|hybrid_mpi|openmp_parallel|upcxx_latency|mpirun|oshrun|upcxx-run' 2>/dev/null; echo 'Cleaned: \\$(hostname)'\""
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            print(result.stdout)
        except Exception as e:
            print(f"Warning: Cleanup had issues: {e}")
        
        time.sleep(1)  # Give processes time to die
        
    def get_node_list(self) -> str:
        """Get comma-separated list of node IPs"""
        return ",".join(node.ip for node in self.nodes)
    
    def get_hostfile_content(self) -> str:
        """Generate hostfile content for MPI"""
        lines = []
        for node in self.nodes:
            lines.append(f"{node.ip} slots={node.cpus}")
        return "\n".join(lines)
    
    def create_hostfile(self) -> Path:
        """Create MPI hostfile"""
        hostfile = self.benchmark_dir / "hostfile"
        hostfile.write_text(self.get_hostfile_content())
        print(f"✓ Created hostfile: {hostfile}")
        return hostfile
    
    def run_openmp_all_nodes(self) -> Dict[str, any]:
        """Run OpenMP benchmark on all nodes simultaneously using pdsh"""
        print("\n" + "="*60)
        print("OPENMP BENCHMARK - ALL NODES SIMULTANEOUSLY")
        print("="*60)
        print(f"Total CPUs: {self.total_cpus}")
        print(f"Nodes: {len(self.nodes)}")
        
        benchmark = self.benchmark_dir / "bin" / "openmp_parallel"
        if not benchmark.exists():
            print(f"✗ Benchmark not found: {benchmark}")
            return {"success": False, "error": "Benchmark not compiled"}
        
        node_list = self.get_node_list()
        cmd = f"pdsh -w {node_list} 'cd {self.benchmark_dir} && bin/openmp_parallel'"
        
        print(f"\nCommand: {cmd}")
        print("-" * 60)
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_mpi_all_nodes(self, num_processes: int = 4) -> Dict[str, any]:
        """Run MPI benchmark across all nodes"""
        print("\n" + "="*60)
        print("MPI BENCHMARK - MULTI-NODE EXECUTION")
        print("="*60)
        print(f"Total processes: {num_processes}")
        print(f"Nodes: {len(self.nodes)}")
        
        benchmark = self.benchmark_dir / "bin" / "mpi_latency"
        if not benchmark.exists():
            print(f"✗ Benchmark not found: {benchmark}")
            return {"success": False, "error": "Benchmark not compiled"}
        
        hostfile = self.create_hostfile()
        
        # Use PMI2 for better compatibility - removed specific interface constraint
        cmd = [
            "mpirun",
            "-np", str(num_processes),
            "--hostfile", str(hostfile),
            "--mca", "btl", "tcp,self",
            "--mca", "pml", "ob1",
            "--map-by", "node",
            str(benchmark)
        ]
        
        print(f"\nCommand: {' '.join(cmd)}")
        print("-" * 60)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_hybrid_all_nodes(self, mpi_processes: int = 4, threads_per_process: int = None) -> Dict[str, any]:
        """Run hybrid MPI+OpenMP benchmark across all nodes"""
        print("\n" + "="*60)
        print("HYBRID MPI+OPENMP BENCHMARK - MULTI-NODE EXECUTION")
        print("="*60)
        
        if threads_per_process is None:
            # Calculate threads per process to use all CPUs
            threads_per_process = self.total_cpus // mpi_processes
        
        total_parallelism = mpi_processes * threads_per_process
        
        print(f"MPI processes: {mpi_processes}")
        print(f"OpenMP threads per process: {threads_per_process}")
        print(f"Total parallelism: {total_parallelism}")
        print(f"Nodes: {len(self.nodes)}")
        
        benchmark = self.benchmark_dir / "bin" / "hybrid_mpi_openmp"
        if not benchmark.exists():
            print(f"✗ Benchmark not found: {benchmark}")
            return {"success": False, "error": "Benchmark not compiled"}
        
        hostfile = self.create_hostfile()
        
        cmd = [
            "mpirun",
            "-np", str(mpi_processes),
            "--hostfile", str(hostfile),
            "--mca", "btl", "tcp,self",
            "--mca", "pml", "ob1",
            "--map-by", "node",
            "-x", f"OMP_NUM_THREADS={threads_per_process}",
            "-x", "OMP_PROC_BIND=close",
            "-x", "OMP_PLACES=cores",
            str(benchmark)
        ]
        
        print(f"\nCommand: {' '.join(cmd)}")
        print("-" * 60)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_openshmem_all_nodes(self, num_pes: int = 4) -> Dict[str, any]:
        """Run OpenSHMEM benchmark across all nodes"""
        print("\n" + "="*60)
        print("OPENSHMEM BENCHMARK - MULTI-NODE EXECUTION")
        print("="*60)
        print(f"Total PEs: {num_pes}")
        print(f"Nodes: {len(self.nodes)}")
        
        benchmark = self.benchmark_dir / "bin" / "openshmem_latency"
        if not benchmark.exists():
            print(f"✗ Benchmark not found: {benchmark}")
            return {"success": False, "error": "Benchmark not compiled"}
        
        hostfile = self.create_hostfile()
        
        # OpenSHMEM uses oshrun which wraps mpirun
        # Use same MCA params as MPI for consistency
        cmd = [
            "oshrun",
            "-np", str(num_pes),
            "--hostfile", str(hostfile),
            "--mca", "btl", "tcp,self",
            "--mca", "pml", "ob1",
            "--map-by", "node",
            str(benchmark),
            "100"  # iterations
        ]
        
        print(f"\nCommand: {' '.join(cmd)}")
        print("-" * 60)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_upcxx_all_nodes(self, num_processes: int = 4) -> Dict[str, any]:
        """Run UPC++ benchmark across all nodes"""
        print("\n" + "="*60)
        print("UPC++ BENCHMARK - MULTI-NODE EXECUTION")
        print("="*60)
        print(f"Total processes: {num_processes}")
        print(f"Nodes: {len(self.nodes)}")
        
        benchmark = self.benchmark_dir / "bin" / "upcxx_latency"
        if not benchmark.exists():
            print(f"✗ Benchmark not found: {benchmark}")
            return {"success": False, "error": "Benchmark not compiled"}
        
        # UPC++ uses GASNet with SSH spawning
        import os
        env = os.environ.copy()
        env['GASNET_SSH_SERVERS'] = self.get_node_list()
        env['GASNET_SPAWNFN'] = 'ssh'
        
        cmd = [
            "upcxx-run",
            "-n", str(num_processes),
            str(benchmark)
        ]
        
        print(f"\nCommand: {' '.join(cmd)}")
        print(f"GASNET_SSH_SERVERS={env['GASNET_SSH_SERVERS']}")
        print("-" * 60)
        
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    
    def run_all_benchmarks(self):
        """Run comprehensive benchmark suite across all nodes"""
        print("\n" + "="*70)
        print("COMPREHENSIVE MULTI-NODE BENCHMARK SUITE")
        print("="*70)
        print(f"Cluster: 4 nodes, {self.total_cpus} cores total")
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Clean up any hanging processes first
        self.cleanup_processes()
        
        results = {}
        
        # 1. OpenMP on all nodes simultaneously
        results['openmp'] = self.run_openmp_all_nodes()
        time.sleep(2)
        self.cleanup_processes()
        
        # 2. MPI across 4 nodes
        results['mpi'] = self.run_mpi_all_nodes(num_processes=4)
        time.sleep(2)
        self.cleanup_processes()
        
        # 3. Hybrid MPI+OpenMP (4 processes × max threads each)
        results['hybrid'] = self.run_hybrid_all_nodes(mpi_processes=4)
        time.sleep(2)
        self.cleanup_processes()
        
        # 4. OpenSHMEM across 4 PEs
        results['openshmem'] = self.run_openshmem_all_nodes(num_pes=4)
        time.sleep(2)
        self.cleanup_processes()
        
        # 5. UPC++ across 4 processes
        results['upcxx'] = self.run_upcxx_all_nodes(num_processes=4)
        self.cleanup_processes()
        
        # Save results
        results_file = self.results_dir / f"multi_node_results_{int(time.time())}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print("\n" + "="*70)
        print("BENCHMARK SUMMARY")
        print("="*70)
        for name, result in results.items():
            status = "✓ PASS" if result.get('success') else "✗ FAIL"
            print(f"{name.upper():20s} {status}")
        print(f"\nResults saved to: {results_file}")
        print("="*70 + "\n")
        
        return results


if __name__ == '__main__':
    runner = MultiNodeBenchmarkRunner()
    runner.run_all_benchmarks()
