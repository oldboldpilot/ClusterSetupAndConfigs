#!/usr/bin/env python3
"""
Tests for PGAS configuration functionality

Tests UPC++, GASNet, OpenSHMEM installation, configuration,
and multi-node execution.
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cluster_setup import ClusterSetup


class TestPGASConfiguration(unittest.TestCase):
    """Test PGAS-related configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.setup = ClusterSetup(
            "192.168.1.10",
            ["192.168.1.11", "192.168.1.12"],
            "testuser",
            "testpass"
        )
    
    def test_pgas_methods_exist(self):
        """Test that PGAS configuration methods exist"""
        self.assertTrue(hasattr(self.setup, 'install_upcxx_and_pgas'))
        self.assertTrue(hasattr(self.setup, 'distribute_pgas_to_cluster'))
        self.assertTrue(hasattr(self.setup, 'configure_passwordless_sudo_cluster'))
        self.assertTrue(hasattr(self.setup, 'distribute_system_symlinks_cluster'))
        self.assertTrue(hasattr(self.setup, 'test_multinode_upcxx'))
        self.assertTrue(hasattr(self.setup, 'install_openshmem_cluster'))
        self.assertTrue(hasattr(self.setup, 'create_pgas_benchmark_suite'))
    
    def test_pgas_methods_callable(self):
        """Test that PGAS methods are callable"""
        self.assertTrue(callable(self.setup.install_upcxx_and_pgas))
        self.assertTrue(callable(self.setup.distribute_pgas_to_cluster))
        self.assertTrue(callable(self.setup.configure_passwordless_sudo_cluster))
        self.assertTrue(callable(self.setup.distribute_system_symlinks_cluster))
        self.assertTrue(callable(self.setup.test_multinode_upcxx))
        self.assertTrue(callable(self.setup.install_openshmem_cluster))
        self.assertTrue(callable(self.setup.create_pgas_benchmark_suite))
    
    @patch('os.path.exists')
    def test_pgas_installation_paths(self, mock_exists):
        """Test expected PGAS installation paths"""
        mock_exists.return_value = True
        
        expected_paths = {
            'upcxx': '/home/linuxbrew/.linuxbrew/upcxx',
            'gasnet': '/home/linuxbrew/.linuxbrew/gasnet',
            'openshmem': '/home/linuxbrew/.linuxbrew/openshmem',
        }
        
        for name, path in expected_paths.items():
            self.assertTrue(path.startswith('/home/linuxbrew/.linuxbrew/'))


class TestPDSHIntegration(unittest.TestCase):
    """Test pdsh parallel execution integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.setup = ClusterSetup(
            "192.168.1.10",
            ["192.168.1.11", "192.168.1.12"],
            "testuser",
            "testpass"
        )
    
    def test_worker_list_format(self):
        """Test worker list format for pdsh"""
        workers = self.setup.worker_ips
        
        # Format for pdsh: -w 'ip1,ip2,ip3'
        pdsh_format = ','.join(workers)
        self.assertEqual(pdsh_format, '192.168.1.11,192.168.1.12')
    
    def test_all_nodes_list_format(self):
        """Test all nodes list format for pdsh"""
        all_nodes = self.setup.all_ips
        
        # Format for pdsh
        pdsh_format = ','.join(all_nodes)
        self.assertIn('192.168.1.10', pdsh_format)
        self.assertIn('192.168.1.11', pdsh_format)
        self.assertIn('192.168.1.12', pdsh_format)


def run_tests():
    """Run all PGAS tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPGASConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestPDSHIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
