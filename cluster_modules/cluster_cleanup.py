#!/usr/bin/env python3
"""
Cluster Cleanup Module
======================
Kills orphaned and conflicting processes across all cluster nodes.
Should be called before cluster setup to ensure clean state.

Author: ClusterSetupAndConfigs
"""

import subprocess
import sys
from typing import List, Dict
from pathlib import Path


class ClusterCleanup:
    """Handle cleanup of orphaned processes across cluster nodes."""
    
    # Processes that commonly cause conflicts
    # Note: Be specific to avoid killing the cleanup script itself
    PROCESS_PATTERNS = [
        'prterun',
        'mpirun.*test_mpi', 
        'orted',
        'sshd.*mpi',
        'oshrun',
        'upcxx-run',
    ]
    
    def __init__(self, master_ip: str, worker_ips: List[str], username: str = "muyiwa"):
        """
        Initialize cluster cleanup.
        
        Args:
            master_ip: Master node IP address
            worker_ips: List of worker node IP addresses
            username: SSH username for cluster access
        """
        self.master_ip = master_ip
        self.worker_ips = worker_ips
        self.username = username
        self.all_ips = [master_ip] + worker_ips
        
    def cleanup_local(self) -> bool:
        """
        Clean up processes on local (master) node.
        
        Returns:
            bool: True if cleanup successful
        """
        print("\n" + "="*70)
        print("CLEANING UP LOCAL NODE")
        print("="*70)
        
        success = True
        for pattern in self.PROCESS_PATTERNS:
            try:
                # Use pkill with pattern matching
                cmd = ['pkill', '-9', '-f', pattern]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # pkill returns 0 if processes were killed, 1 if none found
                if result.returncode == 0:
                    print(f"  ✓ Killed processes matching: {pattern}")
                elif result.returncode == 1:
                    # No processes found - this is fine
                    pass
                else:
                    print(f"  ⚠ Warning cleaning {pattern}: {result.stderr}")
                    
            except Exception as e:
                print(f"  ✗ Error killing {pattern}: {e}")
                success = False
                
        # Wait a moment for processes to terminate
        import time
        time.sleep(1)
        
        print("\n✓ Local cleanup completed")
        return success
    
    def cleanup_node(self, ip: str) -> bool:
        """
        Clean up processes on a specific remote node.
        
        Args:
            ip: IP address of node to clean
            
        Returns:
            bool: True if cleanup successful
        """
        print(f"\n→ Cleaning up node: {ip}")
        
        success = True
        for pattern in self.PROCESS_PATTERNS:
            try:
                # Build kill command for remote execution
                kill_cmd = f"pkill -9 -f '{pattern}' 2>/dev/null; exit 0"
                
                cmd = [
                    'ssh',
                    '-o', 'StrictHostKeyChecking=no',
                    '-o', 'ConnectTimeout=5',
                    f'{self.username}@{ip}',
                    kill_cmd
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                # SSH returns 0 on success
                if result.returncode == 0:
                    pass  # Quiet success
                else:
                    print(f"    ⚠ Warning cleaning {pattern} on {ip}")
                    
            except subprocess.TimeoutExpired:
                print(f"    ⚠ Timeout cleaning {pattern} on {ip}")
                success = False
            except Exception as e:
                print(f"    ✗ Error cleaning {pattern} on {ip}: {e}")
                success = False
                
        print(f"  ✓ Node {ip} cleaned")
        return success
    
    def cleanup_all_nodes(self) -> bool:
        """
        Clean up processes on all cluster nodes.
        
        Returns:
            bool: True if all cleanups successful
        """
        print("\n" + "="*70)
        print("CLEANING UP ALL CLUSTER NODES")
        print("="*70)
        
        success = True
        
        # Clean local node first
        if not self.cleanup_local():
            success = False
            
        # Clean worker nodes
        for ip in self.worker_ips:
            if not self.cleanup_node(ip):
                success = False
                
        # Final verification - check for remaining processes
        print("\n" + "="*70)
        print("VERIFICATION")
        print("="*70)
        self._verify_cleanup()
        
        return success
    
    def _verify_cleanup(self):
        """Verify that problematic processes are gone."""
        try:
            # Check for any remaining MPI processes
            result = subprocess.run(
                ['pgrep', '-f', 'mpi|prte|orted'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ⚠ Warning: Some MPI processes still running")
                print(f"    PIDs: {result.stdout.strip()}")
            else:
                print("  ✓ No orphaned MPI processes found")
                
        except Exception as e:
            print(f"  ⚠ Could not verify: {e}")
    
    def cleanup_stale_files(self) -> bool:
        """
        Clean up stale lock files and temp files that might cause issues.
        
        Returns:
            bool: True if cleanup successful
        """
        print("\n" + "="*70)
        print("CLEANING UP STALE FILES")
        print("="*70)
        
        success = True
        home = Path.home()
        
        # Patterns of files to remove
        stale_patterns = [
            '.uv/cache/*/locks/*',
            '/tmp/mpi*',
            '/tmp/ompi*',
            '/tmp/ssh-*',
        ]
        
        for pattern in stale_patterns:
            try:
                if pattern.startswith('/tmp/'):
                    # System temp files
                    result = subprocess.run(
                        ['find', '/tmp', '-name', pattern.split('/')[-1], '-delete'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout:
                        print(f"  ✓ Cleaned {pattern}")
                else:
                    # Home directory patterns
                    full_pattern = home / pattern
                    result = subprocess.run(
                        ['find', str(home), '-path', str(full_pattern), '-delete'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0 and result.stdout:
                        print(f"  ✓ Cleaned {full_pattern}")
                        
            except Exception as e:
                print(f"  ⚠ Warning cleaning {pattern}: {e}")
                
        print("  ✓ Stale file cleanup completed")
        return success


def main():
    """Main entry point for cluster cleanup script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean up orphaned processes across HPC cluster"
    )
    parser.add_argument(
        '--config', '-c',
        help='Path to cluster config YAML file',
        default='cluster_config_actual.yaml'
    )
    parser.add_argument(
        '--processes-only',
        action='store_true',
        help='Only clean processes, skip file cleanup'
    )
    parser.add_argument(
        '--files-only',
        action='store_true',
        help='Only clean files, skip process cleanup'
    )
    
    args = parser.parse_args()
    
    # Load config
    try:
        import yaml
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
            
        master = config['master'][0]['ip'] if isinstance(config['master'], list) else config['master']['ip']
        workers = [w['ip'] for w in config['workers']]
        username = config.get('username', 'muyiwa')
        
    except Exception as e:
        print(f"✗ Error loading config: {e}")
        sys.exit(1)
    
    # Create cleanup instance
    cleanup = ClusterCleanup(master, workers, username)
    
    success = True
    
    # Execute cleanup
    if not args.files_only:
        if not cleanup.cleanup_all_nodes():
            success = False
            
    if not args.processes_only:
        if not cleanup.cleanup_stale_files():
            success = False
    
    # Summary
    print("\n" + "="*70)
    if success:
        print("✓ CLUSTER CLEANUP COMPLETED SUCCESSFULLY")
    else:
        print("⚠ CLUSTER CLEANUP COMPLETED WITH WARNINGS")
    print("="*70 + "\n")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
