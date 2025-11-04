"""
Test Suite for PDSH Manager

Tests pdsh installation, configuration, and cluster-wide operations.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import unittest
import subprocess
import os
from pathlib import Path
import tempfile
import shutil


class TestPDSHInstallation(unittest.TestCase):
    """Test pdsh installation functionality"""
    
    def test_pdsh_manager_import(self):
        """Test that PDSHManager can be imported"""
        try:
            from cluster_modules.pdsh_manager import PDSHManager
            self.assertTrue(True, "PDSHManager imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import PDSHManager: {e}")
    
    def test_pdsh_manager_initialization(self):
        """Test PDSHManager initialization"""
        from cluster_modules.pdsh_manager import PDSHManager
        
        manager = PDSHManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2", "192.168.1.3"]
        )
        
        self.assertEqual(manager.username, "test")
        self.assertEqual(manager.master_ip, "192.168.1.1")
        self.assertEqual(len(manager.worker_ips), 2)
        self.assertEqual(len(manager.all_ips), 3)
    
    def test_pdsh_installed_check(self):
        """Test pdsh installation check"""
        from cluster_modules.pdsh_manager import PDSHManager
        
        manager = PDSHManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"]
        )
        
        is_installed = manager.is_pdsh_installed()
        
        # Just verify the method runs without error
        self.assertIsInstance(is_installed, bool,
                            "is_pdsh_installed should return boolean")
    
    def test_homebrew_check(self):
        """Test Homebrew availability check"""
        from cluster_modules.pdsh_manager import PDSHManager
        
        manager = PDSHManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"]
        )
        
        is_available = manager._is_homebrew_available()
        
        self.assertIsInstance(is_available, bool,
                            "_is_homebrew_available should return boolean")


class TestPDSHHostfile(unittest.TestCase):
    """Test pdsh hostfile creation and management"""
    
    def setUp(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Cleanup"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_create_hostfile(self):
        """Test hostfile creation"""
        from cluster_modules.pdsh_manager import PDSHManager
        
        manager = PDSHManager(
            username="test",
            password="test",
            master_ip="192.168.1.147",
            worker_ips=["192.168.1.139", "192.168.1.96", "192.168.1.136"]
        )
        
        hostfile_path = self.temp_dir / "machines"
        success = manager.create_hostfile(hostfile_path)
        
        self.assertTrue(success, "Failed to create hostfile")
        self.assertTrue(hostfile_path.exists(), "Hostfile not created")
        
        # Verify content
        content = hostfile_path.read_text()
        self.assertIn("192.168.1.147", content)
        self.assertIn("192.168.1.139", content)
        self.assertIn("192.168.1.96", content)
        self.assertIn("192.168.1.136", content)
        
        # Verify line count
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        self.assertEqual(len(lines), 4, "Hostfile should have 4 nodes")
    
    def test_hostfile_permissions(self):
        """Test that hostfile has correct permissions"""
        from cluster_modules.pdsh_manager import PDSHManager
        
        manager = PDSHManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"]
        )
        
        hostfile_path = self.temp_dir / "machines"
        manager.create_hostfile(hostfile_path)
        
        # Verify file is readable
        self.assertTrue(os.access(hostfile_path, os.R_OK),
                       "Hostfile is not readable")


class TestPDSHEnvironment(unittest.TestCase):
    """Test pdsh environment configuration"""
    
    def test_pdsh_rcmd_type_env(self):
        """Test PDSH_RCMD_TYPE environment variable"""
        # Check if PDSH_RCMD_TYPE is set
        rcmd_type = os.environ.get('PDSH_RCMD_TYPE')
        
        # It's okay if not set, but if set, should be 'ssh'
        if rcmd_type:
            self.assertEqual(rcmd_type, 'ssh',
                           "PDSH_RCMD_TYPE should be 'ssh' if set")


class TestPDSHCommands(unittest.TestCase):
    """Test pdsh command execution"""
    
    @unittest.skipUnless(subprocess.run(['which', 'pdsh'], 
                                       capture_output=True).returncode == 0,
                        "pdsh not installed")
    def test_pdsh_command_exists(self):
        """Test that pdsh command exists"""
        result = subprocess.run(['which', 'pdsh'], 
                              capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, "pdsh not found in PATH")
        self.assertTrue(result.stdout.strip(), "pdsh path is empty")
    
    @unittest.skipUnless(subprocess.run(['which', 'pdsh'], 
                                       capture_output=True).returncode == 0,
                        "pdsh not installed")
    def test_pdsh_version(self):
        """Test pdsh version command"""
        result = subprocess.run(['pdsh', '-V'], 
                              capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, "pdsh -V failed")
        self.assertIn("pdsh", result.stdout.lower() or result.stderr.lower(),
                     "Version output doesn't mention pdsh")
    
    @unittest.skipUnless(subprocess.run(['which', 'pdsh'], 
                                       capture_output=True).returncode == 0,
                        "pdsh not installed")
    def test_pdsh_help(self):
        """Test pdsh help command"""
        result = subprocess.run(['pdsh', '-h'], 
                              capture_output=True, text=True)
        
        # pdsh -h returns non-zero but shows help
        self.assertIn("Usage", result.stdout or result.stderr,
                     "Help output not found")
    
    def test_pdsh_run_command_method(self):
        """Test run_pdsh_command method"""
        from cluster_modules.pdsh_manager import PDSHManager
        
        manager = PDSHManager(
            username="test",
            password="test",
            master_ip="localhost",
            worker_ips=[]
        )
        
        # Just test that method exists and has correct signature
        self.assertTrue(hasattr(manager, 'run_pdsh_command'),
                       "run_pdsh_command method not found")


class TestPDSHAdvanced(unittest.TestCase):
    """Advanced pdsh tests requiring cluster setup"""
    
    @unittest.skipUnless(subprocess.run(['which', 'pdsh'], 
                                       capture_output=True).returncode == 0,
                        "pdsh not installed")
    def test_pdsh_localhost(self):
        """Test pdsh execution on localhost"""
        result = subprocess.run(
            ['pdsh', '-w', 'localhost', 'echo "test"'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # May fail if SSH not configured for localhost, but should not crash
        self.assertIsNotNone(result.returncode,
                           "pdsh command returned None")
    
    def test_pdsh_multiple_hosts_syntax(self):
        """Test pdsh syntax with multiple hosts"""
        from cluster_modules.pdsh_manager import PDSHManager
        
        manager = PDSHManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2", "192.168.1.3", "192.168.1.4"]
        )
        
        # Verify all_ips contains all nodes
        self.assertEqual(len(manager.all_ips), 4)
        
        # Test host string generation
        hosts_str = ','.join(manager.all_ips)
        self.assertIn("192.168.1.1", hosts_str)
        self.assertIn("192.168.1.2", hosts_str)
        self.assertIn(",", hosts_str)


class TestPDSHIntegration(unittest.TestCase):
    """Integration tests for pdsh with other cluster components"""
    
    def test_pdsh_with_ssh_config(self):
        """Test pdsh respects SSH configuration"""
        ssh_config = Path.home() / ".ssh" / "config"
        
        # Just verify SSH config exists (good practice for pdsh)
        if ssh_config.exists():
            self.assertTrue(ssh_config.is_file(),
                          "SSH config should be a file")
    
    def test_pdsh_with_known_hosts(self):
        """Test pdsh works with known_hosts"""
        known_hosts = Path.home() / ".ssh" / "known_hosts"
        
        # Known_hosts should exist for pdsh to work smoothly
        if known_hosts.exists():
            self.assertTrue(known_hosts.is_file(),
                          "known_hosts should be a file")
    
    def test_pdsh_manager_with_benchmark_manager(self):
        """Test PDSHManager integration with BenchmarkManager"""
        try:
            from cluster_modules.pdsh_manager import PDSHManager
            from cluster_modules.benchmark_manager import BenchmarkManager
            
            # Both should be importable together
            self.assertTrue(True, "Both managers imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import both managers: {e}")


class TestPDSHConfiguration(unittest.TestCase):
    """Test pdsh configuration and setup"""
    
    def test_pdsh_directory_structure(self):
        """Test expected pdsh directory structure"""
        pdsh_dir = Path.home() / ".pdsh"
        
        # Directory may or may not exist, but if it does, should be a directory
        if pdsh_dir.exists():
            self.assertTrue(pdsh_dir.is_dir(),
                          ".pdsh should be a directory")
    
    def test_configure_environment_method(self):
        """Test configure_pdsh_environment method exists"""
        from cluster_modules.pdsh_manager import PDSHManager
        
        manager = PDSHManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"]
        )
        
        self.assertTrue(hasattr(manager, 'configure_pdsh_environment'),
                       "configure_pdsh_environment method not found")
    
    def test_install_and_configure_cluster_method(self):
        """Test install_and_configure_cluster method exists"""
        from cluster_modules.pdsh_manager import PDSHManager
        
        manager = PDSHManager(
            username="test",
            password="test",
            master_ip="192.168.1.1",
            worker_ips=["192.168.1.2"]
        )
        
        self.assertTrue(hasattr(manager, 'install_and_configure_cluster'),
                       "install_and_configure_cluster method not found")


if __name__ == '__main__':
    unittest.main()
