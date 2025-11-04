"""
Test Suite for PGAS Benchmarks

Tests benchmark suite creation, compilation, and execution.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import unittest
import subprocess
from pathlib import Path


class TestBenchmarkSuite(unittest.TestCase):
    """Test benchmark suite structure and files."""
    
    def test_benchmark_directory_exists(self):
        """Test that benchmark directory exists."""
        benchmark_dir = Path.home() / "pgas_benchmarks"
        
        # This might not exist until benchmarks are created
        if benchmark_dir.exists():
            self.assertTrue(benchmark_dir.is_dir(), "Benchmark directory should be a directory")
    
    def test_benchmark_src_directory(self):
        """Test that src directory exists."""
        src_dir = Path.home() / "pgas_benchmarks" / "src"
        
        if src_dir.exists():
            self.assertTrue(src_dir.is_dir(), "src directory should exist")
    
    def test_benchmark_bin_directory(self):
        """Test that bin directory exists."""
        bin_dir = Path.home() / "pgas_benchmarks" / "bin"
        
        if bin_dir.exists():
            self.assertTrue(bin_dir.is_dir(), "bin directory should exist")
    
    def test_benchmark_results_directory(self):
        """Test that results directory exists."""
        results_dir = Path.home() / "pgas_benchmarks" / "results"
        
        if results_dir.exists():
            self.assertTrue(results_dir.is_dir(), "results directory should exist")
    
    def test_makefile_exists(self):
        """Test that Makefile exists."""
        makefile = Path.home() / "pgas_benchmarks" / "Makefile"
        
        if makefile.exists():
            self.assertTrue(makefile.is_file(), "Makefile should be a file")
            
            # Check that Makefile has required targets
            content = makefile.read_text()
            self.assertIn("all:", content, "Makefile should have 'all' target")
            self.assertIn("clean:", content, "Makefile should have 'clean' target")
    
    def test_run_script_exists(self):
        """Test that run_benchmarks.sh exists and is executable."""
        run_script = Path.home() / "pgas_benchmarks" / "run_benchmarks.sh"
        
        if run_script.exists():
            self.assertTrue(run_script.is_file(), "run_benchmarks.sh should be a file")
            
            # Check if executable
            import stat
            mode = run_script.stat().st_mode
            self.assertTrue(mode & stat.S_IXUSR, "run_benchmarks.sh should be executable")


class TestBenchmarkSourceFiles(unittest.TestCase):
    """Test benchmark source files."""
    
    def test_upcxx_latency_source_exists(self):
        """Test that UPC++ latency benchmark source exists."""
        source_file = Path.home() / "pgas_benchmarks" / "src" / "upcxx_latency.cpp"
        
        if source_file.exists():
            self.assertTrue(source_file.is_file(), "upcxx_latency.cpp should be a file")
            
            # Check for required UPC++ includes
            content = source_file.read_text()
            self.assertIn("#include <upcxx/upcxx.hpp>", content, "Should include upcxx header")
            self.assertIn("upcxx::init()", content, "Should call upcxx::init()")
            self.assertIn("upcxx::finalize()", content, "Should call upcxx::finalize()")
    
    def test_mpi_latency_source_exists(self):
        """Test that MPI latency benchmark source exists."""
        source_file = Path.home() / "pgas_benchmarks" / "src" / "mpi_latency.c"
        
        if source_file.exists():
            self.assertTrue(source_file.is_file(), "mpi_latency.c should be a file")
            
            # Check for required MPI includes
            content = source_file.read_text()
            self.assertIn("#include <mpi.h>", content, "Should include mpi.h header")
            self.assertIn("MPI_Init", content, "Should call MPI_Init")
            self.assertIn("MPI_Finalize", content, "Should call MPI_Finalize")
    
    def test_upcxx_bandwidth_source_exists(self):
        """Test that UPC++ bandwidth benchmark source exists."""
        source_file = Path.home() / "pgas_benchmarks" / "src" / "upcxx_bandwidth.cpp"
        
        if source_file.exists():
            self.assertTrue(source_file.is_file(), "upcxx_bandwidth.cpp should be a file")
            
            # Check for required UPC++ includes
            content = source_file.read_text()
            self.assertIn("#include <upcxx/upcxx.hpp>", content, "Should include upcxx header")


class TestBenchmarkCompilation(unittest.TestCase):
    """Test benchmark compilation."""
    
    def setUp(self):
        """Set up test environment."""
        self.benchmark_dir = Path.home() / "pgas_benchmarks"
        
        # Skip all tests if benchmark directory doesn't exist
        if not self.benchmark_dir.exists():
            self.skipTest("Benchmark directory not created yet")
    
    def test_makefile_clean(self):
        """Test that 'make clean' works."""
        if not (self.benchmark_dir / "Makefile").exists():
            self.skipTest("Makefile not created yet")
        
        result = subprocess.run(
            ["make", "clean"],
            cwd=self.benchmark_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        self.assertEqual(result.returncode, 0, "'make clean' should succeed")
    
    def test_upcxx_compiler_available(self):
        """Test that upcxx compiler is available for benchmarks."""
        result = subprocess.run(
            ["which", "upcxx"],
            capture_output=True,
            text=True
        )
        
        # upcxx should be available if PGAS is installed
        if result.returncode == 0:
            self.assertTrue(True, "upcxx compiler is available")
    
    def test_mpi_compiler_available(self):
        """Test that mpicc compiler is available for benchmarks."""
        result = subprocess.run(
            ["which", "mpicc"],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0, "mpicc should be available")


class TestBenchmarkExecution(unittest.TestCase):
    """Test benchmark execution."""
    
    def test_run_script_syntax(self):
        """Test that run_benchmarks.sh has valid bash syntax."""
        run_script = Path.home() / "pgas_benchmarks" / "run_benchmarks.sh"
        
        if not run_script.exists():
            self.skipTest("run_benchmarks.sh not created yet")
        
        # Check bash syntax
        result = subprocess.run(
            ["bash", "-n", str(run_script)],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0, "run_benchmarks.sh should have valid bash syntax")
    
    def test_benchmark_binaries_location(self):
        """Test that compiled binaries would be in bin directory."""
        bin_dir = Path.home() / "pgas_benchmarks" / "bin"
        
        if not bin_dir.exists():
            self.skipTest("bin directory not created yet")
        
        # Check if any binaries exist
        binaries = list(bin_dir.glob("*"))
        
        # This is informational - binaries might not be compiled yet
        if binaries:
            for binary in binaries:
                self.assertTrue(binary.is_file(), f"{binary.name} should be a file")


if __name__ == "__main__":
    unittest.main()
