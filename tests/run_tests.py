#!/usr/bin/env python3
"""
Test Runner for ClusterSetupAndConfigs

Runs all unit tests and generates a report.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test modules
from tests import (
    test_cluster_setup,
    test_pgas,
    test_openmpi,
    test_openmp,
    test_openshmem,
    test_berkeley_upc,
    test_benchmarks,
    test_benchmark_templates,
    test_pdsh,
    test_ssh,
    test_sudo
)


def run_all_tests():
    """Run all test suites"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Discover and add all tests
    suite.addTests(loader.loadTestsFromModule(test_cluster_setup))
    suite.addTests(loader.loadTestsFromModule(test_pgas))
    suite.addTests(loader.loadTestsFromModule(test_openmpi))
    suite.addTests(loader.loadTestsFromModule(test_openmp))
    suite.addTests(loader.loadTestsFromModule(test_openshmem))
    suite.addTests(loader.loadTestsFromModule(test_berkeley_upc))
    suite.addTests(loader.loadTestsFromModule(test_benchmarks))
    suite.addTests(loader.loadTestsFromModule(test_benchmark_templates))
    suite.addTests(loader.loadTestsFromModule(test_pdsh))
    suite.addTests(loader.loadTestsFromModule(test_ssh))
    suite.addTests(loader.loadTestsFromModule(test_sudo))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 70)
    print("CLUSTERSSETUPANDCONFIGS TEST SUITE")
    print("=" * 70)
    print()
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
