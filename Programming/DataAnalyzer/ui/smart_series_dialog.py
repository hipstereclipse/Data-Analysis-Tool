#!/usr/bin/env python3
"""
Smart Series Configuration Dialog - Professional Data Analysis Interface
Advanced series configuration with intelligent data understanding and modern UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
import re

from models.data_models import SeriesConfig, FileData
from analysis.legacy_analysis_tools import DataAnalysisTools

logger = logging.getLogger(__name__)


class SmartSeriesDialog(ctk.CTkToplevel):
    """
    Professional Smart Series Configuration Dialog
    Features:
    - Intelligent data type detection
    - Automatic column analysis and recommendations
    - Live preview with instant updates
    - Professional styling options
    - Advanced filtering and data range selection
    - Statistical analysis integration
    - Export-ready configuration
    """

    def __init__(self, parent, series: SeriesConfig = None, file_data: FileData = None):
        super().__init__(parent)
        
        self.parent = parent
        self.file_data = file_data
        self.original_series = series
        # Safely create a copy of the series
        if series and hasattr(series, 'copy'):
            try:
                self.series = series.copy()
            except Exception as e:
                logger.warning(f"Failed to copy series: {e}, creating new one")
                self.series = self._create_smart_series()
        else:
            self.series = self._create_smart_series()
        self.analysis_tools = DataAnalysisTools()
        
        # Dialog state
        self.result = None
        self.preview_enabled = True
        self.live_update = True
        
        # UI Components
        self.setup_dialog()
        self.create_interface()
        self.analyze_data()
        self.populate_fields()
        self.update_preview()
        
        # Center dialog
        self.center_window()

    def _create_smart_series(self) -> SeriesConfig:
        """Create a new series with intelligent defaults"""
        if not self.file_data:
            return SeriesConfig(
                name="New Series",
                file_id="",
                x_column="",
                y_column=""
            )
        
        # Intelligent column selection
        numeric_cols = self.file_data.get_numeric_columns()
        datetime_cols = self.file_data.datetime_columns
        all_cols = self.file_data.columns
        
        # Smart X-axis selection (prefer datetime, then first numeric, then first column)
        x_column = ""
        if datetime_cols:
            x_column = datetime_cols[0]
        elif numeric_cols:
            x_column = numeric_cols[0]
        elif all_cols:
            x_column = all_cols[0]
        
        # Smart Y-axis selection (prefer second numeric column, or first if only one)
        y_column = ""
        if len(numeric_cols) > 1:
            y_column = numeric_cols[1] if numeric_cols[0] == x_column else numeric_cols[0]
        elif numeric_cols:
            y_column = numeric_cols[0]
        elif len(all_cols) > 1:
            y_column = all_cols[1] if all_cols[0] == x_column else all_cols[0]
        
        # Generate smart series name
        name = self._generate_smart_name(x_column, y_column)
        
        return SeriesConfig(
            name=name,
            file_id=self.file_data.id,
            x_column=x_column,
            y_column=y_column,
            color=self._get_smart_color(),
            line_style="-",
            line_width=1.5,
            visible=True,
            show_in_legend=True
        )

    def _generate_smart_name(self, x_col: str, y_col: str) -> str:
        """Generate intelligent series name based on column names"""
        if not x_col or not y_col:
            return "New Series"
        
        try:
            # Ensure columns are strings
            x_col_str = str(x_col)
            y_col_str = str(y_col)
            
            # Clean column names
            clean_y = re.sub(r'[_\s]+', ' ', y_col_str).strip().title()
            clean_x = re.sub(r'[_\s]+', ' ', x_col_str).strip().title()
            
            # Generate contextual name
            if 'time' in x_col_str.lower() or 'date' in x_col_str.lower():
                return f"{clean_y} vs Time"
            elif 'pressure' in y_col_str.lower():
                return f"Pressure Analysis"
            elif 'temp' in y_col_str.lower():
                return f"Temperature Data"
            else:
                return f"{clean_y} vs {clean_x}"
        except Exception as e:
            logger.warning(f"Error generating smart name: {e}")
            return "New Series"

    def _get_smart_color(self) -> str:
        """Get next available color from professional palette"""
        colors = [
            "#2E86AB", "#A23B72", "#F18F01", "#C73E1D", 
            "#8B5CF6", "#10B981", "#F59E0B", "#EF4444",
            "#6366F1", "#EC4899", "#14B8A6", "#F97316"
        ]
        # Simple rotation based on existing series count
        return colors[0]  # For now, return first color

    def setup_dialog(self):
        """Setup dialog window properties with responsive sizing"""
        self.title("Smart Series Configuration")
        
        # Get screen dimensions for responsive sizing
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Use 70% of screen size for better compatibility
        dialog_width = min(1200, int(screen_width * 0.7))
        dialog_height = min(800, int(screen_height * 0.7))
        
        self.geometry(f"{dialog_width}x{dialog_height}")
        self.minsize(min(1000, dialog_width), min(700, dialog_height))
        self.transient(self.parent)
        self.grab_set()
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def create_interface(self):
        """Create the modern interface"""
        # Main container
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel - Configuration
        self.create_config_panel(main_frame)
        
        # Right panel - Preview
        self.create_preview_panel(main_frame)
        
        # Bottom panel - Actions
        self.create_action_panel(main_frame)

    def create_config_panel(self, parent):
        """Create configuration panel with intelligent controls"""
        config_frame = ctk.CTkFrame(parent)
        config_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        config_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            config_frame, 
            text="📊 Smart Series Configuration",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 20), sticky="w")
        
        # Create tabbed interface for organized configuration
        self.config_notebook = ctk.CTkTabview(config_frame)
        self.config_notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        config_frame.grid_rowconfigure(1, weight=1)
        
        # Add tabs
        self.config_notebook.add("📈 Data")
        self.config_notebook.add("🎨 Style")
        self.config_notebook.add("📊 Analysis")
        self.config_notebook.add("⚙️ Advanced")
        
        # Create tab content
        self.create_data_tab()
        self.create_style_tab()
        self.create_analysis_tab()
        self.create_advanced_tab()

    def create_data_tab(self):
        """Create intelligent data selection tab"""
        tab_frame = self.config_notebook.tab("📈 Data")
        
        # Basic Information Section
        info_frame = ctk.CTkFrame(tab_frame)
        info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        info_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(info_frame, text="Series Name:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.name_var = tk.StringVar(value=self.series.name)
        self.name_entry = ctk.CTkEntry(info_frame, textvariable=self.name_var, width=300)
        self.name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.name_entry.bind('<KeyRelease>', self.on_config_change)
        
        # Smart Column Selection Section
        column_frame = ctk.CTkFrame(tab_frame)
        column_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        column_frame.grid_columnconfigure(1, weight=1)
        
        # Column analysis display
        if self.file_data:
            self.create_column_analysis(column_frame)
        
        # Data Range Section
        range_frame = ctk.CTkFrame(tab_frame)
        range_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        self.create_data_range_controls(range_frame)
        
        # Data Quality Section
        quality_frame = ctk.CTkFrame(tab_frame)
        quality_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        self.create_data_quality_display(quality_frame)

    def create_column_analysis(self, parent):
        """Create intelligent column analysis and selection"""
        parent.grid_columnconfigure(1, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(
            parent, 
            text="🔍 Intelligent Column Analysis",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # X-axis selection with recommendations
        ctk.CTkLabel(parent, text="X-Axis (Independent):", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        
        x_frame = ctk.CTkFrame(parent)
        x_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        x_frame.grid_columnconfigure(0, weight=1)
        
        self.x_column_var = tk.StringVar(value=self.series.x_column)
        self.x_column_combo = ctk.CTkComboBox(
            x_frame, 
            variable=self.x_column_var,
            values=[str(col) for col in self.file_data.columns] if self.file_data else [],
            command=self.on_column_change,
            width=200
        )
        self.x_column_combo.grid(row=0, column=0, sticky="ew", padx=5)
        
        # X-axis info button
        self.x_info_button = ctk.CTkButton(
            x_frame, 
            text="ℹ️", 
            width=30,
            command=lambda: self.show_column_info(self.x_column_var.get())
        )
        self.x_info_button.grid(row=0, column=1, padx=(5, 0))
        
        # X-axis recommendations
        self.x_recommendations = ctk.CTkLabel(
            parent, 
            text="💡 Recommendation: Select time/date column for time series analysis",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.x_recommendations.grid(row=2, column=1, sticky="w", padx=5)
        
        # Y-axis selection with recommendations  
        ctk.CTkLabel(parent, text="Y-Axis (Dependent):", font=ctk.CTkFont(weight="bold")).grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        
        y_frame = ctk.CTkFrame(parent)
        y_frame.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        y_frame.grid_columnconfigure(0, weight=1)
        
        self.y_column_var = tk.StringVar(value=self.series.y_column)
        self.y_column_combo = ctk.CTkComboBox(
            y_frame,
            variable=self.y_column_var,
            values=[str(col) for col in self.file_data.columns] if self.file_data else [],
            command=self.on_column_change,
            width=200
        )
        self.y_column_combo.grid(row=0, column=0, sticky="ew", padx=5)
        
        # Y-axis info button
        self.y_info_button = ctk.CTkButton(
            y_frame,
            text="ℹ️",
            width=30,
            command=lambda: self.show_column_info(self.y_column_var.get())
        )
        self.y_info_button.grid(row=0, column=1, padx=(5, 0))
        
        # Y-axis recommendations
        self.y_recommendations = ctk.CTkLabel(
            parent,
            text="💡 Recommendation: Select numeric column for measurement data",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.y_recommendations.grid(row=4, column=1, sticky="w", padx=5)

    def create_data_range_controls(self, parent):
        """Create intelligent data range selection"""
        parent.grid_columnconfigure(1, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(
            parent,
            text="📊 Data Range Selection",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Range controls
        range_control_frame = ctk.CTkFrame(parent)
        range_control_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        range_control_frame.grid_columnconfigure((1, 3), weight=1)
        
        # Start index
        ctk.CTkLabel(range_control_frame, text="Start Row:").grid(row=0, column=0, padx=5, pady=5)
        self.start_var = tk.IntVar(value=self.series.start_index or 0)
        self.start_spinbox = ctk.CTkEntry(range_control_frame, textvariable=self.start_var, width=100)
        self.start_spinbox.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.start_spinbox.bind('<KeyRelease>', self.on_range_change)
        
        # End index
        ctk.CTkLabel(range_control_frame, text="End Row:").grid(row=0, column=2, padx=5, pady=5)
        max_rows = len(self.file_data.data) if self.file_data else 1000
        self.end_var = tk.IntVar(value=self.series.end_index or max_rows)
        self.end_spinbox = ctk.CTkEntry(range_control_frame, textvariable=self.end_var, width=100)
        self.end_spinbox.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.end_spinbox.bind('<KeyRelease>', self.on_range_change)
        
        # Quick range buttons
        quick_frame = ctk.CTkFrame(parent)
        quick_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(quick_frame, text="Quick Select:").grid(row=0, column=0, padx=5, pady=5)
        
        ctk.CTkButton(quick_frame, text="All Data", width=80, 
                     command=self.select_all_data).grid(row=0, column=1, padx=2)
        ctk.CTkButton(quick_frame, text="First 100", width=80,
                     command=self.select_first_100).grid(row=0, column=2, padx=2)
        ctk.CTkButton(quick_frame, text="Last 100", width=80,
                     command=self.select_last_100).grid(row=0, column=3, padx=2)
        ctk.CTkButton(quick_frame, text="Auto Detect", width=80,
                     command=self.auto_detect_range).grid(row=0, column=4, padx=2)

    def create_data_quality_display(self, parent):
        """Create data quality analysis display"""
        parent.grid_columnconfigure(0, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(
            parent,
            text="🔍 Data Quality Analysis",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.grid(row=0, column=0, pady=(10, 15), sticky="w")
        
        # Quality metrics
        self.quality_text = ctk.CTkTextbox(parent, height=100, width=400)
        self.quality_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

    def create_style_tab(self):
        """Create professional styling options"""
        tab_frame = self.config_notebook.tab("🎨 Style")
        
        # Visual Style Section
        style_frame = ctk.CTkFrame(tab_frame)
        style_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        style_frame.grid_columnconfigure(1, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(
            style_frame,
            text="🎨 Visual Appearance",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Color selection
        ctk.CTkLabel(style_frame, text="Color:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        
        color_frame = ctk.CTkFrame(style_frame)
        color_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.color_var = tk.StringVar(value=self.series.color)
        self.color_button = ctk.CTkButton(
            color_frame,
            text="🎨 Choose Color",
            command=self.choose_color,
            fg_color=self.series.color,
            width=120
        )
        self.color_button.grid(row=0, column=0, padx=5)
        
        # Color presets
        preset_frame = ctk.CTkFrame(color_frame)
        preset_frame.grid(row=0, column=1, padx=(10, 0))
        
        colors = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#8B5CF6", "#10B981"]
        for i, color in enumerate(colors):
            btn = ctk.CTkButton(
                preset_frame,
                text="",
                width=25,
                height=25,
                fg_color=color,
                command=lambda c=color: self.set_color(c)
            )
            btn.grid(row=0, column=i, padx=1)
        
        # Line style
        ctk.CTkLabel(style_frame, text="Line Style:", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.line_style_var = tk.StringVar(value=self.series.line_style)
        self.line_style_combo = ctk.CTkComboBox(
            style_frame,
            variable=self.line_style_var,
            values=["-", "--", "-.", ":", "None"],
            command=self.on_style_change,
            width=150
        )
        self.line_style_combo.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Line width
        ctk.CTkLabel(style_frame, text="Line Width:", font=ctk.CTkFont(weight="bold")).grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        self.line_width_var = tk.DoubleVar(value=self.series.line_width)
        self.line_width_slider = ctk.CTkSlider(
            style_frame,
            from_=0.5,
            to=5.0,
            variable=self.line_width_var,
            command=self.on_style_change,
            width=200
        )
        self.line_width_slider.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        # Marker options
        marker_frame = ctk.CTkFrame(tab_frame)
        marker_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        marker_frame.grid_columnconfigure(1, weight=1)
        
        # Header
        header_label = ctk.CTkLabel(
            marker_frame,
            text="📍 Markers & Points",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Marker style
        ctk.CTkLabel(marker_frame, text="Marker Style:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.marker_var = tk.StringVar(value=self.series.marker or "None")
        self.marker_combo = ctk.CTkComboBox(
            marker_frame,
            variable=self.marker_var,
            values=["None", "o", "s", "^", "v", "<", ">", "D", "*", "+", "x"],
            command=self.on_style_change,
            width=150
        )
        self.marker_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

    def create_analysis_tab(self):
        """Create analysis options tab"""
        tab_frame = self.config_notebook.tab("📊 Analysis")
        
        # Statistical Options
        stats_frame = ctk.CTkFrame(tab_frame)
        stats_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # Header
        header_label = ctk.CTkLabel(
            stats_frame,
            text="📈 Statistical Analysis",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Show trend
        self.show_trend_var = tk.BooleanVar(value=self.series.show_trend)
        self.show_trend_check = ctk.CTkCheckBox(
            stats_frame,
            text="Show Trend Line",
            variable=self.show_trend_var,
            command=self.on_analysis_change
        )
        self.show_trend_check.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        # Moving average
        self.show_ma_var = tk.BooleanVar(value=self.series.show_moving_average)
        self.show_ma_check = ctk.CTkCheckBox(
            stats_frame,
            text="Show Moving Average",
            variable=self.show_ma_var,
            command=self.on_analysis_change
        )
        self.show_ma_check.grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        # Show peaks
        self.show_peaks_var = tk.BooleanVar(value=self.series.show_peaks)
        self.show_peaks_check = ctk.CTkCheckBox(
            stats_frame,
            text="Highlight Peaks",
            variable=self.show_peaks_var,
            command=self.on_analysis_change
        )
        self.show_peaks_check.grid(row=3, column=0, sticky="w", padx=5, pady=5)

    def create_advanced_tab(self):
        """Create advanced options tab"""
        tab_frame = self.config_notebook.tab("⚙️ Advanced")
        
        # Data Processing
        processing_frame = ctk.CTkFrame(tab_frame)
        processing_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        # Header
        header_label = ctk.CTkLabel(
            processing_frame,
            text="⚙️ Data Processing",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        header_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Missing data handling
        ctk.CTkLabel(processing_frame, text="Missing Data:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.missing_data_var = tk.StringVar(value=self.series.missing_data_method)
        self.missing_data_combo = ctk.CTkComboBox(
            processing_frame,
            variable=self.missing_data_var,
            values=["skip", "interpolate", "zero", "forward_fill", "backward_fill"],
            command=self.on_config_change,
            width=150
        )
        self.missing_data_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

    def create_preview_panel(self, parent):
        """Create live preview panel"""
        preview_frame = ctk.CTkFrame(parent)
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(1, weight=1)
        
        # Header with controls
        header_frame = ctk.CTkFrame(preview_frame)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 Live Preview",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w", padx=5)
        
        # Preview controls
        control_frame = ctk.CTkFrame(header_frame)
        control_frame.grid(row=0, column=1, sticky="e", padx=5)
        
        self.auto_update_var = tk.BooleanVar(value=True)
        self.auto_update_check = ctk.CTkCheckBox(
            control_frame,
            text="Auto Update",
            variable=self.auto_update_var
        )
        self.auto_update_check.grid(row=0, column=0, padx=5)
        
        self.update_button = ctk.CTkButton(
            control_frame,
            text="🔄 Update",
            command=self.update_preview,
            width=80
        )
        self.update_button.grid(row=0, column=1, padx=5)
        
        # Create matplotlib preview
        self.create_matplotlib_preview(preview_frame)

    def create_matplotlib_preview(self, parent):
        """Create matplotlib preview canvas"""
        # Create figure
        self.preview_fig, self.preview_ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.preview_fig.patch.set_facecolor('#2b2b2b')
        self.preview_ax.set_facecolor('#2b2b2b')
        
        # Create canvas
        self.preview_canvas = FigureCanvasTkAgg(self.preview_fig, parent)
        self.preview_canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def create_action_panel(self, parent):
        """Create action buttons panel"""
        action_frame = ctk.CTkFrame(parent)
        action_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        # Buttons
        button_frame = ctk.CTkFrame(action_frame)
        button_frame.pack(side="right", padx=10, pady=10)
        
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self.cancel,
            width=100
        )
        self.cancel_button.pack(side="left", padx=(0, 5))
        
        self.apply_button = ctk.CTkButton(
            button_frame,
            text="✅ Apply",
            command=self.apply,
            width=100
        )
        self.apply_button.pack(side="left", padx=5)
        
        self.ok_button = ctk.CTkButton(
            button_frame,
            text="💾 OK",
            command=self.ok,
            width=100,
            fg_color="green"
        )
        self.ok_button.pack(side="left", padx=(5, 0))

    def analyze_data(self):
        """Perform intelligent data analysis"""
        if not self.file_data:
            return
        
        # Update recommendations based on column selection
        self.update_column_recommendations()
        
        # Update data quality display
        self.update_data_quality()

    def update_column_recommendations(self):
        """Update intelligent column recommendations"""
        if not self.file_data:
            return
        
        x_col = self.x_column_var.get()
        y_col = self.y_column_var.get()
        
        # X-axis recommendations
        x_rec = "💡 "
        if x_col in self.file_data.datetime_columns:
            x_rec += "Perfect for time series analysis!"
        elif x_col in self.file_data.numeric_columns:
            x_rec += "Good numeric column for correlation analysis."
        else:
            x_rec += "Consider using a datetime or numeric column."
        
        self.x_recommendations.configure(text=x_rec)
        
        # Y-axis recommendations
        y_rec = "💡 "
        if y_col in self.file_data.numeric_columns:
            stats = self.file_data.get_column_stats(y_col)
            if stats.get('missing', 0) == 0:
                y_rec += f"Excellent! Complete data, range: {stats.get('min', 0):.2f} to {stats.get('max', 0):.2f}"
            else:
                y_rec += f"Good choice, {stats.get('missing', 0)} missing values to handle."
        else:
            y_rec += "Recommend selecting a numeric column for measurement data."
        
        self.y_recommendations.configure(text=y_rec)

    def update_data_quality(self):
        """Update data quality analysis display"""
        if not self.file_data:
            return
        
        x_col = self.x_column_var.get()
        y_col = self.y_column_var.get()
        
        quality_info = "📊 Data Quality Analysis\n\n"
        
        if x_col and y_col:
            # Get data slice
            start_idx = self.start_var.get()
            end_idx = self.end_var.get()
            
            if start_idx < len(self.file_data.data) and end_idx <= len(self.file_data.data):
                data_slice = self.file_data.data.iloc[start_idx:end_idx]
                
                if x_col in data_slice.columns and y_col in data_slice.columns:
                    x_data = data_slice[x_col]
                    y_data = data_slice[y_col]
                    
                    quality_info += f"Selected Range: {end_idx - start_idx} rows\n"
                    quality_info += f"X-column ({x_col}): {x_data.count()}/{len(x_data)} valid values\n"
                    quality_info += f"Y-column ({y_col}): {y_data.count()}/{len(y_data)} valid values\n\n"
                    
                    if pd.api.types.is_numeric_dtype(y_data):
                        quality_info += f"Y-data statistics:\n"
                        quality_info += f"  Mean: {y_data.mean():.3f}\n"
                        quality_info += f"  Std: {y_data.std():.3f}\n"
                        quality_info += f"  Range: {y_data.min():.3f} to {y_data.max():.3f}\n"
        else:
            quality_info += "Select both X and Y columns to see quality metrics."
        
        self.quality_text.delete("1.0", tk.END)
        self.quality_text.insert("1.0", quality_info)

    def populate_fields(self):
        """Populate fields from series configuration"""
        if not self.series:
            return
        
        # Update all variables
        self.name_var.set(self.series.name)
        if self.file_data and self.series.x_column in self.file_data.columns:
            self.x_column_var.set(self.series.x_column)
        if self.file_data and self.series.y_column in self.file_data.columns:
            self.y_column_var.set(self.series.y_column)
        
        self.start_var.set(self.series.start_index or 0)
        self.end_var.set(self.series.end_index or (len(self.file_data.data) if self.file_data else 1000))
        
        # Style variables
        self.color_var.set(self.series.color)
        self.line_style_var.set(self.series.line_style)
        self.line_width_var.set(self.series.line_width)
        self.marker_var.set(self.series.marker or "None")
        
        # Analysis variables
        self.show_trend_var.set(self.series.show_trend)
        self.show_ma_var.set(self.series.show_moving_average)
        self.show_peaks_var.set(self.series.show_peaks)
        
        # Advanced variables
        self.missing_data_var.set(self.series.missing_data_method)

    def update_preview(self):
        """Update the live preview"""
        if not self.file_data or not self.auto_update_var.get():
            return
        
        try:
            # Clear previous plot
            self.preview_ax.clear()
            
            # Get current configuration
            x_col = self.x_column_var.get()
            y_col = self.y_column_var.get()
            
            if not x_col or not y_col:
                self.preview_ax.text(0.5, 0.5, "Select X and Y columns\nto see preview", 
                                   ha='center', va='center', transform=self.preview_ax.transAxes,
                                   color='white', fontsize=12)
                self.preview_canvas.draw()
                return
            
            # Get data
            start_idx = self.start_var.get()
            end_idx = self.end_var.get()
            
            if start_idx >= len(self.file_data.data) or end_idx > len(self.file_data.data):
                self.preview_ax.text(0.5, 0.5, "Invalid data range", 
                                   ha='center', va='center', transform=self.preview_ax.transAxes,
                                   color='red', fontsize=12)
                self.preview_canvas.draw()
                return
            
            data_slice = self.file_data.data.iloc[start_idx:end_idx]
            
            # Handle X data (Index vs column)
            if x_col == 'Index':
                x_data = np.arange(start_idx, end_idx)
            else:
                x_data = data_slice[x_col]
                
            # Handle Y data (Index vs column)
            if y_col == 'Index':
                y_data = np.arange(start_idx, end_idx)
            else:
                y_data = data_slice[y_col]
            
            # Convert to numeric if needed (skip for Index which is already numeric)
            if x_col != 'Index' and pd.api.types.is_object_dtype(x_data):
                x_data = pd.to_numeric(x_data, errors='coerce')
            if y_col != 'Index' and pd.api.types.is_object_dtype(y_data):
                y_data = pd.to_numeric(y_data, errors='coerce')
            
            # Handle different data types for masking
            if x_col == 'Index':
                # For Index, only check y_data for NaN
                mask = ~pd.isna(y_data)
                x_clean = x_data[mask] if hasattr(x_data, '__getitem__') else x_data
                y_clean = y_data[mask]
            else:
                # For column data, check both x and y
                mask = ~(pd.isna(x_data) | pd.isna(y_data))
                x_clean = x_data[mask]
                y_clean = y_data[mask]
            
            if len(x_clean) == 0:
                self.preview_ax.text(0.5, 0.5, "No valid data to plot", 
                                   ha='center', va='center', transform=self.preview_ax.transAxes,
                                   color='orange', fontsize=12)
                self.preview_canvas.draw()
                return
            
            # Plot main series
            plot_kwargs = {
                'color': self.color_var.get(),
                'linestyle': self.line_style_var.get() if self.line_style_var.get() != "None" else '-',
                'linewidth': self.line_width_var.get(),
                'label': self.name_var.get()
            }
            
            if self.marker_var.get() != "None":
                plot_kwargs['marker'] = self.marker_var.get()
                plot_kwargs['markersize'] = 4
            
            self.preview_ax.plot(x_clean, y_clean, **plot_kwargs)
            
            # Add analysis overlays
            if self.show_trend_var.get() and len(x_clean) > 2:
                try:
                    z = np.polyfit(x_clean, y_clean, 1)
                    p = np.poly1d(z)
                    self.preview_ax.plot(x_clean, p(x_clean), '--', 
                                       color=self.color_var.get(), alpha=0.7, label='Trend')
                except:
                    pass
            
            if self.show_ma_var.get() and len(y_clean) > 10:
                try:
                    window = min(20, len(y_clean) // 4)
                    ma = pd.Series(y_clean).rolling(window=window).mean()
                    self.preview_ax.plot(x_clean, ma, ':', 
                                       color=self.color_var.get(), alpha=0.8, label='Moving Avg')
                except:
                    pass
            
            # Styling
            self.preview_ax.set_xlabel(x_col, color='white')
            self.preview_ax.set_ylabel(y_col, color='white')
            self.preview_ax.set_title(f"Preview: {self.name_var.get()}", color='white')
            self.preview_ax.tick_params(colors='white')
            self.preview_ax.grid(True, alpha=0.3)
            self.preview_ax.legend()
            
            # Update canvas
            self.preview_canvas.draw()
            
        except Exception as e:
            logger.error(f"Preview update error: {e}")
            self.preview_ax.clear()
            self.preview_ax.text(0.5, 0.5, f"Preview Error:\n{str(e)}", 
                               ha='center', va='center', transform=self.preview_ax.transAxes,
                               color='red', fontsize=10)
            self.preview_canvas.draw()

    # Event handlers
    def on_config_change(self, event=None):
        """Handle configuration changes"""
        if self.auto_update_var.get():
            self.update_preview()
            self.update_data_quality()

    def on_column_change(self, value=None):
        """Handle column selection changes"""
        self.update_column_recommendations()
        self.on_config_change()

    def on_style_change(self, value=None):
        """Handle style changes"""
        self.on_config_change()

    def on_analysis_change(self):
        """Handle analysis option changes"""
        self.on_config_change()

    def on_range_change(self, event=None):
        """Handle range changes"""
        self.on_config_change()

    def show_column_info(self, column_name):
        """Show detailed column information"""
        if not column_name or not self.file_data:
            return
        
        stats = self.file_data.get_column_stats(column_name)
        info = f"Column: {column_name}\n\n"
        info += f"Data Type: {stats.get('dtype', 'Unknown')}\n"
        info += f"Valid Values: {stats.get('count', 0)}\n"
        info += f"Missing Values: {stats.get('missing', 0)}\n"
        info += f"Unique Values: {stats.get('unique', 0)}\n"
        
        if 'mean' in stats:
            info += f"\nStatistics:\n"
            info += f"Mean: {stats['mean']:.3f}\n"
            info += f"Std Dev: {stats['std']:.3f}\n"
            info += f"Min: {stats['min']:.3f}\n"
            info += f"Max: {stats['max']:.3f}\n"
        
        messagebox.showinfo("Column Information", info)

    def choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(title="Choose series color", color=self.color_var.get())
        if color[1]:  # User didn't cancel
            self.set_color(color[1])

    def set_color(self, color):
        """Set series color"""
        self.color_var.set(color)
        self.color_button.configure(fg_color=color)
        self.on_style_change()

    # Quick range selection methods
    def select_all_data(self):
        """Select all available data"""
        self.start_var.set(0)
        self.end_var.set(len(self.file_data.data) if self.file_data else 1000)
        self.on_range_change()

    def select_first_100(self):
        """Select first 100 rows"""
        self.start_var.set(0)
        self.end_var.set(min(100, len(self.file_data.data) if self.file_data else 100))
        self.on_range_change()

    def select_last_100(self):
        """Select last 100 rows"""
        if self.file_data:
            total = len(self.file_data.data)
            self.start_var.set(max(0, total - 100))
            self.end_var.set(total)
        else:
            self.start_var.set(900)
            self.end_var.set(1000)
        self.on_range_change()

    def auto_detect_range(self):
        """Automatically detect optimal data range"""
        if not self.file_data:
            return
        
        # Simple auto-detection: skip header rows with text, find data end
        y_col = self.y_column_var.get()
        if y_col and y_col in self.file_data.columns:
            data = self.file_data.data[y_col]
            
            # Find first valid numeric value
            start_idx = 0
            for i, val in enumerate(data):
                if pd.api.types.is_numeric_dtype(type(val)) and not pd.isna(val):
                    start_idx = i
                    break
            
            # Find last valid numeric value
            end_idx = len(data)
            for i in range(len(data) - 1, -1, -1):
                if pd.api.types.is_numeric_dtype(type(data.iloc[i])) and not pd.isna(data.iloc[i]):
                    end_idx = i + 1
                    break
            
            self.start_var.set(start_idx)
            self.end_var.set(end_idx)
            self.on_range_change()

    def center_window(self):
        """Center dialog on parent window"""
        self.update_idletasks()
        
        # Get window size
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        pos_x = parent_x + (parent_width - window_width) // 2
        pos_y = parent_y + (parent_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    def apply(self):
        """Apply current configuration to series"""
        self.update_series_from_fields()

    def ok(self):
        """Apply and close dialog"""
        self.update_series_from_fields()
        self.result = self.series
        self.destroy()

    def cancel(self):
        """Cancel and close dialog"""
        self.result = None
        self.destroy()

    def update_series_from_fields(self):
        """Update series configuration from UI fields"""
        # Basic configuration
        self.series.name = self.name_var.get()
        self.series.x_column = self.x_column_var.get()
        self.series.y_column = self.y_column_var.get()
        self.series.start_index = self.start_var.get()
        self.series.end_index = self.end_var.get()
        
        # Style configuration
        self.series.color = self.color_var.get()
        self.series.line_style = self.line_style_var.get()
        self.series.line_width = self.line_width_var.get()
        self.series.marker = self.marker_var.get() if self.marker_var.get() != "None" else None
        
        # Analysis configuration
        self.series.show_trend = self.show_trend_var.get()
        self.series.show_trendline = self.show_trend_var.get()  # Legacy compatibility
        self.series.show_moving_average = self.show_ma_var.get()
        self.series.show_peaks = self.show_peaks_var.get()
        
        # Advanced configuration
        self.series.missing_data_method = self.missing_data_var.get()
        
        # Update file ID if needed
        if self.file_data:
            self.series.file_id = self.file_data.id


def show_smart_series_dialog(parent, series: SeriesConfig = None, file_data: FileData = None) -> Optional[SeriesConfig]:
    """
    Show the smart series configuration dialog
    
    Args:
        parent: Parent window
        series: Existing series to edit (None for new series)
        file_data: Associated file data
        
    Returns:
        Configured SeriesConfig or None if cancelled
    """
    try:
        dialog = SmartSeriesDialog(parent, series, file_data)
        parent.wait_window(dialog)
        return dialog.result
    except Exception as e:
        import traceback
        error_msg = f"Error showing smart series dialog: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        messagebox.showerror("Error", f"Failed to open series configuration:\n{str(e)[:200]}...")
        return None
