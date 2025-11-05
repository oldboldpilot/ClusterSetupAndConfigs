# Slurm Job Submission Guide

**Author:** Olumuyiwa Oluwasanmi  
**Date:** November 5, 2025  
**Version:** 1.0.0

## Overview

This guide covers the comprehensive Slurm job submission system for submitting parallel programming jobs across the HPC cluster. The system supports 5 frameworks: MPI, OpenMP, Hybrid MPI+OpenMP, UPC++, and OpenSHMEM.

## Architecture

### Modular Components

```
cluster_modules/
├── slurm_job_manager.py         # Job generation and submission
├── slurm_setup_helper.py         # Munge and Slurm configuration
└── templates/
    └── slurm_jobs/               # Jinja2 job templates
        ├── mpi_job.sh.j2
        ├── openmp_job.sh.j2
        ├── hybrid_job.sh.j2
        ├── upcxx_job.sh.j2
        └── openshmem_job.sh.j2
```

### Key Features

- **Template-based**: All job scripts generated from Jinja2 templates
- **Resource-aware**: Automatically allocates nodes/cores based on cluster configuration
- **Multi-framework**: Supports MPI, OpenMP, UPC++, OpenSHMEM, and hybrid jobs
- **Job management**: Submit, monitor, cancel, and retrieve job output
- **Munge authentication**: Automatic setup and distribution across cluster

## Setup

### Prerequisites

- Slurm installed on all nodes (`slurm-wlm` or `slurm`)
- Munge installed on all nodes (`munge`, `munge-libs`)
- Cluster configuration file (`cluster_config_actual.yaml`)
- Passwordless SSH between nodes (recommended)

### Initial Setup

```bash
cd ~/cluster_build_sources/config/ClusterSetupAndConfigs
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup

# Setup Munge and Slurm
uv run python setup_slurm.py --config cluster_config_actual.yaml --password

# Verify setup
sinfo
munge -n | unmunge
```

### Setup Steps Explained

The `setup_slurm.py` script performs 4 steps:

1. **Munge Authentication Setup**
   - Installs Munge if not present
   - Generates `/etc/munge/munge.key` (1024-byte random key)
   - Sets proper permissions (munge:munge, 0400)
   - Starts `munge` service

2. **Munge Key Distribution** (with --password)
   - Copies Munge key to all worker nodes
   - Configures permissions on each node
   - Restarts Munge service on workers

3. **Slurm Partition Configuration**
   - Verifies or creates default partition
   - Restarts `slurmctld` to apply changes

4. **Verification**
   - Tests Munge: `munge -n | unmunge`
   - Tests Slurm: `sinfo`

## Usage

### Python API

```python
from pathlib import Path
from cluster_modules.slurm_job_manager import SlurmJobManager

# Initialize with cluster configuration
config_path = Path("cluster_config_actual.yaml")
job_mgr = SlurmJobManager(config_path=config_path)

# Generate MPI job script
job_script = job_mgr.generate_mpi_job(
    job_name="my_mpi_job",
    executable="/path/to/mpi_executable",
    num_tasks=16,                    # 16 MPI processes
    args="--input data.txt",
    time_limit="02:00:00",           # 2 hours
    partition="all"
)

# Submit job
job_id = job_mgr.submit_job(job_script)
print(f"Job submitted: {job_id}")

# Monitor job
success, state = job_mgr.wait_for_job(job_id, timeout=3600)
print(f"Job completed with state: {state}")

# Retrieve output
stdout, stderr = job_mgr.get_job_output(job_id, "my_mpi_job")
print(stdout)
```

### MPI Jobs

```python
# Generate MPI job
job_script = job_mgr.generate_mpi_job(
    job_name="mpi_benchmark",
    executable="~/cluster_build_sources/benchmarks/bin/mpi_latency",
    num_tasks=8,                     # 8 MPI ranks
    time_limit="00:30:00"
)

# Generated script uses:
# - srun --mpi=pmix for process launching
# - OpenMPI environment variables
# - Network interface configuration
job_id = job_mgr.submit_job(job_script)
```

### OpenMP Jobs

```python
# Generate OpenMP job (single node, multiple threads)
job_script = job_mgr.generate_openmp_job(
    job_name="openmp_compute",
    executable="~/cluster_build_sources/benchmarks/bin/openmp_parallel",
    num_threads=32,                  # 32 OpenMP threads
    time_limit="01:00:00"
)

# Generated script sets:
# - OMP_NUM_THREADS=32
# - OMP_PROC_BIND=true
# - OMP_PLACES=cores
job_id = job_mgr.submit_job(job_script)
```

### Hybrid MPI+OpenMP Jobs

```python
# Generate hybrid job (MPI processes × OpenMP threads)
job_script = job_mgr.generate_hybrid_job(
    job_name="hybrid_simulation",
    executable="./hybrid_app",
    num_tasks=4,                     # 4 MPI ranks
    threads_per_task=8,              # 8 OpenMP threads per rank
    time_limit="03:00:00"
)

# Total parallelism: 4 MPI × 8 OpenMP = 32 threads
job_id = job_mgr.submit_job(job_script)
```

### UPC++ Jobs

```python
# Generate UPC++ job (PGAS model)
job_script = job_mgr.generate_upcxx_job(
    job_name="upcxx_latency",
    executable="~/cluster_build_sources/benchmarks/bin/upcxx_latency",
    num_processes=4,                 # 4 UPC++ localities
    network="mpi",                   # GASNet conduit: mpi, smp, udp
    time_limit="00:30:00"
)

# Uses upcxx-run launcher with GASNet-EX
job_id = job_mgr.submit_job(job_script)
```

### OpenSHMEM Jobs

```python
# Generate OpenSHMEM job (symmetric memory model)
job_script = job_mgr.generate_openshmem_job(
    job_name="shmem_test",
    executable="~/cluster_build_sources/benchmarks/bin/openshmem_latency",
    num_pes=8,                       # 8 Processing Elements
    time_limit="00:15:00"
)

job_id = job_mgr.submit_job(job_script)
```

## Job Management

### List Active Jobs

```python
jobs = job_mgr.list_jobs()
for job in jobs:
    print(f"{job['job_id']}: {job['name']} - {job['state']}")
```

Or use command line:
```bash
squeue                              # All jobs
squeue -u $USER                     # Your jobs
squeue -p all                       # Jobs in 'all' partition
```

### Check Job Status

```python
status = job_mgr.get_job_status(job_id)
print(f"State: {status.get('JobState')}")
print(f"Runtime: {status.get('RunTime')}")
```

Or use command line:
```bash
scontrol show job <job_id>
```

### Wait for Job Completion

```python
# Block until job completes (with timeout)
success, final_state = job_mgr.wait_for_job(
    job_id,
    poll_interval=5,                 # Check every 5 seconds
    timeout=3600                     # Max 1 hour
)

if success:
    print("Job completed successfully")
else:
    print(f"Job ended with state: {final_state}")
```

### Cancel Job

```python
job_mgr.cancel_job(job_id)
```

Or use command line:
```bash
scancel <job_id>
scancel -u $USER                    # Cancel all your jobs
```

### Retrieve Job Output

```python
stdout, stderr = job_mgr.get_job_output(job_id, "job_name")

if stdout:
    print("Standard Output:")
    print(stdout)

if stderr:
    print("Standard Error:")
    print(stderr)
```

Output files are saved as:
- `~/cluster_build_sources/slurm_results/job_name_<jobid>.out`
- `~/cluster_build_sources/slurm_results/job_name_<jobid>.err`

## Resource Allocation

### Automatic Node Selection

The `SlurmJobManager` automatically selects nodes based on:

```python
# For MPI/UPC++/OpenSHMEM jobs:
num_nodes = min(total_available_nodes, requested_tasks)

# Example: 8 tasks on 5-node cluster → uses 4 nodes
```

### Thread Allocation

Thread counts are read from `cluster_config_actual.yaml`:

```yaml
threads:
  192.168.1.136: 88    # 44 cores × 2 threads
  192.168.1.139: 16    # 8 cores × 2 threads
  192.168.1.96: 16
  192.168.1.48: 16
  192.168.1.147: 32
```

Total: 168 cores available for parallel execution

### Partition Selection

Available partitions:
- `all` (default): All nodes, unlimited time
- `debug`: Master node only, 1-hour limit
- `compute`: All nodes, 24-hour limit

Specify partition in job generation:
```python
job_script = job_mgr.generate_mpi_job(
    ...,
    partition="compute"              # Use compute partition
)
```

## Testing

### Run Comprehensive Tests

```bash
cd ~/cluster_build_sources/config/ClusterSetupAndConfigs
export UV_PROJECT_ENVIRONMENT=$HOME/.venv/cluster-setup
uv run python test_slurm_jobs.py
```

The test suite:
1. Checks Slurm operational status
2. Tests MPI job submission
3. Tests OpenMP job submission
4. Tests Hybrid job submission
5. Tests UPC++ job submission
6. Tests OpenSHMEM job submission
7. Lists active jobs
8. Reports test summary

### Manual Testing

```bash
# 1. Generate simple test job
cat > /tmp/test_job.sh << 'EOF'
#!/bin/bash
#SBATCH --job-name=test
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=00:01:00
#SBATCH --partition=debug
#SBATCH --output=/tmp/test_%j.out

echo "Test job running on $(hostname)"
echo "Cores available: $(nproc)"
echo "Date: $(date)"
EOF

# 2. Submit job
sbatch /tmp/test_job.sh

# 3. Monitor
squeue

# 4. View output
cat /tmp/test_*.out
```

## Troubleshooting

### Munge Not Working

**Symptom**: `sinfo` fails with "Munge encode failed"

**Solution**:
```bash
# Check Munge service
sudo systemctl status munge

# Restart Munge
sudo systemctl restart munge

# Test Munge
munge -n | unmunge

# If fails, check permissions
ls -la /etc/munge/munge.key
# Should be: -r-------- 1 munge munge

# Fix permissions
sudo chown munge:munge /etc/munge/munge.key
sudo chmod 400 /etc/munge/munge.key
```

### Nodes Down/Unknown

**Symptom**: `sinfo` shows nodes as DOWN, DRAINED, or UNKNOWN

**Solution**:
```bash
# Check slurmd on worker nodes
ssh worker1 'sudo systemctl status slurmd'

# Restart slurmd on all workers
pdsh -w 192.168.1.[139,96,48,147] 'sudo systemctl restart slurmd'

# Update node state in Slurm
sudo scontrol update nodename=worker1 state=idle
```

### Job Submission Fails

**Symptom**: `sbatch: error: invalid partition specified`

**Solution**:
```bash
# Check available partitions
scontrol show partition

# Use correct partition name
sbatch --partition=all job_script.sh
```

### Job Pending Forever

**Symptom**: Job stays in PD (Pending) state

**Reason**: Check with `squeue -l`:
- Nodes DOWN/DRAINED
- Resource request exceeds available
- Priority queue

**Solution**:
```bash
# Check node states
sinfo -N -l

# Check job reason
squeue -j <job_id> -o "%.18i %.9P %.8T %.10M %.10l %.6D %.20R"

# Cancel and resubmit with corrected resources
scancel <job_id>
```

### No Job Output Files

**Symptom**: Expected output files don't exist

**Solution**:
- Check job completed: `scontrol show job <job_id>`
- Verify output path in job script
- Check directory permissions
- Look in job script's `#SBATCH --output` location

## Advanced Usage

### Job Arrays

```python
# Not directly supported in SlurmJobManager yet
# Use custom SBATCH script:
"""
#!/bin/bash
#SBATCH --array=1-10
#SBATCH --job-name=array_job

echo "Task ID: $SLURM_ARRAY_TASK_ID"
./process_task.sh $SLURM_ARRAY_TASK_ID
"""
```

### Job Dependencies

```bash
# Submit job1
job1=$(sbatch job1.sh | awk '{print $4}')

# Submit job2 that depends on job1
sbatch --dependency=afterok:$job1 job2.sh
```

### Email Notifications

Add to job script template or manually:
```bash
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=your.email@domain.com
```

### GPU Jobs

For nodes with GPU support (as configured):
```bash
#SBATCH --gres=gpu:1
#SBATCH --partition=gpu    # If GPU partition exists
```

## Best Practices

### 1. Resource Estimation

- Start with shorter time limits, increase if needed
- Request only the resources you need
- Test on small scale before large runs

### 2. Output Management

- Use unique job names: `job_name_$(date +%Y%m%d_%H%M%S)`
- Organize output: `/path/to/results/<project>/<date>/`
- Clean up old output files regularly

### 3. Job Efficiency

- Use appropriate partition (debug for testing, compute for production)
- Batch multiple small tasks into one job
- Use job arrays for parameter sweeps

### 4. Error Handling

- Always capture stderr: `#SBATCH --error=...`
- Add error checking in job scripts
- Log intermediate results

### 5. Development Workflow

1. Test executable locally
2. Test with simple Slurm job (1 node)
3. Scale to multiple nodes
4. Benchmark and optimize
5. Run production jobs

## Performance Tuning

### MPI Performance

```bash
# In job script, tune OpenMPI parameters:
export OMPI_MCA_btl_tcp_if_include=192.168.1.0/24
export OMPI_MCA_oob_tcp_if_include=192.168.1.0/24
export OMPI_MCA_btl_openib_allow_ib=1  # For InfiniBand
```

### OpenMP Performance

```bash
# Thread affinity for best performance:
export OMP_PROC_BIND=close
export OMP_PLACES=cores

# Or spread threads:
export OMP_PROC_BIND=spread
export OMP_PLACES=sockets
```

### UPC++ Performance

```bash
# For better latency with MPI conduit:
export GASNET_NETWORKDEPTH=24
export GASNET_MAXPIN=0.8           # Pin 80% of memory
```

## Examples

### Example 1: MPI Benchmark Suite

```python
from cluster_modules.slurm_job_manager import SlurmJobManager
from pathlib import Path

job_mgr = SlurmJobManager(config_path=Path("cluster_config_actual.yaml"))

benchmarks = [
    ("mpi_latency", 2),
    ("mpi_bandwidth", 2),
    ("mpi_allreduce", 4),
]

job_ids = []
for bench_name, num_tasks in benchmarks:
    executable = f"~/cluster_build_sources/benchmarks/bin/{bench_name}"
    
    job_script = job_mgr.generate_mpi_job(
        job_name=bench_name,
        executable=executable,
        num_tasks=num_tasks,
        time_limit="00:10:00"
    )
    
    job_id = job_mgr.submit_job(job_script)
    if job_id:
        job_ids.append((bench_name, job_id))

# Wait for all jobs
for name, job_id in job_ids:
    success, state = job_mgr.wait_for_job(job_id, timeout=1200)
    print(f"{name}: {state}")
```

### Example 2: Parameter Sweep

```python
# Test different thread counts for OpenMP
thread_counts = [1, 2, 4, 8, 16, 32]

for threads in thread_counts:
    job_script = job_mgr.generate_openmp_job(
        job_name=f"openmp_sweep_{threads}",
        executable="./openmp_benchmark",
        num_threads=threads,
        time_limit="00:05:00"
    )
    job_mgr.submit_job(job_script)
```

## Files and Directories

```
~/cluster_build_sources/
├── slurm_jobs/                     # Generated job scripts
│   ├── test_mpi_mpi.sh
│   ├── test_openmp_openmp.sh
│   └── ...
└── slurm_results/                  # Job output files
    ├── test_mpi_123.out
    ├── test_mpi_123.err
    └── ...

~/cluster_build_sources/config/ClusterSetupAndConfigs/
├── cluster_modules/
│   ├── slurm_job_manager.py
│   ├── slurm_setup_helper.py
│   └── templates/slurm_jobs/       # Jinja2 templates
├── setup_slurm.py                  # Setup script
└── test_slurm_jobs.py              # Test suite
```

## References

- [Slurm Documentation](https://slurm.schedmd.com/)
- [Munge Documentation](https://github.com/dun/munge/wiki)
- [OpenMPI Documentation](https://www.open-mpi.org/doc/)
- [UPC++ Documentation](https://upcxx.lbl.gov/)
- [OpenSHMEM Specification](http://openshmem.org/)

---

**Document Version:** 1.0.0  
**Last Updated:** November 5, 2025  
**Author:** Olumuyiwa Oluwasanmi
