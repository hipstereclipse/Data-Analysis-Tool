#!/usr/bin/env python3
"""
Dialog windows for user interaction
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import customtkinter as ctk
from typing import Optional, Dict, List, Any, Callable
import numpy as np
import pandas as pd
from pathlib import Path
import json

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from models.data_models import FileData, SeriesConfig, AnnotationConfig
from config.constants import UIConfig, MissingDataMethods, TrendTypes
from ui.components import CollapsibleFrame, ToolTip
from utils.helpers import detect_datetime_column


class SeriesDialog:
    """Dialog for creating/editing data series"""

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

    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel - Configuration
        left_panel = ctk.CTkScrollableFrame(main_frame, width=400)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        # Right panel - Preview
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        # Create sections
        self._create_basic_section(left_panel)
        self._create_data_section(left_panel)
        self._create_visual_section(left_panel)
        self._create_processing_section(left_panel)
        self._create_analysis_section(left_panel)

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

        # File selection
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

        if file_names:
            file_combo.set(file_names[0])
            self._on_file_change(file_names[0])

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
        # Find file data
        file_data = None
        for f in self.files.values():
            if f.filename == filename:
                file_data = f
                break

        if not file_data:
            return

        # Update column lists
        columns = ["Index"] + list(file_data.dataframe.columns)

        self.x_combo.configure(values=columns)
        self.y_combo.configure(values=columns[1:])  # Exclude Index for Y

        # Set defaults
        if not self.x_column_var.get():
            self.x_combo.set(columns[0])

        numeric_cols = file_data.get_numeric_columns()
        if numeric_cols and not self.y_column_var.get():
            self.y_combo.set(numeric_cols[0])

        # Update range sliders
        data_length = len(file_data.dataframe)
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
            df_slice = file_data.dataframe.iloc[start:end]

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
                from scipy.signal import savgol_filter
                window = min(self.smoothing_window_var.get(), len(y_data))
                if window >= 3 and len(y_data) > window:
                    y_data = savgol_filter(y_data, window, min(3, window - 1))

            # Plot data
            self.ax.plot(
                x_data, y_data,
                color=self.color_var.get(),
                linestyle=self.line_style_var.get(),
                linewidth=self.line_width_var.get(),
                marker=self.marker_var.get() if self.marker_var.get() else None,
                markersize=self.marker_size_var.get(),
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
            y_series = pd.Series(y_data).fillna(method='ffill')
            return x_data, y_series.values
        elif method == "backward":
            y_series = pd.Series(y_data).fillna(method='bfill')
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
        stats_text = f"Mean: {np.nanmean(y_data):.3g}\\n"
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
        from scipy.signal import find_peaks

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
        self.end_var.set(self.series.end_index or len(file_data.dataframe))

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

        # Set result and close
        self.result = series
        self.dialog.destroy()

    def _center_dialog(self):
        """Center dialog on screen"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")


class AnalysisDialog:
    """Dialog for data analysis"""

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

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Data Analysis Tools")
        self.dialog.geometry("1000x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create notebook for different analysis types
        self.notebook = ttk.Notebook(self.dialog)
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
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📊 Statistical Analysis")

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
        self.stat_results = tk.Text(tab, wrap="word", height=20)
        self.stat_results.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_vacuum_tab(self):
        """Create vacuum analysis tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="🎯 Vacuum Analysis")

        # Implementation similar to VacuumAnalysisDialog
        # Add vacuum-specific analysis tools

    def _create_comparison_tab(self):
        """Create series comparison tab"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📈 Comparison")

        # Implementation for comparing multiple series

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
        results = f"STATISTICAL ANALYSIS: {series_name}\\n"
        results += "=" * 50 + "\\n\\n"

        results += "Basic Statistics:\\n"
        results += f"  Count: {stats['count']}\\n"
        results += f"  Mean: {stats['mean']:.6f}\\n"
        results += f"  Median: {stats['median']:.6f}\\n"
        results += f"  Std Dev: {stats['std']:.6f}\\n"
        results += f"  Min: {stats['min']:.6f}\\n"
        results += f"  Max: {stats['max']:.6f}\\n"
        results += f"  Skewness: {stats['skewness']:.3f}\\n"
        results += f"  Kurtosis: {stats['kurtosis']:.3f}\\n\\n"

        results += "Normality Test:\\n"
        results += f"  Is Normal: {normality['is_normal']}\\n"
        results += f"  Shapiro p-value: {normality['shapiro_p']:.6f}\\n\\n"

        results += "Outlier Detection:\\n"
        results += f"  Outliers Found: {outliers['count']}\\n"
        results += f"  Percentage: {outliers['percentage']:.2f}%\\n"

        self.stat_results.delete(1.0, tk.END)
        self.stat_results.insert(1.0, results)

    def _export_results(self):
        """Export analysis results"""
        filename = filedialog.asksaveasfilename(
            title="Export Results",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )

        #if filename:
    # Export current tab's results
    # Implementation depends on active tab


class AnnotationDialog:
    """Dialog for managing plot annotations"""

    def __init__(self, parent, annotation_manager, axes):
        self.parent = parent
        self.annotation_manager = annotation_manager
        self.axes = axes
        self.changed = False

        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Annotation Manager")
        self.dialog.geometry("800x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create UI
        self._create_widgets()

        # Load existing annotations
        self._refresh_annotation_list()

    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel - Annotation list
        left_panel = ctk.CTkFrame(main_frame, width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(left_panel, text="Annotations", font=("", 14, "bold")).pack(pady=10)

        # Annotation listbox
        self.annotation_listbox = tk.Listbox(left_panel, selectmode="single")
        self.annotation_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.annotation_listbox.bind("<<ListboxSelect>>", self._on_select_annotation)

        # Add buttons
        button_frame = ctk.CTkFrame(left_panel)
        button_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            button_frame,
            text="+ Add",
            command=self._add_annotation,
            width=70
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            button_frame,
            text="- Remove",
            command=self._remove_annotation,
            width=70
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            button_frame,
            text="Clear All",
            command=self._clear_all,
            width=70
        ).pack(side="left", padx=2)

        # Right panel - Properties
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(right_panel, text="Properties", font=("", 14, "bold")).pack(pady=10)

        self.properties_frame = ctk.CTkScrollableFrame(right_panel)
        self.properties_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Dialog buttons
        dialog_buttons = ctk.CTkFrame(self.dialog)
        dialog_buttons.pack(fill="x", pady=10)

        ctk.CTkButton(
            dialog_buttons,
            text="Apply",
            command=self._apply,
            width=100
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            dialog_buttons,
            text="Close",
            command=self.dialog.destroy,
            width=100
        ).pack(side="right", padx=5)

    def _refresh_annotation_list(self):
        """Refresh the annotation list"""
        self.annotation_listbox.delete(0, tk.END)

        for ann_id, ann in self.annotation_manager.get_annotations().items():
            display_text = f"{ann.type}: {ann.label}" if ann.label else f"{ann.type}"
            self.annotation_listbox.insert(tk.END, display_text)

    def _on_select_annotation(self, event):
        """Handle annotation selection"""
        selection = self.annotation_listbox.curselection()
        if not selection:
            return

        # Get selected annotation
        index = selection[0]
        annotations = list(self.annotation_manager.get_annotations().values())

        if index < len(annotations):
            self._show_properties(annotations[index])

    def _show_properties(self, annotation: AnnotationConfig):
        """Show annotation properties"""
        # Clear previous properties
        for widget in self.properties_frame.winfo_children():
            widget.destroy()

        # Type
        frame = ctk.CTkFrame(self.properties_frame)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Type:").pack(side="left", padx=5)
        ctk.CTkLabel(frame, text=annotation.type).pack(side="left", padx=5)

        # Label
        frame = ctk.CTkFrame(self.properties_frame)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Label:").pack(side="left", padx=5)
        label_entry = ctk.CTkEntry(frame, width=200)
        label_entry.insert(0, annotation.label)
        label_entry.pack(side="left", padx=5)

        # Color
        frame = ctk.CTkFrame(self.properties_frame)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text="Color:").pack(side="left", padx=5)
        color_button = ctk.CTkButton(
            frame,
            text="",
            width=30,
            height=30,
            fg_color=annotation.color
        )
        color_button.pack(side="left", padx=5)

        # Position fields based on type
        if annotation.type in ["line", "point"]:
            if annotation.x_data is not None:
                frame = ctk.CTkFrame(self.properties_frame)
                frame.pack(fill="x", pady=5)
                ctk.CTkLabel(frame, text="X Position:").pack(side="left", padx=5)
                ctk.CTkLabel(frame, text=str(annotation.x_data)).pack(side="left", padx=5)

            if annotation.y_data is not None:
                frame = ctk.CTkFrame(self.properties_frame)
                frame.pack(fill="x", pady=5)
                ctk.CTkLabel(frame, text="Y Position:").pack(side="left", padx=5)
                ctk.CTkLabel(frame, text=str(annotation.y_data)).pack(side="left", padx=5)

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

        ctk.CTkLabel(dialog, text="Select Type:", font=("", 12)).pack(pady=10)

        selected_type = tk.StringVar(value="line")

        for ann_type in types:
            ctk.CTkRadioButton(
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

        ctk.CTkButton(
            dialog,
            text="Create",
            command=create_annotation,
            width=100
        ).pack(pady=20)

        ctk.CTkButton(
            dialog,
            text="Cancel",
            command=dialog.destroy,
            width=100
        ).pack()

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
        notebook.add(data_tab, text="📊 Data")
        self._create_data_tab(data_tab)

        # Info tab
        info_tab = ttk.Frame(notebook)
        notebook.add(info_tab, text="ℹ️ Info")
        self._create_info_tab(info_tab)

        # Statistics tab
        stats_tab = ttk.Frame(notebook)
        notebook.add(stats_tab, text="📈 Statistics")
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
        columns = list(self.file_data.dataframe.columns)
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
        df_preview = self.file_data.dataframe.head(1000)
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