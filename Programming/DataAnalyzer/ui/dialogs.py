#!/usr/bin/env python3
"""
Dialog windows for user interaction - FIXED VERSION WITH LEGACY FEATURES
"""

import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, colorchooser, filedialog
import customtkinter as ctk
from typing import Optional, Dict, List, Any, Callable
import numpy as np
import pandas as pd
from pathlib import Path
import json
import logging

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from analysis.vacuum import VacuumAnalyzer
from models.data_models import FileData, SeriesConfig, AnnotationConfig
from config.constants import UIConfig, MissingDataMethods, TrendTypes
from ui.components import CollapsibleFrame, ToolTip
from utils.helpers import detect_datetime_column
from scipy.signal import find_peaks, savgol_filter

# Initialize logger
logger = logging.getLogger(__name__)


class SeriesConfigDialog:
    """
    Modern, intuitive series configuration dialog
    Provides comprehensive settings for how data series are displayed
    """

    def __init__(self, parent, series_config, file_data):
        """
        Initialize series configuration dialog

        Args:
            parent: Parent window
            series_config: SeriesConfig object to edit
            file_data: FileData object containing the data
        """
        self.parent = parent
        self.series = series_config
        self.file_data = file_data
        self.result = None

        # Analyze data for smart defaults
        self.analyze_data()

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Configure: {series_config.name}")
        self.dialog.geometry("1050x750")
        self.dialog.configure(bg='#f0f0f0')

        # Modern styling
        self.setup_styles()

        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Store dialog as 'top' for compatibility
        self.top = self.dialog

        self.create_widgets()
        self.dialog.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")

    def setup_styles(self):
        """Configure ttk styles for modern appearance"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Success.TButton', foreground='white')
        style.map('Success.TButton', background=[('active', '#059669'), ('!active', '#10B981')])

    def analyze_data(self):
        """Analyze data to provide intelligent defaults"""
        if self.file_data and self.file_data.data is not None:
            df = self.file_data.data

            # Detect datetime columns
            self.datetime_columns = []
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    self.datetime_columns.append(col)
                else:
                    # Try to parse as datetime
                    try:
                        pd.to_datetime(df[col], errors='coerce')
                        if df[col].notna().sum() > 0:  # At least some valid dates
                            self.datetime_columns.append(col)
                    except:
                        pass

            # Detect numeric columns
            self.numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()

            # Calculate data quality metrics
            self.missing_data = df.isnull().sum()
            self.data_ranges = {}
            for col in self.numeric_columns:
                self.data_ranges[col] = {
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean(),
                    'std': df[col].std()
                }

    def create_widgets(self):
        """Create the dialog interface"""
        # Create main notebook
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.create_data_tab()
        self.create_appearance_tab()
        self.create_processing_tab()
        self.create_analysis_tab()
        self.create_preview_tab()

        # Button frame
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Apply", command=self.apply,
                   style='Success.TButton').pack(side='right', padx=5)

        # Load current settings
        self.load_current_settings()

    def create_data_tab(self):
        """Create data selection tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Data Selection")

        # Series name
        name_frame = ttk.LabelFrame(tab, text="Series Identification", padding=10)
        name_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(name_frame, text="Series Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.name_var = tk.StringVar(value=self.series.name)
        ttk.Entry(name_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, padx=5, pady=5)

        # Column selection
        col_frame = ttk.LabelFrame(tab, text="Data Columns", padding=10)
        col_frame.pack(fill='x', padx=10, pady=10)

        # X Column with smart suggestions
        ttk.Label(col_frame, text="X Column:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.x_col_var = tk.StringVar(value=self.series.x_column)
        x_combo = ttk.Combobox(col_frame, textvariable=self.x_col_var, width=30)
        x_combo['values'] = list(self.file_data.data.columns)
        x_combo.grid(row=0, column=1, padx=5, pady=5)

        # Suggest datetime columns for X
        if self.datetime_columns:
            suggest_btn = ttk.Button(col_frame, text="Suggest Time",
                                     command=lambda: self.x_col_var.set(self.datetime_columns[0]))
            suggest_btn.grid(row=0, column=2, padx=5, pady=5)

        # Y Column
        ttk.Label(col_frame, text="Y Column:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.y_col_var = tk.StringVar(value=self.series.y_column)
        y_combo = ttk.Combobox(col_frame, textvariable=self.y_col_var, width=30)
        y_combo['values'] = list(self.file_data.data.columns)
        y_combo.grid(row=1, column=1, padx=5, pady=5)

        # Data range selection
        range_frame = ttk.LabelFrame(tab, text="Data Range", padding=10)
        range_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(range_frame, text="Start Row:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.start_var = tk.StringVar(value=str(self.series.start_row) if self.series.start_row else "")
        start_entry = ttk.Entry(range_frame, textvariable=self.start_var, width=15)
        start_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(range_frame, text="End Row:").grid(row=0, column=2, sticky='w', padx=20, pady=5)
        self.end_var = tk.StringVar(value=str(self.series.end_row) if self.series.end_row else "")
        end_entry = ttk.Entry(range_frame, textvariable=self.end_var, width=15)
        end_entry.grid(row=0, column=3, padx=5, pady=5)

        # Quick range buttons
        btn_frame = ttk.Frame(range_frame)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=10)

        ttk.Button(btn_frame, text="First 100",
                   command=lambda: self.set_range(1, 100)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="First 1000",
                   command=lambda: self.set_range(1, 1000)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="All Data",
                   command=lambda: self.set_range("", "")).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Last 100",
                   command=lambda: self.set_range(-100, "")).pack(side='left', padx=5)

        # Data quality info
        quality_frame = ttk.LabelFrame(tab, text="Data Quality", padding=10)
        quality_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Create treeview for data quality
        quality_tree = ttk.Treeview(quality_frame, columns=('Value',), height=6)
        quality_tree.heading('#0', text='Metric')
        quality_tree.heading('Value', text='Value')
        quality_tree.pack(fill='both', expand=True)

        # Add quality metrics
        if hasattr(self, 'missing_data'):
            for col in [self.series.x_column, self.series.y_column]:
                if col and col in self.missing_data.index:
                    quality_tree.insert('', 'end', text=f"{col} Missing",
                                        values=(f"{self.missing_data[col]} values",))

    def create_appearance_tab(self):
        """Create appearance settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Appearance")

        # Plot type
        type_frame = ttk.LabelFrame(tab, text="Plot Type", padding=10)
        type_frame.pack(fill='x', padx=10, pady=10)

        self.plot_type_var = tk.StringVar(value=self.series.plot_type)

        # Create radio buttons for plot types
        plot_types = [
            ("Line", "line"),
            ("Scatter", "scatter"),
            ("Line + Markers", "both"),
            ("Bar", "bar"),
            ("Area", "area"),
            ("Step", "step")
        ]

        for i, (label, value) in enumerate(plot_types):
            ttk.Radiobutton(type_frame, text=label, variable=self.plot_type_var,
                            value=value).grid(row=i // 3, column=i % 3, padx=10, pady=5, sticky='w')

        # Line style
        line_frame = ttk.LabelFrame(tab, text="Line Properties", padding=10)
        line_frame.pack(fill='x', padx=10, pady=10)

        # Color
        ttk.Label(line_frame, text="Color:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.color_var = tk.StringVar(value=self.series.color)
        self.color_button = tk.Button(line_frame, text="    ", bg=self.series.color,
                                      command=self.choose_color)
        self.color_button.grid(row=0, column=1, padx=5, pady=5)
        self.color_label = ttk.Label(line_frame, text=self.series.color)
        self.color_label.grid(row=0, column=2, padx=5, pady=5)

        # Line style
        ttk.Label(line_frame, text="Line Style:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.line_style_var = tk.StringVar(value=self.series.line_style)
        style_combo = ttk.Combobox(line_frame, textvariable=self.line_style_var, width=15)
        style_combo['values'] = ["-", "--", ":", "-.", ""]
        style_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky='w')

        # Line width
        ttk.Label(line_frame, text="Line Width:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.line_width_var = tk.DoubleVar(value=self.series.line_width)
        width_scale = ttk.Scale(line_frame, from_=0.5, to=5.0, variable=self.line_width_var,
                                orient='horizontal', length=200)
        width_scale.grid(row=2, column=1, columnspan=2, padx=5, pady=5)
        self.width_label = ttk.Label(line_frame, text=f"{self.series.line_width:.1f}")
        self.width_label.grid(row=2, column=3, padx=5, pady=5)

        # Update label when scale changes
        width_scale.configure(command=lambda v: self.width_label.config(text=f"{float(v):.1f}"))

        # Marker style
        marker_frame = ttk.LabelFrame(tab, text="Marker Properties", padding=10)
        marker_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(marker_frame, text="Marker Style:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.marker_style_var = tk.StringVar(value=self.series.marker_style)
        marker_combo = ttk.Combobox(marker_frame, textvariable=self.marker_style_var, width=15)
        marker_combo['values'] = ["", "o", "s", "^", "v", "D", "*", "+", "x", "."]
        marker_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(marker_frame, text="Marker Size:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.marker_size_var = tk.DoubleVar(value=self.series.marker_size)
        size_scale = ttk.Scale(marker_frame, from_=1, to=20, variable=self.marker_size_var,
                               orient='horizontal', length=200)
        size_scale.grid(row=1, column=1, padx=5, pady=5)
        self.size_label = ttk.Label(marker_frame, text=f"{self.series.marker_size:.1f}")
        self.size_label.grid(row=1, column=2, padx=5, pady=5)

        size_scale.configure(command=lambda v: self.size_label.config(text=f"{float(v):.1f}"))

        # Transparency
        ttk.Label(marker_frame, text="Transparency:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.alpha_var = tk.DoubleVar(value=self.series.alpha)
        alpha_scale = ttk.Scale(marker_frame, from_=0.1, to=1.0, variable=self.alpha_var,
                                orient='horizontal', length=200)
        alpha_scale.grid(row=2, column=1, padx=5, pady=5)
        self.alpha_label = ttk.Label(marker_frame, text=f"{self.series.alpha:.2f}")
        self.alpha_label.grid(row=2, column=2, padx=5, pady=5)

        alpha_scale.configure(command=lambda v: self.alpha_label.config(text=f"{float(v):.2f}"))

    def create_processing_tab(self):
        """Create data processing tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Data Processing")

        # Missing data handling
        missing_frame = ttk.LabelFrame(tab, text="Missing Data Handling", padding=10)
        missing_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(missing_frame, text="Method:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.missing_method_var = tk.StringVar(value=self.series.missing_data_method)
        method_combo = ttk.Combobox(missing_frame, textvariable=self.missing_method_var, width=20)
        method_combo['values'] = ["drop", "interpolate", "forward", "backward", "zero", "mean"]
        method_combo.grid(row=0, column=1, padx=5, pady=5)

        # Add tooltips for methods
        ToolTip(method_combo, "drop: Remove missing values\n"
                              "interpolate: Linear interpolation\n"
                              "forward: Use previous value\n"
                              "backward: Use next value\n"
                              "zero: Fill with zeros\n"
                              "mean: Fill with column mean")

        # Smoothing
        smooth_frame = ttk.LabelFrame(tab, text="Data Smoothing", padding=10)
        smooth_frame.pack(fill='x', padx=10, pady=10)

        self.smoothing_var = tk.BooleanVar(value=self.series.smoothing)
        smooth_check = ttk.Checkbutton(smooth_frame, text="Apply Smoothing",
                                       variable=self.smoothing_var,
                                       command=self.toggle_smoothing)
        smooth_check.grid(row=0, column=0, padx=5, pady=5)

        ttk.Label(smooth_frame, text="Window Size:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.smooth_factor_var = tk.IntVar(value=self.series.smooth_factor)
        self.smooth_scale = ttk.Scale(smooth_frame, from_=3, to=51, variable=self.smooth_factor_var,
                                      orient='horizontal', length=200)
        self.smooth_scale.grid(row=1, column=1, padx=5, pady=5)
        self.smooth_label = ttk.Label(smooth_frame, text=str(self.series.smooth_factor))
        self.smooth_label.grid(row=1, column=2, padx=5, pady=5)

        # Only odd numbers for Savitzky-Golay
        def update_smooth(v):
            val = int(float(v))
            if val % 2 == 0:
                val += 1
            self.smooth_factor_var.set(val)
            self.smooth_label.config(text=str(val))

        self.smooth_scale.configure(command=update_smooth)

        # Enable/disable based on checkbox
        self.toggle_smoothing()

        # Advanced processing
        advanced_frame = ttk.LabelFrame(tab, text="Advanced Processing", padding=10)
        advanced_frame.pack(fill='x', padx=10, pady=10)

        # Y-axis selection
        ttk.Label(advanced_frame, text="Y-Axis:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.y_axis_var = tk.StringVar(value=self.series.y_axis)
        axis_combo = ttk.Combobox(advanced_frame, textvariable=self.y_axis_var, width=10)
        axis_combo['values'] = ["left", "right"]
        axis_combo.grid(row=0, column=1, padx=5, pady=5)

        # Z-order
        ttk.Label(advanced_frame, text="Z-Order:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.z_order_var = tk.IntVar(value=self.series.z_order)
        z_spin = ttk.Spinbox(advanced_frame, from_=0, to=100, textvariable=self.z_order_var, width=10)
        z_spin.grid(row=1, column=1, padx=5, pady=5)

        ToolTip(z_spin, "Higher values are drawn on top")

    def create_analysis_tab(self):
        """Create analysis options tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Analysis")

        # Trend line
        trend_frame = ttk.LabelFrame(tab, text="Trend Line", padding=10)
        trend_frame.pack(fill='x', padx=10, pady=10)

        self.show_trend_var = tk.BooleanVar(value=self.series.show_trend)
        trend_check = ttk.Checkbutton(trend_frame, text="Show Trend Line",
                                      variable=self.show_trend_var,
                                      command=self.toggle_trend)
        trend_check.grid(row=0, column=0, padx=5, pady=5)

        ttk.Label(trend_frame, text="Type:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.trend_type_var = tk.StringVar(value=self.series.trend_type)
        self.trend_combo = ttk.Combobox(trend_frame, textvariable=self.trend_type_var, width=20)
        self.trend_combo['values'] = ["linear", "polynomial", "exponential", "logarithmic", "moving_average"]
        self.trend_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(trend_frame, text="Color:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.trend_color_var = tk.StringVar(value=self.series.trend_color or "")
        self.trend_color_button = tk.Button(trend_frame, text="Auto" if not self.series.trend_color else "    ",
                                            bg=self.series.trend_color if self.series.trend_color else "#999999",
                                            command=self.choose_trend_color)
        self.trend_color_button.grid(row=2, column=1, padx=5, pady=5, sticky='w')

        # Enable/disable based on checkbox
        self.toggle_trend()

        # Statistics
        stats_frame = ttk.LabelFrame(tab, text="Statistical Overlays", padding=10)
        stats_frame.pack(fill='x', padx=10, pady=10)

        self.show_mean_var = tk.BooleanVar(value=self.series.show_mean)
        ttk.Checkbutton(stats_frame, text="Show Mean Line",
                        variable=self.show_mean_var).grid(row=0, column=0, padx=5, pady=5, sticky='w')

        self.show_std_var = tk.BooleanVar(value=self.series.show_std)
        ttk.Checkbutton(stats_frame, text="Show Standard Deviation Bands",
                        variable=self.show_std_var).grid(row=1, column=0, padx=5, pady=5, sticky='w')

    def create_preview_tab(self):
        """Create preview tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Preview")

        # Create matplotlib figure for preview
        self.preview_figure = Figure(figsize=(8, 6), dpi=80)
        self.preview_ax = self.preview_figure.add_subplot(111)

        # Create canvas
        self.preview_canvas = FigureCanvasTkAgg(self.preview_figure, master=tab)
        self.preview_canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)

        # Update button
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill='x', padx=10, pady=5)

        ttk.Button(btn_frame, text="Update Preview", command=self.update_preview).pack(side='right', padx=5)

        # Initial preview
        self.update_preview()

    def toggle_smoothing(self):
        """Enable/disable smoothing controls"""
        state = 'normal' if self.smoothing_var.get() else 'disabled'
        self.smooth_scale.configure(state=state)

    def toggle_trend(self):
        """Enable/disable trend controls"""
        state = 'normal' if self.show_trend_var.get() else 'disabled'
        self.trend_combo.configure(state=state)
        self.trend_color_button.configure(state=state)

    def choose_color(self):
        """Open color chooser for line color"""
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])
            self.color_button.configure(bg=color[1])
            self.color_label.configure(text=color[1])

    def choose_trend_color(self):
        """Open color chooser for trend line color"""
        color = colorchooser.askcolor(initialcolor=self.trend_color_var.get() or self.color_var.get())
        if color[1]:
            self.trend_color_var.set(color[1])
            self.trend_color_button.configure(bg=color[1], text="    ")

    def set_range(self, start, end):
        """Set data range quickly"""
        self.start_var.set(str(start) if start else "")
        self.end_var.set(str(end) if end else "")

    def update_preview(self):
        """Update the preview plot"""
        try:
            # Clear previous plot
            self.preview_ax.clear()

            # Get current settings
            x_col = self.x_col_var.get()
            y_col = self.y_col_var.get()

            if not x_col or not y_col:
                self.preview_ax.text(0.5, 0.5, "Select X and Y columns",
                                     ha='center', va='center', transform=self.preview_ax.transAxes)
                self.preview_canvas.draw()
                return

            # Get data
            df = self.file_data.data

            # Apply range
            start = int(self.start_var.get()) if self.start_var.get() else None
            end = int(self.end_var.get()) if self.end_var.get() else None

            if start is not None or end is not None:
                df = df.iloc[start:end]

            x_data = df[x_col]
            y_data = df[y_col]

            # Apply missing data handling
            method = self.missing_method_var.get()
            if method == "drop":
                mask = y_data.notna()
                x_data = x_data[mask]
                y_data = y_data[mask]
            elif method == "interpolate":
                y_data = y_data.interpolate()
            elif method == "forward":
                y_data = y_data.fillna(method='ffill')
            elif method == "backward":
                y_data = y_data.fillna(method='bfill')
            elif method == "zero":
                y_data = y_data.fillna(0)
            elif method == "mean":
                y_data = y_data.fillna(y_data.mean())

            # Apply smoothing if enabled
            if self.smoothing_var.get() and len(y_data) > self.smooth_factor_var.get():
                from scipy.signal import savgol_filter
                window = min(self.smooth_factor_var.get(), len(y_data))
                if window % 2 == 0:
                    window -= 1
                y_data = savgol_filter(y_data, window, 3)

            # Plot based on type
            plot_type = self.plot_type_var.get()
            color = self.color_var.get()

            if plot_type == "line":
                self.preview_ax.plot(x_data, y_data, color=color,
                                     linestyle=self.line_style_var.get(),
                                     linewidth=self.line_width_var.get(),
                                     alpha=self.alpha_var.get())
            elif plot_type == "scatter":
                self.preview_ax.scatter(x_data, y_data, color=color,
                                        marker=self.marker_style_var.get() or 'o',
                                        s=self.marker_size_var.get() ** 2,
                                        alpha=self.alpha_var.get())
            elif plot_type == "both":
                self.preview_ax.plot(x_data, y_data, color=color,
                                     linestyle=self.line_style_var.get(),
                                     linewidth=self.line_width_var.get(),
                                     marker=self.marker_style_var.get() or 'o',
                                     markersize=self.marker_size_var.get(),
                                     alpha=self.alpha_var.get())

            # Add trend line if enabled
            if self.show_trend_var.get():
                self.add_trend_line(x_data, y_data)

            # Add statistics if enabled
            if self.show_mean_var.get():
                mean_val = y_data.mean()
                self.preview_ax.axhline(mean_val, color='red', linestyle='--', alpha=0.5, label=f'Mean: {mean_val:.2f}')

            if self.show_std_var.get():
                mean_val = y_data.mean()
                std_val = y_data.std()
                self.preview_ax.axhline(mean_val + std_val, color='orange', linestyle=':', alpha=0.3)
                self.preview_ax.axhline(mean_val - std_val, color='orange', linestyle=':', alpha=0.3)
                self.preview_ax.fill_between(x_data, mean_val - std_val, mean_val + std_val,
                                             color='orange', alpha=0.1)

            # Set labels
            self.preview_ax.set_xlabel(x_col)
            self.preview_ax.set_ylabel(y_col)
            self.preview_ax.set_title(self.name_var.get())
            self.preview_ax.grid(True, alpha=0.3)

            if self.show_mean_var.get():
                self.preview_ax.legend()

            self.preview_canvas.draw()

        except Exception as e:
            self.preview_ax.clear()
            self.preview_ax.text(0.5, 0.5, f"Error: {str(e)}",
                                 ha='center', va='center', transform=self.preview_ax.transAxes,
                                 color='red')
            self.preview_canvas.draw()

    def add_trend_line(self, x_data, y_data):
        """Add trend line to preview"""
        try:
            # Convert to numeric if needed
            if hasattr(x_data, 'values'):
                x_vals = np.arange(len(x_data))
            else:
                x_vals = np.arange(len(x_data))

            y_vals = y_data.values if hasattr(y_data, 'values') else y_data

            # Remove NaN values
            mask = ~np.isnan(y_vals)
            x_vals = x_vals[mask]
            y_vals = y_vals[mask]

            if len(x_vals) < 2:
                return

            trend_type = self.trend_type_var.get()
            trend_color = self.trend_color_var.get() or self.color_var.get()

            if trend_type == "linear":
                # Linear regression with error handling
                try:
                    # Check for valid data
                    valid_mask = np.isfinite(x_vals) & np.isfinite(y_vals)
                    if np.sum(valid_mask) > 1:
                        x_clean = x_vals[valid_mask]
                        y_clean = y_vals[valid_mask]
                        
                        # Only fit if we have enough data and variation
                        if len(x_clean) > 1 and np.std(x_clean) > 1e-10:
                            z = np.polyfit(x_clean, y_clean, 1)
                            p = np.poly1d(z)
                            self.preview_ax.plot(x_data, p(x_vals), '--', color=trend_color, alpha=0.7,
                                                 label=f'Linear: y={z[0]:.2e}x+{z[1]:.2f}')
                except (np.linalg.LinAlgError, np.RankWarning, ValueError) as e:
                    print(f"Linear trend computation failed: {e}")
                    pass

            elif trend_type == "polynomial":
                # Polynomial fit (degree 2) with error handling
                try:
                    # Check for valid data
                    valid_mask = np.isfinite(x_vals) & np.isfinite(y_vals)
                    if np.sum(valid_mask) > 2:  # Need at least 3 points for degree 2
                        x_clean = x_vals[valid_mask]
                        y_clean = y_vals[valid_mask]
                        
                        # Only fit if we have enough data and variation
                        if len(x_clean) > 2 and np.std(x_clean) > 1e-10:
                            z = np.polyfit(x_clean, y_clean, 2)
                            p = np.poly1d(z)
                            self.preview_ax.plot(x_data, p(x_vals), '--', color=trend_color, alpha=0.7,
                                                 label='Polynomial (2nd degree)')
                except (np.linalg.LinAlgError, np.RankWarning, ValueError) as e:
                    print(f"Polynomial trend computation failed: {e}")
                    pass

            elif trend_type == "moving_average":
                # Moving average
                window = min(20, len(y_vals) // 4)
                ma = pd.Series(y_vals).rolling(window=window, center=True).mean()
                self.preview_ax.plot(x_data, ma, '--', color=trend_color, alpha=0.7,
                                     label=f'Moving Avg (window={window})')

            self.preview_ax.legend()

        except Exception as e:
            print(f"Trend line error: {e}")

    def load_current_settings(self):
        """Load current series settings into the dialog"""
        # Already done through variable initialization
        pass

    def apply(self):
        """Apply the configuration changes"""
        # Update series object
        self.series.name = self.name_var.get()
        self.series.x_column = self.x_col_var.get()
        self.series.y_column = self.y_col_var.get()

        # Data range
        self.series.start_row = int(self.start_var.get()) if self.start_var.get() else None
        self.series.end_row = int(self.end_var.get()) if self.end_var.get() else None

        # Appearance
        self.series.color = self.color_var.get()
        self.series.line_style = self.line_style_var.get()
        self.series.line_width = self.line_width_var.get()
        self.series.marker_style = self.marker_style_var.get()
        self.series.marker_size = self.marker_size_var.get()
        self.series.alpha = self.alpha_var.get()
        self.series.plot_type = self.plot_type_var.get()

        # Processing
        self.series.missing_data_method = self.missing_method_var.get()
        self.series.smoothing = self.smoothing_var.get()
        self.series.smooth_factor = self.smooth_factor_var.get()

        # Analysis
        self.series.show_trend = self.show_trend_var.get()
        self.series.trend_type = self.trend_type_var.get()
        self.series.trend_color = self.trend_color_var.get() if self.trend_color_var.get() else None
        self.series.show_mean = self.show_mean_var.get()
        self.series.show_std = self.show_std_var.get()

        # Advanced
        self.series.y_axis = self.y_axis_var.get()
        self.series.z_order = self.z_order_var.get()

        self.result = "apply"
        self.dialog.destroy()

    def cancel(self):
        """Cancel without applying changes"""
        self.result = "cancel"
        self.dialog.destroy()


class SeriesDialog:
    """Dialog for creating/editing data series - Enhanced with Legacy Features"""

    def __init__(
            self,
            parent,
            files: Dict[str, FileData],
            series: Optional[SeriesConfig] = None,
            mode: str = "create"
    ):
        self.parent = parent
        self.files = files
        self.series = series
        self.mode = mode
        self.result = None

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Series" if mode == "create" else "Edit Series")
        self.dialog.geometry("1200x800")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Initialize variables
        self._init_variables()

        # Create UI
        self._create_widgets()

        # Initialize file selection AFTER widgets are created
        if self.files:
            file_names = [f.filename for f in self.files.values()]
            if file_names:
                self.file_var.set(file_names[0])
                self._on_file_change(file_names[0])

        # Load existing values if editing
        if mode == "edit" and series:
            self._load_series_config()

        # Center dialog
        self._center_dialog()

        # Initial preview
        self._update_preview()

    def _init_variables(self):
        """Initialize dialog variables"""
        self.name_var = tk.StringVar(value="New Series" if not self.series else self.series.name)
        self.file_var = tk.StringVar()
        self.x_column_var = tk.StringVar()
        self.y_column_var = tk.StringVar()
        self.start_var = tk.IntVar(value=0)
        self.end_var = tk.IntVar(value=0)

        # Visual properties
        self.color_var = tk.StringVar(value="#3B82F6")
        self.line_style_var = tk.StringVar(value="-")
        self.line_width_var = tk.DoubleVar(value=1.5)
        self.marker_var = tk.StringVar(value="")
        self.marker_size_var = tk.IntVar(value=6)
        self.alpha_var = tk.DoubleVar(value=1.0)

        # Options
        self.visible_var = tk.BooleanVar(value=True)
        self.show_legend_var = tk.BooleanVar(value=True)
        self.missing_method_var = tk.StringVar(value="drop")
        self.smoothing_var = tk.BooleanVar(value=False)
        self.smoothing_window_var = tk.IntVar(value=5)

        # Trend line
        self.show_trend_var = tk.BooleanVar(value=False)
        self.trend_type_var = tk.StringVar(value="linear")
        self.trend_order_var = tk.IntVar(value=2)

        # Analysis
        self.show_stats_var = tk.BooleanVar(value=False)
        self.show_peaks_var = tk.BooleanVar(value=False)
        self.peak_prominence_var = tk.DoubleVar(value=0.1)

        # Legacy properties
        self.z_order_var = tk.IntVar(value=0)
        self.plot_type_var = tk.StringVar(value="line")

    def _create_widgets(self):
        """Create dialog widgets with legacy enhancements"""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel - Configuration
        left_panel = ctk.CTkScrollableFrame(main_frame, width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        # Right panel - Preview
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        # Create ALL sections first - this ensures all widgets exist
        self._create_basic_section(left_panel)
        self._create_data_section(left_panel)
        self._create_visual_section(left_panel)
        self._create_processing_section(left_panel)
        self._create_analysis_section(left_panel)
        self._create_legacy_section(left_panel)  # New legacy section

        # Create preview
        self._create_preview_panel(right_panel)

        # Buttons
        self._create_buttons()

    def _create_basic_section(self, parent):
        """Create basic configuration section"""
        section = CollapsibleFrame(parent, "Basic Settings")
        section.pack(fill="x", pady=5)
        content = section.get_content_frame()

        # Series name
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Name:", width=100).pack(side="left")
        ctk.CTkEntry(frame, textvariable=self.name_var, width=200).pack(side="left", padx=5)

        # File selection - DON'T call _on_file_change here yet
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="File:", width=100).pack(side="left")

        file_names = [f.filename for f in self.files.values()]
        file_combo = ctk.CTkComboBox(
            frame,
            variable=self.file_var,
            values=file_names,
            width=200,
            command=self._on_file_change
        )
        file_combo.pack(side="left", padx=5)

    def _create_data_section(self, parent):
        """Create data selection section"""
        section = CollapsibleFrame(parent, "Data Selection")
        section.pack(fill="x", pady=5)
        content = section.get_content_frame()

        # X column
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="X Column:", width=100).pack(side="left")
        self.x_combo = ctk.CTkComboBox(
            frame,
            variable=self.x_column_var,
            values=["Index"],  # Default value
            width=200,
            command=lambda e: self._update_preview()
        )
        self.x_combo.pack(side="left", padx=5)

        # Y column
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Y Column:", width=100).pack(side="left")
        self.y_combo = ctk.CTkComboBox(
            frame,
            variable=self.y_column_var,
            values=[],  # Will be populated when file is selected
            width=200,
            command=lambda e: self._update_preview()
        )
        self.y_combo.pack(side="left", padx=5)

        # Data range
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Range:").pack(side="left", padx=5)

        # Start index
        ctk.CTkLabel(frame, text="Start:").pack(side="left", padx=5)
        self.start_slider = ctk.CTkSlider(
            frame,
            from_=0,
            to=1000,
            variable=self.start_var,
            width=100,
            command=lambda v: self._update_range()
        )
        self.start_slider.pack(side="left", padx=5)
        self.start_label = ctk.CTkLabel(frame, text="0")
        self.start_label.pack(side="left")

        # End index
        ctk.CTkLabel(frame, text="End:").pack(side="left", padx=5)
        self.end_slider = ctk.CTkSlider(
            frame,
            from_=0,
            to=1000,
            variable=self.end_var,
            width=100,
            command=lambda v: self._update_range()
        )
        self.end_slider.pack(side="left", padx=5)
        self.end_label = ctk.CTkLabel(frame, text="0")
        self.end_label.pack(side="left")

    def _create_visual_section(self, parent):
        """Create visual properties section"""
        section = CollapsibleFrame(parent, "Visual Properties", collapsed=True)
        section.pack(fill="x", pady=5)
        content = section.get_content_frame()

        # Color
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Color:", width=100).pack(side="left")
        self.color_button = ctk.CTkButton(
            frame,
            text="",
            width=30,
            height=30,
            fg_color=self.color_var.get(),
            command=self._choose_color
        )
        self.color_button.pack(side="left", padx=5)
        ctk.CTkLabel(frame, textvariable=self.color_var).pack(side="left", padx=5)

        # Line style
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Line Style:", width=100).pack(side="left")
        ctk.CTkComboBox(
            frame,
            variable=self.line_style_var,
            values=["-", "--", ":", "-."],
            width=100,
            command=lambda e: self._update_preview()
        ).pack(side="left", padx=5)

        # Line width
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Line Width:", width=100).pack(side="left")
        ctk.CTkSlider(
            frame,
            from_=0.5,
            to=5,
            variable=self.line_width_var,
            width=150,
            command=lambda v: self._update_preview()
        ).pack(side="left", padx=5)

        # Marker
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Marker:", width=100).pack(side="left")
        ctk.CTkComboBox(
            frame,
            variable=self.marker_var,
            values=["", "o", "s", "^", "v", "D", "*", "+", "x"],
            width=100,
            command=lambda e: self._update_preview()
        ).pack(side="left", padx=5)

        # Alpha
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Opacity:", width=100).pack(side="left")
        ctk.CTkSlider(
            frame,
            from_=0.1,
            to=1.0,
            variable=self.alpha_var,
            width=150,
            command=lambda v: self._update_preview()
        ).pack(side="left", padx=5)

        # Display options
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkCheckBox(
            frame,
            text="Visible",
            variable=self.visible_var,
            command=self._update_preview
        ).pack(side="left", padx=5)
        ctk.CTkCheckBox(
            frame,
            text="Show in Legend",
            variable=self.show_legend_var,
            command=self._update_preview
        ).pack(side="left", padx=5)

    def _create_processing_section(self, parent):
        """Create data processing section"""
        section = CollapsibleFrame(parent, "Data Processing", collapsed=True)
        section.pack(fill="x", pady=5)
        content = section.get_content_frame()

        # Missing data
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Missing Data:", width=100).pack(side="left")
        ctk.CTkComboBox(
            frame,
            variable=self.missing_method_var,
            values=["drop", "interpolate", "forward", "backward", "zero", "mean"],
            width=150,
            command=lambda e: self._update_preview()
        ).pack(side="left", padx=5)

        # Smoothing
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkCheckBox(
            frame,
            text="Enable Smoothing",
            variable=self.smoothing_var,
            command=self._update_preview
        ).pack(side="left", padx=5)

        ctk.CTkLabel(frame, text="Window:").pack(side="left", padx=5)
        ctk.CTkSlider(
            frame,
            from_=3,
            to=51,
            variable=self.smoothing_window_var,
            width=100,
            command=lambda v: self._update_preview()
        ).pack(side="left", padx=5)

    def _create_analysis_section(self, parent):
        """Create analysis options section"""
        section = CollapsibleFrame(parent, "Analysis Options", collapsed=True)
        section.pack(fill="x", pady=5)
        content = section.get_content_frame()

        # Trend line
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkCheckBox(
            frame,
            text="Show Trend Line",
            variable=self.show_trend_var,
            command=self._update_preview
        ).pack(side="left", padx=5)

        ctk.CTkComboBox(
            frame,
            variable=self.trend_type_var,
            values=["linear", "polynomial", "exponential", "moving_average"],
            width=120,
            command=lambda e: self._update_preview()
        ).pack(side="left", padx=5)

        # Statistics
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkCheckBox(
            frame,
            text="Show Statistics",
            variable=self.show_stats_var,
            command=self._update_preview
        ).pack(side="left", padx=5)

        # Peak detection
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkCheckBox(
            frame,
            text="Mark Peaks",
            variable=self.show_peaks_var,
            command=self._update_preview
        ).pack(side="left", padx=5)

        ctk.CTkLabel(frame, text="Prominence:").pack(side="left", padx=5)
        ctk.CTkSlider(
            frame,
            from_=0.01,
            to=0.5,
            variable=self.peak_prominence_var,
            width=100,
            command=lambda v: self._update_preview()
        ).pack(side="left", padx=5)

    def _create_legacy_section(self, parent):
        """Create legacy properties section"""
        section = CollapsibleFrame(parent, "Legacy Properties", collapsed=True)
        section.pack(fill="x", pady=5)
        content = section.get_content_frame()

        # Plot type
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Plot Type:", width=100).pack(side="left")
        ctk.CTkComboBox(
            frame,
            variable=self.plot_type_var,
            values=["line", "scatter", "both", "bar", "area", "step"],
            width=120,
            command=lambda e: self._update_preview()
        ).pack(side="left", padx=5)

        # Z-order
        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Z-Order:", width=100).pack(side="left")
        ctk.CTkSlider(
            frame,
            from_=0,
            to=10,
            variable=self.z_order_var,
            width=150,
            command=lambda v: self._update_preview()
        ).pack(side="left", padx=5)

    def _create_preview_panel(self, parent):
        """Create preview panel"""
        # Title
        title = ctk.CTkLabel(parent, text="📊 Live Preview", font=("", 14, "bold"))
        title.pack(pady=10)

        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=80)
        self.ax = self.figure.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Info label
        self.info_label = ctk.CTkLabel(parent, text="", text_color="gray")
        self.info_label.pack(pady=5)

    def _create_buttons(self):
        """Create dialog buttons"""
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", pady=10)

        # Cancel button
        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            width=100
        ).pack(side="right", padx=5)

        # Apply button
        apply_text = "Create" if self.mode == "create" else "Apply"
        ctk.CTkButton(
            button_frame,
            text=apply_text,
            command=self._apply,
            width=100
        ).pack(side="right", padx=5)

        # Reset button
        if self.mode == "edit":
            ctk.CTkButton(
                button_frame,
                text="Reset",
                command=self._load_series_config,
                width=100
            ).pack(side="right", padx=5)

    def _on_file_change(self, filename: str):
        """Handle file selection change"""
        # Check if x_combo and y_combo exist
        if not hasattr(self, 'x_combo') or not hasattr(self, 'y_combo'):
            return

        # Find file data
        file_data = None
        for f in self.files.values():
            if f.filename == filename:
                file_data = f
                break

        if not file_data:
            return

        # Update column lists
        columns = ["Index"] + list(file_data.data.columns)

        self.x_combo.configure(values=columns)
        self.y_combo.configure(values=columns[1:])  # Exclude Index for Y

        # Set defaults
        if not self.x_column_var.get():
            self.x_combo.set(columns[0])

        numeric_cols = file_data.get_numeric_columns()
        if numeric_cols and not self.y_column_var.get():
            self.y_combo.set(numeric_cols[0])

        # Update range sliders
        data_length = len(file_data.data)
        self.start_slider.configure(to=data_length - 1)
        self.end_slider.configure(to=data_length)
        self.end_var.set(min(1000, data_length))

        self._update_preview()

    def _update_range(self):
        """Update range labels and preview"""
        self.start_label.configure(text=str(self.start_var.get()))
        self.end_label.configure(text=str(self.end_var.get()))
        self._update_preview()

    def _choose_color(self):
        """Open color chooser"""
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])
            self.color_button.configure(fg_color=color[1])
            self._update_preview()

    def _update_preview(self):
        """Update the preview plot"""
        try:
            # Clear previous plot
            self.ax.clear()

            # Get file data
            filename = self.file_var.get()
            if not filename:
                return

            file_data = None
            for f in self.files.values():
                if f.filename == filename:
                    file_data = f
                    break

            if not file_data:
                return

            # Get data
            x_col = self.x_column_var.get()
            y_col = self.y_column_var.get()

            if not x_col or not y_col:
                return

            # Extract data
            start = self.start_var.get()
            end = self.end_var.get()
            df_slice = file_data.data.iloc[start:end]

            if x_col == "Index":
                x_data = np.arange(start, end)
            else:
                x_data = df_slice[x_col].values

            y_data = df_slice[y_col].values

            # Handle missing data
            method = self.missing_method_var.get()
            x_data, y_data = self._handle_missing_data(x_data, y_data, method)

            # Apply smoothing
            if self.smoothing_var.get():
                window = min(self.smoothing_window_var.get(), len(y_data))
                if window >= 3 and len(y_data) > window:
                    y_data = savgol_filter(y_data, window, min(3, window - 1))

            # Plot data based on plot type
            plot_type = self.plot_type_var.get()
            if plot_type == "line":
                self.ax.plot(
                    x_data, y_data,
                    color=self.color_var.get(),
                    linestyle=self.line_style_var.get(),
                    linewidth=self.line_width_var.get(),
                    alpha=self.alpha_var.get(),
                    label=self.name_var.get() if self.show_legend_var.get() else ""
                )
            elif plot_type == "scatter":
                self.ax.scatter(
                    x_data, y_data,
                    color=self.color_var.get(),
                    marker=self.marker_var.get() if self.marker_var.get() else "o",
                    s=self.marker_size_var.get() ** 2,
                    alpha=self.alpha_var.get(),
                    label=self.name_var.get() if self.show_legend_var.get() else ""
                )
            elif plot_type == "both":
                self.ax.plot(
                    x_data, y_data,
                    color=self.color_var.get(),
                    linestyle=self.line_style_var.get(),
                    linewidth=self.line_width_var.get(),
                    marker=self.marker_var.get() if self.marker_var.get() else "o",
                    markersize=self.marker_size_var.get(),
                    alpha=self.alpha_var.get(),
                    label=self.name_var.get() if self.show_legend_var.get() else ""
                )
            elif plot_type == "bar":
                self.ax.bar(
                    x_data, y_data,
                    color=self.color_var.get(),
                    alpha=self.alpha_var.get(),
                    label=self.name_var.get() if self.show_legend_var.get() else ""
                )
            elif plot_type == "area":
                self.ax.fill_between(
                    x_data, y_data,
                    color=self.color_var.get(),
                    alpha=self.alpha_var.get(),
                    label=self.name_var.get() if self.show_legend_var.get() else ""
                )
            elif plot_type == "step":
                self.ax.step(
                    x_data, y_data,
                    color=self.color_var.get(),
                    linestyle=self.line_style_var.get(),
                    linewidth=self.line_width_var.get(),
                    alpha=self.alpha_var.get(),
                    label=self.name_var.get() if self.show_legend_var.get() else ""
                )

            # Add trend line
            if self.show_trend_var.get():
                self._add_trend_line(x_data, y_data)

            # Add statistics
            if self.show_stats_var.get():
                self._add_statistics(y_data)

            # Mark peaks
            if self.show_peaks_var.get():
                self._mark_peaks(x_data, y_data)

            # Configure plot
            self.ax.set_xlabel(x_col)
            self.ax.set_ylabel(y_col)
            self.ax.set_title(f"Preview: {self.name_var.get()}")
            self.ax.grid(True, alpha=0.3)

            if self.show_legend_var.get():
                self.ax.legend()

            # Update info
            self.info_label.configure(
                text=f"Points: {len(y_data)} | "
                     f"Range: [{np.min(y_data):.3g}, {np.max(y_data):.3g}]"
            )

            # Refresh canvas
            self.canvas.draw()

        except Exception as e:
            self.info_label.configure(text=f"Error: {str(e)}", text_color="red")

    def _handle_missing_data(self, x_data, y_data, method: str):
        """Handle missing data"""
        mask = ~(pd.isna(x_data) | pd.isna(y_data))

        if method == "drop":
            return x_data[mask], y_data[mask]
        elif method == "interpolate":
            y_series = pd.Series(y_data).interpolate()
            return x_data, y_series.values
        elif method == "forward":
            y_series = pd.Series(y_data).ffill()
            return x_data, y_series.values
        elif method == "backward":
            y_series = pd.Series(y_data).bfill()
            return x_data, y_series.values
        elif method == "zero":
            return x_data, np.nan_to_num(y_data, 0)
        elif method == "mean":
            mean_val = np.nanmean(y_data)
            return x_data, np.nan_to_num(y_data, mean_val)

        return x_data[mask], y_data[mask]

    def _add_trend_line(self, x_data, y_data):
        """Add trend line to preview"""
        # Implementation similar to plot_manager
        pass

    def _add_statistics(self, y_data):
        """Add statistics to preview"""
        stats_text = f"Mean: {np.nanmean(y_data):.3g}\n"
        stats_text += f"Std: {np.nanstd(y_data):.3g}"

        self.ax.text(
            0.02, 0.98, stats_text,
            transform=self.ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        )

    def _mark_peaks(self, x_data, y_data):
        """Mark peaks in preview"""
        prominence = self.peak_prominence_var.get() * (np.max(y_data) - np.min(y_data))
        peaks, _ = find_peaks(y_data, prominence=prominence)

        if len(peaks) > 0:
            self.ax.scatter(
                x_data[peaks], y_data[peaks],
                marker='^', s=100, color='red', zorder=5
            )

    def _load_series_config(self):
        """Load existing series configuration"""
        if not self.series:
            return

        # Basic settings
        self.name_var.set(self.series.name)

        # Find and set file
        file_data = None
        for f in self.files.values():
            if f.id == self.series.file_id:
                file_data = f
                self.file_var.set(f.filename)
                self._on_file_change(f.filename)
                break

        # Data columns
        self.x_column_var.set(self.series.x_column)
        self.y_column_var.set(self.series.y_column)
        self.start_var.set(self.series.start_index)
        self.end_var.set(self.series.end_index or len(file_data.data))

        # Visual properties
        self.color_var.set(self.series.color or "#3B82F6")
        self.color_button.configure(fg_color=self.color_var.get())
        self.line_style_var.set(self.series.line_style)
        self.line_width_var.set(self.series.line_width)
        self.marker_var.set(self.series.marker or "")
        self.marker_size_var.set(self.series.marker_size)
        self.alpha_var.set(self.series.alpha)

        # Options
        self.visible_var.set(self.series.visible)
        self.show_legend_var.set(self.series.show_in_legend)
        self.missing_method_var.set(self.series.missing_data_method)
        self.smoothing_var.set(self.series.smoothing_enabled)
        self.smoothing_window_var.set(self.series.smoothing_window)

        # Analysis
        self.show_trend_var.set(self.series.show_trendline)
        self.trend_type_var.set(self.series.trend_type)
        self.trend_order_var.set(self.series.trend_order)
        self.show_stats_var.set(self.series.show_statistics)
        self.show_peaks_var.set(self.series.show_peaks)
        self.peak_prominence_var.set(self.series.peak_prominence)

        # Legacy properties
        self.z_order_var.set(self.series.z_order)
        self.plot_type_var.set(self.series.plot_type)

        self._update_preview()

    def _apply(self):
        """Apply configuration and close dialog"""
        # Validate inputs
        if not self.name_var.get():
            messagebox.showerror("Error", "Please enter a series name")
            return

        if not self.file_var.get():
            messagebox.showerror("Error", "Please select a file")
            return

        if not self.y_column_var.get():
            messagebox.showerror("Error", "Please select Y column")
            return

        # Find file ID
        file_id = None
        for f in self.files.values():
            if f.filename == self.file_var.get():
                file_id = f.id
                break

        if not file_id:
            messagebox.showerror("Error", "File not found")
            return

        # Create or update series
        if self.mode == "create":
            series = SeriesConfig(
                name=self.name_var.get(),
                file_id=file_id,
                x_column=self.x_column_var.get(),
                y_column=self.y_column_var.get()
            )
        else:
            series = self.series
            series.name = self.name_var.get()
            series.file_id = file_id
            series.x_column = self.x_column_var.get()
            series.y_column = self.y_column_var.get()

        # Update all properties
        series.start_index = self.start_var.get()
        series.end_index = self.end_var.get()
        series.color = self.color_var.get()
        series.line_style = self.line_style_var.get()
        series.line_width = self.line_width_var.get()
        series.marker = self.marker_var.get() if self.marker_var.get() else None
        series.marker_size = self.marker_size_var.get()
        series.alpha = self.alpha_var.get()
        series.visible = self.visible_var.get()
        series.show_in_legend = self.show_legend_var.get()
        series.legend_label = self.name_var.get()
        series.missing_data_method = self.missing_method_var.get()
        series.smoothing_enabled = self.smoothing_var.get()
        series.smoothing_window = self.smoothing_window_var.get()
        series.show_trendline = self.show_trend_var.get()
        series.trend_type = self.trend_type_var.get()
        series.trend_order = self.trend_order_var.get()
        series.show_statistics = self.show_stats_var.get()
        series.show_peaks = self.show_peaks_var.get()
        series.peak_prominence = self.peak_prominence_var.get()
        series.z_order = self.z_order_var.get()
        series.plot_type = self.plot_type_var.get()

        # Set result and close
        self.result = series
        self.dialog.destroy()

    def _center_dialog(self):
        """Center dialog on screen"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")


class StatisticalAnalysisDialog:
    """Dialog for data analysis - Enhanced with Legacy Features"""

    def __init__(
            self,
            parent,
            series_configs: Dict[str, SeriesConfig],
            loaded_files: Dict[str, FileData],
            statistical_analyzer,
            vacuum_analyzer
    ):
        self.parent = parent
        self.series_configs = series_configs
        self.loaded_files = loaded_files
        self.statistical_analyzer = statistical_analyzer
        self.vacuum_analyzer = vacuum_analyzer
        self.vacuum_results = {}

        # Create dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Data Analysis Tools")
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Add root property for compatibility
        self.root = self.dialog

        # Initialize theme manager
        from ui.theme_manager import theme_manager
        self.theme_manager = theme_manager

        # Create notebook for different analysis types
        self.notebook = ctk.CTkTabview(self.dialog)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Add analysis tabs
        self._create_statistical_tab()
        self._create_vacuum_tab()
        self._create_comparison_tab()

        # Buttons
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            button_frame,
            text="Export Results",
            command=self._export_results,
            width=120
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            width=100
        ).pack(side="right", padx=5)

    def _create_statistical_tab(self):
        """Create statistical analysis tab"""
        tab = self.notebook.add("📊 Statistical Analysis")

        # Series selection
        select_frame = ctk.CTkFrame(tab)
        select_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(select_frame, text="Select Series:").pack(side="left", padx=5)

        self.stat_series_var = tk.StringVar()
        series_names = [s.name for s in self.series_configs.values()]
        ctk.CTkComboBox(
            select_frame,
            variable=self.stat_series_var,
            values=series_names,
            width=200
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            select_frame,
            text="Analyze",
            command=self._run_statistical_analysis,
            width=100
        ).pack(side="left", padx=10)

        # Results display
        self.stat_results = ctk.CTkTextbox(tab, wrap="word", height=400)
        self.stat_results.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_vacuum_tab(self):
        """Create vacuum analysis tab with legacy features"""
        tab = self.notebook.add("🎯 Vacuum Analysis")

        # Create notebook for vacuum sub-tabs
        vacuum_notebook = ctk.CTkTabview(tab)
        vacuum_notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Add vacuum sub-tabs
        self._create_base_pressure_tab(vacuum_notebook)
        self._create_spike_detection_tab(vacuum_notebook)
        self._create_leak_detection_tab(vacuum_notebook)
        self._create_pumpdown_tab(vacuum_notebook)

    def _create_base_pressure_tab(self, notebook):
        """Create base pressure analysis tab"""
        tab = notebook.add("Base Pressure")

        # Series selection
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame, text="Series:").pack(side="left", padx=5)
        self.base_series_var = tk.StringVar()
        series_names = [s.name for s in self.series_configs.values()]
        ctk.CTkComboBox(
            frame,
            variable=self.base_series_var,
            values=series_names,
            width=200
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame,
            text="Analyze",
            command=self._run_base_pressure_analysis,
            width=100
        ).pack(side="left", padx=10)

        # Parameters
        param_frame = ctk.CTkFrame(tab)
        param_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(param_frame, text="Window Size (min):").pack(side="left", padx=5)
        self.window_size_var = tk.IntVar(value=10)
        ctk.CTkSlider(
            param_frame,
            from_=1,
            to=60,
            variable=self.window_size_var,
            width=150
        ).pack(side="left", padx=5)
        ctk.CTkLabel(param_frame, textvariable=self.window_size_var).pack(side="left", padx=5)

        # Results
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.base_text = tk.Text(results_frame, wrap="word")
        scrollbar = ttk.Scrollbar(results_frame, command=self.base_text.yview)
        self.base_text.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.base_text.pack(side="left", fill="both", expand=True)

    def _create_spike_detection_tab(self, notebook):
        """Create spike detection tab"""
        tab = notebook.add("Spike Detection")

        # Series selection
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame, text="Series:").pack(side="left", padx=5)
        self.spike_series_var = tk.StringVar()
        series_names = [s.name for s in self.series_configs.values()]
        ctk.CTkComboBox(
            frame,
            variable=self.spike_series_var,
            values=series_names,
            width=200
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame,
            text="Detect",
            command=self._detect_spikes,
            width=100
        ).pack(side="left", padx=10)

        # Parameters
        param_frame = ctk.CTkFrame(tab)
        param_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(param_frame, text="Threshold (σ):").pack(side="left", padx=5)
        self.spike_threshold_var = tk.DoubleVar(value=3.0)
        ctk.CTkSlider(
            param_frame,
            from_=1.0,
            to=10.0,
            variable=self.spike_threshold_var,
            width=150
        ).pack(side="left", padx=5)
        ctk.CTkLabel(param_frame, textvariable=self.spike_threshold_var).pack(side="left", padx=5)

        # Results
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("#", "Start Time", "End Time", "Duration", "Max Pressure", "Severity")
        self.spikes_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=10)

        for col in columns:
            self.spikes_tree.heading(col, text=col)
            self.spikes_tree.column(col, width=100)

        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.spikes_tree.yview)
        self.spikes_tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.spikes_tree.pack(side="left", fill="both", expand=True)

    def _create_leak_detection_tab(self, notebook):
        """Create leak detection tab"""
        tab = notebook.add("Leak Detection")

        # Series selection
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame, text="Series:").pack(side="left", padx=5)
        self.leak_series_var = tk.StringVar()
        series_names = [s.name for s in self.series_configs.values()]
        ctk.CTkComboBox(
            frame,
            variable=self.leak_series_var,
            values=series_names,
            width=200
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame,
            text="Detect",
            command=self._detect_leaks,
            width=100
        ).pack(side="left", padx=10)

        # Results
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.leak_text = tk.Text(results_frame, wrap="word")
        scrollbar = ttk.Scrollbar(results_frame, command=self.leak_text.yview)
        self.leak_text.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.leak_text.pack(side="left", fill="both", expand=True)

    def _create_pumpdown_tab(self, notebook):
        """Create pump-down analysis tab"""
        tab = notebook.add("Pump-down")

        # Series selection
        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame, text="Series:").pack(side="left", padx=5)
        self.pump_series_var = tk.StringVar()
        series_names = [s.name for s in self.series_configs.values()]
        ctk.CTkComboBox(
            frame,
            variable=self.pump_series_var,
            values=series_names,
            width=200
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            frame,
            text="Analyze",
            command=self._analyze_pumpdown,
            width=100
        ).pack(side="left", padx=10)

        # Results
        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.pump_text = tk.Text(results_frame, wrap="word")
        scrollbar = ttk.Scrollbar(results_frame, command=self.pump_text.yview)
        self.pump_text.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.pump_text.pack(side="left", fill="both", expand=True)

    def _create_comparison_tab(self):
        """Create enhanced comparison tab with smart screen-aware two-column layout"""
        tab = self.notebook.add("📊 Comparison")
        
        # Get screen dimensions for intelligent sizing
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        # Calculate smaller dialog size for better usability (70% of screen, with smaller limits)
        dialog_width = min(1400, max(1000, int(screen_width * 0.70)))
        dialog_height = min(900, max(700, int(screen_height * 0.70)))
        
        # Resize dialog to be screen-aware
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        
        # Main container with intelligent two-column layout
        main_container = ctk.CTkFrame(tab, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create left and right frames using pack instead of grid to avoid conflict
        left_frame_wrapper = ctk.CTkFrame(main_container, fg_color="transparent")
        left_frame_wrapper.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_frame_wrapper = ctk.CTkFrame(main_container, fg_color="transparent")
        right_frame_wrapper.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # === LEFT COLUMN: Controls and Configuration ===
        left_panel = ctk.CTkScrollableFrame(
            left_frame_wrapper,
            corner_radius=10,
            label_text="🎛️ Comparison Configuration"
        )
        left_panel.pack(fill="both", expand=True)
        
        # Header with description
        desc_label = ctk.CTkLabel(
            left_panel,
            text="🧠 Intelligent comparison with series name recognition",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40"),
            wraplength=int(dialog_width * 0.35)
        )
        desc_label.pack(anchor="w", pady=(0, 15))
        
        # === Series Selection Section ===
        selection_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        selection_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            selection_frame,
            text="📈 Series Selection",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        # Get series names (not IDs) for intelligent display
        series_names = [config.name for config in self.series_configs.values() if config.name]
        
        # Primary series
        primary_frame = ctk.CTkFrame(selection_frame, corner_radius=6)
        primary_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            primary_frame,
            text="🔵 Primary Series",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(8, 2))
        
        self.comp_primary_var = tk.StringVar()
        self.comp_primary_combo = ctk.CTkComboBox(
            primary_frame,
            variable=self.comp_primary_var,
            values=series_names,
            width=int(dialog_width * 0.32),
            height=30,
            corner_radius=6,
            command=self._on_primary_series_change
        )
        self.comp_primary_combo.pack(padx=10, pady=(0, 5))
        
        # Primary series info preview
        self.primary_info_label = ctk.CTkLabel(
            primary_frame,
            text="Select a series to see intelligent preview",
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray40"),
            wraplength=int(dialog_width * 0.32)
        )
        self.primary_info_label.pack(anchor="w", padx=10, pady=(0, 8))
        
        # Secondary series
        secondary_frame = ctk.CTkFrame(selection_frame, corner_radius=6)
        secondary_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            secondary_frame,
            text="� Secondary Series",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(8, 2))
        
        self.comp_secondary_var = tk.StringVar()
        self.comp_secondary_combo = ctk.CTkComboBox(
            secondary_frame,
            variable=self.comp_secondary_var,
            values=series_names,
            width=int(dialog_width * 0.32),
            height=30,
            corner_radius=6,
            command=self._on_secondary_series_change
        )
        self.comp_secondary_combo.pack(padx=10, pady=(0, 5))
        
        # Secondary series info preview
        self.secondary_info_label = ctk.CTkLabel(
            secondary_frame,
            text="Select a series to see intelligent preview",
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray40"),
            wraplength=int(dialog_width * 0.32)
        )
        self.secondary_info_label.pack(anchor="w", padx=10, pady=(0, 8))
        
        # === Analysis Configuration Section ===
        config_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        config_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            config_frame,
            text="⚙️ Analysis Configuration",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        # Comparison type selection
        comp_type_frame = ctk.CTkFrame(config_frame, corner_radius=6)
        comp_type_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            comp_type_frame,
            text="📊 Comparison Type",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(8, 2))
        
        self.comp_type_var = tk.StringVar(value="Smart Overlay")
        comp_type_values = [
            "Smart Overlay", "Side-by-Side", "Difference Analysis", 
            "Correlation Plot", "Statistical Summary", "Performance Comparison"
        ]
        self.comp_type_combo = ctk.CTkComboBox(
            comp_type_frame,
            variable=self.comp_type_var,
            values=comp_type_values,
            width=int(dialog_width * 0.32),
            height=30,
            corner_radius=6,
            command=self._on_comparison_type_change
        )
        self.comp_type_combo.pack(padx=10, pady=(0, 5))
        
        # Description for comparison type
        self.comp_type_desc = ctk.CTkLabel(
            comp_type_frame,
            text="Intelligent overlay with auto-scaling and optimal color selection",
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray40"),
            wraplength=int(dialog_width * 0.32)
        )
        self.comp_type_desc.pack(anchor="w", padx=10, pady=(0, 8))
        
        # Time alignment options
        align_frame = ctk.CTkFrame(config_frame, corner_radius=6)
        align_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            align_frame,
            text="⏱️ Time Alignment",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(8, 2))
        
        self.time_align_var = tk.StringVar(value="Auto-Detect")
        align_values = [
            "Auto-Detect", "None", "Start Times", "Peak Alignment", 
            "Cross-Correlation", "Custom Offset"
        ]
        self.time_align_combo = ctk.CTkComboBox(
            align_frame,
            variable=self.time_align_var,
            values=align_values,
            width=int(dialog_width * 0.32),
            height=30,
            corner_radius=6,
            command=self._on_alignment_change
        )
        self.time_align_combo.pack(padx=10, pady=(0, 5))
        
        # Alignment description
        self.align_desc = ctk.CTkLabel(
            align_frame,
            text="Smart alignment detection based on data characteristics",
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray40"),
            wraplength=int(dialog_width * 0.32)
        )
        self.align_desc.pack(anchor="w", padx=10, pady=(0, 8))
        
        # Manual offset controls (initially hidden)
        self.manual_offset_frame = ctk.CTkFrame(align_frame, corner_radius=4)
        # Don't pack initially - will be shown when "Custom Offset" is selected
        
        ctk.CTkLabel(
            self.manual_offset_frame,
            text="Manual Time Offsets",
            font=ctk.CTkFont(weight="bold", size=11),
            text_color=("#1E40AF", "#3B82F6")
        ).pack(pady=(8, 5))
        
        # Primary series offset
        primary_offset_frame = ctk.CTkFrame(self.manual_offset_frame, fg_color="transparent")
        primary_offset_frame.pack(fill="x", padx=8, pady=2)
        
        ctk.CTkLabel(
            primary_offset_frame,
            text="Primary Series Offset:",
            font=ctk.CTkFont(size=10)
        ).pack(side="left")
        
        self.primary_offset_var = tk.DoubleVar(value=0.0)
        primary_offset_entry = ctk.CTkEntry(
            primary_offset_frame,
            textvariable=self.primary_offset_var,
            width=80,
            height=25
        )
        primary_offset_entry.pack(side="right")
        
        # Secondary series offset
        secondary_offset_frame = ctk.CTkFrame(self.manual_offset_frame, fg_color="transparent")
        secondary_offset_frame.pack(fill="x", padx=8, pady=2)
        
        ctk.CTkLabel(
            secondary_offset_frame,
            text="Secondary Series Offset:",
            font=ctk.CTkFont(size=10)
        ).pack(side="left")
        
        self.secondary_offset_var = tk.DoubleVar(value=0.0)
        secondary_offset_entry = ctk.CTkEntry(
            secondary_offset_frame,
            textvariable=self.secondary_offset_var,
            width=80,
            height=25
        )
        secondary_offset_entry.pack(side="right")
        
        # Offset units info
        offset_info = ctk.CTkLabel(
            self.manual_offset_frame,
            text="⏱️ Offsets in time units (e.g., seconds, minutes)",
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray40")
        )
        offset_info.pack(pady=(2, 8))
        
        # Advanced options
        advanced_frame = ctk.CTkFrame(config_frame, corner_radius=6)
        advanced_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            advanced_frame,
            text="🔬 Advanced Options",
            font=ctk.CTkFont(weight="bold", size=12)
        ).pack(anchor="w", padx=10, pady=(8, 5))
        
        # Confidence level
        confidence_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        confidence_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        confidence_label_frame = ctk.CTkFrame(confidence_frame, fg_color="transparent")
        confidence_label_frame.pack(fill="x")
        
        ctk.CTkLabel(
            confidence_label_frame,
            text="Confidence Level:",
            font=ctk.CTkFont(size=11)
        ).pack(side="left")
        
        self.confidence_label = ctk.CTkLabel(
            confidence_label_frame,
            text="95%",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#1E40AF", "#3B82F6")
        )
        self.confidence_label.pack(side="right")
        
        self.confidence_var = tk.DoubleVar(value=0.95)
        confidence_slider = ctk.CTkSlider(
            confidence_frame,
            from_=0.8,
            to=0.99,
            variable=self.confidence_var,
            width=int(dialog_width * 0.28),
            height=20,
            number_of_steps=19
        )
        confidence_slider.pack(pady=(5, 5))
        
        # Confidence description
        confidence_desc = ctk.CTkLabel(
            confidence_frame,
            text="🔍 Controls statistical confidence intervals and uncertainty bounds in analysis results",
            font=ctk.CTkFont(size=9),
            text_color=("gray60", "gray40"),
            wraplength=int(dialog_width * 0.32)
        )
        confidence_desc.pack(anchor="w", pady=(0, 5))
        
        # Smart toggles
        toggles_frame = ctk.CTkFrame(advanced_frame, fg_color="transparent")
        toggles_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        self.auto_analysis_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            toggles_frame,
            text="🤖 Auto-update analysis",
            variable=self.auto_analysis_var,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", pady=2)
        
        # === Action Buttons ===
        button_frame = ctk.CTkFrame(left_panel, corner_radius=8)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Main action buttons
        main_buttons = ctk.CTkFrame(button_frame, fg_color="transparent")
        main_buttons.pack(fill="x", padx=15, pady=15)
        
        self.run_button = ctk.CTkButton(
            main_buttons,
            text="🚀 Run Analysis",
            command=self.run_comparison_analysis,
            width=int(dialog_width * 0.32),
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#1E40AF", "#3B82F6"),
            hover_color=("#1E3A8A", "#2563EB")
        )
        self.run_button.pack(fill="x", pady=(0, 8))
        
        # Quick action buttons row
        quick_actions = ctk.CTkFrame(main_buttons, fg_color="transparent")
        quick_actions.pack(fill="x")
        
        ctk.CTkButton(
            quick_actions,
            text="⚡ Quick",
            command=self._quick_compare,
            width=int(dialog_width * 0.09),
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=(0, 3), fill="x", expand=True)
        
        ctk.CTkButton(
            quick_actions,
            text="📋 Copy",
            command=self._copy_results,
            width=int(dialog_width * 0.09),
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=2, fill="x", expand=True)
        
        ctk.CTkButton(
            quick_actions,
            text="🔄 Reset",
            command=self._reset_comparison,
            width=int(dialog_width * 0.09),
            height=32,
            corner_radius=6,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=(3, 0), fill="x", expand=True)
        
        # === RIGHT COLUMN: Results and Visualization ===
        right_panel = ctk.CTkFrame(
            right_frame_wrapper,
            corner_radius=10
        )
        right_panel.pack(fill="both", expand=True)
        
        # Results header with status
        results_header = ctk.CTkFrame(right_panel, height=50, corner_radius=8)
        results_header.pack(fill="x", padx=15, pady=(15, 10))
        results_header.pack_propagate(False)
        
        # Header content frame to manage left and right elements
        header_content = ctk.CTkFrame(results_header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=15, pady=12)
        
        ctk.CTkLabel(
            header_content,
            text="📊 Analysis Results & Visualization",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")
        
        # Dynamic status indicator
        self.status_label = ctk.CTkLabel(
            header_content,
            text="🟡 Ready for analysis",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray40")
        )
        self.status_label.pack(side="right")
        
        # Tabbed results with intelligent height based on screen
        results_height = max(500, dialog_height - 250)
        
        self.results_tabview = ctk.CTkTabview(
            right_panel,
            height=results_height,
            corner_radius=8
        )
        self.results_tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # === Visualization Tab ===
        viz_tab = self.results_tabview.add("📈 Visualization")
        
        # Plot container with scrolling for large plots
        self.comparison_plot_frame = ctk.CTkScrollableFrame(
            viz_tab,
            corner_radius=6
        )
        self.comparison_plot_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))
        
        # Initial message
        initial_viz_msg = ctk.CTkLabel(
            self.comparison_plot_frame,
            text="🎯 Select two series and run analysis\nto see intelligent visualization",
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40"),
            justify="center"
        )
        initial_viz_msg.pack(expand=True, pady=50)
        
        # Graphical analysis type selector underneath the plot
        viz_controls_frame = ctk.CTkFrame(viz_tab, height=60, corner_radius=6)
        viz_controls_frame.pack(fill="x", padx=10, pady=(5, 10))
        viz_controls_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            viz_controls_frame,
            text="📊 Graphical Analysis Type:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(15, 10), pady=15)
        
        self.viz_type_var = tk.StringVar(value="Smart Overlay")
        viz_type_values = [
            "Smart Overlay", "Side-by-Side Comparison", "Difference Plot", 
            "Correlation Analysis", "Statistical Distribution", "Trend Comparison",
            "Scatter Matrix", "Box Plot Comparison", "Histogram Overlay", "Time Series Alignment"
        ]
        
        self.viz_type_combo = ctk.CTkComboBox(
            viz_controls_frame,
            variable=self.viz_type_var,
            values=viz_type_values,
            width=220,
            height=30,
            corner_radius=6,
            command=self._on_viz_type_change
        )
        self.viz_type_combo.pack(side="left", padx=(0, 10), pady=15)
        
        # Update button for real-time visualization changes
        self.update_viz_button = ctk.CTkButton(
            viz_controls_frame,
            text="🔄 Update",
            command=self._update_visualization,
            width=80,
            height=30,
            corner_radius=6,
            font=ctk.CTkFont(size=10)
        )
        self.update_viz_button.pack(side="left", padx=(0, 15), pady=15)
        
        # === Statistics Tab ===
        stats_tab = self.results_tabview.add("📊 Statistics")
        
        self.comparison_results = ctk.CTkTextbox(
            stats_tab,
            corner_radius=6,
            font=ctk.CTkFont(family="Consolas", size=11),
            wrap="word"
        )
        self.comparison_results.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === AI Insights Tab ===
        insights_tab = self.results_tabview.add("🧠 AI Insights")
        
        self.insights_text = ctk.CTkTextbox(
            insights_tab,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            wrap="word"
        )
        self.insights_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configure event handlers for intelligent behavior
        confidence_slider.configure(command=self._update_confidence_label)

        # Initialize with smart defaults
        self.root.after(100, self._initialize_smart_defaults)
    def _initialize_smart_defaults(self):
        """Initialize smart defaults for the comparison interface"""
        # Set up auto-completion and smart suggestions
        if hasattr(self, 'series_configs') and self.series_configs:
            series_names = [config.name for config in self.series_configs.values() if config.name]
            
            if len(series_names) >= 2:
                # Auto-select first two series for quick start
                self.comp_primary_var.set(series_names[0])
                self.comp_secondary_var.set(series_names[1])
                self._on_primary_series_change(series_names[0])
                self._on_secondary_series_change(series_names[1])
    
    def _on_primary_series_change(self, selected_name):
        """Handle primary series selection change"""
        if not selected_name:
            return
            
        # Find the series config by name
        series_config = None
        for config in self.series_configs.values():
            if config.name == selected_name:
                series_config = config
                break
        
        if series_config:
            # Get file data for preview
            file_data = self.loaded_files.get(series_config.file_id)
            if file_data:
                try:
                    x_data, y_data = series_config.get_data(file_data)
                    
                    # Validate data before processing
                    if len(y_data) == 0:
                        self.primary_info_label.configure(text="⚠️ No valid data points in selected series")
                        return
                    
                    # Generate smart info display
                    info_text = f"📈 {len(y_data):,} points | "
                    
                    # Only calculate min/max if we have data
                    try:
                        y_min = y_data.min()
                        y_max = y_data.max()
                        if not (np.isnan(y_min) or np.isnan(y_max)):
                            info_text += f"Range: {y_min:.2e} to {y_max:.2e} | "
                        else:
                            info_text += "Range: No valid numerical data | "
                    except (ValueError, TypeError):
                        info_text += "Range: Unable to calculate | "
                    
                    info_text += f"File: {file_data.filename}"
                    
                    self.primary_info_label.configure(text=info_text)
                except Exception as e:
                    self.primary_info_label.configure(text=f"⚠️ Error processing series data: {str(e)}")
                    return
                
                # Update secondary series options (exclude selected primary)
                other_series = [config.name for config in self.series_configs.values() 
                              if config.name and config.name != selected_name]
                self.comp_secondary_combo.configure(values=other_series)
                
                # Auto-run analysis if enabled
                if hasattr(self, 'auto_analysis_var') and self.auto_analysis_var.get():
                    if self.comp_secondary_var.get() and self.comp_secondary_var.get() != selected_name:
                        self._quick_compare()
    
    def _on_secondary_series_change(self, selected_name):
        """Handle secondary series selection change"""
        if not selected_name:
            return
            
        # Find the series config by name
        series_config = None
        for config in self.series_configs.values():
            if config.name == selected_name:
                series_config = config
                break
        
        if series_config:
            # Get file data for preview
            file_data = self.loaded_files.get(series_config.file_id)
            if file_data:
                try:
                    x_data, y_data = series_config.get_data(file_data)
                    
                    # Validate data before processing
                    if len(y_data) == 0:
                        self.secondary_info_label.configure(text="⚠️ No valid data points in selected series")
                        return
                    
                    # Generate smart info display
                    info_text = f"📈 {len(y_data):,} points | "
                    
                    # Only calculate min/max if we have data
                    try:
                        y_min = y_data.min()
                        y_max = y_data.max()
                        if not (np.isnan(y_min) or np.isnan(y_max)):
                            info_text += f"Range: {y_min:.2e} to {y_max:.2e} | "
                        else:
                            info_text += "Range: No valid numerical data | "
                    except (ValueError, TypeError):
                        info_text += "Range: Unable to calculate | "
                    
                    info_text += f"File: {file_data.filename}"
                    
                    self.secondary_info_label.configure(text=info_text)
                except Exception as e:
                    self.secondary_info_label.configure(text=f"⚠️ Error processing series data: {str(e)}")
                    return
                
                # Update primary series options (exclude selected secondary)
                other_series = [config.name for config in self.series_configs.values() 
                              if config.name and config.name != selected_name]
                self.comp_primary_combo.configure(values=other_series)
                
                # Auto-run analysis if enabled
                if hasattr(self, 'auto_analysis_var') and self.auto_analysis_var.get():
                    if self.comp_primary_var.get() and self.comp_primary_var.get() != selected_name:
                        self._quick_compare()
    
    def _on_comparison_type_change(self, selected_type):
        """Update description when comparison type changes"""
        descriptions = {
            "Smart Overlay": "Intelligent overlay with auto-scaling and optimal color selection",
            "Side-by-Side": "Independent plots for detailed individual analysis",
            "Difference Analysis": "Point-by-point difference with statistical significance",
            "Correlation Plot": "Scatter plot with correlation metrics and trend analysis",
            "Statistical Summary": "Comprehensive statistical comparison and tests",
            "Performance Comparison": "Vacuum-specific performance metrics and ratings"
        }
        
        desc = descriptions.get(selected_type, "Advanced comparison analysis")
        self.comp_type_desc.configure(text=desc)
        
        # Auto-suggest best alignment for this comparison type
        if selected_type in ["Difference Analysis", "Correlation Plot"]:
            self.time_align_var.set("Auto-Detect")
        elif selected_type == "Performance Comparison":
            self.time_align_var.set("Start Times")
    
    def _on_alignment_change(self, selected_alignment):
        """Update description when alignment method changes"""
        descriptions = {
            "Auto-Detect": "Smart alignment detection based on data characteristics",
            "None": "No alignment - use original time bases",
            "Start Times": "Align series start times to zero",
            "Peak Alignment": "Align based on maximum values",
            "Cross-Correlation": "Optimal lag detection using correlation",
            "Custom Offset": "Manual time offset specification"
        }
        
        desc = descriptions.get(selected_alignment, "Time series alignment")
        self.align_desc.configure(text=desc)
        
        # Show/hide manual offset controls based on selection
        if hasattr(self, 'manual_offset_frame'):
            if selected_alignment == "Custom Offset":
                self.manual_offset_frame.pack(fill="x", padx=10, pady=(5, 8))
            else:
                self.manual_offset_frame.pack_forget()
    
    def _update_confidence_label(self, value):
        """Update confidence level label"""
        self.confidence_label.configure(text=f"{int(float(value) * 100)}%")
    
    def _on_viz_type_change(self, selected_type):
        """Handle visualization type change from the dropdown under the plot"""
        # Auto-update visualization if data is available
        if hasattr(self, 'comp_primary_var') and self.comp_primary_var.get() and \
           hasattr(self, 'comp_secondary_var') and self.comp_secondary_var.get():
            # Update visualization immediately when type changes
            self.root.after(100, self._update_visualization)  # Small delay to ensure UI updates
    
    def _update_visualization(self):
        """Update the visualization based on current settings"""
        if not hasattr(self, 'comp_primary_var') or not self.comp_primary_var.get() or \
           not hasattr(self, 'comp_secondary_var') or not self.comp_secondary_var.get():
            return
            
        # Update the status
        if hasattr(self, 'status_label'):
            self.status_label.configure(text="🔄 Updating visualization...")
            
        try:
            # Get the selected visualization type
            viz_type = self.viz_type_var.get() if hasattr(self, 'viz_type_var') else "Smart Overlay"
            
            # Map visualization type to comparison type
            type_mapping = {
                "Smart Overlay": "Overlay",
                "Side-by-Side Comparison": "Side-by-Side", 
                "Difference Plot": "Difference Analysis",
                "Correlation Analysis": "Correlation Plot",
                "Statistical Distribution": "Statistical Summary",
                "Trend Comparison": "Performance Comparison",
                "Scatter Matrix": "Correlation",
                "Box Plot Comparison": "Statistical",
                "Histogram Overlay": "Overlay",
                "Time Series Alignment": "Smart Overlay"
            }
            
            mapped_type = type_mapping.get(viz_type, "Overlay")
            
            # Run comparison with the specific visualization type
            primary_name = self.comp_primary_var.get()
            secondary_name = self.comp_secondary_var.get()
            
            # Find the series configurations
            primary_config = None
            secondary_config = None
            
            for config in self.series_configs.values():
                if config.name == primary_name:
                    primary_config = config
                elif config.name == secondary_name:
                    secondary_config = config
            
            if primary_config and secondary_config:
                # Get the data for both series
                primary_file_data = self.loaded_files.get(primary_config.file_id)
                secondary_file_data = self.loaded_files.get(secondary_config.file_id)
                
                if primary_file_data and secondary_file_data:
                    # Get x and y data with error handling
                    try:
                        # Check if columns exist
                        if primary_config.x_column not in primary_file_data.data.columns:
                            raise ValueError(f"Column '{primary_config.x_column}' not found in primary series file")
                        if primary_config.y_column not in primary_file_data.data.columns:
                            raise ValueError(f"Column '{primary_config.y_column}' not found in primary series file")
                        if secondary_config.x_column not in secondary_file_data.data.columns:
                            raise ValueError(f"Column '{secondary_config.x_column}' not found in secondary series file")
                        if secondary_config.y_column not in secondary_file_data.data.columns:
                            raise ValueError(f"Column '{secondary_config.y_column}' not found in secondary series file")
                        
                        x1 = primary_file_data.data[primary_config.x_column].values
                        y1 = primary_file_data.data[primary_config.y_column].values
                        x2 = secondary_file_data.data[secondary_config.x_column].values
                        y2 = secondary_file_data.data[secondary_config.y_column].values
                        
                        # Validate data arrays
                        if len(x1) == 0 or len(y1) == 0 or len(x2) == 0 or len(y2) == 0:
                            raise ValueError("One or more data arrays are empty")
                        
                    except Exception as data_error:
                        raise ValueError(f"Data access error: {data_error}")
                    
                    # Perform comparison and create plot with the selected type
                    results = self.perform_series_comparison(
                        x1, y1, x2, y2, primary_name, secondary_name, 
                        mapped_type, self.time_align_var.get()
                    )
                    
                    # Create the plot with the specific type
                    self.create_comparison_plot(x1, y1, x2, y2, primary_name, secondary_name, mapped_type, results)
                    
                    # Update status
                    if hasattr(self, 'status_label'):
                        self.status_label.configure(text="✅ Visualization updated")
                        
        except Exception as e:
            print(f"Visualization update error: {e}")
            if hasattr(self, 'status_label'):
                self.status_label.configure(text="❌ Update failed")
            # Fallback to simple plot update
            self._create_simple_comparison_plot()

    def _create_simple_comparison_plot(self):
        """Create a simple comparison plot as fallback"""
        try:
            # Clear previous plot
            for widget in self.comparison_plot_frame.winfo_children():
                widget.destroy()
            
            # Create a simple message
            fallback_msg = ctk.CTkLabel(
                self.comparison_plot_frame,
                text="⚠️ Unable to update visualization\nPlease run analysis again",
                font=ctk.CTkFont(size=12),
                text_color=("gray60", "gray40"),
                justify="center"
            )
            fallback_msg.pack(expand=True, pady=50)
        except Exception as e:
            print(f"Fallback plot error: {e}")
    
    def _quick_compare(self):
        """Run a quick comparison with smart defaults"""
        if not self.comp_primary_var.get() or not self.comp_secondary_var.get():
            return
        
        # Save current settings
        original_type = self.comp_type_var.get()
        
        # Set to smart overlay for quick comparison
        self.comp_type_var.set("Smart Overlay")
        
        # Run the analysis
        self.run_comparison_analysis()
        
        # Restore original type
        self.comp_type_var.set(original_type)
    
    def _copy_results(self):
        """Copy results to clipboard"""
        try:
            results_text = self.comparison_results.get("1.0", "end-1c")
            self.comparison_results.clipboard_clear()
            self.comparison_results.clipboard_append(results_text)
            
            # Show temporary feedback
            original_text = self.comparison_results.get("1.0", "1.0 lineend")
            self.comparison_results.insert("1.0", "📋 Results copied to clipboard!\n\n")
            self.comparison_results.after(2000, lambda: self._remove_copy_notification())
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy results: {str(e)}")
    
    def _remove_copy_notification(self):
        """Remove the copy notification"""
        try:
            content = self.comparison_results.get("1.0", "end-1c")
            if content.startswith("📋 Results copied"):
                # Remove the first two lines (notification + empty line)
                lines = content.split('\n')
                new_content = '\n'.join(lines[2:])
                self.comparison_results.delete("1.0", "end")
                self.comparison_results.insert("1.0", new_content)
        except:
            pass
    
    def _reset_comparison(self):
        """Reset comparison interface to defaults"""
        self.comp_primary_var.set("")
        self.comp_secondary_var.set("")
        self.comp_type_var.set("Smart Overlay")
        self.time_align_var.set("Auto-Detect")
        self.confidence_var.set(0.95)
        self.auto_analysis_var.set(True)
        
        # Clear results
        self.comparison_results.delete("1.0", "end")
        self.insights_text.delete("1.0", "end")
        
        # Clear plot
        for widget in self.comparison_plot_frame.winfo_children():
            widget.destroy()
        
        # Reset info labels
        self.primary_info_label.configure(text="Select a series to see details")
        self.secondary_info_label.configure(text="Select a series to see details")
        
        # Restore series options
        series_names = [config.name for config in self.series_configs.values() if config.name]
        self.comp_primary_combo.configure(values=series_names)
        self.comp_secondary_combo.configure(values=series_names)

    def run_comparison_analysis(self):
        """Run intelligent comparison analysis between two series"""
        primary_name = self.comp_primary_var.get()
        secondary_name = self.comp_secondary_var.get()
        
        if not primary_name or not secondary_name:
            messagebox.showwarning("⚠️ Selection Required", 
                                 "Please select both primary and secondary series for comparison")
            return
            
        if primary_name == secondary_name:
            messagebox.showwarning("⚠️ Different Series Required", 
                                 "Please select different series for meaningful comparison")
            return
        
        # Update button to show progress
        original_text = self.run_button.cget("text")
        self.run_button.configure(text="🔄 Analyzing...", state="disabled")
        
        try:
            # Find series configs by name instead of ID
            primary_series = None
            secondary_series = None
            
            for config in self.series_configs.values():
                if config.name == primary_name:
                    primary_series = config
                elif config.name == secondary_name:
                    secondary_series = config
            
            if not primary_series or not secondary_series:
                messagebox.showerror("Error", "Could not find selected series configurations")
                return
            
            # Get file data
            primary_file = self.loaded_files.get(primary_series.file_id)
            secondary_file = self.loaded_files.get(secondary_series.file_id)
            
            if not primary_file or not secondary_file:
                messagebox.showerror("Error", "Could not find file data for selected series")
                return
            
            # Extract data
            primary_x, primary_y = primary_series.get_data(primary_file)
            secondary_x, secondary_y = secondary_series.get_data(secondary_file)
            
            # Map comparison type names to internal names
            comp_type_mapping = {
                "Smart Overlay": "Overlay",
                "Side-by-Side": "Side-by-Side", 
                "Difference Analysis": "Difference",
                "Correlation Plot": "Correlation",
                "Statistical Summary": "Statistical",
                "Performance Comparison": "Statistical"
            }
            
            comparison_type = comp_type_mapping.get(self.comp_type_var.get(), "Overlay")
            
            # Map alignment names
            align_mapping = {
                "Auto-Detect": self._detect_best_alignment(primary_x, primary_y, secondary_x, secondary_y),
                "None": "None",
                "Start Times": "Start Times", 
                "Peak Alignment": "Peak Alignment",
                "Cross-Correlation": "Cross-Correlation",
                "Custom Offset": f"Primary: {getattr(self, 'primary_offset_var', tk.DoubleVar(value=0.0)).get():.2f}, Secondary: {getattr(self, 'secondary_offset_var', tk.DoubleVar(value=0.0)).get():.2f}"
            }
            
            time_align = align_mapping.get(self.time_align_var.get(), "None")
            
            # Perform enhanced comparison
            results = self.perform_series_comparison(
                primary_x, primary_y, secondary_x, secondary_y,
                primary_name, secondary_name, comparison_type, time_align
            )
            
            # Create intelligent visualization
            self.create_comparison_plot(
                primary_x, primary_y, secondary_x, secondary_y,
                primary_name, secondary_name, comparison_type, results
            )
            
            # Display comprehensive results
            self.display_comparison_results(results, primary_name, secondary_name, comparison_type)
            
            # Generate AI insights
            self._generate_insights(results, primary_name, secondary_name, comparison_type)
            
            # Switch to appropriate results tab
            if comparison_type in ["Overlay", "Side-by-Side"]:
                self.results_tabview.set("📈 Visualization")
            else:
                self.results_tabview.set("📊 Statistics")
            
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Error in comparison analysis: {str(e)}")
            logger.error(f"Comparison analysis error: {e}")
        
        finally:
            # Restore button
            self.run_button.configure(text=original_text, state="normal")
    
    def _detect_best_alignment(self, x1, y1, x2, y2):
        """Intelligently detect the best alignment method"""
        try:
            # Check if series have similar time ranges
            t1_range = np.max(x1) - np.min(x1) 
            t2_range = np.max(x2) - np.min(x2)
            
            # Check for similar patterns (correlation-based)
            if len(y1) > 10 and len(y2) > 10:
                # Simple correlation check with error handling
                try:
                    min_len = min(len(y1), len(y2))
                    y1_sample = y1[:min_len]
                    y2_sample = y2[:min_len]
                    
                    # Check for valid data
                    valid_mask = np.isfinite(y1_sample) & np.isfinite(y2_sample)
                    if np.sum(valid_mask) > 10:
                        y1_clean = y1_sample[valid_mask]
                        y2_clean = y2_sample[valid_mask]
                        
                        # Check for sufficient variation
                        if np.std(y1_clean) > 1e-10 and np.std(y2_clean) > 1e-10:
                            corr = np.corrcoef(y1_clean, y2_clean)[0, 1]
                            
                            if not np.isfinite(corr):
                                corr = 0.0
                                
                            if abs(corr) > 0.7:
                                return "Start Times"  # Similar patterns, align starts
                            elif abs(corr) > 0.3:
                                return "Cross-Correlation"  # Some similarity, find best offset
                            else:
                                return "Peak Alignment"  # Different patterns, align peaks
                        else:
                            return "Start Times"  # No variation, use simple alignment
                    else:
                        return "Start Times"  # Not enough valid data
                except (np.linalg.LinAlgError, ValueError) as e:
                    print(f"Correlation calculation failed: {e}")
                    return "Start Times"  # Fallback to simple alignment
            
            # Default for short series
            return "Start Times"
            
        except Exception:
            return "None"
    
    def _generate_insights(self, results, primary_name, secondary_name, comparison_type):
        """Generate AI-like insights from comparison results"""
        insights = []
        
        try:
            # Header
            insights.append("🧠 INTELLIGENT ANALYSIS INSIGHTS")
            insights.append("=" * 50)
            insights.append("")
            
            # Basic comparison insights
            if 'series1_stats' in results and 'series2_stats' in results:
                s1 = results['series1_stats']
                s2 = results['series2_stats']
                
                # Mean comparison
                mean_diff_pct = ((s1['mean'] - s2['mean']) / s2['mean']) * 100 if s2['mean'] != 0 else 0
                if abs(mean_diff_pct) > 50:
                    insights.append(f"🔍 SIGNIFICANT DIFFERENCE: {primary_name} has {abs(mean_diff_pct):.1f}% {'higher' if mean_diff_pct > 0 else 'lower'} average values than {secondary_name}")
                elif abs(mean_diff_pct) > 10:
                    insights.append(f"📊 MODERATE DIFFERENCE: {mean_diff_pct:+.1f}% difference in average values")
                else:
                    insights.append(f"✅ SIMILAR AVERAGES: Both series have comparable mean values (±{abs(mean_diff_pct):.1f}%)")
                
                # Variability insights
                cv1 = s1['std'] / s1['mean'] if s1['mean'] != 0 else 0
                cv2 = s2['std'] / s2['mean'] if s2['mean'] != 0 else 0
                
                if cv1 > cv2 * 2:
                    insights.append(f"📈 VOLATILITY: {primary_name} is much more variable than {secondary_name}")
                elif cv2 > cv1 * 2:
                    insights.append(f"📈 VOLATILITY: {secondary_name} is much more variable than {primary_name}")
                else:
                    insights.append(f"📊 STABILITY: Both series show similar variability patterns")
                
                insights.append("")
            
            # Correlation insights
            if 'correlation' in results:
                corr = results['correlation']
                if abs(corr) > 0.8:
                    relationship = "STRONG" if corr > 0 else "STRONG INVERSE"
                    insights.append(f"🔗 {relationship} CORRELATION: R = {corr:.3f}")
                    insights.append(f"   The series move {'together' if corr > 0 else 'in opposite directions'} very consistently")
                elif abs(corr) > 0.5:
                    relationship = "MODERATE" if corr > 0 else "MODERATE INVERSE"  
                    insights.append(f"🔗 {relationship} CORRELATION: R = {corr:.3f}")
                    insights.append(f"   There's a noticeable {'positive' if corr > 0 else 'negative'} relationship")
                elif abs(corr) > 0.3:
                    insights.append(f"🔗 WEAK CORRELATION: R = {corr:.3f}")
                    insights.append(f"   Limited linear relationship between the series")
                else:
                    insights.append(f"🔗 NO LINEAR CORRELATION: R = {corr:.3f}")
                    insights.append(f"   The series appear to be independent or have non-linear relationships")
                
                insights.append("")
            
            # Statistical test insights
            if 'ttest' in results:
                p_val = results['ttest']['p_value']
                if p_val < 0.001:
                    insights.append(f"📊 HIGHLY SIGNIFICANT DIFFERENCE: p < 0.001")
                    insights.append(f"   Strong statistical evidence that the means differ")
                elif p_val < 0.05:
                    insights.append(f"📊 SIGNIFICANT DIFFERENCE: p = {p_val:.4f}")
                    insights.append(f"   Statistical evidence that the means differ")
                else:
                    insights.append(f"📊 NO SIGNIFICANT DIFFERENCE: p = {p_val:.4f}")
                    insights.append(f"   No strong evidence that the means differ statistically")
                
                insights.append("")
            
            # Vacuum-specific insights
            if 'vacuum_comparison' in results:
                vacuum = results['vacuum_comparison']
                insights.append("🔬 VACUUM SYSTEM INSIGHTS")
                insights.append("-" * 30)
                
                if 'base_pressure' in vacuum:
                    bp = vacuum['base_pressure']
                    ratio = bp['ratio']
                    if ratio > 10:
                        insights.append(f"🚨 LARGE BASE PRESSURE DIFFERENCE: {ratio:.1f}x difference")
                        insights.append(f"   {primary_name} may have significant leak or contamination issues")
                    elif ratio > 2:
                        insights.append(f"⚠️ MODERATE BASE PRESSURE DIFFERENCE: {ratio:.1f}x difference")
                        insights.append(f"   Consider checking pump efficiency and leak rates")
                    else:
                        insights.append(f"✅ SIMILAR BASE PRESSURES: {ratio:.1f}x difference")
                        insights.append(f"   Both systems achieve comparable ultimate vacuum")
                
                if 'stability' in vacuum:
                    better = vacuum['stability']['better']
                    insights.append(f"📊 STABILITY WINNER: {better}")
                    insights.append(f"   More stable pressure indicates better system control")
                
                insights.append("")
            
            # Recommendations
            insights.append("💡 RECOMMENDATIONS")
            insights.append("-" * 20)
            
            if comparison_type == "Overlay":
                insights.append("• Use 'Difference Analysis' to quantify point-by-point variations")
                insights.append("• Try 'Correlation Plot' to understand the relationship structure")
            elif comparison_type == "Correlation":
                insights.append("• Check 'Statistical Summary' for detailed hypothesis testing")
                insights.append("• Consider 'Performance Comparison' for vacuum-specific metrics")
            elif comparison_type == "Difference":
                insights.append("• Large differences may indicate different operating conditions")
                insights.append("• Check time alignment if patterns look similar but offset")
            
            # Add data quality insights
            insights.append("• Ensure both series represent comparable measurement conditions")
            insights.append("• Consider data preprocessing if noise levels differ significantly")
            
        except Exception as e:
            insights = [
                "🧠 INTELLIGENT ANALYSIS INSIGHTS",
                "=" * 50,
                "",
                f"⚠️ Could not generate insights: {str(e)}",
                "",
                "📊 Basic analysis completed successfully.",
                "Check the Statistics tab for detailed numerical results."
            ]
        
        # Display insights
        insights_text = "\n".join(insights)
        self.insights_text.delete("1.0", "end")
        self.insights_text.insert("1.0", insights_text)

    def perform_series_comparison(self, x1, y1, x2, y2, name1, name2, comp_type, time_align):
        """Perform detailed comparison analysis between two series"""
        results = {}
        
        # Validate input data
        if len(y1) == 0 or len(y2) == 0:
            raise ValueError("Cannot analyze empty data series")
        
        # Remove any NaN or infinite values
        y1_clean = y1[np.isfinite(y1)]
        y2_clean = y2[np.isfinite(y2)]
        
        if len(y1_clean) == 0 or len(y2_clean) == 0:
            raise ValueError("No valid data points after removing NaN/infinite values")
        
        # Basic statistics for both series (use original data for consistency)
        results['series1_stats'] = {
            'mean': np.mean(y1_clean),
            'std': np.std(y1_clean),
            'min': np.min(y1_clean),
            'max': np.max(y1_clean),
            'count': len(y1)
        }
        
        results['series2_stats'] = {
            'mean': np.mean(y2_clean),
            'std': np.std(y2_clean),
            'min': np.min(y2_clean),
            'max': np.max(y2_clean),
            'count': len(y2)
        }
        
        # Time alignment if requested
        if time_align != "None":
            x1_aligned, y1_aligned, x2_aligned, y2_aligned = self.align_time_series(
                x1, y1, x2, y2, time_align
            )
            results['alignment_method'] = time_align
        else:
            x1_aligned, y1_aligned = x1, y1
            x2_aligned, y2_aligned = x2, y2
        
        # Interpolate to common time base for detailed comparison
        if comp_type in ["Difference", "Correlation", "Statistical"]:
            # Create common time base
            try:
                # Convert datetime to numeric if needed
                if pd.api.types.is_datetime64_any_dtype(x1_aligned):
                    x1_numeric = (pd.Series(x1_aligned) - pd.Series(x1_aligned).iloc[0]).dt.total_seconds()
                else:
                    x1_numeric = np.array(x1_aligned)
                    
                if pd.api.types.is_datetime64_any_dtype(x2_aligned):
                    x2_numeric = (pd.Series(x2_aligned) - pd.Series(x2_aligned).iloc[0]).dt.total_seconds()
                else:
                    x2_numeric = np.array(x2_aligned)
                
                t_min = max(np.min(x1_numeric), np.min(x2_numeric))
                t_max = min(np.max(x1_numeric), np.max(x2_numeric))
                
                if t_max > t_min:
                    common_time = np.linspace(t_min, t_max, 1000)
                    
                    # Interpolate both series to common time base
                    y1_interp = np.interp(common_time, x1_numeric, y1_aligned)
                    y2_interp = np.interp(common_time, x2_numeric, y2_aligned)
                    
                    results['common_time'] = common_time
                    results['y1_interpolated'] = y1_interp
                    results['y2_interpolated'] = y2_interp
                    
                    # Calculate correlation with robust error handling
                    if len(y1_interp) > 1 and len(y2_interp) > 1:
                        try:
                            # Check for valid data
                            valid_mask = np.isfinite(y1_interp) & np.isfinite(y2_interp)
                            if np.sum(valid_mask) > 1:
                                y1_clean = y1_interp[valid_mask]
                                y2_clean = y2_interp[valid_mask]
                                
                                # Check for sufficient variation
                                if np.std(y1_clean) > 1e-10 and np.std(y2_clean) > 1e-10 and len(y1_clean) > 1:
                                    correlation = np.corrcoef(y1_clean, y2_clean)[0, 1]
                                    if np.isfinite(correlation):
                                        results['correlation'] = correlation
                                    else:
                                        results['correlation'] = 0.0
                                else:
                                    results['correlation'] = 0.0
                            else:
                                results['correlation'] = 0.0
                        except (np.linalg.LinAlgError, ValueError) as e:
                            print(f"Correlation calculation failed: {e}")
                            results['correlation'] = 0.0
                    
                    # Calculate difference metrics
                    try:
                        diff = y1_interp - y2_interp
                        results['difference_stats'] = {
                            'mean_diff': np.mean(diff),
                            'std_diff': np.std(diff),
                            'max_diff': np.max(np.abs(diff)),
                            'rms_diff': np.sqrt(np.mean(diff**2))
                        }
                    except Exception as e:
                        print(f"Difference calculation failed: {e}")
                        results['difference_stats'] = {
                            'mean_diff': 0.0,
                            'std_diff': 0.0,
                            'max_diff': 0.0,
                            'rms_diff': 0.0
                        }
                    
                    # Statistical tests
                    try:
                        from scipy.stats import ttest_ind, ks_2samp
                        
                        # T-test for means
                        t_stat, t_pval = ttest_ind(y1_interp, y2_interp)
                        results['ttest'] = {'statistic': t_stat, 'p_value': t_pval}
                        
                        # Kolmogorov-Smirnov test for distributions
                        ks_stat, ks_pval = ks_2samp(y1_interp, y2_interp)
                        results['ks_test'] = {'statistic': ks_stat, 'p_value': ks_pval}
                        
                    except ImportError:
                        logger.warning("scipy.stats not available for statistical tests")
                    except Exception as e:
                        print(f"Statistical tests failed: {e}")
                        
            except Exception as e:
                logger.warning(f"Failed to create common time base: {e}")
                # Skip interpolation-dependent analysis
                results['correlation'] = 0.0
        
        # Performance metrics comparison (if applicable for vacuum data)
        if 'pressure' in name1.lower() or 'vacuum' in name1.lower():
            results['vacuum_comparison'] = self.compare_vacuum_performance(
                x1_aligned, y1_aligned, x2_aligned, y2_aligned, name1, name2
            )
        
        return results

    def align_time_series(self, x1, y1, x2, y2, method):
        """Align time series using specified method"""
        if method == "Start Times":
            # Align start times to zero
            x1_aligned = x1 - x1[0]
            x2_aligned = x2 - x2[0]
            return x1_aligned, y1, x2_aligned, y2
            
        elif method == "Peak Alignment":
            # Align based on maximum values
            peak1_idx = np.argmax(y1)
            peak2_idx = np.argmax(y2)
            
            time_offset = x1[peak1_idx] - x2[peak2_idx]
            x2_aligned = x2 + time_offset
            
            return x1, y1, x2_aligned, y2
            
        elif method == "Cross-Correlation":
            # Align based on cross-correlation
            # Simplified implementation - could be enhanced
            correlation = np.correlate(y1, y2, mode='full')
            lag = np.argmax(correlation) - len(y2) + 1
            
            if lag > 0:
                x1_aligned = x1[lag:]
                y1_aligned = y1[lag:]
                x2_aligned = x2
                y2_aligned = y2
            else:
                x1_aligned = x1
                y1_aligned = y1
                x2_aligned = x2[-lag:]
                y2_aligned = y2[-lag:]
            
            return x1_aligned, y1_aligned, x2_aligned, y2_aligned
            
        elif method == "Custom Offset":
            # Apply manual time offsets
            primary_offset = getattr(self, 'primary_offset_var', tk.DoubleVar(value=0.0)).get()
            secondary_offset = getattr(self, 'secondary_offset_var', tk.DoubleVar(value=0.0)).get()
            
            x1_aligned = x1 + primary_offset
            x2_aligned = x2 + secondary_offset
            
            return x1_aligned, y1, x2_aligned, y2
        
        return x1, y1, x2, y2

    def compare_vacuum_performance(self, x1, y1, x2, y2, name1, name2):
        """Compare vacuum-specific performance metrics"""
        comparison = {}
        
        try:
            # Base pressure comparison
            base1 = np.percentile(y1, 10)
            base2 = np.percentile(y2, 10)
            comparison['base_pressure'] = {
                name1: base1,
                name2: base2,
                'ratio': base1 / base2 if base2 != 0 else float('inf')
            }
            
            # Pressure stability comparison
            stability1 = np.std(y1) / np.mean(y1)
            stability2 = np.std(y2) / np.mean(y2)
            comparison['stability'] = {
                name1: stability1,
                name2: stability2,
                'better': name1 if stability1 < stability2 else name2
            }
            
            # Pump-down efficiency (if applicable)
            if len(y1) > 10 and len(y2) > 10:
                # Check for pump-down patterns
                log_y1 = np.log10(y1 + 1e-12)
                log_y2 = np.log10(y2 + 1e-12)
                
                # Calculate average pumping rates
                pump_rate1 = -np.mean(np.gradient(log_y1))
                pump_rate2 = -np.mean(np.gradient(log_y2))
                
                comparison['pump_efficiency'] = {
                    name1: pump_rate1,
                    name2: pump_rate2,
                    'better': name1 if pump_rate1 > pump_rate2 else name2
                }
        
        except Exception as e:
            logger.error(f"Error in vacuum performance comparison: {e}")
            comparison['error'] = str(e)
        
        return comparison

    def create_comparison_plot(self, x1, y1, x2, y2, name1, name2, comp_type, results):
        """Create comparison visualization with appropriate sizing"""
        # Clear previous plot
        for widget in self.comparison_plot_frame.winfo_children():
            widget.destroy()
        
        # Use smaller, more appropriate figure size for UI
        fig = Figure(figsize=(8, 5), dpi=80)
        fig.patch.set_facecolor('white')
        
        try:
            if comp_type in ["Overlay", "Smart Overlay"]:
                ax = fig.add_subplot(111)
                ax.plot(x1, y1, label=name1, alpha=0.8, linewidth=1.5)
                ax.plot(x2, y2, label=name2, alpha=0.8, linewidth=1.5)
                ax.set_xlabel("Time", fontsize=10)
                ax.set_ylabel("Value", fontsize=10)
                ax.set_title(f"Overlay Comparison: {name1} vs {name2}", fontsize=11, pad=10)
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
                ax.tick_params(labelsize=9)
                
            elif comp_type == "Side-by-Side":
                ax1 = fig.add_subplot(211)
                ax1.plot(x1, y1, label=name1, color='blue', linewidth=1.5)
                ax1.set_title(name1, fontsize=10, pad=8)
                ax1.grid(True, alpha=0.3)
                ax1.tick_params(labelsize=8)
                
                ax2 = fig.add_subplot(212)
                ax2.plot(x2, y2, label=name2, color='orange', linewidth=1.5)
                ax2.set_title(name2, fontsize=10, pad=8)
                ax2.set_xlabel("Time", fontsize=10)
                ax2.grid(True, alpha=0.3)
                ax2.tick_params(labelsize=8)
                
            elif comp_type in ["Difference", "Difference Analysis"] and 'common_time' in results:
                ax = fig.add_subplot(111)
                diff = results['y1_interpolated'] - results['y2_interpolated']
                ax.plot(results['common_time'], diff, label=f"{name1} - {name2}", color='red', linewidth=1.5)
                ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
                ax.set_xlabel("Time", fontsize=10)
                ax.set_ylabel("Difference", fontsize=10)
                ax.set_title(f"Difference: {name1} - {name2}", fontsize=11, pad=10)
                ax.grid(True, alpha=0.3)
                ax.tick_params(labelsize=9)
                
            elif comp_type in ["Correlation", "Correlation Plot"] and 'y1_interpolated' in results:
                ax = fig.add_subplot(111)
                y1_interp = results['y1_interpolated']
                y2_interp = results['y2_interpolated']
                ax.scatter(y1_interp, y2_interp, alpha=0.6, s=20)
                
                # Add trend line with robust error handling
                if len(y1_interp) > 1:
                    try:
                        # Check for valid data
                        valid_mask = np.isfinite(y1_interp) & np.isfinite(y2_interp)
                        if np.sum(valid_mask) > 1:
                            y1_clean = y1_interp[valid_mask]
                            y2_clean = y2_interp[valid_mask]
                            
                            # Only fit if we have enough data points
                            if len(y1_clean) > 1 and np.std(y1_clean) > 1e-10:
                                z = np.polyfit(y1_clean, y2_clean, 1)
                                p = np.poly1d(z)
                                ax.plot(y1_clean, p(y1_clean), "r--", alpha=0.8, linewidth=1.5)
                    except (np.linalg.LinAlgError, np.RankWarning, ValueError) as e:
                        # Skip trend line if computation fails
                        print(f"Trend line computation failed: {e}")
                        pass
                
                ax.set_xlabel(name1, fontsize=10)
                ax.set_ylabel(name2, fontsize=10)
                ax.set_title(f"Correlation: {name1} vs {name2}", fontsize=11, pad=10)
                if 'correlation' in results:
                    ax.text(0.05, 0.95, f"R = {results['correlation']:.3f}", 
                           transform=ax.transAxes, bbox=dict(boxstyle="round", facecolor="white"),
                           fontsize=9)
                ax.grid(True, alpha=0.3)
                ax.tick_params(labelsize=9)
                
            elif comp_type in ["Statistical Summary", "Statistical"]:
                # Create statistical summary visualization
                ax = fig.add_subplot(111)
                
                # Box plot comparison
                data_to_plot = [y1, y2]
                box_plot = ax.boxplot(data_to_plot, tick_labels=[name1, name2], patch_artist=True)
                
                # Color the boxes
                colors = ['lightblue', 'lightcoral']
                for patch, color in zip(box_plot['boxes'], colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.7)
                
                ax.set_ylabel("Value", fontsize=10)
                ax.set_title("Statistical Summary Comparison", fontsize=11, pad=10)
                ax.grid(True, alpha=0.3, axis='y')
                ax.tick_params(labelsize=9)
                
                # Add statistical annotations
                if 'series1_stats' in results and 'series2_stats' in results:
                    stats1 = results['series1_stats']
                    stats2 = results['series2_stats']
                    
                    info_text = f"{name1}: μ={stats1['mean']:.3f}, σ={stats1['std']:.3f}\n"
                    info_text += f"{name2}: μ={stats2['mean']:.3f}, σ={stats2['std']:.3f}"
                    
                    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, 
                           bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
                           fontsize=8, verticalalignment='top')
                
            elif comp_type in ["Performance Comparison", "Performance"]:
                # Create performance comparison visualization
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
                    
                    ax.set_xlabel('Performance Metrics', fontsize=10)
                    ax.set_ylabel('Value', fontsize=10)
                    ax.set_title('Performance Comparison', fontsize=11, pad=10)
                    ax.set_xticks(x_pos)
                    ax.set_xticklabels(metrics, fontsize=9)
                    ax.legend(fontsize=9)
                    ax.grid(True, alpha=0.3, axis='y')
                    ax.tick_params(labelsize=9)
                    
                    # Add value labels on bars
                    for bars in [bars1, bars2]:
                        for bar in bars:
                            height = bar.get_height()
                            if np.isfinite(height) and height != 0:
                                ax.text(bar.get_x() + bar.get_width()/2., height,
                                       f'{height:.3e}', ha='center', va='bottom', fontsize=7)
                    
                except Exception as e:
                    # Fallback to simple overlay if performance metrics fail
                    ax.plot(x1, y1, label=name1, alpha=0.8, linewidth=1.5)
                    ax.plot(x2, y2, label=name2, alpha=0.8, linewidth=1.5)
                    ax.set_xlabel("Time", fontsize=10)
                    ax.set_ylabel("Value", fontsize=10)
                    ax.set_title(f"Performance Comparison: {name1} vs {name2}", fontsize=11, pad=10)
                    ax.legend(fontsize=9)
                    ax.grid(True, alpha=0.3)
                    ax.tick_params(labelsize=9)
            
            else:
                # Default fallback - overlay plot
                ax = fig.add_subplot(111)
                ax.plot(x1, y1, label=name1, alpha=0.8, linewidth=1.5)
                ax.plot(x2, y2, label=name2, alpha=0.8, linewidth=1.5)
                ax.set_xlabel("Time", fontsize=10)
                ax.set_ylabel("Value", fontsize=10)
                ax.set_title(f"Comparison: {name1} vs {name2}", fontsize=11, pad=10)
                ax.legend(fontsize=9)
                ax.grid(True, alpha=0.3)
                ax.tick_params(labelsize=9)
            
            # Apply tight layout with smaller padding
            fig.tight_layout(pad=1.5)
            
        except Exception as e:
            # Error handling - create simple error plot
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Plot Error: {str(e)}\n\nUsing fallback visualization", 
                   ha='center', va='center', transform=ax.transAxes,
                   bbox=dict(boxstyle="round", facecolor="lightyellow"),
                   fontsize=10)
            
            # Try simple fallback plot
            try:
                ax.plot(x1, y1, label=name1, alpha=0.8, linewidth=1.5)
                ax.plot(x2, y2, label=name2, alpha=0.8, linewidth=1.5)
                ax.legend(fontsize=9)
            except:
                pass  # If even fallback fails, show error message only
            
            ax.set_title(f"Comparison Plot ({comp_type})", fontsize=11, pad=10)
            fig.tight_layout(pad=1.5)
        
        # Embed plot with better sizing
        canvas = FigureCanvasTkAgg(fig, self.comparison_plot_frame)
        canvas.draw()
        
        # Configure canvas widget to fit properly
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.configure(highlightthickness=0)
        canvas_widget.pack(fill="both", expand=True, padx=5, pady=5)

    def display_comparison_results(self, results, name1, name2, comp_type):
        """Display comparison results in text area"""
        results_text = f"COMPARISON ANALYSIS\n"
        results_text += "=" * 50 + "\n\n"
        
        results_text += f"Primary Series: {name1}\n"
        results_text += f"Secondary Series: {name2}\n"
        results_text += f"Comparison Type: {comp_type}\n\n"
        
        # Basic statistics
        if 'series1_stats' in results and 'series2_stats' in results:
            s1 = results['series1_stats']
            s2 = results['series2_stats']
            
            results_text += "BASIC STATISTICS\n"
            results_text += "-" * 20 + "\n"
            results_text += f"{name1}:\n"
            results_text += f"  Mean: {s1['mean']:.6f}\n"
            results_text += f"  Std:  {s1['std']:.6f}\n"
            results_text += f"  Min:  {s1['min']:.6f}\n"
            results_text += f"  Max:  {s1['max']:.6f}\n\n"
            
            results_text += f"{name2}:\n"
            results_text += f"  Mean: {s2['mean']:.6f}\n"
            results_text += f"  Std:  {s2['std']:.6f}\n"
            results_text += f"  Min:  {s2['min']:.6f}\n"
            results_text += f"  Max:  {s2['max']:.6f}\n\n"
            
            # Relative differences
            results_text += "RELATIVE DIFFERENCES\n"
            results_text += "-" * 20 + "\n"
            if s2['mean'] != 0:
                mean_diff_pct = ((s1['mean'] - s2['mean']) / s2['mean']) * 100
                results_text += f"Mean difference: {mean_diff_pct:.2f}%\n"
            if s2['std'] != 0:
                std_diff_pct = ((s1['std'] - s2['std']) / s2['std']) * 100
                results_text += f"Std difference: {std_diff_pct:.2f}%\n"
            results_text += "\n"
        
        # Correlation
        if 'correlation' in results:
            results_text += "CORRELATION ANALYSIS\n"
            results_text += "-" * 20 + "\n"
            corr = results['correlation']
            results_text += f"Correlation coefficient: {corr:.4f}\n"
            if abs(corr) > 0.8:
                strength = "Strong"
            elif abs(corr) > 0.5:
                strength = "Moderate"
            elif abs(corr) > 0.3:
                strength = "Weak"
            else:
                strength = "Very weak"
            results_text += f"Correlation strength: {strength}\n\n"
        
        # Difference statistics
        if 'difference_stats' in results:
            diff = results['difference_stats']
            results_text += "DIFFERENCE ANALYSIS\n"
            results_text += "-" * 20 + "\n"
            results_text += f"Mean difference: {diff['mean_diff']:.6f}\n"
            results_text += f"Std of differences: {diff['std_diff']:.6f}\n"
            results_text += f"Max absolute difference: {diff['max_diff']:.6f}\n"
            results_text += f"RMS difference: {diff['rms_diff']:.6f}\n\n"
        
        # Statistical tests
        if 'ttest' in results:
            ttest = results['ttest']
            results_text += "STATISTICAL TESTS\n"
            results_text += "-" * 20 + "\n"
            results_text += f"T-test p-value: {ttest['p_value']:.6f}\n"
            if ttest['p_value'] < 0.05:
                results_text += "Means are significantly different (p < 0.05)\n"
            else:
                results_text += "Means are not significantly different (p ≥ 0.05)\n"
        
        if 'ks_test' in results:
            ks = results['ks_test']
            results_text += f"K-S test p-value: {ks['p_value']:.6f}\n"
            if ks['p_value'] < 0.05:
                results_text += "Distributions are significantly different (p < 0.05)\n"
            else:
                results_text += "Distributions are not significantly different (p ≥ 0.05)\n"
            results_text += "\n"
        
        # Vacuum-specific comparison
        if 'vacuum_comparison' in results:
            vacuum = results['vacuum_comparison']
            results_text += "VACUUM PERFORMANCE\n"
            results_text += "-" * 20 + "\n"
            
            if 'base_pressure' in vacuum:
                bp = vacuum['base_pressure']
                results_text += f"Base pressure ratio: {bp['ratio']:.2f}\n"
                better_base = name1 if bp[name1] < bp[name2] else name2
                results_text += f"Better base pressure: {better_base}\n"
            
            if 'stability' in vacuum:
                stab = vacuum['stability']
                results_text += f"Better stability: {stab['better']}\n"
            
            if 'pump_efficiency' in vacuum:
                pump = vacuum['pump_efficiency']
                results_text += f"Better pump efficiency: {pump['better']}\n"
        
        self.comparison_results.delete("1.0", "end")
        self.comparison_results.insert("1.0", results_text)

    def export_comparison_results(self):
        """Export comparison results to file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Comparison Results"
            )
            
            if file_path:
                content = self.comparison_results.get("1.0", "end-1c")
                with open(file_path, 'w') as f:
                    f.write(content)
                messagebox.showinfo("Success", f"Results exported to {file_path}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export results: {str(e)}")

    def _run_statistical_analysis(self):
        """Run statistical analysis on selected series"""
        series_name = self.stat_series_var.get()
        if not series_name:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find series
        series = None
        for s in self.series_configs.values():
            if s.name == series_name:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files.get(series.file_id)
        if not file_data:
            return

        x_data, y_data = series.get_data(file_data)

        # Run analysis
        stats = self.statistical_analyzer.calculate_basic_stats(y_data)
        normality = self.statistical_analyzer.test_normality(y_data)
        outliers = self.statistical_analyzer.detect_outliers(y_data)

        # Display results
        results = f"STATISTICAL ANALYSIS: {series_name}\n"
        results += "=" * 50 + "\n\n"

        results += "Basic Statistics:\n"
        results += f"  Count: {stats['count']}\n"
        results += f"  Mean: {stats['mean']:.6f}\n"
        results += f"  Median: {stats['median']:.6f}\n"
        results += f"  Std Dev: {stats['std']:.6f}\n"
        results += f"  Min: {stats['min']:.6f}\n"
        results += f"  Max: {stats['max']:.6f}\n"
        results += f"  Skewness: {stats['skewness']:.3f}\n"
        results += f"  Kurtosis: {stats['kurtosis']:.3f}\n\n"

        results += "Normality Test:\n"
        results += f"  Is Normal: {normality['is_normal']}\n"
        results += f"  Shapiro p-value: {normality['shapiro_p']:.6f}\n\n"

        results += "Outlier Detection:\n"
        outlier_count = len(outliers) if isinstance(outliers, list) else 0
        total_count = len(y_data)
        outlier_percentage = (outlier_count / total_count * 100) if total_count > 0 else 0
        results += f"  Outliers Found: {outlier_count}\n"
        results += f"  Percentage: {outlier_percentage:.2f}%\n"

        self.stat_results.delete("1.0", "end")
        self.stat_results.insert("1.0", results)

    def _run_base_pressure_analysis(self):
        """Run base pressure analysis"""
        series_name = self.base_series_var.get()
        if not series_name:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find series
        series = None
        for s in self.series_configs.values():
            if s.name == series_name:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files.get(series.file_id)
        if not file_data:
            return

        x_data, y_data = series.get_data(file_data)
        window_size = self.window_size_var.get()

        # Run analysis
        result = self.vacuum_analyzer.calculate_base_pressure(
        y_data, window_size)
        
        # Handle different return types
        if isinstance(result, tuple):
            base_pressure, rolling_min, rolling_std = result
        else:
            base_pressure = result
            rolling_min = rolling_std = None

        # Store result
        self.vacuum_results['base_pressure'] = result

        # Display results
        text = f"BASE PRESSURE ANALYSIS: {series_name}\n"
        text += "=" * 50 + "\n\n"
        
        if isinstance(result, tuple):
            base_pressure = result[0]
            stability = result[1] if len(result) > 1 else 0.0
        else:
            base_pressure = result
            stability = 0.0
            
        text += f"Base Pressure: {base_pressure:.2e} mbar\n"
        text += f"Stability: {stability:.2e} mbar\n"
        text += f"Analysis Window: {window_size} minutes\n"

        self.base_text.delete(1.0, tk.END)
        self.base_text.insert(1.0, text)

    def _detect_spikes(self):
        """Detect pressure spikes"""
        series_name = self.spike_series_var.get()
        if not series_name:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find series
        series = None
        for s in self.series_configs.values():
            if s.name == series_name:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files.get(series.file_id)
        if not file_data:
            return

        x_data, y_data = series.get_data(file_data)
        threshold = self.spike_threshold_var.get()

        # Detect spikes
        spikes = self.vacuum_analyzer.detect_spikes(y_data, threshold)

        # Clear previous results
        for item in self.spikes_tree.get_children():
            self.spikes_tree.delete(item)

        # Add to treeview
        for i, spike in enumerate(spikes):
            self.spikes_tree.insert("", "end", values=(
                i + 1,
                spike['start_time'],
                spike['end_time'],
                spike['duration'],
                f"{spike['max_pressure']:.2e}",
                spike['severity']
            ))

        # Store result
        self.vacuum_results['spikes'] = spikes

    def _detect_leaks(self):
        """Detect vacuum leaks"""
        series_name = self.leak_series_var.get()
        if not series_name:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find series
        series = None
        for s in self.series_configs.values():
            if s.name == series_name:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files.get(series.file_id)
        if not file_data:
            return

        x_data, y_data = series.get_data(file_data)

        # Detect leaks (returns leak rate, not list of leaks)
        leak_rate = self.vacuum_analyzer.detect_leaks(y_data)

        # Display results
        text = f"LEAK DETECTION: {series_name}\n"
        text += "=" * 50 + "\n\n"

        if leak_rate and not np.isnan(leak_rate) and leak_rate > 0:
            text += f"Leak Rate Analysis:\n\n"
            text += f"  Calculated Leak Rate: {leak_rate:.2e} mbar·L/s\n\n"
            
            # Provide interpretation
            if leak_rate > 1e-6:
                text += "  Interpretation: High leak rate detected - significant leak present\n"
            elif leak_rate > 1e-8:
                text += "  Interpretation: Moderate leak rate - minor leak may be present\n"
            else:
                text += "  Interpretation: Low leak rate - system appears tight\n"
        else:
            text += "No significant leak detected or insufficient data for analysis\n"

        self.leak_text.delete(1.0, tk.END)
        self.leak_text.insert(1.0, text)

        # Store result
        self.vacuum_results['leak_rate'] = leak_rate

    def _analyze_pumpdown(self):
        """Analyze pump-down characteristics"""
        series_name = self.pump_series_var.get()
        if not series_name:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find series
        series = None
        for s in self.series_configs.values():
            if s.name == series_name:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files.get(series.file_id)
        if not file_data:
            return

        x_data, y_data = series.get_data(file_data)

        # Analyze pump-down
        result = self.vacuum_analyzer.analyze_pumpdown(y_data)

        # Display results
        text = f"PUMP-DOWN ANALYSIS: {series_name}\n"
        text += "=" * 50 + "\n\n"
        
        if result and isinstance(result, dict):
            text += f"Initial Pressure: {result.get('initial_pressure', 'N/A'):.2e} mbar\n"
            text += f"Minimum Pressure: {result.get('min_pressure', 'N/A'):.2e} mbar\n"
            text += f"Base Pressure: {result.get('base_pressure', 'N/A'):.2e} mbar\n"
            text += f"Pump-down Rate: {result.get('pumpdown_rate', 'N/A'):.2e} mbar/s\n"
            text += f"Leak Rate: {result.get('leak_rate', 'N/A'):.2e} mbar·L/s\n"
            
            if result.get('time_to_10_percent'):
                text += f"Time to 10% of initial: {result['time_to_10_percent']:.1f} seconds\n"
            
            text += f"Time to minimum: {result.get('time_to_min', 'N/A'):.1f} seconds\n"
            text += f"Pumping Efficiency: {result.get('pumping_efficiency', 'N/A'):.2e} mbar/s\n"
        else:
            text += "Error: Unable to analyze pumpdown data\n"

        self.pump_text.delete(1.0, tk.END)
        self.pump_text.insert(1.0, text)

        # Store result
        self.vacuum_results['pumpdown'] = result

    def _export_results(self):
        """Export analysis results"""
        filename = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    # Export current tab's results
                    active_tab = self.notebook.index(self.notebook.select())

                    if active_tab == 0:  # Statistical
                        f.write(self.stat_results.get(1.0, tk.END))
                    elif active_tab == 1:  # Vacuum
                        # Determine which vacuum sub-tab is active
                        vacuum_tab = self.notebook.nametowidget(self.notebook.select())
                        if "Base Pressure" in vacuum_tab.winfo_children()[0].winfo_name():
                            f.write(self.base_text.get(1.0, tk.END))
                        elif "Spike" in vacuum_tab.winfo_children()[0].winfo_name():
                            # Export spike data
                            f.write("Spike Detection Results\n")
                            f.write("=" * 50 + "\n")
                            for item in self.spikes_tree.get_children():
                                values = self.spikes_tree.item(item, 'values')
                                f.write(f"Spike {values[0]}: Start={values[1]}, End={values[2]}, "
                                        f"Duration={values[3]}, Max={values[4]}, Severity={values[5]}\n")
                        elif "Leak" in vacuum_tab.winfo_children()[0].winfo_name():
                            f.write(self.leak_text.get(1.0, tk.END))
                        elif "Pump-down" in vacuum_tab.winfo_children()[0].winfo_name():
                            f.write(self.pump_text.get(1.0, tk.END))

                    messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def protocol(self, protocol_name, callback):
        """Set protocol handler for dialog window"""
        return self.dialog.protocol(protocol_name, callback)

    def destroy(self):
        """Destroy the dialog"""
        try:
            self.dialog.destroy()
        except Exception:
            pass


class AnnotationDialog:
    """Dialog for managing plot annotations - Enhanced with Legacy Features"""

    def __init__(self, parent, annotation_manager, axes):
        self.parent = parent
        self.annotation_manager = annotation_manager
        self.axes = axes
        self.changed = False

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Annotation Manager")
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create UI
        self._create_widgets()

        # Load existing annotations
        self._refresh_annotation_list()

    def _create_widgets(self):
        """Create dialog widgets with legacy enhancements"""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Paned window for split view
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        # Left panel - Annotation tools
        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)

        # Right panel - Annotation list and properties
        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=2)

        # Create tools notebook
        self._create_tools_notebook(left_panel)

        # Create annotation list and properties
        self._create_annotation_list(right_panel)
        self._create_properties_panel(right_panel)

        # Buttons
        self._create_buttons()

    def _create_tools_notebook(self, parent):
        """Create annotation tools notebook"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Basic annotations tab
        basic_tab = ttk.Frame(notebook)
        notebook.add(basic_tab, text="Basic")
        self._create_basic_tools(basic_tab)

        # Data points tab
        data_tab = ttk.Frame(notebook)
        notebook.add(data_tab, text="Data Points")
        self._create_data_point_tools(data_tab)

        # Templates tab
        templates_tab = ttk.Frame(notebook)
        notebook.add(templates_tab, text="Templates")
        self._create_template_tools(templates_tab)

    def _create_basic_tools(self, parent):
        """Create basic annotation tools"""
        frame = ttk.LabelFrame(parent, text="Basic Annotations")
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        buttons = [
            ("Horizontal Line", self._add_horizontal_line),
            ("Vertical Line", self._add_vertical_line),
            ("Rectangle Region", self._add_region),
            ("Text Label", self._add_text),
            ("Arrow", self._add_arrow),
            ("Point", self._add_point)
        ]

        for text, command in buttons:
            btn = ttk.Button(frame, text=text, command=command)
            btn.pack(fill="x", padx=5, pady=2)

    def _create_data_point_tools(self, parent):
        """Create data point annotation tools"""
        frame = ttk.LabelFrame(parent, text="Data Point Annotations")
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Data point selection
        entry_frame = ttk.Frame(frame)
        entry_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(entry_frame, text="X:").pack(side="left")
        self.data_x_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.data_x_var, width=10).pack(side="left", padx=5)

        ttk.Label(entry_frame, text="Y:").pack(side="left")
        self.data_y_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable=self.data_y_var, width=10).pack(side="left", padx=5)

        ttk.Button(
            frame,
            text="Add Data Point",
            command=self._add_data_point
        ).pack(fill="x", padx=5, pady=5)

    def _create_template_tools(self, parent):
        """Create template annotation tools"""
        frame = ttk.LabelFrame(parent, text="Annotation Templates")
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        templates = [
            ("Base Pressure Line", self._add_base_pressure_template),
            ("Pressure Targets", self._add_pressure_targets),
            ("Process Regions", self._add_process_regions),
            ("Critical Points", self._add_critical_points)
        ]

        for text, command in templates:
            btn = ttk.Button(frame, text=text, command=command)
            btn.pack(fill="x", padx=5, pady=2)

    def _create_annotation_list(self, parent):
        """Create annotation list panel"""
        frame = ttk.LabelFrame(parent, text="Annotations")
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Annotation listbox
        self.annotation_listbox = tk.Listbox(frame, selectmode="single")
        self.annotation_listbox.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.annotation_listbox.bind("<<ListboxSelect>>", self._on_select_annotation)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, command=self.annotation_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.annotation_listbox.config(yscrollcommand=scrollbar.set)

        # Add buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            button_frame,
            text="+ Add",
            command=self._add_annotation,
            width=10
        ).pack(side="left", padx=2)

        ttk.Button(
            button_frame,
            text="- Remove",
            command=self._remove_annotation,
            width=10
        ).pack(side="left", padx=2)

        ttk.Button(
            button_frame,
            text="Clear All",
            command=self._clear_all,
            width=10
        ).pack(side="left", padx=2)

    def _create_properties_panel(self, parent):
        """Create properties panel"""
        frame = ttk.LabelFrame(parent, text="Properties")
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.properties_frame = ttk.Frame(frame)
        self.properties_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Placeholder for dynamic properties
        ttk.Label(self.properties_frame, text="Select an annotation to edit properties").pack(pady=20)

    def _create_buttons(self):
        """Create dialog buttons"""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", pady=10)

        ttk.Button(
            button_frame,
            text="Apply",
            command=self._apply,
            width=10
        ).pack(side="right", padx=5)

        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            width=10
        ).pack(side="right", padx=5)

    def _refresh_annotation_list(self):
        """Refresh the annotation list"""
        self.annotation_listbox.delete(0, tk.END)

        for ann in self.annotation_manager.get_annotations():
            display_text = f"{ann.type}: {ann.label}" if hasattr(ann, 'label') and ann.label else f"{ann.type}"
            self.annotation_listbox.insert(tk.END, display_text)

    def _on_select_annotation(self, event):
        """Handle annotation selection"""
        selection = self.annotation_listbox.curselection()
        if not selection:
            return

        # Get selected annotation
        index = selection[0]
        annotations = self.annotation_manager.get_annotations()

        if index < len(annotations):
            self._show_properties(annotations[index])

    def _show_properties(self, annotation: AnnotationConfig):
        """Show annotation properties"""
        # Clear previous properties
        for widget in self.properties_frame.winfo_children():
            widget.destroy()

        # Type
        frame = ttk.Frame(self.properties_frame)
        frame.pack(fill="x", pady=5)
        ttk.Label(frame, text="Type:").pack(side="left", padx=5)
        ttk.Label(frame, text=annotation.type).pack(side="left", padx=5)

        # Label
        frame = ttk.Frame(self.properties_frame)
        frame.pack(fill="x", pady=5)
        ttk.Label(frame, text="Label:").pack(side="left", padx=5)
        label_entry = ttk.Entry(frame, width=20)
        label_entry.insert(0, annotation.label)
        label_entry.pack(side="left", padx=5)

        # Color
        frame = ttk.Frame(self.properties_frame)
        frame.pack(fill="x", pady=5)
        ttk.Label(frame, text="Color:").pack(side="left", padx=5)
        color_button = ctk.CTkButton(
            frame,
            text="",
            width=3,
            fg_color=annotation.color
        )
        color_button.pack(side="left", padx=5)

        # Position fields based on type
        if annotation.type in ["line", "point"]:
            if annotation.x_data is not None:
                frame = ttk.Frame(self.properties_frame)
                frame.pack(fill="x", pady=5)
                ttk.Label(frame, text="X Position:").pack(side="left", padx=5)
                ttk.Label(frame, text=str(annotation.x_data)).pack(side="left", padx=5)

            if annotation.y_data is not None:
                frame = ttk.Frame(self.properties_frame)
                frame.pack(fill="x", pady=5)
                ttk.Label(frame, text="Y Position:").pack(side="left", padx=5)
                ttk.Label(frame, text=str(annotation.y_data)).pack(side="left", padx=5)

    def _add_annotation(self):
        """Add new annotation"""
        # Simple dialog for annotation type
        types = ["line", "region", "text", "arrow", "point"]

        # Create simple selection dialog
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Add Annotation")
        dialog.geometry("300x400")
        dialog.transient(self.dialog)
        dialog.grab_set()

        ttk.Label(dialog, text="Select Type:", font=("", 12)).pack(pady=10)

        selected_type = tk.StringVar(value="line")

        for ann_type in types:
            ttk.Radiobutton(
                dialog,
                text=ann_type.capitalize(),
                variable=selected_type,
                value=ann_type
            ).pack(pady=5)

        def create_annotation():
            ann_type = selected_type.get()

            # Create default annotation based on type
            if ann_type == "line":
                ann = AnnotationConfig(
                    type="line",
                    label="Vertical Line",
                    x_data=0
                )
            elif ann_type == "region":
                ann = AnnotationConfig(
                    type="region",
                    label="Region",
                    x_data=0,
                    x_end=1
                )
            elif ann_type == "text":
                ann = AnnotationConfig(
                    type="text",
                    label="Text",
                    text="Annotation",
                    x_data=0,
                    y_data=0
                )
            elif ann_type == "arrow":
                ann = AnnotationConfig(
                    type="arrow",
                    label="Arrow",
                    x_data=0,
                    y_data=0,
                    x_end=1,
                    y_end=1
                )
            else:  # point
                ann = AnnotationConfig(
                    type="point",
                    label="Point",
                    x_data=0,
                    y_data=0
                )

            self.annotation_manager.add_annotation(ann)
            self._refresh_annotation_list()
            self.changed = True
            dialog.destroy()

        ttk.Button(
            dialog,
            text="Create",
            command=create_annotation,
            width=10
        ).pack(pady=20)

        ttk.Button(
            dialog,
            text="Cancel",
            command=dialog.destroy,
            width=10
        ).pack()

    def _add_horizontal_line(self):
        """Add horizontal line annotation"""
        ann = AnnotationConfig(
            type="hline",
            label="Horizontal Line",
            y_data=0.5
        )
        self.annotation_manager.add_annotation(ann)
        self._refresh_annotation_list()
        self.changed = True

    def _add_vertical_line(self):
        """Add vertical line annotation"""
        ann = AnnotationConfig(
            type="vline",
            label="Vertical Line",
            x_data=0.5
        )
        self.annotation_manager.add_annotation(ann)
        self._refresh_annotation_list()
        self.changed = True

    def _add_region(self):
        """Add region annotation"""
        ann = AnnotationConfig(
            type="region",
            label="Region",
            x_data=0.2,
            x_end=0.8
        )
        self.annotation_manager.add_annotation(ann)
        self._refresh_annotation_list()
        self.changed = True

    def _add_text(self):
        """Add text annotation"""
        ann = AnnotationConfig(
            type="text",
            label="Text",
            text="Annotation",
            x_data=0.5,
            y_data=0.5
        )
        self.annotation_manager.add_annotation(ann)
        self._refresh_annotation_list()
        self.changed = True

    def _add_arrow(self):
        """Add arrow annotation"""
        ann = AnnotationConfig(
            type="arrow",
            label="Arrow",
            x_data=0.2,
            y_data=0.2,
            x_end=0.8,
            y_end=0.8
        )
        self.annotation_manager.add_annotation(ann)
        self._refresh_annotation_list()
        self.changed = True

    def _add_point(self):
        """Add point annotation"""
        ann = AnnotationConfig(
            type="point",
            label="Point",
            x_data=0.5,
            y_data=0.5
        )
        self.annotation_manager.add_annotation(ann)
        self._refresh_annotation_list()
        self.changed = True

    def _add_data_point(self):
        """Add data point annotation"""
        try:
            x = float(self.data_x_var.get())
            y = float(self.data_y_var.get())

            ann = AnnotationConfig(
                type="point",
                label=f"Data Point ({x},{y})",
                x_data=x,
                y_data=y
            )
            self.annotation_manager.add_annotation(ann)
            self._refresh_annotation_list()
            self.changed = True
        except ValueError:
            messagebox.showerror("Error", "Invalid X or Y value")

    def _add_base_pressure_template(self):
        """Add base pressure line template"""
        ann = AnnotationConfig(
            type="hline",
            label="Base Pressure",
            y_data=0.1,
            color="green",
            line_style="--"
        )
        self.annotation_manager.add_annotation(ann)
        self._refresh_annotation_list()
        self.changed = True

    def _add_pressure_targets(self):
        """Add pressure target lines"""
        targets = [
            (1e-3, "High Vacuum", "blue"),
            (1e-6, "Ultra-High Vacuum", "green"),
            (1e-9, "Extreme High Vacuum", "purple")
        ]

        for pressure, label, color in targets:
            ann = AnnotationConfig(
                type="hline",
                label=label,
                y_data=pressure,
                color=color,
                line_style=":"
            )
            self.annotation_manager.add_annotation(ann)

        self._refresh_annotation_list()
        self.changed = True

    def _add_process_regions(self):
        """Add process region templates"""
        regions = [
            (0.1, 0.3, "Pump-down", "green"),
            (0.4, 0.6, "Process", "blue"),
            (0.7, 0.9, "Venting", "orange")
        ]

        for start, end, label, color in regions:
            ann = AnnotationConfig(
                type="region",
                label=label,
                x_data=start,
                x_end=end,
                color=color,
                alpha=0.2
            )
            self.annotation_manager.add_annotation(ann)

        self._refresh_annotation_list()
        self.changed = True

    def _add_critical_points(self):
        """Add critical point markers"""
        points = [
            (0.3, 0.8, "Peak", "red", "^"),
            (0.5, 0.2, "Valley", "blue", "v"),
            (0.7, 0.5, "Anomaly", "orange", "D")
        ]

        for x, y, label, color, marker in points:
            ann = AnnotationConfig(
                type="point",
                label=label,
                x_data=x,
                y_data=y,
                color=color,
                marker=marker,
                size=100
            )
            self.annotation_manager.add_annotation(ann)

        self._refresh_annotation_list()
        self.changed = True

    def _remove_annotation(self):
        """Remove selected annotation"""
        selection = self.annotation_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        annotations = list(self.annotation_manager.get_annotations().keys())

        if index < len(annotations):
            self.annotation_manager.remove_annotation(annotations[index])
            self._refresh_annotation_list()
            self.changed = True

    def _clear_all(self):
        """Clear all annotations"""
        if messagebox.askyesno("Confirm", "Remove all annotations?"):
            self.annotation_manager.clear_annotations()
            self._refresh_annotation_list()
            self.changed = True

    def _apply(self):
        """Apply changes and close"""
        self.dialog.destroy()


class DataPreviewDialog:
    """Dialog for previewing data files"""

    def __init__(self, parent, file_data: FileData):
        self.file_data = file_data

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Data Preview: {file_data.filename}")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create notebook
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Data tab
        data_tab = ttk.Frame(notebook)
        self.notebook.add("📊 Data")
        self._create_data_tab(data_tab)

        # Info tab
        info_tab = ttk.Frame(notebook)
        self.notebook.add("ℹ️ Info")
        self._create_info_tab(info_tab)

        # Statistics tab
        stats_tab = ttk.Frame(notebook)
        self.notebook.add("📈 Statistics")
        self._create_stats_tab(stats_tab)

        # Close button
        ctk.CTkButton(
            self.dialog,
            text="Close",
            command=self.dialog.destroy,
            width=100
        ).pack(pady=10)

    def _create_data_tab(self, parent):
        """Create data preview tab"""
        # Create treeview for data display
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Treeview
        columns = list(self.file_data.data.columns)
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )

        # Configure scrollbars
        v_scroll.config(command=tree.yview)
        h_scroll.config(command=tree.xview)

        # Pack components
        tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Configure columns
        tree.heading("#0", text="Index")
        tree.column("#0", width=60)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)

        # Add data (limited to first 1000 rows)
        df_preview = self.file_data.data.head(1000)
        for idx, row in df_preview.iterrows():
            tree.insert("", "end", text=str(idx), values=list(row))

    def _create_info_tab(self, parent):
        """Create file info tab"""
        info_frame = ctk.CTkScrollableFrame(parent)
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # File information
        info_data = [
            ("File Path", self.file_data.filepath),
            ("File Name", self.file_data.filename),
            ("Load Time", self.file_data.load_time.strftime("%Y-%m-%d %H:%M:%S")),
            ("Rows", f"{self.file_data.metadata['rows']:,}"),
            ("Columns", str(self.file_data.metadata['columns'])),
            ("Memory Usage", f"{self.file_data.metadata['memory_usage']:,} bytes"),
            ("Has Datetime", "Yes" if self.file_data.metadata['has_datetime'] else "No"),
            ("Has Numeric", "Yes" if self.file_data.metadata['has_numeric'] else "No")
        ]

        for label, value in info_data:
            frame = ctk.CTkFrame(info_frame)
            frame.pack(fill="x", pady=5)

            ctk.CTkLabel(
                frame,
                text=f"{label}:",
                font=("", 12, "bold"),
                width=150,
                anchor="w"
            ).pack(side="left", padx=10)

            ctk.CTkLabel(
                frame,
                text=str(value),
                anchor="w"
            ).pack(side="left", padx=10)

        # Column types
        ctk.CTkLabel(
            info_frame,
            text="Column Types:",
            font=("", 14, "bold")
        ).pack(pady=(20, 10))

        for col, dtype in self.file_data.metadata['dtypes'].items():
            frame = ctk.CTkFrame(info_frame)
            frame.pack(fill="x", pady=2)

            ctk.CTkLabel(
                frame,
                text=col,
                width=200,
                anchor="w"
            ).pack(side="left", padx=10)

            ctk.CTkLabel(
                frame,
                text=str(dtype),
                text_color="gray",
                anchor="w"
            ).pack(side="left", padx=10)

    def _create_stats_tab(self, parent):
        """Create statistics tab"""
        stats_frame = ctk.CTkScrollableFrame(parent)
        stats_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Get numeric columns
        numeric_cols = self.file_data.get_numeric_columns()

        if not numeric_cols:
            ctk.CTkLabel(
                stats_frame,
                text="No numeric columns found",
                font=("", 14),
                text_color="gray"
            ).pack(pady=50)
            return

        # Display statistics for each numeric column
        for col in numeric_cols[:10]:  # Limit to first 10 columns
            # Column header
            header = ctk.CTkFrame(stats_frame)
            header.pack(fill="x", pady=(10, 5))

            ctk.CTkLabel(
                header,
                text=col,
                font=("", 12, "bold")
            ).pack(side="left", padx=10)

            # Get column statistics
            stats = self.file_data.get_column_stats(col)

            # Display stats
            stats_text = (
                f"Mean: {stats['mean']:.3f} | "
                f"Median: {stats['median']:.3f} | "
                f"Std: {stats['std']:.3f} | "
                f"Min: {stats['min']:.3f} | "
                f"Max: {stats['max']:.3f}"
            )

            ctk.CTkLabel(
                stats_frame,
                text=stats_text,
                text_color="gray",
                anchor="w"
            ).pack(fill="x", padx=20, pady=2)

            # Separator
            ttk.Separator(stats_frame, orient="horizontal").pack(fill="x", pady=5)


class PlotConfigDialog:
    """Comprehensive plot configuration dialog"""

    def __init__(self, parent, plot_config):
        """
        Initialize plot configuration dialog

        Args:
            parent: Parent window
            plot_config: Dictionary containing current plot configuration
        """
        self.parent = parent
        self.plot_config = plot_config.copy()  # Work with a copy
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Plot Configuration")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Modern styling
        self.setup_styles()

        self.create_widgets()
        self.dialog.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")

    def setup_styles(self):
        """Configure ttk styles for modern appearance"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Success.TButton', foreground='white')
        style.map('Success.TButton', background=[('active', '#059669'), ('!active', '#10B981')])

    def create_widgets(self):
        """Create the dialog interface"""
        # Create main notebook
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.create_general_tab()
        self.create_axes_tab()
        self.create_style_tab()
        self.create_data_tab()

        # Button frame
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Apply", command=self.apply_config,
                   style='Success.TButton').pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Reset Defaults", command=self.reset_defaults).pack(side='left')

    def create_general_tab(self):
        """Create general settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="General")

        # Title settings
        title_frame = ttk.LabelFrame(tab, text="Title", padding=10)
        title_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(title_frame, text="Title:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.title_var = tk.StringVar(value=self.plot_config.get('title', ''))
        ttk.Entry(title_frame, textvariable=self.title_var, width=50).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(title_frame, text="Size:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.title_size_var = tk.IntVar(value=self.plot_config.get('title_size', 16))
        ttk.Spinbox(title_frame, from_=8, to=32, textvariable=self.title_size_var, width=10).grid(row=0, column=3,
                                                                                                  padx=5, pady=5)

        # Figure size
        size_frame = ttk.LabelFrame(tab, text="Figure Size", padding=10)
        size_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(size_frame, text="Width:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.fig_width_var = tk.DoubleVar(value=self.plot_config.get('fig_width', 14))
        ttk.Spinbox(size_frame, from_=6, to=24, increment=0.5,
                    textvariable=self.fig_width_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(size_frame, text="Height:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.fig_height_var = tk.DoubleVar(value=self.plot_config.get('fig_height', 9))
        ttk.Spinbox(size_frame, from_=4, to=16, increment=0.5,
                    textvariable=self.fig_height_var, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(size_frame, text="DPI:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.dpi_var = tk.IntVar(value=self.plot_config.get('dpi', 100))
        ttk.Spinbox(size_frame, from_=50, to=300, increment=50,
                    textvariable=self.dpi_var, width=10).grid(row=1, column=1, padx=5, pady=5)

    def create_axes_tab(self):
        """Create axes configuration tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Axes")

        # X-axis
        x_frame = ttk.LabelFrame(tab, text="X-Axis", padding=10)
        x_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(x_frame, text="Label:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.xlabel_var = tk.StringVar(value=self.plot_config.get('xlabel', 'X Axis'))
        ttk.Entry(x_frame, textvariable=self.xlabel_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(x_frame, text="Size:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.xlabel_size_var = tk.IntVar(value=self.plot_config.get('xlabel_size', 12))
        ttk.Spinbox(x_frame, from_=8, to=24, textvariable=self.xlabel_size_var, width=10).grid(row=0, column=3, padx=5,
                                                                                               pady=5)

        self.log_x_var = tk.BooleanVar(value=self.plot_config.get('log_scale_x', False))
        ttk.Checkbutton(x_frame, text="Logarithmic Scale", variable=self.log_x_var).grid(row=1, column=0, columnspan=2,
                                                                                         sticky='w', padx=5, pady=5)

        self.x_auto_var = tk.BooleanVar(value=self.plot_config.get('x_auto_scale', True))
        ttk.Checkbutton(x_frame, text="Auto Scale", variable=self.x_auto_var,
                        command=self.toggle_x_limits).grid(row=1, column=2, columnspan=2, sticky='w', padx=5, pady=5)

        ttk.Label(x_frame, text="Min:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.x_min_var = tk.StringVar(value=self.plot_config.get('x_min', ''))
        self.x_min_entry = ttk.Entry(x_frame, textvariable=self.x_min_var, width=15)
        self.x_min_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(x_frame, text="Max:").grid(row=2, column=2, sticky='w', padx=5, pady=5)
        self.x_max_var = tk.StringVar(value=self.plot_config.get('x_max', ''))
        self.x_max_entry = ttk.Entry(x_frame, textvariable=self.x_max_var, width=15)
        self.x_max_entry.grid(row=2, column=3, sticky='w', padx=5, pady=5)

        # Y-axis
        y_frame = ttk.LabelFrame(tab, text="Y-Axis", padding=10)
        y_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(y_frame, text="Label:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.ylabel_var = tk.StringVar(value=self.plot_config.get('ylabel', 'Y Axis'))
        ttk.Entry(y_frame, textvariable=self.ylabel_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(y_frame, text="Size:").grid(row=0, column=2, sticky='w', padx=5, pady=5)
        self.ylabel_size_var = tk.IntVar(value=self.plot_config.get('ylabel_size', 12))
        ttk.Spinbox(y_frame, from_=8, to=24, textvariable=self.ylabel_size_var, width=10).grid(row=0, column=3, padx=5,
                                                                                               pady=5)

        self.log_y_var = tk.BooleanVar(value=self.plot_config.get('log_scale_y', False))
        ttk.Checkbutton(y_frame, text="Logarithmic Scale", variable=self.log_y_var).grid(row=1, column=0, columnspan=2,
                                                                                         sticky='w', padx=5, pady=5)

        self.y_auto_var = tk.BooleanVar(value=self.plot_config.get('y_auto_scale', True))
        ttk.Checkbutton(y_frame, text="Auto Scale", variable=self.y_auto_var,
                        command=self.toggle_y_limits).grid(row=1, column=2, columnspan=2, sticky='w', padx=5, pady=5)

        ttk.Label(y_frame, text="Min:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.y_min_var = tk.StringVar(value=self.plot_config.get('y_min', ''))
        self.y_min_entry = ttk.Entry(y_frame, textvariable=self.y_min_var, width=15)
        self.y_min_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(y_frame, text="Max:").grid(row=2, column=2, sticky='w', padx=5, pady=5)
        self.y_max_var = tk.StringVar(value=self.plot_config.get('y_max', ''))
        self.y_max_entry = ttk.Entry(y_frame, textvariable=self.y_max_var, width=15)
        self.y_max_entry.grid(row=2, column=3, sticky='w', padx=5, pady=5)

        self.toggle_x_limits()
        self.toggle_y_limits()

    def create_style_tab(self):
        """Create visual style settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Style")

        # Grid settings
        grid_frame = ttk.LabelFrame(tab, text="Grid", padding=10)
        grid_frame.pack(fill='x', padx=10, pady=10)

        self.show_grid_var = tk.BooleanVar(value=self.plot_config.get('show_grid', True))
        ttk.Checkbutton(grid_frame, text="Show Grid", variable=self.show_grid_var).grid(row=0, column=0, sticky='w',
                                                                                        padx=5, pady=5)

        ttk.Label(grid_frame, text="Style:").grid(row=0, column=1, sticky='w', padx=5, pady=5)
        self.grid_style_var = tk.StringVar(value=self.plot_config.get('grid_style', '-'))
        ttk.Combobox(grid_frame, textvariable=self.grid_style_var,
                     values=['-', '--', ':', '-.'], width=10).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(grid_frame, text="Alpha:").grid(row=0, column=3, sticky='w', padx=5, pady=5)
        self.grid_alpha_var = tk.DoubleVar(value=self.plot_config.get('grid_alpha', 0.3))
        ttk.Scale(grid_frame, from_=0.1, to=1.0, variable=self.grid_alpha_var,
                  orient='horizontal', length=150).grid(row=0, column=4, padx=5, pady=5)

        # Legend
        legend_frame = ttk.LabelFrame(tab, text="Legend", padding=10)
        legend_frame.pack(fill='x', padx=10, pady=10)

        self.show_legend_var = tk.BooleanVar(value=self.plot_config.get('show_legend', True))
        ttk.Checkbutton(legend_frame, text="Show Legend", variable=self.show_legend_var).grid(row=0, column=0,
                                                                                              sticky='w', padx=5,
                                                                                              pady=5)

        ttk.Label(legend_frame, text="Location:").grid(row=0, column=1, sticky='w', padx=5, pady=5)
        self.legend_loc_var = tk.StringVar(value=self.plot_config.get('legend_location', 'best'))
        ttk.Combobox(legend_frame, textvariable=self.legend_loc_var,
                     values=['best', 'upper right', 'upper left', 'lower right', 'lower left', 'center'],
                     width=15).grid(row=0, column=2, padx=5, pady=5)

        # Margins
        margin_frame = ttk.LabelFrame(tab, text="Margins", padding=10)
        margin_frame.pack(fill='x', padx=10, pady=10)

        margins = [('Left', 'margin_left'), ('Right', 'margin_right'),
                   ('Top', 'margin_top'), ('Bottom', 'margin_bottom')]

        for i, (label, key) in enumerate(margins):
            ttk.Label(margin_frame, text=f"{label}:").grid(row=i // 2, column=(i % 2) * 2, sticky='w', padx=5, pady=5)
            var = tk.DoubleVar(value=self.plot_config.get(key, 0.1))
            setattr(self, f"{key}_var", var)
            ttk.Scale(margin_frame, from_=0.02, to=0.3, variable=var,
                      orient='horizontal', length=150).grid(row=i // 2, column=(i % 2) * 2 + 1, padx=5, pady=5)

    def create_data_tab(self):
        """Create data handling settings tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Data")

        # Problematic data handling
        prob_frame = ttk.LabelFrame(tab, text="Problematic Data Detection", padding=10)
        prob_frame.pack(fill='x', padx=10, pady=10)

        self.detect_zeros_var = tk.BooleanVar(value=self.plot_config.get('detect_zeros', True))
        ttk.Checkbutton(prob_frame, text="Highlight Zero Values",
                        variable=self.detect_zeros_var).grid(row=0, column=0, sticky='w', padx=5, pady=5)

        self.zero_color_var = tk.StringVar(value=self.plot_config.get('zero_color', 'red'))
        ttk.Label(prob_frame, text="Zero Color:").grid(row=0, column=1, sticky='w', padx=5, pady=5)
        ttk.Combobox(prob_frame, textvariable=self.zero_color_var,
                     values=['red', 'orange', 'yellow', 'purple'], width=10).grid(row=0, column=2, padx=5, pady=5)

        self.detect_outliers_var = tk.BooleanVar(value=self.plot_config.get('detect_outliers', True))
        ttk.Checkbutton(prob_frame, text="Highlight Outliers",
                        variable=self.detect_outliers_var).grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self.outlier_threshold_var = tk.DoubleVar(value=self.plot_config.get('outlier_threshold', 3.0))
        ttk.Label(prob_frame, text="Outlier Threshold (σ):").grid(row=1, column=1, sticky='w', padx=5, pady=5)
        ttk.Spinbox(prob_frame, from_=1, to=10, increment=0.5,
                    textvariable=self.outlier_threshold_var, width=10).grid(row=1, column=2, padx=5, pady=5)

        self.detect_gaps_var = tk.BooleanVar(value=self.plot_config.get('detect_gaps', True))
        ttk.Checkbutton(prob_frame, text="Highlight Data Gaps",
                        variable=self.detect_gaps_var).grid(row=2, column=0, sticky='w', padx=5, pady=5)

        # Missing data handling
        missing_frame = ttk.LabelFrame(tab, text="Missing Data Handling", padding=10)
        missing_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(missing_frame, text="Method:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.missing_method_var = tk.StringVar(value=self.plot_config.get('missing_method', 'interpolate'))
        ttk.Combobox(missing_frame, textvariable=self.missing_method_var,
                     values=['interpolate', 'drop', 'fill_zero', 'forward_fill'],
                     width=15).grid(row=0, column=1, padx=5, pady=5)

        self.highlight_missing_var = tk.BooleanVar(value=self.plot_config.get('highlight_missing', True))
        ttk.Checkbutton(missing_frame, text="Highlight Missing Data",
                        variable=self.highlight_missing_var).grid(row=1, column=0, sticky='w', padx=5, pady=5)

        self.missing_color_var = tk.StringVar(value=self.plot_config.get('missing_color', 'gray'))
        ttk.Label(missing_frame, text="Missing Data Color:").grid(row=1, column=1, sticky='w', padx=5, pady=5)
        ttk.Combobox(missing_frame, textvariable=self.missing_color_var,
                     values=['gray', 'red', 'orange', 'purple'], width=10).grid(row=1, column=2, padx=5, pady=5)

    def toggle_x_limits(self):
        """Enable/disable X limit entries"""
        state = 'disabled' if self.x_auto_var.get() else 'normal'
        self.x_min_entry.config(state=state)
        self.x_max_entry.config(state=state)

    def toggle_y_limits(self):
        """Enable/disable Y limit entries"""
        state = 'disabled' if self.y_auto_var.get() else 'normal'
        self.y_min_entry.config(state=state)
        self.y_max_entry.config(state=state)

    def reset_defaults(self):
        """Reset to default configuration"""
        if messagebox.askyesno("Confirm", "Reset all settings to defaults?"):
            # Reset all variables to defaults
            self.title_var.set("Multi-File Data Analysis")
            self.title_size_var.set(16)
            self.fig_width_var.set(14)
            self.fig_height_var.set(9)
            self.dpi_var.set(100)

            self.xlabel_var.set("X Axis")
            self.xlabel_size_var.set(12)
            self.ylabel_var.set("Y Axis")
            self.ylabel_size_var.set(12)

            self.log_x_var.set(False)
            self.log_y_var.set(False)
            self.x_auto_var.set(True)
            self.y_auto_var.set(True)

            self.show_grid_var.set(True)
            self.grid_style_var.set('-')
            self.grid_alpha_var.set(0.3)
            self.show_legend_var.set(True)
            self.legend_loc_var.set('best')

            self.detect_zeros_var.set(True)
            self.detect_outliers_var.set(True)
            self.detect_gaps_var.set(True)

            self.toggle_x_limits()
            self.toggle_y_limits()

    def apply_config(self):
        """Apply configuration changes"""
        # Gather all settings
        self.plot_config = {
            'title': self.title_var.get(),
            'title_size': self.title_size_var.get(),
            'fig_width': self.fig_width_var.get(),
            'fig_height': self.fig_height_var.get(),
            'dpi': self.dpi_var.get(),

            'xlabel': self.xlabel_var.get(),
            'xlabel_size': self.xlabel_size_var.get(),
            'ylabel': self.ylabel_var.get(),
            'ylabel_size': self.ylabel_size_var.get(),

            'log_scale_x': self.log_x_var.get(),
            'log_scale_y': self.log_y_var.get(),
            'x_auto_scale': self.x_auto_var.get(),
            'y_auto_scale': self.y_auto_var.get(),

            'show_grid': self.show_grid_var.get(),
            'grid_style': self.grid_style_var.get(),
            'grid_alpha': self.grid_alpha_var.get(),
            'show_legend': self.show_legend_var.get(),
            'legend_location': self.legend_loc_var.get(),

            'margin_left': self.margin_left_var.get(),
            'margin_right': self.margin_right_var.get(),
            'margin_top': self.margin_top_var.get(),
            'margin_bottom': self.margin_bottom_var.get(),

            'detect_zeros': self.detect_zeros_var.get(),
            'zero_color': self.zero_color_var.get(),
            'detect_outliers': self.detect_outliers_var.get(),
            'outlier_threshold': self.outlier_threshold_var.get(),
            'detect_gaps': self.detect_gaps_var.get(),
            'missing_method': self.missing_method_var.get(),
            'highlight_missing': self.highlight_missing_var.get(),
            'missing_color': self.missing_color_var.get()
        }

        if not self.x_auto_var.get():
            self.plot_config['x_min'] = self.x_min_var.get()
            self.plot_config['x_max'] = self.x_max_var.get()

        if not self.y_auto_var.get():
            self.plot_config['y_min'] = self.y_min_var.get()
            self.plot_config['y_max'] = self.y_max_var.get()

        self.result = 'apply'
        self.dialog.destroy()

    def cancel(self):
        """Cancel without applying changes"""
        self.result = 'cancel'
        self.dialog.destroy()


class ExportDialog:
    """Dialog for exporting plots and data"""

    def __init__(self, parent, plot_manager):
        """
        Initialize export dialog

        Args:
            parent: Parent window
            plot_manager: PlotManager instance containing current plot and data
        """
        self.parent = parent
        self.plot_manager = plot_manager
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Export Options")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Modern styling
        self.setup_styles()

        self.create_widgets()
        self.dialog.geometry(f"+{parent.winfo_rootx() + 50}+{parent.winfo_rooty() + 50}")

    def setup_styles(self):
        """Configure ttk styles for modern appearance"""
        style = ttk.Style()
        style.theme_use('clam')

        # Configure colors
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Success.TButton', foreground='white')
        style.map('Success.TButton', background=[('active', '#059669'), ('!active', '#10B981')])

    def create_widgets(self):
        """Create the dialog interface"""
        # Create main notebook
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.create_plot_tab()
        self.create_data_tab()

        # Button frame
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Export", command=self.export,
                   style='Success.TButton').pack(side='right', padx=5)

    def create_plot_tab(self):
        """Create plot export tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Plot Export")

        # Format selection
        format_frame = ttk.LabelFrame(tab, text="Export Format", padding=10)
        format_frame.pack(fill='x', padx=10, pady=10)

        self.format_var = tk.StringVar(value="PNG")
        formats = ["PNG", "JPEG", "SVG", "PDF", "TIFF"]

        for i, fmt in enumerate(formats):
            ttk.Radiobutton(format_frame, text=fmt, variable=self.format_var,
                            value=fmt).grid(row=i // 3, column=i % 3, padx=10, pady=5, sticky='w')

        # Resolution settings
        res_frame = ttk.LabelFrame(tab, text="Resolution", padding=10)
        res_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(res_frame, text="DPI:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.dpi_var = tk.IntVar(value=300)
        ttk.Spinbox(res_frame, from_=72, to=1200, textvariable=self.dpi_var, width=10).grid(row=0, column=1, padx=5,
                                                                                            pady=5)

        ttk.Label(res_frame, text="Width (inches):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.width_var = tk.DoubleVar(value=10)
        ttk.Spinbox(res_frame, from_=4, to=48, increment=0.5,
                    textvariable=self.width_var, width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(res_frame, text="Height (inches):").grid(row=1, column=2, sticky='w', padx=5, pady=5)
        self.height_var = tk.DoubleVar(value=8)
        ttk.Spinbox(res_frame, from_=3, to=36, increment=0.5,
                    textvariable=self.height_var, width=10).grid(row=1, column=3, padx=5, pady=5)

        # Include elements
        elements_frame = ttk.LabelFrame(tab, text="Include Elements", padding=10)
        elements_frame.pack(fill='x', padx=10, pady=10)

        self.include_legend_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(elements_frame, text="Legend", variable=self.include_legend_var).grid(row=0, column=0, padx=5,
                                                                                              pady=5, sticky='w')

        self.include_title_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(elements_frame, text="Title", variable=self.include_title_var).grid(row=0, column=1, padx=5,
                                                                                            pady=5, sticky='w')

        self.include_grid_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(elements_frame, text="Grid", variable=self.include_grid_var).grid(row=0, column=2, padx=5,
                                                                                          pady=5, sticky='w')

        self.include_annotations_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(elements_frame, text="Annotations", variable=self.include_annotations_var).grid(row=1, column=0,
                                                                                                        padx=5, pady=5,
                                                                                                        sticky='w')

        # File selection
        file_frame = ttk.LabelFrame(tab, text="Output File", padding=10)
        file_frame.pack(fill='x', padx=10, pady=10)

        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var).pack(side='left', fill='x', expand=True, padx=5, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_plot_file).pack(side='right', padx=5, pady=5)

    def create_data_tab(self):
        """Create data export tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Data Export")

        # Format selection
        format_frame = ttk.LabelFrame(tab, text="Export Format", padding=10)
        format_frame.pack(fill='x', padx=10, pady=10)

        self.data_format_var = tk.StringVar(value="CSV")
        formats = ["CSV", "Excel", "JSON", "Parquet", "HDF5"]

        for i, fmt in enumerate(formats):
            ttk.Radiobutton(format_frame, text=fmt, variable=self.data_format_var,
                            value=fmt).grid(row=i // 3, column=i % 3, padx=10, pady=5, sticky='w')

        # Series selection
        series_frame = ttk.LabelFrame(tab, text="Series to Export", padding=10)
        series_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Create treeview for series selection
        columns = ('name', 'file', 'x_col', 'y_col')
        self.series_tree = ttk.Treeview(series_frame, columns=columns, show='headings', selectmode='extended')

        # Define headings
        self.series_tree.heading('name', text='Series Name')
        self.series_tree.heading('file', text='Data File')
        self.series_tree.heading('x_col', text='X Column')
        self.series_tree.heading('y_col', text='Y Column')

        # Set column widths
        self.series_tree.column('name', width=120)
        self.series_tree.column('file', width=120)
        self.series_tree.column('x_col', width=80)
        self.series_tree.column('y_col', width=80)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(series_frame, orient='vertical', command=self.series_tree.yview)
        self.series_tree.configure(yscrollcommand=scrollbar.set)

        # Pack components
        self.series_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Populate with series
        for series_id, series in self.plot_manager.series_configs.items():
            file_name = self.plot_manager.loaded_files[series.file_id].filename
            self.series_tree.insert('', 'end', iid=series_id,
                                    values=(series.name, file_name, series.x_column, series.y_column),
                                    tags=('series',))

        # Select all by default
        for series_id in self.plot_manager.series_configs:
            self.series_tree.selection_add(series_id)

        # File selection
        file_frame = ttk.LabelFrame(tab, text="Output File", padding=10)
        file_frame.pack(fill='x', padx=10, pady=10)

        self.data_file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.data_file_path_var).pack(side='left', fill='x', expand=True, padx=5,
                                                                         pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_data_file).pack(side='right', padx=5, pady=5)

    def browse_plot_file(self):
        """Browse for plot export file"""
        file_types = [
            ('PNG files', '*.png'),
            ('JPEG files', '*.jpg;*.jpeg'),
            ('SVG files', '*.svg'),
            ('PDF files', '*.pdf'),
            ('TIFF files', '*.tif;*.tiff'),
            ('All files', '*.*')
        ]

        file_path = filedialog.asksaveasfilename(
            title="Save Plot As",
            defaultextension=".png",
            filetypes=file_types
        )

        if file_path:
            self.file_path_var.set(file_path)

    def browse_data_file(self):
        """Browse for data export file"""
        file_types = [
            ('CSV files', '*.csv'),
            ('Excel files', '*.xlsx'),
            ('JSON files', '*.json'),
            ('Parquet files', '*.parquet'),
            ('HDF5 files', '*.h5;*.hdf5'),
            ('All files', '*.*')
        ]

        file_path = filedialog.asksaveasfilename(
            title="Save Data As",
            defaultextension=".csv",
            filetypes=file_types
        )

        if file_path:
            self.data_file_path_var.set(file_path)

    def export(self):
        """Handle export process"""
        # Determine which tab is active
        if self.notebook.index(self.notebook.select()) == 0:  # Plot export tab
            self.export_plot()
        else:  # Data export tab
            self.export_data()

        self.result = 'export'
        self.dialog.destroy()

    def export_plot(self):
        """Export the plot"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select an output file")
            return

        try:
            # Configure plot based on settings
            fig = self.plot_manager.figure
            fig.set_size_inches(self.width_var.get(), self.height_var.get())
            fig.set_dpi(self.dpi_var.get())

            # Toggle visibility of elements
            self.plot_manager.toggle_legend(self.include_legend_var.get())
            self.plot_manager.toggle_title(self.include_title_var.get())
            self.plot_manager.toggle_grid(self.include_grid_var.get())
            self.plot_manager.toggle_annotations(self.include_annotations_var.get())

            # Save the plot
            fig.savefig(file_path, bbox_inches='tight', dpi=self.dpi_var.get())

            # Restore original visibility
            self.plot_manager.toggle_legend(True)
            self.plot_manager.toggle_title(True)
            self.plot_manager.toggle_grid(True)
            self.plot_manager.toggle_annotations(True)

            messagebox.showinfo("Success", f"Plot exported to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export plot:\n{str(e)}")

    def export_data(self):
        """Export the data"""
        file_path = self.data_file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select an output file")
            return

        selected_series = self.series_tree.selection()
        if not selected_series:
            messagebox.showerror("Error", "Please select at least one series to export")
            return

        try:
            # Collect all selected series data
            all_data = []
            for series_id in selected_series:
                series = self.plot_manager.series_configs[series_id]
                file_data = self.plot_manager.loaded_files[series.file_id]
                data = series.get_data(file_data)

                # Create DataFrame for this series
                df = pd.DataFrame({
                    'series': series.name,
                    'x': data[0],
                    'y': data[1]
                })
                all_data.append(df)

            # Combine all series data
            combined = pd.concat(all_data, ignore_index=True)

            # Export based on selected format
            export_format = self.data_format_var.get().lower()
            if export_format == 'csv':
                combined.to_csv(file_path, index=False)
            elif export_format == 'excel':
                combined.to_excel(file_path, index=False)
            elif export_format == 'json':
                combined.to_json(file_path, orient='records')
            elif export_format == 'parquet':
                combined.to_parquet(file_path)
            elif export_format == 'hdf5':
                combined.to_hdf(file_path, key='data', mode='w')

            messagebox.showinfo("Success", f"Data exported to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data:\n{str(e)}")

    def cancel(self):
        """Cancel without exporting"""
        self.result = 'cancel'
        self.dialog.destroy()

from ui.vacuum_analysis_dialog import VacuumAnalysisDialog as _CanonicalVacuumAnalysisDialog

class VacuumAnalysisDialog(_CanonicalVacuumAnalysisDialog):
    """Deprecated shim that forwards to ui.vacuum_analysis_dialog.VacuumAnalysisDialog.

    This consolidates duplicate Vacuum UI by preferring the dedicated dialog.
    """
    pass

    def export_results(self):
        """Export all analysis results"""
        filename = filedialog.asksaveasfilename(
            title="Export Vacuum Analysis Results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, "w") as f:
                    f.write("VACUUM DATA ANALYSIS RESULTS\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 70 + "\n\n")

                    # Base pressure
                    if self.base_text.get(1.0, tk.END).strip():
                        f.write("BASE PRESSURE ANALYSIS\n")
                        f.write("-" * 70 + "\n")
                        f.write(self.base_text.get(1.0, tk.END))
                        f.write("\n\n")

                    # Leak detection
                    if self.leak_text.get(1.0, tk.END).strip():
                        f.write("LEAK DETECTION RESULTS\n")
                        f.write("-" * 70 + "\n")
                        f.write(self.leak_text.get(1.0, tk.END))
                        f.write("\n\n")

                    # Pump-down analysis
                    if self.pump_text.get(1.0, tk.END).strip():
                        f.write("PUMP-DOWN ANALYSIS\n")
                        f.write("-" * 70 + "\n")
                        f.write(self.pump_text.get(1.0, tk.END))
                        f.write("\n\n")

                messagebox.showinfo("Success", f"Analysis results exported to:\n{filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results:\n{str(e)}")


class DataSelectorDialog:
    """Dialog for advanced data selection from non-standard layouts"""

    def __init__(
            self,
            parent,
            file_data: FileData,
            on_data_selected: Optional[Callable] = None
    ):
        self.parent = parent
        self.file_data = file_data
        self.on_data_selected = on_data_selected
        self.result = None

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Data Selection: {file_data.filename}")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create UI
        self.create_widgets()

        # Center dialog
        self._center_dialog()

    def _center_dialog(self):
        """Center dialog on screen"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def create_widgets(self):
        """Create dialog widgets"""
        # Preview section
        preview_frame = ctk.CTkFrame(self.dialog)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create treeview for data display
        tree_frame = ttk.Frame(preview_frame)
        tree_frame.pack(fill="both", expand=True)

        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical")
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Treeview
        columns = list(self.file_data.data.columns)
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            yscrollcommand=v_scroll.set,
            xscrollcommand=h_scroll.set
        )

        # Configure scrollbars
        v_scroll.config(command=self.tree.yview)
        h_scroll.config(command=self.tree.xview)

        # Pack components
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Configure columns
        self.tree.heading("#0", text="Index")
        self.tree.column("#0", width=60)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)

        # Add data (limited to first 1000 rows)
        df_preview = self.file_data.data.head(1000)
        for idx, row in df_preview.iterrows():
            self.tree.insert("", "end", text=str(idx), values=list(row))

        # Selection controls
        control_frame = ctk.CTkFrame(self.dialog)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Header row selection
        ctk.CTkLabel(control_frame, text="Header Row:").grid(row=0, column=0, padx=5, pady=5)
        self.header_row_var = tk.IntVar(value=0)
        self.header_row_spin = ctk.CTkEntry(control_frame, textvariable=self.header_row_var, width=50)
        self.header_row_spin.grid(row=0, column=1, padx=5, pady=5)

        # Auto-detect button
        ctk.CTkButton(
            control_frame,
            text="Auto-Detect Headers",
            command=self.auto_detect_headers
        ).grid(row=0, column=2, padx=10, pady=5)

        # Data range
        ctk.CTkLabel(control_frame, text="Start Row:").grid(row=1, column=0, padx=5, pady=5)
        self.start_row_var = tk.IntVar(value=1)
        self.start_row_spin = ctk.CTkEntry(control_frame, textvariable=self.start_row_var, width=50)
        self.start_row_spin.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(control_frame, text="End Row:").grid(row=2, column=0, padx=5, pady=5)
        self.end_row_var = tk.IntVar(value=len(self.file_data.data))
        self.end_row_spin = ctk.CTkEntry(control_frame, textvariable=self.end_row_var, width=50)
        self.end_row_spin.grid(row=2, column=1, padx=5, pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(
            button_frame,
            text="Apply Selection",
            command=self.apply_selection,
            width=120
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy,
            width=100
        ).pack(side="right", padx=5)

    def auto_detect_headers(self):
        """Auto-detect header row"""
        # Use utility function to find header row
        header_row = detect_datetime_column(self.file_data.data)
        self.header_row_var.set(header_row)

        # Update start row
        self.start_row_var.set(header_row + 1)

    def apply_selection(self):
        """Apply data selection"""
        selection_info = {
            "header_row": self.header_row_var.get(),
            "start_row": self.start_row_var.get(),
            "end_row": self.end_row_var.get()
        }

        if self.on_data_selected:
            self.on_data_selected(selection_info)

        self.dialog.destroy()
