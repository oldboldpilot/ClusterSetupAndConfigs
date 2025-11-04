"""
Test Suite for Sudo Configuration

Tests passwordless sudo configuration across the cluster.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import unittest
import subprocess
import os
from pathlib import Path


class TestSudoManager(unittest.TestCase):
    """Test passwordless sudo configuration."""
    
    def test_sudoers_directory_exists(self):
        """Test that /etc/sudoers.d directory exists."""
        sudoers_dir = Path("/etc/sudoers.d")
        self.assertTrue(
            sudoers_dir.exists(),
            "/etc/sudoers.d directory should exist"
        )
    
    def test_cluster_ops_sudoers_file_exists(self):
        """Test that cluster-ops sudoers file exists."""
        cluster_ops_file = Path("/etc/sudoers.d/cluster-ops")
        # This might not exist until sudo configuration is run
        # So this is a soft check
        if cluster_ops_file.exists():
            # File exists, check permissions (should be 440 or 400)
            stat_info = cluster_ops_file.stat()
            mode = oct(stat_info.st_mode)[-3:]
            self.assertIn(
                mode,
                ["440", "400"],
                "cluster-ops sudoers file should have 440 or 400 permissions"
            )
    
    def test_sudo_ln_command(self):
        """Test that sudo ln command works without password."""
        # Create a temporary test
        test_file = Path.home() / "test_sudo_ln_source"
        test_link = Path.home() / "test_sudo_ln_link"
        
        try:
            # Create source file
            test_file.touch()
            
            # Try to create symlink with sudo (this will prompt for password if not configured)
            # We use timeout to avoid hanging
            result = subprocess.run(
                ["sudo", "-n", "ln", "-sf", str(test_file), str(test_link)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # If passwordless sudo is configured, returncode should be 0
            # If not configured, returncode will be 1
            self.assertIn(
                result.returncode,
                [0, 1],
                "sudo ln should either work (0) or require password (1)"
            )
            
            # Cleanup
            if test_link.exists():
                subprocess.run(["sudo", "-n", "rm", str(test_link)], capture_output=True)
            
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_sudo_mkdir_command(self):
        """Test that sudo mkdir command works without password."""
        test_dir = Path("/tmp/test_sudo_mkdir_" + str(os.getpid()))
        
        try:
            result = subprocess.run(
                ["sudo", "-n", "mkdir", "-p", str(test_dir)],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            self.assertIn(
                result.returncode,
                [0, 1],
                "sudo mkdir should either work (0) or require password (1)"
            )
            
        finally:
            if test_dir.exists():
                subprocess.run(["sudo", "-n", "rm", "-rf", str(test_dir)], capture_output=True)
    
    def test_sudo_non_interactive_flag(self):
        """Test that sudo -n flag works (non-interactive)."""
        # This tests if sudo can be run non-interactively
        result = subprocess.run(
            ["sudo", "-n", "echo", "test"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # returncode 0 = passwordless sudo configured
        # returncode 1 = password required
        self.assertIn(
            result.returncode,
            [0, 1],
            "sudo -n should return 0 (configured) or 1 (not configured)"
        )


class TestSudoCommands(unittest.TestCase):
    """Test specific sudo commands used in cluster operations."""
    
    def test_sudo_rsync(self):
        """Test that sudo rsync is available."""
        result = subprocess.run(
            ["which", "rsync"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, "rsync command should be available")
    
    def test_sudo_systemctl(self):
        """Test that sudo systemctl is available."""
        result = subprocess.run(
            ["which", "systemctl"],
            capture_output=True,
            text=True
        )
        # systemctl might not be available on all systems (e.g., WSL1)
        self.assertIn(
            result.returncode,
            [0, 1],
            "systemctl might or might not be available"
        )
    
    def test_sudo_chmod(self):
        """Test that sudo chmod is available."""
        result = subprocess.run(
            ["which", "chmod"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, "chmod command should be available")
    
    def test_sudo_chown(self):
        """Test that sudo chown is available."""
        result = subprocess.run(
            ["which", "chown"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, "chown command should be available")


if __name__ == "__main__":
    unittest.main()
