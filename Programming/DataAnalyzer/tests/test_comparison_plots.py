#!/usr/bin/env python3
"""
Test suite for comparison analysis plot types
Ensures all comparison plot types work correctly with various data configurations
"""

import unittest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from unittest.mock import Mock, patch
import sys
import os

# Add the DataAnalyzer directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ui.dialogs import StatisticalAnalysisDialog
from models.data_models import SeriesConfig, FileData


class TestComparisonPlots(unittest.TestCase):
    """Test all comparison plot types and configurations"""
    
    def setUp(self):
        """Set up test data and mock objects"""
        # Create test data
        self.time_data = np.linspace(0, 100, 1000)
        self.series1_data = np.sin(self.time_data * 0.1) + np.random.normal(0, 0.1, 1000)
        self.series2_data = np.cos(self.time_data * 0.1) + np.random.normal(0, 0.1, 1000) + 0.5
        
        # Create mock file data
        self.file_data1 = FileData(
            filename="test_data1.csv",
            filepath="/test/path1.csv",
            data=pd.DataFrame({
                'time': self.time_data,
                'pressure': self.series1_data
            })
        )
        
        self.file_data2 = FileData(
            filename="test_data2.csv", 
            filepath="/test/path2.csv",
            data=pd.DataFrame({
                'time': self.time_data,
                'pressure': self.series2_data
            })
        )
        
        # Create mock series configs
        self.series_config1 = SeriesConfig(
            name="Test Series 1",
            file_id="file1",
            x_column="time",
            y_column="pressure",
            color="#FF0000",
            start_index=0,
            end_index=1000
        )
        
        self.series_config2 = SeriesConfig(
            name="Test Series 2",
            file_id="file2",
            x_column="time", 
            y_column="pressure",
            color="#0000FF",
            start_index=0,
            end_index=1000
        )
        
        # Mock parent and create dialog
        self.mock_parent = Mock()
        self.mock_parent.winfo_screenwidth.return_value = 1920
        self.mock_parent.winfo_screenheight.return_value = 1080
        
        self.series_configs = {
            "series1": self.series_config1,
            "series2": self.series_config2
        }
        
        self.loaded_files = {
            "file1": self.file_data1,
            "file2": self.file_data2
        }

    def create_dialog_mock(self):
        """Create a properly mocked dialog for testing"""
        with patch('customtkinter.CTkToplevel'), \
             patch('customtkinter.CTkTabview'), \
             patch('customtkinter.CTkFrame'), \
             patch('customtkinter.CTkLabel'), \
             patch('customtkinter.CTkComboBox'), \
             patch('customtkinter.CTkButton'), \
             patch('customtkinter.CTkSlider'), \
             patch('customtkinter.CTkCheckBox'), \
             patch('customtkinter.CTkEntry'), \
             patch('customtkinter.CTkScrollableFrame'):
            
            dialog = StatisticalAnalysisDialog(
                self.mock_parent,
                self.series_configs,
                self.loaded_files,
                Mock(),  # statistical_analyzer
                Mock()   # vacuum_analyzer
            )
            return dialog
    
    def test_smart_overlay_plot(self):
        """Test Smart Overlay comparison plot"""
        dialog = self.create_dialog_mock()
        
        try:
            results = dialog.perform_series_comparison(
                self.time_data, self.series1_data,
                self.time_data, self.series2_data,
                "Test Series 1", "Test Series 2",
                "Smart Overlay", "None"
            )
            
            # Verify results structure
            self.assertIn('series1_stats', results)
            self.assertIn('series2_stats', results)
            
            # Test plot creation
            with patch('matplotlib.pyplot.figure') as mock_fig:
                dialog.create_comparison_plot(
                    self.time_data, self.series1_data,
                    self.time_data, self.series2_data,
                    "Test Series 1", "Test Series 2",
                    "Overlay", results
                )
                # Verify plot was attempted
                mock_fig.assert_called()
                
        except Exception as e:
            self.fail(f"Smart Overlay plot failed: {str(e)}")
    
    def test_side_by_side_plot(self):
        """Test Side-by-Side comparison plot"""
        dialog = self.create_dialog_mock()
        
        try:
            results = dialog.perform_series_comparison(
                self.time_data, self.series1_data,
                self.time_data, self.series2_data,
                "Test Series 1", "Test Series 2",
                "Side-by-Side", "None"
            )
            
            with patch('matplotlib.pyplot.figure') as mock_fig:
                dialog.create_comparison_plot(
                    self.time_data, self.series1_data,
                    self.time_data, self.series2_data,
                    "Test Series 1", "Test Series 2",
                    "Side-by-Side", results
                )
                mock_fig.assert_called()
                
        except Exception as e:
            self.fail(f"Side-by-Side plot failed: {str(e)}")
    
    def test_difference_analysis_plot(self):
        """Test Difference Analysis plot"""
        dialog = self.create_dialog_mock()
        
        try:
            results = dialog.perform_series_comparison(
                self.time_data, self.series1_data,
                self.time_data, self.series2_data,
                "Test Series 1", "Test Series 2",
                "Difference", "None"
            )
            
            with patch('matplotlib.pyplot.figure') as mock_fig:
                dialog.create_comparison_plot(
                    self.time_data, self.series1_data,
                    self.time_data, self.series2_data,
                    "Test Series 1", "Test Series 2",
                    "Difference", results
                )
                mock_fig.assert_called()
                
        except Exception as e:
            self.fail(f"Difference Analysis plot failed: {str(e)}")
    
    def test_correlation_plot(self):
        """Test Correlation Plot"""
        dialog = self.create_dialog_mock()
        
        try:
            results = dialog.perform_series_comparison(
                self.time_data, self.series1_data,
                self.time_data, self.series2_data,
                "Test Series 1", "Test Series 2",
                "Correlation", "None"
            )
            
            with patch('matplotlib.pyplot.figure') as mock_fig:
                dialog.create_comparison_plot(
                    self.time_data, self.series1_data,
                    self.time_data, self.series2_data,
                    "Test Series 1", "Test Series 2",
                    "Correlation", results
                )
                mock_fig.assert_called()
                
        except Exception as e:
            self.fail(f"Correlation plot failed: {str(e)}")
    
    def test_statistical_summary_plot(self):
        """Test Statistical Summary plot"""
        dialog = self.create_dialog_mock()
        
        try:
            results = dialog.perform_series_comparison(
                self.time_data, self.series1_data,
                self.time_data, self.series2_data,
                "Test Series 1", "Test Series 2",
                "Statistical Summary", "None"
            )
            
            with patch('matplotlib.pyplot.figure') as mock_fig:
                dialog.create_comparison_plot(
                    self.time_data, self.series1_data,
                    self.time_data, self.series2_data,
                    "Test Series 1", "Test Series 2",
                    "Statistical Summary", results
                )
                mock_fig.assert_called()
                
        except Exception as e:
            self.fail(f"Statistical Summary plot failed: {str(e)}")
    
    def test_performance_comparison_plot(self):
        """Test Performance Comparison plot"""
        dialog = self.create_dialog_mock()
        
        try:
            results = dialog.perform_series_comparison(
                self.time_data, self.series1_data,
                self.time_data, self.series2_data,
                "Test Series 1", "Test Series 2",
                "Performance Comparison", "None"
            )
            
            with patch('matplotlib.pyplot.figure') as mock_fig:
                dialog.create_comparison_plot(
                    self.time_data, self.series1_data,
                    self.time_data, self.series2_data,
                    "Test Series 1", "Test Series 2",
                    "Performance Comparison", results
                )
                mock_fig.assert_called()
                
        except Exception as e:
            self.fail(f"Performance Comparison plot failed: {str(e)}")
    
    def test_time_alignment_methods(self):
        """Test all time alignment methods"""
        dialog = self.create_dialog_mock()
        
        alignment_methods = [
            "None", "Start Times", "Peak Alignment", 
            "Cross-Correlation", "Custom Offset"
        ]
        
        for method in alignment_methods:
            with self.subTest(method=method):
                try:
                    # Set up custom offset values for Custom Offset test
                    if method == "Custom Offset":
                        dialog.primary_offset_var = Mock()
                        dialog.primary_offset_var.get.return_value = 5.0
                        dialog.secondary_offset_var = Mock()
                        dialog.secondary_offset_var.get.return_value = -2.0
                    
                    x1_aligned, y1_aligned, x2_aligned, y2_aligned = dialog.align_time_series(
                        self.time_data, self.series1_data,
                        self.time_data, self.series2_data,
                        method
                    )
                    
                    # Verify alignment didn't break data integrity
                    self.assertTrue(len(x1_aligned) > 0)
                    self.assertTrue(len(y1_aligned) > 0)
                    self.assertTrue(len(x2_aligned) > 0)
                    self.assertTrue(len(y2_aligned) > 0)
                    self.assertEqual(len(x1_aligned), len(y1_aligned))
                    self.assertEqual(len(x2_aligned), len(y2_aligned))
                    
                except Exception as e:
                    self.fail(f"Time alignment method '{method}' failed: {str(e)}")
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        dialog = self.create_dialog_mock()
        
        # Test with empty data
        try:
            empty_data = np.array([])
            results = dialog.perform_series_comparison(
                empty_data, empty_data,
                self.time_data, self.series2_data,
                "Empty Series", "Test Series 2",
                "Smart Overlay", "None"
            )
            # Should handle gracefully without crashing
        except Exception as e:
            # This is expected for empty data
            pass
        
        # Test with NaN data
        try:
            nan_data = np.full(100, np.nan)
            time_short = np.linspace(0, 10, 100)
            results = dialog.perform_series_comparison(
                time_short, nan_data,
                self.time_data[:100], self.series2_data[:100],
                "NaN Series", "Test Series 2",
                "Smart Overlay", "None"
            )
            # Should handle gracefully
        except Exception as e:
            # This is expected for NaN data
            pass
        
        # Test with single data point
        try:
            single_time = np.array([0])
            single_data = np.array([1.0])
            results = dialog.perform_series_comparison(
                single_time, single_data,
                self.time_data[:1], self.series2_data[:1],
                "Single Point 1", "Single Point 2",
                "Smart Overlay", "None"
            )
            # Should handle gracefully
        except Exception as e:
            # This is expected for insufficient data
            pass
    
    def test_data_validation(self):
        """Test data validation in comparison analysis"""
        dialog = self.create_dialog_mock()
        
        # Test mismatched array lengths
        short_time = self.time_data[:500]
        try:
            results = dialog.perform_series_comparison(
                short_time, self.series1_data,  # Mismatched lengths
                self.time_data, self.series2_data,
                "Mismatched Series 1", "Test Series 2",
                "Smart Overlay", "None"
            )
            # Should either handle gracefully or raise appropriate error
        except (ValueError, IndexError):
            # Expected for mismatched data
            pass
    
    def test_all_plot_types_comprehensive(self):
        """Comprehensive test of all plot types with various data scenarios"""
        dialog = self.create_dialog_mock()
        
        plot_types = [
            "Overlay", "Side-by-Side", "Difference", 
            "Correlation", "Statistical Summary", "Performance Comparison"
        ]
        
        # Test different data scenarios
        data_scenarios = [
            ("Normal", self.time_data, self.series1_data, self.time_data, self.series2_data),
            ("Positive Only", self.time_data, np.abs(self.series1_data), self.time_data, np.abs(self.series2_data)),
            ("Large Values", self.time_data, self.series1_data * 1e6, self.time_data, self.series2_data * 1e6),
            ("Small Values", self.time_data, self.series1_data * 1e-6, self.time_data, self.series2_data * 1e-6),
        ]
        
        for plot_type in plot_types:
            for scenario_name, x1, y1, x2, y2 in data_scenarios:
                with self.subTest(plot_type=plot_type, scenario=scenario_name):
                    try:
                        results = dialog.perform_series_comparison(
                            x1, y1, x2, y2,
                            f"Series 1 ({scenario_name})", f"Series 2 ({scenario_name})",
                            plot_type, "None"
                        )
                        
                        with patch('matplotlib.pyplot.figure'):
                            dialog.create_comparison_plot(
                                x1, y1, x2, y2,
                                f"Series 1 ({scenario_name})", f"Series 2 ({scenario_name})",
                                plot_type, results
                            )
                        
                    except Exception as e:
                        self.fail(f"Plot type '{plot_type}' failed with scenario '{scenario_name}': {str(e)}")


if __name__ == '__main__':
    # Set up test environment
    plt.ioff()  # Turn off interactive plotting for tests
    
    # Run tests
    unittest.main(verbosity=2)
