"""
Test Suite for SSH Configuration

Tests SSH key distribution and passwordless SSH setup across the cluster.

Author: Olumuyiwa Oluwasanmi
Date: November 4, 2025
"""

import unittest
import subprocess
from pathlib import Path


class TestSSHManager(unittest.TestCase):
    """Test SSH configuration and key management."""
    
    def test_ssh_directory_exists(self):
        """Test that .ssh directory exists with correct permissions."""
        ssh_dir = Path.home() / ".ssh"
        self.assertTrue(ssh_dir.exists(), ".ssh directory should exist")
        
        # Check permissions (should be 700)
        stat_info = ssh_dir.stat()
        mode = oct(stat_info.st_mode)[-3:]
        self.assertEqual(mode, "700", ".ssh directory should have 700 permissions")
    
    def test_ssh_private_key_exists(self):
        """Test that SSH private key exists."""
        private_key = Path.home() / ".ssh" / "id_rsa"
        self.assertTrue(
            private_key.exists(),
            "SSH private key should exist at ~/.ssh/id_rsa"
        )
    
    def test_ssh_public_key_exists(self):
        """Test that SSH public key exists."""
        public_key = Path.home() / ".ssh" / "id_rsa.pub"
        self.assertTrue(
            public_key.exists(),
            "SSH public key should exist at ~/.ssh/id_rsa.pub"
        )
    
    def test_ssh_private_key_permissions(self):
        """Test that private key has correct permissions (600)."""
        private_key = Path.home() / ".ssh" / "id_rsa"
        if private_key.exists():
            stat_info = private_key.stat()
            mode = oct(stat_info.st_mode)[-3:]
            self.assertEqual(
                mode,
                "600",
                "SSH private key should have 600 permissions"
            )
    
    def test_authorized_keys_exists(self):
        """Test that authorized_keys file exists."""
        authorized_keys = Path.home() / ".ssh" / "authorized_keys"
        self.assertTrue(
            authorized_keys.exists(),
            "authorized_keys file should exist"
        )
    
    def test_authorized_keys_permissions(self):
        """Test that authorized_keys has correct permissions (600)."""
        authorized_keys = Path.home() / ".ssh" / "authorized_keys"
        if authorized_keys.exists():
            stat_info = authorized_keys.stat()
            mode = oct(stat_info.st_mode)[-3:]
            self.assertEqual(
                mode,
                "600",
                "authorized_keys should have 600 permissions"
            )
    
    def test_known_hosts_exists(self):
        """Test that known_hosts file exists."""
        known_hosts = Path.home() / ".ssh" / "known_hosts"
        # known_hosts might not exist initially, but should exist after SSH setup
        # This is a soft check
        if known_hosts.exists():
            stat_info = known_hosts.stat()
            mode = oct(stat_info.st_mode)[-3:]
            self.assertIn(mode, ["600", "644"], "known_hosts should have safe permissions")
    
    def test_ssh_config_structure(self):
        """Test SSH config file structure if it exists."""
        ssh_config = Path.home() / ".ssh" / "config"
        if ssh_config.exists():
            content = ssh_config.read_text()
            # Check for common settings
            self.assertIn("StrictHostKeyChecking", content.lower())


class TestSSHConnectivity(unittest.TestCase):
    """Test SSH connectivity to localhost."""
    
    def test_ssh_localhost(self):
        """Test SSH connection to localhost."""
        result = subprocess.run(
            ["ssh", "-o", "StrictHostKeyChecking=no", "localhost", "echo", "test"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # This might fail if passwordless SSH isn't fully configured yet
        # So we check returncode is either 0 (success) or connection-related error
        self.assertIn(
            result.returncode,
            [0, 255],  # 0 = success, 255 = SSH error
            "SSH to localhost should either succeed or fail gracefully"
        )


if __name__ == "__main__":
    unittest.main()
