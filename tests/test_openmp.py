"""
Test Suite for OpenMP Configuration

Tests OpenMP installation, configuration, and functionality across the cluster.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import unittest
import subprocess
import os
from pathlib import Path


class TestOpenMP(unittest.TestCase):
    """Test OpenMP installation and basic functionality."""
    
    def test_libomp_installed(self):
        """Test that libomp is installed via Homebrew."""
        result = subprocess.run(
            ["brew", "list", "libomp"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, "libomp should be installed via Homebrew")
    
    def test_libomp_prefix_exists(self):
        """Test that libomp installation directory exists."""
        result = subprocess.run(
            ["brew", "--prefix", "libomp"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, "libomp prefix should exist")
        
        prefix = result.stdout.strip()
        self.assertTrue(os.path.exists(prefix), f"libomp prefix {prefix} should exist")
    
    def test_omp_header_exists(self):
        """Test that omp.h header file exists."""
        result = subprocess.run(
            ["brew", "--prefix", "libomp"],
            capture_output=True,
            text=True
        )
        prefix = result.stdout.strip()
        omp_header = Path(prefix) / "include" / "omp.h"
        self.assertTrue(omp_header.exists(), f"omp.h should exist at {omp_header}")
    
    def test_libomp_library_exists(self):
        """Test that libomp library file exists."""
        result = subprocess.run(
            ["brew", "--prefix", "libomp"],
            capture_output=True,
            text=True
        )
        prefix = result.stdout.strip()
        
        # Check for either libomp.dylib (macOS) or libomp.so (Linux)
        lib_dir = Path(prefix) / "lib"
        has_dylib = (lib_dir / "libomp.dylib").exists()
        has_so = (lib_dir / "libomp.so").exists()
        
        self.assertTrue(
            has_dylib or has_so,
            f"libomp library should exist in {lib_dir}"
        )
    
    def test_gcc_supports_openmp(self):
        """Test that GCC supports OpenMP flag."""
        # Create minimal OpenMP test
        test_code = """
#include <omp.h>
int main() { return 0; }
"""
        test_dir = Path.home() / "test_openmp_gcc"
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test.c"
        test_file.write_text(test_code)
        
        # Get libomp prefix
        prefix_result = subprocess.run(
            ["brew", "--prefix", "libomp"],
            capture_output=True,
            text=True
        )
        prefix = prefix_result.stdout.strip()
        
        # Try to compile with -fopenmp
        compile_cmd = [
            "gcc",
            "-fopenmp",
            f"-I{prefix}/include",
            f"-L{prefix}/lib",
            "-lomp",
            str(test_file),
            "-o", str(test_dir / "test")
        ]
        
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "GCC should compile OpenMP code")
        
        # Cleanup
        if (test_dir / "test").exists():
            (test_dir / "test").unlink()
        test_file.unlink()


class TestOpenMPAdvanced(unittest.TestCase):
    """Advanced OpenMP tests."""
    
    def test_openmp_parallel_execution(self):
        """Test OpenMP parallel region execution."""
        test_code = """
#include <stdio.h>
#include <omp.h>

int main() {
    int count = 0;
    #pragma omp parallel
    {
        #pragma omp atomic
        count++;
    }
    printf("%d\\n", count);
    return 0;
}
"""
        test_dir = Path.home() / "test_openmp_parallel"
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test_parallel.c"
        test_file.write_text(test_code)
        
        # Get libomp prefix
        prefix_result = subprocess.run(
            ["brew", "--prefix", "libomp"],
            capture_output=True,
            text=True
        )
        prefix = prefix_result.stdout.strip()
        
        # Compile
        compile_cmd = [
            "gcc",
            "-fopenmp",
            f"-I{prefix}/include",
            f"-L{prefix}/lib",
            "-lomp",
            str(test_file),
            "-o", str(test_dir / "test_parallel")
        ]
        
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)
        self.assertEqual(compile_result.returncode, 0, "Should compile parallel test")
        
        # Run with 4 threads
        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = "4"
        
        run_result = subprocess.run(
            [str(test_dir / "test_parallel")],
            capture_output=True,
            text=True,
            env=env
        )
        
        self.assertEqual(run_result.returncode, 0, "Should execute successfully")
        
        thread_count = int(run_result.stdout.strip())
        self.assertEqual(thread_count, 4, "Should use 4 threads")
        
        # Cleanup
        if (test_dir / "test_parallel").exists():
            (test_dir / "test_parallel").unlink()
        test_file.unlink()
    
    def test_openmp_environment_variable(self):
        """Test that OMP_NUM_THREADS environment variable works."""
        test_code = """
#include <stdio.h>
#include <omp.h>

int main() {
    int max_threads = omp_get_max_threads();
    printf("%d\\n", max_threads);
    return 0;
}
"""
        test_dir = Path.home() / "test_openmp_env"
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test_env.c"
        test_file.write_text(test_code)
        
        # Get libomp prefix
        prefix_result = subprocess.run(
            ["brew", "--prefix", "libomp"],
            capture_output=True,
            text=True
        )
        prefix = prefix_result.stdout.strip()
        
        # Compile
        compile_cmd = [
            "gcc",
            "-fopenmp",
            f"-I{prefix}/include",
            f"-L{prefix}/lib",
            "-lomp",
            str(test_file),
            "-o", str(test_dir / "test_env")
        ]
        
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)
        self.assertEqual(compile_result.returncode, 0, "Should compile env test")
        
        # Test with different thread counts
        for num_threads in [2, 4, 8]:
            env = os.environ.copy()
            env["OMP_NUM_THREADS"] = str(num_threads)
            
            run_result = subprocess.run(
                [str(test_dir / "test_env")],
                capture_output=True,
                text=True,
                env=env
            )
            
            max_threads = int(run_result.stdout.strip())
            self.assertEqual(
                max_threads,
                num_threads,
                f"OMP_NUM_THREADS={num_threads} should set max threads to {num_threads}"
            )
        
        # Cleanup
        if (test_dir / "test_env").exists():
            (test_dir / "test_env").unlink()
        test_file.unlink()


if __name__ == "__main__":
    unittest.main()
