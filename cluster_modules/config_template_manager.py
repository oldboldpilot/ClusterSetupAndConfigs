#!/usr/bin/env python3
"""
Template-Based Configuration Manager

Unified configuration management using Jinja2 templates for all cluster
configuration files (MPI, SSH, Slurm, benchmarks).

This module provides a modular, maintainable approach to generating
configuration files from templates with proper validation and deployment.
"""

import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class NodeConfig:
    """Configuration for a single cluster node"""
    hostname: str
    ip: str
    cpus: int
    memory_mb: int
    os: str
    username: str = "muyiwa"
    is_master: bool = False


@dataclass
class ClusterConfig:
    """Complete cluster configuration"""
    name: str
    master: NodeConfig
    workers: List[NodeConfig]
    subnet: str
    openmpi_version: str = "5.0.8"
    homebrew_prefix: str = "/home/linuxbrew/.linuxbrew"
    btl_port_min: int = 50000
    oob_port_range: str = "50100-50200"
    ssh_key_path: Optional[str] = None
    
    @property
    def all_nodes(self) -> List[NodeConfig]:
        """Get all nodes (master + workers)"""
        return [self.master] + self.workers
    
    @property
    def all_ips(self) -> List[str]:
        """Get all node IPs"""
        return [node.ip for node in self.all_nodes]
    
    @property
    def total_cpus(self) -> int:
        """Total CPUs across cluster"""
        return sum(node.cpus for node in self.all_nodes)
    
    @property
    def total_memory_gb(self) -> int:
        """Total memory in GB across cluster"""
        return sum(node.memory_mb for node in self.all_nodes) // 1024


class ConfigTemplateManager:
    """Manages Jinja2 templates for configuration files"""
    
    def __init__(self, template_dir: Path = None, config_file: str = "cluster_config_actual.yaml"):
        self.base_dir = Path(__file__).parent.parent
        self.template_dir = template_dir or self.base_dir / "templates"
        self.config_file = self.base_dir / config_file
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Load cluster configuration
        self.cluster_config = self._load_cluster_config()
        
        logger.info(f"Initialized ConfigTemplateManager")
        logger.info(f"  Template dir: {self.template_dir}")
        logger.info(f"  Cluster: {self.cluster_config.name}")
        logger.info(f"  Nodes: {len(self.cluster_config.all_nodes)}")
    
    def _load_cluster_config(self) -> ClusterConfig:
        """Load cluster configuration from YAML file"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_file}")
        
        with open(self.config_file) as f:
            config = yaml.safe_load(f)
        
        # Parse master node (handle both dict and list formats)
        master_data = config['master']
        if isinstance(master_data, list):
            master_data = master_data[0]  # Take first element if list
        
        master = NodeConfig(
            hostname=master_data.get('name', 'master'),
            ip=master_data['ip'],
            cpus=config.get('threads', {}).get(master_data['ip'], 32),
            memory_mb=64 * 1024,  # Default to 64GB
            os=master_data.get('os', 'ubuntu'),
            username=config.get('username', 'muyiwa'),
            is_master=True
        )
        
        # Parse worker nodes
        workers = []
        for worker_data in config.get('workers', []):
            worker = NodeConfig(
                hostname=worker_data.get('name', f"worker-{worker_data['ip'].split('.')[-1]}"),
                ip=worker_data['ip'],
                cpus=config.get('threads', {}).get(worker_data['ip'], 16),
                memory_mb=32 * 1024,  # Default to 32GB
                os=worker_data.get('os', 'ubuntu'),
                username=config.get('username', 'muyiwa'),
                is_master=False
            )
            workers.append(worker)
        
        # Determine subnet from IPs
        ip_parts = master.ip.split('.')
        subnet = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        
        return ClusterConfig(
            name="hpc_cluster",
            master=master,
            workers=workers,
            subnet=subnet
        )
    
    def _get_template_context(self) -> Dict[str, Any]:
        """Get common template context variables"""
        return {
            'generation_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cluster_name': self.cluster_config.name,
            'cluster_subnet': self.cluster_config.subnet,
            'cluster_ips': self.cluster_config.all_ips,
            'master_node': {
                'hostname': self.cluster_config.master.hostname,
                'ip': self.cluster_config.master.ip,
                'cpus': self.cluster_config.master.cpus,
                'memory_mb': self.cluster_config.master.memory_mb,
                'username': self.cluster_config.master.username,
            },
            'worker_nodes': [
                {
                    'hostname': w.hostname,
                    'ip': w.ip,
                    'cpus': w.cpus,
                    'memory_mb': w.memory_mb,
                    'username': w.username,
                }
                for w in self.cluster_config.workers
            ],
            'nodes': [
                {
                    'hostname': n.hostname,
                    'ip': n.ip,
                    'cpus': n.cpus,
                    'memory_mb': n.memory_mb,
                    'username': n.username,
                }
                for n in self.cluster_config.all_nodes
            ],
            'openmpi_version': self.cluster_config.openmpi_version,
            'homebrew_prefix': self.cluster_config.homebrew_prefix,
            'btl_port_min': self.cluster_config.btl_port_min,
            'oob_port_range': self.cluster_config.oob_port_range,
            'oob_port_max': int(self.cluster_config.oob_port_range.split('-')[1]),
            'ssh_key_path': self.cluster_config.ssh_key_path,
            'total_cpus': self.cluster_config.total_cpus,
            'total_memory_gb': self.cluster_config.total_memory_gb,
        }
    
    def render_template(self, template_path: str, extra_context: Dict = None) -> str:
        """
        Render a Jinja2 template with cluster configuration
        
        Args:
            template_path: Relative path to template from template_dir
            extra_context: Additional context variables
        
        Returns:
            Rendered template content
        """
        template = self.jinja_env.get_template(template_path)
        context = self._get_template_context()
        
        if extra_context:
            context.update(extra_context)
        
        return template.render(**context)
    
    def generate_mpi_mca_config(self, debug: bool = False, use_exact_ips: bool = True) -> str:
        """
        Generate OpenMPI MCA parameters configuration
        
        Args:
            debug: Enable verbose debugging
            use_exact_ips: Use exact IP list instead of subnet (recommended for multi-homed nodes)
        """
        # Create CIDR-formatted IP list for exact IP matching
        cluster_ips_cidr = ','.join(f"{ip}/32" for ip in self.cluster_config.all_ips)
        
        return self.render_template('mpi/mca-params.conf.j2', {
            'enable_debug': debug,
            'use_exact_ips': use_exact_ips,
            'cluster_ips_cidr': cluster_ips_cidr
        })
    
    def generate_mpi_hostfile(self, slots_mode: str = 'max', output_filename: str = 'hostfile') -> str:
        """
        Generate MPI hostfile
        
        Args:
            slots_mode: 'max' (all CPUs), 'optimal' (1 per node), or integer
            output_filename: Name of hostfile for usage examples
        """
        return self.render_template('mpi/hostfile.j2', {
            'slots_per_node': slots_mode,
            'output_filename': output_filename
        })
    
    def generate_ssh_config(self, connection_timeout: int = 10) -> str:
        """Generate SSH configuration"""
        return self.render_template('ssh/config.j2', {
            'connection_timeout': connection_timeout
        })
    
    def generate_slurm_config(self, mpi_default: str = 'pmi2') -> str:
        """Generate Slurm configuration"""
        return self.render_template('slurm/slurm.conf.j2', {
            'mpi_default': mpi_default,
            'slurm_user': 'slurm',
            'spool_dir': '/var/spool/slurm',
            'log_dir': '/var/log/slurm'
        })
    
    def deploy_config_to_nodes(
        self,
        content: str,
        remote_path: str,
        nodes: List[str] = None,
        backup: bool = True
    ) -> Dict[str, bool]:
        """
        Deploy configuration content to cluster nodes
        
        Args:
            content: Configuration file content
            remote_path: Destination path on remote nodes (e.g., '~/.openmpi/mca-params.conf')
            nodes: List of node IPs to deploy to (None = all nodes)
            backup: Create backup before overwriting
        
        Returns:
            Dict mapping node IP to success status
        """
        if nodes is None:
            nodes = self.cluster_config.all_ips
        
        # Write to temporary file
        temp_file = Path('/tmp/config_deploy.tmp')
        temp_file.write_text(content)
        
        results = {}
        for node_ip in nodes:
            try:
                # Create directory if needed
                remote_dir = Path(remote_path).parent
                subprocess.run(
                    f"ssh {node_ip} 'mkdir -p {remote_dir}'",
                    shell=True,
                    check=True,
                    timeout=10,
                    capture_output=True
                )
                
                # Backup existing file
                if backup:
                    subprocess.run(
                        f"ssh {node_ip} 'cp {remote_path} {remote_path}.backup 2>/dev/null || true'",
                        shell=True,
                        timeout=10,
                        capture_output=True
                    )
                
                # Copy new config
                subprocess.run(
                    f"scp {temp_file} {node_ip}:{remote_path}",
                    shell=True,
                    check=True,
                    timeout=15,
                    capture_output=True
                )
                
                results[node_ip] = True
                logger.info(f"✓ Deployed to {node_ip}")
                
            except subprocess.TimeoutExpired:
                results[node_ip] = False
                logger.error(f"✗ {node_ip} - timeout")
            except subprocess.CalledProcessError as e:
                results[node_ip] = False
                logger.error(f"✗ {node_ip} - error: {e}")
        
        # Cleanup
        temp_file.unlink(missing_ok=True)
        
        return results
    
    def print_summary(self):
        """Print cluster configuration summary"""
        print("\n" + "=" * 70)
        print(f"Cluster Configuration: {self.cluster_config.name}")
        print("=" * 70)
        print(f"Subnet: {self.cluster_config.subnet}")
        print(f"Total Nodes: {len(self.cluster_config.all_nodes)}")
        print(f"Total CPUs: {self.cluster_config.total_cpus}")
        print(f"Total Memory: {self.cluster_config.total_memory_gb} GB")
        print(f"\nMaster Node: {self.cluster_config.master.hostname} ({self.cluster_config.master.ip})")
        print(f"  CPUs: {self.cluster_config.master.cpus}")
        print(f"  Memory: {self.cluster_config.master.memory_mb // 1024} GB")
        print(f"\nWorker Nodes: {len(self.cluster_config.workers)}")
        for worker in self.cluster_config.workers:
            print(f"  {worker.hostname} ({worker.ip}) - {worker.cpus} CPUs, {worker.memory_mb // 1024} GB")
        print("=" * 70)


def main():
    """CLI interface for template manager"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Template-based cluster configuration manager"
    )
    parser.add_argument(
        '--config',
        default='cluster_config_actual.yaml',
        help='Cluster configuration file'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate configuration files')
    gen_parser.add_argument('type', choices=['mpi-mca', 'mpi-hostfile', 'ssh', 'slurm', 'all'])
    gen_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    gen_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy configuration to nodes')
    deploy_parser.add_argument('type', choices=['mpi-mca', 'ssh', 'slurm'])
    deploy_parser.add_argument('--nodes', nargs='+', help='Specific nodes to deploy to')
    deploy_parser.add_argument('--no-backup', action='store_true', help='Skip backup')
    
    # Summary command
    subparsers.add_parser('summary', help='Print cluster configuration summary')
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = ConfigTemplateManager(config_file=args.config)
    
    if args.command == 'summary':
        manager.print_summary()
    
    elif args.command == 'generate':
        if args.type in ['mpi-mca', 'all']:
            content = manager.generate_mpi_mca_config(debug=args.debug)
            if args.output:
                Path(args.output).write_text(content)
                print(f"Generated MPI MCA config: {args.output}")
            else:
                print(content)
        
        if args.type in ['mpi-hostfile', 'all']:
            content = manager.generate_mpi_hostfile()
            if args.output:
                Path(args.output).write_text(content)
                print(f"Generated MPI hostfile: {args.output}")
            elif args.type == 'mpi-hostfile':
                print(content)
        
        if args.type in ['ssh', 'all']:
            content = manager.generate_ssh_config()
            if args.output:
                Path(args.output).write_text(content)
                print(f"Generated SSH config: {args.output}")
            elif args.type == 'ssh':
                print(content)
        
        if args.type in ['slurm', 'all']:
            content = manager.generate_slurm_config()
            if args.output:
                Path(args.output).write_text(content)
                print(f"Generated Slurm config: {args.output}")
            elif args.type == 'slurm':
                print(content)
    
    elif args.command == 'deploy':
        if args.type == 'mpi-mca':
            content = manager.generate_mpi_mca_config()
            results = manager.deploy_config_to_nodes(
                content,
                '~/.openmpi/mca-params.conf',
                nodes=args.nodes,
                backup=not args.no_backup
            )
            
            success_count = sum(1 for v in results.values() if v)
            print(f"\nDeployed to {success_count}/{len(results)} nodes")
            
            if success_count == len(results):
                print("✓ All nodes configured successfully!")
            else:
                print("✗ Some nodes failed. Check logs above.")


if __name__ == '__main__':
    main()
