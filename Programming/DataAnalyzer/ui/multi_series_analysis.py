#!/usr/bin/env python3
"""
Enhanced Multi-Series Analysis Dialog with advanced features
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from scipy import stats
from typing import Dict, List, Optional, Any, Callable
import logging
from datetime import datetime

from models.data_models import SeriesConfig, FileData
from ui.theme_manager import theme_manager
from analysis.statistical import StatisticalAnalyzer
from analysis.vacuum import VacuumAnalyzer

logger = logging.getLogger(__name__)

class MultiSeriesAnalysisDialog:
    """Enhanced analysis dialog supporting multiple series simultaneously"""
    
    def __init__(self, parent, series_configs: Dict[str, SeriesConfig], 
                 loaded_files: Dict[str, FileData]):
        self.parent = parent
        self.series_configs = series_configs
        self.loaded_files = loaded_files
        self.result = None
        
        # Analysis results storage
        self.analysis_results = {}
        self.statistical_analyzer = StatisticalAnalyzer()
        self.vacuum_analyzer = VacuumAnalyzer()
        
        # Create dialog
        self.create_dialog()
        
    def create_dialog(self):
        """Create the enhanced analysis dialog"""
        # Calculate responsive size
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        dialog_width = min(1600, int(screen_width * 0.9))
        dialog_height = min(1000, int(screen_height * 0.9))
        
        # Create dialog
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Enhanced Multi-Series Analysis")
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Configure grid
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)
        
        # Create main container
        main_container = ctk.CTkFrame(self.dialog)
        main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_container.grid_columnconfigure(1, weight=2)
        main_container.grid_rowconfigure(0, weight=1)
        
        # Left panel - Analysis configuration
        self.create_analysis_panel(main_container)
        
        # Right panel - Results and visualization
        self.create_results_panel(main_container)
        
        # Bottom button panel
        self.create_button_panel()
        
        # Initialize
        self.populate_series_list()
        
    def create_analysis_panel(self, parent):
        """Create analysis configuration panel"""
        analysis_frame = ctk.CTkFrame(parent)
        analysis_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        analysis_frame.configure(width=500)
        
        # Title
        title_label = ctk.CTkLabel(
            analysis_frame,
            text="Multi-Series Analysis",
            font=theme_manager.get_font("heading")
        )
        title_label.pack(pady=10)
        
        # Create analysis notebook
        self.analysis_notebook = ctk.CTkTabview(analysis_frame)
        self.analysis_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Analysis tabs
        self.create_series_selection_tab()
        self.create_statistical_analysis_tab()
        self.create_vacuum_analysis_tab()
        self.create_comparison_tab()
        
    def create_series_selection_tab(self):
        """Create series selection tab"""
        selection_tab = self.analysis_notebook.add("Series Selection")
        
        # Series list with checkboxes
        list_frame = ctk.CTkFrame(selection_tab)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(
            list_frame,
            text="Select Series for Analysis:",
            font=theme_manager.get_font("subheading")
        ).pack(anchor="w", pady=5)
        
        # Scrollable frame for series
        self.series_scroll_frame = ctk.CTkScrollableFrame(list_frame)
        self.series_scroll_frame.pack(fill="both", expand=True, pady=5)
        
        # Buttons for selection
        button_frame = ctk.CTkFrame(list_frame)
        button_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="Select All",
            command=self.select_all_series,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="Clear All",
            command=self.clear_all_series,
            width=100
        ).pack(side="left", padx=5)
        
    def create_statistical_analysis_tab(self):
        """Create statistical analysis tab"""
        stats_tab = self.analysis_notebook.add("Statistical Analysis")
        
        # Analysis options
        options_frame = ctk.CTkFrame(stats_tab)
        options_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            options_frame,
            text="Statistical Analysis Options:",
            font=theme_manager.get_font("subheading")
        ).pack(anchor="w", pady=5)
        
        # Analysis checkboxes
        self.stats_options = {}
        options = [
            ("basic_stats", "Basic Statistics (mean, std, etc.)"),
            ("normality_test", "Normality Tests"),
            ("correlation", "Cross-Correlation Analysis"),
            ("outlier_detection", "Outlier Detection"),
            ("trend_analysis", "Trend Analysis")
        ]
        
        for option_key, option_text in options:
            var = tk.BooleanVar(value=True)
            self.stats_options[option_key] = var
            ctk.CTkCheckBox(
                options_frame,
                text=option_text,
                variable=var
            ).pack(anchor="w", pady=2)
            
        # Run button
        ctk.CTkButton(
            stats_tab,
            text="Run Statistical Analysis",
            command=self.run_statistical_analysis,
            font=theme_manager.get_font("subheading")
        ).pack(pady=10)
        
    def create_vacuum_analysis_tab(self):
        """Create vacuum-specific analysis tab"""
        vacuum_tab = self.analysis_notebook.add("Vacuum Analysis")
        
        # Vacuum analysis options
        options_frame = ctk.CTkFrame(vacuum_tab)
        options_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            options_frame,
            text="Vacuum Analysis Options:",
            font=theme_manager.get_font("subheading")
        ).pack(anchor="w", pady=5)
        
        # Analysis checkboxes
        self.vacuum_options = {}
        options = [
            ("base_pressure", "Base Pressure Calculation"),
            ("pumpdown_curves", "Pump-down Curve Analysis"),
            ("leak_detection", "Leak Detection"),
            ("spike_detection", "Pressure Spike Detection"),
            ("stability_analysis", "Pressure Stability Analysis")
        ]
        
        for option_key, option_text in options:
            var = tk.BooleanVar(value=True)
            self.vacuum_options[option_key] = var
            ctk.CTkCheckBox(
                options_frame,
                text=option_text,
                variable=var
            ).pack(anchor="w", pady=2)
            
        # Parameters frame
        params_frame = ctk.CTkFrame(vacuum_tab)
        params_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            params_frame,
            text="Analysis Parameters:",
            font=theme_manager.get_font("subheading")
        ).pack(anchor="w", pady=5)
        
        # Parameter inputs
        param_grid = ctk.CTkFrame(params_frame)
        param_grid.pack(fill="x", pady=5)
        param_grid.grid_columnconfigure(1, weight=1)
        
        # Spike threshold
        ctk.CTkLabel(param_grid, text="Spike Threshold (σ):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.spike_threshold_var = tk.DoubleVar(value=3.0)
        ctk.CTkEntry(param_grid, textvariable=self.spike_threshold_var, width=100).grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        # Leak threshold  
        ctk.CTkLabel(param_grid, text="Leak Threshold:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.leak_threshold_var = tk.DoubleVar(value=0.01)
        ctk.CTkEntry(param_grid, textvariable=self.leak_threshold_var, width=100).grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        # Window size
        ctk.CTkLabel(param_grid, text="Analysis Window (points):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.window_size_var = tk.IntVar(value=100)
        ctk.CTkEntry(param_grid, textvariable=self.window_size_var, width=100).grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        # Run button
        ctk.CTkButton(
            vacuum_tab,
            text="Run Vacuum Analysis",
            command=self.run_vacuum_analysis,
            font=theme_manager.get_font("subheading")
        ).pack(pady=10)
        
    def create_comparison_tab(self):
        """Create series comparison tab"""
        comparison_tab = self.analysis_notebook.add("Series Comparison")
        
        # Comparison options
        options_frame = ctk.CTkFrame(comparison_tab)
        options_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            options_frame,
            text="Comparison Analysis:",
            font=theme_manager.get_font("subheading")
        ).pack(anchor="w", pady=5)
        
        # Comparison types
        self.comparison_options = {}
        options = [
            ("overlay_plot", "Overlay Plot Comparison"),
            ("statistical_comparison", "Statistical Comparison"),
            ("time_alignment", "Time-Aligned Comparison"),
            ("correlation_matrix", "Cross-Correlation Matrix"),
            ("performance_metrics", "Performance Metrics")
        ]
        
        for option_key, option_text in options:
            var = tk.BooleanVar(value=True)
            self.comparison_options[option_key] = var
            ctk.CTkCheckBox(
                options_frame,
                text=option_text,
                variable=var
            ).pack(anchor="w", pady=2)
            
        # Run button
        ctk.CTkButton(
            comparison_tab,
            text="Run Comparison Analysis",
            command=self.run_comparison_analysis,
            font=theme_manager.get_font("subheading")
        ).pack(pady=10)
        
    def create_results_panel(self, parent):
        """Create results and visualization panel"""
        results_frame = ctk.CTkFrame(parent)
        results_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        
        # Results title
        results_title = ctk.CTkLabel(
            results_frame,
            text="Analysis Results",
            font=theme_manager.get_font("heading")
        )
        results_title.grid(row=0, column=0, pady=10)
        
        # Results notebook
        self.results_notebook = ctk.CTkTabview(results_frame)
        self.results_notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Result tabs
        self.create_summary_tab()
        self.create_plots_tab()
        self.create_detailed_results_tab()
        
    def create_summary_tab(self):
        """Create summary results tab"""
        summary_tab = self.results_notebook.add("Summary")
        
        # Summary text area
        self.summary_text = tk.Text(
            summary_tab,
            wrap="word",
            font=theme_manager.get_font("monospace"),
            bg=theme_manager.get_color("bg_secondary"),
            fg=theme_manager.get_color("fg_primary"),
            insertbackground=theme_manager.get_color("fg_primary")
        )
        
        summary_scroll = ttk.Scrollbar(summary_tab, command=self.summary_text.yview)
        self.summary_text.config(yscrollcommand=summary_scroll.set)
        
        self.summary_text.pack(side="left", fill="both", expand=True)
        summary_scroll.pack(side="right", fill="y")
        
    def create_plots_tab(self):
        """Create plots visualization tab"""
        plots_tab = self.results_notebook.add("Plots")
        
        # Create matplotlib figure
        self.plots_fig = Figure(figsize=(12, 8), dpi=100)
        theme_manager.configure_matplotlib_figure(self.plots_fig)
        
        # Create canvas
        self.plots_canvas = FigureCanvasTkAgg(self.plots_fig, plots_tab)
        self.plots_canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Navigation toolbar
        toolbar_frame = ctk.CTkFrame(plots_tab)
        toolbar_frame.pack(fill="x")
        
        self.plots_toolbar = NavigationToolbar2Tk(self.plots_canvas, toolbar_frame)
        self.plots_toolbar.update()
        
    def create_detailed_results_tab(self):
        """Create detailed results tab"""
        detailed_tab = self.results_notebook.add("Detailed Results")
        
        # Detailed results text area
        self.detailed_text = tk.Text(
            detailed_tab,
            wrap="word",
            font=theme_manager.get_font("monospace"),
            bg=theme_manager.get_color("bg_secondary"),
            fg=theme_manager.get_color("fg_primary"),
            insertbackground=theme_manager.get_color("fg_primary")
        )
        
        detailed_scroll = ttk.Scrollbar(detailed_tab, command=self.detailed_text.yview)
        self.detailed_text.config(yscrollcommand=detailed_scroll.set)
        
        self.detailed_text.pack(side="left", fill="both", expand=True)
        detailed_scroll.pack(side="right", fill="y")
        
    def create_button_panel(self):
        """Create bottom button panel"""
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        
        # Export button
        export_btn = ctk.CTkButton(
            button_frame,
            text="Export Results",
            command=self.export_results,
            width=120
        )
        export_btn.pack(side="left", padx=5)
        
        # Close button
        close_btn = ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.close_dialog,
            width=100
        )
        close_btn.pack(side="right", padx=5)
        
    def populate_series_list(self):
        """Populate the series selection list"""
        self.series_vars = {}
        
        for series_id, config in self.series_configs.items():
            # Create checkbox for each series
            var = tk.BooleanVar(value=True)
            self.series_vars[series_id] = var
            
            # Series info frame
            series_frame = ctk.CTkFrame(self.series_scroll_frame)
            series_frame.pack(fill="x", pady=2)
            
            # Checkbox
            checkbox = ctk.CTkCheckBox(
                series_frame,
                text="",
                variable=var,
                width=20
            )
            checkbox.pack(side="left", padx=5)
            
            # Series info
            file_data = self.loaded_files.get(config.file_id)
            filename = file_data.filename if file_data else "Unknown File"
            
            info_text = f"{config.name} | {filename} | {config.y_column}"
            info_label = ctk.CTkLabel(
                series_frame,
                text=info_text,
                font=theme_manager.get_font("default")
            )
            info_label.pack(side="left", padx=5, fill="x", expand=True)
            
            # Color indicator
            color_frame = ctk.CTkFrame(
                series_frame,
                width=20,
                height=20,
                fg_color=config.color
            )
            color_frame.pack(side="right", padx=5)
            
    def select_all_series(self):
        """Select all series"""
        for var in self.series_vars.values():
            var.set(True)
            
    def clear_all_series(self):
        """Clear all series selection"""
        for var in self.series_vars.values():
            var.set(False)
            
    def get_selected_series(self) -> List[str]:
        """Get list of selected series IDs"""
        selected = []
        for series_id, var in self.series_vars.items():
            if var.get():
                selected.append(series_id)
        return selected
        
    def run_statistical_analysis(self):
        """Run statistical analysis on selected series"""
        try:
            selected_series = self.get_selected_series()
            if not selected_series:
                messagebox.showwarning("Warning", "Please select at least one series")
                return
                
            # Clear previous results
            self.summary_text.delete(1.0, tk.END)
            self.detailed_text.delete(1.0, tk.END)
            
            # Run analysis
            results = {}
            summary = "STATISTICAL ANALYSIS SUMMARY\n" + "="*50 + "\n\n"
            detailed = "DETAILED STATISTICAL ANALYSIS\n" + "="*60 + "\n\n"
            
            for series_id in selected_series:
                config = self.series_configs[series_id]
                file_data = self.loaded_files[config.file_id]
                
                # Get data
                x_data, y_data = self.get_series_data(config, file_data)
                
                if len(y_data) == 0:
                    continue
                    
                # Run statistical analysis
                series_results = {}
                
                if self.stats_options["basic_stats"].get():
                    series_results["basic_stats"] = self.statistical_analyzer.calculate_basic_stats(y_data)
                    
                if self.stats_options["normality_test"].get():
                    series_results["normality"] = self.statistical_analyzer.test_normality(y_data)
                    
                if self.stats_options["outlier_detection"].get():
                    series_results["outliers"] = self.statistical_analyzer.detect_outliers(y_data)
                    
                results[series_id] = series_results
                
                # Add to summary
                summary += f"Series: {config.name}\n"
                if "basic_stats" in series_results:
                    stats = series_results["basic_stats"]
                    summary += f"  Mean: {stats['mean']:.3e}\n"
                    summary += f"  Std:  {stats['std']:.3e}\n"
                    summary += f"  Min:  {stats['min']:.3e}\n"
                    summary += f"  Max:  {stats['max']:.3e}\n"
                    
                if "normality" in series_results:
                    norm = series_results["normality"]
                    summary += f"  Normal: {'Yes' if norm['is_normal'] else 'No'} (p={norm['p_value']:.3f})\n"
                    
                if "outliers" in series_results:
                    outliers = series_results["outliers"]
                    summary += f"  Outliers: {len(outliers)} detected\n"
                    
                summary += "\n"
                
                # Add detailed results
                detailed += f"SERIES: {config.name}\n" + "-"*40 + "\n"
                for key, value in series_results.items():
                    detailed += f"{key.upper()}:\n"
                    if isinstance(value, dict):
                        for k, v in value.items():
                            detailed += f"  {k}: {v}\n"
                    else:
                        detailed += f"  {value}\n"
                    detailed += "\n"
                detailed += "\n"
                
            # Store results
            self.analysis_results["statistical"] = results
            
            # Display results
            self.summary_text.insert(1.0, summary)
            self.detailed_text.insert(1.0, detailed)
            
            # Create plots
            self.create_statistical_plots(results)
            
            messagebox.showinfo("Success", "Statistical analysis completed!")
            
        except Exception as e:
            logger.error(f"Error in statistical analysis: {e}")
            messagebox.showerror("Error", f"Statistical analysis failed: {str(e)}")
            
    def run_vacuum_analysis(self):
        """Run vacuum-specific analysis"""
        try:
            selected_series = self.get_selected_series()
            if not selected_series:
                messagebox.showwarning("Warning", "Please select at least one series")
                return
                
            # Implementation similar to statistical analysis
            # but using vacuum-specific methods
            
            messagebox.showinfo("Info", "Vacuum analysis feature coming soon!")
            
        except Exception as e:
            logger.error(f"Error in vacuum analysis: {e}")
            messagebox.showerror("Error", f"Vacuum analysis failed: {str(e)}")
            
    def run_comparison_analysis(self):
        """Run series comparison analysis"""
        try:
            selected_series = self.get_selected_series()
            if len(selected_series) < 2:
                messagebox.showwarning("Warning", "Please select at least two series for comparison")
                return
                
            # Implementation for comparison analysis
            
            messagebox.showinfo("Info", "Comparison analysis feature coming soon!")
            
        except Exception as e:
            logger.error(f"Error in comparison analysis: {e}")
            messagebox.showerror("Error", f"Comparison analysis failed: {str(e)}")
            
    def get_series_data(self, config: SeriesConfig, file_data: FileData):
        """Get data for a series"""
        try:
            # Get data slice
            start_idx = config.start_index or 0
            end_idx = config.end_index or len(file_data.data)
            data_slice = file_data.data.iloc[start_idx:end_idx]
            
            # Get X data
            if config.x_column == "Index":
                x_data = np.arange(len(data_slice))
            else:
                x_data = data_slice[config.x_column].values
                if pd.api.types.is_object_dtype(x_data):
                    x_data = pd.to_numeric(x_data, errors='coerce')
                    
            # Get Y data
            y_data = data_slice[config.y_column].values
            if pd.api.types.is_object_dtype(y_data):
                y_data = pd.to_numeric(y_data, errors='coerce')
                
            # Remove NaN values
            mask = ~(pd.isna(x_data) | pd.isna(y_data))
            return x_data[mask], y_data[mask]
            
        except Exception as e:
            logger.error(f"Error getting series data: {e}")
            return np.array([]), np.array([])
            
    def create_statistical_plots(self, results):
        """Create statistical visualization plots"""
        try:
            self.plots_fig.clear()
            
            # Create subplots
            if len(results) == 1:
                axes = [self.plots_fig.add_subplot(111)]
            elif len(results) <= 4:
                rows, cols = (2, 2) if len(results) > 2 else (1, len(results))
                axes = []
                for i in range(len(results)):
                    axes.append(self.plots_fig.add_subplot(rows, cols, i+1))
            else:
                # More than 4 series - create histogram comparison
                axes = [self.plots_fig.add_subplot(111)]
                
            # Apply theme to all axes
            for ax in axes:
                theme_manager.configure_matplotlib_figure(self.plots_fig, ax)
                
            # Plot data for each series
            for i, (series_id, series_results) in enumerate(results.items()):
                if i >= len(axes):
                    break
                    
                config = self.series_configs[series_id]
                file_data = self.loaded_files[config.file_id]
                x_data, y_data = self.get_series_data(config, file_data)
                
                ax = axes[i] if len(axes) > 1 else axes[0]
                
                # Plot histogram of data
                ax.hist(y_data, bins=50, alpha=0.7, color=config.color, label=config.name)
                ax.set_xlabel("Value")
                ax.set_ylabel("Frequency")
                ax.set_title(f"Distribution: {config.name}")
                ax.legend()
                
                # Add statistics text
                if "basic_stats" in series_results:
                    stats = series_results["basic_stats"]
                    stats_text = f"μ = {stats['mean']:.2e}\nσ = {stats['std']:.2e}"
                    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                           verticalalignment='top', fontsize=10,
                           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
                           
            self.plots_fig.tight_layout()
            self.plots_canvas.draw()
            
        except Exception as e:
            logger.error(f"Error creating statistical plots: {e}")
            
    def export_results(self):
        """Export analysis results"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Export Analysis Results",
                defaultextension=".txt",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("CSV files", "*.csv"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write("MULTI-SERIES ANALYSIS RESULTS\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*60 + "\n\n")
                    
                    # Write summary
                    f.write("SUMMARY:\n")
                    f.write(self.summary_text.get(1.0, tk.END))
                    f.write("\n\n")
                    
                    # Write detailed results
                    f.write("DETAILED RESULTS:\n")
                    f.write(self.detailed_text.get(1.0, tk.END))
                    
                messagebox.showinfo("Success", f"Results exported to:\n{filename}")
                
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            messagebox.showerror("Error", f"Failed to export results: {str(e)}")
            
    def close_dialog(self):
        """Close the dialog"""
        self.result = 'close'
        self.dialog.destroy()


def show_multi_series_analysis(parent, series_configs: Dict[str, SeriesConfig], 
                                       loaded_files: Dict[str, FileData]):
    """Show the enhanced multi-series analysis dialog"""
    dialog = MultiSeriesAnalysisDialog(parent, series_configs, loaded_files)
    parent.wait_window(dialog.dialog)
    return dialog.result
