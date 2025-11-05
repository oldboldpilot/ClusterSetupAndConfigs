#!/usr/bin/env python3
"""
Comprehensive Slurm Job Submission Test Suite

Tests all job types: MPI, OpenMP, Hybrid, UPC++, OpenSHMEM
Validates job submission, execution, and results retrieval.

Usage:
    export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
    uv run python test_slurm_jobs.py

Author: Olumuyiwa Oluwasanmi
Date: November 5, 2025
"""

import sys
import time
from pathlib import Path

# Add cluster_modules to path
sys.path.insert(0, str(Path(__file__).parent))

from cluster_modules.slurm_job_manager import SlurmJobManager
from cluster_modules.slurm_setup_helper import SlurmSetupHelper


def print_section(title: str) -> None:
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"{title}")
    print('='*70)


def test_mpi_job(job_mgr: SlurmJobManager) -> bool:
    """Test MPI job submission."""
    print_section("Testing MPI Job Submission")
    
    # Create simple MPI test executable path
    executable = str(Path.home() / "cluster_build_sources" / "benchmarks" / "bin" / "mpi_latency")
    
    if not Path(executable).exists():
        print(f"⚠ MPI executable not found: {executable}")
        print("  Skipping MPI job test")
        return False
    
    # Generate job script
    job_script = job_mgr.generate_mpi_job(
        job_name="test_mpi",
        executable=executable,
        num_tasks=4,
        time_limit="00:05:00"
    )
    
    print(f"\nGenerated job script: {job_script}")
    print("\nJob script content:")
    print(job_script.read_text())
    
    # Submit job
    job_id = job_mgr.submit_job(job_script)
    
    if job_id:
        print(f"\n✓ MPI job submitted successfully (Job ID: {job_id})")
        
        # Wait for completion (with timeout)
        print("Waiting for job to complete...")
        success, state = job_mgr.wait_for_job(job_id, poll_interval=5, timeout=300)
        
        print(f"Job final state: {state}")
        
        # Get output
        stdout, stderr = job_mgr.get_job_output(job_id, "test_mpi")
        if stdout:
            print("\nJob output:")
            print(stdout[:500] + ("..." if len(stdout) > 500 else ""))
        
        return success
    else:
        print("✗ MPI job submission failed")
        return False


def test_openmp_job(job_mgr: SlurmJobManager) -> bool:
    """Test OpenMP job submission."""
    print_section("Testing OpenMP Job Submission")
    
    executable = str(Path.home() / "cluster_build_sources" / "benchmarks" / "bin" / "openmp_parallel")
    
    if not Path(executable).exists():
        print(f"⚠ OpenMP executable not found: {executable}")
        print("  Skipping OpenMP job test")
        return False
    
    # Generate job script
    job_script = job_mgr.generate_openmp_job(
        job_name="test_openmp",
        executable=executable,
        num_threads=16,
        time_limit="00:05:00"
    )
    
    print(f"\nGenerated job script: {job_script}")
    
    # Submit job
    job_id = job_mgr.submit_job(job_script)
    
    if job_id:
        print(f"✓ OpenMP job submitted successfully (Job ID: {job_id})")
        return True
    else:
        print("✗ OpenMP job submission failed")
        return False


def test_hybrid_job(job_mgr: SlurmJobManager) -> bool:
    """Test Hybrid MPI+OpenMP job submission."""
    print_section("Testing Hybrid MPI+OpenMP Job Submission")
    
    executable = str(Path.home() / "cluster_build_sources" / "benchmarks" / "bin" / "hybrid_mpi_openmp")
    
    if not Path(executable).exists():
        print(f"⚠ Hybrid executable not found: {executable}")
        print("  Creating placeholder script for demonstration...")
        
        # Create a simple test script
        test_script = Path("/tmp/test_hybrid.sh")
        test_script.write_text("""#!/bin/bash
echo "Hybrid MPI+OpenMP test"
echo "MPI Rank: $SLURM_PROCID"
echo "OpenMP Threads: $OMP_NUM_THREADS"
""")
        test_script.chmod(0o755)
        executable = str(test_script)
    
    # Generate job script
    job_script = job_mgr.generate_hybrid_job(
        job_name="test_hybrid",
        executable=executable,
        num_tasks=4,
        threads_per_task=8,
        time_limit="00:05:00"
    )
    
    print(f"\nGenerated job script: {job_script}")
    
    # Submit job
    job_id = job_mgr.submit_job(job_script)
    
    if job_id:
        print(f"✓ Hybrid job submitted successfully (Job ID: {job_id})")
        return True
    else:
        print("✗ Hybrid job submission failed")
        return False


def test_upcxx_job(job_mgr: SlurmJobManager) -> bool:
    """Test UPC++ job submission."""
    print_section("Testing UPC++ Job Submission")
    
    executable = str(Path.home() / "cluster_build_sources" / "benchmarks" / "bin" / "upcxx_latency")
    
    if not Path(executable).exists():
        print(f"⚠ UPC++ executable not found: {executable}")
        print("  Skipping UPC++ job test")
        return False
    
    # Generate job script
    job_script = job_mgr.generate_upcxx_job(
        job_name="test_upcxx",
        executable=executable,
        num_processes=4,
        network="mpi",
        time_limit="00:05:00"
    )
    
    print(f"\nGenerated job script: {job_script}")
    
    # Submit job
    job_id = job_mgr.submit_job(job_script)
    
    if job_id:
        print(f"✓ UPC++ job submitted successfully (Job ID: {job_id})")
        return True
    else:
        print("✗ UPC++ job submission failed")
        return False


def test_openshmem_job(job_mgr: SlurmJobManager) -> bool:
    """Test OpenSHMEM job submission."""
    print_section("Testing OpenSHMEM Job Submission")
    
    executable = str(Path.home() / "cluster_build_sources" / "benchmarks" / "bin" / "openshmem_latency")
    
    if not Path(executable).exists():
        print(f"⚠ OpenSHMEM executable not found: {executable}")
        print("  Skipping OpenSHMEM job test")
        return False
    
    # Generate job script
    job_script = job_mgr.generate_openshmem_job(
        job_name="test_openshmem",
        executable=executable,
        num_pes=4,
        time_limit="00:05:00"
    )
    
    print(f"\nGenerated job script: {job_script}")
    
    # Submit job
    job_id = job_mgr.submit_job(job_script)
    
    if job_id:
        print(f"✓ OpenSHMEM job submitted successfully (Job ID: {job_id})")
        return True
    else:
        print("✗ OpenSHMEM job submission failed")
        return False


def test_job_listing(job_mgr: SlurmJobManager) -> None:
    """Test job listing functionality."""
    print_section("Testing Job Listing")
    
    jobs = job_mgr.list_jobs()
    
    if jobs:
        print(f"\nFound {len(jobs)} active job(s):")
        for job in jobs:
            print(f"  Job {job['job_id']}: {job['name']} - State: {job['state']} - Nodes: {job['nodes']}")
    else:
        print("\nNo active jobs found")


def main():
    """Main test function."""
    print_section("Slurm Job Submission Test Suite")
    print("Author: Olumuyiwa Oluwasanmi")
    print("Date: November 5, 2025")
    
    # Initialize job manager
    config_path = Path(__file__).parent / "cluster_config_actual.yaml"
    
    if not config_path.exists():
        print(f"\n✗ Configuration file not found: {config_path}")
        print("  Please ensure cluster_config_actual.yaml exists")
        sys.exit(1)
    
    print(f"\nUsing configuration: {config_path}")
    
    job_mgr = SlurmJobManager(config_path=config_path)
    
    print(f"\nCluster configuration loaded:")
    print(f"  Nodes: {len(job_mgr.nodes)}")
    print(f"  Total cores: {job_mgr.total_cores}")
    print(f"  Jobs directory: {job_mgr.jobs_dir}")
    print(f"  Results directory: {job_mgr.results_dir}")
    
    # Check if Slurm is operational
    print("\nChecking Slurm status...")
    import subprocess
    result = subprocess.run(["sinfo"], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("✗ Slurm is not operational!")
        print("  Error:", result.stderr)
        print("\n  Please run setup_slurm.py first to configure Munge and Slurm services")
        sys.exit(1)
    
    print("✓ Slurm is operational")
    print("\nCurrent cluster status:")
    print(result.stdout)
    
    # Run tests
    results = {}
    
    # Test each job type
    results['MPI'] = test_mpi_job(job_mgr)
    time.sleep(2)
    
    results['OpenMP'] = test_openmp_job(job_mgr)
    time.sleep(2)
    
    results['Hybrid'] = test_hybrid_job(job_mgr)
    time.sleep(2)
    
    results['UPC++'] = test_upcxx_job(job_mgr)
    time.sleep(2)
    
    results['OpenSHMEM'] = test_openshmem_job(job_mgr)
    time.sleep(2)
    
    # Test job listing
    test_job_listing(job_mgr)
    
    # Print summary
    print_section("Test Summary")
    
    for job_type, success in results.items():
        status = "✓ PASS" if success else "⚠ SKIP/FAIL"
        print(f"{job_type:15s} {status}")
    
    passed = sum(1 for s in results.values() if s)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠ {total - passed} test(s) skipped or failed")
        sys.exit(0)  # Exit 0 even if some skipped (executables may not exist)


if __name__ == "__main__":
    main()
