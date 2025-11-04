"""
Test Suite for Benchmark Template Generation

Tests the Jinja2-based benchmark code generation system, ensuring all templates
render correctly and produce valid benchmark code.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import unittest
import subprocess
import os
from pathlib import Path
import tempfile
import shutil


class TestBenchmarkTemplateGeneration(unittest.TestCase):
    """Test Jinja2 template-based benchmark generation"""
    
    def setUp(self):
        """Setup test environment before each test"""
        self.test_dir = Path(__file__).parent
        self.cluster_dir = self.test_dir.parent
        self.template_dir = self.cluster_dir / "cluster_modules" / "templates"
        
        # Create temporary benchmark directory
        self.temp_dir = Path(tempfile.mkdtemp())
        self.benchmark_dir = self.temp_dir / "test_benchmarks"
        self.benchmark_dir.mkdir(parents=True)
    
    def tearDown(self):
        """Cleanup after each test"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_template_directory_exists(self):
        """Verify template directory exists"""
        self.assertTrue(self.template_dir.exists(),
                       f"Template directory not found: {self.template_dir}")
    
    def test_upcxx_latency_template_exists(self):
        """Verify UPC++ latency template exists"""
        template_file = self.template_dir / "upcxx_latency.cpp.j2"
        self.assertTrue(template_file.exists(),
                       f"UPC++ latency template not found: {template_file}")
    
    def test_mpi_latency_template_exists(self):
        """Verify MPI latency template exists"""
        template_file = self.template_dir / "mpi_latency.cpp.j2"
        self.assertTrue(template_file.exists(),
                       f"MPI latency template not found: {template_file}")
    
    def test_upcxx_bandwidth_template_exists(self):
        """Verify UPC++ bandwidth template exists"""
        template_file = self.template_dir / "upcxx_bandwidth.cpp.j2"
        self.assertTrue(template_file.exists(),
                       f"UPC++ bandwidth template not found: {template_file}")
    
    def test_openshmem_latency_template_exists(self):
        """Verify OpenSHMEM latency template exists"""
        template_file = self.template_dir / "openshmem_latency.cpp.j2"
        self.assertTrue(template_file.exists(),
                       f"OpenSHMEM latency template not found: {template_file}")
    
    def test_berkeley_upc_latency_template_exists(self):
        """Verify Berkeley UPC latency template exists"""
        template_file = self.template_dir / "berkeley_upc_latency.c.j2"
        self.assertTrue(template_file.exists(),
                       f"Berkeley UPC latency template not found: {template_file}")
    
    def test_makefile_template_exists(self):
        """Verify Makefile template exists"""
        template_file = self.template_dir / "Makefile.j2"
        self.assertTrue(template_file.exists(),
                       f"Makefile template not found: {template_file}")
    
    def test_run_script_template_exists(self):
        """Verify run script template exists"""
        template_file = self.template_dir / "run_benchmarks.sh.j2"
        self.assertTrue(template_file.exists(),
                       f"Run script template not found: {template_file}")


class TestBenchmarkManagerJinja2(unittest.TestCase):
    """Test BenchmarkManager with Jinja2 templates"""
    
    def setUp(self):
        """Setup test environment before each test"""
        self.test_dir = Path(__file__).parent
        self.cluster_dir = self.test_dir.parent
        
        # Create temporary benchmark directory
        self.temp_dir = Path(tempfile.mkdtemp())
        self.benchmark_dir = self.temp_dir / "test_benchmarks"
    
    def tearDown(self):
        """Cleanup after each test"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_benchmark_manager_import(self):
        """Test that BenchmarkManager can be imported"""
        try:
            from cluster_modules.benchmark_manager import BenchmarkManager
            self.assertTrue(True, "BenchmarkManager imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import BenchmarkManager: {e}")
    
    def test_benchmark_manager_jinja2_env(self):
        """Test that BenchmarkManager initializes Jinja2 environment"""
        from cluster_modules.benchmark_manager import BenchmarkManager
        
        manager = BenchmarkManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"],
            benchmark_dir=self.benchmark_dir
        )
        
        self.assertIsNotNone(manager.jinja_env,
                           "Jinja2 environment not initialized")
    
    def test_create_benchmark_directory(self):
        """Test benchmark directory creation"""
        from cluster_modules.benchmark_manager import BenchmarkManager
        
        manager = BenchmarkManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"],
            benchmark_dir=self.benchmark_dir
        )
        
        success = manager.create_benchmark_directory()
        
        self.assertTrue(success, "Failed to create benchmark directory")
        self.assertTrue(self.benchmark_dir.exists(), "Benchmark directory not created")
        self.assertTrue((self.benchmark_dir / "src").exists(), "src directory not created")
        self.assertTrue((self.benchmark_dir / "bin").exists(), "bin directory not created")
        self.assertTrue((self.benchmark_dir / "results").exists(), "results directory not created")
    
    def test_create_upcxx_latency_benchmark(self):
        """Test UPC++ latency benchmark generation"""
        from cluster_modules.benchmark_manager import BenchmarkManager
        
        manager = BenchmarkManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"],
            benchmark_dir=self.benchmark_dir
        )
        
        manager.create_benchmark_directory()
        success = manager.create_upcxx_latency_benchmark(iterations=500, warmup_iterations=50)
        
        self.assertTrue(success, "Failed to create UPC++ latency benchmark")
        
        benchmark_file = self.benchmark_dir / "src" / "upcxx_latency.cpp"
        self.assertTrue(benchmark_file.exists(), "UPC++ latency benchmark file not created")
        
        # Verify content contains expected values
        content = benchmark_file.read_text()
        self.assertIn("500", content, "Iterations not found in generated code")
        self.assertIn("50", content, "Warmup iterations not found in generated code")
        self.assertIn("upcxx", content, "UPC++ include not found")
    
    def test_create_mpi_latency_benchmark(self):
        """Test MPI latency benchmark generation"""
        from cluster_modules.benchmark_manager import BenchmarkManager
        
        manager = BenchmarkManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"],
            benchmark_dir=self.benchmark_dir
        )
        
        manager.create_benchmark_directory()
        success = manager.create_mpi_latency_benchmark(
            iterations=500, 
            warmup_iterations=50,
            message_size=16
        )
        
        self.assertTrue(success, "Failed to create MPI latency benchmark")
        
        benchmark_file = self.benchmark_dir / "src" / "mpi_latency.cpp"
        self.assertTrue(benchmark_file.exists(), "MPI latency benchmark file not created")
        
        # Verify content
        content = benchmark_file.read_text()
        self.assertIn("mpi.h", content, "MPI include not found")
        self.assertIn("16", content, "Message size not found in generated code")
    
    def test_create_makefile(self):
        """Test Makefile generation"""
        from cluster_modules.benchmark_manager import BenchmarkManager
        
        manager = BenchmarkManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"],
            benchmark_dir=self.benchmark_dir
        )
        
        manager.create_benchmark_directory()
        success = manager.create_makefile()
        
        self.assertTrue(success, "Failed to create Makefile")
        
        makefile = self.benchmark_dir / "Makefile"
        self.assertTrue(makefile.exists(), "Makefile not created")
        
        # Verify Makefile content
        content = makefile.read_text()
        self.assertIn("upcxx_latency", content, "upcxx_latency target not found")
        self.assertIn("mpi_latency", content, "mpi_latency target not found")
        self.assertIn("openshmem_latency", content, "openshmem_latency target not found")
        self.assertIn("berkeley_upc_latency", content, "berkeley_upc_latency target not found")
        self.assertIn("clean", content, "clean target not found")
    
    def test_create_run_script(self):
        """Test run script generation"""
        from cluster_modules.benchmark_manager import BenchmarkManager
        
        manager = BenchmarkManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"],
            benchmark_dir=self.benchmark_dir
        )
        
        manager.create_benchmark_directory()
        success = manager.create_run_script(num_procs=4)
        
        self.assertTrue(success, "Failed to create run script")
        
        run_script = self.benchmark_dir / "run_benchmarks.sh"
        self.assertTrue(run_script.exists(), "Run script not created")
        
        # Verify script is executable
        self.assertTrue(os.access(run_script, os.X_OK), 
                       "Run script is not executable")
        
        # Verify script content
        content = run_script.read_text()
        self.assertIn("NUM_PROCS=4", content, "NUM_PROCS not set correctly")
        self.assertIn("upcxx-run", content, "upcxx-run launcher not found")
        self.assertIn("mpirun", content, "mpirun launcher not found")
        self.assertIn("oshrun", content, "oshrun launcher not found")
    
    def test_create_all_benchmarks(self):
        """Test creating complete benchmark suite"""
        from cluster_modules.benchmark_manager import BenchmarkManager
        
        manager = BenchmarkManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"],
            benchmark_dir=self.benchmark_dir
        )
        
        success = manager.create_all_benchmarks(
            iterations=500,
            warmup_iterations=50,
            num_procs=2
        )
        
        self.assertTrue(success, "Failed to create complete benchmark suite")
        
        # Verify all components exist
        self.assertTrue((self.benchmark_dir / "src" / "upcxx_latency.cpp").exists())
        self.assertTrue((self.benchmark_dir / "src" / "mpi_latency.cpp").exists())
        self.assertTrue((self.benchmark_dir / "src" / "upcxx_bandwidth.cpp").exists())
        self.assertTrue((self.benchmark_dir / "src" / "openshmem_latency.cpp").exists())
        self.assertTrue((self.benchmark_dir / "src" / "berkeley_upc_latency.c").exists())
        self.assertTrue((self.benchmark_dir / "Makefile").exists())
        self.assertTrue((self.benchmark_dir / "run_benchmarks.sh").exists())


class TestBenchmarkTemplateContent(unittest.TestCase):
    """Test generated benchmark code syntax and structure"""
    
    def setUp(self):
        """Setup test environment"""
        self.test_dir = Path(__file__).parent
        self.cluster_dir = self.test_dir.parent
        
        # Create temporary directory
        self.temp_dir = Path(tempfile.mkdtemp())
        self.benchmark_dir = self.temp_dir / "test_benchmarks"
        
        # Create benchmark manager and generate suite
        from cluster_modules.benchmark_manager import BenchmarkManager
        
        self.manager = BenchmarkManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"],
            benchmark_dir=self.benchmark_dir
        )
        
        self.manager.create_all_benchmarks()
    
    def tearDown(self):
        """Cleanup"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_upcxx_latency_syntax(self):
        """Test UPC++ latency code has valid C++ syntax"""
        benchmark_file = self.benchmark_dir / "src" / "upcxx_latency.cpp"
        content = benchmark_file.read_text()
        
        # Check for required includes
        self.assertIn("#include <upcxx/upcxx.hpp>", content)
        self.assertIn("#include <iostream>", content)
        self.assertIn("#include <chrono>", content)
        
        # Check for main function
        self.assertIn("int main(", content)
        
        # Check for UPC++ initialization/finalization
        self.assertIn("upcxx::init()", content)
        self.assertIn("upcxx::finalize()", content)
    
    def test_mpi_latency_syntax(self):
        """Test MPI latency code has valid C++ syntax"""
        benchmark_file = self.benchmark_dir / "src" / "mpi_latency.cpp"
        content = benchmark_file.read_text()
        
        # Check for required includes
        self.assertIn("#include <mpi.h>", content)
        self.assertIn("#include <iostream>", content)
        
        # Check for MPI initialization/finalization
        self.assertIn("MPI_Init", content)
        self.assertIn("MPI_Finalize", content)
        self.assertIn("MPI_Send", content)
        self.assertIn("MPI_Recv", content)
    
    def test_openshmem_latency_syntax(self):
        """Test OpenSHMEM latency code has valid C++ syntax"""
        benchmark_file = self.benchmark_dir / "src" / "openshmem_latency.cpp"
        content = benchmark_file.read_text()
        
        # Check for required includes
        self.assertIn("#include <shmem.h>", content)
        
        # Check for OpenSHMEM functions
        self.assertIn("shmem_init", content)
        self.assertIn("shmem_finalize", content)
        self.assertIn("shmem_barrier_all", content)
    
    def test_berkeley_upc_latency_syntax(self):
        """Test Berkeley UPC latency code has valid C syntax"""
        benchmark_file = self.benchmark_dir / "src" / "berkeley_upc_latency.c"
        content = benchmark_file.read_text()
        
        # Check for required includes
        self.assertIn("#include <upc.h>", content)
        
        # Check for UPC constructs
        self.assertIn("MYTHREAD", content)
        self.assertIn("THREADS", content)
        self.assertIn("upc_barrier", content)
        self.assertIn("shared", content)
    
    def test_makefile_syntax(self):
        """Test Makefile has valid syntax"""
        makefile = self.benchmark_dir / "Makefile"
        content = makefile.read_text()
        
        # Check for targets
        self.assertIn("all:", content)
        self.assertIn("clean:", content)
        self.assertIn(".PHONY:", content)
        
        # Check for compilers
        self.assertIn("UPCXX", content)
        self.assertIn("MPICXX", content)
        self.assertIn("OSHCC", content)
        self.assertIn("UPCC", content)
    
    def test_run_script_syntax(self):
        """Test run script has valid bash syntax"""
        run_script = self.benchmark_dir / "run_benchmarks.sh"
        content = run_script.read_text()
        
        # Check for bash shebang
        self.assertTrue(content.startswith("#!/bin/bash"),
                       "Script missing bash shebang")
        
        # Verify script syntax using bash -n
        result = subprocess.run(
            ['bash', '-n', str(run_script)],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0,
                        f"Script has syntax errors:\n{result.stderr}")


if __name__ == '__main__':
    unittest.main()
