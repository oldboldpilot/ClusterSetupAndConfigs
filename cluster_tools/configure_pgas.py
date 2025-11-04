#!/usr/bin/env python3
"""
PGAS Cluster Configuration Tool

Helper script to configure PGAS cluster settings after installation.
Runs configuration methods for passwordless sudo, system symlinks, 
multi-node testing, OpenSHMEM installation, and benchmark suite creation.

Usage:
    # Using uv (recommended)
    uv run python cluster_tools/configure_pgas.py
    
    # Direct python
    python3 cluster_tools/configure_pgas.py
    
    # With environment activation
    source .venv/bin/activate
    python cluster_tools/configure_pgas.py
"""

import sys
import getpass
from pathlib import Path

# Add parent directory to path to import cluster_setup
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from cluster_setup import ClusterSetup


def main():
    """Main entry point for PGAS cluster configuration"""
    
    # Cluster configuration (4-node HPC cluster)
    master_ip = "192.168.1.147"  # WSL2, 32 threads
    worker_ips = [
        "192.168.1.139",  # Ubuntu, 16 threads
        "192.168.1.96",   # Ubuntu, 16 threads
        "192.168.1.136",  # Red Hat, 88 threads (build node)
    ]
    username = "muyiwa"
    
    print("=" * 70)
    print("PGAS CLUSTER CONFIGURATION TOOL")
    print("=" * 70)
    print(f"Master Node:  {master_ip} (WSL2)")
    print(f"Worker Nodes: {len(worker_ips)} nodes")
    for idx, ip in enumerate(worker_ips, 1):
        print(f"  Worker {idx}:   {ip}")
    print(f"Username:     {username}")
    print("=" * 70)
    
    # Get password from user (never hardcoded)
    password = getpass.getpass("\nEnter password for cluster nodes: ")
    
    if not password:
        print("ERROR: Password is required for cluster operations")
        sys.exit(1)
    
    # Create cluster setup instance
    setup = ClusterSetup(master_ip, worker_ips, username, password)
    
    print("\n" + "=" * 70)
    print("STARTING PGAS CLUSTER CONFIGURATION")
    print("=" * 70)
    print("\nThis will perform the following operations:")
    print("  1. Configure passwordless sudo on all nodes")
    print("  2. Distribute system symlinks (binutils, Python, UPC++)")
    print("  3. Test multi-node UPC++ execution")
    print("  4. Install OpenSHMEM 1.5.2 cluster-wide")
    print("  5. Create PGAS vs MPI benchmark suite")
    print("\n" + "=" * 70)
    
    confirm = input("\nProceed with configuration? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("Configuration cancelled by user")
        sys.exit(0)
    
    try:
        # Task 1: Configure passwordless sudo
        print("\n" + "=" * 70)
        print("[1/5] CONFIGURING PASSWORDLESS SUDO")
        print("=" * 70)
        setup.configure_passwordless_sudo_cluster()
        print("✓ Passwordless sudo configuration complete")
        
        # Task 2: Distribute system symlinks
        print("\n" + "=" * 70)
        print("[2/5] DISTRIBUTING SYSTEM SYMLINKS")
        print("=" * 70)
        setup.distribute_system_symlinks_cluster()
        print("✓ System symlinks distributed to all nodes")
        
        # Task 3: Test multi-node UPC++
        print("\n" + "=" * 70)
        print("[3/5] TESTING MULTI-NODE UPC++")
        print("=" * 70)
        setup.test_multinode_upcxx()
        print("✓ Multi-node UPC++ testing complete")
        
        # Task 4: Install OpenSHMEM
        print("\n" + "=" * 70)
        print("[4/5] INSTALLING OPENSHMEM")
        print("=" * 70)
        setup.install_openshmem_cluster()
        print("✓ OpenSHMEM installation complete")
        
        # Task 5: Create benchmark suite
        print("\n" + "=" * 70)
        print("[5/5] CREATING PGAS BENCHMARK SUITE")
        print("=" * 70)
        setup.create_pgas_benchmark_suite()
        print("✓ Benchmark suite created")
        
        # Success summary
        print("\n" + "=" * 70)
        print("✓✓✓ PGAS CLUSTER CONFIGURATION COMPLETED SUCCESSFULLY ✓✓✓")
        print("=" * 70)
        
        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        
        print("\n1. Test UPC++ across cluster:")
        print("   cd ~/cluster_build_sources/upcxx_tests")
        print("   export GASNET_SSH_SERVERS='192.168.1.147,192.168.1.139,192.168.1.96,192.168.1.136'")
        print("   upcxx-run -n 16 ./hello_udp")
        
        print("\n2. Run PGAS vs MPI benchmarks:")
        print("   cd ~/cluster_build_sources/pgas_benchmarks")
        print("   ./run_benchmarks.sh")
        
        print("\n3. Test OpenSHMEM:")
        print("   oshcc -o test test.c")
        print("   oshrun -np 4 ./test")
        
        print("\n4. View test results:")
        print("   ls -lh ~/cluster_build_sources/upcxx_tests/")
        print("   ls -lh ~/cluster_build_sources/pgas_benchmarks/results/")
        
        print("\n" + "=" * 70)
        
    except KeyboardInterrupt:
        print("\n\nConfiguration interrupted by user")
        sys.exit(130)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("ERROR DURING CONFIGURATION")
        print("=" * 70)
        print(f"\n{type(e).__name__}: {e}")
        
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        
        print("\n" + "=" * 70)
        print("Configuration failed. Check the error above.")
        print("=" * 70)
        sys.exit(1)


if __name__ == '__main__':
    main()
