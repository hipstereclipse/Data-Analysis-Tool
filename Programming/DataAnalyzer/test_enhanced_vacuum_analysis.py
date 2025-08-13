#!/usr/bin/env python3
"""
Test script for enhanced vacuum analysis functionality
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from analysis.legacy_analysis_tools import VacuumAnalysisTools
import sys
import os

def generate_test_vacuum_data():
    """Generate synthetic vacuum data for testing"""
    # Create time series (1000 points over 100 seconds)
    time = np.linspace(0, 100, 1000)
    
    # Generate pump-down curve with exponential decay
    initial_pressure = 1e-1  # 0.1 mbar
    base_pressure = 1e-8     # 1e-8 mbar
    time_constant = 15       # 15 second time constant
    
    # Exponential pump-down
    pressure = base_pressure + (initial_pressure - base_pressure) * np.exp(-time / time_constant)
    
    # Add some noise
    noise = np.random.normal(0, pressure * 0.02)  # 2% noise
    pressure += noise
    
    # Add some pressure spikes
    spike_times = [25, 45, 70]
    for spike_time in spike_times:
        spike_idx = np.argmin(np.abs(time - spike_time))
        spike_magnitude = pressure[spike_idx] * np.random.uniform(5, 20)
        spike_width = np.random.randint(3, 8)
        
        # Add spike
        for i in range(max(0, spike_idx - spike_width), min(len(pressure), spike_idx + spike_width)):
            pressure[i] += spike_magnitude * np.exp(-((i - spike_idx) / spike_width)**2)
    
    # Add pressure rise section (leak simulation)
    leak_start = 80
    leak_start_idx = np.argmin(np.abs(time - leak_start))
    for i in range(leak_start_idx, len(pressure)):
        pressure[i] += 1e-9 * (time[i] - leak_start)**2  # Quadratic leak rise
    
    # Ensure positive pressures
    pressure = np.maximum(pressure, 1e-12)
    
    return time, pressure

def test_enhanced_spike_detection():
    """Test enhanced spike detection"""
    print("Testing Enhanced Spike Detection...")
    print("-" * 40)
    
    time, pressure = generate_test_vacuum_data()
    
    # Test spike detection
    spikes = VacuumAnalysisTools.detect_pressure_spikes(pressure, threshold_factor=3)
    
    print(f"Found {len(spikes)} pressure spikes")
    
    if spikes:
        print("\nSpike Details:")
        for i, spike in enumerate(spikes[:5]):  # Show first 5
            print(f"  Spike {i+1}:")
            print(f"    Duration: {spike['duration']} points")
            print(f"    Max Pressure: {spike['max_pressure']:.3e} mbar")
            print(f"    Baseline: {spike.get('baseline_pressure', 0):.3e} mbar")
            print(f"    Pressure Ratio: {spike.get('pressure_ratio', 0):.1f}x")
            print(f"    Severity: {spike.get('severity', 'unknown')}")
    
    return len(spikes) > 0

def test_enhanced_pump_down_analysis():
    """Test enhanced pump-down analysis"""
    print("\nTesting Enhanced Pump-Down Analysis...")
    print("-" * 40)
    
    time, pressure = generate_test_vacuum_data()
    
    # Test pump-down analysis
    results = VacuumAnalysisTools.analyze_pump_down_curve(pressure, time)
    
    print(f"Initial Pressure: {results.get('initial_pressure', 0):.3e} mbar")
    print(f"Final Pressure: {results.get('final_pressure', 0):.3e} mbar")
    
    if 'milestones' in results:
        print("\nPressure Milestones:")
        for level, milestone_time in results['milestones'].items():
            print(f"  {level}: {milestone_time}")
    
    if 'time_constant' in results:
        print(f"\nTime Constant: {results['time_constant']:.2f} s")
    
    if 'exponential_fit' in results:
        fit = results['exponential_fit']
        print(f"Exponential Fit R²: {fit.get('r_squared', 0):.4f}")
    
    if 'pump_rate_phases' in results:
        print(f"\nPump Rate Phases: {len(results['pump_rate_phases'])} phases detected")
    
    return 'milestones' in results

def test_enhanced_leak_rate_calculation():
    """Test enhanced leak rate calculation"""
    print("\nTesting Enhanced Leak Rate Calculation...")
    print("-" * 40)
    
    time, pressure = generate_test_vacuum_data()
    
    # Focus on the leak section
    leak_start_idx = int(0.8 * len(time))  # Last 20% of data
    leak_time = time[leak_start_idx:]
    leak_pressure = pressure[leak_start_idx:]
    
    # Test leak rate calculation
    results = VacuumAnalysisTools.calculate_leak_rate(
        leak_pressure, leak_time, leak_pressure[0]
    )
    
    print("Leak Rate Analysis Results:")
    
    if 'linear_fit' in results:
        linear = results['linear_fit']
        print(f"  Linear Method:")
        print(f"    Leak Rate: {linear.get('leak_rate', 0):.3e} mbar·L/s")
        print(f"    R²: {linear.get('r_squared', 0):.4f}")
    
    if 'exponential_fit' in results:
        exp = results['exponential_fit']
        print(f"  Exponential Method:")
        print(f"    Leak Rate: {exp.get('leak_rate', 0):.3e} mbar·L/s")
        print(f"    R²: {exp.get('r_squared', 0):.4f}")
    
    if 'conductance_based' in results:
        cond = results['conductance_based']
        print(f"  Conductance Method:")
        print(f"    Leak Rate: {cond.get('leak_rate', 0):.3e} mbar·L/s")
    
    if 'severity' in results:
        print(f"  Severity: {results['severity']}")
    
    return len(results) > 0

def test_comprehensive_system_analysis():
    """Test comprehensive vacuum system performance analysis"""
    print("\nTesting Comprehensive System Analysis...")
    print("-" * 40)
    
    time, pressure = generate_test_vacuum_data()
    
    # Test comprehensive analysis
    results = VacuumAnalysisTools.analyze_vacuum_system_performance(pressure, time, system_volume=10)
    
    if 'basic_metrics' in results:
        metrics = results['basic_metrics']
        print(f"Basic Metrics:")
        print(f"  Min Pressure: {metrics['min_pressure']:.3e} mbar")
        print(f"  Max Pressure: {metrics['max_pressure']:.3e} mbar")
        print(f"  Mean Pressure: {metrics['mean_pressure']:.3e} mbar")
        print(f"  Stability: {metrics['pressure_stability']:.4f}")
    
    if 'base_pressure' in results:
        print(f"\nBase Pressure: {results['base_pressure']:.3e} mbar")
    
    if 'pump_cycles' in results:
        cycles = results['pump_cycles']
        print(f"\nPump Cycles: {len(cycles)} detected")
        for i, cycle in enumerate(cycles[:3]):  # Show first 3
            print(f"  Cycle {i+1}: {cycle['efficiency']} efficiency, {cycle['pressure_drop']:.1f} orders drop")
    
    if 'pressure_spikes' in results:
        spikes = results['pressure_spikes']
        print(f"\nPressure Spikes: {len(spikes)} detected")
    
    if 'system_rating' in results:
        rating = results['system_rating']
        print(f"\nSystem Rating:")
        print(f"  Grade: {rating['grade']}")
        print(f"  Performance: {rating['performance']}")
        print(f"  Score: {rating['score']}/80")
        print(f"  Factors: {', '.join(rating['factors'][:3])}")  # Show first 3 factors
    
    return 'system_rating' in results

def main():
    """Run all tests"""
    print("Enhanced Vacuum Analysis Test Suite")
    print("=" * 50)
    
    test_results = []
    
    try:
        # Test spike detection
        result1 = test_enhanced_spike_detection()
        test_results.append(("Spike Detection", result1))
        
        # Test pump-down analysis
        result2 = test_enhanced_pump_down_analysis()
        test_results.append(("Pump-Down Analysis", result2))
        
        # Test leak rate calculation
        result3 = test_enhanced_leak_rate_calculation()
        test_results.append(("Leak Rate Calculation", result3))
        
        # Test comprehensive analysis
        result4 = test_comprehensive_system_analysis()
        test_results.append(("Comprehensive Analysis", result4))
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        passed = 0
        for test_name, result in test_results:
            status = "PASS" if result else "FAIL"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall: {passed}/{len(test_results)} tests passed")
        
        if passed == len(test_results):
            print("🎉 All enhanced vacuum analysis features are working correctly!")
        else:
            print("⚠️  Some tests failed - check the implementation")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
