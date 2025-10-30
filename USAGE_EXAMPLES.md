# Usage Examples for Cluster Setup Script

## Basic Setup

### Example 1: Simple 3-Node Cluster

```bash
# On all nodes (master and workers), run:
python cluster_setup.py --master 192.168.1.10 --workers 192.168.1.11 192.168.1.12
```

### Example 2: Larger Cluster with 5 Workers

```bash
python cluster_setup.py \
  --master 10.0.0.10 \
  --workers 10.0.0.11 10.0.0.12 10.0.0.13 10.0.0.14 10.0.0.15
```

### Example 3: Local Testing with Localhost

```bash
# For single-machine testing
python cluster_setup.py --master localhost --workers 127.0.0.2 127.0.0.3
```

### Example 4: Custom Username

```bash
python cluster_setup.py \
  --master 192.168.1.10 \
  --workers 192.168.1.11 192.168.1.12 \
  --username admin
```

## Step-by-Step Workflow

### 1. Prepare Your Cluster Nodes

Ensure all nodes have:
- Ubuntu Linux or WSL with Ubuntu
- Network connectivity
- Same username on all nodes
- Sudo access

### 2. Run Setup on Master Node

```bash
# SSH into master node
ssh user@192.168.1.10

# Clone the repository
git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
cd ClusterSetupAndConfigs

# Run the setup script
python cluster_setup.py --master 192.168.1.10 --workers 192.168.1.11 192.168.1.12
```

The script will:
- Install Homebrew
- Install and configure SSH
- Generate SSH keys
- Configure /etc/hosts
- Install Slurm and OpenMPI
- Start Slurm controller (slurmctld) on master
- Start Slurm daemon (slurmd)
- Create OpenMPI configuration

### 3. Copy SSH Key to Workers

After setup on master, you'll see output like:

```
Public key content:
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQ... user@master

NOTE: You need to manually copy this public key to all other nodes
On each node, add this key to /home/user/.ssh/authorized_keys
```

Copy the public key and add it to each worker's `~/.ssh/authorized_keys` file.

### 4. Run Setup on Each Worker Node

```bash
# SSH into worker1
ssh user@192.168.1.11

# Clone the repository
git clone https://github.com/oldboldpilot/ClusterSetupAndConfigs.git
cd ClusterSetupAndConfigs

# Run the same setup command
python cluster_setup.py --master 192.168.1.10 --workers 192.168.1.11 192.168.1.12

# Repeat for worker2, etc.
```

### 5. Verify Setup

On the master node:

```bash
# Check Slurm cluster status
sinfo

# Should show output like:
# PARTITION AVAIL  TIMELIMIT  NODES  STATE NODELIST
# all*      up     infinite       3   idle master,worker1,worker2

# Check detailed node information
scontrol show nodes

# Test SSH connectivity
ssh worker1 hostname
ssh worker2 hostname

# Test MPI
mpirun -np 4 -hostfile ~/.openmpi/hostfile hostname
```

### 6. Submit Test Jobs

#### Slurm Job Examples

```bash
# Simple command
srun -N 2 hostname

# Interactive job
salloc -N 2

# Batch job
cat > test_job.sh << 'EOF'
#!/bin/bash
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=2
#SBATCH --time=00:10:00
#SBATCH --job-name=test_job

echo "Running on nodes:"
srun hostname
EOF

sbatch test_job.sh
```

#### OpenMPI Job Examples

```bash
# Simple hostname test
mpirun -np 4 -hostfile ~/.openmpi/hostfile hostname

# MPI Hello World (if you have one compiled)
mpirun -np 8 -hostfile ~/.openmpi/hostfile ./mpi_hello_world

# Using specific hosts
mpirun -np 4 -host master,worker1,worker2 hostname
```

## Advanced Configurations

### Custom Slurm Configuration

After initial setup, you can customize `/etc/slurm/slurm.conf`:

```bash
sudo nano /etc/slurm/slurm.conf

# Make your changes, then restart Slurm
sudo killall slurmctld slurmd
sudo slurmctld  # On master
sudo slurmd     # On all nodes
```

### Custom OpenMPI Hostfile

Edit `~/.openmpi/hostfile` to adjust slots per node:

```bash
192.168.1.10 slots=8 max_slots=16
192.168.1.11 slots=8 max_slots=16
192.168.1.12 slots=8 max_slots=16
```

### Adding New Nodes

To add a new worker node:

1. Update `/etc/hosts` on all existing nodes
2. Run the setup script on the new node
3. Update `/etc/slurm/slurm.conf` on all nodes
4. Update `~/.openmpi/hostfile` on all nodes
5. Restart Slurm services

```bash
# On all nodes, add to /etc/hosts:
echo "192.168.1.13    worker3 worker-node3" | sudo tee -a /etc/hosts

# On new node:
python cluster_setup.py --master 192.168.1.10 --workers 192.168.1.11 192.168.1.12 192.168.1.13

# On master, update slurm.conf to include worker3, then:
sudo scontrol reconfigure
```

## Troubleshooting Common Issues

### Issue: Slurm nodes show as "down"

```bash
# Check Slurm daemon is running
ps aux | grep slurmd

# Check logs
tail -f /var/log/slurm/slurmd.log

# Restart daemon
sudo killall slurmd
sudo slurmd
```

### Issue: SSH asks for password

```bash
# Verify key is in authorized_keys
cat ~/.ssh/authorized_keys | grep $(cat ~/.ssh/id_rsa.pub | cut -d' ' -f2)

# Check permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### Issue: MPI jobs hang

```bash
# Check network connectivity
ping worker1

# Test SSH without password
ssh worker1 'echo test'

# Try with verbose output
mpirun --mca btl_base_verbose 30 -np 2 hostname
```

### Issue: Homebrew installation fails

```bash
# Install from apt instead
sudo apt-get update
sudo apt-get install -y slurm-wlm openmpi-bin

# The script will fall back to apt automatically
```

## Performance Tuning

### For CPU-bound workloads:

1. Adjust slots in OpenMPI hostfile to match CPU cores
2. Configure Slurm with appropriate CPUs per node
3. Use `--cpus-per-task` in Slurm submissions

### For memory-bound workloads:

1. Set appropriate memory limits in Slurm
2. Use `--mem` or `--mem-per-cpu` in job submissions

### For I/O-intensive workloads:

1. Consider NFS or shared filesystem
2. Use local scratch directories
3. Optimize data locality

## Security Considerations

1. **Firewall**: Ensure required ports are open:
   - SSH: 22
   - Slurm: 6817 (slurmctld), 6818 (slurmd)
   - MPI: Various (typically high ports)

2. **SSH Keys**: Protect private keys with passphrases in production

3. **User Isolation**: Configure proper user permissions and cgroups

4. **Network**: Use private network for cluster communication

## References

- [Slurm Documentation](https://slurm.schedmd.com/)
- [OpenMPI Documentation](https://www.open-mpi.org/doc/)
- [Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux)
