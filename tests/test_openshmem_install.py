#!/usr/bin/env python3
"""
Integration test for OpenSHMEM installation on cluster.

This test verifies the complete OpenSHMEM installation workflow:
- Download
- Extract
- Configure
- Build
- Install
- Symlink creation
- Binary verification

Usage:
    python tests/test_openshmem_install.py
    
    # Or with custom config
    python tests/test_openshmem_install.py --config path/to/config.yaml
"""

import sys
import yaml
import argparse
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cluster_modules.openshmem_manager import OpenSHMEMManager


def load_cluster_config(config_path: str = 'cluster_config_actual.yaml') -> dict:
    """Load cluster configuration from YAML file."""
    config_file = Path(__file__).parent.parent / config_path
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def verify_openshmem_installation() -> bool:
    """Verify OpenSHMEM binaries are accessible."""
    print("\nVerifying OpenSHMEM installation...")
    
    binaries = ['oshcc', 'oshc++', 'oshfort', 'oshrun']
    all_found = True
    
    for binary in binaries:
        result = subprocess.run(
            ['which', binary],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {binary:10} found at: {result.stdout.strip()}")
        else:
            print(f"✗ {binary:10} not found in PATH")
            all_found = False
    
    return all_found


def test_openshmem_installation(config_path: str = 'cluster_config_actual.yaml') -> bool:
    """
    Run complete OpenSHMEM installation test.
    
    Args:
        config_path: Path to cluster configuration YAML
        
    Returns:
        True if all steps succeed, False otherwise
    """
    print("=" * 70)
    print("OpenSHMEM Installation Integration Test")
    print("=" * 70)
    
    # Load configuration
    config = load_cluster_config(config_path)
    master = config['master']['ip']
    workers = [w['ip'] for w in config['workers']]
    username = config.get('username', 'muyiwa')
    
    print(f"\nCluster Configuration:")
    print(f"  Master: {master}")
    print(f"  Workers: {', '.join(workers)}")
    print(f"  Username: {username}")
    print()
    
    # Create manager
    mgr = OpenSHMEMManager(
        username=username,
        password='',  # Using SSH keys
        master_ip=master,
        worker_ips=workers
    )
    
    # Step 1: Download
    print("\n[1/6] Downloading OpenSHMEM...")
    if not mgr.download_openshmem():
        print("✗ Failed to download")
        return False
    print("✓ Download successful")
    
    # Step 2: Extract
    print("\n[2/6] Extracting OpenSHMEM...")
    if not mgr.extract_openshmem():
        print("✗ Failed to extract")
        return False
    print("✓ Extract successful")
    
    # Step 3: Configure
    print("\n[3/6] Configuring OpenSHMEM...")
    if not mgr.configure_openshmem():
        print("✗ Failed to configure")
        return False
    print("✓ Configure successful")
    
    # Step 4: Build
    print("\n[4/6] Building OpenSHMEM (this may take several minutes)...")
    if not mgr.build_openshmem(num_jobs=8):
        print("✗ Failed to build")
        return False
    print("✓ Build successful")
    
    # Step 5: Install
    print("\n[5/6] Installing OpenSHMEM...")
    if not mgr.install_openshmem():
        print("✗ Failed to install")
        return False
    print("✓ Install successful")
    
    # Step 6: Create symlinks
    print("\n[6/6] Creating OpenSHMEM wrapper symlinks...")
    if mgr.create_wrapper_symlinks():
        print("✓ Symlinks created")
    else:
        print("⚠ Symlinks creation had issues (may be non-critical)")
    
    # Verify installation
    if verify_openshmem_installation():
        print("\n" + "=" * 70)
        print("✓ OpenSHMEM installation test PASSED!")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("✗ OpenSHMEM installation test FAILED!")
        print("  Some binaries not found in PATH")
        print("=" * 70)
        return False


def main():
    """Main entry point for OpenSHMEM installation test."""
    parser = argparse.ArgumentParser(
        description='Test OpenSHMEM installation on cluster'
    )
    parser.add_argument(
        '--config',
        default='cluster_config_actual.yaml',
        help='Path to cluster configuration file (default: cluster_config_actual.yaml)'
    )
    
    args = parser.parse_args()
    
    try:
        success = test_openshmem_installation(args.config)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
