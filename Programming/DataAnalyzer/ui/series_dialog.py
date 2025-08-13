#!/usr/bin/env python3
"""
Series Configuration Dialog - Unified implementation
Consolidated from enhanced_series_dialog_fixed.py, smart_series_dialog.py, and dialogs.py
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import customtkinter as ctk
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, Dict, List, Any, Callable
import logging

from models.data_models import FileData, SeriesConfig
from core.ui_factory import UIFactory, DualRangeSlider
from core.data_utils import DataProcessor, DataValidator
from config.constants import PlotTypes, MissingDataMethods, TrendTypes

logger = logging.getLogger(__name__)


class SeriesDialog:
    """Unified series configuration dialog with advanced features"""
    
    def __init__(self, parent, files: Dict[str, FileData], 
                 series: Optional[SeriesConfig] = None, mode: str = "create"):
        self.parent = parent
        self.files = files
        self.series = series
        self.mode = mode  # "create" or "edit"
        self.result = None
        
        # Create dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(f"{'Edit' if mode == 'edit' else 'Create'} Series")
        self.dialog.geometry("1200x800")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Initialize variables
        self._init_variables()
        
        # Create UI
        self._create_widgets()
        
        # Load existing series if editing
        if mode == "edit" and series:
            self._load_series_config()
            
        # Get screen dimensions and set responsive size
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        
        # Use 80% of screen size, but cap at reasonable maximum
        dialog_width = min(1200, int(screen_width * 0.8))
        dialog_height = min(800, int(screen_height * 0.8))
        
        # Center dialog with responsive size
        UIFactory.center_window(self.dialog, dialog_width, dialog_height)
        
        # Initial preview update
        self._update_preview()
    
    def _init_variables(self):
        """Initialize dialog variables"""
        # Basic configuration
        self.name_var = tk.StringVar(value=self.series.name if self.series else "New Series")
        self.file_var = tk.StringVar()
        self.x_column_var = tk.StringVar()
        self.y_column_var = tk.StringVar()
        
        # Data range
        self.start_var = tk.IntVar(value=0)
        self.end_var = tk.IntVar(value=1000)
        
        # Visual properties
        self.color_var = tk.StringVar(value=self.series.color if self.series else "#1f77b4")
        self.plot_type_var = tk.StringVar(value=self.series.plot_type if self.series else "line")
        self.line_style_var = tk.StringVar(value=self.series.line_style if self.series else "-")
        self.line_width_var = tk.DoubleVar(value=self.series.line_width if self.series else 1.0)
        self.marker_var = tk.StringVar(value=self.series.marker if self.series else "")
        self.marker_size_var = tk.DoubleVar(value=self.series.marker_size if self.series else 6.0)
        self.alpha_var = tk.DoubleVar(value=self.series.alpha if self.series else 1.0)
        
        # Data processing
        self.smoothing_var = tk.BooleanVar(value=False)
        self.smoothing_window_var = tk.IntVar(value=5)
        self.missing_method_var = tk.StringVar(value="drop")
        
        # Analysis options
        self.show_trend_var = tk.BooleanVar(value=False)
        self.trend_type_var = tk.StringVar(value="linear")
        self.show_stats_var = tk.BooleanVar(value=False)
        self.show_peaks_var = tk.BooleanVar(value=False)
        self.show_legend_var = tk.BooleanVar(value=True)
        
        # Set initial file if only one available
        if len(self.files) == 1:
            self.file_var.set(list(self.files.keys())[0])
            self._on_file_change(list(self.files.keys())[0])
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel - Configuration
        config_panel = ctk.CTkScrollableFrame(main_frame, width=400)
        config_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Right panel - Preview
        preview_panel = ctk.CTkFrame(main_frame)
        preview_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Create configuration sections
        self._create_basic_section(config_panel)
        self._create_data_section(config_panel)
        self._create_visual_section(config_panel)
        self._create_processing_section(config_panel)
        self._create_analysis_section(config_panel)
        
        # Create preview panel
        self._create_preview_panel(preview_panel)
        
        # Create button panel
        self._create_button_panel()
    
    def _create_basic_section(self, parent):
        """Create basic configuration section"""
        section = UIFactory.create_labeled_frame(parent, "Basic Configuration")
        section.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)
        
        # Series name
        ctk.CTkLabel(content, text="Series Name:").pack(anchor="w", pady=2)
        name_entry = ctk.CTkEntry(content, textvariable=self.name_var, width=300)
        name_entry.pack(fill="x", pady=2)
        name_entry.bind("<KeyRelease>", lambda e: self._update_preview())
        
        # File selection
        ctk.CTkLabel(content, text="Data File:").pack(anchor="w", pady=(10, 2))
        file_combo = ctk.CTkComboBox(
            content,
            variable=self.file_var,
            values=list(self.files.keys()),
            command=self._on_file_change,
            width=300
        )
        file_combo.pack(fill="x", pady=2)
    
    def _create_data_section(self, parent):
        """Create data selection section"""
        section = UIFactory.create_labeled_frame(parent, "Data Selection")
        section.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)
        
        # Column selection
        columns_frame = ctk.CTkFrame(content)
        columns_frame.pack(fill="x", pady=5)
        columns_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(columns_frame, text="X Column:").grid(row=0, column=0, sticky="w", padx=5)
        self.x_combo = ctk.CTkComboBox(
            columns_frame,
            variable=self.x_column_var,
            command=lambda x: self._update_preview(),
            width=200
        )
        self.x_combo.grid(row=0, column=1, sticky="ew", padx=5)
        
        ctk.CTkLabel(columns_frame, text="Y Column:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.y_combo = ctk.CTkComboBox(
            columns_frame,
            variable=self.y_column_var,
            command=lambda x: self._update_preview(),
            width=200
        )
        self.y_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Data range selection
        ctk.CTkLabel(content, text="Data Range:").pack(anchor="w", pady=(10, 2))
        self.range_slider = DualRangeSlider(
            content,
            from_=0,
            to=1000,
            start_var=self.start_var,
            end_var=self.end_var,
            start_command=lambda x: self._update_range_display(),
            end_command=lambda x: self._update_range_display()
        )
        self.range_slider.pack(fill="x", pady=5)
        
        # Timestamp display frame
        timestamp_frame = ctk.CTkFrame(content)
        timestamp_frame.pack(fill="x", pady=2)
        timestamp_frame.grid_columnconfigure(0, weight=1)
        timestamp_frame.grid_columnconfigure(1, weight=1)
        
        # Start and end timestamp labels
        self.start_timestamp_label = ctk.CTkLabel(timestamp_frame, text="Start: Index 0", font=("Arial", 10))
        self.start_timestamp_label.grid(row=0, column=0, sticky="w", padx=5)
        
        self.end_timestamp_label = ctk.CTkLabel(timestamp_frame, text="End: Index 1000", font=("Arial", 10))
        self.end_timestamp_label.grid(row=0, column=1, sticky="e", padx=5)
    
    def _create_visual_section(self, parent):
        """Create visual properties section"""
        section = UIFactory.create_labeled_frame(parent, "Visual Properties")
        section.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)
        
        # Plot type
        type_frame = ctk.CTkFrame(content)
        type_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(type_frame, text="Plot Type:", width=100).pack(side="left")
        ctk.CTkComboBox(
            type_frame,
            variable=self.plot_type_var,
            values=["line", "scatter", "both", "bar", "area", "step"],
            command=lambda x: self._update_preview(),
            width=150
        ).pack(side="left", padx=5)
        
        # Color selection
        color_frame = ctk.CTkFrame(content)
        color_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(color_frame, text="Color:", width=100).pack(side="left")
        self.color_button = ctk.CTkButton(
            color_frame,
            text="",
            command=self._choose_color,
            width=50,
            fg_color=self.color_var.get()
        )
        self.color_button.pack(side="left", padx=5)
        
        # Line style
        line_frame = ctk.CTkFrame(content)
        line_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(line_frame, text="Line Style:", width=100).pack(side="left")
        ctk.CTkComboBox(
            line_frame,
            variable=self.line_style_var,
            values=["-", "--", "-.", ":", ""],
            command=lambda x: self._update_preview(),
            width=100
        ).pack(side="left", padx=5)
        
        # Line width
        width_frame = ctk.CTkFrame(content)
        width_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(width_frame, text="Line Width:", width=100).pack(side="left")
        ctk.CTkSlider(
            width_frame,
            from_=0.5,
            to=5.0,
            variable=self.line_width_var,
            command=lambda x: self._update_preview(),
            width=150
        ).pack(side="left", padx=5)
        
        # Marker
        marker_frame = ctk.CTkFrame(content)
        marker_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(marker_frame, text="Marker:", width=100).pack(side="left")
        ctk.CTkComboBox(
            marker_frame,
            variable=self.marker_var,
            values=["", "o", "s", "^", "v", "D", "*", "+", "x"],
            command=lambda x: self._update_preview(),
            width=100
        ).pack(side="left", padx=5)
        
        # Alpha
        alpha_frame = ctk.CTkFrame(content)
        alpha_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(alpha_frame, text="Opacity:", width=100).pack(side="left")
        ctk.CTkSlider(
            alpha_frame,
            from_=0.1,
            to=1.0,
            variable=self.alpha_var,
            command=lambda x: self._update_preview(),
            width=150
        ).pack(side="left", padx=5)
    
    def _create_processing_section(self, parent):
        """Create data processing section"""
        section = UIFactory.create_labeled_frame(parent, "Data Processing")
        section.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)
        
        # Smoothing
        smooth_frame = ctk.CTkFrame(content)
        smooth_frame.pack(fill="x", pady=2)
        ctk.CTkCheckBox(
            smooth_frame,
            text="Apply Smoothing",
            variable=self.smoothing_var,
            command=self._update_preview
        ).pack(side="left")
        
        ctk.CTkLabel(smooth_frame, text="Window:").pack(side="left", padx=(20, 5))
        ctk.CTkEntry(
            smooth_frame,
            textvariable=self.smoothing_window_var,
            width=60
        ).pack(side="left")
        
        # Missing data handling
        missing_frame = ctk.CTkFrame(content)
        missing_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(missing_frame, text="Missing Data:", width=100).pack(side="left")
        ctk.CTkComboBox(
            missing_frame,
            variable=self.missing_method_var,
            values=["drop", "interpolate", "forward_fill", "zero_fill"],
            command=lambda x: self._update_preview(),
            width=120
        ).pack(side="left", padx=5)
    
    def _create_analysis_section(self, parent):
        """Create analysis options section"""
        section = UIFactory.create_labeled_frame(parent, "Analysis Options")
        section.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)
        
        # Trend line
        trend_frame = ctk.CTkFrame(content)
        trend_frame.pack(fill="x", pady=2)
        ctk.CTkCheckBox(
            trend_frame,
            text="Show Trend Line",
            variable=self.show_trend_var,
            command=self._update_preview
        ).pack(side="left")
        
        ctk.CTkComboBox(
            trend_frame,
            variable=self.trend_type_var,
            values=["linear", "polynomial"],
            command=lambda x: self._update_preview(),
            width=100
        ).pack(side="right")
        
        # Statistics
        ctk.CTkCheckBox(
            content,
            text="Show Statistics",
            variable=self.show_stats_var,
            command=self._update_preview
        ).pack(anchor="w", pady=2)
        
        # Peak detection
        ctk.CTkCheckBox(
            content,
            text="Mark Peaks",
            variable=self.show_peaks_var,
            command=self._update_preview
        ).pack(anchor="w", pady=2)
        
        # Legend
        ctk.CTkCheckBox(
            content,
            text="Show in Legend",
            variable=self.show_legend_var,
            command=self._update_preview
        ).pack(anchor="w", pady=2)
    
    def _create_preview_panel(self, parent):
        """Create preview panel"""
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(parent, text="📊 Live Preview", font=("", 16, "bold"))
        title.grid(row=0, column=0, pady=10)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=80)
        self.ax = self.figure.add_subplot(111)
        
        # Create canvas
        canvas_frame = ctk.CTkFrame(parent)
        canvas_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        self.canvas = UIFactory.create_matplotlib_canvas(canvas_frame, self.figure)
        
        # Info label
        self.info_label = ctk.CTkLabel(parent, text="", text_color="gray")
        self.info_label.grid(row=2, column=0, pady=5)
    
    def _create_button_panel(self):
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
        
        # Reset button (only for edit mode)
        if self.mode == "edit":
            ctk.CTkButton(
                button_frame,
                text="Reset",
                command=self._load_series_config,
                width=100
            ).pack(side="right", padx=5)
    
    def _on_file_change(self, file_key: str):
        """Handle file selection change"""
        # Get file data by key (could be filename or file_id)
        file_data = None
        
        # First try direct key lookup
        if file_key in self.files:
            file_data = self.files[file_key]
        else:
            # Fall back to searching by filename
            for f in self.files.values():
                if f.filename == file_key:
                    file_data = f
                    break
        
        if not file_data:
            logger.warning(f"Could not find file data for key: {file_key}")
            return
        
        # Update column lists - use the data attribute correctly
        df = file_data.data if hasattr(file_data, 'data') else file_data.df
        columns = ["Index"] + list(df.columns)
        
        if hasattr(self, 'x_combo'):
            self.x_combo.configure(values=columns)
            self.y_combo.configure(values=columns[1:])  # Exclude Index for Y
            
            # Set defaults if not already set
            if not self.x_column_var.get():
                self.x_combo.set(columns[0])
            
            # Find numeric columns
            numeric_cols = []
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    numeric_cols.append(col)
                    
            if numeric_cols and not self.y_column_var.get():
                self.y_combo.set(numeric_cols[0])
            
            # Update range slider
            data_length = len(df)
            if hasattr(self, 'range_slider'):
                self.range_slider.configure_range(from_=0, to=data_length-1)
                self.end_var.set(min(1000, data_length))
            
            # Update both range display and preview
            if hasattr(self, 'start_timestamp_label'):
                self._update_range_display()
            else:
                self._update_preview()
    
    def _update_range_display(self):
        """Update the timestamp display for range slider"""
        try:
            # Get current file data
            file_key = self.file_var.get()
            if not file_key:
                self.start_timestamp_label.configure(text=f"Start: Index {self.start_var.get()}")
                self.end_timestamp_label.configure(text=f"End: Index {self.end_var.get()}")
                self._update_preview()
                return
            
            # Get file data
            file_data = None
            if file_key in self.files:
                file_data = self.files[file_key]
            else:
                for f in self.files.values():
                    if f.filename == file_key:
                        file_data = f
                        break
            
            if not file_data:
                self.start_timestamp_label.configure(text=f"Start: Index {self.start_var.get()}")
                self.end_timestamp_label.configure(text=f"End: Index {self.end_var.get()}")
                self._update_preview()
                return
            
            # Get dataframe
            df = file_data.data if hasattr(file_data, 'data') else file_data.df
            start_idx = self.start_var.get()
            end_idx = self.end_var.get()
            
            # Check if we have a timestamp column
            x_col = self.x_column_var.get()
            if x_col and x_col in df.columns and x_col.lower() in ['timestamp', 'time', 'datetime']:
                try:
                    # Get timestamp values at start and end indices
                    start_time = df.iloc[start_idx][x_col] if start_idx < len(df) else "N/A"
                    end_time = df.iloc[min(end_idx-1, len(df)-1)][x_col] if end_idx > 0 else "N/A"
                    
                    self.start_timestamp_label.configure(text=f"Start: {start_time}")
                    self.end_timestamp_label.configure(text=f"End: {end_time}")
                except:
                    self.start_timestamp_label.configure(text=f"Start: Index {start_idx}")
                    self.end_timestamp_label.configure(text=f"End: Index {end_idx}")
            else:
                self.start_timestamp_label.configure(text=f"Start: Index {start_idx}")
                self.end_timestamp_label.configure(text=f"End: Index {end_idx}")
                
        except Exception as e:
            logger.error(f"Error updating range display: {e}")
            self.start_timestamp_label.configure(text=f"Start: Index {self.start_var.get()}")
            self.end_timestamp_label.configure(text=f"End: Index {self.end_var.get()}")
        
        # Update preview after range display
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
            
            # Get data
            x_data, y_data = self._get_current_data()
            
            if len(y_data) == 0:
                self.ax.text(0.5, 0.5, "No valid data to plot", 
                           ha='center', va='center', transform=self.ax.transAxes)
                self.canvas.draw()
                return
            
            # Apply data processing
            if self.smoothing_var.get():
                window = min(self.smoothing_window_var.get(), len(y_data))
                if window >= 3:
                    y_data = DataProcessor.apply_smoothing(y_data, window)
            
            # Handle missing data
            x_data, y_data = DataProcessor.handle_missing_data(
                x_data, y_data, self.missing_method_var.get()
            )
            
            # Plot data
            plot_type = self.plot_type_var.get()
            color = self.color_var.get()
            label = self.name_var.get() if self.show_legend_var.get() else ""
            
            if plot_type == "line":
                self.ax.plot(
                    x_data, y_data,
                    color=color,
                    linestyle=self.line_style_var.get(),
                    linewidth=self.line_width_var.get(),
                    alpha=self.alpha_var.get(),
                    label=label
                )
            elif plot_type == "scatter":
                self.ax.scatter(
                    x_data, y_data,
                    color=color,
                    marker=self.marker_var.get() or "o",
                    s=self.marker_size_var.get() ** 2,
                    alpha=self.alpha_var.get(),
                    label=label
                )
            elif plot_type == "both":
                self.ax.plot(
                    x_data, y_data,
                    color=color,
                    linestyle=self.line_style_var.get(),
                    linewidth=self.line_width_var.get(),
                    marker=self.marker_var.get() or "o",
                    markersize=self.marker_size_var.get(),
                    alpha=self.alpha_var.get(),
                    label=label
                )
            elif plot_type == "bar":
                self.ax.bar(x_data, y_data, color=color, alpha=self.alpha_var.get(), label=label)
            elif plot_type == "area":
                self.ax.fill_between(x_data, y_data, color=color, alpha=self.alpha_var.get(), label=label)
            elif plot_type == "step":
                self.ax.step(x_data, y_data, color=color, linewidth=self.line_width_var.get(), 
                           alpha=self.alpha_var.get(), label=label)
            
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
            self.ax.set_xlabel(self.x_column_var.get())
            self.ax.set_ylabel(self.y_column_var.get())
            self.ax.set_title(f"Preview: {self.name_var.get()}")
            self.ax.grid(True, alpha=0.3)
            
            if self.show_legend_var.get() and label:
                self.ax.legend()
            
            # Update info
            self.info_label.configure(
                text=f"Points: {len(y_data)} | Range: [{np.min(y_data):.3g}, {np.max(y_data):.3g}]"
            )
            
            # Refresh canvas
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Error updating preview: {e}")
            self.info_label.configure(text=f"Error: {str(e)}", text_color="red")
    
    def _get_current_data(self) -> tuple:
        """Get current data based on selections"""
        try:
            # Get file
            file_key = self.file_var.get()
            if not file_key:
                return np.array([]), np.array([])
            
            # Get file data by key (could be filename or file_id)
            file_data = None
            if file_key in self.files:
                file_data = self.files[file_key]
            else:
                # Fall back to searching by filename
                for f in self.files.values():
                    if f.filename == file_key:
                        file_data = f
                        break
            
            if not file_data:
                logger.warning(f"Could not find file data for key: {file_key}")
                return np.array([]), np.array([])
            
            # Get columns
            x_col = self.x_column_var.get()
            y_col = self.y_column_var.get()
            
            if not x_col or not y_col:
                return np.array([]), np.array([])
            
            # Get data slice - use the correct data attribute
            df = file_data.data if hasattr(file_data, 'data') else file_data.df
            start_idx = self.start_var.get()
            end_idx = self.end_var.get()
            
            # Ensure indices are within bounds
            start_idx = max(0, start_idx)
            end_idx = min(len(df), end_idx)
            
            if start_idx >= end_idx:
                return np.array([]), np.array([])
                
            data_slice = df.iloc[start_idx:end_idx]
            
            # Get X data
            if x_col == "Index":
                x_data = np.arange(len(data_slice))
            else:
                x_data = data_slice[x_col].values
                if pd.api.types.is_object_dtype(x_data) or pd.api.types.is_string_dtype(x_data):
                    # Try to convert to datetime first, then to numeric
                    try:
                        x_data_dt = pd.to_datetime(x_data)
                        # Convert datetime to seconds since the first timestamp
                        x_data = (x_data_dt - x_data_dt.min()).dt.total_seconds().values
                    except:
                        # If datetime conversion fails, try numeric conversion
                        x_data = pd.to_numeric(x_data, errors='coerce').values
                
                # Ensure data is numeric numpy array
                x_data = np.asarray(x_data, dtype=float)
            
            # Get Y data
            y_data = data_slice[y_col].values
            if pd.api.types.is_object_dtype(y_data) or pd.api.types.is_string_dtype(y_data):
                try:
                    # Try datetime conversion first
                    y_data_dt = pd.to_datetime(y_data)
                    y_data = (y_data_dt - y_data_dt.min()).dt.total_seconds().values
                except:
                    # Fall back to numeric conversion
                    y_data = pd.to_numeric(y_data, errors='coerce').values
            
            # Ensure data is numeric numpy array
            y_data = np.asarray(y_data, dtype=float)
            
            return x_data, y_data
            
        except Exception as e:
            logger.error(f"Error getting current data: {e}")
            return np.array([]), np.array([])
    
    def _add_trend_line(self, x_data, y_data):
        """Add trend line to preview"""
        try:
            trend_y, stats = DataProcessor.calculate_trend_line(
                x_data, y_data, self.trend_type_var.get()
            )
            
            if len(trend_y) > 0:
                self.ax.plot(x_data, trend_y, 'r--', alpha=0.7, 
                           label=f"Trend (R² = {stats.get('r_squared', 0):.3f})")
        except Exception as e:
            logger.error(f"Error adding trend line: {e}")
    
    def _add_statistics(self, y_data):
        """Add statistics to preview"""
        try:
            stats = DataProcessor.calculate_basic_statistics(y_data)
            mean_val = stats['mean']
            std_val = stats['std']
            
            self.ax.axhline(mean_val, color='red', linestyle='--', alpha=0.5, 
                          label=f'Mean: {mean_val:.2e}')
            self.ax.axhline(mean_val + std_val, color='orange', linestyle=':', alpha=0.3)
            self.ax.axhline(mean_val - std_val, color='orange', linestyle=':', alpha=0.3)
        except Exception as e:
            logger.error(f"Error adding statistics: {e}")
    
    def _mark_peaks(self, x_data, y_data):
        """Mark peaks in preview"""
        try:
            peaks, _ = DataProcessor.find_peaks_in_data(y_data)
            if len(peaks) > 0:
                self.ax.scatter(x_data[peaks], y_data[peaks], 
                              color='red', marker='^', s=100, 
                              label=f'{len(peaks)} peaks')
        except Exception as e:
            logger.error(f"Error marking peaks: {e}")
    
    def _load_series_config(self):
        """Load existing series configuration"""
        if not self.series:
            return
        
        try:
            # Load basic settings
            self.name_var.set(self.series.name or "")
            self.color_var.set(self.series.color or "#1f77b4")
            self.plot_type_var.set(self.series.plot_type or "line")
            self.line_style_var.set(self.series.line_style or "-")
            self.line_width_var.set(self.series.line_width or 1.0)
            self.marker_var.set(self.series.marker or "")
            self.marker_size_var.set(self.series.marker_size or 6.0)
            self.alpha_var.set(self.series.alpha or 1.0)
            
            # Load file and columns
            if self.series.file_id:
                # Look for the file by ID (the key in the files dict should match the series.file_id)
                if self.series.file_id in self.files:
                    # Use the file_id as the key since that's how files_dict is structured
                    self.file_var.set(self.series.file_id)
                    self._on_file_change(self.series.file_id)
                else:
                    # Fallback: search by file_data.id 
                    for file_key, file_data in self.files.items():
                        if hasattr(file_data, 'id') and file_data.id == self.series.file_id:
                            self.file_var.set(file_key)
                            self._on_file_change(file_key)
                            break
                        elif hasattr(file_data, 'file_id') and file_data.file_id == self.series.file_id:
                            self.file_var.set(file_key)
                            self._on_file_change(file_key)
                            break
            
            self.x_column_var.set(self.series.x_column or "")
            self.y_column_var.set(self.series.y_column or "")
            
            # Load range
            self.start_var.set(self.series.start_index or 0)
            self.end_var.set(self.series.end_index or 1000)
            
            # Update preview
            self._update_preview()
            
        except Exception as e:
            logger.error(f"Error loading series config: {e}")
            messagebox.showerror("Error", f"Failed to load series configuration: {str(e)}")
    
    def _apply(self):
        """Apply configuration and close dialog"""
        try:
            # Validate inputs
            if not self.name_var.get().strip():
                messagebox.showerror("Error", "Please enter a series name")
                return
            
            if not self.file_var.get():
                messagebox.showerror("Error", "Please select a data file")
                return
            
            if not self.y_column_var.get():
                messagebox.showerror("Error", "Please select a Y column")
                return
            
            # Get file data using the file key (which is what's stored in file_var)
            file_key = self.file_var.get()
            file_data = self.files.get(file_key)
            
            if not file_data:
                # Fallback: try to find by filename in case the key is wrong
                for key, f in self.files.items():
                    if f.filename == file_key:
                        file_data = f
                        break
                        
            if not file_data:
                messagebox.showerror("Error", "Selected file not found")
                return
            
            # Validate data
            x_data, y_data = self._get_current_data()
            is_valid, error_msg = DataValidator.validate_data_compatibility(x_data, y_data)
            
            if not is_valid:
                messagebox.showerror("Error", f"Data validation failed: {error_msg}")
                return
            
            # Create or update series config
            if self.mode == "create" or not self.series:
                self.series = SeriesConfig()
            
            # Apply configuration
            self.series.name = self.name_var.get().strip()
            self.series.file_id = file_data.file_id
            self.series.x_column = self.x_column_var.get()
            self.series.y_column = self.y_column_var.get()
            self.series.start_index = self.start_var.get()
            self.series.end_index = self.end_var.get()
            self.series.color = self.color_var.get()
            self.series.plot_type = self.plot_type_var.get()
            self.series.line_style = self.line_style_var.get()
            self.series.line_width = self.line_width_var.get()
            self.series.marker = self.marker_var.get()
            self.series.marker_size = self.marker_size_var.get()
            self.series.alpha = self.alpha_var.get()
            
            # Store processing options
            self.series.smoothing = self.smoothing_var.get()
            self.series.smoothing_window = self.smoothing_window_var.get()
            self.series.missing_data_method = self.missing_method_var.get()
            
            self.result = self.series
            self.dialog.destroy()
            
        except Exception as e:
            logger.error(f"Error applying series configuration: {e}")
            messagebox.showerror("Error", f"Failed to apply configuration: {str(e)}")


def show_series_dialog(parent, files: Dict[str, FileData], 
                      series: Optional[SeriesConfig] = None, 
                      mode: str = "create") -> Optional[SeriesConfig]:
    """Show the series configuration dialog
    
    Args:
        parent: Parent widget
        files: Dictionary of available files
        series: Existing series config (for edit mode)
        mode: Dialog mode ("create" or "edit")
        
    Returns:
        SeriesConfig if successful, None if cancelled
    """
    dialog = SeriesDialog(parent, files, series, mode)
    parent.wait_window(dialog.dialog)
    return dialog.result
