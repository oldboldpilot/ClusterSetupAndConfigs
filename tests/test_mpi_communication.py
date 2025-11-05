#!/usr/bin/env python3
"""
MPI cluster communication test.

This test verifies MPI functionality across the cluster:
- Process distribution across nodes
- Point-to-point communication
- Collective operations
- Network connectivity

Usage:
    # Run with 4 processes across cluster
    mpirun -np 4 --hostfile ~/cluster_build_sources/benchmarks/hostfile python tests/test_mpi_communication.py
    
    # Run with specific hosts
    mpirun -np 4 --host node1,node2,node3,node4 python tests/test_mpi_communication.py
    
    # Run with map-by-node (one process per node)
    mpirun -np 4 --hostfile hostfile --map-by ppr:1:node python tests/test_mpi_communication.py
    
Note: Requires mpi4py installed in the Python environment
"""

from mpi4py import MPI
import socket
import sys
from datetime import datetime


def print_header(rank: int, message: str):
    """Print formatted header (only from rank 0)."""
    if rank == 0:
        print("\n" + "=" * 70)
        print(message)
        print("=" * 70)


def test_basic_info():
    """Test 1: Basic MPI environment information."""
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    hostname = socket.gethostname()
    
    print_header(rank, "Test 1: Basic MPI Environment")
    
    print(f"Hello from rank {rank} of {size} on {hostname}")
    
    return rank, size, hostname, comm


def test_hostname_collection(rank: int, size: int, hostname: str, comm):
    """Test 2: Collect and display process distribution."""
    print_header(rank, "Test 2: Process Distribution")
    
    if rank == 0:
        # Collect hostnames from all processes
        hostnames = [hostname]
        for i in range(1, size):
            data = comm.recv(source=i, tag=11)
            hostnames.append(data)
        
        # Display distribution
        print(f"\nTotal processes: {size}")
        print(f"\nProcesses distributed across nodes:")
        unique_hosts = sorted(set(hostnames))
        for host in unique_hosts:
            count = hostnames.count(host)
            percentage = (count / size) * 100
            print(f"  {host:30} {count:3} process(es) ({percentage:5.1f}%)")
        
        print(f"\nTotal unique nodes: {len(unique_hosts)}")
        
        return True
    else:
        # Send hostname to rank 0
        comm.send(hostname, dest=0, tag=11)
        return True


def test_point_to_point(rank: int, size: int, comm):
    """Test 3: Point-to-point communication."""
    print_header(rank, "Test 3: Point-to-Point Communication")
    
    if rank == 0:
        # Send test data to all other ranks
        test_data = {
            "message": "Test successful!",
            "from_rank": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        for i in range(1, size):
            comm.send(test_data, dest=i, tag=22)
        
        print(f"✓ Rank 0 sent test data to {size - 1} process(es)")
        return True
    else:
        # Receive test data from rank 0
        data = comm.recv(source=0, tag=22)
        print(f"✓ Rank {rank} received: {data['message']} (timestamp: {data['timestamp']})")
        return True


def test_broadcast(rank: int, size: int, comm):
    """Test 4: Collective broadcast operation."""
    print_header(rank, "Test 4: Collective Broadcast")
    
    if rank == 0:
        bcast_data = {
            "operation": "broadcast",
            "test_value": 42,
            "test_string": "Cluster communication successful"
        }
    else:
        bcast_data = None
    
    # Broadcast from rank 0 to all
    bcast_data = comm.bcast(bcast_data, root=0)
    
    print(f"Rank {rank} received broadcast: test_value={bcast_data['test_value']}, "
          f"test_string='{bcast_data['test_string']}'")
    
    return True


def test_barrier(rank: int, size: int, comm):
    """Test 5: Synchronization barrier."""
    print_header(rank, "Test 5: Synchronization Barrier")
    
    if rank == 0:
        print("All processes reaching barrier...")
    
    # Wait for all processes
    comm.Barrier()
    
    if rank == 0:
        print("✓ All processes synchronized successfully")
    
    return True


def test_reduce(rank: int, size: int, comm):
    """Test 6: Reduction operation."""
    print_header(rank, "Test 6: Reduction Operation")
    
    # Each rank contributes its rank number
    local_value = rank
    
    # Sum all rank numbers
    total = comm.reduce(local_value, op=MPI.SUM, root=0)
    
    if rank == 0:
        expected = sum(range(size))
        if total == expected:
            print(f"✓ Reduction successful: sum of ranks = {total} (expected {expected})")
            return True
        else:
            print(f"✗ Reduction failed: got {total}, expected {expected}")
            return False
    
    return True


def run_all_tests():
    """Run all MPI communication tests."""
    rank = -1  # Initialize for error handling
    try:
        # Test 1: Basic info
        rank, size, hostname, comm = test_basic_info()
        
        # Test 2: Hostname collection
        if not test_hostname_collection(rank, size, hostname, comm):
            return False
        
        # Test 3: Point-to-point
        if not test_point_to_point(rank, size, comm):
            return False
        
        # Test 4: Broadcast
        if not test_broadcast(rank, size, comm):
            return False
        
        # Test 5: Barrier
        if not test_barrier(rank, size, comm):
            return False
        
        # Test 6: Reduce
        if not test_reduce(rank, size, comm):
            return False
        
        # Final summary
        if rank == 0:
            print("\n" + "=" * 70)
            print("✓ ALL MPI COMMUNICATION TESTS PASSED!")
            print("=" * 70)
            print("\nCluster is ready for MPI workloads.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed on rank {rank} with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for MPI communication test."""
    success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
