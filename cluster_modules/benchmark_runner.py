#!/usr/bin/env python3
"""
Cluster Benchmark Runner with pdsh

Modular benchmark orchestration system for running benchmarks
across cluster nodes using pdsh for distributed execution.
"""

import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Configuration for a single benchmark"""
    name: str
    binary: str
    framework: str  # openmp, mpi, hybrid, openshmem, upcxx
    num_processes: int = 1
    args: List[str] = field(default_factory=list)
    timeout: int = 60
    run_mode: str = "mpi"  # mpi, pdsh, local
    

@dataclass
class BenchmarkResult:
    """Result from a benchmark execution"""
    name: str
    success: bool
    duration: float
    output: str
    error: str = ""
    exit_code: int = 0
    timestamp: str = ""


class ClusterBenchmarkRunner:
    """
    Runs benchmarks across cluster using pdsh and MPI
    
    Features:
    - Parallel execution using pdsh
    - MPI-based benchmarks
    - Result collection and reporting
    - Error handling and cleanup
    """
    
    def __init__(
        self,
        benchmark_dir: Path = None,
        hostfile: Path = None,
        config_file: Path = None
    ):
        """Initialize benchmark runner"""
        self.benchmark_dir = benchmark_dir or Path.home() / "cluster_build_sources" / "benchmarks"
        self.hostfile = hostfile or self.benchmark_dir / "hostfile"
        self.config_file = config_file or Path("cluster_config_actual.yaml")
        
        self.results_dir = Path.home() / "cluster_benchmark_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Load cluster configuration
        self.cluster_nodes = self._load_cluster_nodes()
        self.node_list = ','.join(self.cluster_nodes)
        
        logger.info(f"Initialized ClusterBenchmarkRunner")
        logger.info(f"  Benchmark dir: {self.benchmark_dir}")
        logger.info(f"  Hostfile: {self.hostfile}")
        logger.info(f"  Nodes: {len(self.cluster_nodes)}")
    
    def _load_cluster_nodes(self) -> List[str]:
        """Load cluster node IPs"""
        try:
            with open(self.config_file) as f:
                config = yaml.safe_load(f)
            
            nodes = []
            master_data = config['master']
            if isinstance(master_data, list):
                master_data = master_data[0]
            nodes.append(master_data['ip'])
            
            for worker in config.get('workers', []):
                nodes.append(worker['ip'])
            
            return nodes
            
        except Exception as e:
            logger.warning(f"Could not load config: {e}, using hostfile")
            return self._load_from_hostfile()
    
    def _load_from_hostfile(self) -> List[str]:
        """Load nodes from hostfile"""
        if not self.hostfile.exists():
            return []
        
        nodes = []
        with open(self.hostfile) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ip = line.split()[0]
                    if ip not in nodes:
                        nodes.append(ip)
        return nodes
    
    def sync_benchmarks(self) -> Dict[str, bool]:
        """Sync benchmark binaries to all nodes"""
        logger.info("Syncing benchmarks to all nodes...")
        
        if not (self.benchmark_dir / "bin").exists():
            logger.error(f"No binaries found in {self.benchmark_dir}/bin")
            return {}
        
        # Create directories
        cmd = f"pdsh -w {self.node_list} 'mkdir -p {self.benchmark_dir}/bin'"
        subprocess.run(cmd, shell=True, capture_output=True)
        
        # Sync to each node
        results = {}
        for node in self.cluster_nodes:
            try:
                cmd = f"rsync -az {self.benchmark_dir}/bin/ {node}:{self.benchmark_dir}/bin/"
                result = subprocess.run(cmd, shell=True, timeout=30, capture_output=True)
                results[node] = (result.returncode == 0)
                status = "✓" if results[node] else "✗"
                logger.info(f"  {status} {node}")
            except Exception as e:
                logger.error(f"  ✗ {node}: {e}")
                results[node] = False
        
        return results
    
    def run_mpi_benchmark(self, config: BenchmarkConfig) -> BenchmarkResult:
        """Run MPI benchmark"""
        binary = self.benchmark_dir / "bin" / config.binary
        
        if not binary.exists():
            return BenchmarkResult(
                name=config.name,
                success=False,
                duration=0,
                output="",
                error=f"Binary not found: {binary}"
            )
        
        args_str = ' '.join(config.args) if config.args else ''
        cmd = f"mpirun -np {config.num_processes} --hostfile {self.hostfile} --map-by ppr:1:node {binary} {args_str}"
        
        logger.info(f"Running: {config.name}")
        start = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                timeout=config.timeout,
                capture_output=True,
                text=True,
                cwd=self.benchmark_dir
            )
            
            duration = time.time() - start
            
            return BenchmarkResult(
                name=config.name,
                success=(result.returncode == 0),
                duration=duration,
                output=result.stdout,
                error=result.stderr,
                exit_code=result.returncode,
                timestamp=datetime.now().isoformat()
            )
            
        except subprocess.TimeoutExpired:
            return BenchmarkResult(
                name=config.name,
                success=False,
                duration=time.time() - start,
                output="",
                error=f"Timeout after {config.timeout}s",
                exit_code=124,
                timestamp=datetime.now().isoformat()
            )
    
    def run_pdsh_benchmark(self, config: BenchmarkConfig) -> Dict[str, BenchmarkResult]:
        """Run benchmark on all nodes via pdsh"""
        binary = self.benchmark_dir / "bin" / config.binary
        args_str = ' '.join(config.args) if config.args else ''
        cmd = f"pdsh -w {self.node_list} '{binary} {args_str}'"
        
        logger.info(f"Running pdsh: {config.name}")
        start = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                timeout=config.timeout,
                capture_output=True,
                text=True
            )
            
            duration = time.time() - start
            results = {}
            
            for line in result.stdout.split('\n'):
                if ':' in line:
                    node, output = line.split(':', 1)
                    node = node.strip()
                    if node in self.cluster_nodes:
                        results[node] = BenchmarkResult(
                            name=config.name,
                            success=True,
                            duration=duration,
                            output=output.strip(),
                            timestamp=datetime.now().isoformat()
                        )
            
            return results
            
        except subprocess.TimeoutExpired:
            return {
                node: BenchmarkResult(
                    name=config.name,
                    success=False,
                    duration=time.time() - start,
                    output="",
                    error=f"Timeout after {config.timeout}s",
                    timestamp=datetime.now().isoformat()
                )
                for node in self.cluster_nodes
            }
    
    def cleanup_processes(self):
        """Kill stuck processes"""
        logger.info("Cleaning up stuck processes...")
        patterns = 'mpi_|openshmem_|upcxx_|prte|orted'
        cmd = f"pdsh -w {self.node_list} 'pkill -9 -f \"{patterns}\" 2>/dev/null || true'"
        try:
            subprocess.run(cmd, shell=True, timeout=15, capture_output=True)
            logger.info("✓ Cleanup complete")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")
    
    def save_results(self, results: List[BenchmarkResult], filename: str = None) -> Path:
        """Save results to JSON"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"benchmark_results_{timestamp}.json"
        
        output_file = self.results_dir / filename
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'cluster_nodes': self.cluster_nodes,
            'total': len(results),
            'successful': sum(1 for r in results if r.success),
            'failed': sum(1 for r in results if not r.success),
            'results': [
                {
                    'name': r.name,
                    'success': r.success,
                    'duration': r.duration,
                    'output': r.output[:500],
                    'error': r.error,
                    'exit_code': r.exit_code,
                    'timestamp': r.timestamp
                }
                for r in results
            ]
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Results saved: {output_file}")
        return output_file
    
    def print_summary(self, results: List[BenchmarkResult]):
        """Print summary"""
        print("\n" + "="*70)
        print("Benchmark Results Summary")
        print("="*70)
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"Total: {len(results)}")
        print(f"✓ Successful: {len(successful)}")
        print(f"✗ Failed: {len(failed)}")
        
        if successful:
            avg = sum(r.duration for r in successful) / len(successful)
            print(f"Average duration: {avg:.2f}s")
        
        if failed:
            print("\nFailed benchmarks:")
            for r in failed:
                print(f"  ✗ {r.name}: {r.error}")
        
        print("="*70)


def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cluster Benchmark Runner")
    parser.add_argument('--config', default='cluster_config_actual.yaml')
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Sync
    subparsers.add_parser('sync', help='Sync binaries to all nodes')
    
    # Run
    run_parser = subparsers.add_parser('run', help='Run benchmarks')
    run_parser.add_argument('benchmark', help='Benchmark name or "all"')
    run_parser.add_argument('--np', type=int, default=4)
    run_parser.add_argument('--timeout', type=int, default=60)
    run_parser.add_argument('--no-sync', action='store_true')
    
    # Cleanup
    subparsers.add_parser('cleanup', help='Clean up stuck processes')
    
    # List
    subparsers.add_parser('list', help='List available benchmarks')
    
    args = parser.parse_args()
    
    runner = ClusterBenchmarkRunner(config_file=Path(args.config))
    
    if args.command == 'sync':
        results = runner.sync_benchmarks()
        success = sum(1 for v in results.values() if v)
        print(f"\n✓ Synced to {success}/{len(results)} nodes")
    
    elif args.command == 'run':
        benchmarks = []
        
        if args.benchmark == 'all':
            benchmarks = [
                BenchmarkConfig("MPI Latency", "mpi_latency", "mpi", args.np, timeout=args.timeout),
                BenchmarkConfig("MPI Bandwidth", "mpi_bandwidth", "mpi", args.np, timeout=args.timeout),
            ]
        else:
            benchmarks = [
                BenchmarkConfig(args.benchmark, args.benchmark, "mpi", args.np, timeout=args.timeout)
            ]
        
        if not args.no_sync:
            runner.sync_benchmarks()
        
        results = []
        for config in benchmarks:
            result = runner.run_mpi_benchmark(config)
            results.append(result)
            time.sleep(2)
        
        runner.print_summary(results)
        runner.save_results(results)
    
    elif args.command == 'cleanup':
        runner.cleanup_processes()
    
    elif args.command == 'list':
        bin_dir = runner.benchmark_dir / "bin"
        if bin_dir.exists():
            print("\nAvailable benchmarks:")
            for binary in sorted(bin_dir.glob('*')):
                if binary.is_file() and binary.stat().st_mode & 0o111:
                    print(f"  - {binary.name}")


if __name__ == '__main__':
    main()
