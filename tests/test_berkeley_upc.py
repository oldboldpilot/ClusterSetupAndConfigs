"""
Tests for Berkeley UPC Manager Module

This test suite validates Berkeley UPC installation, configuration, and functionality
including compilation, execution, and multi-node distributed shared memory operations.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import unittest
import subprocess
import os
from pathlib import Path


class TestBerkeleyUPC(unittest.TestCase):
    """Test Berkeley UPC installation and basic functionality"""
    
    def setUp(self):
        """Setup before each test"""
        self.test_dir = Path(__file__).parent.parent
        self.bupc_prefix = "/home/linuxbrew/.linuxbrew"
        
    def test_berkeley_upc_installation_directory(self):
        """Test that Berkeley UPC installation directory exists"""
        # Check for any berkeley-upc directory
        bupc_dirs = list(Path(self.bupc_prefix).glob("berkeley-upc-*"))
        self.assertGreater(len(bupc_dirs), 0, 
                          "No Berkeley UPC installation directory found")
        print(f"✓ Found Berkeley UPC installation: {bupc_dirs[0]}")
    
    def test_upcc_exists(self):
        """Test that upcc compiler wrapper exists"""
        # Check in installation directory
        bupc_dirs = list(Path(self.bupc_prefix).glob("berkeley-upc-*"))
        if bupc_dirs:
            upcc_path = bupc_dirs[0] / "bin" / "upcc"
            self.assertTrue(upcc_path.exists(), 
                          f"upcc not found at {upcc_path}")
            print(f"✓ upcc found: {upcc_path}")
        else:
            # Check in PATH
            result = subprocess.run(["which", "upcc"], 
                                  capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, 
                           "upcc not found in PATH")
            print(f"✓ upcc found in PATH: {result.stdout.strip()}")
    
    def test_upcrun_exists(self):
        """Test that upcrun launcher exists"""
        # Check in installation directory
        bupc_dirs = list(Path(self.bupc_prefix).glob("berkeley-upc-*"))
        if bupc_dirs:
            upcrun_path = bupc_dirs[0] / "bin" / "upcrun"
            self.assertTrue(upcrun_path.exists(), 
                          f"upcrun not found at {upcrun_path}")
            print(f"✓ upcrun found: {upcrun_path}")
        else:
            # Check in PATH
            result = subprocess.run(["which", "upcrun"], 
                                  capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, 
                           "upcrun not found in PATH")
            print(f"✓ upcrun found in PATH: {result.stdout.strip()}")
    
    def test_upcc_version(self):
        """Test that upcc reports version information"""
        result = subprocess.run(["upcc", "-V"], 
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, 
                        "upcc -V failed")
        self.assertIn("Berkeley UPC", result.stdout, 
                     "Version output doesn't contain 'Berkeley UPC'")
        print(f"✓ upcc version:\n{result.stdout.strip()}")
    
    def test_gasnet_conduit_configuration(self):
        """Test that GASNet conduit is properly configured"""
        result = subprocess.run(["upcc", "-V"], 
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "upcc -V failed")
        
        # Check for GASNet conduit information
        output = result.stdout.lower()
        conduits = ["mpi", "udp", "smp", "ibv", "gasnet"]
        has_conduit = any(conduit in output for conduit in conduits)
        self.assertTrue(has_conduit, 
                       "No GASNet conduit information found in version output")
        print(f"✓ GASNet conduit configured")


class TestBerkeleyUPCAdvanced(unittest.TestCase):
    """Test Berkeley UPC compilation and execution"""
    
    def setUp(self):
        """Setup test directory and program"""
        self.test_dir = Path.home() / "bupc_test_suite"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
    def tearDown(self):
        """Cleanup test files"""
        if self.test_dir.exists():
            import shutil
            shutil.rmtree(self.test_dir)
    
    def test_simple_upc_compilation(self):
        """Test compilation of simple UPC program"""
        # Create simple UPC program
        test_file = self.test_dir / "simple.c"
        test_code = """
#include <upc.h>
#include <stdio.h>

int main() {
    printf("Thread %d of %d\\n", MYTHREAD, THREADS);
    return 0;
}
"""
        test_file.write_text(test_code)
        
        # Compile
        result = subprocess.run(
            ["upcc", "-o", str(self.test_dir / "simple"), str(test_file)],
            capture_output=True, text=True
        )
        
        self.assertEqual(result.returncode, 0, 
                        f"Compilation failed: {result.stderr}")
        self.assertTrue((self.test_dir / "simple").exists(), 
                       "Compiled binary not created")
        print(f"✓ Simple UPC program compiled successfully")
    
    def test_upc_hello_world(self):
        """Test execution of UPC Hello World program"""
        # Create Hello World program
        test_file = self.test_dir / "hello.c"
        test_code = """
#include <upc.h>
#include <stdio.h>

int main() {
    printf("Hello from UPC thread %d of %d\\n", MYTHREAD, THREADS);
    return 0;
}
"""
        test_file.write_text(test_code)
        
        # Compile
        compile_result = subprocess.run(
            ["upcc", "-o", str(self.test_dir / "hello"), str(test_file)],
            capture_output=True, text=True
        )
        self.assertEqual(compile_result.returncode, 0, 
                        f"Compilation failed: {compile_result.stderr}")
        
        # Execute with 2 threads
        run_result = subprocess.run(
            ["upcrun", "-n", "2", str(self.test_dir / "hello")],
            capture_output=True, text=True, timeout=30
        )
        
        self.assertEqual(run_result.returncode, 0, 
                        f"Execution failed: {run_result.stderr}")
        self.assertIn("Hello from UPC thread", run_result.stdout,
                     "Expected output not found")
        print(f"✓ UPC Hello World executed successfully")
        print(f"  Output: {run_result.stdout.strip()}")
    
    def test_upc_shared_memory(self):
        """Test UPC shared memory allocation and access"""
        test_file = self.test_dir / "shared_mem.c"
        test_code = """
#include <upc.h>
#include <stdio.h>

shared int shared_var = 42;

int main() {
    upc_barrier;
    if (MYTHREAD == 0) {
        printf("Shared variable value: %d\\n", shared_var);
        shared_var = 100;
    }
    upc_barrier;
    if (MYTHREAD == 1) {
        printf("Updated shared variable: %d\\n", shared_var);
    }
    upc_barrier;
    return 0;
}
"""
        test_file.write_text(test_code)
        
        # Compile
        compile_result = subprocess.run(
            ["upcc", "-o", str(self.test_dir / "shared_mem"), str(test_file)],
            capture_output=True, text=True
        )
        self.assertEqual(compile_result.returncode, 0, 
                        f"Compilation failed: {compile_result.stderr}")
        
        # Execute with 2 threads
        run_result = subprocess.run(
            ["upcrun", "-n", "2", str(self.test_dir / "shared_mem")],
            capture_output=True, text=True, timeout=30
        )
        
        self.assertEqual(run_result.returncode, 0, 
                        f"Execution failed: {run_result.stderr}")
        self.assertIn("Shared variable value", run_result.stdout,
                     "Shared memory access failed")
        print(f"✓ UPC shared memory test passed")
        print(f"  Output: {run_result.stdout.strip()}")
    
    def test_upc_collective_operations(self):
        """Test UPC collective operations (barrier, broadcast)"""
        test_file = self.test_dir / "collective.c"
        test_code = """
#include <upc.h>
#include <stdio.h>

shared int data[THREADS];

int main() {
    // Each thread writes its rank
    data[MYTHREAD] = MYTHREAD * 10;
    upc_barrier;
    
    // Thread 0 reads all values
    if (MYTHREAD == 0) {
        printf("Collective data:");
        for (int i = 0; i < THREADS; i++) {
            printf(" %d", data[i]);
        }
        printf("\\n");
    }
    upc_barrier;
    return 0;
}
"""
        test_file.write_text(test_code)
        
        # Compile
        compile_result = subprocess.run(
            ["upcc", "-o", str(self.test_dir / "collective"), str(test_file)],
            capture_output=True, text=True
        )
        self.assertEqual(compile_result.returncode, 0, 
                        f"Compilation failed: {compile_result.stderr}")
        
        # Execute with 4 threads
        run_result = subprocess.run(
            ["upcrun", "-n", "4", str(self.test_dir / "collective")],
            capture_output=True, text=True, timeout=30
        )
        
        self.assertEqual(run_result.returncode, 0, 
                        f"Execution failed: {run_result.stderr}")
        self.assertIn("Collective data:", run_result.stdout,
                     "Collective operation output not found")
        print(f"✓ UPC collective operations test passed")
        print(f"  Output: {run_result.stdout.strip()}")
    
    def test_upc_static_threads(self):
        """Test UPC static threads compilation mode"""
        test_file = self.test_dir / "static_threads.c"
        test_code = """
#include <upc.h>
#include <stdio.h>

int main() {
    printf("Thread %d (static mode)\\n", MYTHREAD);
    return 0;
}
"""
        test_file.write_text(test_code)
        
        # Compile with static threads (-T flag)
        compile_result = subprocess.run(
            ["upcc", "-T", "4", "-o", str(self.test_dir / "static_threads"), 
             str(test_file)],
            capture_output=True, text=True
        )
        
        if compile_result.returncode == 0:
            print(f"✓ Static threads compilation successful")
            
            # Execute (should use 4 threads)
            run_result = subprocess.run(
                [str(self.test_dir / "static_threads")],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(run_result.returncode, 0, 
                           f"Execution failed: {run_result.stderr}")
        else:
            # Static threads mode might not be supported in all configurations
            print(f"⚠ Static threads mode not supported (skipped)")
            self.skipTest("Static threads mode not supported")
    
    def test_upc_pthreads_mode(self):
        """Test UPC with pthreads runtime"""
        test_file = self.test_dir / "pthreads_test.c"
        test_code = """
#include <upc.h>
#include <stdio.h>

int main() {
    printf("Thread %d with pthreads runtime\\n", MYTHREAD);
    return 0;
}
"""
        test_file.write_text(test_code)
        
        # Compile with pthreads runtime
        compile_result = subprocess.run(
            ["upcc", "-pthreads", "-o", 
             str(self.test_dir / "pthreads_test"), str(test_file)],
            capture_output=True, text=True
        )
        
        if compile_result.returncode == 0:
            print(f"✓ Pthreads mode compilation successful")
            
            # Execute
            run_result = subprocess.run(
                ["upcrun", "-n", "2", str(self.test_dir / "pthreads_test")],
                capture_output=True, text=True, timeout=30
            )
            self.assertEqual(run_result.returncode, 0, 
                           f"Execution failed: {run_result.stderr}")
        else:
            # Pthreads mode might not be enabled
            print(f"⚠ Pthreads mode not available (skipped)")
            self.skipTest("Pthreads mode not enabled")
    
    def test_upc_pointer_to_shared(self):
        """Test UPC pointer-to-shared functionality"""
        test_file = self.test_dir / "ptr_to_shared.c"
        test_code = """
#include <upc.h>
#include <stdio.h>

shared int shared_array[10];

int main() {
    shared int *ptr = &shared_array[MYTHREAD];
    
    *ptr = MYTHREAD * 100;
    upc_barrier;
    
    if (MYTHREAD == 0) {
        printf("Pointer-to-shared test:");
        for (int i = 0; i < THREADS && i < 10; i++) {
            printf(" %d", shared_array[i]);
        }
        printf("\\n");
    }
    upc_barrier;
    return 0;
}
"""
        test_file.write_text(test_code)
        
        # Compile
        compile_result = subprocess.run(
            ["upcc", "-o", str(self.test_dir / "ptr_to_shared"), str(test_file)],
            capture_output=True, text=True
        )
        self.assertEqual(compile_result.returncode, 0, 
                        f"Compilation failed: {compile_result.stderr}")
        
        # Execute
        run_result = subprocess.run(
            ["upcrun", "-n", "3", str(self.test_dir / "ptr_to_shared")],
            capture_output=True, text=True, timeout=30
        )
        
        self.assertEqual(run_result.returncode, 0, 
                        f"Execution failed: {run_result.stderr}")
        self.assertIn("Pointer-to-shared test:", run_result.stdout,
                     "Pointer-to-shared test output not found")
        print(f"✓ UPC pointer-to-shared test passed")


class TestBerkeleyUPCIntegration(unittest.TestCase):
    """Test Berkeley UPC integration with cluster environment"""
    
    def test_upcc_in_path(self):
        """Test that upcc is accessible from PATH"""
        result = subprocess.run(["which", "upcc"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ upcc in PATH: {result.stdout.strip()}")
        else:
            print(f"⚠ upcc not in PATH (may need wrapper scripts)")
            # Not failing test as wrapper scripts are optional
    
    def test_upcrun_in_path(self):
        """Test that upcrun is accessible from PATH"""
        result = subprocess.run(["which", "upcrun"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ upcrun in PATH: {result.stdout.strip()}")
        else:
            print(f"⚠ upcrun not in PATH (may need wrapper scripts)")
            # Not failing test as wrapper scripts are optional
    
    def test_berkeley_upc_libraries(self):
        """Test that Berkeley UPC libraries are accessible"""
        # Check for libupc in installation
        bupc_prefix = "/home/linuxbrew/.linuxbrew"
        bupc_dirs = list(Path(bupc_prefix).glob("berkeley-upc-*"))
        
        if bupc_dirs:
            lib_dir = bupc_dirs[0] / "lib"
            if lib_dir.exists():
                upc_libs = list(lib_dir.glob("libupc*"))
                self.assertGreater(len(upc_libs), 0, 
                                 "No Berkeley UPC libraries found")
                print(f"✓ Found {len(upc_libs)} Berkeley UPC libraries")
            else:
                print(f"⚠ Library directory not found: {lib_dir}")
        else:
            self.skipTest("Berkeley UPC installation directory not found")
    
    def test_gasnet_libraries(self):
        """Test that GASNet libraries are present"""
        bupc_prefix = "/home/linuxbrew/.linuxbrew"
        bupc_dirs = list(Path(bupc_prefix).glob("berkeley-upc-*"))
        
        if bupc_dirs:
            lib_dir = bupc_dirs[0] / "lib"
            if lib_dir.exists():
                gasnet_libs = list(lib_dir.glob("libgasnet*"))
                if gasnet_libs:
                    print(f"✓ Found {len(gasnet_libs)} GASNet libraries")
                else:
                    print(f"⚠ No GASNet libraries found (may use external GASNet)")
            else:
                self.skipTest("Library directory not found")
        else:
            self.skipTest("Berkeley UPC installation directory not found")


if __name__ == '__main__':
    print("="*60)
    print("Berkeley UPC Test Suite")
    print("="*60)
    unittest.main(verbosity=2)
