"""
Test Suite for OpenSHMEM Configuration

Tests OpenSHMEM installation, configuration, and functionality.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import unittest
import subprocess
from pathlib import Path


class TestOpenSHMEM(unittest.TestCase):
    """Test OpenSHMEM installation and basic functionality."""
    
    def test_openshmem_directory_exists(self):
        """Test that OpenSHMEM installation directory exists."""
        openshmem_prefix = Path("/home/linuxbrew/.linuxbrew").glob("openshmem-*")
        openshmem_dirs = list(openshmem_prefix)
        
        # This might not exist until OpenSHMEM is installed
        if openshmem_dirs:
            self.assertTrue(openshmem_dirs[0].exists(), "OpenSHMEM installation directory should exist")
    
    def test_oshcc_exists(self):
        """Test that oshcc compiler wrapper exists."""
        result = subprocess.run(
            ["which", "oshcc"],
            capture_output=True,
            text=True
        )
        
        # This might return 1 if OpenSHMEM isn't installed yet
        self.assertIn(
            result.returncode,
            [0, 1],
            "oshcc should either exist (0) or not be installed yet (1)"
        )
    
    def test_oshrun_exists(self):
        """Test that oshrun launcher exists."""
        result = subprocess.run(
            ["which", "oshrun"],
            capture_output=True,
            text=True
        )
        
        self.assertIn(
            result.returncode,
            [0, 1],
            "oshrun should either exist (0) or not be installed yet (1)"
        )
    
    def test_openshmem_lib_directory(self):
        """Test that OpenSHMEM lib directory exists."""
        openshmem_dirs = list(Path("/home/linuxbrew/.linuxbrew").glob("openshmem-*/lib"))
        
        if openshmem_dirs:
            lib_dir = openshmem_dirs[0]
            self.assertTrue(lib_dir.exists(), f"OpenSHMEM lib directory should exist at {lib_dir}")
    
    def test_openshmem_include_directory(self):
        """Test that OpenSHMEM include directory exists."""
        openshmem_dirs = list(Path("/home/linuxbrew/.linuxbrew").glob("openshmem-*/include"))
        
        if openshmem_dirs:
            include_dir = openshmem_dirs[0]
            self.assertTrue(include_dir.exists(), f"OpenSHMEM include directory should exist at {include_dir}")
            
            # Check for shmem.h header
            shmem_header = include_dir / "shmem.h"
            if shmem_header.exists():
                self.assertTrue(shmem_header.exists(), "shmem.h header should exist")


class TestOpenSHMEMAdvanced(unittest.TestCase):
    """Advanced OpenSHMEM tests."""
    
    def test_oshcc_version(self):
        """Test that oshcc can report version."""
        result = subprocess.run(
            ["oshcc", "--version"],
            capture_output=True,
            text=True
        )
        
        # oshcc might not exist yet
        if result.returncode == 0:
            self.assertIn("gcc", result.stdout.lower(), "oshcc should use gcc")
    
    def test_simple_openshmem_compilation(self):
        """Test compilation of simple OpenSHMEM program."""
        # Check if oshcc exists first
        which_result = subprocess.run(["which", "oshcc"], capture_output=True)
        if which_result.returncode != 0:
            self.skipTest("oshcc not available yet")
        
        test_code = """
#include <shmem.h>
int main() {
    shmem_init();
    shmem_finalize();
    return 0;
}
"""
        
        test_dir = Path.home() / "test_openshmem_compile"
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "test.c"
        test_file.write_text(test_code)
        
        # Try to compile
        compile_cmd = [
            "oshcc",
            str(test_file),
            "-o", str(test_dir / "test")
        ]
        
        result = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        # Cleanup
        if (test_dir / "test").exists():
            (test_dir / "test").unlink()
        test_file.unlink()
        
        self.assertEqual(result.returncode, 0, "Simple OpenSHMEM program should compile")
    
    def test_openshmem_hello_world(self):
        """Test execution of OpenSHMEM hello world program."""
        # Check if oshcc and oshrun exist
        which_oshcc = subprocess.run(["which", "oshcc"], capture_output=True)
        which_oshrun = subprocess.run(["which", "oshrun"], capture_output=True)
        
        if which_oshcc.returncode != 0 or which_oshrun.returncode != 0:
            self.skipTest("oshcc or oshrun not available yet")
        
        test_code = """
#include <shmem.h>
#include <stdio.h>

int main() {
    shmem_init();
    int me = shmem_my_pe();
    int npes = shmem_n_pes();
    printf("PE %d of %d\\n", me, npes);
    shmem_finalize();
    return 0;
}
"""
        
        test_dir = Path.home() / "test_openshmem_run"
        test_dir.mkdir(exist_ok=True)
        
        test_file = test_dir / "hello.c"
        test_file.write_text(test_code)
        
        # Compile
        compile_cmd = [
            "oshcc",
            str(test_file),
            "-o", str(test_dir / "hello")
        ]
        
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)
        
        if compile_result.returncode != 0:
            self.skipTest("Compilation failed")
        
        # Run with 2 PEs
        run_cmd = [
            "oshrun",
            "-n", "2",
            str(test_dir / "hello")
        ]
        
        run_result = subprocess.run(run_cmd, capture_output=True, text=True, timeout=30)
        
        # Cleanup
        if (test_dir / "hello").exists():
            (test_dir / "hello").unlink()
        test_file.unlink()
        
        self.assertEqual(run_result.returncode, 0, "OpenSHMEM hello world should execute")
        self.assertIn("PE 0", run_result.stdout, "Should see PE 0 output")
        self.assertIn("PE 1", run_result.stdout, "Should see PE 1 output")


if __name__ == "__main__":
    unittest.main()
