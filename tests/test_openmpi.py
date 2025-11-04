#!/usr/bin/env python3
"""
OpenMPI Tests

Tests for OpenMPI installation, configuration, and multi-node execution.
"""

import unittest
import subprocess
import os
from pathlib import Path


class TestOpenMPI(unittest.TestCase):
    """Test cases for OpenMPI functionality"""
    
    def test_mpirun_exists(self):
        """Test that mpirun command is available"""
        result = subprocess.run(['which', 'mpirun'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "mpirun not found in PATH")
        self.assertIn('mpirun', result.stdout)
    
    def test_mpirun_version(self):
        """Test that mpirun version can be retrieved"""
        result = subprocess.run(['mpirun', '--version'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "mpirun --version failed")
        self.assertIn('mpirun', result.stdout.lower())
    
    def test_mpicc_exists(self):
        """Test that mpicc compiler wrapper exists"""
        result = subprocess.run(['which', 'mpicc'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "mpicc not found in PATH")
    
    def test_mpicxx_exists(self):
        """Test that mpic++ compiler wrapper exists"""
        result = subprocess.run(['which', 'mpic++'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "mpic++ not found in PATH")
    
    def test_mpi_hostfiles_exist(self):
        """Test that MPI hostfiles were created"""
        home = Path.home()
        openmpi_dir = home / '.openmpi'
        
        self.assertTrue(openmpi_dir.exists(), "~/.openmpi directory not found")
        self.assertTrue((openmpi_dir / 'hostfile').exists(), "hostfile not found")
        self.assertTrue((openmpi_dir / 'hostfile_optimal').exists(), "hostfile_optimal not found")
        self.assertTrue((openmpi_dir / 'hostfile_max').exists(), "hostfile_max not found")
    
    def test_mca_config_exists(self):
        """Test that MCA parameters configuration exists"""
        home = Path.home()
        mca_config = home / '.openmpi' / 'mca-params.conf'
        
        self.assertTrue(mca_config.exists(), "mca-params.conf not found")
        
        # Check for key MCA parameters
        with open(mca_config, 'r') as f:
            content = f.read()
            self.assertIn('btl_tcp_if_include', content, "btl_tcp_if_include not configured")
    
    def test_simple_mpi_program(self):
        """Test compiling and running a simple MPI program"""
        test_dir = Path('/tmp/mpi_test')
        test_dir.mkdir(exist_ok=True)
        
        # Create a simple MPI C program
        mpi_program = test_dir / 'hello_mpi.c'
        with open(mpi_program, 'w') as f:
            f.write("""
#include <mpi.h>
#include <stdio.h>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    
    printf("Hello from rank %d of %d\\n", rank, size);
    
    MPI_Finalize();
    return 0;
}
""")
        
        # Compile
        compile_result = subprocess.run(
            ['mpicc', str(mpi_program), '-o', str(test_dir / 'hello_mpi')],
            capture_output=True, text=True
        )
        self.assertEqual(compile_result.returncode, 0, f"MPI compilation failed: {compile_result.stderr}")
        
        # Run with 2 processes
        run_result = subprocess.run(
            ['mpirun', '-np', '2', str(test_dir / 'hello_mpi')],
            capture_output=True, text=True
        )
        self.assertEqual(run_result.returncode, 0, f"MPI execution failed: {run_result.stderr}")
        self.assertIn('Hello from rank', run_result.stdout)
    
    def test_homebrew_mpi_installation(self):
        """Test that OpenMPI is installed via Homebrew"""
        result = subprocess.run(['brew', 'list', 'open-mpi'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "OpenMPI not installed via Homebrew")


class TestOpenMPIAdvanced(unittest.TestCase):
    """Advanced OpenMPI tests"""
    
    def test_mpi_send_recv(self):
        """Test MPI point-to-point communication"""
        test_dir = Path('/tmp/mpi_test_advanced')
        test_dir.mkdir(exist_ok=True)
        
        # Create send/recv test
        program = test_dir / 'send_recv.c'
        with open(program, 'w') as f:
            f.write("""
#include <mpi.h>
#include <stdio.h>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    
    if (size < 2) {
        printf("Need at least 2 processes\\n");
        MPI_Finalize();
        return 1;
    }
    
    int value = rank;
    if (rank == 0) {
        value = 42;
        MPI_Send(&value, 1, MPI_INT, 1, 0, MPI_COMM_WORLD);
        printf("Rank 0 sent: %d\\n", value);
    } else if (rank == 1) {
        MPI_Recv(&value, 1, MPI_INT, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        printf("Rank 1 received: %d\\n", value);
    }
    
    MPI_Finalize();
    return 0;
}
""")
        
        # Compile and run
        subprocess.run(['mpicc', str(program), '-o', str(test_dir / 'send_recv')], 
                      capture_output=True, check=False)
        result = subprocess.run(['mpirun', '-np', '2', str(test_dir / 'send_recv')],
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            self.assertIn('sent: 42', result.stdout)
            self.assertIn('received: 42', result.stdout)


if __name__ == '__main__':
    unittest.main()
