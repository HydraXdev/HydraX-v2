#!/usr/bin/env python3
"""
Comprehensive Test Runner for TCS++ and Stealth Protocol
Runs all tests and generates detailed reports
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestRunner:
    """Main test runner class"""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results = {
            'start_time': datetime.now().isoformat(),
            'test_suites': {},
            'summary': {
                'total_tests': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0,
                'duration': 0
            }
        }
        
    def run_test_suite(self, test_file: str, verbose: bool = True) -> dict:
        """Run a single test suite"""
        print(f"\n{'='*60}")
        print(f"Running: {test_file}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Construct pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            str(self.test_dir / test_file),
            '-v' if verbose else '-q',
            '--tb=short',
            '--color=yes',
            '-x'  # Stop on first failure
        ]
        
        # Add coverage if available
        try:
            import coverage
            cmd.extend(['--cov=core', '--cov=src.bitten_core', '--cov-report=term-missing'])
        except ImportError:
            pass
        
        # Run tests
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start_time
        
        # Parse results
        suite_results = {
            'file': test_file,
            'duration': duration,
            'return_code': result.returncode,
            'passed': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr
        }
        
        # Extract test counts from output
        if 'passed' in result.stdout:
            import re
            match = re.search(r'(\d+) passed', result.stdout)
            if match:
                suite_results['test_count'] = int(match.group(1))
            else:
                suite_results['test_count'] = 0
        else:
            suite_results['test_count'] = 0
            
        return suite_results
    
    def run_all_tests(self):
        """Run all test suites"""
        print(f"\nTCS++ and Stealth Protocol Test Suite")
        print(f"Started at: {self.results['start_time']}")
        
        # Define test suites in order
        test_suites = [
            # Unit tests
            ('test_tcs_plus_engine.py', 'TCS++ Engine Tests'),
            ('test_stealth_protocol_comprehensive.py', 'Stealth Protocol Tests'),
            
            # Integration tests
            ('integration/test_tcs_stealth_integration.py', 'TCS++/Stealth Integration'),
            
            # Performance tests
            ('test_performance_benchmarks.py', 'Performance Benchmarks'),
        ]
        
        total_start = time.time()
        
        for test_file, description in test_suites:
            print(f"\n\n{'#'*60}")
            print(f"# {description}")
            print(f"{'#'*60}")
            
            try:
                results = self.run_test_suite(test_file)
                self.results['test_suites'][test_file] = results
                
                if results['passed']:
                    self.results['summary']['passed'] += results.get('test_count', 1)
                    print(f"\n✓ {description} - PASSED")
                else:
                    self.results['summary']['failed'] += 1
                    print(f"\n✗ {description} - FAILED")
                    
            except Exception as e:
                print(f"\n✗ {description} - ERROR: {str(e)}")
                self.results['test_suites'][test_file] = {
                    'file': test_file,
                    'error': str(e),
                    'passed': False
                }
                self.results['summary']['failed'] += 1
        
        self.results['summary']['duration'] = time.time() - total_start
        self.results['end_time'] = datetime.now().isoformat()
        
    def generate_report(self):
        """Generate test report"""
        print(f"\n\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        summary = self.results['summary']
        total_tests = summary['passed'] + summary['failed'] + summary['skipped']
        
        print(f"Total Test Suites: {len(self.results['test_suites'])}")
        print(f"Total Tests Run: {total_tests}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Duration: {summary['duration']:.2f} seconds")
        
        if summary['failed'] == 0:
            print(f"\n✓ ALL TESTS PASSED!")
        else:
            print(f"\n✗ {summary['failed']} TESTS FAILED")
            
        # Show failed tests
        print(f"\n{'='*60}")
        print("DETAILED RESULTS")
        print(f"{'='*60}")
        
        for test_file, results in self.results['test_suites'].items():
            status = "PASS" if results.get('passed', False) else "FAIL"
            duration = results.get('duration', 0)
            print(f"\n{test_file}:")
            print(f"  Status: {status}")
            print(f"  Duration: {duration:.2f}s")
            
            if not results.get('passed', False):
                if 'error' in results:
                    print(f"  Error: {results['error']}")
                elif 'errors' in results and results['errors']:
                    print(f"  Errors: {results['errors'][:200]}...")
                    
    def save_report(self):
        """Save detailed report to file"""
        report_dir = self.test_dir / 'reports'
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f'test_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\nDetailed report saved to: {report_file}")
        
        # Also save a summary
        summary_file = report_dir / f'test_summary_{timestamp}.txt'
        with open(summary_file, 'w') as f:
            f.write(f"TCS++ and Stealth Protocol Test Summary\n")
            f.write(f"{'='*50}\n")
            f.write(f"Date: {self.results['start_time']}\n")
            f.write(f"Duration: {self.results['summary']['duration']:.2f}s\n")
            f.write(f"\nResults:\n")
            f.write(f"  Passed: {self.results['summary']['passed']}\n")
            f.write(f"  Failed: {self.results['summary']['failed']}\n")
            f.write(f"  Skipped: {self.results['summary']['skipped']}\n")
            f.write(f"\nTest Suites:\n")
            
            for test_file, results in self.results['test_suites'].items():
                status = "PASS" if results.get('passed', False) else "FAIL"
                f.write(f"  {test_file}: {status}\n")
                
        print(f"Summary saved to: {summary_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run TCS++ and Stealth Protocol tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--suite', '-s', help='Run specific test suite')
    parser.add_argument('--quick', '-q', action='store_true', help='Skip performance tests')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.suite:
        # Run single suite
        results = runner.run_test_suite(args.suite, args.verbose)
        print(f"\nResults: {'PASSED' if results['passed'] else 'FAILED'}")
    else:
        # Run all tests
        runner.run_all_tests()
        runner.generate_report()
        runner.save_report()
        
        # Exit with appropriate code
        if runner.results['summary']['failed'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == '__main__':
    main()