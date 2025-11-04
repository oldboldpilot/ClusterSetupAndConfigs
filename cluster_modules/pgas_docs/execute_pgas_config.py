#!/usr/bin/env python3
"""
Execute remaining PGAS cluster configuration tasks

Completes:
1. Passwordless sudo configuration across cluster
2. System symlinks distribution (binutils, Python, UPC++)
3. Multi-node UPC++ testing
4. OpenSHMEM installation and distribution
5. PGAS benchmark suite creation and execution

Usage:
    python3 execute_pgas_config.py
    
The script will prompt for the cluster password.
"""

import sys
import os
import getpass
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("=" * 80)
    print("PGAS CLUSTER CONFIGURATION EXECUTION")
    print("=" * 80)
    
    # Import cluster_setup
    try:
        from cluster_setup import ClusterSetup
    except ImportError as e:
        print(f"Error importing cluster_setup: {e}")
        sys.exit(1)
    
    # Cluster configuration (from your actual cluster)
    master_ip = "192.168.1.147"  # WSL2, 32 threads
    worker_ips = [
        "192.168.1.139",  # Ubuntu, 16 threads
        "192.168.1.96",   # Ubuntu, 16 threads
        "192.168.1.136",  # Red Hat, 88 threads (build node/current)
    ]
    username = "muyiwa"
    
    print(f"\nCluster Configuration:")
    print(f"  Master: {master_ip}")
    print(f"  Workers: {', '.join(worker_ips)}")
    print(f"  Username: {username}")
    print()
    
    # Get password
    password = getpass.getpass("Enter cluster password: ")
    
    if not password:
        print("Error: Password is required")
        sys.exit(1)
    
    # Create cluster instance
    print("\nInitializing cluster setup...")
    cluster = ClusterSetup(master_ip, worker_ips, username, password)
    
    print(f"Current node is: {'MASTER' if cluster.is_master else 'WORKER'}")
    print(f"OS type: {cluster.os_type}")
    print()
    
    # Execute configuration tasks
    tasks = [
        ("Configure passwordless sudo on all nodes", 
         cluster.configure_passwordless_sudo_cluster),
        ("Distribute system symlinks to all nodes", 
         cluster.distribute_system_symlinks_cluster),
        ("Test multi-node UPC++ execution", 
         cluster.test_multinode_upcxx),
        ("Install OpenSHMEM cluster-wide", 
         cluster.install_openshmem_cluster),
        ("Create PGAS benchmark suite", 
         cluster.create_pgas_benchmark_suite),
    ]
    
    completed = []
    failed = []
    
    for i, (task_name, task_func) in enumerate(tasks, 1):
        print("\n" + "=" * 80)
        print(f"[{i}/{len(tasks)}] {task_name}")
        print("=" * 80)
        
        try:
            task_func()
            completed.append(task_name)
            print(f"\n✓ Task completed: {task_name}")
        except Exception as e:
            failed.append((task_name, str(e)))
            print(f"\n✗ Task failed: {task_name}")
            print(f"   Error: {e}")
            
            # Ask if we should continue
            response = input("\nContinue with remaining tasks? (y/N): ")
            if response.lower() != 'y':
                break
    
    # Summary
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Completed: {len(completed)}/{len(tasks)} tasks")
    
    if completed:
        print("\n✓ Successful tasks:")
        for task in completed:
            print(f"  - {task}")
    
    if failed:
        print("\n✗ Failed tasks:")
        for task, error in failed:
            print(f"  - {task}")
            print(f"    Error: {error}")
    
    print("\n" + "=" * 80)
    
    if len(completed) == len(tasks):
        print("ALL TASKS COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Test UPC++ cluster execution:")
        print("   cd ~/cluster_build_sources/upcxx_tests")
        print("   GASNET_SSH_SERVERS='192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136' \\")
        print("     upcxx-run -n 16 ./hello_udp")
        print()
        print("2. Run benchmarks:")
        print("   cd ~/cluster_build_sources/pgas_benchmarks")
        print("   ./run_benchmarks.sh")
        print()
        print("3. Commit changes:")
        print("   cd /home/muyiwa/Development/ClusterSetupAndConfigs")
        print("   git add -A && git commit -m 'Complete PGAS cluster configuration' && git push")
        print("=" * 80)
        return 0
    else:
        print("SOME TASKS FAILED - Review errors above")
        print("=" * 80)
        return 1

if __name__ == '__main__':
    sys.exit(main())
