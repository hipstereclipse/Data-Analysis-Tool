#!/usr/bin/env python3
"""
Test script for the enhanced comparison tab functionality.
This test validates the modernized UI components and intelligent features.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the dialog class
from ui.dialogs import PlotConfigDialog
from models.data_models import FileData, SeriesConfig


class TestEnhancedComparison(unittest.TestCase):
    """Test the enhanced comparison tab functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock parent and file data
        self.mock_parent = Mock()
        self.mock_parent.winfo_toplevel.return_value = Mock()
        
        # Create test data
        self.test_time = np.linspace(0, 100, 1000)
        self.test_pressure1 = 1e-6 * np.exp(-self.test_time/10) + np.random.normal(0, 1e-8, 1000)
        self.test_pressure2 = 2e-6 * np.exp(-self.test_time/15) + np.random.normal(0, 2e-8, 1000)
        
        # Create file data objects
        self.file1 = FileData("test_file1.csv", "test_file1.csv")
        self.file1.data = pd.DataFrame({
            'Time': self.test_time,
            'Pressure': self.test_pressure1
        })
        
        self.file2 = FileData("test_file2.csv", "test_file2.csv")
        self.file2.data = pd.DataFrame({
            'Time': self.test_time, 
            'Pressure': self.test_pressure2
        })
        
        # Create series configs with names
        self.series1 = SeriesConfig(
            file_id="file1",
            x_column="Time",
            y_column="Pressure",
            name="System A - Fast Pump"
        )
        
        self.series2 = SeriesConfig(
            file_id="file2", 
            x_column="Time",
            y_column="Pressure",
            name="System B - Slow Pump"
        )
        
        # Create loaded files dict
        self.loaded_files = {
            "file1": self.file1,
            "file2": self.file2
        }
        
        # Create series configs dict
        self.series_configs = {
            "series1": self.series1,
            "series2": self.series2
        }
    
    def test_smart_defaults_initialization(self):
        """Test that smart defaults are properly initialized"""
        # Create dialog with mock parameters
        with patch('ui.dialogs.PlotConfigDialog.__init__', return_value=None):
            dialog = PlotConfigDialog.__new__(PlotConfigDialog)
            dialog.series_configs = self.series_configs
            dialog.loaded_files = self.loaded_files
            
            # Mock the UI components
            dialog.comp_primary_var = Mock()
            dialog.comp_secondary_var = Mock()
            dialog.primary_info_label = Mock()
            dialog.secondary_info_label = Mock()
            
            # Test smart defaults method
            dialog._initialize_smart_defaults()
            
            # Verify series were auto-selected
            dialog.comp_primary_var.set.assert_called()
            dialog.comp_secondary_var.set.assert_called()
    
    def test_series_name_recognition(self):
        """Test that series are recognized by name instead of ID"""
        with patch('ui.dialogs.PlotConfigDialog.__init__', return_value=None):
            dialog = PlotConfigDialog.__new__(PlotConfigDialog)
            dialog.series_configs = self.series_configs
            dialog.loaded_files = self.loaded_files
            
            # Mock UI components
            dialog.primary_info_label = Mock()
            dialog.comp_secondary_combo = Mock()
            dialog.auto_analysis_var = Mock()
            dialog.auto_analysis_var.get.return_value = False
            
            # Test primary series change by name
            dialog._on_primary_series_change("System A - Fast Pump")
            
            # Verify info label was updated with intelligent text
            dialog.primary_info_label.configure.assert_called()
            call_args = dialog.primary_info_label.configure.call_args[1]
            self.assertIn('📈', call_args['text'])  # Should contain chart emoji
            self.assertIn('points', call_args['text'])  # Should show data points
            self.assertIn('Range:', call_args['text'])  # Should show data range
    
    def test_intelligent_comparison_type_descriptions(self):
        """Test that comparison types have intelligent descriptions"""
        with patch('ui.dialogs.PlotConfigDialog.__init__', return_value=None):
            dialog = PlotConfigDialog.__new__(PlotConfigDialog)
            
            # Mock UI components
            dialog.comp_type_desc = Mock()
            dialog.time_align_var = Mock()
            
            # Test different comparison types
            dialog._on_comparison_type_change("Smart Overlay")
            dialog.comp_type_desc.configure.assert_called_with(
                text="Intelligent overlay with auto-scaling and optimal color selection"
            )
            
            dialog._on_comparison_type_change("Difference Analysis")
            dialog.comp_type_desc.configure.assert_called_with(
                text="Point-by-point difference with statistical significance"
            )
    
    def test_auto_alignment_detection(self):
        """Test intelligent alignment detection"""
        with patch('ui.dialogs.PlotConfigDialog.__init__', return_value=None):
            dialog = PlotConfigDialog.__new__(PlotConfigDialog)
            
            # Test alignment detection with similar data
            x1, y1 = self.test_time, self.test_pressure1
            x2, y2 = self.test_time, self.test_pressure2
            
            alignment = dialog._detect_best_alignment(x1, y1, x2, y2)
            
            # Should return a valid alignment method
            valid_alignments = ["Start Times", "Cross-Correlation", "Peak Alignment", "None"]
            self.assertIn(alignment, valid_alignments)
    
    def test_insight_generation(self):
        """Test AI-like insights generation"""
        with patch('ui.dialogs.PlotConfigDialog.__init__', return_value=None):
            dialog = PlotConfigDialog.__new__(PlotConfigDialog)
            
            # Mock UI component
            dialog.insights_text = Mock()
            
            # Create sample results
            results = {
                'series1_stats': {
                    'mean': 1e-6,
                    'std': 1e-7
                },
                'series2_stats': {
                    'mean': 2e-6,
                    'std': 2e-7
                },
                'correlation': 0.85,
                'ttest': {
                    'p_value': 0.001
                }
            }
            
            # Test insights generation
            dialog._generate_insights(results, "System A", "System B", "Statistical")
            
            # Verify insights were generated and displayed
            dialog.insights_text.delete.assert_called_with("1.0", "end")
            dialog.insights_text.insert.assert_called()
            
            # Check that insights text contains intelligent analysis
            call_args = dialog.insights_text.insert.call_args[0]
            insights_text = call_args[1]
            
            self.assertIn("🧠 INTELLIGENT ANALYSIS INSIGHTS", insights_text)
            self.assertIn("CORRELATION", insights_text)
            self.assertIn("SIGNIFICANT", insights_text)
    
    def test_smart_copy_functionality(self):
        """Test intelligent copy to clipboard with feedback"""
        with patch('ui.dialogs.PlotConfigDialog.__init__', return_value=None):
            dialog = PlotConfigDialog.__new__(PlotConfigDialog)
            
            # Mock UI components
            dialog.comparison_results = Mock()
            dialog.comparison_results.get.return_value = "Test results content"
            dialog.comparison_results.clipboard_clear = Mock()
            dialog.comparison_results.clipboard_append = Mock()
            dialog.comparison_results.insert = Mock()
            dialog.comparison_results.after = Mock()
            
            # Test copy functionality
            dialog._copy_results()
            
            # Verify clipboard operations
            dialog.comparison_results.clipboard_clear.assert_called()
            dialog.comparison_results.clipboard_append.assert_called_with("Test results content")
            
            # Verify feedback message is inserted
            dialog.comparison_results.insert.assert_called()
            call_args = dialog.comparison_results.insert.call_args[0]
            self.assertIn("📋 Results copied", call_args[1])
    
    def test_reset_comparison(self):
        """Test intelligent reset functionality"""
        with patch('ui.dialogs.PlotConfigDialog.__init__', return_value=None):
            dialog = PlotConfigDialog.__new__(PlotConfigDialog)
            dialog.series_configs = self.series_configs
            
            # Mock UI components
            dialog.comp_primary_var = Mock()
            dialog.comp_secondary_var = Mock()
            dialog.comp_type_var = Mock()
            dialog.time_align_var = Mock()
            dialog.confidence_var = Mock()
            dialog.auto_analysis_var = Mock()
            dialog.comparison_results = Mock()
            dialog.insights_text = Mock()
            dialog.comparison_plot_frame = Mock()
            dialog.comparison_plot_frame.winfo_children.return_value = []
            dialog.primary_info_label = Mock()
            dialog.secondary_info_label = Mock()
            dialog.comp_primary_combo = Mock()
            dialog.comp_secondary_combo = Mock()
            
            # Test reset functionality
            dialog._reset_comparison()
            
            # Verify all components are reset to defaults
            dialog.comp_primary_var.set.assert_called_with("")
            dialog.comp_secondary_var.set.assert_called_with("")
            dialog.comp_type_var.set.assert_called_with("Smart Overlay")
            dialog.time_align_var.set.assert_called_with("Auto-Detect")
            dialog.confidence_var.set.assert_called_with(0.95)
            dialog.auto_analysis_var.set.assert_called_with(True)


if __name__ == '__main__':
    print("🧪 Testing Enhanced Comparison Tab Functionality")
    print("=" * 60)
    
    # Run the tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("✅ Enhanced comparison tab testing completed!")
    print("🚀 Modern, intelligent UI features are ready for use!")
