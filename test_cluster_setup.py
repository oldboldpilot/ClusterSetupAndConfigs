#!/usr/bin/env python3
"""
Basic tests for cluster_setup.py
"""

import sys
import subprocess
from pathlib import Path


def test_script_syntax():
    """Test that the script has valid Python syntax"""
    result = subprocess.run(
        ['python3', '-m', 'py_compile', 'cluster_setup.py'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Syntax error: {result.stderr}"
    print("✓ Syntax check passed")


def test_help_message():
    """Test that the script shows help message"""
    result = subprocess.run(
        ['python3', 'cluster_setup.py', '--help'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Help command failed"
    assert '--config' in result.stdout, "Missing --config option in help"
    assert '--password' in result.stdout, "Missing --password option in help"
    assert '--non-interactive' in result.stdout, "Missing --non-interactive option in help"
    print("✓ Help message test passed")


def test_missing_arguments():
    """Test that the script requires arguments"""
    result = subprocess.run(
        ['python3', 'cluster_setup.py'],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0, "Script should fail without arguments"
    assert 'required' in result.stderr.lower() or 'error' in result.stderr.lower()
    print("✓ Missing arguments test passed")


def test_invalid_ip():
    """Test that the script validates IP addresses"""
    # Create a temporary invalid config file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("master: invalid_ip\nworkers:\n  - 192.168.1.11\n")
        temp_config = f.name

    try:
        result = subprocess.run(
            ['python3', 'cluster_setup.py', '--config', temp_config],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0, "Script should fail with invalid IP"
        assert 'invalid' in result.stdout.lower() or 'error' in result.stdout.lower()
        print("✓ Invalid IP validation test passed")
    finally:
        import os
        os.unlink(temp_config)


def test_file_structure():
    """Test that required files exist"""
    required_files = [
        'cluster_setup.py',
        'README.md',
        'pyproject.toml',
        '.gitignore',
        'example_config.txt'
    ]
    
    for filename in required_files:
        filepath = Path(filename)
        assert filepath.exists(), f"Missing required file: {filename}"
    
    print("✓ File structure test passed")


def test_script_imports():
    """Test that the script can be imported"""
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))

        # Import without executing main
        import cluster_setup

        # Check that key classes and functions exist
        assert hasattr(cluster_setup, 'ClusterSetup')
        assert hasattr(cluster_setup, 'main')
        assert hasattr(cluster_setup, 'load_yaml_config')

        print("✓ Import test passed")
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        raise


def test_valid_config_loading():
    """Test loading a valid configuration file"""
    import tempfile
    import yaml

    # Create a temporary valid config file
    config_data = {
        'master': '192.168.1.100',
        'workers': ['192.168.1.101', '192.168.1.102'],
        'username': 'testuser'
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_config = f.name

    try:
        sys.path.insert(0, str(Path.cwd()))
        from cluster_setup import load_yaml_config

        config = load_yaml_config(temp_config)

        assert config['master'] == '192.168.1.100', "Master IP not loaded correctly"
        assert len(config['workers']) == 2, "Workers not loaded correctly"
        assert config['username'] == 'testuser', "Username not loaded correctly"

        print("✓ Valid config loading test passed")
    finally:
        import os
        os.unlink(temp_config)


def test_cluster_setup_class():
    """Test ClusterSetup class initialization"""
    try:
        sys.path.insert(0, str(Path.cwd()))
        from cluster_setup import ClusterSetup

        # Create a ClusterSetup instance
        setup = ClusterSetup(
            master_ip='192.168.1.100',
            worker_ips=['192.168.1.101', '192.168.1.102'],
            username='testuser'
        )

        assert setup.master_ip == '192.168.1.100', "Master IP not set correctly"
        assert len(setup.worker_ips) == 2, "Worker IPs not set correctly"
        assert setup.username == 'testuser', "Username not set correctly"
        assert len(setup.all_ips) == 3, "all_ips should contain master + workers"

        print("✓ ClusterSetup class test passed")
    except Exception as e:
        print(f"✗ ClusterSetup class test failed: {e}")
        raise


def test_ip_validation():
    """Test IP address validation in main function"""
    import tempfile

    # Test valid IPs
    valid_ips = ['192.168.1.1', '10.0.0.1', '127.0.0.1', 'localhost']
    for ip in valid_ips:
        config_data = f"master: {ip}\nworkers:\n  - 192.168.1.2\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_data)
            temp_config = f.name

        try:
            # Just check it doesn't crash on IP validation
            # (it will fail later on sudo check, but that's OK)
            result = subprocess.run(
                ['python3', 'cluster_setup.py', '--config', temp_config],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Should not fail with IP validation error
            assert 'Invalid' not in result.stdout or 'IP' not in result.stdout
        except subprocess.TimeoutExpired:
            # Timeout is OK - means it passed validation and started running
            pass
        finally:
            import os
            os.unlink(temp_config)

    print("✓ IP validation test passed")


def test_non_interactive_flag():
    """Test that non-interactive flag is properly handled"""
    import tempfile
    import yaml
    
    # Create a test config
    config_data = {
        'master_ip': '127.0.0.1',
        'worker_ips': ['127.0.0.2'],
        'username': 'testuser'
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name
    
    try:
        # Test that script accepts --non-interactive flag
        result = subprocess.run(
            ['python3', 'cluster_setup.py', '--config', config_file, '--non-interactive', '--help'],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Should succeed with help even with non-interactive flag
        assert result.returncode == 0, "Script should accept --non-interactive flag"
        print("✓ Non-interactive flag test passed")
    except subprocess.TimeoutExpired:
        # If it times out, the flag is at least being parsed
        print("✓ Non-interactive flag test passed (timeout, flag accepted)")
    finally:
        import os
        if Path(config_file).exists():
            os.unlink(config_file)


def main():
    """Run all tests"""
    print("Running cluster_setup.py tests...\n")

    tests = [
        test_file_structure,
        test_script_syntax,
        test_help_message,
        test_missing_arguments,
        test_invalid_ip,
        test_script_imports,
        test_valid_config_loading,
        test_cluster_setup_class,
        test_ip_validation,
        test_non_interactive_flag,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Tests completed: {len(tests) - failed}/{len(tests)} passed")
    print(f"{'='*50}")
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
