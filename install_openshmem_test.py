#!/usr/bin/env python3
"""Quick test to install OpenSHMEM"""

from cluster_modules.openshmem_manager import OpenSHMEMManager
import yaml

# Load config
with open('cluster_config_actual.yaml', 'r') as f:
    config = yaml.safe_load(f)

master = config['master']['ip']
workers = [w['ip'] for w in config['workers']]
username = config.get('username', 'muyiwa')

print(f"Installing OpenSHMEM on cluster:")
print(f"Master: {master}")
print(f"Workers: {workers}")
print()

# Create manager
mgr = OpenSHMEMManager(
    username=username,
    password='',  # Using SSH keys
    master_ip=master,
    worker_ips=workers
)

# Download
if not mgr.download_openshmem():
    print("Failed to download")
    exit(1)

# Extract
if not mgr.extract_openshmem():
    print("Failed to extract")
    exit(1)

# Configure
if not mgr.configure_openshmem():
    print("Failed to configure")
    exit(1)

# Build
if not mgr.build_openshmem(num_jobs=8):
    print("Failed to build")
    exit(1)

# Install
if not mgr.install_openshmem():
    print("Failed to install")
    exit(1)

# Create symlinks
mgr.create_openshmem_symlinks()

print("\n✓ OpenSHMEM installation completed!")
print("\nVerifying installation...")
import subprocess
result = subprocess.run(['which', 'oshcc'], capture_output=True, text=True)
if result.returncode == 0:
    print(f"✓ oshcc found at: {result.stdout.strip()}")
else:
    print("✗ oshcc not found in PATH")
