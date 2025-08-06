#!/usr/bin/env python3
"""
app.py - Main application window for Excel Data Plotter
Complete implementation with all features from the original application
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from scipy.signal import savgol_filter
from sklearn.linear_model import LinearRegression
import os
import json
from datetime import datetime
import uuid
import logging

# Import application modules
from constants import AppConfig, ColorPalette, FileTypes, PlotTypes, MissingDataMethods, TrendTypes
from models import FileData, SeriesConfig, ProjectData, AnalysisResult
from ui_components import (StatusBar, FileCard, SeriesCard, QuickActionBar, SearchBar,
                           CollapsiblePanel, Tooltip, FloatingPanel)
from file_manager import FileManager
from plot_manager import PlotManager
from annotation_manager import AnnotationManager
from analysis_tools import DataAnalysisTools, VacuumAnalysisTools
from utils import (format_file_size, validate_data_range, detect_datetime_column,
                   convert_to_datetime, generate_color_sequence)

# Import dialogs (will be defined in dialogs.py)
from dialogs import (SeriesConfigDialog, VacuumAnalysisDialog, AnnotationDialog,
                     DataSelectorDialog, PlotConfigDialog)

# Get logger
logger = logging.getLogger(__name__)


class ExcelDataPlotter(ctk.CTk):
    """
    Main application window class
    Coordinates all application components and handles user interactions
    """

    def __init__(self):
        """Initialize the main application window"""
        super().__init__()

        # Configure window properties
        self.title(f"{AppConfig.APP_NAME} - {AppConfig.APP_SUBTITLE}")
        self.geometry(f"{AppConfig.DEFAULT_WIDTH}x{AppConfig.DEFAULT_HEIGHT}")
        self.minsize(AppConfig.MIN_WIDTH, AppConfig.MIN_HEIGHT)

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Initialize data storage
        self.loaded_files = {}  # Dictionary of loaded FileData objects
        self.all_series = {}  # Dictionary of SeriesConfig objects
        self.color_index = 0  # For auto-assigning colors
        self.auto_colors = ColorPalette.CHART_COLORS

        # Initialize managers
        self.file_manager = FileManager()
        self.plot_manager = PlotManager()
        self.annotation_manager = AnnotationManager()
        self.analysis_tools = DataAnalysisTools()
        self.vacuum_tools = VacuumAnalysisTools()

        # Plot state
        self.figure = None
        self.canvas = None
        self.toolbar = None

        # Initialize UI variables
        self.init_variables()

        # Create UI components
        self.create_ui()

        # Bind window events
        self.bind_events()

        # Initialize status
        self.status_bar.set_status("Welcome to Professional Excel Data Plotter", "info")

        logger.info("Application window initialized")

    def init_variables(self):
        """Initialize tkinter variables for UI controls"""
        # Plot configuration variables
        self.title_var = tk.StringVar(value="Multi-File Data Analysis")
        self.title_size_var = tk.IntVar(value=16)
        self.xlabel_var = tk.StringVar(value="X Axis")
        self.xlabel_size_var = tk.IntVar(value=12)
        self.ylabel_var = tk.StringVar(value="Y Axis")
        self.ylabel_size_var = tk.IntVar(value=12)
        self.log_scale_x_var = tk.BooleanVar(value=False)
        self.log_scale_y_var = tk.BooleanVar(value=False)
        self.show_grid_var = tk.BooleanVar(value=True)
        self.show_legend_var = tk.BooleanVar(value=True)
        self.grid_style_var = tk.StringVar(value="-")
        self.grid_alpha_var = tk.DoubleVar(value=0.3)
        self.fig_width_var = tk.DoubleVar(value=14.0)
        self.fig_height_var = tk.DoubleVar(value=9.0)
        self.plot_type_var = tk.StringVar(value="line")

        # Axis scaling
        self.x_auto_scale = tk.BooleanVar(value=True)
        self.y_auto_scale = tk.BooleanVar(value=True)
        self.x_min_var = tk.StringVar(value="")
        self.x_max_var = tk.StringVar(value="")
        self.y_min_var = tk.StringVar(value="")
        self.y_max_var = tk.StringVar(value="")

        # Margins
        self.margin_left_var = tk.DoubleVar(value=0.1)
        self.margin_right_var = tk.DoubleVar(value=0.05)
        self.margin_top_var = tk.DoubleVar(value=0.1)
        self.margin_bottom_var = tk.DoubleVar(value=0.1)

        # Series creation variables
        self.series_file_var = tk.StringVar()
        self.series_x_var = tk.StringVar()
        self.series_y_var = tk.StringVar()
        self.series_name_var = tk.StringVar(value="New Series")
        self.series_start_var = tk.IntVar(value=0)
        self.series_end_var = tk.IntVar(value=1000)

        # Layout tracking
        self.current_layout = "default"
        self.current_theme = ctk.get_appearance_mode()

        # Export settings
        self.export_format = tk.StringVar(value='PNG (High Quality)')
        self.dpi_var = tk.IntVar(value=300)

    def create_ui(self):
        """Create the main UI layout"""
        # Main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Create UI sections
        self.create_top_bar()
        self.create_main_content()
        self.create_status_bar()
        self.create_floating_panels()

    def create_top_bar(self):
        """Create the top action bar with rearranged buttons"""
        self.top_bar = QuickActionBar(self.main_container)
        self.top_bar.grid(row=0, column=0, sticky="ew")

        # File actions (left side)
        self.top_bar.add_action("Add Files", "📁", self.add_files, "Load Excel/CSV files", side="left")
        self.top_bar.add_action("Load Project", "📂", self.load_project, "Load saved project", side="left")
        self.top_bar.add_action("Save Project", "💾", self.save_project, "Save current project", side="left")
        self.top_bar.add_separator(side="left")

        # Plot actions (right side)
        self.top_bar.add_action("Generate Plot", "📊", self.create_plot, "Create plot from series", side="right")
        self.top_bar.add_action("Export", "📤", self.show_export_dialog, "Export plot or data", side="right")
        self.top_bar.add_separator(side="right")

        # Analysis actions (center) - FIXED
        self.top_bar.add_action("Analysis", "🔬", self.show_statistical_analysis, "Statistical analysis tools",
                                side="center")
        self.top_bar.add_action("Vacuum Tools", "🎯", self.show_vacuum_analysis, "Vacuum analysis tools", side="center")
        self.top_bar.add_action("Annotations", "📍", self.show_annotation_panel, "Manage annotations", side="center")
        self.top_bar.add_separator(side="center")

        # View actions (center) - FIXED
        self.top_bar.add_action("Theme", "🎨", self.toggle_theme, "Toggle dark/light theme", side="center")
        self.top_bar.add_action("Configure", "📐", self.show_plot_config, "Configure plot settings", side="center")

        logger.debug("Top action bar created")

    def show_plot_config(self):
        """Show plot configuration dialog"""
        config = {
            'title': self.title_var.get(),
            'title_size': self.title_size_var.get(),
            'xlabel': self.xlabel_var.get(),
            'xlabel_size': self.xlabel_size_var.get(),
            'ylabel': self.ylabel_var.get(),
            'ylabel_size': self.ylabel_size_var.get(),
            'log_scale_x': self.log_scale_x_var.get(),
            'log_scale_y': self.log_scale_y_var.get(),
            'show_grid': self.show_grid_var.get(),
            'show_legend': self.show_legend_var.get(),
            'grid_style': self.grid_style_var.get(),
            'grid_alpha': self.grid_alpha_var.get(),
            'fig_width': self.fig_width_var.get(),
            'fig_height': self.fig_height_var.get()
        }

        dialog = PlotConfigDialog(self, config)
        self.wait_window(dialog.dialog)

        if dialog.result == 'apply':
            # Apply configuration
            self.title_var.set(dialog.plot_config['title'])
            self.title_size_var.set(dialog.plot_config['title_size'])
            self.xlabel_var.set(dialog.plot_config['xlabel'])
            self.xlabel_size_var.set(dialog.plot_config['xlabel_size'])
            self.ylabel_var.set(dialog.plot_config['ylabel'])
            self.ylabel_size_var.set(dialog.plot_config['ylabel_size'])
            self.log_scale_x_var.set(dialog.plot_config['log_scale_x'])
            self.log_scale_y_var.set(dialog.plot_config['log_scale_y'])
            self.show_grid_var.set(dialog.plot_config['show_grid'])
            self.show_legend_var.set(dialog.plot_config['show_legend'])
            self.grid_style_var.set(dialog.plot_config['grid_style'])
            self.grid_alpha_var.set(dialog.plot_config['grid_alpha'])
            self.fig_width_var.set(dialog.plot_config['fig_width'])
            self.fig_height_var.set(dialog.plot_config['fig_height'])

            # Store additional config
            self.plot_config_extra = dialog.plot_config

            # Refresh plot if exists
            if self.figure:
                self.create_plot()

            self.status_bar.set_status("Plot configuration updated", "success")

    def show_statistical_analysis(self):
        """Show generic statistical analysis dialog"""
        if self.all_series:
            # Create a simplified statistical analysis dialog
            # You can implement this as needed
            messagebox.showinfo("Statistical Analysis",
                                "Statistical analysis tools will be available here.\n" +
                                "Features: correlation, regression, distribution analysis, etc.")
        else:
            self.status_bar.set_status("No series available for analysis", "warning")

    def refresh_plot(self):
        """Refresh the plot with current settings"""
        if self.figure:
            self.create_plot()
    def create_main_content(self):
        """Create the main content area with adaptive layout"""
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Determine initial layout based on window size
        self.create_default_layout()

    def create_default_layout(self):
        """Create the default layout with sidebar and main area"""
        # Clear existing widgets
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)

        # Collapsible sidebar
        self.sidebar = ctk.CTkFrame(self.content_frame, width=400)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.sidebar.grid_propagate(False)

        # Sidebar content with tabs
        self.sidebar_tabs = ctk.CTkTabview(self.sidebar, width=390, height=800)
        self.sidebar_tabs.pack(fill="both", expand=True)

        # Create tabs
        self.files_tab = self.sidebar_tabs.add("Files")
        self.series_tab = self.sidebar_tabs.add("Series")
        self.config_tab = self.sidebar_tabs.add("Configuration")
        self.export_tab = self.sidebar_tabs.add("Export")

        self.create_files_panel()
        self.create_series_panel()
        self.create_config_panel()
        self.create_export_panel()

        # Main plot area
        self.plot_frame = ctk.CTkFrame(self.content_frame)
        self.plot_frame.grid(row=0, column=1, sticky="nsew")
        self.plot_frame.grid_rowconfigure(0, weight=1)
        self.plot_frame.grid_columnconfigure(0, weight=1)

        self.create_plot_area()

    def create_files_panel(self):
        """Create the files management panel"""
        # Search bar
        self.file_search = SearchBar(
            self.files_tab,
            on_search=self.search_files
        )
        self.file_search.pack(fill="x", padx=10, pady=(10, 5))

        # File actions
        action_frame = ctk.CTkFrame(self.files_tab)
        action_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            action_frame,
            text="Add Files",
            command=self.add_files,
            fg_color=ColorPalette.PRIMARY
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            action_frame,
            text="Reload All",
            command=self.reload_all_files,
            fg_color=ColorPalette.SECONDARY
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            action_frame,
            text="Clear All",
            command=self.clear_all_files,
            fg_color=ColorPalette.ERROR
        ).pack(side="left")

        # Files list with scrollable frame
        self.files_scroll = ctk.CTkScrollableFrame(self.files_tab)
        self.files_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Update files display
        self.update_files_display()

    def create_series_panel(self):
        """Create the series management panel with professional features"""
        # Series creation section
        create_frame = CollapsiblePanel(self.series_tab, "Create New Series", start_collapsed=False)
        create_frame.pack(fill="x", padx=10, pady=(10, 5))

        content = create_frame.get_content_frame()

        # File selection
        ctk.CTkLabel(content, text="Source File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.series_file_combo = ctk.CTkComboBox(
            content,
            variable=self.series_file_var,
            command=self.on_file_selected_for_series,
            width=200
        )
        self.series_file_combo.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        # Advanced data selection button
        self.data_select_btn = ctk.CTkButton(
            content,
            text="Advanced Selection",
            command=self.show_advanced_data_selector,
            width=120
        )
        self.data_select_btn.grid(row=0, column=3, padx=5, pady=5)

        # Column selection
        ctk.CTkLabel(content, text="X Column:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.series_x_combo = ctk.CTkComboBox(content, variable=self.series_x_var, width=120,
                                              command=lambda x: self.update_series_range_limits())
        self.series_x_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(content, text="Y Column:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.series_y_combo = ctk.CTkComboBox(content, variable=self.series_y_var, width=120,
                                              command=lambda x: self.update_series_range_limits())
        self.series_y_combo.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        # Range selection with data preview
        range_frame = ttk.Frame(content)
        range_frame.grid(row=2, column=0, columnspan=4, sticky='ew', pady=10)

        ttk.Label(range_frame, text="Data Range:").grid(row=0, column=0, sticky='w', padx=5, pady=5)

        # Start selection
        self.series_start_frame = ttk.Frame(range_frame)
        self.series_start_frame.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=5)

        ttk.Label(self.series_start_frame, text="Start:").pack(side='left')
        self.series_start_entry = ctk.CTkEntry(self.series_start_frame, textvariable=self.series_start_var, width=80)
        self.series_start_entry.pack(side='left', padx=5)
        self.series_start_label = ttk.Label(self.series_start_frame, text="", foreground='gray')
        self.series_start_label.pack(side='left', padx=5)

        # End selection
        self.series_end_frame = ttk.Frame(range_frame)
        self.series_end_frame.grid(row=1, column=2, columnspan=2, sticky='w', padx=5, pady=5)

        ttk.Label(self.series_end_frame, text="End:").pack(side='left')
        self.series_end_entry = ctk.CTkEntry(self.series_end_frame, textvariable=self.series_end_var, width=80)
        self.series_end_entry.pack(side='left', padx=5)
        self.series_end_label = ttk.Label(self.series_end_frame, text="", foreground='gray')
        self.series_end_label.pack(side='left', padx=5)

        # Bind change events to update labels
        self.series_start_var.trace('w', self.update_range_labels)
        self.series_end_var.trace('w', self.update_range_labels)

        # Series name
        ctk.CTkLabel(content, text="Name:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.series_name_entry = ctk.CTkEntry(content, textvariable=self.series_name_var, width=200)
        self.series_name_entry.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        ctk.CTkButton(
            content,
            text="Add Series",
            command=self.add_series,
            fg_color=ColorPalette.SUCCESS
        ).grid(row=4, column=3, padx=5, pady=5)

        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(3, weight=1)

        # Series list
        series_label = ctk.CTkLabel(self.series_tab, text="Active Series", font=("", 14, "bold"))
        series_label.pack(padx=10, pady=(20, 5), anchor="w")

        self.series_scroll = ctk.CTkScrollableFrame(self.series_tab)
        self.series_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Update series display
        self.update_series_display()

    def update_range_labels(self, *args):
        """Update range labels with actual data values"""
        selection = self.series_file_var.get()
        if not selection:
            return

        try:
            file_id = selection.split('(')[-1].rstrip(')')
            matching_file = None
            for fid, fdata in self.loaded_files.items():
                if fid.startswith(file_id):
                    matching_file = fdata
                    break

            if matching_file and self.series_x_var.get():
                x_col = self.series_x_var.get()
                start_idx = self.series_start_var.get()
                end_idx = self.series_end_var.get()

                if x_col != 'Index' and x_col in matching_file.df.columns:
                    # Show actual data values
                    if 0 <= start_idx < len(matching_file.df):
                        start_val = matching_file.df.iloc[start_idx][x_col]
                        self.series_start_label.config(text=f"({start_val})")

                    if 0 < end_idx <= len(matching_file.df):
                        end_val = matching_file.df.iloc[end_idx - 1][x_col]
                        self.series_end_label.config(text=f"({end_val})")
                else:
                    self.series_start_label.config(text="")
                    self.series_end_label.config(text="")
        except:
            pass
    def create_config_panel(self):
        """Create the configuration panel with professional features"""
        # Plot configuration sections
        sections = [
            ("Plot Settings", self.create_plot_settings),
            ("Axis Configuration", self.create_axis_config),
            ("Visual Style", self.create_visual_style),
            ("Advanced Options", self.create_advanced_options)
        ]

        for title, create_func in sections:
            panel = CollapsiblePanel(self.config_tab, title, start_collapsed=True)
            panel.pack(fill="x", padx=10, pady=5)
            create_func(panel.get_content_frame())

    def create_plot_settings(self, parent):
        """Create plot settings controls"""
        # Plot type
        ctk.CTkLabel(parent, text="Plot Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        plot_types = ["line", "scatter", "bar", "area", "box"]

        plot_type_frame = ctk.CTkFrame(parent, fg_color="transparent")
        plot_type_frame.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        for i, ptype in enumerate(plot_types):
            ctk.CTkRadioButton(
                plot_type_frame,
                text=ptype.capitalize(),
                variable=self.plot_type_var,
                value=ptype
            ).pack(side="left", padx=5, pady=5)

        # Figure size
        ctk.CTkLabel(parent, text="Figure Size:").grid(row=1, column=0, sticky="w", padx=5, pady=5)

        size_frame = ctk.CTkFrame(parent, fg_color="transparent")
        size_frame.grid(row=1, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(size_frame, text="W:").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(size_frame, textvariable=self.fig_width_var, width=60).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(size_frame, text="H:").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(size_frame, textvariable=self.fig_height_var, width=60).pack(side="left")

        # Margins
        ctk.CTkLabel(parent, text="Margins:").grid(row=2, column=0, sticky="w", padx=5, pady=5)

        margin_frame = ctk.CTkFrame(parent, fg_color="transparent")
        margin_frame.grid(row=2, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(margin_frame, text="L:").pack(side="left", padx=2)
        ctk.CTkSlider(margin_frame, from_=0.05, to=0.3, variable=self.margin_left_var,
                      width=80).pack(side="left", padx=2)

        ctk.CTkLabel(margin_frame, text="R:").pack(side="left", padx=2)
        ctk.CTkSlider(margin_frame, from_=0.02, to=0.2, variable=self.margin_right_var,
                      width=80).pack(side="left", padx=2)

    def create_axis_config(self, parent):
        """Create axis configuration controls"""
        # Title
        ctk.CTkLabel(parent, text="Title:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.title_var, width=300).grid(row=0, column=1, columnspan=3, sticky="ew",
                                                                          padx=5, pady=5)

        ctk.CTkLabel(parent, text="Size:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.title_size_var, width=60).grid(row=0, column=5, padx=5, pady=5)

        # X-axis
        ctk.CTkLabel(parent, text="X Label:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.xlabel_var, width=140).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(parent, text="Size:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.xlabel_size_var, width=60).grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkCheckBox(parent, text="Log Scale", variable=self.log_scale_x_var).grid(row=1, column=4, padx=5, pady=5)

        # Y-axis
        ctk.CTkLabel(parent, text="Y Label:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.ylabel_var, width=140).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(parent, text="Size:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.ylabel_size_var, width=60).grid(row=2, column=3, padx=5, pady=5)

        ctk.CTkCheckBox(parent, text="Log Scale", variable=self.log_scale_y_var).grid(row=2, column=4, padx=5, pady=5)

        parent.grid_columnconfigure(1, weight=1)

    def create_visual_style(self, parent):
        """Create visual style controls"""
        # Grid style
        ctk.CTkLabel(parent, text="Grid Style:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.grid_style_combo = ctk.CTkComboBox(
            parent,
            variable=self.grid_style_var,
            values=["-", "--", ":", "-."],
            width=100
        )
        self.grid_style_combo.grid(row=0, column=1, padx=5, pady=5)

        # Grid alpha
        ctk.CTkLabel(parent, text="Grid Alpha:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkSlider(
            parent,
            from_=0.1,
            to=1.0,
            variable=self.grid_alpha_var,
            width=150
        ).grid(row=0, column=3, padx=5, pady=5)

        # Show grid
        ctk.CTkCheckBox(parent, text="Show Grid", variable=self.show_grid_var).grid(row=1, column=0, sticky="w", padx=5,
                                                                                    pady=5)

        # Show legend
        ctk.CTkCheckBox(parent, text="Show Legend", variable=self.show_legend_var).grid(row=1, column=1, sticky="w",
                                                                                        padx=5, pady=5)

    def create_advanced_options(self, parent):
        """Create advanced options section"""
        # X-axis auto scale
        ctk.CTkCheckBox(parent, text="Auto X Scale", variable=self.x_auto_scale,
                        command=self.toggle_x_manual_limits).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # X-axis manual limits
        ctk.CTkLabel(parent, text="X Min:").grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.x_min_entry = ctk.CTkEntry(parent, textvariable=self.x_min_var, width=80, state="disabled")
        self.x_min_entry.grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkLabel(parent, text="X Max:").grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.x_max_entry = ctk.CTkEntry(parent, textvariable=self.x_max_var, width=80, state="disabled")
        self.x_max_entry.grid(row=0, column=4, padx=5, pady=5)

        # Y-axis auto scale
        ctk.CTkCheckBox(parent, text="Auto Y Scale", variable=self.y_auto_scale,
                        command=self.toggle_y_manual_limits).grid(row=1, column=0, sticky="w", padx=5, pady=5)

        # Y-axis manual limits
        ctk.CTkLabel(parent, text="Y Min:").grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.y_min_entry = ctk.CTkEntry(parent, textvariable=self.y_min_var, width=80, state="disabled")
        self.y_min_entry.grid(row=1, column=2, padx=5, pady=5)

        ctk.CTkLabel(parent, text="Y Max:").grid(row=1, column=3, sticky="w", padx=5, pady=5)
        self.y_max_entry = ctk.CTkEntry(parent, textvariable=self.y_max_var, width=80, state="disabled")
        self.y_max_entry.grid(row=1, column=4, padx=5, pady=5)

    def create_export_panel(self):
        """Create export panel with professional options"""
        export_frame = ctk.CTkFrame(self.export_tab)
        export_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Image format
        ctk.CTkLabel(export_frame, text="Image Format:").pack(anchor="w", pady=2)
        format_combo = ctk.CTkComboBox(export_frame, width=200,
                                       values=['PNG (High Quality)', 'PDF (Vector)', 'SVG (Scalable)',
                                               'JPG (Compressed)'],
                                       variable=self.export_format)
        format_combo.pack(fill="x", pady=2)

        # Resolution
        ctk.CTkLabel(export_frame, text="Resolution (DPI):").pack(anchor="w", pady=2)

        dpi_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        dpi_frame.pack(fill="x", pady=2)

        for dpi in [150, 300, 600, 1200]:
            ctk.CTkRadioButton(dpi_frame, text=str(dpi), variable=self.dpi_var,
                               value=dpi).pack(side="left", padx=10)

        # Export buttons
        ctk.CTkButton(export_frame, text="Export Plot", command=self.export_plot,
                      fg_color=ColorPalette.SUCCESS).pack(fill="x", pady=10)
        ctk.CTkButton(export_frame, text="Export All Data", command=self.export_all_data,
                      fg_color=ColorPalette.SECONDARY).pack(fill="x", pady=2)
        ctk.CTkButton(export_frame, text="Export Series Config", command=self.export_series_config,
                      fg_color=ColorPalette.SECONDARY).pack(fill="x", pady=2)

    def create_plot_area(self):
        """Create the main plot area"""
        # Welcome message for empty state
        self.empty_plot_frame = ctk.CTkFrame(self.plot_frame)
        self.empty_plot_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        welcome_label = ctk.CTkLabel(
            self.empty_plot_frame,
            text="Professional Multi-File Excel Data Plotter\nVacuum Analysis Edition\n\nLoad multiple Excel files and create custom series ranges\nfor comprehensive vacuum data visualization and analysis.",
            font=("", 18),
            text_color=("gray40", "gray60")
        )
        welcome_label.pack(expand=True)

        ctk.CTkButton(
            self.empty_plot_frame,
            text="Get Started - Add Files",
            command=self.add_files,
            width=200,
            height=40,
            font=("", 14)
        ).pack(pady=20)

    def create_status_bar(self):
        """Create the bottom status bar"""
        self.status_bar = StatusBar(self.main_container)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def create_floating_panels(self):
        """Create floating panels for analysis and annotations"""
        # These will be created on-demand
        self.analysis_panel = None
        self.annotation_panel = None

    def bind_events(self):
        """Bind window and widget events"""
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Configure>", self.on_window_resize)

    # ============= File Operations =============

    def add_files(self):
        """Add multiple files with progress indication"""
        filenames = filedialog.askopenfilenames(
            title="Select Excel/CSV files",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if filenames:
            self.status_bar.show_progress()
            success_count = 0
            error_files = []

            for i, filename in enumerate(filenames):
                try:
                    progress = (i + 1) / len(filenames)
                    self.status_bar.show_progress(progress)
                    self.status_bar.set_status(f"Loading: {os.path.basename(filename)}", "info")

                    # Load file
                    if filename.endswith('.csv'):
                        df = pd.read_csv(filename)
                    else:
                        df = pd.read_excel(filename)

                    # Create FileData object
                    file_data = FileData(filename, df)
                    self.loaded_files[file_data.id] = file_data

                    success_count += 1

                except Exception as e:
                    error_files.append((filename, str(e)))

            # Update UI
            self.update_files_display()
            self.update_series_file_combo()
            self.status_bar.hide_progress()
            self.update_counts()

            # Show results
            if success_count > 0:
                self.status_bar.set_status(f"Successfully loaded {success_count} file(s)", "success")
                if error_files:
                    self.show_error_details(error_files)
            else:
                self.status_bar.set_status("Failed to load any files", "error")

    def clear_all_files(self):
        """Clear all loaded files and series"""
        if self.loaded_files:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Clear All")
            dialog.geometry("400x200")
            dialog.transient(self)
            dialog.grab_set()

            x = (dialog.winfo_screenwidth() - 400) // 2
            y = (dialog.winfo_screenheight() - 200) // 2
            dialog.geometry(f"+{x}+{y}")

            ctk.CTkLabel(
                dialog,
                text="Clear all files and series?",
                font=("", 16, "bold")
            ).pack(pady=20)

            ctk.CTkLabel(
                dialog,
                text="This action cannot be undone.",
                text_color=ColorPalette.ERROR
            ).pack(pady=10)

            btn_frame = ctk.CTkFrame(dialog)
            btn_frame.pack(pady=20)

            ctk.CTkButton(
                btn_frame,
                text="Cancel",
                command=dialog.destroy,
                fg_color="gray50"
            ).pack(side="left", padx=10)

            def confirm_clear():
                self.loaded_files.clear()
                self.all_series.clear()
                self.color_index = 0

                self.update_files_display()
                self.update_series_display()
                self.update_series_file_combo()
                self.clear_plot_area()

                self.update_counts()
                self.status_bar.set_status("All files and series cleared", "info")

                dialog.destroy()

            ctk.CTkButton(
                btn_frame,
                text="Clear All",
                command=confirm_clear,
                fg_color=ColorPalette.ERROR
            ).pack(side="left", padx=10)

    def reload_all_files(self):
        """Reload all loaded files"""
        if not self.loaded_files:
            self.status_bar.set_status("No files to reload", "warning")
            return

        file_paths = [file_data.filepath for file_data in self.loaded_files.values()]
        self.clear_all_files()

        success_count = 0
        for filepath in file_paths:
            try:
                if filepath.endswith('.csv'):
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_excel(filepath)

                file_data = FileData(filepath, df)
                self.loaded_files[file_data.id] = file_data
                success_count += 1
            except Exception as e:
                print(f"Error reloading {filepath}: {e}")

        self.update_files_display()
        self.update_series_file_combo()
        self.update_counts()

        if success_count > 0:
            self.status_bar.set_status(f"Reloaded {success_count} files", "success")

    def search_files(self, query):
        """Search files by name"""
        query = query.lower()
        for widget in self.files_scroll.winfo_children():
            if isinstance(widget, FileCard):
                if query in widget.file_data.filename.lower():
                    widget.pack(fill="x", pady=5)
                else:
                    widget.pack_forget()

    def update_files_display(self):
        """Update the files display with modern cards"""
        for widget in self.files_scroll.winfo_children():
            widget.destroy()

        for file_data in self.loaded_files.values():
            card = FileCard(
                self.files_scroll,
                file_data,
                on_remove=self.remove_file,
                on_view=self.view_file_data
            )
            card.pack(fill="x", pady=5)

    def remove_file(self, file_data):
        """Remove a file and its associated series"""
        series_count = len(file_data.series_list)

        if series_count > 0:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Remove")
            dialog.geometry("400x200")
            dialog.transient(self)
            dialog.grab_set()

            x = (self.winfo_screenwidth() - 400) // 2
            y = (self.winfo_screenheight() - 200) // 2
            dialog.geometry(f"+{x}+{y}")

            ctk.CTkLabel(
                dialog,
                text=f"Remove '{file_data.filename}'?",
                font=("", 16, "bold")
            ).pack(pady=10)

            ctk.CTkLabel(
                dialog,
                text=f"This will also remove {series_count} associated series.",
                text_color=ColorPalette.WARNING
            ).pack(pady=5)

            btn_frame = ctk.CTkFrame(dialog)
            btn_frame.pack(pady=15)

            ctk.CTkButton(
                btn_frame,
                text="Cancel",
                command=dialog.destroy,
                fg_color="gray50"
            ).pack(side="left", padx=10)

            def confirm_remove():
                for series_id in file_data.series_list.copy():
                    if series_id in self.all_series:
                        del self.all_series[series_id]

                del self.loaded_files[file_data.id]

                self.update_files_display()
                self.update_series_display()
                self.update_series_file_combo()
                self.update_counts()

                dialog.destroy()
                self.status_bar.set_status(f"Removed file and {series_count} series", "info")

            ctk.CTkButton(
                btn_frame,
                text="Remove",
                command=confirm_remove,
                fg_color=ColorPalette.ERROR
            ).pack(side="left", padx=10)
        else:
            del self.loaded_files[file_data.id]
            self.update_files_display()
            self.update_counts()
            self.status_bar.set_status(f"Removed file: {file_data.filename}", "info")

    def view_file_data(self, file_data):
        """View file data in a modern data viewer"""
        viewer = ctk.CTkToplevel(self)
        viewer.title(f"Data Viewer - {file_data.filename}")
        viewer.geometry("900x600")
        viewer.transient(self)

        viewer_frame = ctk.CTkFrame(viewer)
        viewer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        info_frame = ctk.CTkFrame(viewer_frame)
        info_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            info_frame,
            text=f"Rows: {len(file_data.df):,} | Columns: {len(file_data.df.columns)}",
            font=("", 12)
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            info_frame,
            text="Export Data",
            command=lambda: self.export_dataframe(file_data.df, file_data.filename),
            width=100
        ).pack(side="right", padx=10)

        text_frame = ctk.CTkFrame(viewer_frame)
        text_frame.pack(fill="both", expand=True)

        text_widget = ctk.CTkTextbox(text_frame, font=("Consolas", 10))

        display_df = file_data.df.head(1000)
        text_widget.insert("1.0", display_df.to_string())
        text_widget.configure(state="disabled")

        text_widget.pack(fill="both", expand=True)

        status_label = ctk.CTkLabel(
            viewer_frame,
            text=f"Showing first {min(1000, len(file_data.df))} rows",
            text_color=("gray60", "gray40")
        )
        status_label.pack(pady=5)

    # ============= Series Operations =============

    def update_series_file_combo(self):
        """Update the file selection combo for series creation"""
        file_options = [f"{fd.filename} ({fd.id[:8]})" for fd in self.loaded_files.values()]

        if hasattr(self, 'series_file_combo'):
            self.series_file_combo.configure(values=file_options)
            if file_options and not self.series_file_var.get():
                self.series_file_combo.set(file_options[0])
                self.on_file_selected_for_series()

    def on_file_selected_for_series(self, choice=None):
        """Handle file selection for series creation"""
        selection = self.series_file_var.get()
        if not selection:
            return

        try:
            file_id = selection.split('(')[-1].rstrip(')')

            matching_file = None
            for fid, fdata in self.loaded_files.items():
                if fid.startswith(file_id):
                    matching_file = fdata
                    break

            if matching_file:
                actual_columns = matching_file.df.columns.tolist()
                columns = [str(col) for col in actual_columns]

                self.series_x_combo.configure(values=['Index'] + columns)
                self.series_y_combo.configure(values=columns)

                max_rows = len(matching_file.df)
                self.series_end_var.set(min(1000, max_rows))

                if columns:
                    self.series_x_combo.set('Index')
                    numeric_cols = []
                    for col in actual_columns:
                        try:
                            if pd.api.types.is_numeric_dtype(matching_file.df[col]):
                                numeric_cols.append(str(col))
                        except:
                            pass

                    if numeric_cols:
                        self.series_y_combo.set(numeric_cols[0])

                self.update_series_range_limits()

        except Exception as e:
            print(f"File selection error: {e}")
            self.status_bar.set_status(f"File selection error: {str(e)}", "error")

    def update_series_range_limits(self):
        """Update the range limits based on selected columns"""
        selection = self.series_file_var.get()
        if not selection:
            return

        try:
            file_id = selection.split('(')[-1].rstrip(')')

            matching_file = None
            for fid, fdata in self.loaded_files.items():
                if fid.startswith(file_id):
                    matching_file = fdata
                    break

            if matching_file:
                x_col = self.series_x_combo.get()
                y_col = self.series_y_combo.get()

                if x_col and y_col:
                    df = matching_file.df
                    max_rows = len(df)

                    if x_col != 'Index' and x_col in df.columns:
                        x_valid = df[x_col].notna()
                    else:
                        x_valid = pd.Series([True] * len(df))

                    if y_col in df.columns:
                        y_valid = df[y_col].notna()
                    else:
                        y_valid = pd.Series([True] * len(df))

                    valid_mask = x_valid & y_valid
                    if valid_mask.any():
                        valid_indices = valid_mask[valid_mask].index
                        first_valid = valid_indices[0]
                        last_valid = valid_indices[-1]

                        self.range_info_label.configure(
                            text=f"Valid data range: {first_valid} to {last_valid} ({len(valid_indices)} points)"
                        )

                        if self.series_start_var.get() == 0 or self.series_start_var.get() > last_valid:
                            self.series_start_var.set(first_valid)
                        if self.series_end_var.get() > last_valid or self.series_end_var.get() < first_valid:
                            self.series_end_var.set(min(last_valid + 1, max_rows))
                    else:
                        self.range_info_label.configure(text="No valid data in selected columns")
                else:
                    self.range_info_label.configure(text="Select both X and Y columns")

        except Exception as e:
            print(f"Range update error: {e}")
            self.range_info_label.configure(text="")

    def add_series(self):
        """Add a new data series"""
        selection = self.series_file_var.get()
        if not selection:
            self.status_bar.set_status("Please select a source file", "warning")
            return

        x_col = self.series_x_combo.get()
        y_col = self.series_y_combo.get()

        if not x_col or not y_col:
            self.status_bar.set_status("Please select both X and Y columns", "warning")
            return

        file_id = selection.split('(')[-1].rstrip(')')
        matching_file = None
        for fid, fdata in self.loaded_files.items():
            if fid.startswith(file_id):
                matching_file = fdata
                matching_file_id = fid
                break

        if not matching_file:
            self.status_bar.set_status("Invalid file selection", "error")
            return

        start_idx = self.series_start_var.get()
        end_idx = self.series_end_var.get()

        if start_idx >= end_idx:
            self.status_bar.set_status("Start index must be less than end index", "warning")
            return

        series_name = self.series_name_var.get()
        series = SeriesConfig(series_name, matching_file_id, x_col, y_col, start_idx, end_idx)

        series.color = self.auto_colors[self.color_index % len(self.auto_colors)]
        self.color_index += 1

        self.all_series[series.id] = series
        matching_file.series_list.append(series.id)

        self.update_series_display()
        self.update_counts()

        self.series_name_var.set(f"Series {len(self.all_series) + 1}")

        self.status_bar.set_status(f"Added series: {series_name}", "success")

    def update_series_display(self):
        """Update the series display with modern cards"""
        for widget in self.series_scroll.winfo_children():
            widget.destroy()

        for series in self.all_series.values():
            file_data = self.loaded_files.get(series.file_id)
            if file_data:
                card = SeriesCard(
                    self.series_scroll,
                    series,
                    file_data,
                    on_configure=self.configure_series,
                    on_toggle=self.toggle_series_visibility,
                    on_remove=self.remove_series
                )
                card.pack(fill="x", pady=5)

    def configure_series(self, series):
        """Open series configuration dialog"""
        dialog = SeriesConfigDialog(self, series, self.loaded_files[series.file_id])
        self.wait_window(dialog.dialog)

        if dialog.result == "apply":
            self.update_series_display()
            self.status_bar.set_status(f"Configured series: {series.name}", "success")

    def toggle_series_visibility(self, series):
        """Toggle series visibility"""
        series.visible = not series.visible
        self.status_bar.set_status(f"Series '{series.name}' {'shown' if series.visible else 'hidden'}", "info")

    def remove_series(self, series):
        """Remove a series"""
        if series.file_id in self.loaded_files:
            file_data = self.loaded_files[series.file_id]
            if series.id in file_data.series_list:
                file_data.series_list.remove(series.id)

        del self.all_series[series.id]

        self.update_series_display()
        self.update_counts()
        self.status_bar.set_status(f"Removed series: {series.name}", "info")

    # ============= Plot Operations =============

    def clear_plot_area(self):
        """Clear the plot area and show empty state"""
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

        self.empty_plot_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def create_plot(self):
        """Create the plot with modern styling and professional features"""
        if not self.all_series:
            self.status_bar.set_status("No series defined. Please add at least one series.", "warning")
            return

        visible_series = [s for s in self.all_series.values() if s.visible]
        if not visible_series:
            self.status_bar.set_status("No visible series. Please make at least one series visible.", "warning")
            return

        try:
            self.status_bar.set_status("Generating plot...", "info")
            self.status_bar.show_progress()

            self.empty_plot_frame.grid_forget()

            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            if self.toolbar:
                self.toolbar.destroy()

            if self.current_theme == "dark":
                plt.style.use('dark_background')
            else:
                plt.style.use('seaborn-v0_8-whitegrid')

            self.figure = Figure(figsize=(self.fig_width_var.get(), self.fig_height_var.get()),
                                 facecolor='white', dpi=100)
            ax = self.figure.add_subplot(111)

            plot_type = self.plot_type_var.get()

            for i, series in enumerate(visible_series):
                self.status_bar.show_progress((i + 1) / len(visible_series))

                file_data = self.loaded_files.get(series.file_id)
                if not file_data:
                    continue

                try:
                    self.plot_single_series(ax, series, file_data, plot_type)
                except Exception as e:
                    print(f"Error plotting series {series.name}: {e}")
                    continue

            self.configure_plot_axes(ax)

            self.annotation_manager.draw_annotations(ax)

            self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

            toolbar_frame = ctk.CTkFrame(self.plot_frame, height=40)
            toolbar_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
            toolbar_frame.grid_propagate(False)

            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()

            self.status_bar.hide_progress()
            self.status_bar.set_status("Plot created successfully", "success")

        except Exception as e:
            self.status_bar.hide_progress()
            self.status_bar.set_status(f"Failed to create plot: {str(e)}", "error")
            import traceback
            traceback.print_exc()

    def plot_single_series(self, ax, series, file_data, plot_type):
        """Plot a single data series with enhanced problematic data handling"""
        start_idx = max(0, series.start_index)
        end_idx = min(len(file_data.df), series.end_index or len(file_data.df))

        if start_idx >= end_idx:
            return

        data_slice = file_data.df.iloc[start_idx:end_idx].copy()

        # Get X data
        if series.x_column == 'Index':
            x_data = np.arange(start_idx, end_idx)
            x_label = "Index"
        else:
            x_data = data_slice[series.x_column]
            x_label = series.x_column
            if detect_datetime_column(x_data):
                x_data = convert_to_datetime(x_data)

        # Get Y data
        y_data = data_slice[series.y_column].copy()

        # Detect and handle problematic data
        problematic_mask, problem_types = self.detect_problematic_data(y_data, series)

        # Store original data for problem highlighting
        y_original = y_data.copy()

        # Handle missing/problematic data
        y_data = self.handle_missing_data(y_data, series.missing_data_method)

        # Filter valid data
        if isinstance(x_data, pd.Series):
            valid_mask = ~(x_data.isna() | y_data.isna())
            x_plot = x_data[valid_mask]
            y_plot = y_data[valid_mask]
        else:
            valid_mask = ~y_data.isna()
            x_plot = x_data[valid_mask] if hasattr(x_data, '__getitem__') else [x for x, v in zip(x_data, valid_mask) if
                                                                                v]
            y_plot = y_data[valid_mask]

        if len(x_plot) == 0:
            return

        # Apply smoothing if requested
        if series.smooth_factor > 0 and len(y_plot) > 5:
            window_size = max(5, int(len(y_plot) * series.smooth_factor / 100))
            if window_size % 2 == 0:
                window_size += 1
            try:
                y_plot_smooth = savgol_filter(y_plot, window_size, 3)
            except:
                y_plot_smooth = y_plot
        else:
            y_plot_smooth = y_plot

        # Main plot
        if plot_type == 'line':
            # Plot normal data
            line = ax.plot(x_plot, y_plot_smooth,
                           color=series.color,
                           linestyle=series.line_style,
                           linewidth=series.line_width,
                           marker=series.marker if series.marker else None,
                           markersize=series.marker_size,
                           alpha=series.alpha,
                           label=series.legend_label if series.show_in_legend else "")

            if series.fill_area:
                ax.fill_between(x_plot, y_plot_smooth, alpha=series.alpha * 0.3, color=series.color)

        elif plot_type == 'scatter':
            ax.scatter(x_plot, y_plot_smooth,
                       color=series.color,
                       s=series.marker_size ** 2,
                       marker=series.marker if series.marker else 'o',
                       alpha=series.alpha,
                       label=series.legend_label if series.show_in_legend else "")

        # Highlight problematic data if configured
        if hasattr(self, 'plot_config_extra') and self.plot_config_extra:
            self.highlight_problematic_data(ax, x_data, y_original, problematic_mask, problem_types, series)

        # Add analysis features
        if series.show_trendline and plot_type in ['scatter', 'line']:
            self.add_trendline(ax, x_plot, y_plot, series)

        if series.show_peaks:
            self.mark_peaks(ax, x_plot, y_plot_smooth, series)

        if series.show_statistics:
            self.add_statistics_box(ax, y_plot, series)

        if series.highlight_base_pressure:
            base_pressure, _, _ = VacuumAnalysisTools.calculate_base_pressure(y_plot_smooth)
            ax.axhline(y=base_pressure, color='green', linestyle='--', alpha=0.5,
                       label=f'Base: {base_pressure:.2e}')

        if series.highlight_spikes:
            spikes = VacuumAnalysisTools.detect_pressure_spikes(y_plot_smooth)
            for spike in spikes:
                if spike['severity'] == 'high':
                    ax.axvspan(x_plot.iloc[spike['start']], x_plot.iloc[spike['end']],
                               color='red', alpha=0.2)

        # Format datetime axis if needed
        if pd.api.types.is_datetime64_any_dtype(x_data):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.figure.autofmt_xdate()

    def detect_problematic_data(self, y_data, series):
        """
        Detect various types of problematic data

        Returns:
            tuple: (problematic_mask, problem_types)
        """
        problematic_mask = np.zeros(len(y_data), dtype=bool)
        problem_types = []

        # Get config
        config = getattr(self, 'plot_config_extra', {})

        # Detect zeros
        if config.get('detect_zeros', True):
            zero_mask = (y_data == 0) | (y_data <= 1e-10)  # Consider very small values as zeros
            if zero_mask.any():
                problematic_mask |= zero_mask
                problem_types.append(('zeros', zero_mask))

        # Detect outliers
        if config.get('detect_outliers', True):
            threshold = config.get('outlier_threshold', 3.0)
            mean = np.nanmean(y_data)
            std = np.nanstd(y_data)
            outlier_mask = np.abs(y_data - mean) > threshold * std
            if outlier_mask.any():
                problematic_mask |= outlier_mask
                problem_types.append(('outliers', outlier_mask))

        # Detect sudden jumps/drops
        if config.get('detect_gaps', True):
            # Calculate differences
            diff = np.abs(np.diff(y_data))
            median_diff = np.nanmedian(diff)
            if median_diff > 0:
                jump_threshold = 10 * median_diff
                jump_mask = np.zeros(len(y_data), dtype=bool)
                jump_indices = np.where(diff > jump_threshold)[0]
                for idx in jump_indices:
                    if idx < len(jump_mask) - 1:
                        jump_mask[idx:idx + 2] = True
                if jump_mask.any():
                    problematic_mask |= jump_mask
                    problem_types.append(('jumps', jump_mask))

        # Detect NaN/missing values
        nan_mask = pd.isna(y_data)
        if nan_mask.any():
            problematic_mask |= nan_mask
            problem_types.append(('missing', nan_mask))

        return problematic_mask, problem_types

    def highlight_problematic_data(self, ax, x_data, y_data, problematic_mask, problem_types, series):
        """Highlight problematic data points on the plot"""
        config = getattr(self, 'plot_config_extra', {})

        # Convert to arrays for indexing
        x_array = np.array(x_data)
        y_array = np.array(y_data)

        for problem_type, mask in problem_types:
            if not mask.any():
                continue

            # Get indices where problem occurs
            problem_indices = np.where(mask)[0]

            if problem_type == 'zeros' and config.get('detect_zeros', True):
                # Highlight zero values
                color = config.get('zero_color', 'red')
                for idx in problem_indices:
                    if idx < len(x_array) and idx < len(y_array):
                        ax.scatter(x_array[idx], y_array[idx],
                                   color=color, s=100, marker='x',
                                   linewidths=3, zorder=10, alpha=0.8)

                # Add to legend
                ax.scatter([], [], color=color, marker='x', s=100,
                           linewidths=3, label=f'{series.name}: Zero/Invalid')

            elif problem_type == 'outliers' and config.get('detect_outliers', True):
                # Highlight outliers
                for idx in problem_indices:
                    if idx < len(x_array) and idx < len(y_array):
                        ax.scatter(x_array[idx], y_array[idx],
                                   color='orange', s=150, marker='D',
                                   edgecolors='red', linewidths=2,
                                   zorder=10, alpha=0.7)

                ax.scatter([], [], color='orange', marker='D', s=150,
                           edgecolors='red', linewidths=2,
                           label=f'{series.name}: Outliers')

            elif problem_type == 'jumps' and config.get('detect_gaps', True):
                # Highlight data jumps/gaps
                for idx in problem_indices:
                    if idx < len(x_array) - 1:
                        ax.plot([x_array[idx], x_array[idx + 1]],
                                [y_array[idx], y_array[idx + 1]],
                                'r--', linewidth=2, alpha=0.5)

            elif problem_type == 'missing' and config.get('highlight_missing', True):
                # Mark missing data regions
                color = config.get('missing_color', 'gray')
                # Group consecutive missing values
                groups = []
                current_group = []
                for idx in problem_indices:
                    if not current_group or idx == current_group[-1] + 1:
                        current_group.append(idx)
                    else:
                        groups.append(current_group)
                        current_group = [idx]
                if current_group:
                    groups.append(current_group)

                # Shade missing data regions
                for group in groups:
                    if len(group) > 1:
                        start_idx = max(0, group[0] - 1)
                        end_idx = min(len(x_array) - 1, group[-1] + 1)
                        ax.axvspan(x_array[start_idx], x_array[end_idx],
                                   color=color, alpha=0.2, label='Missing Data')

    def handle_missing_data(self, y_data, method):
        """Handle missing data according to specified method"""
        if method == 'drop':
            return y_data.dropna()
        elif method == 'fill_zero':
            return y_data.fillna(0)
        elif method == 'forward_fill':
            return y_data.fillna(method='ffill')
        elif method == 'interpolate':
            return y_data.interpolate()
        else:
            return y_data

    def add_trendline(self, ax, x_data, y_data, series):
        """Add trendline to plot"""
        try:
            if pd.api.types.is_datetime64_any_dtype(x_data):
                x_numeric = pd.to_numeric(x_data)
            else:
                x_numeric = pd.to_numeric(x_data, errors='coerce')

            y_numeric = pd.to_numeric(y_data, errors='coerce')

            valid = ~(x_numeric.isna() | y_numeric.isna())
            if valid.sum() < 2:
                return

            x_valid = x_numeric[valid].values
            y_valid = y_numeric[valid].values

            if series.trend_type == 'linear':
                x_valid_2d = x_valid.reshape(-1, 1)
                reg = LinearRegression()
                reg.fit(x_valid_2d, y_valid)

                x_trend = np.array([x_valid.min(), x_valid.max()]).reshape(-1, 1)
                y_trend = reg.predict(x_trend)

                ax.plot(x_trend.flatten(), y_trend,
                        color=series.color,
                        linestyle='--',
                        linewidth=series.line_width * 0.8,
                        alpha=series.alpha * 0.7,
                        label=f"{series.name} trend (R²={reg.score(x_valid_2d, y_valid):.3f})")

            elif series.trend_type == 'polynomial':
                degree = series.trend_params.get('degree', 2)
                coeffs = np.polyfit(x_valid, y_valid, degree)
                poly = np.poly1d(coeffs)

                x_trend = np.linspace(x_valid.min(), x_valid.max(), 100)
                y_trend = poly(x_trend)

                ax.plot(x_trend, y_trend,
                        color=series.color,
                        linestyle='--',
                        linewidth=series.line_width * 0.8,
                        alpha=series.alpha * 0.7,
                        label=f"{series.name} poly{degree}")

            elif series.trend_type == 'moving_average':
                window = series.trend_params.get('window', 20)
                ma = pd.Series(y_valid).rolling(window=window, center=True).mean()

                ax.plot(x_valid, ma,
                        color=series.color,
                        linestyle='--',
                        linewidth=series.line_width * 0.8,
                        alpha=series.alpha * 0.7,
                        label=f"{series.name} MA({window})")

        except Exception as e:
            print(f"Failed to add trendline: {e}")

    def mark_peaks(self, ax, x_data, y_data, series):
        """Mark peaks and valleys on the plot"""
        try:
            data_range = np.max(y_data) - np.min(y_data)
            prominence = series.peak_prominence * data_range

            peak_results = DataAnalysisTools.find_peaks_and_valleys(
                np.array(x_data), np.array(y_data), prominence
            )

            if len(peak_results['peaks']['indices']) > 0:
                ax.scatter(peak_results['peaks']['x_values'],
                           peak_results['peaks']['y_values'],
                           marker='^', s=100, color='red', zorder=5,
                           label=f'{series.name} peaks')

            if len(peak_results['valleys']['indices']) > 0:
                ax.scatter(peak_results['valleys']['x_values'],
                           peak_results['valleys']['y_values'],
                           marker='v', s=100, color='blue', zorder=5,
                           label=f'{series.name} valleys')

        except Exception as e:
            print(f"Failed to mark peaks: {e}")

    def add_statistics_box(self, ax, y_data, series):
        """Add statistics box to plot"""
        try:
            stats = DataAnalysisTools.calculate_statistics(y_data)

            stats_text = f"{series.name}\n"
            stats_text += f"Mean: {stats['mean']:.3e}\n"
            stats_text += f"Std: {stats['std']:.3e}\n"
            stats_text += f"Min: {stats['min']:.3e}\n"
            stats_text += f"Max: {stats['max']:.3e}"

            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
                    verticalalignment='top', bbox=props)

        except Exception as e:
            print(f"Failed to add statistics: {e}")

    def configure_plot_axes(self, ax):
        """Configure plot axes and styling"""
        ax.set_title(self.title_var.get(), fontsize=self.title_size_var.get(), fontweight='bold', pad=20)
        ax.set_xlabel(self.xlabel_var.get(), fontsize=self.xlabel_size_var.get())
        ax.set_ylabel(self.ylabel_var.get(), fontsize=self.ylabel_size_var.get())

        if self.show_grid_var.get():
            ax.grid(True, linestyle=self.grid_style_var.get(),
                    alpha=self.grid_alpha_var.get(), which='both')
            ax.set_axisbelow(True)

        if self.show_legend_var.get():
            handles, labels = ax.get_legend_handles_labels()
            filtered = [(h, l) for h, l in zip(handles, labels) if l]
            if filtered:
                handles, labels = zip(*filtered)
                ax.legend(handles, labels, loc='best', frameon=True,
                          fancybox=True, shadow=True, fontsize=10)

        if self.log_scale_x_var.get():
            ax.set_xscale('log')
        if self.log_scale_y_var.get():
            ax.set_yscale('log')

        if not self.x_auto_scale.get():
            try:
                x_min = float(self.x_min_var.get())
                x_max = float(self.x_max_var.get())
                ax.set_xlim(x_min, x_max)
            except ValueError:
                pass

        if not self.y_auto_scale.get():
            try:
                y_min = float(self.y_min_var.get())
                y_max = float(self.y_max_var.get())
                ax.set_ylim(y_min, y_max)
            except ValueError:
                pass

    # ============= Analysis & Export Operations =============

    def show_analysis_panel(self):
        """Show the analysis tools panel"""
        if self.all_series:
            self.show_vacuum_analysis()
        else:
            self.status_bar.set_status("No series available for analysis", "warning")

    def show_vacuum_analysis(self):
        """Show vacuum-specific analysis tools"""
        if self.all_series:
            vacuum_dialog = VacuumAnalysisDialog(self, None, self.all_series, self.loaded_files)
            self.status_bar.set_status("Vacuum analysis tools opened", "info")
        else:
            self.status_bar.set_status("No series available for analysis", "warning")

    def show_annotation_panel(self):
        """Show the annotation manager panel"""
        ax = self.figure.axes[0] if self.figure and self.figure.axes else None
        annotation_dialog = AnnotationDialog(self, self.annotation_manager, self.figure, ax)
        self.status_bar.set_status("Annotation manager opened", "info")

    def show_advanced_data_selector(self):
        """Show advanced data selector for non-standard Excel layouts"""
        if not self.series_file_var.get():
            self.status_bar.set_status("Please select a source file first", "warning")
            return

        selection = self.series_file_var.get()
        file_id = selection.split('(')[-1].rstrip(')')
        matching_file = None
        for fid, fdata in self.loaded_files.items():
            if fid.startswith(file_id):
                matching_file = fdata
                break

        if not matching_file:
            return

        selector_dialog = DataSelectorDialog(
            self,
            matching_file,
            on_data_selected=lambda info: self.apply_advanced_selection(info)
        )

    def apply_advanced_selection(self, selection_info):
        """Apply the advanced data selection"""
        try:
            self.series_start_var.set(selection_info['start_row'])
            self.series_end_var.set(selection_info['end_row'])
            self.status_bar.set_status("Advanced selection applied", "success")
        except Exception as e:
            self.status_bar.set_status(f"Selection error: {str(e)}", "error")

    def show_export_dialog(self):
        """Show export options dialog"""
        export_dialog = ExportDialog(self)

    def export_plot(self):
        """Export the current plot"""
        if not self.figure:
            self.status_bar.set_status("No plot to export", "warning")
            return

        format_map = {
            'PNG (High Quality)': '.png',
            'PDF (Vector)': '.pdf',
            'SVG (Scalable)': '.svg',
            'JPG (Compressed)': '.jpg'
        }

        selected_format = self.export_format.get()
        default_ext = format_map.get(selected_format, '.png')

        filetypes = [
            ("PNG files", "*.png"),
            ("PDF files", "*.pdf"),
            ("SVG files", "*.svg"),
            ("JPG files", "*.jpg"),
            ("All files", "*.*")
        ]

        filename = filedialog.asksaveasfilename(
            title="Export Plot",
            defaultextension=default_ext,
            filetypes=filetypes
        )

        if filename:
            try:
                dpi = self.dpi_var.get()
                self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')
                self.status_bar.set_status(f"Plot exported to: {filename}", "success")
            except Exception as e:
                self.status_bar.set_status(f"Export failed: {str(e)}", "error")

    def export_all_data(self):
        """Export all series data to a single Excel file"""
        if not self.all_series:
            self.status_bar.set_status("No series to export", "warning")
            return

        filename = filedialog.asksaveasfilename(
            title="Export All Data",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if filename:
            try:
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    for series in self.all_series.values():
                        file_data = self.loaded_files.get(series.file_id)
                        if not file_data:
                            continue

                        start_idx = max(0, series.start_index)
                        end_idx = min(len(file_data.df), series.end_index or len(file_data.df))
                        data_slice = file_data.df.iloc[start_idx:end_idx]

                        if series.x_column == 'Index':
                            export_df = data_slice[[series.y_column]].copy()
                            export_df.insert(0, 'Index', range(start_idx, end_idx))
                        else:
                            cols = [series.x_column, series.y_column]
                            export_df = data_slice[cols].copy()

                        sheet_name = series.name[:31]
                        export_df.to_excel(writer, sheet_name=sheet_name, index=False)

                self.status_bar.set_status(f"Data exported to: {filename}", "success")

            except Exception as e:
                self.status_bar.set_status(f"Export failed: {str(e)}", "error")

    def export_series_config(self):
        """Export series configuration for later import"""
        if not self.all_series:
            self.status_bar.set_status("No series configuration to export", "warning")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Series Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                config = {
                    'version': '1.0',
                    'export_date': datetime.now().isoformat(),
                    'series': []
                }

                for series in self.all_series.values():
                    series_dict = {
                        'name': series.name,
                        'file': self.loaded_files[series.file_id].filepath,
                        'x_column': series.x_column,
                        'y_column': series.y_column,
                        'start_index': series.start_index,
                        'end_index': series.end_index,
                        'color': series.color,
                        'line_style': series.line_style,
                        'marker': series.marker,
                        'line_width': series.line_width,
                        'marker_size': series.marker_size,
                        'alpha': series.alpha,
                        'fill_area': series.fill_area,
                        'visible': series.visible,
                        'legend_label': series.legend_label,
                        'missing_data_method': series.missing_data_method,
                        'show_trendline': series.show_trendline,
                        'trend_type': series.trend_type,
                        'trend_params': series.trend_params
                    }
                    config['series'].append(series_dict)

                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)

                self.status_bar.set_status(f"Configuration exported to: {filename}", "success")

            except Exception as e:
                self.status_bar.set_status(f"Export failed: {str(e)}", "error")

    def export_dataframe(self, df, filename):
        """Export a dataframe to Excel or CSV"""
        filetypes = [
            ("Excel files", "*.xlsx"),
            ("CSV files", "*.csv"),
            ("All files", "*.*")
        ]

        export_filename = filedialog.asksaveasfilename(
            title=f"Export {os.path.basename(filename)}",
            defaultextension=".xlsx",
            filetypes=filetypes
        )

        if export_filename:
            try:
                if export_filename.endswith('.csv'):
                    df.to_csv(export_filename, index=False)
                else:
                    df.to_excel(export_filename, index=False)

                self.status_bar.set_status(f"Data exported to: {export_filename}", "success")
            except Exception as e:
                self.status_bar.set_status(f"Export failed: {str(e)}", "error")

    # ============= Project Operations =============

    def save_project(self):
        """Save the current project state"""
        filename = filedialog.asksaveasfilename(
            title="Save Project",
            defaultextension=".json",
            filetypes=[("Project files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                project_data = {
                    'version': '1.0',
                    'creation_date': datetime.now().isoformat(),
                    'files': [],
                    'series': [],
                    'plot_config': {
                        'title': self.title_var.get(),
                        'title_size': self.title_size_var.get(),
                        'xlabel': self.xlabel_var.get(),
                        'xlabel_size': self.xlabel_size_var.get(),
                        'ylabel': self.ylabel_var.get(),
                        'ylabel_size': self.ylabel_size_var.get(),
                        'log_scale_x': self.log_scale_x_var.get(),
                        'log_scale_y': self.log_scale_y_var.get(),
                        'show_grid': self.show_grid_var.get(),
                        'show_legend': self.show_legend_var.get(),
                        'grid_style': self.grid_style_var.get(),
                        'grid_alpha': self.grid_alpha_var.get(),
                        'fig_width': self.fig_width_var.get(),
                        'fig_height': self.fig_height_var.get(),
                        'plot_type': self.plot_type_var.get()
                    }
                }

                for file_id, file_data in self.loaded_files.items():
                    project_data['files'].append({
                        'id': file_id,
                        'filepath': file_data.filepath,
                        'filename': file_data.filename
                    })

                for series_id, series in self.all_series.items():
                    project_data['series'].append({
                        'id': series_id,
                        'name': series.name,
                        'file_id': series.file_id,
                        'x_column': series.x_column,
                        'y_column': series.y_column,
                        'start_index': series.start_index,
                        'end_index': series.end_index,
                        'color': series.color,
                        'line_style': series.line_style,
                        'marker': series.marker,
                        'line_width': series.line_width,
                        'marker_size': series.marker_size,
                        'alpha': series.alpha,
                        'fill_area': series.fill_area,
                        'visible': series.visible,
                        'legend_label': series.legend_label,
                        'missing_data_method': series.missing_data_method,
                        'show_trendline': series.show_trendline,
                        'trend_type': series.trend_type,
                        'trend_params': series.trend_params
                    })

                with open(filename, 'w') as f:
                    json.dump(project_data, f, indent=2)

                self.status_bar.set_status(f"Project saved to: {filename}", "success")

            except Exception as e:
                self.status_bar.set_status(f"Save failed: {str(e)}", "error")

    def load_project(self):
        """Load a saved project"""
        filename = filedialog.askopenfilename(
            title="Load Project",
            filetypes=[("Project files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    project_data = json.load(f)

                self.clear_all_files()

                file_mapping = {}
                for file_info in project_data['files']:
                    try:
                        filepath = file_info['filepath']
                        if os.path.exists(filepath):
                            if filepath.endswith('.csv'):
                                df = pd.read_csv(filepath)
                            else:
                                df = pd.read_excel(filepath)

                            file_data = FileData(filepath, df)
                            self.loaded_files[file_data.id] = file_data
                            file_mapping[file_info['id']] = file_data.id
                        else:
                            self.status_bar.set_status(f"File not found: {filepath}", "warning")
                    except Exception as e:
                        print(f"Error loading file {filepath}: {e}")

                for series_info in project_data['series']:
                    try:
                        old_file_id = series_info['file_id']
                        if old_file_id in file_mapping:
                            new_file_id = file_mapping[old_file_id]

                            series = SeriesConfig(
                                series_info['name'],
                                new_file_id,
                                series_info['x_column'],
                                series_info['y_column'],
                                series_info['start_index'],
                                series_info['end_index']
                            )

                            for prop in ['color', 'line_style', 'marker', 'line_width',
                                         'marker_size', 'alpha', 'fill_area', 'visible',
                                         'legend_label', 'missing_data_method', 'show_trendline',
                                         'trend_type', 'trend_params']:
                                if prop in series_info:
                                    setattr(series, prop, series_info[prop])

                            self.all_series[series.id] = series
                            self.loaded_files[new_file_id].series_list.append(series.id)

                    except Exception as e:
                        print(f"Error loading series: {e}")

                if 'plot_config' in project_data:
                    config = project_data['plot_config']
                    self.title_var.set(config.get('title', 'Multi-File Data Analysis'))
                    self.title_size_var.set(config.get('title_size', 16))
                    self.xlabel_var.set(config.get('xlabel', 'X Axis'))
                    self.xlabel_size_var.set(config.get('xlabel_size', 12))
                    self.ylabel_var.set(config.get('ylabel', 'Y Axis'))
                    self.ylabel_size_var.set(config.get('ylabel_size', 12))
                    self.log_scale_x_var.set(config.get('log_scale_x', False))
                    self.log_scale_y_var.set(config.get('log_scale_y', False))
                    self.show_grid_var.set(config.get('show_grid', True))
                    self.show_legend_var.set(config.get('show_legend', True))
                    self.grid_style_var.set(config.get('grid_style', '-'))
                    self.grid_alpha_var.set(config.get('grid_alpha', 0.3))
                    self.fig_width_var.set(config.get('fig_width', 14.0))
                    self.fig_height_var.set(config.get('fig_height', 9.0))
                    self.plot_type_var.set(config.get('plot_type', 'line'))

                self.update_files_display()
                self.update_series_display()
                self.update_series_file_combo()
                self.update_counts()

                self.status_bar.set_status(f"Project loaded from: {filename}", "success")

            except Exception as e:
                self.status_bar.set_status(f"Load failed: {str(e)}", "error")

    # ============= Utility Operations =============

    def update_counts(self):
        """Update file and series counts in status bar"""
        file_count = len(self.loaded_files)
        series_count = len(self.all_series)
        self.status_bar.update_counts(files=file_count, series=series_count)

    def toggle_x_manual_limits(self):
        """Toggle X-axis manual limit entry fields"""
        state = "normal" if not self.x_auto_scale.get() else "disabled"
        self.x_min_entry.configure(state=state)
        self.x_max_entry.configure(state=state)

    def toggle_y_manual_limits(self):
        """Toggle Y-axis manual limit entry fields"""
        state = "normal" if not self.y_auto_scale.get() else "disabled"
        self.y_min_entry.configure(state=state)
        self.y_max_entry.configure(state=state)

    def show_error_details(self, error_files):
        """Show detailed error information"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("File Loading Errors")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()

        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 400) // 2
        dialog.geometry(f"+{x}+{y}")

        content = ctk.CTkFrame(dialog)
        content.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            content,
            text=f"{len(error_files)} files failed to load:",
            font=("", 14, "bold")
        ).pack(pady=5)

        scroll_frame = ctk.CTkScrollableFrame(content, height=300)
        scroll_frame.pack(fill="both", expand=True, pady=10)

        for filename, error in error_files:
            error_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            error_frame.pack(fill="x", pady=5)

            ctk.CTkLabel(
                error_frame,
                text=os.path.basename(filename),
                font=("", 11, "bold"),
                anchor="w"
            ).pack(fill="x")

            ctk.CTkLabel(
                error_frame,
                text=error,
                text_color=ColorPalette.ERROR,
                anchor="w"
            ).pack(fill="x", padx=10)

        ctk.CTkButton(
            content,
            text="Close",
            command=dialog.destroy,
            width=100
        ).pack(pady=10)

    def on_window_resize(self, event=None):
        """Handle window resize events"""
        if event and event.widget == self:
            width = self.winfo_width()
            if width < 1400:
                if self.current_layout != "compact":
                    self.current_layout = "compact"
                    # Could switch to compact layout here
            else:
                if self.current_layout != "default":
                    self.current_layout = "default"
                    # Could switch to default layout here

    def cycle_layout(self):
        """Cycle through layout modes"""
        layouts = ["default", "compact"]
        current_idx = layouts.index(self.current_layout)
        next_idx = (current_idx + 1) % len(layouts)
        self.current_layout = layouts[next_idx]
        self.status_bar.set_status(f"Layout changed to: {self.current_layout}", "info")

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        current = ctk.get_appearance_mode().lower()
        new_mode = "light" if current == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.current_theme = new_mode

        if hasattr(self, 'figure') and self.figure:
            self.create_plot()

        self.status_bar.set_status(f"Theme changed to: {new_mode}", "info")

    def on_closing(self):
        """Handle window closing event"""
        if self.loaded_files or self.all_series:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Exit")
            dialog.geometry("350x150")
            dialog.transient(self)
            dialog.grab_set()

            x = (self.winfo_screenwidth() - 350) // 2
            y = (self.winfo_screenheight() - 150) // 2
            dialog.geometry(f"+{x}+{y}")

            ctk.CTkLabel(
                dialog,
                text="Do you want to quit?",
                font=("", 14)
            ).pack(pady=20)

            ctk.CTkLabel(
                dialog,
                text="Any unsaved work will be lost.",
                text_color=ColorPalette.WARNING
            ).pack()

            btn_frame = ctk.CTkFrame(dialog)
            btn_frame.pack(pady=20)

            ctk.CTkButton(
                btn_frame,
                text="Cancel",
                command=dialog.destroy,
                width=80
            ).pack(side="left", padx=10)

            ctk.CTkButton(
                btn_frame,
                text="Quit",
                command=self.destroy,
                fg_color=ColorPalette.ERROR,
                width=80
            ).pack(side="left", padx=10)
        else:
            self.destroy()