#!/usr/bin/env python3
"""
Test Runner for Compass Framework

Provides convenient commands to run different categories of tests:
- Unit tests: Individual component testing
- Integration tests: Multi-component interaction testing  
- E2E tests: End-to-end browser automation testing
- All tests: Complete test suite
"""

import sys
import unittest
import argparse
from pathlib import Path


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="Compass Framework Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Categories:
  unit        - Unit tests (individual components)
  integration - Integration tests (multi-component)
  e2e         - End-to-end tests (browser automation) 
  all         - All tests (default)

Examples:
  python run_tests.py unit                 # Run only unit tests
  python run_tests.py integration          # Run only integration tests
  python run_tests.py e2e                  # Run only E2E tests (with E2E enabled)
  python run_tests.py all                  # Run all tests
  python run_tests.py --enable-e2e all     # Run all tests including E2E
        """
    )
    
    parser.add_argument(
        'category', 
        nargs='?', 
        default='all',
        choices=['unit', 'integration', 'e2e', 'all'],
        help='Test category to run (default: all)'
    )
    
    parser.add_argument(
        '--enable-e2e', 
        action='store_true',
        help='Enable E2E tests (requires browser setup)'
    )
    
    parser.add_argument(
        '-v', '--verbose', 
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Enable E2E tests if requested
    if args.enable_e2e or args.category == 'e2e':
        unittest._e2e_enabled = True
        print("🌐 E2E tests enabled")
    
    # Determine test directory based on category
    if args.category == 'unit':
        test_dir = 'tests/unit'
    elif args.category == 'integration':
        test_dir = 'tests/integration'
    elif args.category == 'e2e':
        test_dir = 'tests/e2e'
        if not args.enable_e2e:
            unittest._e2e_enabled = True
    else:  # all
        test_dir = 'tests'
    
    print(f"🧪 Running {args.category} tests from {test_dir}/")
    
    # Configure test loader and runner
    loader = unittest.TestLoader()
    runner = unittest.TextTestRunner(verbosity=2 if args.verbose else 1)
    
    # Discover and run tests
    suite = loader.discover(test_dir, pattern='test_*.py')
    result = runner.run(suite)
    
    # Print summary
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    
    print(f"\n{'='*60}")
    print(f"📊 Test Summary ({args.category})")
    print(f"{'='*60}")
    print(f"Tests run:     {tests_run}")
    print(f"Passed:        {tests_run - failures - errors}")
    print(f"Failed:        {failures}")
    print(f"Errors:        {errors}")
    print(f"Skipped:       {skipped}")
    
    if failures == 0 and errors == 0:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()