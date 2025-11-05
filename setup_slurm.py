#!/usr/bin/env python3
"""
Slurm and Munge Setup Script

Configures Munge authentication and Slurm services across the cluster
to enable job submission.

Usage:
    export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
    uv run python setup_slurm.py --config cluster_config_actual.yaml

Author: Olumuyiwa Oluwasanmi
Date: November 5, 2025
"""

import sys
import argparse
from pathlib import Path
import yaml
import getpass

# Add cluster_modules to path
sys.path.insert(0, str(Path(__file__).parent))

from cluster_modules.slurm_setup_helper import SlurmSetupHelper


def load_config(config_path: Path) -> dict:
    """Load cluster configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_node_ips(config: dict) -> tuple:
    """Extract master and worker IPs from configuration."""
    # Parse master
    master = config.get('master', {})
    if isinstance(master, list):
        # Master is a list with one dict
        master_ip = master[0].get('ip') if master else None
    elif isinstance(master, dict):
        master_ip = master.get('ip')
    else:
        master_ip = master
    
    # Parse workers
    worker_ips = []
    for worker in config.get('workers', []):
        if isinstance(worker, dict):
            worker_ips.append(worker.get('ip'))
        else:
            worker_ips.append(worker)
    
    return master_ip, worker_ips


def main():
    parser = argparse.ArgumentParser(
        description="Setup Slurm and Munge authentication for job submission"
    )
    parser.add_argument(
        '--config', '-c',
        type=Path,
        required=True,
        help="Path to cluster configuration YAML file"
    )
    parser.add_argument(
        '--password', '-p',
        action='store_true',
        help="Prompt for password (for remote operations)"
    )
    parser.add_argument(
        '--skip-munge',
        action='store_true',
        help="Skip Munge setup (if already configured)"
    )
    parser.add_argument(
        '--partition',
        type=str,
        default="normal",
        help="Slurm partition name to create (default: normal)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    if not args.config.exists():
        print(f"✗ Configuration file not found: {args.config}")
        sys.exit(1)
    
    print("="*70)
    print("Slurm and Munge Setup")
    print("="*70)
    print(f"Configuration: {args.config}")
    
    config = load_config(args.config)
    master_ip, worker_ips = get_node_ips(config)
    username = config.get('username', getpass.getuser())
    
    print(f"Master: {master_ip}")
    print(f"Workers: {', '.join(worker_ips)}")
    print(f"Username: {username}")
    print("="*70)
    
    # Get password if needed
    password = ""
    if args.password:
        password = getpass.getpass("Enter cluster password: ")
    
    # Initialize setup helper
    helper = SlurmSetupHelper(username, password, master_ip, worker_ips)
    
    # Setup Munge
    if not args.skip_munge:
        print("\n" + "="*70)
        print("Step 1: Munge Authentication Setup")
        print("="*70)
        
        if not helper.setup_munge_master():
            print("\n✗ Failed to setup Munge on master node")
            print("  Please check error messages above")
            sys.exit(1)
        
        if worker_ips and password:
            print("\nDistributing Munge key to workers...")
            if not helper.distribute_munge_key():
                print("\n⚠ Failed to distribute Munge key to some workers")
                print("  You may need to manually copy /etc/munge/munge.key to each worker")
        else:
            print("\n⚠ Skipping Munge key distribution (no password provided)")
            print("  To distribute manually:")
            print("    1. Copy /etc/munge/munge.key from master to each worker")
            print("    2. Place in /etc/munge/munge.key on each worker")
            print("    3. Run: sudo chown munge:munge /etc/munge/munge.key")
            print("    4. Run: sudo chmod 400 /etc/munge/munge.key")
            print("    5. Run: sudo systemctl restart munge")
    else:
        print("\n⚠ Skipping Munge setup (--skip-munge specified)")
    
    # Configure Slurm partition
    print("\n" + "="*70)
    print("Step 2: Slurm Partition Configuration")
    print("="*70)
    
    if not helper.configure_slurm_partition(args.partition):
        print(f"\n⚠ Failed to configure partition '{args.partition}'")
        print("  Partition may already exist or slurm.conf needs manual editing")
    
    # Restart Slurm services
    print("\n" + "="*70)
    print("Step 3: Restart Slurm Services")
    print("="*70)
    
    if not helper.restart_slurm_services():
        print("\n⚠ Some Slurm services failed to restart")
        print("  Check logs with: sudo journalctl -u slurmctld -u slurmd -n 50")
    
    # Verify cluster
    print("\n" + "="*70)
    print("Step 4: Verify Slurm Cluster")
    print("="*70)
    
    if helper.verify_slurm_cluster():
        print("\n" + "="*70)
        print("✓ Slurm cluster setup complete and operational!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Test job submission: uv run python test_slurm_jobs.py")
        print("  2. View cluster status: sinfo")
        print("  3. Submit a test job: sbatch <job_script>")
        print("  4. View job queue: squeue")
    else:
        print("\n" + "="*70)
        print("✗ Slurm cluster verification failed")
        print("="*70)
        print("\nTroubleshooting:")
        print("  1. Check Munge: sudo systemctl status munge")
        print("  2. Check Slurm controller: sudo systemctl status slurmctld")
        print("  3. Check Slurm daemon: sudo systemctl status slurmd")
        print("  4. View logs: sudo journalctl -u slurmctld -u slurmd -u munge -n 100")
        print("  5. Test Munge: munge -n | unmunge")
        sys.exit(1)


if __name__ == "__main__":
    main()
