"""
Benchmark Manager Module for HPC Cluster Setup (Jinja2-based)

This module handles PGAS benchmark suite creation and execution using Jinja2 templates:
- Point-to-point latency tests (UPC++, MPI, OpenSHMEM, Berkeley UPC)
- Bandwidth benchmarks  
- Collective operation tests
- Makefile and run script generation from templates
- Multi-node benchmark execution

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from jinja2 import Environment, FileSystemLoader, Template


class BenchmarkManager:
    """
    Manages PGAS benchmark suite creation and execution across the cluster using Jinja2 templates.
    
    Attributes:
        username (str): Username for cluster nodes
        password (str): Password for authentication (never hardcoded)
        master_ip (str): Master node IP address
        worker_ips (List[str]): List of worker node IP addresses
        all_ips (List[str]): All cluster node IPs
        benchmark_dir (Path): Directory for benchmark files
        jinja_env (Environment): Jinja2 environment for template rendering
    """
    
    def __init__(self, username: str, password: str, master_ip: str, worker_ips: List[str],
                 benchmark_dir: Optional[Path] = None):
        """
        Initialize Benchmark manager with Jinja2 template support.
        
        Args:
            username: Username for cluster nodes
            password: Password for authentication
            master_ip: Master node IP address
            worker_ips: List of worker node IP addresses
            benchmark_dir: Optional custom benchmark directory
        """
        self.username = username
        self.password = password
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.all_ips = [master_ip] + worker_ips
        self.benchmark_dir = benchmark_dir or (Path.home() / "pgas_benchmarks")
        
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def create_benchmark_directory(self) -> bool:
        """
        Create benchmark directory structure.
        
        Returns:
            bool: True if directory created successfully, False otherwise
        """
        print("\n=== Creating Benchmark Directory Structure ===")
        
        try:
            self.benchmark_dir.mkdir(exist_ok=True)
            (self.benchmark_dir / "src").mkdir(exist_ok=True)
            (self.benchmark_dir / "bin").mkdir(exist_ok=True)
            (self.benchmark_dir / "results").mkdir(exist_ok=True)
            
            print(f"✓ Created benchmark directory: {self.benchmark_dir}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating benchmark directory: {e}")
            return False
    
    def create_upcxx_latency_benchmark(self, iterations: int = 1000, 
                                      warmup_iterations: int = 100) -> bool:
        """
        Create UPC++ point-to-point latency benchmark from Jinja2 template.
        
        Args:
            iterations: Number of measurement iterations
            warmup_iterations: Number of warmup iterations
            
        Returns:
            bool: True if benchmark created successfully, False otherwise
        """
        print("\n=== Creating UPC++ Latency Benchmark ===")
        
        try:
            template = self.jinja_env.get_template("upcxx_latency.cpp.j2")
            code = template.render(
                iterations=iterations,
                warmup_iterations=warmup_iterations
            )
            
            benchmark_file = self.benchmark_dir / "src" / "upcxx_latency.cpp"
            benchmark_file.write_text(code)
            
            print(f"✓ Created UPC++ latency benchmark: {benchmark_file}")
            print(f"  Iterations: {iterations}, Warmup: {warmup_iterations}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating UPC++ latency benchmark: {e}")
            return False
    
    def create_mpi_latency_benchmark(self, iterations: int = 1000,
                                    warmup_iterations: int = 100,
                                    message_size: int = 8) -> bool:
        """
        Create MPI point-to-point latency benchmark from Jinja2 template.
        
        Args:
            iterations: Number of measurement iterations
            warmup_iterations: Number of warmup iterations
            message_size: Message size in bytes
            
        Returns:
            bool: True if benchmark created successfully, False otherwise
        """
        print("\n=== Creating MPI Latency Benchmark ===")
        
        try:
            template = self.jinja_env.get_template("mpi_latency.cpp.j2")
            code = template.render(
                iterations=iterations,
                warmup_iterations=warmup_iterations,
                message_size=message_size
            )
            
            benchmark_file = self.benchmark_dir / "src" / "mpi_latency.cpp"
            benchmark_file.write_text(code)
            
            print(f"✓ Created MPI latency benchmark: {benchmark_file}")
            print(f"  Iterations: {iterations}, Warmup: {warmup_iterations}, Size: {message_size} bytes")
            return True
            
        except Exception as e:
            print(f"✗ Error creating MPI latency benchmark: {e}")
            return False
    
    def create_upcxx_bandwidth_benchmark(self, iterations: int = 100,
                                        message_sizes: Optional[List[int]] = None) -> bool:
        """
        Create UPC++ bandwidth benchmark from Jinja2 template.
        
        Args:
            iterations: Number of measurement iterations
            message_sizes: List of message sizes to test (in bytes)
            
        Returns:
            bool: True if benchmark created successfully, False otherwise
        """
        print("\n=== Creating UPC++ Bandwidth Benchmark ===")
        
        if message_sizes is None:
            message_sizes = [1024, 4096, 16384, 65536, 262144, 1048576]
        
        try:
            template = self.jinja_env.get_template("upcxx_bandwidth.cpp.j2")
            code = template.render(
                iterations=iterations,
                message_sizes=message_sizes
            )
            
            benchmark_file = self.benchmark_dir / "src" / "upcxx_bandwidth.cpp"
            benchmark_file.write_text(code)
            
            print(f"✓ Created UPC++ bandwidth benchmark: {benchmark_file}")
            print(f"  Iterations: {iterations}, Message sizes: {len(message_sizes)} values")
            return True
            
        except Exception as e:
            print(f"✗ Error creating UPC++ bandwidth benchmark: {e}")
            return False
    
    def create_openshmem_latency_benchmark(self, iterations: int = 1000,
                                          warmup_iterations: int = 100) -> bool:
        """
        Create OpenSHMEM point-to-point latency benchmark from Jinja2 template.
        
        Args:
            iterations: Number of measurement iterations
            warmup_iterations: Number of warmup iterations
            
        Returns:
            bool: True if benchmark created successfully, False otherwise
        """
        print("\n=== Creating OpenSHMEM Latency Benchmark ===")
        
        try:
            template = self.jinja_env.get_template("openshmem_latency.cpp.j2")
            code = template.render(
                iterations=iterations,
                warmup_iterations=warmup_iterations
            )
            
            benchmark_file = self.benchmark_dir / "src" / "openshmem_latency.cpp"
            benchmark_file.write_text(code)
            
            print(f"✓ Created OpenSHMEM latency benchmark: {benchmark_file}")
            print(f"  Iterations: {iterations}, Warmup: {warmup_iterations}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating OpenSHMEM latency benchmark: {e}")
            return False
    
    def create_berkeley_upc_latency_benchmark(self, iterations: int = 1000,
                                             warmup_iterations: int = 100) -> bool:
        """
        Create Berkeley UPC point-to-point latency benchmark from Jinja2 template.
        
        Args:
            iterations: Number of measurement iterations
            warmup_iterations: Number of warmup iterations
            
        Returns:
            bool: True if benchmark created successfully, False otherwise
        """
        print("\n=== Creating Berkeley UPC Latency Benchmark ===")
        
        try:
            template = self.jinja_env.get_template("berkeley_upc_latency.c.j2")
            code = template.render(
                iterations=iterations,
                warmup_iterations=warmup_iterations
            )
            
            benchmark_file = self.benchmark_dir / "src" / "berkeley_upc_latency.c"
            benchmark_file.write_text(code)
            
            print(f"✓ Created Berkeley UPC latency benchmark: {benchmark_file}")
            print(f"  Iterations: {iterations}, Warmup: {warmup_iterations}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating Berkeley UPC latency benchmark: {e}")
            return False
    
    def create_makefile(self, config: Optional[Dict] = None) -> bool:
        """
        Create Makefile for compiling benchmarks from Jinja2 template.
        
        Args:
            config: Optional configuration dictionary with compiler settings
            
        Returns:
            bool: True if Makefile created successfully, False otherwise
        """
        print("\n=== Creating Makefile ===")
        
        # Default configuration
        default_config = {
            'upcxx_compiler': 'upcxx',
            'mpi_compiler': 'mpicxx',
            'openshmem_compiler': 'oshcc',
            'berkeley_upc_compiler': 'upcc',
            'upcxx_flags': '-O3',
            'mpi_flags': '-O3',
            'openshmem_flags': '-O3',
            'berkeley_upc_flags': '-O3',
            'benchmarks': [
                'upcxx_latency',
                'upcxx_bandwidth',
                'mpi_latency',
                'openshmem_latency',
                'berkeley_upc_latency'
            ]
        }
        
        if config:
            default_config.update(config)
        
        try:
            template = self.jinja_env.get_template("Makefile.j2")
            makefile_content = template.render(**default_config)
            
            makefile_path = self.benchmark_dir / "Makefile"
            makefile_path.write_text(makefile_content)
            
            print(f"✓ Created Makefile: {makefile_path}")
            print(f"  Benchmarks: {len(default_config['benchmarks'])}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating Makefile: {e}")
            return False
    
    def create_run_script(self, num_procs: int = 2) -> bool:
        """
        Create shell script to run all benchmarks from Jinja2 template.
        
        Args:
            num_procs: Number of processes/ranks to use
            
        Returns:
            bool: True if run script created successfully, False otherwise
        """
        print("\n=== Creating Run Script ===")
        
        benchmarks = [
            {'name': 'upcxx_latency', 'launcher': 'upcxx-run'},
            {'name': 'upcxx_bandwidth', 'launcher': 'upcxx-run'},
            {'name': 'mpi_latency', 'launcher': 'mpirun'},
            {'name': 'openshmem_latency', 'launcher': 'oshrun'},
            {'name': 'berkeley_upc_latency', 'launcher': 'upcc-run'}
        ]
        
        try:
            template = self.jinja_env.get_template("run_benchmarks.sh.j2")
            script_content = template.render(
                num_procs=num_procs,
                benchmark_dir=str(self.benchmark_dir),
                benchmarks=benchmarks
            )
            
            script_path = self.benchmark_dir / "run_benchmarks.sh"
            script_path.write_text(script_content)
            script_path.chmod(0o755)  # Make executable
            
            print(f"✓ Created run script: {script_path}")
            print(f"  Number of processes: {num_procs}")
            print(f"  Benchmarks: {len(benchmarks)}")
            return True
            
        except Exception as e:
            print(f"✗ Error creating run script: {e}")
            return False
    
    def create_all_benchmarks(self, iterations: int = 1000,
                             warmup_iterations: int = 100,
                             num_procs: int = 2) -> bool:
        """
        Create all benchmark files, Makefile, and run script.
        
        Args:
            iterations: Number of measurement iterations
            warmup_iterations: Number of warmup iterations
            num_procs: Number of processes for run script
            
        Returns:
            bool: True if all benchmarks created successfully, False otherwise
        """
        print("\n=== Creating Complete Benchmark Suite ===")
        
        success = True
        success = success and self.create_benchmark_directory()
        success = success and self.create_upcxx_latency_benchmark(iterations, warmup_iterations)
        success = success and self.create_mpi_latency_benchmark(iterations, warmup_iterations)
        success = success and self.create_upcxx_bandwidth_benchmark(iterations // 10)
        success = success and self.create_openshmem_latency_benchmark(iterations, warmup_iterations)
        success = success and self.create_berkeley_upc_latency_benchmark(iterations, warmup_iterations)
        success = success and self.create_makefile()
        success = success and self.create_run_script(num_procs)
        
        if success:
            print("\n✓ Benchmark suite created successfully!")
            print(f"  Location: {self.benchmark_dir}")
        else:
            print("\n✗ Some benchmarks failed to create")
        
        return success
    
    def compile_benchmarks(self) -> bool:
        """
        Compile all benchmarks using the generated Makefile.
        
        Returns:
            bool: True if compilation successful, False otherwise
        """
        print("\n=== Compiling Benchmarks ===")
        
        makefile_path = self.benchmark_dir / "Makefile"
        if not makefile_path.exists():
            print(f"✗ Makefile not found: {makefile_path}")
            return False
        
        try:
            result = subprocess.run(
                ['make', '-C', str(self.benchmark_dir), 'all'],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✓ Benchmarks compiled successfully")
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
    
    def distribute_benchmarks_pdsh(self) -> bool:
        """
        Distribute compiled benchmarks to all cluster nodes using pdsh.
        Falls back to sequential distribution if pdsh is not available.
        
        Returns:
            bool: True if distribution successful, False otherwise
        """
        print("\n=== Distributing Benchmarks to Cluster ===")
        
        # Check if benchmarks are compiled
        bin_dir = self.benchmark_dir / "bin"
        if not bin_dir.exists() or not any(bin_dir.iterdir()):
            print("✗ No compiled benchmarks found. Run compile_benchmarks() first.")
            return False
        
        # Get local IP to exclude from distribution
        local_ip = self._get_local_ip()
        target_ips = [ip for ip in self.all_ips if ip != local_ip]
        
        if not target_ips:
            print("✓ Running on single node, no distribution needed")
            return True
        
        # Try pdsh first
        pdsh_available = subprocess.run(['which', 'pdsh'], 
                                       capture_output=True).returncode == 0
        
        if pdsh_available:
            return self._distribute_with_pdsh(target_ips)
        else:
            print("⚠ pdsh not available, using sequential distribution")
            return self._distribute_sequential(target_ips)
    
    def _distribute_with_pdsh(self, target_ips: List[str]) -> bool:
        """
        Distribute benchmarks using pdsh for parallel execution.
        
        Args:
            target_ips: List of target IP addresses
            
        Returns:
            bool: True if distribution successful
        """
        print(f"Using pdsh to distribute to {len(target_ips)} nodes...")
        
        try:
            # Create hosts string for pdsh
            hosts = ','.join(target_ips)
            
            # Use rsync via pdsh
            cmd = [
                'pdsh', '-w', hosts,
                'rsync', '-avz', '--delete',
                f'{self.username}@{self.master_ip}:{self.benchmark_dir}/',
                str(self.benchmark_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✓ Distributed benchmarks to {len(target_ips)} nodes via pdsh")
                return True
            else:
                print(f"✗ pdsh distribution failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error with pdsh distribution: {e}")
            return False
    
    def _distribute_sequential(self, target_ips: List[str]) -> bool:
        """
        Distribute benchmarks sequentially using rsync.
        
        Args:
            target_ips: List of target IP addresses
            
        Returns:
            bool: True if all distributions successful
        """
        success = True
        
        for ip in target_ips:
            try:
                print(f"  Copying to {ip}...")
                cmd = [
                    'rsync', '-avz', '--delete',
                    f'{self.benchmark_dir}/',
                    f'{self.username}@{ip}:{self.benchmark_dir}/'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    print(f"  ✓ Copied to {ip}")
                else:
                    print(f"  ✗ Failed to copy to {ip}: {result.stderr}")
                    success = False
                    
            except Exception as e:
                print(f"  ✗ Error copying to {ip}: {e}")
                success = False
        
        return success
    
    def _get_local_ip(self) -> Optional[str]:
        """
        Get the local machine's IP address.
        
        Returns:
            Optional[str]: Local IP address or None if not found
        """
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                if ips:
                    return ips[0]
        except:
            pass
        return None
