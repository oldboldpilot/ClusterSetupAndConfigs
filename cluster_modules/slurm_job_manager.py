"""
Slurm Job Manager Module for HPC Cluster

This module handles Slurm job submission and management for various parallel
programming frameworks including MPI, OpenMP, UPC++, and OpenSHMEM.

Features:
- Jinja2-based job script generation
- Automatic resource allocation (cores, nodes, threads)
- Support for MPI, OpenMP, hybrid MPI+OpenMP, UPC++, OpenSHMEM jobs
- Job status monitoring and output retrieval
- Batch job submission with dependencies

Author: Olumuyiwa Oluwasanmi
Date: November 5, 2025
"""

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from jinja2 import Environment, FileSystemLoader, Template
import yaml


class SlurmJobManager:
    """
    Manages Slurm job submission for parallel programming frameworks.
    
    Attributes:
        cluster_config (Dict): Cluster configuration from YAML
        templates_dir (Path): Directory containing Jinja2 templates
        jobs_dir (Path): Directory for storing generated job scripts
        results_dir (Path): Directory for job output files
    """
    
    def __init__(self, config_path: Optional[Path] = None, 
                 jobs_dir: Optional[Path] = None,
                 results_dir: Optional[Path] = None):
        """
        Initialize Slurm Job Manager.
        
        Args:
            config_path: Path to cluster configuration YAML file
            jobs_dir: Directory for generated job scripts
            results_dir: Directory for job output files
        """
        # Load cluster configuration
        if config_path:
            with open(config_path, 'r') as f:
                self.cluster_config = yaml.safe_load(f)
        else:
            self.cluster_config = {}
        
        # Setup directories
        self.jobs_dir = jobs_dir or Path.home() / "cluster_build_sources" / "slurm_jobs"
        self.results_dir = results_dir or Path.home() / "cluster_build_sources" / "slurm_results"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        templates_path = Path(__file__).parent / "templates" / "slurm_jobs"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(templates_path)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Extract cluster information
        self._parse_cluster_info()
    
    def _parse_cluster_info(self) -> None:
        """Parse cluster configuration to extract node and thread information."""
        self.nodes = []
        self.threads_per_node = {}
        self.total_cores = 0
        
        # Parse master node
        if 'master' in self.cluster_config:
            master = self.cluster_config['master']
            if isinstance(master, list):
                # Master is a list with one dict
                master_dict = master[0] if master else {}
                master_ip = master_dict.get('ip')
                master_name = master_dict.get('name', 'master')
            elif isinstance(master, dict):
                master_ip = master.get('ip')
                master_name = master.get('name', 'master')
            else:
                master_ip = master
                master_name = 'master'
            
            self.nodes.append({'ip': master_ip, 'name': master_name})
            
            # Get thread count for master
            if 'threads' in self.cluster_config and master_ip and master_ip in self.cluster_config['threads']:
                threads = self.cluster_config['threads'][master_ip]
                self.threads_per_node[master_name] = threads
                self.total_cores += threads
        
        # Parse worker nodes
        if 'workers' in self.cluster_config:
            for worker in self.cluster_config['workers']:
                if isinstance(worker, dict):
                    worker_ip = worker.get('ip')
                    worker_name = worker.get('name', f"worker-{worker_ip}")
                else:
                    worker_ip = worker
                    worker_name = f"worker-{worker_ip}"
                
                self.nodes.append({'ip': worker_ip, 'name': worker_name})
                
                # Get thread count for worker
                if 'threads' in self.cluster_config and worker_ip in self.cluster_config['threads']:
                    threads = self.cluster_config['threads'][worker_ip]
                    self.threads_per_node[worker_name] = threads
                    self.total_cores += threads
        
        print(f"Cluster info: {len(self.nodes)} nodes, {self.total_cores} total cores")
    
    def generate_mpi_job(self, 
                        job_name: str,
                        executable: str,
                        num_tasks: int,
                        args: str = "",
                        time_limit: str = "01:00:00",
                        partition: str = "all",
                        output_file: Optional[str] = None) -> Path:
        """
        Generate MPI job script.
        
        Args:
            job_name: Name of the job
            executable: Path to MPI executable
            num_tasks: Number of MPI tasks/processes
            args: Command-line arguments for executable
            time_limit: Wall time limit (HH:MM:SS)
            partition: Slurm partition name
            output_file: Custom output file path
            
        Returns:
            Path to generated job script
        """
        template = self.jinja_env.get_template("mpi_job.sh.j2")
        
        # Calculate nodes needed (distribute evenly)
        num_nodes = min(len(self.nodes), num_tasks)
        tasks_per_node = num_tasks // num_nodes
        
        if output_file is None:
            output_file = str(self.results_dir / f"{job_name}_%j.out")
        
        job_script = template.render(
            job_name=job_name,
            num_nodes=num_nodes,
            num_tasks=num_tasks,
            tasks_per_node=tasks_per_node,
            time_limit=time_limit,
            partition=partition,
            output_file=output_file,
            error_file=str(self.results_dir / f"{job_name}_%j.err"),
            executable=executable,
            args=args,
            openmpi_prefix="/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8"
        )
        
        job_file = self.jobs_dir / f"{job_name}_mpi.sh"
        job_file.write_text(job_script)
        job_file.chmod(0o755)
        
        print(f"✓ Generated MPI job script: {job_file}")
        return job_file
    
    def generate_openmp_job(self,
                           job_name: str,
                           executable: str,
                           num_threads: Optional[int] = None,
                           args: str = "",
                           time_limit: str = "01:00:00",
                           partition: str = "all",
                           output_file: Optional[str] = None) -> Path:
        """
        Generate OpenMP job script.
        
        Args:
            job_name: Name of the job
            executable: Path to OpenMP executable
            num_threads: Number of OpenMP threads (default: all available cores on one node)
            args: Command-line arguments
            time_limit: Wall time limit
            partition: Slurm partition
            output_file: Custom output file path
            
        Returns:
            Path to generated job script
        """
        template = self.jinja_env.get_template("openmp_job.sh.j2")
        
        # Use max threads of first node if not specified
        if num_threads is None:
            first_node = list(self.threads_per_node.keys())[0]
            num_threads = self.threads_per_node[first_node]
        
        if output_file is None:
            output_file = str(self.results_dir / f"{job_name}_%j.out")
        
        job_script = template.render(
            job_name=job_name,
            num_threads=num_threads,
            time_limit=time_limit,
            partition=partition,
            output_file=output_file,
            error_file=str(self.results_dir / f"{job_name}_%j.err"),
            executable=executable,
            args=args
        )
        
        job_file = self.jobs_dir / f"{job_name}_openmp.sh"
        job_file.write_text(job_script)
        job_file.chmod(0o755)
        
        print(f"✓ Generated OpenMP job script: {job_file}")
        return job_file
    
    def generate_hybrid_job(self,
                           job_name: str,
                           executable: str,
                           num_tasks: int,
                           threads_per_task: int,
                           args: str = "",
                           time_limit: str = "01:00:00",
                           partition: str = "all",
                           output_file: Optional[str] = None) -> Path:
        """
        Generate hybrid MPI+OpenMP job script.
        
        Args:
            job_name: Name of the job
            executable: Path to hybrid executable
            num_tasks: Number of MPI tasks
            threads_per_task: OpenMP threads per MPI task
            args: Command-line arguments
            time_limit: Wall time limit
            partition: Slurm partition
            output_file: Custom output file path
            
        Returns:
            Path to generated job script
        """
        template = self.jinja_env.get_template("hybrid_job.sh.j2")
        
        # Calculate resources
        num_nodes = min(len(self.nodes), num_tasks)
        tasks_per_node = num_tasks // num_nodes
        cpus_per_task = threads_per_task
        
        if output_file is None:
            output_file = str(self.results_dir / f"{job_name}_%j.out")
        
        job_script = template.render(
            job_name=job_name,
            num_nodes=num_nodes,
            num_tasks=num_tasks,
            tasks_per_node=tasks_per_node,
            cpus_per_task=cpus_per_task,
            threads_per_task=threads_per_task,
            time_limit=time_limit,
            partition=partition,
            output_file=output_file,
            error_file=str(self.results_dir / f"{job_name}_%j.err"),
            executable=executable,
            args=args,
            openmpi_prefix="/home/linuxbrew/.linuxbrew/Cellar/open-mpi/5.0.8"
        )
        
        job_file = self.jobs_dir / f"{job_name}_hybrid.sh"
        job_file.write_text(job_script)
        job_file.chmod(0o755)
        
        print(f"✓ Generated Hybrid MPI+OpenMP job script: {job_file}")
        return job_file
    
    def generate_upcxx_job(self,
                          job_name: str,
                          executable: str,
                          num_processes: int,
                          args: str = "",
                          network: str = "mpi",
                          time_limit: str = "01:00:00",
                          partition: str = "all",
                          output_file: Optional[str] = None) -> Path:
        """
        Generate UPC++ job script.
        
        Args:
            job_name: Name of the job
            executable: Path to UPC++ executable
            num_processes: Number of UPC++ processes
            args: Command-line arguments
            network: GASNet network (mpi, smp, udp)
            time_limit: Wall time limit
            partition: Slurm partition
            output_file: Custom output file path
            
        Returns:
            Path to generated job script
        """
        template = self.jinja_env.get_template("upcxx_job.sh.j2")
        
        num_nodes = min(len(self.nodes), num_processes)
        
        if output_file is None:
            output_file = str(self.results_dir / f"{job_name}_%j.out")
        
        job_script = template.render(
            job_name=job_name,
            num_nodes=num_nodes,
            num_processes=num_processes,
            network=network,
            time_limit=time_limit,
            partition=partition,
            output_file=output_file,
            error_file=str(self.results_dir / f"{job_name}_%j.err"),
            executable=executable,
            args=args,
            upcxx_install="/home/linuxbrew/.linuxbrew",
            gasnet_root="/home/linuxbrew/.linuxbrew/gasnet"
        )
        
        job_file = self.jobs_dir / f"{job_name}_upcxx.sh"
        job_file.write_text(job_script)
        job_file.chmod(0o755)
        
        print(f"✓ Generated UPC++ job script: {job_file}")
        return job_file
    
    def generate_openshmem_job(self,
                              job_name: str,
                              executable: str,
                              num_pes: int,
                              args: str = "",
                              time_limit: str = "01:00:00",
                              partition: str = "all",
                              output_file: Optional[str] = None) -> Path:
        """
        Generate OpenSHMEM job script.
        
        Args:
            job_name: Name of the job
            executable: Path to OpenSHMEM executable
            num_pes: Number of Processing Elements
            args: Command-line arguments
            time_limit: Wall time limit
            partition: Slurm partition
            output_file: Custom output file path
            
        Returns:
            Path to generated job script
        """
        template = self.jinja_env.get_template("openshmem_job.sh.j2")
        
        num_nodes = min(len(self.nodes), num_pes)
        
        if output_file is None:
            output_file = str(self.results_dir / f"{job_name}_%j.out")
        
        job_script = template.render(
            job_name=job_name,
            num_nodes=num_nodes,
            num_pes=num_pes,
            time_limit=time_limit,
            partition=partition,
            output_file=output_file,
            error_file=str(self.results_dir / f"{job_name}_%j.err"),
            executable=executable,
            args=args,
            openshmem_install="/home/linuxbrew/.linuxbrew"
        )
        
        job_file = self.jobs_dir / f"{job_name}_openshmem.sh"
        job_file.write_text(job_script)
        job_file.chmod(0o755)
        
        print(f"✓ Generated OpenSHMEM job script: {job_file}")
        return job_file
    
    def submit_job(self, job_script: Path) -> Optional[int]:
        """
        Submit job to Slurm.
        
        Args:
            job_script: Path to job script
            
        Returns:
            Job ID if successful, None otherwise
        """
        try:
            result = subprocess.run(
                ["sbatch", str(job_script)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse job ID from output: "Submitted batch job 12345"
            output = result.stdout.strip()
            if "Submitted batch job" in output:
                job_id = int(output.split()[-1])
                print(f"✓ Job submitted with ID: {job_id}")
                return job_id
            else:
                print(f"⚠ Unexpected sbatch output: {output}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"✗ Job submission failed: {e.stderr}")
            return None
        except Exception as e:
            print(f"✗ Error submitting job: {e}")
            return None
    
    def get_job_status(self, job_id: int) -> Optional[Dict]:
        """
        Get status of a Slurm job.
        
        Args:
            job_id: Slurm job ID
            
        Returns:
            Dictionary with job information or None
        """
        try:
            result = subprocess.run(
                ["scontrol", "show", "job", str(job_id)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse output
            info = {}
            for line in result.stdout.split('\n'):
                for item in line.split():
                    if '=' in item:
                        key, value = item.split('=', 1)
                        info[key] = value
            
            return info
            
        except subprocess.CalledProcessError:
            return None
        except Exception as e:
            print(f"✗ Error getting job status: {e}")
            return None
    
    def wait_for_job(self, job_id: int, poll_interval: int = 5, timeout: int = 3600) -> Tuple[bool, str]:
        """
        Wait for job to complete.
        
        Args:
            job_id: Slurm job ID
            poll_interval: Seconds between status checks
            timeout: Maximum wait time in seconds
            
        Returns:
            Tuple of (success, final_state)
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            status = self.get_job_status(job_id)
            
            if status is None:
                # Job no longer in queue, check if completed
                return (True, "COMPLETED")
            
            job_state = status.get('JobState', 'UNKNOWN')
            
            if job_state in ['COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT']:
                return (job_state == 'COMPLETED', job_state)
            
            time.sleep(poll_interval)
        
        return (False, 'TIMEOUT')
    
    def cancel_job(self, job_id: int) -> bool:
        """
        Cancel a Slurm job.
        
        Args:
            job_id: Slurm job ID
            
        Returns:
            True if cancellation successful
        """
        try:
            subprocess.run(
                ["scancel", str(job_id)],
                capture_output=True,
                check=True
            )
            print(f"✓ Job {job_id} cancelled")
            return True
        except subprocess.CalledProcessError:
            print(f"✗ Failed to cancel job {job_id}")
            return False
    
    def get_job_output(self, job_id: int, job_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Retrieve job output and error files.
        
        Args:
            job_id: Slurm job ID
            job_name: Job name used when generating script
            
        Returns:
            Tuple of (stdout_content, stderr_content)
        """
        stdout_file = self.results_dir / f"{job_name}_{job_id}.out"
        stderr_file = self.results_dir / f"{job_name}_{job_id}.err"
        
        stdout_content = None
        stderr_content = None
        
        if stdout_file.exists():
            stdout_content = stdout_file.read_text()
        
        if stderr_file.exists():
            stderr_content = stderr_file.read_text()
        
        return (stdout_content, stderr_content)
    
    def list_jobs(self, user: Optional[str] = None) -> List[Dict]:
        """
        List current Slurm jobs.
        
        Args:
            user: Username to filter jobs (default: current user)
            
        Returns:
            List of job dictionaries
        """
        cmd = ["squeue", "--format=%i|%j|%t|%M|%D|%C", "--noheader"]
        if user:
            cmd.extend(["--user", user])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            jobs = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('|')
                    if len(parts) >= 6:
                        jobs.append({
                            'job_id': parts[0],
                            'name': parts[1],
                            'state': parts[2],
                            'time': parts[3],
                            'nodes': parts[4],
                            'cpus': parts[5]
                        })
            
            return jobs
            
        except subprocess.CalledProcessError:
            return []
