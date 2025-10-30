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
    assert '--master' in result.stdout, "Missing --master option in help"
    assert '--workers' in result.stdout, "Missing --workers option in help"
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
    result = subprocess.run(
        ['python3', 'cluster_setup.py', '--master', 'invalid', '--workers', '192.168.1.11'],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0, "Script should fail with invalid IP"
    print("✓ Invalid IP validation test passed")


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
        
        # Check that key classes exist
        assert hasattr(cluster_setup, 'ClusterSetup')
        assert hasattr(cluster_setup, 'main')
        
        print("✓ Import test passed")
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        raise


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
