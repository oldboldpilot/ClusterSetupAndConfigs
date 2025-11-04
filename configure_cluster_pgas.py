#!/usr/bin/env python3
"""
Helper script to configure PGAS cluster settings after installation
Runs the new configuration methods added to cluster_setup.py
"""

import sys
import getpass
from pathlib import Path

# Add current directory to path to import cluster_setup
sys.path.insert(0, str(Path(__file__).parent))

from cluster_setup import ClusterSetup

def main():
    # Cluster configuration (from conversation history)
    master_ip = "192.168.1.147"  # WSL2, 32 threads
    worker_ips = [
        "192.168.1.139",  # Ubuntu, 16 threads
        "192.168.1.96",   # Ubuntu, 16 threads
        "192.168.1.136",  # Red Hat, 88 threads (build node)
    ]
    username = "muyiwa"
    
    print("=" * 70)
    print("PGAS Cluster Configuration Script")
    print("=" * 70)
    print(f"Master: {master_ip}")
    print(f"Workers: {', '.join(worker_ips)}")
    print(f"Username: {username}")
    print("=" * 70)
    
    # Get password
    password = getpass.getpass("Enter password for cluster nodes: ")
    
    # Create cluster setup instance
    setup = ClusterSetup(master_ip, worker_ips, username, password)
    
    print("\n" + "=" * 70)
    print("Starting PGAS Cluster Configuration")
    print("=" * 70)
    
    try:
        # 1. Configure passwordless sudo
        print("\n[1/5] Configuring passwordless sudo...")
        setup.configure_passwordless_sudo_cluster()
        
        # 2. Distribute system symlinks
        print("\n[2/5] Distributing system symlinks...")
        setup.distribute_system_symlinks_cluster()
        
        # 3. Test multi-node UPC++
        print("\n[3/5] Testing multi-node UPC++...")
        setup.test_multinode_upcxx()
        
        # 4. Install OpenSHMEM
        print("\n[4/5] Installing OpenSHMEM...")
        setup.install_openshmem_cluster()
        
        # 5. Create benchmark suite
        print("\n[5/5] Creating PGAS benchmark suite...")
        setup.create_pgas_benchmark_suite()
        
        print("\n" + "=" * 70)
        print("PGAS CLUSTER CONFIGURATION COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Test UPC++ across cluster:")
        print("   cd ~/cluster_build_sources/upcxx_tests")
        print("   upcxx-run -n 16 ./hello_udp")
        print()
        print("2. Run benchmarks:")
        print("   cd ~/cluster_build_sources/pgas_benchmarks")
        print("   ./run_benchmarks.sh")
        print()
        print("3. Test OpenSHMEM:")
        print("   oshcc -o test test.c")
        print("   oshrun -np 4 ./test")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
