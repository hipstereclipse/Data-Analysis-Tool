#!/usr/bin/env python3
"""
Enhanced Vacuum Analysis Dialog - Full Legacy Functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from analysis.legacy_analysis_tools import VacuumAnalysisTools, DataAnalysisTools
from models.data_models import FileData, SeriesConfig
from ui.components import CollapsiblePanel
from ui.theme_manager import ThemeManager


class VacuumAnalysisDialog:
    """
    Enhanced vacuum analysis dialog with full legacy functionality
    """

    def __init__(self, parent, selected_series=None, all_series=None, loaded_files=None):
        """
        Initialize the vacuum analysis dialog

        Args:
            parent: Parent window
            selected_series: Initially selected series
            all_series: Dictionary of all available series
            loaded_files: Dictionary of all loaded files
        """
        self.parent = parent
        self.selected_series = selected_series
        self.all_series = all_series or {}
        self.loaded_files = loaded_files or {}
        self.result = None
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()

        # Analysis results storage
        self.analysis_results = {}

        # Create dialog window
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Vacuum Data Analysis Tools")
        self.dialog.geometry("1200x800")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Center the dialog
        self.center_dialog()

        # Create the interface
        self.create_widgets()

    def center_dialog(self):
        """Center the dialog on parent window"""
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        x = parent_x + (parent_width - 1200) // 2
        y = parent_y + (parent_height - 800) // 2

        self.dialog.geometry(f"1200x800+{x}+{y}")

    def create_widgets(self):
        """Create the dialog interface"""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create notebook for different analysis types
        self.notebook = ctk.CTkTabview(main_frame)
        self.notebook.pack(fill="both", expand=True)

        # Create analysis tabs
        self.create_base_pressure_tab()
        self.create_leak_rate_tab()
        self.create_noise_analysis_tab()
        self.create_spike_detection_tab()
        self.create_pump_down_tab()
        self.create_outgassing_tab()

        # Button frame
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(
            btn_frame,
            text="Close",
            command=self.close_dialog,
            width=100
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Export Results",
            command=self.export_results,
            width=120
        ).pack(side="right", padx=5)

    def create_base_pressure_tab(self):
        """Create base pressure analysis tab"""
        tab = self.notebook.add("Base Pressure")
        
        # Controls frame
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.pack(fill="x", padx=10, pady=10)

        # Series selection
        ctk.CTkLabel(controls_frame, text="Select Series:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.base_pressure_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.id[:8]})" for s in self.all_series.values()]
        self.base_pressure_combo = ctk.CTkComboBox(
            controls_frame,
            variable=self.base_pressure_series_var,
            values=series_options,
            width=300
        )
        self.base_pressure_combo.grid(row=0, column=1, padx=5, pady=5)

        # Analysis parameters
        ctk.CTkLabel(controls_frame, text="Window (minutes):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.window_var = tk.IntVar(value=10)
        ctk.CTkEntry(controls_frame, textvariable=self.window_var, width=80).grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Analyze",
            command=self.analyze_base_pressure,
            width=100
        ).grid(row=0, column=4, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Add Base Pressure Annotation",
            command=self.add_base_pressure_annotation,
            width=220
        ).grid(row=0, column=5, padx=5, pady=5)

        # Results frame
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Plot area
        self.base_pressure_plot_frame = ctk.CTkFrame(results_frame)
        self.base_pressure_plot_frame.pack(fill="both", expand=True, side="left")

        # Results text
        self.base_pressure_results = ctk.CTkTextbox(results_frame, width=250)
        self.base_pressure_results.pack(fill="y", side="right", padx=(10, 0))

    def create_leak_rate_tab(self):
        """Create leak rate analysis tab"""
        tab = self.notebook.add("Leak Rate")
        
        # Controls
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(controls_frame, text="Select Series:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.leak_rate_series_var = tk.StringVar()
        self.leak_rate_combo = ctk.CTkComboBox(
            controls_frame,
            variable=self.leak_rate_series_var,
            values=[f"{s.name} ({s.id[:8]})" for s in self.all_series.values()],
            width=300
        )
        self.leak_rate_combo.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(controls_frame, text="Volume (L):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.volume_var = tk.DoubleVar(value=1.0)
        ctk.CTkEntry(controls_frame, textvariable=self.volume_var, width=80).grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Analyze",
            command=self.analyze_leak_rate,
            width=100
        ).grid(row=0, column=4, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Annotate Leak Rate",
            command=self.add_leak_rate_annotation,
            width=180
        ).grid(row=0, column=5, padx=5, pady=5)

        # Annotation controls for leak rate (mirrored from spike detection)
        ctk.CTkLabel(controls_frame, text="Color:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.leak_color_var = tk.StringVar(value="blue")
        ctk.CTkEntry(controls_frame, textvariable=self.leak_color_var, width=100).grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(controls_frame, text="Label:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.leak_label_var = tk.StringVar(value="")
        ctk.CTkEntry(controls_frame, textvariable=self.leak_label_var, width=180).grid(row=1, column=3, padx=5, pady=5)

        # Results
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.leak_rate_plot_frame = ctk.CTkFrame(results_frame)
        self.leak_rate_plot_frame.pack(fill="both", expand=True, side="left")

        self.leak_rate_results = ctk.CTkTextbox(results_frame, width=250)
        self.leak_rate_results.pack(fill="y", side="right", padx=(10, 0))

    def create_noise_analysis_tab(self):
        """Create noise analysis tab"""
        tab = self.notebook.add("Noise Analysis")
        
        # Controls
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(controls_frame, text="Select Series:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.noise_series_var = tk.StringVar()
        self.noise_combo = ctk.CTkComboBox(
            controls_frame,
            variable=self.noise_series_var,
            values=[f"{s.name} ({s.id[:8]})" for s in self.all_series.values()],
            width=300
        )
        self.noise_combo.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(controls_frame, text="Sample Rate (Hz):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.sample_rate_var = tk.DoubleVar(value=1.0)
        ctk.CTkEntry(controls_frame, textvariable=self.sample_rate_var, width=80).grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Analyze",
            command=self.analyze_noise,
            width=100
        ).grid(row=0, column=4, padx=5, pady=5)

        # Results
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.noise_plot_frame = ctk.CTkFrame(results_frame)
        self.noise_plot_frame.pack(fill="both", expand=True, side="left")

        self.noise_results = ctk.CTkTextbox(results_frame, width=250)
        self.noise_results.pack(fill="y", side="right", padx=(10, 0))

    def create_spike_detection_tab(self):
        """Create spike detection tab"""
        tab = self.notebook.add("Spike Detection")
        
        # Controls
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(controls_frame, text="Select Series:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.spike_series_var = tk.StringVar()
        self.spike_combo = ctk.CTkComboBox(
            controls_frame,
            variable=self.spike_series_var,
            values=[f"{s.name} ({s.id[:8]})" for s in self.all_series.values()],
            width=300
        )
        self.spike_combo.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(controls_frame, text="Threshold:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.threshold_var = tk.DoubleVar(value=3.0)
        ctk.CTkEntry(controls_frame, textvariable=self.threshold_var, width=80).grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Detect",
            command=self.detect_spikes,
            width=100
        ).grid(row=0, column=4, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Annotate Top Spike",
            command=self.add_top_spike_annotation,
            width=180
        ).grid(row=0, column=5, padx=5, pady=5)

        # Optional UX: color and label inputs + annotate all
        ctk.CTkLabel(controls_frame, text="Color:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.spike_color_var = tk.StringVar(value="red")
        ctk.CTkEntry(controls_frame, textvariable=self.spike_color_var, width=100).grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(controls_frame, text="Label:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.spike_label_var = tk.StringVar(value="")
        ctk.CTkEntry(controls_frame, textvariable=self.spike_label_var, width=180).grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Annotate All Spikes",
            command=self.annotate_all_spikes,
            width=180
        ).grid(row=1, column=4, padx=5, pady=5)

        # Results
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.spike_plot_frame = ctk.CTkFrame(results_frame)
        self.spike_plot_frame.pack(fill="both", expand=True, side="left")

        self.spike_results = ctk.CTkTextbox(results_frame, width=250)
        self.spike_results.pack(fill="y", side="right", padx=(10, 0))

    def create_pump_down_tab(self):
        """Create pump down analysis tab"""
        tab = self.notebook.add("Pump Down")
        
        # Controls
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(controls_frame, text="Select Series:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.pump_series_var = tk.StringVar()
        self.pump_combo = ctk.CTkComboBox(
            controls_frame,
            variable=self.pump_series_var,
            values=[f"{s.name} ({s.id[:8]})" for s in self.all_series.values()],
            width=300
        )
        self.pump_combo.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Analyze",
            command=self.analyze_pump_down,
            width=100
        ).grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Annotate Pumpdown Window",
            command=self.add_pumpdown_annotation,
            width=220
        ).grid(row=0, column=3, padx=5, pady=5)

        # Annotation controls for pump down (mirrored from spike detection)
        ctk.CTkLabel(controls_frame, text="Color:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.pumpdown_color_var = tk.StringVar(value="green")
        ctk.CTkEntry(controls_frame, textvariable=self.pumpdown_color_var, width=100).grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(controls_frame, text="Label:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.pumpdown_label_var = tk.StringVar(value="")
        ctk.CTkEntry(controls_frame, textvariable=self.pumpdown_label_var, width=180).grid(row=1, column=3, padx=5, pady=5)

        # Results
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.pump_plot_frame = ctk.CTkFrame(results_frame)
        self.pump_plot_frame.pack(fill="both", expand=True, side="left")

        self.pump_results = ctk.CTkTextbox(results_frame, width=250)
        self.pump_results.pack(fill="y", side="right", padx=(10, 0))

    def create_outgassing_tab(self):
        """Create outgassing analysis tab"""
        tab = self.notebook.add("Outgassing")
        
        # Controls
        controls_frame = ctk.CTkFrame(tab)
        controls_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(controls_frame, text="Select Series:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.outgas_series_var = tk.StringVar()
        self.outgas_combo = ctk.CTkComboBox(
            controls_frame,
            variable=self.outgas_series_var,
            values=[f"{s.name} ({s.id[:8]})" for s in self.all_series.values()],
            width=300
        )
        self.outgas_combo.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(controls_frame, text="Volume (L):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self.outgas_volume_var = tk.DoubleVar(value=1.0)
        ctk.CTkEntry(controls_frame, textvariable=self.outgas_volume_var, width=80).grid(row=0, column=3, padx=5, pady=5)

        ctk.CTkButton(
            controls_frame,
            text="Analyze",
            command=self.analyze_outgassing,
            width=100
        ).grid(row=0, column=4, padx=5, pady=5)

        # Results
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.outgas_plot_frame = ctk.CTkFrame(results_frame)
        self.outgas_plot_frame.pack(fill="both", expand=True, side="left")

        self.outgas_results = ctk.CTkTextbox(results_frame, width=250)
        self.outgas_results.pack(fill="y", side="right", padx=(10, 0))

    def get_series_data(self, series_var):
        """Get data from selected series"""
        selection = series_var.get()
        if not selection:
            return None, None, None

        series_id = selection.split('(')[-1].rstrip(')')
        
        # Find matching series
        for sid, series in self.all_series.items():
            if sid.startswith(series_id):
                file_data = self.loaded_files.get(series.file_id)
                if file_data:
                    x_data, y_data = series.get_data(file_data)
                    return series, x_data, y_data
        
        return None, None, None

    def analyze_base_pressure(self):
        """Analyze base pressure"""
        series, x_data, y_data = self.get_series_data(self.base_pressure_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series")
            return

        try:
            # Perform analysis
            window_minutes = self.window_var.get()
            base_pressure, rolling_min, rolling_std = VacuumAnalysisTools.calculate_base_pressure(
                y_data, window_minutes=window_minutes
            )

            # Create plot
            self.create_base_pressure_plot(x_data, y_data, rolling_min, rolling_std, base_pressure)

            # Display results
            results_text = f"""Base Pressure Analysis Results:

Base Pressure: {base_pressure:.3e} mbar
Analysis Window: {window_minutes} minutes

The base pressure represents the lowest stable 
pressure achieved by the vacuum system.

Rolling minimum and standard deviation are 
shown in the plot to illustrate pressure 
stability over time."""

            self.base_pressure_results.delete("1.0", "end")
            self.base_pressure_results.insert("1.0", results_text)

            # Store results
            self.analysis_results['base_pressure'] = {
                'base_pressure': base_pressure,
                'window_minutes': window_minutes,
                'series_name': series.name
            }

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")

    def create_base_pressure_plot(self, x_data, y_data, rolling_min, rolling_std, base_pressure):
        """Create base pressure analysis plot"""
        # Clear existing plot
        for widget in self.base_pressure_plot_frame.winfo_children():
            widget.destroy()

        # Create matplotlib figure
        fig = Figure(figsize=(8, 6), facecolor=self.theme_manager.get_color("bg_secondary"))
        ax = fig.add_subplot(111)

        # Plot data
        ax.plot(x_data, y_data, 'b-', alpha=0.7, label='Pressure Data')
        ax.plot(x_data, rolling_min, 'g-', linewidth=2, label='Rolling Minimum')
        ax.axhline(y=base_pressure, color='r', linestyle='--', linewidth=2, label=f'Base Pressure: {base_pressure:.3e}')

        ax.set_xlabel('Time/Index')
        ax.set_ylabel('Pressure (mbar)')
        ax.set_title('Base Pressure Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')

        # Embed plot
        canvas = FigureCanvasTkAgg(fig, self.base_pressure_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def analyze_leak_rate(self):
        """Analyze leak rate"""
        series, x_data, y_data = self.get_series_data(self.leak_rate_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series")
            return

        try:
            # Perform leak rate analysis
            volume = self.volume_var.get()
            start_pressure = y_data[0]
            
            results = VacuumAnalysisTools.calculate_leak_rate(
                y_data, x_data, start_pressure
            )

            # Create plot
            if 'fitted_curve' in results:
                self.create_leak_rate_plot(x_data, y_data, results['fitted_curve'])
            elif 'linear_fit' in results:
                self.create_leak_rate_plot(x_data, y_data, results['linear_fit'].get('fitted_curve', []))

            # Display enhanced results
            results_text = f"""Leak Rate Analysis Results:

Analysis Methods:"""

            # Linear fit results
            if 'linear_fit' in results:
                linear = results['linear_fit']
                results_text += f"""

Linear Fit Method:
  Leak Rate: {linear.get('leak_rate', 0):.3e} mbar·L/s
  R-squared: {linear.get('r_squared', 0):.4f}
  Pressure Rise Rate: {linear.get('pressure_rise_rate', 0):.3e} mbar/s"""

            # Exponential fit results  
            if 'exponential_fit' in results:
                exp = results['exponential_fit']
                results_text += f"""

Exponential Fit Method:
  Leak Rate: {exp.get('leak_rate', 0):.3e} mbar·L/s
  Time Constant: {exp.get('time_constant', 0):.1f} s
  R-squared: {exp.get('r_squared', 0):.4f}"""

            # Conductance-based results
            if 'conductance_based' in results:
                cond = results['conductance_based']
                results_text += f"""

Conductance-Based Method:
  Leak Rate: {cond.get('leak_rate', 0):.3e} mbar·L/s
  Effective Conductance: {cond.get('conductance', 0):.3e} L/s"""

            # Overall assessment
            if 'severity' in results:
                results_text += f"""

Overall Assessment:
  Severity: {results['severity'].title()}
  Primary Method: {results.get('primary_method', 'unknown')}
  Confidence: {results.get('confidence', 'unknown')}"""

            results_text += f"""

System Volume: {volume} L

The leak rate represents the rate of pressure 
increase due to leaks in the vacuum system.
Multiple calculation methods provide different
perspectives on leak characteristics."""

            self.leak_rate_results.delete("1.0", "end")
            self.leak_rate_results.insert("1.0", results_text)

            # Store enhanced results
            self.analysis_results['leak_rate'] = {
                'linear_fit': results.get('linear_fit', {}),
                'exponential_fit': results.get('exponential_fit', {}),
                'conductance_based': results.get('conductance_based', {}),
                'severity': results.get('severity'),
                'primary_method': results.get('primary_method'),
                'volume': volume,
                'series_name': series.name
            }

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")

    def create_leak_rate_plot(self, x_data, y_data, fitted_curve):
        """Create leak rate analysis plot"""
        # Clear existing plot
        for widget in self.leak_rate_plot_frame.winfo_children():
            widget.destroy()

        # Create matplotlib figure
        fig = Figure(figsize=(8, 6), facecolor=self.theme_manager.get_color("bg_secondary"))
        ax = fig.add_subplot(111)

        # Plot data
        ax.plot(x_data, y_data, 'bo', alpha=0.6, label='Measured Data')
        ax.plot(x_data, fitted_curve, 'r-', linewidth=2, label='Exponential Fit')

        ax.set_xlabel('Time')
        ax.set_ylabel('Pressure (mbar)')
        ax.set_title('Leak Rate Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')

        # Embed plot
        canvas = FigureCanvasTkAgg(fig, self.leak_rate_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def analyze_noise(self):
        """Analyze noise characteristics"""
        series, x_data, y_data = self.get_series_data(self.noise_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series")
            return

        try:
            # Perform noise analysis
            sample_rate = self.sample_rate_var.get()
            results = VacuumAnalysisTools.calculate_noise_metrics(y_data, sample_rate)

            # Create plot
            self.create_noise_plot(results)

            # Display results
            results_text = f"""Noise Analysis Results:

RMS Noise: {results['noise_rms']:.3e} mbar
Peak-to-Peak: {results['noise_p2p']:.3e} mbar
Dominant Frequency: {results['dominant_freq']:.3f} Hz
Sample Rate: {sample_rate} Hz

RMS noise represents the typical noise level.
Peak-to-peak shows maximum noise excursions.
Dominant frequency indicates the main noise 
component frequency.

Lower noise levels indicate better vacuum 
stability and measurement quality."""

            self.noise_results.delete("1.0", "end")
            self.noise_results.insert("1.0", results_text)

            # Store results
            self.analysis_results['noise'] = {
                'noise_rms': results['noise_rms'],
                'noise_p2p': results['noise_p2p'],
                'dominant_freq': results['dominant_freq'],
                'sample_rate': sample_rate,
                'series_name': series.name
            }

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")

    def create_noise_plot(self, results):
        """Create noise analysis plot"""
        # Clear existing plot
        for widget in self.noise_plot_frame.winfo_children():
            widget.destroy()

        # Create matplotlib figure
        fig = Figure(figsize=(8, 6), facecolor=self.theme_manager.get_color("bg_secondary"))
        
        # Detrended signal
        ax1 = fig.add_subplot(211)
        ax1.plot(results['detrended_signal'], 'b-', alpha=0.7)
        ax1.set_ylabel('Detrended Signal')
        ax1.set_title('Noise Analysis')
        ax1.grid(True, alpha=0.3)

        # Power spectrum
        ax2 = fig.add_subplot(212)
        ax2.semilogy(results['frequencies'], results['power_spectrum'], 'r-')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Power')
        ax2.set_title('Power Spectrum')
        ax2.grid(True, alpha=0.3)

        fig.tight_layout()

        # Embed plot
        canvas = FigureCanvasTkAgg(fig, self.noise_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def detect_spikes(self):
        """Detect pressure spikes"""
        series, x_data, y_data = self.get_series_data(self.spike_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series")
            return

        try:
            # Detect spikes
            threshold = self.threshold_var.get()
            spikes = VacuumAnalysisTools.detect_pressure_spikes(y_data, threshold_factor=threshold)

            # Create plot
            self.create_spike_plot(x_data, y_data, spikes)

            # Display enhanced results
            if spikes:
                # Group spikes by severity
                severity_counts = {}
                for spike in spikes:
                    severity = spike.get('severity', 'unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                severity_summary = "\n".join([f"{sev.title()}: {count}" for sev, count in severity_counts.items()])
                
                # Show detailed spike information
                spike_details = []
                for i, s in enumerate(spikes[:10]):  # Show first 10 spikes
                    spike_info = f"Spike {i+1}: "
                    spike_info += f"Start={s['start']}, Duration={s['duration']}, "
                    spike_info += f"Max={s['max_pressure']:.2e}, "
                    spike_info += f"Baseline={s.get('baseline_pressure', 0):.2e}, "
                    spike_info += f"Ratio={s.get('pressure_ratio', 0):.1f}x, "
                    spike_info += f"Severity={s.get('severity', 'unknown')}"
                    spike_details.append(spike_info)
                
                spike_summary = "\n".join(spike_details)
                
                results_text = f"""Spike Detection Results:

Threshold Factor: {threshold} σ
Total Spikes Found: {len(spikes)}

Severity Distribution:
{severity_summary}

Detailed Spike Information:
{spike_summary}

{"... (showing first 10 spikes)" if len(spikes) > 10 else ""}

Spikes indicate sudden pressure increases
that may be caused by outgassing events,
leaks, or contamination. Severity is based
on pressure ratio compared to baseline."""
            else:
                results_text = f"""Spike Detection Results:

Threshold Factor: {threshold} σ
Total Spikes Found: 0

No pressure spikes detected with the current
threshold setting. Try lowering the threshold
to detect smaller pressure variations."""

            self.spike_results.delete("1.0", "end")
            self.spike_results.insert("1.0", results_text)

            # Store results
            self.analysis_results['spikes'] = {
                'threshold': threshold,
                'spike_count': len(spikes),
                'spikes': spikes,
                'series_name': series.name
            }

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")

    def create_spike_plot(self, x_data, y_data, spikes):
        """Create spike detection plot"""
        # Clear existing plot
        for widget in self.spike_plot_frame.winfo_children():
            widget.destroy()

        # Create matplotlib figure
        fig = Figure(figsize=(8, 6), facecolor=self.theme_manager.get_color("bg_secondary"))
        ax = fig.add_subplot(111)

        # Plot data
        ax.plot(x_data, y_data, 'b-', alpha=0.7, label='Pressure Data')

        # Highlight spikes
        for spike in spikes:
            start_idx = spike['start']
            end_idx = spike['end']
            if end_idx < len(x_data):
                color = 'red' if spike['severity'] == 'high' else 'orange'
                ax.axvspan(x_data[start_idx], x_data[end_idx], alpha=0.3, color=color)

        ax.set_xlabel('Time/Index')
        ax.set_ylabel('Pressure (mbar)')
        ax.set_title('Pressure Spike Detection')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')

        # Embed plot
        canvas = FigureCanvasTkAgg(fig, self.spike_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def analyze_pump_down(self):
        """Analyze pump down curve"""
        series, x_data, y_data = self.get_series_data(self.pump_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series")
            return

        try:
            # Perform pump down analysis
            results = VacuumAnalysisTools.analyze_pump_down_curve(y_data, x_data)

            # Create plot
            self.create_pump_down_plot(x_data, y_data, results)

            # Display enhanced results
            results_text = f"""Pump Down Analysis Results:

Initial Pressure: {results.get('initial_pressure', 0):.3e} mbar
Final Pressure: {results.get('final_pressure', 0):.3e} mbar
Ultimate Vacuum: {results.get('ultimate_vacuum', 'N/A')}

Pressure Milestones:"""

            # Add milestones if available
            milestones = results.get('milestones', {})
            for level, time in milestones.items():
                if isinstance(time, str):
                    results_text += f"\n{level}: {time}"
                else:
                    results_text += f"\n{level}: {time:.2f}s"

            # Add enhanced features
            if 'pump_rate_phases' in results:
                phases = results['pump_rate_phases']
                results_text += f"\n\nPump Rate Phases:"
                for phase in phases:
                    results_text += f"\n  {phase['pressure_range']}: {phase['avg_rate']:.3e} mbar/s"

            if 'time_constant' in results:
                results_text += f"\n\nTime Constant: {results['time_constant']:.2f}s"

            if 'exponential_fit' in results:
                fit = results['exponential_fit']
                results_text += f"\nExponential Fit R²: {fit.get('r_squared', 0):.4f}"

            if 'pump_efficiency' in results:
                results_text += f"\nPump Efficiency: {results['pump_efficiency']}"

            results_text += "\n\nThe pump down curve shows the effectiveness\nof the vacuum pumping system. Faster pump\ndown indicates better pumping speed.\n\nMilestones show time to reach standard\nvacuum levels."

            self.pump_results.delete("1.0", "end")
            self.pump_results.insert("1.0", results_text)

            # Store enhanced results
            self.analysis_results['pump_down'] = {
                'initial_pressure': results.get('initial_pressure', 0),
                'final_pressure': results.get('final_pressure', 0),
                'milestones': results.get('milestones', {}),
                'time_constant': results.get('time_constant'),
                'pump_efficiency': results.get('pump_efficiency'),
                'exponential_fit': results.get('exponential_fit'),
                'series_name': series.name
            }

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")

    def create_pump_down_plot(self, x_data, y_data, results):
        """Create pump down analysis plot"""
        # Clear existing plot
        for widget in self.pump_plot_frame.winfo_children():
            widget.destroy()

        # Create matplotlib figure
        fig = Figure(figsize=(8, 6), facecolor=self.theme_manager.get_color("bg_secondary"))
        ax = fig.add_subplot(111)

        # Plot data
        ax.plot(x_data, y_data, 'b-', linewidth=2, label='Pump Down Curve')

        # Mark milestones
        for level, time_point in results['milestones'].items():
            pressure_value = float(level.split()[0])
            ax.axhline(y=pressure_value, color='red', linestyle='--', alpha=0.7)
            ax.text(x_data[-1]*0.8, pressure_value*1.5, level, fontsize=8)

        ax.set_xlabel('Time')
        ax.set_ylabel('Pressure (mbar)')
        ax.set_title('Pump Down Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')

        # Embed plot
        canvas = FigureCanvasTkAgg(fig, self.pump_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def analyze_outgassing(self):
        """Analyze outgassing rate"""
        series, x_data, y_data = self.get_series_data(self.outgas_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series")
            return

        try:
            # Perform outgassing analysis
            volume = self.outgas_volume_var.get()
            results = VacuumAnalysisTools.calculate_outgassing_rate(y_data, x_data, volume)

            # Create plot
            self.create_outgassing_plot(x_data, results['outgassing_rate'])

            # Display results
            results_text = f"""Outgassing Analysis Results:

Average Rate: {results['average_rate']:.3e} {results['units']}
System Volume: {volume} L

Outgassing rate represents the rate at which
gases are released from surfaces and materials
in the vacuum system.

Lower outgassing rates indicate cleaner
surfaces and better vacuum performance.

The plot shows the time-dependent outgassing
rate calculated from pressure rise."""

            self.outgas_results.delete("1.0", "end")
            self.outgas_results.insert("1.0", results_text)

            # Store results
            self.analysis_results['outgassing'] = {
                'average_rate': results['average_rate'],
                'volume': volume,
                'units': results['units'],
                'series_name': series.name
            }

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")

    def create_outgassing_plot(self, x_data, outgassing_rate):
        """Create outgassing analysis plot"""
        # Clear existing plot
        for widget in self.outgas_plot_frame.winfo_children():
            widget.destroy()

        # Create matplotlib figure
        fig = Figure(figsize=(8, 6), facecolor=self.theme_manager.get_color("bg_secondary"))
        ax = fig.add_subplot(111)

        # Plot outgassing rate
        ax.plot(x_data, outgassing_rate, 'g-', linewidth=2, label='Outgassing Rate')
        ax.axhline(y=np.mean(outgassing_rate), color='r', linestyle='--', 
                   label=f'Average: {np.mean(outgassing_rate):.3e}')

        ax.set_xlabel('Time')
        ax.set_ylabel('Outgassing Rate (mbar·L/s)')
        ax.set_title('Outgassing Rate Analysis')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Embed plot
        canvas = FigureCanvasTkAgg(fig, self.outgas_plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_results(self):
        """Export analysis results"""
        if not self.analysis_results:
            messagebox.showwarning("Warning", "No analysis results to export")
            return

        # Create export dialog or save directly
        messagebox.showinfo("Export", "Results export functionality would be implemented here")

    # --- Quick annotation helpers ---
    def _get_main_app(self):
        return getattr(self, 'parent', None)

    def _refresh_main_plot(self):
        app = self._get_main_app()
        if app and hasattr(app, 'create_plot'):
            app.create_plot()

    def add_base_pressure_annotation(self):
        app = self._get_main_app()
        if not app or not hasattr(app, 'annotation_manager'):
            messagebox.showwarning("Warning", "Main plot/annotations not available")
            return
        series, x_data, y_data = self.get_series_data(self.base_pressure_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series and analyze first")
            return
        # Use existing analysis result if available; otherwise compute quickly
        if 'base_pressure' in self.analysis_results:
            bp = self.analysis_results['base_pressure']['base_pressure']
        else:
            try:
                bp, _, _ = VacuumAnalysisTools.calculate_base_pressure(y_data, window_minutes=self.window_var.get())
            except Exception:
                messagebox.showerror("Error", "Could not compute base pressure")
                return
        # Determine x-range from main plot if available
        if getattr(app, 'plot_axes', None):
            x_start, x_end = app.plot_axes.get_xlim()
        else:
            x_start, x_end = (float(x_data[0]), float(x_data[-1]))
        app.annotation_manager.add_base_pressure_annotation(x_start, x_end, bp, series.name)
        self._refresh_main_plot()

    def add_leak_rate_annotation(self):
        app = self._get_main_app()
        if not app or not hasattr(app, 'annotation_manager'):
            messagebox.showwarning("Warning", "Main plot/annotations not available")
            return
        if 'leak_rate' not in self.analysis_results:
            self.analyze_leak_rate()
            if 'leak_rate' not in self.analysis_results:
                return
        lr = self.analysis_results['leak_rate']['leak_rate']
        series, x_data, y_data = self.get_series_data(self.leak_rate_series_var)
        if getattr(app, 'plot_axes', None):
            x_start, x_end = app.plot_axes.get_xlim()
        else:
            x_start, x_end = (float(x_data[0]), float(x_data[-1]))
        
        # Use color and label from controls
        color = getattr(self, 'leak_color_var', None).get() if hasattr(self, 'leak_color_var') else 'blue'
        base_label = getattr(self, 'leak_label_var', None).get() if hasattr(self, 'leak_label_var') else ''
        label = base_label or f"Leak Rate: {lr:.2e}"
        
        app.annotation_manager.add_leak_annotation(x_start, x_end, lr, series.name, color=color, label=label)
        self._refresh_main_plot()

    def add_top_spike_annotation(self):
        app = self._get_main_app()
        if not app or not hasattr(app, 'annotation_manager'):
            messagebox.showwarning("Warning", "Main plot/annotations not available")
            return
        series, x_data, y_data = self.get_series_data(self.spike_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series")
            return
        threshold = self.threshold_var.get()
        spikes = VacuumAnalysisTools.detect_pressure_spikes(y_data, threshold_factor=threshold)
        if not spikes:
            messagebox.showinfo("Info", "No spikes found at current threshold")
            return
        # Choose the spike with max_pressure
        top = max(spikes, key=lambda s: s.get('max_pressure', 0))
        idx = top['start']
        x = float(x_data[idx])
        y = float(top['max_pressure'])
        color = getattr(self, 'spike_color_var', None).get() if hasattr(self, 'spike_color_var') else 'red'
        base_label = getattr(self, 'spike_label_var', None).get() if hasattr(self, 'spike_label_var') else ''
        label = base_label or f"Spike {y:.2e}"
        app.annotation_manager.add_spike_annotation(x, y, magnitude=y, series_name=series.name, label=label, color=color)
        self._refresh_main_plot()

    def annotate_all_spikes(self):
        app = self._get_main_app()
        if not app or not hasattr(app, 'annotation_manager'):
            messagebox.showwarning("Warning", "Main plot/annotations not available")
            return
        series, x_data, y_data = self.get_series_data(self.spike_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series")
            return
        threshold = self.threshold_var.get()
        spikes = VacuumAnalysisTools.detect_pressure_spikes(y_data, threshold_factor=threshold)
        if not spikes:
            messagebox.showinfo("Info", "No spikes found at current threshold")
            return
        color = getattr(self, 'spike_color_var', None).get() if hasattr(self, 'spike_color_var') else 'red'
        base_label = getattr(self, 'spike_label_var', None).get() if hasattr(self, 'spike_label_var') else ''
        for i, s in enumerate(spikes, start=1):
            idx = s.get('start', s.get('index', 0))
            x = float(x_data[idx])
            y = float(s.get('max_pressure', y_data[idx]))
            label = base_label or f"Spike {i}: {y:.2e}"
            app.annotation_manager.add_spike_annotation(x, y, magnitude=y, series_name=series.name, label=label, color=color)
        self._refresh_main_plot()

    def add_pumpdown_annotation(self):
        app = self._get_main_app()
        if not app or not hasattr(app, 'annotation_manager'):
            messagebox.showwarning("Warning", "Main plot/annotations not available")
            return
        series, x_data, y_data = self.get_series_data(self.pump_series_var)
        if series is None:
            messagebox.showwarning("Warning", "Please select a series")
            return
        try:
            results = VacuumAnalysisTools.analyze_pump_down_curve(y_data, x_data)
        except Exception as e:
            messagebox.showerror("Error", f"Pumpdown analysis failed: {e}")
            return
        # Use entire series range
        x_start = float(x_data[0])
        x_end = float(x_data[-1])
        p_initial = float(results.get('initial_pressure', y_data[0]))
        p_final = float(results.get('final_pressure', y_data[-1]))
        
        # Use color and label from controls
        color = getattr(self, 'pumpdown_color_var', None).get() if hasattr(self, 'pumpdown_color_var') else 'green'
        base_label = getattr(self, 'pumpdown_label_var', None).get() if hasattr(self, 'pumpdown_label_var') else ''
        label = base_label or f"Pumpdown {p_initial:.1e}→{p_final:.1e}"
        
        app.annotation_manager.add_pumpdown_annotation(x_start, x_end, p_initial, p_final=p_final, label=label, series_name=series.name, color=color)
        self._refresh_main_plot()

    def close_dialog(self):
        """Close the dialog"""
        self.dialog.destroy()
