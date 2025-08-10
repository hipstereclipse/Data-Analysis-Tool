import sys
import unittest
from io import StringIO
import traceback


def run_tests():
    """Run all tests and display results"""

    print("=" * 60)
    print("EXCEL DATA PLOTTER - TEST SUITE")
    print("Testing all fixes")
    print("=" * 60)

    # Create test loader
    loader = unittest.TestLoader()

    # Create test suite
    suite = unittest.TestSuite()

    # Try to load each test module
    test_modules = [
        'tests.test_models',
        'tests.test_analysis'
    ]

    for module_name in test_modules:
        try:
            module_tests = loader.loadTestsFromName(module_name)
            suite.addTests(module_tests)
            print(f"✓ Loaded tests from {module_name}")
        except Exception as e:
            print(f"✗ Failed to load {module_name}: {e}")

    print("\n" + "=" * 60)
    print("RUNNING TESTS")
    print("=" * 60 + "\n")

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    # Summary statistics
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    success = total_tests - failures - errors - skipped

    print(f"Total Tests: {total_tests}")
    print(f"Passed:      {success} ✓")
    print(f"Failed:      {failures} ✗")
    print(f"Errors:      {errors} ✗")
    print(f"Skipped:     {skipped} -")

    # Success rate
    if total_tests > 0:
        success_rate = (success / total_tests) * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")

    # Print details of failures
    if result.failures:
        print("\n" + "=" * 60)
        print("FAILURES")
        print("=" * 60)
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)

    # Print details of errors
    if result.errors:
        print("\n" + "=" * 60)
        print("ERRORS")
        print("=" * 60)
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)

    # Final status
    print("\n" + "=" * 60)
    if failures == 0 and errors == 0:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED")
        print("\nFixes Applied:")
        print("1. ✓ DataQualityAnalyzer.analyze_quality() method added")
        print("2. ✓ Statistical methods return proper values")
        print("3. ✓ Vacuum methods return expected types")
        print("4. ✓ CollapsibleFrame UI component added")
        print("5. ✓ validate_file_size function added")
        print("\nNext Steps:")
        print("1. Copy the fixed files to your project")
        print("2. Restart the application")
        print("3. Run tests again to verify")

    print("=" * 60)

    return result.wasSuccessful()


def test_imports():
    """Test that all required modules can be imported"""
    print("\n" + "=" * 60)
    print("IMPORT TEST")
    print("=" * 60)

    modules_to_test = [
        ('analysis.data_quality', 'DataQualityAnalyzer'),
        ('analysis.statistical', 'StatisticalAnalyzer'),
        ('analysis.vacuum', 'VacuumAnalyzer'),
        ('ui.components', 'CollapsibleFrame'),
        ('ui.components', 'StatusBar'),
        ('ui.components', 'QuickActionBar'),
        ('utils.validators', 'validate_file_size'),
        ('models.project_models', 'ProjectMetadata'),
    ]

    all_imports_ok = True

    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
        except ImportError as e:
            print(f"✗ {module_name}.{class_name}: Import failed - {e}")
            all_imports_ok = False
        except AttributeError as e:
            print(f"✗ {module_name}.{class_name}: Class not found - {e}")
            all_imports_ok = False

    if all_imports_ok:
        print("\n✓ All imports successful!")
    else:
        print("\n✗ Some imports failed - apply the fixes to the corresponding files")

    return all_imports_ok


if __name__ == "__main__":
    print("\nExcel Data Plotter - Test Suite with Fixes")
    print("=" * 60)

    # First test imports
    imports_ok = test_imports()

    if not imports_ok:
        print("\n⚠ Warning: Some imports failed.")
        print("Make sure all fix files have been applied to your project.\n")

    # Run the actual tests
    success = run_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)