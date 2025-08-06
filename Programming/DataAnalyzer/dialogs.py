#!/usr/bin/env python3
"""
dialogs.py - Dialog windows for Excel Data Plotter
Contains all dialog classes for configuration, analysis, and data selection
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import customtkinter as ctk
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from scipy.signal import savgol_filter
from sklearn.linear_model import LinearRegression
from constants import ColorPalette, MissingDataMethods, TrendTypes
from models import SeriesConfig, AnnotationConfig
from ui_components import Tooltip, CollapsiblePanel
from analysis_tools import DataAnalysisTools, VacuumAnalysisTools
from utils import detect_datetime_column, validate_data_range


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
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

    def setup_styles(self):
        """Setup modern styles"""
        style = ttk.Style()

        # Configure modern notebook style
        style.configure('Modern.TNotebook', tabposition='n', borderwidth=0)
        style.configure('Modern.TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 10))

        # Modern frames
        style.configure('Card.TFrame', relief='flat', borderwidth=1)
        style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))
        style.configure('Modern.TButton', font=('Segoe UI', 10))

    def analyze_data(self):
        """Analyze data to provide smart defaults"""
        try:
            start_idx = self.series.start_index
            end_idx = self.series.end_index or len(self.file_data.df)
            data_slice = self.file_data.df.iloc[start_idx:end_idx]

            # Check if X column is datetime
            self.series._datetime_detected = False
            if self.series.x_column != 'Index':
                x_data = data_slice[self.series.x_column]
                self.series._datetime_detected = self.is_datetime_data(x_data)

            # Initialize as empty dict
            self.series._data_stats = {}

            # Calculate Y data statistics
            if self.series.y_column in data_slice.columns:
                y_data = data_slice[self.series.y_column].dropna()
                if len(y_data) > 0:
                    self.series._data_stats = {
                        'min': y_data.min(),
                        'max': y_data.max(),
                        'mean': y_data.mean(),
                        'std': y_data.std(),
                        'count': len(y_data),
                        'missing': len(data_slice) - len(y_data)
                    }
        except Exception as e:
            print(f"Data analysis error: {e}")
            self.series._datetime_detected = False
            self.series._data_stats = {}

    def is_datetime_data(self, data):
        """Check if data is datetime"""
        if pd.api.types.is_datetime64_any_dtype(data):
            return True

        # Try to detect datetime strings
        try:
            sample = data.dropna().head(10)
            if len(sample) > 0:
                pd.to_datetime(sample, infer_datetime_format=True)
                return True
        except:
            pass

        return False

    def create_widgets(self):
        # Header with series info
        self.create_header()

        # Main content area with cards
        main_frame = ttk.Frame(self.dialog, style='Card.TFrame')
        main_frame.pack(fill='both', expand=True, padx=15, pady=10)

        # Create two columns
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', padx=(10, 0))

        # Create card-based layout in left column
        self.create_card_layout(left_frame)

        # Add preview panel in right column
        self.create_preview_panel(right_frame)

        # Action buttons
        self.create_action_buttons()

    def create_preview_panel(self, parent):
        """Create live preview panel"""
        preview_frame = ttk.LabelFrame(parent, text="Live Preview", padding=10)
        preview_frame.pack(fill='both', expand=True)

        # Placeholder for preview implementation
        ttk.Label(preview_frame, text="Preview will be shown here").pack(expand=True)

    def create_header(self):
        """Create modern header with series info"""
        header_frame = tk.Frame(self.dialog, bg='#2c3e50', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        # Series name and file info
        info_frame = tk.Frame(header_frame, bg='#2c3e50')
        info_frame.pack(expand=True)

        tk.Label(info_frame, text=self.series.name,
                 font=('Segoe UI', 16, 'bold'),
                 fg='white', bg='#2c3e50').pack(pady=(15, 5))

        tk.Label(info_frame,
                 text=f"{self.file_data.filename} | {self.series.x_column} vs {self.series.y_column}",
                 font=('Segoe UI', 10),
                 fg='#ecf0f1', bg='#2c3e50').pack()

        if hasattr(self.series, '_data_stats') and self.series._data_stats:
            stats = self.series._data_stats
            tk.Label(info_frame,
                     text=f"{stats['count']:,} points | {stats['missing']} missing | Range: {stats['min']:.2f} to {stats['max']:.2f}",
                     font=('Segoe UI', 9),
                     fg='#bdc3c7', bg='#2c3e50').pack()

    def create_card_layout(self, parent):
        """Create card-based layout for settings"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Create cards
        self.create_data_range_card()  # New card for data range
        self.create_appearance_card()
        self.create_data_handling_card()
        self.create_analysis_card()
        self.create_display_options_card()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_data_range_card(self):
        """Create data range selection card"""
        card = self.create_card(self.scrollable_frame, "📊 Data Range", expanded=True)

        # Current data info
        info_frame = ttk.Frame(card)
        info_frame.pack(fill='x', pady=5)

        # Get actual data bounds
        max_rows = len(self.file_data.df)

        ttk.Label(info_frame, text=f"Total rows in file: {max_rows:,}",
                  font=('Segoe UI', 10)).pack(anchor='w')

        # Range selection
        range_frame = ttk.Frame(card)
        range_frame.pack(fill='x', pady=10)

        ttk.Label(range_frame, text="Start Index:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.start_var = tk.IntVar(value=self.series.start_index)
        self.start_spin = ttk.Spinbox(range_frame, from_=0, to=max_rows - 1,
                                      textvariable=self.start_var, width=15,
                                      command=self.on_range_changed)
        self.start_spin.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(range_frame, text="End Index:").grid(row=0, column=2, sticky='w', padx=(20, 5), pady=5)
        self.end_var = tk.IntVar(value=self.series.end_index or max_rows)
        self.end_spin = ttk.Spinbox(range_frame, from_=1, to=max_rows,
                                    textvariable=self.end_var, width=15,
                                    command=self.on_range_changed)
        self.end_spin.grid(row=0, column=3, padx=5, pady=5)

        # Quick range buttons
        quick_frame = ttk.Frame(card)
        quick_frame.pack(fill='x', pady=5)

        ttk.Label(quick_frame, text="Quick Select:").pack(side='left', padx=5)

        ttk.Button(quick_frame, text="First 100",
                   command=lambda: self.set_range(0, 100)).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="First 1000",
                   command=lambda: self.set_range(0, 1000)).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="Last 100",
                   command=lambda: self.set_range(max_rows - 100, max_rows)).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="Last 1000",
                   command=lambda: self.set_range(max_rows - 1000, max_rows)).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="All Data",
                   command=lambda: self.set_range(0, max_rows)).pack(side='left', padx=2)

        # Selected range info
        self.range_info_label = ttk.Label(card, text="", font=('Segoe UI', 9))
        self.range_info_label.pack(pady=5)
        self.update_range_info()

    def set_range(self, start, end):
        """Set data range"""
        max_rows = len(self.file_data.df)
        self.start_var.set(max(0, start))
        self.end_var.set(min(max_rows, end))
        self.on_range_changed()

    def on_range_changed(self):
        """Handle range change"""
        self.update_range_info()

    def update_range_info(self):
        """Update range information display"""
        start = self.start_var.get()
        end = self.end_var.get()
        count = end - start
        self.range_info_label.config(text=f"Selected: {count:,} rows (indices {start} to {end - 1})")

    def create_appearance_card(self):
        """Create appearance settings card"""
        card = self.create_card(self.scrollable_frame, "🎨 Appearance", expanded=True)

        # Color selection with preview
        color_frame = ttk.Frame(card)
        color_frame.pack(fill='x', pady=5)

        ttk.Label(color_frame, text="Color:", style='Header.TLabel').pack(side='left', padx=(0, 10))

        self.color_var = tk.StringVar(value=self.series.color or '#3498db')
        self.color_preview = tk.Frame(color_frame, bg=self.color_var.get(),
                                      width=30, height=30, relief='solid', borderwidth=1)
        self.color_preview.pack(side='left', padx=5)

        ttk.Button(color_frame, text="Choose",
                   command=self.choose_color, width=10).pack(side='left', padx=5)

        # Quick color palette
        palette_frame = ttk.Frame(card)
        palette_frame.pack(fill='x', pady=5)

        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6',
                  '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#d35400']

        for color in colors:
            btn = tk.Frame(palette_frame, bg=color, width=25, height=25,
                           relief='raised', borderwidth=1, cursor='hand2')
            btn.pack(side='left', padx=2)
            btn.bind("<Button-1>", lambda e, c=color: self.set_color(c))

        # Line style with preview
        style_frame = ttk.Frame(card)
        style_frame.pack(fill='x', pady=10)

        ttk.Label(style_frame, text="Style:", style='Header.TLabel').grid(row=0, column=0, sticky='w')

        # Style options with visual representation
        self.style_var = tk.StringVar(value=self.series.line_style)
        styles = [
            ('-', 'Solid ——————'),
            ('--', 'Dashed — — — —'),
            (':', 'Dotted · · · · ·'),
            ('-.', 'Dash-dot — · — ·')
        ]

        style_combo = ttk.Combobox(style_frame, textvariable=self.style_var,
                                   values=[desc for _, desc in styles],
                                   state='readonly', width=20)
        style_combo.set(dict(styles).get(self.series.line_style, styles[0][1]))
        style_combo.grid(row=0, column=1, padx=10)

        # Size controls with live preview
        size_frame = ttk.Frame(card)
        size_frame.pack(fill='x', pady=5)

        # Line width
        ttk.Label(size_frame, text="Line Width:").grid(row=0, column=0, sticky='w', pady=5)
        self.width_var = tk.DoubleVar(value=self.series.line_width)
        width_scale = ttk.Scale(size_frame, from_=0.5, to=6, variable=self.width_var,
                                orient='horizontal', length=200,
                                command=lambda v: self.on_width_change())
        width_scale.grid(row=0, column=1, padx=10, pady=5)
        self.width_label = ttk.Label(size_frame, text=f"{self.width_var.get():.1f}")
        self.width_label.grid(row=0, column=2, pady=5)

        # Transparency
        ttk.Label(size_frame, text="Transparency:").grid(row=1, column=0, sticky='w', pady=5)
        self.alpha_var = tk.DoubleVar(value=self.series.alpha)
        alpha_scale = ttk.Scale(size_frame, from_=0.1, to=1.0, variable=self.alpha_var,
                                orient='horizontal', length=200,
                                command=lambda v: self.on_alpha_change())
        alpha_scale.grid(row=1, column=1, padx=10, pady=5)
        self.alpha_label = ttk.Label(size_frame, text=f"{int(self.alpha_var.get() * 100)}%")
        self.alpha_label.grid(row=1, column=2, pady=5)

        # Advanced options
        adv_frame = ttk.LabelFrame(card, text="Advanced Style", padding=10)
        adv_frame.pack(fill='x', pady=10)

        self.fill_var = tk.BooleanVar(value=self.series.fill_area)
        fill_check = ttk.Checkbutton(adv_frame, text="Fill area under curve",
                                     variable=self.fill_var)
        fill_check.pack(anchor='w')

        self.gradient_var = tk.BooleanVar(value=getattr(self.series, 'gradient_fill', False))
        ttk.Checkbutton(adv_frame, text="Use gradient fill",
                        variable=self.gradient_var).pack(anchor='w')

    def on_width_change(self):
        """Handle width change"""
        self.width_label.config(text=f"{self.width_var.get():.1f}")

    def on_alpha_change(self):
        """Handle alpha change"""
        self.alpha_label.config(text=f"{int(self.alpha_var.get() * 100)}%")

    def create_data_handling_card(self):
        """Create data handling settings card"""
        card = self.create_card(self.scrollable_frame, "📊 Data Handling", expanded=True)

        # Missing data handling
        missing_frame = ttk.LabelFrame(card, text="Missing Data", padding=10)
        missing_frame.pack(fill='x', pady=5)

        self.missing_var = tk.StringVar(value=self.series.missing_data_method)
        methods = [
            ('interpolate', 'Interpolate', 'Fill gaps with interpolated values'),
            ('drop', 'Remove', 'Remove missing data points'),
            ('fill_zero', 'Zero', 'Replace with zero'),
            ('forward_fill', 'Forward Fill', 'Use previous valid value')
        ]

        for value, text, tooltip in methods:
            rb = ttk.Radiobutton(missing_frame, text=text, variable=self.missing_var, value=value)
            rb.pack(anchor='w', pady=2)
            self.create_tooltip(rb, tooltip)

        # Date/Time handling (if applicable)
        if hasattr(self.series, '_datetime_detected') and self.series._datetime_detected:
            dt_frame = ttk.LabelFrame(card, text="Date/Time Format", padding=10)
            dt_frame.pack(fill='x', pady=5)

            self.dt_format_var = tk.StringVar(value=self.series.datetime_format)

            ttk.Radiobutton(dt_frame, text="Auto-detect format",
                            variable=self.dt_format_var, value='auto').pack(anchor='w')

            common_formats = [
                ('%Y-%m-%d', 'Date only (2024-03-15)'),
                ('%Y-%m-%d %H:%M:%S', 'Date & Time (2024-03-15 14:30:00)'),
                ('%d/%m/%Y', 'DD/MM/YYYY (15/03/2024)'),
                ('%m/%d/%Y', 'MM/DD/YYYY (03/15/2024)'),
                ('%Y-%m-%d %H:%M', 'Date & Time without seconds')
            ]

            for fmt, desc in common_formats:
                ttk.Radiobutton(dt_frame, text=desc,
                                variable=self.dt_format_var, value=fmt).pack(anchor='w')

            # Custom format
            custom_frame = ttk.Frame(dt_frame)
            custom_frame.pack(fill='x', pady=5)

            ttk.Radiobutton(custom_frame, text="Custom:",
                            variable=self.dt_format_var, value='custom').pack(side='left')

            self.custom_dt_var = tk.StringVar(value=self.series.custom_datetime_format)
            ttk.Entry(custom_frame, textvariable=self.custom_dt_var, width=25).pack(side='left', padx=5)

        # Outlier handling
        outlier_frame = ttk.LabelFrame(card, text="Outlier Detection", padding=10)
        outlier_frame.pack(fill='x', pady=5)

        self.outlier_var = tk.StringVar(value=self.series.outlier_method)

        ttk.Radiobutton(outlier_frame, text="Keep all data",
                        variable=self.outlier_var, value='keep').pack(anchor='w')
        ttk.Radiobutton(outlier_frame, text="Remove outliers",
                        variable=self.outlier_var, value='remove').pack(anchor='w')
        ttk.Radiobutton(outlier_frame, text="Cap outliers",
                        variable=self.outlier_var, value='cap').pack(anchor='w')

        # Threshold setting
        threshold_frame = ttk.Frame(outlier_frame)
        threshold_frame.pack(fill='x', pady=5)

        ttk.Label(threshold_frame, text="Threshold (std dev):").pack(side='left')
        self.threshold_var = tk.DoubleVar(value=self.series.outlier_threshold)
        ttk.Spinbox(threshold_frame, from_=1, to=5, increment=0.5,
                    textvariable=self.threshold_var, width=10).pack(side='left', padx=5)

        # Smoothing
        smooth_frame = ttk.LabelFrame(card, text="Data Smoothing", padding=10)
        smooth_frame.pack(fill='x', pady=5)

        ttk.Label(smooth_frame, text="Smoothing Level:").pack(anchor='w')

        self.smooth_var = tk.IntVar(value=self.series.smooth_factor)
        smooth_scale = ttk.Scale(smooth_frame, from_=0, to=100, variable=self.smooth_var,
                                 orient='horizontal', length=300)
        smooth_scale.pack(fill='x', pady=5)

        # Labels for smoothing scale
        label_frame = ttk.Frame(smooth_frame)
        label_frame.pack(fill='x')
        ttk.Label(label_frame, text="None", font=('Segoe UI', 8)).pack(side='left')
        ttk.Label(label_frame, text="Heavy", font=('Segoe UI', 8)).pack(side='right')

    def create_analysis_card(self):
        """Create analysis settings card"""
        card = self.create_card(self.scrollable_frame, "📈 Analysis", expanded=False)

        # Initialize trend-related variables
        self.poly_degree_var = None
        self.ma_window_var = None

        # Trend analysis
        trend_frame = ttk.LabelFrame(card, text="Trend Analysis", padding=10)
        trend_frame.pack(fill='x', pady=5)

        self.show_trend_var = tk.BooleanVar(value=self.series.show_trendline)
        ttk.Checkbutton(trend_frame, text="Show trend line",
                        variable=self.show_trend_var,
                        command=self.toggle_trend_options).pack(anchor='w')

        self.trend_options_frame = ttk.Frame(trend_frame)
        self.trend_options_frame.pack(fill='x', pady=5)

        ttk.Label(self.trend_options_frame, text="Type:").grid(row=0, column=0, sticky='w', padx=5)
        self.trend_type_var = tk.StringVar(value=self.series.trend_type)
        trend_combo = ttk.Combobox(self.trend_options_frame, textvariable=self.trend_type_var,
                                   values=['linear', 'polynomial', 'exponential', 'moving_average'],
                                   state='readonly', width=15)
        trend_combo.grid(row=0, column=1, padx=5)
        trend_combo.bind('<<ComboboxSelected>>', self.on_trend_type_changed)

        # Dynamic parameters based on trend type
        self.trend_param_frame = ttk.Frame(self.trend_options_frame)
        self.trend_param_frame.grid(row=1, column=0, columnspan=2, pady=5)

        self.update_trend_params()
        self.toggle_trend_options()

        # Peak detection
        peak_frame = ttk.LabelFrame(card, text="Peak Detection", padding=10)
        peak_frame.pack(fill='x', pady=5)

        self.show_peaks_var = tk.BooleanVar(value=self.series.show_peaks)
        ttk.Checkbutton(peak_frame, text="Mark peaks and valleys",
                        variable=self.show_peaks_var).pack(anchor='w')

        prom_frame = ttk.Frame(peak_frame)
        prom_frame.pack(fill='x', pady=5)

        ttk.Label(prom_frame, text="Sensitivity:").pack(side='left')
        self.peak_prom_var = tk.DoubleVar(value=self.series.peak_prominence)
        prom_scale = ttk.Scale(prom_frame, from_=0.01, to=0.5, variable=self.peak_prom_var,
                               orient='horizontal', length=200)
        prom_scale.pack(side='left', padx=10)

        # Statistics overlay
        stats_frame = ttk.LabelFrame(card, text="Statistics Display", padding=10)
        stats_frame.pack(fill='x', pady=5)

        self.show_stats_var = tk.BooleanVar(value=self.series.show_statistics)
        ttk.Checkbutton(stats_frame, text="Show statistics box on plot",
                        variable=self.show_stats_var).pack(anchor='w')

    def create_display_options_card(self):
        """Create display options card"""
        card = self.create_card(self.scrollable_frame, "👁️ Display Options", expanded=False)

        # Basic visibility
        basic_frame = ttk.Frame(card)
        basic_frame.pack(fill='x', pady=5)

        self.visible_var = tk.BooleanVar(value=self.series.visible)
        ttk.Checkbutton(basic_frame, text="Visible", variable=self.visible_var,
                        style='Modern.TCheckbutton').pack(side='left', padx=10)

        self.legend_var = tk.BooleanVar(value=self.series.show_in_legend)
        ttk.Checkbutton(basic_frame, text="Show in legend", variable=self.legend_var,
                        style='Modern.TCheckbutton').pack(side='left', padx=10)

        # Legend customization
        legend_frame = ttk.Frame(card)
        legend_frame.pack(fill='x', pady=5)

        ttk.Label(legend_frame, text="Legend label:").pack(side='left', padx=5)
        self.legend_label_var = tk.StringVar(value=self.series.legend_label)
        ttk.Entry(legend_frame, textvariable=self.legend_label_var, width=30).pack(side='left', padx=5)

        # Y-axis selection
        axis_frame = ttk.Frame(card)
        axis_frame.pack(fill='x', pady=5)

        ttk.Label(axis_frame, text="Y-axis:").pack(side='left', padx=5)
        self.y_axis_var = tk.StringVar(value=self.series.y_axis)
        ttk.Radiobutton(axis_frame, text="Left", variable=self.y_axis_var,
                        value='left').pack(side='left', padx=5)
        ttk.Radiobutton(axis_frame, text="Right", variable=self.y_axis_var,
                        value='right').pack(side='left', padx=5)

        # Vacuum-specific highlighting options
        highlight_frame = ttk.LabelFrame(card, text="Auto-highlighting", padding=10)
        highlight_frame.pack(fill='x', pady=10)

        self.highlight_base_var = tk.BooleanVar(value=getattr(self.series, 'highlight_base_pressure', False))
        self.highlight_spikes_var = tk.BooleanVar(value=getattr(self.series, 'highlight_spikes', False))
        self.highlight_outliers_var = tk.BooleanVar(value=getattr(self.series, 'highlight_outliers', False))

        ttk.Checkbutton(highlight_frame, text="Highlight base pressure level",
                        variable=self.highlight_base_var).pack(anchor='w')
        ttk.Checkbutton(highlight_frame, text="Highlight pressure spikes",
                        variable=self.highlight_spikes_var).pack(anchor='w')
        ttk.Checkbutton(highlight_frame, text="Highlight outliers",
                        variable=self.highlight_outliers_var).pack(anchor='w')

    def create_card(self, parent, title, expanded=True):
        """Create a modern card UI element"""
        # Card container
        card_container = ttk.Frame(parent)
        card_container.pack(fill='x', pady=5)

        # Card frame with shadow effect
        card = tk.Frame(card_container, bg='white', relief='solid', borderwidth=1)
        card.pack(fill='x', padx=5, pady=2)

        # Header
        header = tk.Frame(card, bg='#ecf0f1', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)

        # Title with expand/collapse button
        title_frame = tk.Frame(header, bg='#ecf0f1')
        title_frame.pack(side='left', fill='both', expand=True)

        self.expand_icon = tk.Label(title_frame, text='▼' if expanded else '▶',
                                    font=('Segoe UI', 10), bg='#ecf0f1', cursor='hand2')
        self.expand_icon.pack(side='left', padx=(10, 5), pady=10)

        tk.Label(title_frame, text=title, font=('Segoe UI', 12, 'bold'),
                 bg='#ecf0f1').pack(side='left', pady=10)

        # Content frame
        content = ttk.Frame(card)
        if expanded:
            content.pack(fill='x', padx=15, pady=15)

        # Bind expand/collapse
        def toggle_expand(event=None):
            if content.winfo_viewable():
                content.pack_forget()
                self.expand_icon.config(text='▶')
            else:
                content.pack(fill='x', padx=15, pady=15)
                self.expand_icon.config(text='▼')

        header.bind("<Button-1>", toggle_expand)
        self.expand_icon.bind("<Button-1>", toggle_expand)

        return content

    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""

        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            label = tk.Label(tooltip, text=text, background="#333333",
                             foreground="white", relief='solid', borderwidth=1,
                             font=('Segoe UI', 9))
            label.pack()

            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def create_action_buttons(self):
        """Create modern action buttons"""
        btn_frame = tk.Frame(self.dialog, bg='#ecf0f1')
        btn_frame.pack(fill='x', pady=10)

        # Apply button
        apply_btn = tk.Button(btn_frame, text="Apply Changes",
                              command=self.apply_changes,
                              bg='#3498db', fg='white',
                              font=('Segoe UI', 11, 'bold'),
                              padx=20, pady=8,
                              relief='flat', cursor='hand2')
        apply_btn.pack(side='right', padx=10)

        # Cancel button
        cancel_btn = tk.Button(btn_frame, text="Cancel",
                               command=self.cancel,
                               bg='#95a5a6', fg='white',
                               font=('Segoe UI', 11),
                               padx=20, pady=8,
                               relief='flat', cursor='hand2')
        cancel_btn.pack(side='right', padx=5)

        # Reset button
        reset_btn = tk.Button(btn_frame, text="Reset to Defaults",
                              command=self.reset_defaults,
                              bg='#e74c3c', fg='white',
                              font=('Segoe UI', 10),
                              padx=15, pady=8,
                              relief='flat', cursor='hand2')
        reset_btn.pack(side='left', padx=10)

    def choose_color(self):
        """Choose color with modern color picker"""
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
            self.set_color(color[1])

    def set_color(self, color):
        """Set the selected color"""
        self.color_var.set(color)
        self.color_preview.config(bg=color)

    def toggle_trend_options(self):
        """Toggle trend options visibility"""
        if self.show_trend_var.get():
            self.trend_options_frame.pack(fill='x', pady=5)
        else:
            self.trend_options_frame.pack_forget()

    def on_trend_type_changed(self, event=None):
        """Update trend parameters based on type"""
        self.update_trend_params()

    def update_trend_params(self):
        """Update trend parameter inputs based on selected type"""
        # Clear existing parameters
        for widget in self.trend_param_frame.winfo_children():
            widget.destroy()

        trend_type = self.trend_type_var.get()

        if trend_type == 'polynomial':
            ttk.Label(self.trend_param_frame, text="Degree:").pack(side='left', padx=5)
            self.poly_degree_var = tk.IntVar(value=self.series.trend_params.get('degree', 2))
            ttk.Spinbox(self.trend_param_frame, from_=1, to=10,
                        textvariable=self.poly_degree_var, width=10).pack(side='left')

        elif trend_type == 'moving_average':
            ttk.Label(self.trend_param_frame, text="Window:").pack(side='left', padx=5)
            self.ma_window_var = tk.IntVar(value=self.series.trend_params.get('window', 20))
            ttk.Spinbox(self.trend_param_frame, from_=5, to=100,
                        textvariable=self.ma_window_var, width=10).pack(side='left')

    def apply_changes(self):
        """Apply all changes to series configuration"""
        try:
            # Data range
            self.series.start_index = self.start_var.get()
            self.series.end_index = self.end_var.get()

            # Basic settings
            self.series.color = self.color_var.get()

            # Parse line style
            style_map = {
                'Solid ——————': '-',
                'Dashed — — — —': '--',
                'Dotted · · · · ·': ':',
                'Dash-dot — · — ·': '-.'
            }
            self.series.line_style = style_map.get(self.style_var.get(), '-')

            # Appearance
            self.series.line_width = self.width_var.get()
            self.series.alpha = self.alpha_var.get()
            self.series.fill_area = self.fill_var.get()
            self.series.gradient_fill = self.gradient_var.get()

            # Data handling
            self.series.missing_data_method = self.missing_var.get()
            self.series.outlier_method = self.outlier_var.get()
            self.series.outlier_threshold = self.threshold_var.get()
            self.series.smooth_factor = self.smooth_var.get()

            # DateTime handling
            if hasattr(self, 'dt_format_var'):
                self.series.datetime_format = self.dt_format_var.get()
                if self.series.datetime_format == 'custom':
                    self.series.custom_datetime_format = self.custom_dt_var.get()

            # Analysis
            self.series.show_peaks = self.show_peaks_var.get()
            self.series.peak_prominence = self.peak_prom_var.get()
            self.series.show_statistics = self.show_stats_var.get()

            # Display options
            self.series.visible = self.visible_var.get()
            self.series.show_in_legend = self.legend_var.get()
            self.series.legend_label = self.legend_label_var.get()
            self.series.y_axis = self.y_axis_var.get()

            # Vacuum-specific highlighting
            self.series.highlight_base_pressure = self.highlight_base_var.get() if hasattr(self,
                                                                                           'highlight_base_var') else False
            self.series.highlight_spikes = self.highlight_spikes_var.get() if hasattr(self,
                                                                                      'highlight_spikes_var') else False
            self.series.highlight_outliers = self.highlight_outliers_var.get() if hasattr(self,
                                                                                          'highlight_outliers_var') else False

            self.result = 'apply'
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply changes:\n{str(e)}")

    def cancel(self):
        """Cancel without applying changes"""
        self.result = 'cancel'
        self.dialog.destroy()

    def reset_defaults(self):
        """Reset to default values"""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to defaults?"):
            # Reset all variables to defaults
            self.color_var.set('#3498db')
            self.set_color('#3498db')
            self.style_var.set('Solid ——————')
            self.width_var.set(2.5)
            self.alpha_var.set(0.9)
            self.fill_var.set(False)
            self.gradient_var.set(False)

            self.missing_var.set('interpolate')
            self.outlier_var.set('keep')
            self.threshold_var.set(3.0)
            self.smooth_var.set(0)

            self.show_trend_var.set(False)
            self.show_peaks_var.set(False)
            self.show_stats_var.set(False)

            self.visible_var.set(True)
            self.legend_var.set(True)
            self.y_axis_var.set('left')


class VacuumAnalysisDialog:
    """
    Dialog for vacuum-specific data analysis tools
    Provides specialized analysis for vacuum pressure data
    """

    def __init__(self, parent, series_data, all_series, loaded_files):
        """
        Initialize vacuum analysis dialog

        Args:
            parent: Parent window
            series_data: Current series data
            all_series: Dictionary of all series
            loaded_files: Dictionary of loaded files
        """
        self.parent = parent
        self.series_data = series_data
        self.all_series = all_series
        self.loaded_files = loaded_files
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Vacuum Data Analysis Tools")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

    def create_widgets(self):
        # Create notebook for different analysis categories
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Base pressure analysis tab
        self.create_base_pressure_tab(notebook)

        # Noise analysis tab
        self.create_noise_analysis_tab(notebook)

        # Spike detection tab
        self.create_spike_detection_tab(notebook)

        # Leak rate analysis tab
        self.create_leak_rate_tab(notebook)

        # Pump-down analysis tab
        self.create_pumpdown_tab(notebook)

        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(btn_frame, text="Close", command=self.close).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Export Results", command=self.export_results).pack(side='right', padx=5)

    def create_base_pressure_tab(self, notebook):
        """Create base pressure analysis tab"""
        base_frame = ttk.Frame(notebook)
        notebook.add(base_frame, text='🎯 Base Pressure')

        # Series selection
        select_frame = ttk.LabelFrame(base_frame, text="Select Series", padding=10)
        select_frame.pack(fill='x', padx=5, pady=5)

        self.base_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(select_frame, textvariable=self.base_series_var,
                     values=series_options, state='readonly', width=40).pack(pady=5)

        # Window size setting
        window_frame = ttk.Frame(select_frame)
        window_frame.pack(fill='x', pady=5)

        ttk.Label(window_frame, text="Window Size (minutes):").pack(side='left', padx=5)
        self.window_size_var = tk.IntVar(value=10)
        ttk.Spinbox(window_frame, from_=1, to=60, textvariable=self.window_size_var, width=10).pack(side='left', padx=5)

        ttk.Button(select_frame, text="Calculate Base Pressure",
                   command=self.calculate_base_pressure).pack(pady=5)

        # Results display
        results_frame = ttk.LabelFrame(base_frame, text="Analysis Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create text widget for results
        self.base_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10))
        base_scroll = ttk.Scrollbar(results_frame, command=self.base_text.yview)
        self.base_text.config(yscrollcommand=base_scroll.set)

        self.base_text.pack(side='left', fill='both', expand=True)
        base_scroll.pack(side='right', fill='y')

        # Visualization frame
        viz_frame = ttk.LabelFrame(base_frame, text="Visualization", padding=10)
        viz_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(viz_frame, text="Add Base Pressure Line to Plot",
                   command=self.add_base_pressure_line).pack(pady=5)

    def create_noise_analysis_tab(self, notebook):
        """Create noise analysis tab"""
        noise_frame = ttk.Frame(notebook)
        notebook.add(noise_frame, text='📊 Noise Analysis')

        # Configuration
        config_frame = ttk.LabelFrame(noise_frame, text="Noise Analysis Settings", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)

        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.noise_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.noise_series_var,
                     values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)

        # Sample rate
        ttk.Label(config_frame, text="Sample Rate (Hz):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.sample_rate_var = tk.DoubleVar(value=1.0)
        ttk.Entry(config_frame, textvariable=self.sample_rate_var, width=15).grid(row=1, column=1, sticky='w', padx=5,
                                                                                  pady=5)

        ttk.Button(config_frame, text="Analyze Noise",
                   command=self.analyze_noise).grid(row=2, column=1, pady=10)

        # Results
        results_frame = ttk.LabelFrame(noise_frame, text="Noise Metrics", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.noise_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10), height=10)
        noise_scroll = ttk.Scrollbar(results_frame, command=self.noise_text.yview)
        self.noise_text.config(yscrollcommand=noise_scroll.set)

        self.noise_text.pack(side='left', fill='both', expand=True)
        noise_scroll.pack(side='right', fill='y')

        # Spectrum plot frame
        spectrum_frame = ttk.LabelFrame(noise_frame, text="Frequency Spectrum", padding=10)
        spectrum_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Placeholder for spectrum plot
        ttk.Label(spectrum_frame, text="Spectrum plot will be shown here").pack(expand=True)

    def create_spike_detection_tab(self, notebook):
        """Create spike detection tab"""
        spike_frame = ttk.Frame(notebook)
        notebook.add(spike_frame, text='⚡ Spike Detection')

        # Configuration
        config_frame = ttk.LabelFrame(spike_frame, text="Spike Detection Settings", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)

        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.spike_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.spike_series_var,
                     values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)

        # Threshold setting
        ttk.Label(config_frame, text="Threshold (σ):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.spike_threshold_var = tk.DoubleVar(value=3.0)
        ttk.Scale(config_frame, from_=1.0, to=5.0, variable=self.spike_threshold_var,
                  orient='horizontal', length=200).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(config_frame, textvariable=self.spike_threshold_var).grid(row=1, column=2, padx=5, pady=5)

        ttk.Button(config_frame, text="Detect Spikes",
                   command=self.detect_spikes).grid(row=2, column=1, pady=10)

        # Results
        results_frame = ttk.LabelFrame(spike_frame, text="Detected Spikes", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Create treeview for spikes
        columns = ['Index', 'Start Time', 'Duration', 'Max Pressure', 'Severity']
        self.spikes_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)

        for col in columns:
            self.spikes_tree.heading(col, text=col)
            self.spikes_tree.column(col, width=100)

        spikes_scroll = ttk.Scrollbar(results_frame, orient='vertical', command=self.spikes_tree.yview)
        self.spikes_tree.configure(yscrollcommand=spikes_scroll.set)

        self.spikes_tree.pack(side='left', fill='both', expand=True)
        spikes_scroll.pack(side='right', fill='y')

        # Action buttons
        action_frame = ttk.Frame(spike_frame)
        action_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(action_frame, text="Mark Spikes on Plot",
                   command=self.mark_spikes_on_plot).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Export Spike Data",
                   command=self.export_spike_data).pack(side='left', padx=5)

    def create_leak_rate_tab(self, notebook):
        """Create leak rate analysis tab"""
        leak_frame = ttk.Frame(notebook)
        notebook.add(leak_frame, text='💨 Leak Rate')

        # Configuration
        config_frame = ttk.LabelFrame(leak_frame, text="Leak Rate Analysis", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)

        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.leak_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.leak_series_var,
                     values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(config_frame, text="Calculate Leak Rate",
                   command=self.calculate_leak_rate).grid(row=1, column=1, pady=10)

        # Results
        results_frame = ttk.LabelFrame(leak_frame, text="Leak Rate Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.leak_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10), height=10)
        leak_scroll = ttk.Scrollbar(results_frame, command=self.leak_text.yview)
        self.leak_text.config(yscrollcommand=leak_scroll.set)

        self.leak_text.pack(side='left', fill='both', expand=True)
        leak_scroll.pack(side='right', fill='y')

        # Fit plot frame
        fit_frame = ttk.LabelFrame(leak_frame, text="Leak Rate Fit", padding=10)
        fit_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Placeholder for fit plot
        ttk.Label(fit_frame, text="Leak rate fit plot will be shown here").pack(expand=True)

    def create_pumpdown_tab(self, notebook):
        """Create pump-down analysis tab"""
        pump_frame = ttk.Frame(notebook)
        notebook.add(pump_frame, text='📉 Pump-down')

        # Configuration
        config_frame = ttk.LabelFrame(pump_frame, text="Pump-down Analysis", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)

        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.pump_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.pump_series_var,
                     values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(config_frame, text="Analyze Pump-down",
                   command=self.analyze_pumpdown).grid(row=1, column=1, pady=10)

        # Results
        results_frame = ttk.LabelFrame(pump_frame, text="Pump-down Characteristics", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)

        self.pump_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10))
        pump_scroll = ttk.Scrollbar(results_frame, command=self.pump_text.yview)
        self.pump_text.config(yscrollcommand=pump_scroll.set)

        self.pump_text.pack(side='left', fill='both', expand=True)
        pump_scroll.pack(side='right', fill='y')

    def calculate_base_pressure(self):
        """Calculate base pressure for selected series"""
        series_text = self.base_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)

        y_data = file_data.df.iloc[start_idx:end_idx][series.y_column].dropna()

        if len(y_data) == 0:
            self.base_text.delete(1.0, tk.END)
            self.base_text.insert(1.0, "No valid data in selected series")
            return

        # Calculate base pressure
        window_minutes = self.window_size_var.get()
        base_pressure, rolling_min, rolling_std = VacuumAnalysisTools.calculate_base_pressure(
            y_data.values, window_minutes=window_minutes
        )

        # Display results
        result_text = f"BASE PRESSURE ANALYSIS\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"Window Size: {window_minutes} minutes\n"
        result_text += f"{'=' * 50}\n\n"

        result_text += f"Base Pressure: {base_pressure:.2e} mbar\n\n"

        result_text += f"Additional Statistics:\n"
        result_text += f"  Current Pressure: {y_data.iloc[-1]:.2e} mbar\n"
        result_text += f"  Average Pressure: {y_data.mean():.2e} mbar\n"
        result_text += f"  Minimum Pressure: {y_data.min():.2e} mbar\n"
        result_text += f"  Stability (min std): {rolling_std.min():.2e} mbar\n"

        # Store results for plotting
        self.current_base_pressure = base_pressure
        self.current_base_series = series

        self.base_text.delete(1.0, tk.END)
        self.base_text.insert(1.0, result_text)

    def add_base_pressure_line(self):
        """Add base pressure line to main plot"""
        if not hasattr(self, 'current_base_pressure'):
            messagebox.showwarning("Warning", "Please calculate base pressure first")
            return

        # Add annotation to parent's annotation manager
        if hasattr(self.parent, 'annotation_manager'):
            self.parent.annotation_manager.add_annotation(
                'hline',
                y_pos=self.current_base_pressure,
                label=f"Base Pressure: {self.current_base_pressure:.2e} mbar",
                color='green',
                style='--',
                width=2
            )
            messagebox.showinfo("Success", "Base pressure line added to plot")

    def analyze_noise(self):
        """Analyze noise in pressure data"""
        series_text = self.noise_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)

        y_data = file_data.df.iloc[start_idx:end_idx][series.y_column].dropna()

        if len(y_data) == 0:
            return

        # Analyze noise
        sample_rate = self.sample_rate_var.get()
        noise_metrics = VacuumAnalysisTools.calculate_noise_metrics(y_data.values, sample_rate)

        # Display results
        result_text = f"NOISE ANALYSIS\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"Sample Rate: {sample_rate} Hz\n"
        result_text += f"{'=' * 50}\n\n"

        result_text += f"Noise Metrics:\n"
        result_text += f"  RMS Noise: {noise_metrics['noise_rms']:.2e} mbar\n"
        result_text += f"  Peak-to-Peak: {noise_metrics['noise_p2p']:.2e} mbar\n"
        result_text += f"  Dominant Frequency: {noise_metrics['dominant_freq']:.3f} Hz\n"
        result_text += f"  SNR: {20 * np.log10(y_data.mean() / noise_metrics['noise_rms']):.1f} dB\n"

        self.noise_text.delete(1.0, tk.END)
        self.noise_text.insert(1.0, result_text)

    def detect_spikes(self):
        """Detect pressure spikes"""
        series_text = self.spike_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)
        data_slice = file_data.df.iloc[start_idx:end_idx]

        y_data = data_slice[series.y_column].values

        # Detect spikes
        threshold_factor = self.spike_threshold_var.get()
        spikes = VacuumAnalysisTools.detect_pressure_spikes(y_data, threshold_factor)

        # Clear previous results
        for item in self.spikes_tree.get_children():
            self.spikes_tree.delete(item)

        # Display spikes
        for i, spike in enumerate(spikes):
            # Get time if available
            if series.x_column != 'Index':
                try:
                    start_time = data_slice.iloc[spike['start']][series.x_column]
                except:
                    start_time = spike['start']
            else:
                start_time = spike['start']

            self.spikes_tree.insert('', 'end', values=[
                i,
                str(start_time),
                spike['duration'],
                f"{spike['max_pressure']:.2e}",
                spike['severity']
            ])

        # Store results
        self.current_spikes = spikes
        self.current_spike_series = series

    def mark_spikes_on_plot(self):
        """Mark detected spikes on the main plot"""
        if not hasattr(self, 'current_spikes'):
            messagebox.showwarning("Warning", "Please detect spikes first")
            return

        # Add annotations for spikes
        if hasattr(self.parent, 'annotation_manager'):
            for spike in self.current_spikes:
                # Add region for spike
                self.parent.annotation_manager.add_annotation(
                    'region',
                    x_start=spike['start'],
                    x_end=spike['end'],
                    label=f"Spike: {spike['max_pressure']:.2e} mbar",
                    color='red' if spike['severity'] == 'high' else 'orange',
                    alpha=0.3
                )

            messagebox.showinfo("Success", f"Added {len(self.current_spikes)} spike markers to plot")

    def export_spike_data(self):
        """Export spike detection results"""
        if not hasattr(self, 'current_spikes'):
            messagebox.showwarning("Warning", "No spike data to export")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Spike Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                spike_df = pd.DataFrame(self.current_spikes)
                spike_df.to_csv(filename, index=False)
                messagebox.showinfo("Success", f"Spike data exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export spike data:\n{str(e)}")

    def calculate_leak_rate(self):
        """Calculate vacuum leak rate"""
        series_text = self.leak_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)
        data_slice = file_data.df.iloc[start_idx:end_idx]

        # Prepare data
        if series.x_column == 'Index':
            x_data = np.arange(len(data_slice))
        else:
            x_data = data_slice[series.x_column]

        y_data = data_slice[series.y_column]

        # Remove NaN values
        valid_mask = ~(pd.isna(y_data))
        x_data = x_data[valid_mask]
        y_data = y_data[valid_mask]

        if len(x_data) == 0:
            return

        # Calculate leak rate
        start_pressure = y_data.iloc[0]
        leak_results = VacuumAnalysisTools.calculate_leak_rate(y_data, x_data, start_pressure)

        # Display results
        result_text = f"LEAK RATE ANALYSIS\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"{'=' * 50}\n\n"

        result_text += f"Initial Pressure: {start_pressure:.2e} mbar\n"
        result_text += f"Final Pressure: {y_data.iloc[-1]:.2e} mbar\n\n"

        result_text += f"Leak Rate: {leak_results['leak_rate']:.2e} mbar·L/s\n"
        result_text += f"Time Constant: {leak_results['time_constant']:.1f} s\n"
        result_text += f"R-squared: {leak_results['r_squared']:.4f}\n"

        self.leak_text.delete(1.0, tk.END)
        self.leak_text.insert(1.0, result_text)

    def analyze_pumpdown(self):
        """Analyze pump-down characteristics"""
        series_text = self.pump_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return

        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break

        if not series:
            return

        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)
        data_slice = file_data.df.iloc[start_idx:end_idx]

        # Prepare data
        if series.x_column == 'Index':
            x_data = np.arange(len(data_slice))
        else:
            x_data = data_slice[series.x_column]

        y_data = data_slice[series.y_column]

        # Remove NaN values
        valid_mask = ~(pd.isna(y_data))
        x_data = x_data[valid_mask]
        y_data = y_data[valid_mask]

        if len(x_data) == 0:
            return

        # Analyze pump-down
        pump_results = VacuumAnalysisTools.analyze_pump_down_curve(y_data.values, x_data)

        # Display results
        result_text = f"PUMP-DOWN ANALYSIS\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"{'=' * 50}\n\n"

        result_text += f"Pressure Range:\n"
        result_text += f"  Initial: {pump_results['initial_pressure']:.2e} mbar\n"
        result_text += f"  Final: {pump_results['final_pressure']:.2e} mbar\n"
        result_text += f"  Reduction: {pump_results['initial_pressure'] / pump_results['final_pressure']:.1f}x\n\n"

        result_text += f"Milestones:\n"
        for pressure, time in pump_results['milestones'].items():
            result_text += f"  {pressure}: reached at {time}\n"

        self.pump_text.delete(1.0, tk.END)
        self.pump_text.insert(1.0, result_text)

    def export_results(self):
        """Export all analysis results"""
        filename = filedialog.asksaveasfilename(
            title="Export Vacuum Analysis Results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("VACUUM DATA ANALYSIS RESULTS\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 70 + "\n\n")

                    # Base pressure
                    if self.base_text.get(1.0, tk.END).strip():
                        f.write("BASE PRESSURE ANALYSIS\n")
                        f.write("-" * 70 + "\n")
                        f.write(self.base_text.get(1.0, tk.END))
                        f.write("\n\n")

                    # Noise analysis
                    if self.noise_text.get(1.0, tk.END).strip():
                        f.write("NOISE ANALYSIS\n")
                        f.write("-" * 70 + "\n")
                        f.write(self.noise_text.get(1.0, tk.END))
                        f.write("\n\n")

                    # Leak rate
                    if self.leak_text.get(1.0, tk.END).strip():
                        f.write("LEAK RATE ANALYSIS\n")
                        f.write("-" * 70 + "\n")
                        f.write(self.leak_text.get(1.0, tk.END))
                        f.write("\n\n")

                    # Pump-down
                    if self.pump_text.get(1.0, tk.END).strip():
                        f.write("PUMP-DOWN ANALYSIS\n")
                        f.write("-" * 70 + "\n")
                        f.write(self.pump_text.get(1.0, tk.END))
                        f.write("\n\n")

                messagebox.showinfo("Success", f"Analysis results exported to:\n{filename}")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results:\n{str(e)}")

    def close(self):
        """Close the dialog"""
        self.dialog.destroy()


class AnnotationDialog:
    """
    Modern annotation dialog with inline editing and vacuum templates
    Allows adding, editing, and removing annotations
    """

    def __init__(self, parent, annotation_manager, figure=None, ax=None):
        """
        Initialize annotation dialog

        Args:
            parent: Parent window
            annotation_manager: AnnotationManager instance
            figure: Matplotlib figure (optional)
            axes: Matplotlib axes (optional)
        """
        self.parent = parent
        self.annotation_manager = annotation_manager
        self.figure = figure
        self.ax = ax
        self.selected_annotation = None
        self.dragging = False
        self.drag_data = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Annotations")
        self.dialog.geometry("900x700")
        self.dialog.configure(bg='#f5f5f5')

        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()

        # If figure is provided, set up interactive editing
        if self.figure and self.ax:
            self.setup_interactive_editing()

        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

    def create_widgets(self):
        """Create modern annotation interface"""
        # Header
        header = tk.Frame(self.dialog, bg='#34495e', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text="📍 Plot Annotations",
                 font=('Segoe UI', 16, 'bold'),
                 fg='white', bg='#34495e').pack(pady=15)

        # Main container
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)

        # Left panel - annotation types
        left_panel = ttk.Frame(main_container, width=250)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)

        self.create_annotation_types_panel(left_panel)

        # Right panel - annotation list and properties
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side='left', fill='both', expand=True)

        self.create_annotation_list_panel(right_panel)

    def create_annotation_types_panel(self, parent):
        """Create panel with annotation type buttons"""
        ttk.Label(parent, text="Add Annotation",
                  font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))

        # Annotation type buttons with icons
        buttons = [
            ("➖ Horizontal Line", self.add_horizontal_line),
            ("│ Vertical Line", self.add_vertical_line),
            ("▭ Shaded Region", self.add_region),
            ("● Point Marker", self.add_point),
            ("T Text Label", self.add_text),
            ("→ Enhanced Arrow", self.add_enhanced_arrow),
        ]

        for text, command in buttons:
            btn = tk.Button(parent, text=text, command=command,
                            bg='#3498db', fg='white',
                            font=('Segoe UI', 10),
                            padx=15, pady=10,
                            relief='flat', cursor='hand2',
                            anchor='w')
            btn.pack(fill='x', pady=3)

            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#2980b9'))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#3498db'))

        # Quick templates for vacuum analysis
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=20)

        ttk.Label(parent, text="Vacuum Templates",
                  font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))

        templates = [
            ("🎯 Base Pressure Line", self.add_base_pressure_template),
            ("📊 Noise Region", self.add_noise_region_template),
            ("⚡ Spike Markers", self.add_spike_marker_template),
            ("📉 Pressure Targets", self.add_pressure_targets_template),
        ]

        for text, command in templates:
            btn = tk.Button(parent, text=text, command=command,
                            bg='#27ae60', fg='white',
                            font=('Segoe UI', 9),
                            padx=10, pady=8,
                            relief='flat', cursor='hand2',
                            anchor='w')
            btn.pack(fill='x', pady=2)

            btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#229954'))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#27ae60'))

    def create_annotation_list_panel(self, parent):
        """Create panel showing all annotations with inline editing"""
        # List header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(header_frame, text="Current Annotations",
                  font=('Segoe UI', 12, 'bold')).pack(side='left')

        # Action buttons
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side='right')

        ttk.Button(btn_frame, text="Clear All",
                   command=self.clear_all).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Export",
                   command=self.export_annotations).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Import",
                   command=self.import_annotations).pack(side='left', padx=2)

        # Annotation list with custom styling
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True)

        # Create canvas for scrollable list
        self.canvas = tk.Canvas(list_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill='y')

        # Update list
        self.update_annotation_list()

        # Bottom action bar
        action_bar = ttk.Frame(parent)
        action_bar.pack(fill='x', pady=10)

        ttk.Button(action_bar, text="Apply & Close",
                   command=self.apply_and_close,
                   style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(action_bar, text="Cancel",
                   command=self.cancel).pack(side='right')

    def update_annotation_list(self):
        """Update the annotation list display"""
        # Clear existing items
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Add annotation items
        for ann_id, annotation in self.annotation_manager.annotations.items():
            self.create_annotation_item(ann_id, annotation)

    def create_annotation_item(self, ann_id, annotation):
        """Create a single annotation item with inline controls"""
        # Container frame
        item_frame = tk.Frame(self.scrollable_frame, bg='white', relief='solid',
                              borderwidth=1, padx=10, pady=10)
        item_frame.pack(fill='x', pady=5, padx=5)

        # Selection highlight
        if ann_id == self.annotation_manager.selected_annotation:
            item_frame.config(borderwidth=2, relief='solid', highlightbackground='#3498db')

        # Header row
        header_row = ttk.Frame(item_frame)
        header_row.pack(fill='x')

        # Type icon and label
        type_icons = {
            'vline': '│',
            'hline': '─',
            'region': '▭',
            'point': '●',
            'text': 'T',
            'arrow': '→'
        }

        icon = type_icons.get(annotation['type'], '?')
        ttk.Label(header_row, text=f"{icon} {annotation['type'].title()}",
                  font=('Segoe UI', 10, 'bold')).pack(side='left')

        # Visibility toggle
        vis_var = tk.BooleanVar(value=annotation.get('visible', True))
        vis_check = ttk.Checkbutton(header_row, text="", variable=vis_var,
                                    command=lambda: self.toggle_visibility(ann_id, vis_var.get()))
        vis_check.pack(side='right', padx=5)
        ttk.Label(header_row, text="Visible").pack(side='right')

        # Delete button
        del_btn = tk.Button(header_row, text="🗑", fg='#e74c3c',
                            font=('Segoe UI', 10), relief='flat', cursor='hand2',
                            command=lambda: self.delete_annotation(ann_id))
        del_btn.pack(side='right', padx=5)

        # Properties based on type
        props_frame = ttk.Frame(item_frame)
        props_frame.pack(fill='x', pady=(10, 0))

        self.create_annotation_properties(props_frame, ann_id, annotation)

        # Click to select
        item_frame.bind("<Button-1>", lambda e: self.select_annotation(ann_id))

    def create_annotation_properties(self, parent, ann_id, annotation):
        """Create property controls for annotation"""
        ann_type = annotation['type']

        if ann_type in ['vline', 'hline']:
            # Position with better precision controls
            pos_frame = ttk.Frame(parent)
            pos_frame.pack(fill='x', pady=2)

            pos_key = 'x_pos' if ann_type == 'vline' else 'y_pos'
            ttk.Label(pos_frame, text=f"{pos_key.replace('_', ' ').title()}:").pack(side='left')

            pos_var = tk.StringVar(value=str(annotation.get(pos_key, 0)))
            pos_entry = ttk.Entry(pos_frame, textvariable=pos_var, width=15)
            pos_entry.pack(side='left', padx=5)
            pos_entry.bind('<Return>', lambda e: self.update_property(ann_id, pos_key, float(pos_var.get())))

            # Fine adjustment buttons
            ttk.Button(pos_frame, text="-", width=3,
                       command=lambda: self.adjust_position(ann_id, pos_key, -0.1)).pack(side='left', padx=1)
            ttk.Button(pos_frame, text="+", width=3,
                       command=lambda: self.adjust_position(ann_id, pos_key, 0.1)).pack(side='left', padx=1)

            # Color
            color_btn = tk.Button(pos_frame, text="Color", bg=annotation.get('color', 'red'),
                                  command=lambda: self.change_color(ann_id))
            color_btn.pack(side='left', padx=5)

        elif ann_type == 'region':
            # Start and end positions with better controls
            pos_frame = ttk.Frame(parent)
            pos_frame.pack(fill='x', pady=2)

            ttk.Label(pos_frame, text="From:").pack(side='left')
            start_var = tk.StringVar(value=str(annotation.get('x_start', 0)))
            start_entry = ttk.Entry(pos_frame, textvariable=start_var, width=10)
            start_entry.pack(side='left', padx=5)

            ttk.Label(pos_frame, text="To:").pack(side='left', padx=(10, 0))
            end_var = tk.StringVar(value=str(annotation.get('x_end', 1)))
            end_entry = ttk.Entry(pos_frame, textvariable=end_var, width=10)
            end_entry.pack(side='left', padx=5)

            def update_region():
                self.annotation_manager.update_annotation(ann_id,
                                                          x_start=float(start_var.get()),
                                                          x_end=float(end_var.get()))
                self.refresh_plot()

            start_entry.bind('<Return>', lambda e: update_region())
            end_entry.bind('<Return>', lambda e: update_region())

        elif ann_type == 'text':
            # Text content
            text_frame = ttk.Frame(parent)
            text_frame.pack(fill='x', pady=2)

            ttk.Label(text_frame, text="Text:").pack(side='left')
            text_var = tk.StringVar(value=annotation.get('text', ''))
            text_entry = ttk.Entry(text_frame, textvariable=text_var, width=30)
            text_entry.pack(side='left', padx=5)
            text_entry.bind('<Return>', lambda e: self.update_property(ann_id, 'text', text_var.get()))

        elif ann_type == 'arrow':
            # Enhanced arrow controls
            arrow_frame = ttk.Frame(parent)
            arrow_frame.pack(fill='x', pady=2)

            # Start position
            ttk.Label(arrow_frame, text="Start:").grid(row=0, column=0, sticky='w')
            start_x_var = tk.StringVar(value=str(annotation.get('x_start', 0)))
            start_y_var = tk.StringVar(value=str(annotation.get('y_start', 0)))

            ttk.Entry(arrow_frame, textvariable=start_x_var, width=10).grid(row=0, column=1, padx=2)
            ttk.Entry(arrow_frame, textvariable=start_y_var, width=10).grid(row=0, column=2, padx=2)

            # End position
            ttk.Label(arrow_frame, text="End:").grid(row=1, column=0, sticky='w')
            end_x_var = tk.StringVar(value=str(annotation.get('x_end', 1)))
            end_y_var = tk.StringVar(value=str(annotation.get('y_end', 1)))

            ttk.Entry(arrow_frame, textvariable=end_x_var, width=10).grid(row=1, column=1, padx=2)
            ttk.Entry(arrow_frame, textvariable=end_y_var, width=10).grid(row=1, column=2, padx=2)

            def update_arrow():
                self.annotation_manager.update_annotation(ann_id,
                                                          x_start=float(start_x_var.get()),
                                                          y_start=float(start_y_var.get()),
                                                          x_end=float(end_x_var.get()),
                                                          y_end=float(end_y_var.get()))
                self.refresh_plot()

            ttk.Button(arrow_frame, text="Update", command=update_arrow).grid(row=2, column=1, columnspan=2, pady=5)

        # Label (common to all)
        if ann_type != 'text':
            label_frame = ttk.Frame(parent)
            label_frame.pack(fill='x', pady=2)

            ttk.Label(label_frame, text="Label:").pack(side='left')
            label_var = tk.StringVar(value=annotation.get('label', ''))
            label_entry = ttk.Entry(label_frame, textvariable=label_var, width=25)
            label_entry.pack(side='left', padx=5)
            label_entry.bind('<Return>', lambda e: self.update_property(ann_id, 'label', label_var.get()))

    def adjust_position(self, ann_id, pos_key, delta):
        """Fine adjust position"""
        annotation = self.annotation_manager.annotations.get(ann_id)
        if annotation:
            current_pos = annotation.get(pos_key, 0)
            self.annotation_manager.update_annotation(ann_id, **{pos_key: current_pos + delta})
            self.update_annotation_list()
            self.refresh_plot()

    def select_annotation(self, ann_id):
        """Select an annotation"""
        self.annotation_manager.selected_annotation = ann_id
        self.update_annotation_list()
        self.refresh_plot()

    def toggle_visibility(self, ann_id, visible):
        """Toggle annotation visibility"""
        self.annotation_manager.update_annotation(ann_id, visible=visible)
        self.refresh_plot()

    def update_property(self, ann_id, prop, value):
        """Update annotation property"""
        self.annotation_manager.update_annotation(ann_id, **{prop: value})
        self.refresh_plot()

    def change_color(self, ann_id):
        """Change annotation color"""
        annotation = self.annotation_manager.annotations.get(ann_id)
        if annotation:
            color = colorchooser.askcolor(initialcolor=annotation.get('color', 'red'))
            if color[1]:
                self.annotation_manager.update_annotation(ann_id, color=color[1])
                self.update_annotation_list()
                self.refresh_plot()

    def delete_annotation(self, ann_id):
        """Delete annotation"""
        if messagebox.askyesno("Confirm", "Delete this annotation?"):
            self.annotation_manager.remove_annotation(ann_id)
            self.update_annotation_list()
            self.refresh_plot()

    def add_horizontal_line(self):
        """Add horizontal line annotation"""
        # Get current y-axis limits or default
        y_pos = 0
        if self.ax:
            ylim = self.ax.get_ylim()
            y_pos = (ylim[0] + ylim[1]) / 2

        ann_id = self.annotation_manager.add_annotation('hline',
                                                        y_pos=y_pos,
                                                        label="Horizontal Line",
                                                        color='#3498db',
                                                        style='--',
                                                        width=2)

        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()

    def add_vertical_line(self):
        """Add vertical line annotation"""
        x_pos = 0
        if self.ax:
            xlim = self.ax.get_xlim()
            x_pos = (xlim[0] + xlim[1]) / 2

        ann_id = self.annotation_manager.add_annotation('vline',
                                                        x_pos=x_pos,
                                                        label="Vertical Line",
                                                        color='#e74c3c',
                                                        style='--',
                                                        width=2)

        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()

    def add_region(self):
        """Add shaded region annotation"""
        x_start, x_end = 0, 1
        if self.ax:
            xlim = self.ax.get_xlim()
            span = xlim[1] - xlim[0]
            x_start = xlim[0] + span * 0.3
            x_end = xlim[0] + span * 0.7

        ann_id = self.annotation_manager.add_annotation('region',
                                                        x_start=x_start,
                                                        x_end=x_end,
                                                        label="Region",
                                                        color='#f39c12',
                                                        alpha=0.3)

        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()

    def add_point(self):
        """Add point marker annotation"""
        x_pos, y_pos = 0, 0
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            x_pos = (xlim[0] + xlim[1]) / 2
            y_pos = (ylim[0] + ylim[1]) / 2

        ann_id = self.annotation_manager.add_annotation('point',
                                                        x_pos=x_pos,
                                                        y_pos=y_pos,
                                                        label="Point",
                                                        marker='o',
                                                        size=100,
                                                        color='#e74c3c')

        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()

    def add_text(self):
        """Add text annotation"""
        x_pos, y_pos = 0, 0
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            x_pos = xlim[0] + (xlim[1] - xlim[0]) * 0.1
            y_pos = ylim[1] - (ylim[1] - ylim[0]) * 0.1

        ann_id = self.annotation_manager.add_annotation('text',
                                                        x_pos=x_pos,
                                                        y_pos=y_pos,
                                                        text="Annotation",
                                                        fontsize=12,
                                                        color='black',
                                                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                                                                  alpha=0.8))

        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()

    def add_enhanced_arrow(self):
        """Add enhanced arrow annotation with better defaults"""
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

            # Create arrow pointing from upper left to center
            x_start = xlim[0] + (xlim[1] - xlim[0]) * 0.2
            y_start = ylim[0] + (ylim[1] - ylim[0]) * 0.8
            x_end = xlim[0] + (xlim[1] - xlim[0]) * 0.5
            y_end = ylim[0] + (ylim[1] - ylim[0]) * 0.5
        else:
            x_start, y_start, x_end, y_end = 0, 1, 1, 0

        ann_id = self.annotation_manager.add_annotation('arrow',
                                                        x_start=x_start,
                                                        y_start=y_start,
                                                        x_end=x_end,
                                                        y_end=y_end,
                                                        style='->',
                                                        color='#2c3e50',
                                                        width=2,
                                                        label="Arrow")

        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()

    # Vacuum-specific templates
    def add_base_pressure_template(self):
        """Add base pressure line template"""
        if self.ax:
            ylim = self.ax.get_ylim()
            # Estimate base pressure as lower 10% of range
            base_pressure = ylim[0] + (ylim[1] - ylim[0]) * 0.1
        else:
            base_pressure = 1e-6

        ann_id = self.annotation_manager.add_annotation('hline',
                                                        y_pos=base_pressure,
                                                        label=f"Base Pressure: {base_pressure:.2e} mbar",
                                                        color='green',
                                                        style='--',
                                                        width=2,
                                                        alpha=0.8)

        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()

        messagebox.showinfo("Template Added",
                            "Base pressure line added. Adjust the position to match your measured base pressure.")

    def add_noise_region_template(self):
        """Add noise analysis region template"""
        if self.ax:
            xlim = self.ax.get_xlim()
            # Create region in middle third
            span = xlim[1] - xlim[0]
            x_start = xlim[0] + span * 0.33
            x_end = xlim[0] + span * 0.67
        else:
            x_start, x_end = 100, 200

        ann_id = self.annotation_manager.add_annotation('region',
                                                        x_start=x_start,
                                                        x_end=x_end,
                                                        label="Noise Analysis Region",
                                                        color='purple',
                                                        alpha=0.2)

        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()

        messagebox.showinfo("Template Added",
                            "Noise analysis region added. Adjust to cover a stable pressure region.")

    def add_spike_marker_template(self):
        """Add spike marker template"""
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            x_pos = xlim[0] + (xlim[1] - xlim[0]) * 0.5
            y_pos = ylim[0] + (ylim[1] - ylim[0]) * 0.9
        else:
            x_pos, y_pos = 50, 1e-3

        ann_id = self.annotation_manager.add_annotation('point',
                                                        x_pos=x_pos,
                                                        y_pos=y_pos,
                                                        label="Pressure Spike",
                                                        marker='^',
                                                        size=150,
                                                        color='red')

        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()

        messagebox.showinfo("Template Added",
                            "Spike marker added. Move to actual spike locations.")

    def add_pressure_targets_template(self):
        """Add common vacuum pressure target lines"""
        targets = [
            (1e-3, "High Vacuum", 'blue'),
            (1e-6, "Ultra-High Vacuum", 'green'),
            (1e-9, "Extreme High Vacuum", 'purple')
        ]

        added_count = 0
        for pressure, label, color in targets:
            # Only add if within current plot range
            if self.ax:
                ylim = self.ax.get_ylim()
                if ylim[0] <= pressure <= ylim[1]:
                    self.annotation_manager.add_annotation('hline',
                                                           y_pos=pressure,
                                                           label=f"{label}: {pressure:.0e} mbar",
                                                           color=color,
                                                           style=':',
                                                           width=1.5,
                                                           alpha=0.6)
                    added_count += 1
            else:
                self.annotation_manager.add_annotation('hline',
                                                       y_pos=pressure,
                                                       label=f"{label}: {pressure:.0e} mbar",
                                                       color=color,
                                                       style=':',
                                                       width=1.5,
                                                       alpha=0.6)
                added_count += 1

        self.update_annotation_list()
        self.refresh_plot()

        messagebox.showinfo("Template Added",
                            f"Added {added_count} pressure target lines.")

    def setup_interactive_editing(self):
        """Set up interactive annotation editing on the plot"""
        # Placeholder for interactive editing implementation
        pass

    def clear_all(self):
        """Clear all annotations"""
        if self.annotation_manager.annotations:
            if messagebox.askyesno("Confirm", "Remove all annotations?"):
                self.annotation_manager.annotations.clear()
                self.update_annotation_list()
                self.refresh_plot()

    def export_annotations(self):
        """Export annotations to file"""
        filename = filedialog.asksaveasfilename(
            title="Export Annotations",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.annotation_manager.annotations, f, indent=2)
                messagebox.showinfo("Success", "Annotations exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def import_annotations(self):
        """Import annotations from file"""
        filename = filedialog.askopenfilename(
            title="Import Annotations",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    imported = json.load(f)

                # Merge with existing annotations
                for ann_id, annotation in imported.items():
                    if 'id' in annotation:
                        del annotation['id']
                    new_id = self.annotation_manager.add_annotation(
                        annotation['type'], **annotation)

                self.update_annotation_list()
                self.refresh_plot()
                messagebox.showinfo("Success", f"Imported {len(imported)} annotations!")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {str(e)}")

    def refresh_plot(self):
        """Refresh the plot with updated annotations"""
        if hasattr(self.parent, 'refresh_plot'):
            self.parent.refresh_plot()

    def apply_and_close(self):
        """Apply changes and close dialog"""
        self.refresh_plot()
        self.dialog.destroy()

    def cancel(self):
        """Cancel and close dialog"""
        self.dialog.destroy()


class DataSelectorDialog:
    """
    Dialog for advanced data selection from non-standard Excel layouts
    Helps identify headers and data ranges in complex spreadsheets
    """

    def __init__(self, parent, file_data, on_data_selected=None):
        """
        Initialize data selector dialog

        Args:
            parent: Parent window
            file_data: FileData object to select from
            on_data_selected: Callback function when selection is made
        """
        self.parent = parent
        self.file_data = file_data
        self.on_data_selected = on_data_selected

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Advanced Data Selection")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create UI
        self.create_widgets()

        # Center dialog
        self.center_dialog()

    def create_widgets(self):
        """Create data selector UI"""
        # Preview section
        preview_frame = ttk.LabelFrame(self.dialog, text="Data Preview")
        preview_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Create text widget for preview
        self.preview_text = tk.Text(preview_frame, wrap='none', height=15)
        scrollbar = ttk.Scrollbar(preview_frame, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self.preview_text.pack(fill='both', expand=True)

        # Update preview
        self.update_preview()

        # Selection controls
        self.create_selection_controls()

        # Buttons
        self.create_buttons()

    def create_selection_controls(self):
        """Create data selection controls"""
        control_frame = ttk.Frame(self.dialog)
        control_frame.pack(fill='x', padx=10, pady=10)

        # Header row selection
        ttk.Label(control_frame, text="Header Row:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.header_row_var = tk.IntVar(value=0)
        ttk.Spinbox(control_frame, textvariable=self.header_row_var, from_=0,
                    to=len(self.file_data.df) - 1, width=10).grid(row=0, column=1, padx=5, pady=5)

        # Auto-detect button
        ttk.Button(control_frame, text="Auto-Detect Headers",
                   command=self.auto_detect_headers).grid(row=0, column=2, padx=10, pady=5)

        # Data range
        ttk.Label(control_frame, text="Start Row:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.start_row_var = tk.IntVar(value=1)
        ttk.Spinbox(control_frame, textvariable=self.start_row_var, from_=0,
                    to=len(self.file_data.df) - 1, width=10).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(control_frame, text="End Row:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.end_row_var = tk.IntVar(value=len(self.file_data.df))
        ttk.Spinbox(control_frame, textvariable=self.end_row_var, from_=1,
                    to=len(self.file_data.df), width=10).grid(row=2, column=1, padx=5, pady=5)

    def create_buttons(self):
        """Create dialog buttons"""
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(btn_frame, text="Apply Selection", command=self.apply_selection).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side='right')

    def update_preview(self):
        """Update data preview display"""
        # Show first 20 rows
        preview_df = self.file_data.df.head(20)
        preview_text = preview_df.to_string()

        self.preview_text.delete('1.0', tk.END)
        self.preview_text.insert('1.0', preview_text)

    def auto_detect_headers(self):
        """Auto-detect header row"""
        # Use utility function to find header row
        header_row = detect_datetime_column(self.file_data.df)
        self.header_row_var.set(header_row)

        # Update start row
        self.start_row_var.set(header_row + 1)

    def apply_selection(self):
        """Apply data selection"""
        if self.on_data_selected:
            selection_info = {
                'header_row': self.header_row_var.get(),
                'start_row': self.start_row_var.get(),
                'end_row': self.end_row_var.get()
            }
            self.on_data_selected(selection_info)

        self.dialog.destroy()

    def cancel(self):
        """Cancel selection"""
        self.dialog.destroy()

    def center_dialog(self):
        """Center dialog on screen"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")