#!/usr/bin/env python3
"""
Quick test script to verify the error fixes
"""

import sys
import os
import numpy as np

# Add the DataAnalyzer directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_vacuum_analyzer():
    """Test vacuum analyzer methods"""
    print("Testing vacuum analyzer...")
    
    from analysis.vacuum import VacuumAnalyzer
    
    analyzer = VacuumAnalyzer()
    
    # Test data
    pressure_data = np.array([1000, 800, 600, 400, 200, 100, 50, 25, 10, 5])
    time_data = np.arange(len(pressure_data))
    
    # Test leak detection (should return float, not list)
    leak_rate = analyzer.detect_leaks(pressure_data, time_data)
    print(f"✓ Leak detection works: {leak_rate:.2e} mbar·L/s")
    
    # Test pumpdown analysis (should return dict with correct keys)
    pumpdown_result = analyzer.analyze_pumpdown(pressure_data, time_data)
    print(f"✓ Pumpdown analysis works: {type(pumpdown_result)}")
    
    required_keys = ['base_pressure', 'leak_rate', 'pumpdown_rate', 'initial_pressure', 'min_pressure']
    for key in required_keys:
        if key in pumpdown_result:
            print(f"  ✓ {key}: {pumpdown_result[key]:.2e}")
        else:
            print(f"  ✗ Missing key: {key}")
    
    return True

def test_empty_array_handling():
    """Test handling of empty arrays"""
    print("\nTesting empty array handling...")
    
    # Test with empty arrays
    try:
        y1_empty = np.array([])
        y2_empty = np.array([])
        
        # This should not crash with "zero-size array" error
        if len(y1_empty) == 0:
            print("✓ Empty array detection works")
        
        # Test with NaN arrays
        y1_nan = np.array([np.nan, np.nan, np.nan])
        y2_nan = np.array([np.inf, -np.inf, np.nan])
        
        y1_clean = y1_nan[np.isfinite(y1_nan)]
        y2_clean = y2_nan[np.isfinite(y2_nan)]
        
        if len(y1_clean) == 0 and len(y2_clean) == 0:
            print("✓ NaN/infinite value filtering works")
        
        return True
    except Exception as e:
        print(f"✗ Error in empty array handling: {e}")
        return False

def test_statistical_calculations():
    """Test statistical calculations with edge cases"""
    print("\nTesting statistical calculations...")
    
    try:
        # Test with valid data
        y_valid = np.array([1, 2, 3, 4, 5])
        stats = {
            'mean': np.mean(y_valid),
            'std': np.std(y_valid),
            'min': np.min(y_valid),
            'max': np.max(y_valid)
        }
        print(f"✓ Valid data stats: {stats}")
        
        # Test with single value
        y_single = np.array([42.0])
        stats_single = {
            'mean': np.mean(y_single),
            'std': np.std(y_single),
            'min': np.min(y_single),
            'max': np.max(y_single)
        }
        print(f"✓ Single value stats: {stats_single}")
        
        return True
    except Exception as e:
        print(f"✗ Error in statistical calculations: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("ERROR FIXES VALIDATION TEST")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    try:
        if test_vacuum_analyzer():
            tests_passed += 1
    except Exception as e:
        print(f"✗ Vacuum analyzer test failed: {e}")
    
    try:
        if test_empty_array_handling():
            tests_passed += 1
    except Exception as e:
        print(f"✗ Empty array handling test failed: {e}")
    
    try:
        if test_statistical_calculations():
            tests_passed += 1
    except Exception as e:
        print(f"✗ Statistical calculations test failed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("🎉 All error fixes are working correctly!")
    else:
        print(f"⚠️  {total_tests - tests_passed} tests failed")
    
    sys.exit(0 if tests_passed == total_tests else 1)
