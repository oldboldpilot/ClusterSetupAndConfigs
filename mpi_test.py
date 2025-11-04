#!/usr/bin/env python3.14
"""
Simple MPI test script to verify cluster communication.
Run with: mpirun -np <num_processes> --host <host1>,<host2> python3.14 mpi_test.py
"""

from mpi4py import MPI
import socket

def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    hostname = socket.gethostname()
    
    print(f"Hello from rank {rank} of {size} on {hostname}")
    
    # Simple communication test
    if rank == 0:
        print(f"\n=== MPI Test Results ===")
        print(f"Total processes: {size}")
        print(f"Master node: {hostname}")
        
        # Collect hostnames from all processes
        hostnames = [hostname]
        for i in range(1, size):
            data = comm.recv(source=i, tag=11)
            hostnames.append(data)
        
        print(f"\nProcesses distributed across nodes:")
        unique_hosts = set(hostnames)
        for host in unique_hosts:
            count = hostnames.count(host)
            print(f"  {host}: {count} process(es)")
        
        # Send test data to all other ranks
        test_data = {"message": "Test successful!", "from_rank": 0}
        for i in range(1, size):
            comm.send(test_data, dest=i, tag=22)
        
        print("\n✓ MPI cluster communication test passed!")
    else:
        # Send hostname to rank 0
        comm.send(hostname, dest=0, tag=11)
        
        # Receive test data from rank 0
        data = comm.recv(source=0, tag=22)
        print(f"Rank {rank} received: {data['message']}")

if __name__ == "__main__":
    main()
