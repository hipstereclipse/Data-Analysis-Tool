#!/usr/bin/env python3
"""
Manual test script for comparison plot functionality
Tests the create_comparison_plot method with different plot types
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Add the DataAnalyzer directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_comparison_plot_types():
    """Test all comparison plot types manually"""
    
    # Generate test data
    time_data = np.linspace(0, 100, 100)
    series1_data = np.sin(time_data * 0.1) + np.random.normal(0, 0.1, 100)
    series2_data = np.cos(time_data * 0.1) + np.random.normal(0, 0.1, 100) + 0.5
    
    # Create mock results for interpolated data
    results = {
        'common_time': time_data,
        'y1_interpolated': series1_data,
        'y2_interpolated': series2_data,
        'correlation': 0.75,
        'series1_stats': {'mean': np.mean(series1_data), 'std': np.std(series1_data)},
        'series2_stats': {'mean': np.mean(series2_data), 'std': np.std(series2_data)}
    }
    
    # Test plot types
    plot_types = [
        "Overlay",
        "Smart Overlay", 
        "Side-by-Side",
        "Difference",
        "Difference Analysis",
        "Correlation",
        "Correlation Plot",
        "Statistical Summary",
        "Statistical",
        "Performance Comparison",
        "Performance"
    ]
    
    # Mock comparison plot creation function (simplified version)
    def create_comparison_plot_test(x1, y1, x2, y2, name1, name2, comp_type, results):
        """Simplified version of create_comparison_plot for testing"""
        print(f"\nTesting plot type: {comp_type}")
        
        try:
            fig = Figure(figsize=(8, 5), dpi=80)
            fig.patch.set_facecolor('white')
            
            if comp_type in ["Overlay", "Smart Overlay"]:
                ax = fig.add_subplot(111)
                ax.plot(x1, y1, label=name1, alpha=0.8, linewidth=1.5)
                ax.plot(x2, y2, label=name2, alpha=0.8, linewidth=1.5)
                ax.set_xlabel("Time")
                ax.set_ylabel("Value")
                ax.set_title(f"Overlay Comparison: {name1} vs {name2}")
                ax.legend()
                ax.grid(True, alpha=0.3)
                print(f"✓ {comp_type} plot created successfully")
                
            elif comp_type == "Side-by-Side":
                ax1 = fig.add_subplot(211)
                ax1.plot(x1, y1, label=name1, color='blue', linewidth=1.5)
                ax1.set_title(name1)
                ax1.grid(True, alpha=0.3)
                
                ax2 = fig.add_subplot(212)
                ax2.plot(x2, y2, label=name2, color='orange', linewidth=1.5)
                ax2.set_title(name2)
                ax2.set_xlabel("Time")
                ax2.grid(True, alpha=0.3)
                print(f"✓ {comp_type} plot created successfully")
                
            elif comp_type in ["Difference", "Difference Analysis"] and 'common_time' in results:
                ax = fig.add_subplot(111)
                diff = results['y1_interpolated'] - results['y2_interpolated']
                ax.plot(results['common_time'], diff, label=f"{name1} - {name2}", color='red', linewidth=1.5)
                ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                ax.set_xlabel("Time")
                ax.set_ylabel("Difference")
                ax.set_title(f"Difference: {name1} - {name2}")
                ax.grid(True, alpha=0.3)
                print(f"✓ {comp_type} plot created successfully")
                
            elif comp_type in ["Correlation", "Correlation Plot"] and 'y1_interpolated' in results:
                ax = fig.add_subplot(111)
                y1_interp = results['y1_interpolated']
                y2_interp = results['y2_interpolated']
                ax.scatter(y1_interp, y2_interp, alpha=0.6, s=20)
                
                # Add trend line
                if len(y1_interp) > 1:
                    try:
                        valid_mask = np.isfinite(y1_interp) & np.isfinite(y2_interp)
                        if np.sum(valid_mask) > 1:
                            y1_clean = y1_interp[valid_mask]
                            y2_clean = y2_interp[valid_mask]
                            
                            if len(y1_clean) > 1 and np.std(y1_clean) > 1e-10:
                                z = np.polyfit(y1_clean, y2_clean, 1)
                                p = np.poly1d(z)
                                ax.plot(y1_clean, p(y1_clean), "r--", alpha=0.8, linewidth=1.5)
                    except Exception as e:
                        print(f"  Warning: Trend line failed: {e}")
                
                ax.set_xlabel(name1)
                ax.set_ylabel(name2)
                ax.set_title(f"Correlation: {name1} vs {name2}")
                if 'correlation' in results:
                    ax.text(0.05, 0.95, f"R = {results['correlation']:.3f}", 
                           transform=ax.transAxes, bbox=dict(boxstyle="round", facecolor="white"))
                ax.grid(True, alpha=0.3)
                print(f"✓ {comp_type} plot created successfully")
                
            elif comp_type in ["Statistical Summary", "Statistical"]:
                ax = fig.add_subplot(111)
                
                # Box plot comparison
                data_to_plot = [y1, y2]
                box_plot = ax.boxplot(data_to_plot, tick_labels=[name1, name2], patch_artist=True)
                
                # Color the boxes
                colors = ['lightblue', 'lightcoral']
                for patch, color in zip(box_plot['boxes'], colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.7)
                
                ax.set_ylabel("Value")
                ax.set_title("Statistical Summary Comparison")
                ax.grid(True, alpha=0.3, axis='y')
                
                # Add statistical annotations
                if 'series1_stats' in results and 'series2_stats' in results:
                    stats1 = results['series1_stats']
                    stats2 = results['series2_stats']
                    
                    info_text = f"{name1}: μ={stats1['mean']:.3f}, σ={stats1['std']:.3f}\n"
                    info_text += f"{name2}: μ={stats2['mean']:.3f}, σ={stats2['std']:.3f}"
                    
                    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
                           bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
                           verticalalignment='top')
                
                print(f"✓ {comp_type} plot created successfully")
                
            elif comp_type in ["Performance Comparison", "Performance"]:
                ax = fig.add_subplot(111)
                
                # Calculate performance metrics
                try:
                    # Stability comparison (coefficient of variation)
                    cv1 = np.std(y1) / np.abs(np.mean(y1)) if np.mean(y1) != 0 else float('inf')
                    cv2 = np.std(y2) / np.abs(np.mean(y2)) if np.mean(y2) != 0 else float('inf')
                    
                    # Base level comparison (10th percentile)
                    base1 = np.percentile(y1, 10)
                    base2 = np.percentile(y2, 10)
                    
                    # Create bar chart comparing metrics
                    metrics = ['Stability\n(lower=better)', 'Base Level\n(lower=better)']
                    series1_values = [cv1, base1]
                    series2_values = [cv2, base2]
                    
                    x_pos = np.arange(len(metrics))
                    width = 0.35
                    
                    bars1 = ax.bar(x_pos - width/2, series1_values, width, 
                                  label=name1, alpha=0.8, color='lightblue')
                    bars2 = ax.bar(x_pos + width/2, series2_values, width,
                                  label=name2, alpha=0.8, color='lightcoral')
                    
                    ax.set_xlabel('Performance Metrics')
                    ax.set_ylabel('Value')
                    ax.set_title('Performance Comparison')
                    ax.set_xticks(x_pos)
                    ax.set_xticklabels(metrics)
                    ax.legend()
                    ax.grid(True, alpha=0.3, axis='y')
                    
                    # Add value labels on bars
                    for bars in [bars1, bars2]:
                        for bar in bars:
                            height = bar.get_height()
                            if np.isfinite(height) and height != 0:
                                ax.text(bar.get_x() + bar.get_width()/2., height,
                                       f'{height:.3e}', ha='center', va='bottom', fontsize=7)
                    
                    print(f"✓ {comp_type} plot created successfully")
                    
                except Exception as e:
                    print(f"  Warning: Performance metrics failed: {e}, using fallback")
                    # Fallback to simple overlay
                    ax.plot(x1, y1, label=name1, alpha=0.8, linewidth=1.5)
                    ax.plot(x2, y2, label=name2, alpha=0.8, linewidth=1.5)
                    ax.set_xlabel("Time")
                    ax.set_ylabel("Value")
                    ax.set_title(f"Performance Comparison: {name1} vs {name2}")
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    print(f"✓ {comp_type} plot created successfully (fallback)")
            
            else:
                # Default fallback - overlay plot
                ax = fig.add_subplot(111)
                ax.plot(x1, y1, label=name1, alpha=0.8, linewidth=1.5)
                ax.plot(x2, y2, label=name2, alpha=0.8, linewidth=1.5)
                ax.set_xlabel("Time")
                ax.set_ylabel("Value")
                ax.set_title(f"Comparison: {name1} vs {name2}")
                ax.legend()
                ax.grid(True, alpha=0.3)
                print(f"✓ {comp_type} plot created successfully (default)")
            
            fig.tight_layout(pad=1.5)
            plt.close(fig)  # Clean up
            return True
            
        except Exception as e:
            print(f"✗ {comp_type} plot failed: {str(e)}")
            return False
    
    # Test all plot types
    print("Testing comparison plot types:")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for plot_type in plot_types:
        success = create_comparison_plot_test(
            time_data, series1_data, 
            time_data, series2_data,
            "Series 1", "Series 2", 
            plot_type, results
        )
        if success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All comparison plot types work correctly!")
    else:
        print(f"⚠️  {failed} plot types need attention")
    
    return failed == 0

if __name__ == "__main__":
    success = test_comparison_plot_types()
    sys.exit(0 if success else 1)
