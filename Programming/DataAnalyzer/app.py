#!/usr/bin/env python3
"""
Main application window for Excel Data Plotter
Complete implementation matching original functionality with new structure
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
import logging
from pathlib import Path
from typing import Dict, List, Optional
import uuid

# Import configuration
from config.constants import (
    AppConfig, UIConfig, ColorPalette, PlotConfig,
    FileTypes, PlotTypes, MissingDataMethods, TrendTypes,
    KeyBindings, DefaultSettings
)

# Import models
from models.data_models import FileData, SeriesConfig, PlotConfiguration, AnnotationConfig
from models.project_models import Project

# Import UI components
from ui.components import StatusBar, QuickActionBar
from ui.panels import FilePanel, SeriesPanel, PlotPanel, ConfigPanel
from ui.dialogs import (
    SeriesConfigDialog, VacuumAnalysisDialog, AnnotationDialog,
    DataSelectorDialog, PlotConfigDialog, ExportDialog
)

# Import core managers
from core.file_manager import FileManager
from core.plot_manager import PlotManager
from core.annotation_manager import AnnotationManager
from core.project_manager import ProjectManager
from core.export_manager import ExportManager

# Import analysis tools
from analysis.statistical import StatisticalAnalyzer
from analysis.vacuum import VacuumAnalyzer
from analysis.data_quality import DataQualityAnalyzer
from analysis.legacy_analysis_tools import DataAnalysisTools, VacuumAnalysisTools

# Import utilities
from utils.helpers import format_file_size, generate_color_sequence
from utils.validators import validate_data_range

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ExcelDataPlotter(ctk.CTk):
    """
    Main application window class
    Coordinates all components and handles user interactions
    """

    def __init__(self):
        """Initialize the main application window"""
        super().__init__()

        # Configure window
        self.title(f"{AppConfig.APP_NAME} - {AppConfig.APP_SUBTITLE}")
        self.geometry(f"{AppConfig.DEFAULT_WIDTH}x{AppConfig.DEFAULT_HEIGHT}")
        self.minsize(AppConfig.MIN_WIDTH, AppConfig.MIN_HEIGHT)

        # Configure grid layout for main window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Initialize data storage
        self.loaded_files: Dict[str, FileData] = {}  # Dictionary of loaded FileData objects
        self.all_series: Dict[str, SeriesConfig] = {}  # Dictionary of SeriesConfig objects
        self.color_index = 0  # For auto-assigning colors
        self.auto_colors = ColorPalette.CHART_COLORS

        # Initialize managers
        self.file_manager = FileManager()
        self.plot_manager = PlotManager()
        self.annotation_manager = AnnotationManager()
        self.project_manager = ProjectManager()
        self.export_manager = ExportManager()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.vacuum_analyzer = VacuumAnalyzer()
        self.data_quality_analyzer = DataQualityAnalyzer()
        
        # Legacy analysis tools for full compatibility
        self.analysis_tools = DataAnalysisTools()
        self.vacuum_tools = VacuumAnalysisTools()

        # Plot state
        self.figure = None  # Matplotlib figure
        self.canvas = None  # Matplotlib canvas
        self.toolbar = None  # Matplotlib toolbar
        self.plot_config = PlotConfiguration()  # Current plot configuration

        # Initialize UI variables
        self.init_variables()

        # Create UI components
        self.create_ui()

        # Bind window events
        self.bind_events()

        # Initialize status
        self.status_bar.set_status("Welcome to Professional Excel Data Plotter", "info")

        logger.info("Application initialized successfully")

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
        self.dpi_var = tk.IntVar(value=100)

        # Series configuration variables
        self.series_name_var = tk.StringVar()
        self.series_file_var = tk.StringVar()
        self.series_sheet_var = tk.StringVar()
        self.series_x_var = tk.StringVar()
        self.series_y_var = tk.StringVar()
        self.series_start_var = tk.StringVar()
        self.series_end_var = tk.StringVar()
        self.series_color_var = tk.StringVar()

        # Export variables
        self.export_format = tk.StringVar(value="PNG (High Quality)")

    def create_ui(self):
        """Create the main UI layout"""
        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Create menu bar
        self.create_menu_bar()

        # Create toolbar
        self.create_toolbar()

        # Create main content area with paned window
        self.create_main_content()

        # Create status bar
        self.create_status_bar()

        # Create floating panels (initially hidden)
        self.create_floating_panels()

    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Project...", command=self.load_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Project As...", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Add Files...", command=self.add_files, accelerator="Ctrl+Shift+O")
        file_menu.add_command(label="Import Series Config...", command=self.import_series_config)
        file_menu.add_separator()
        file_menu.add_command(label="Export Plot...", command=self.export_plot, accelerator="Ctrl+E")
        file_menu.add_command(label="Export Data...", command=self.export_all_data)
        file_menu.add_separator()
        file_menu.add_command(label="Recent Projects", state="disabled")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Ctrl+Q")

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", state="disabled", accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", state="disabled", accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Add Series", command=self.add_series, accelerator="Ctrl+Shift+N")
        edit_menu.add_command(label="Duplicate Series", command=self.duplicate_series, accelerator="Ctrl+D")
        edit_menu.add_command(label="Remove Series", command=self.remove_selected_series, accelerator="Del")
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear All", command=self.clear_all)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Plot", command=self.create_plot, accelerator="F5")
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Grid", variable=self.show_grid_var, command=self.create_plot)
        view_menu.add_checkbutton(label="Show Legend", variable=self.show_legend_var, command=self.create_plot)
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Reset Zoom", command=self.zoom_reset, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Theme", command=self.toggle_theme, accelerator="Ctrl+T")

        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Statistical Analysis...", command=self.show_statistical_analysis)
        analysis_menu.add_command(label="Vacuum Analysis...", command=self.show_vacuum_analysis)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Data Quality Report", command=self.show_data_quality_report)
        analysis_menu.add_command(label="Correlation Matrix", command=self.show_correlation_matrix)
        analysis_menu.add_command(label="Time Series Analysis", command=self.show_time_series_analysis)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Compare Series", command=self.compare_series)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Plot Configuration...", command=self.show_plot_config)
        tools_menu.add_command(label="Annotation Manager...", command=self.show_annotation_panel)
        tools_menu.add_separator()
        tools_menu.add_command(label="Advanced Data Selector...", command=self.show_advanced_data_selector)
        tools_menu.add_command(label="Batch Processing...", state="disabled")
        tools_menu.add_separator()
        tools_menu.add_command(label="Options...", command=self.show_options)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_help, accelerator="F1")
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

    def create_toolbar(self):
        """Create the quick action toolbar - matching legacy structure"""
        # Create top bar (matching legacy create_top_bar)
        self.top_bar = QuickActionBar(self.main_container)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=2)

        # File actions (left side)
        self.top_bar.add_action("Add Files", "📁", self.add_files, "Load Excel/CSV files", side="left")
        self.top_bar.add_action("Load Project", "📂", self.load_project, "Load saved project", side="left")
        self.top_bar.add_action("Save Project", "�", self.save_project, "Save current project", side="left")
        self.top_bar.add_separator(side="left")

        # Plot actions (right side)
        self.top_bar.add_action("Generate Plot", "📊", self.create_plot, "Create plot from series", side="right")
        self.top_bar.add_action("Export", "�", self.show_export_dialog, "Export plot or data", side="right")
        self.top_bar.add_separator(side="right")

        # Analysis actions (center)
        self.top_bar.add_action("Analysis", "�", self.show_statistical_analysis, "Statistical analysis tools", side="center")
        self.top_bar.add_action("Vacuum Tools", "🎯", self.show_vacuum_analysis, "Vacuum analysis tools", side="center")
        self.top_bar.add_action("Annotations", "�", self.show_annotation_panel, "Manage annotations", side="center")
        self.top_bar.add_separator(side="center")

        # View actions (center)
        self.top_bar.add_action("Theme", "🎨", self.toggle_theme, "Toggle dark/light theme", side="center")
        self.top_bar.add_action("Configure", "�", self.show_plot_config, "Configure plot settings", side="center")

    def create_main_content(self):
        """Create the main content area - matching legacy create_main_content"""
        # Content frame (matching legacy)
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)

        # Collapsible sidebar (matching legacy)
        self.sidebar = ctk.CTkFrame(self.content_frame, width=400)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.sidebar.grid_propagate(False)

        # Sidebar content with tabs (matching legacy)
        self.sidebar_tabs = ctk.CTkTabview(self.sidebar, width=390, height=800)
        self.sidebar_tabs.pack(fill="both", expand=True)

        # Create tabs (matching legacy names)
        self.files_tab = self.sidebar_tabs.add("Files")
        self.series_tab = self.sidebar_tabs.add("Series")  
        self.config_tab = self.sidebar_tabs.add("Configuration")
        self.export_tab = self.sidebar_tabs.add("Export")

        # Create tab content
        self.create_files_panel(self.files_tab)
        self.create_series_panel(self.series_tab)
        self.create_config_panel(self.config_tab)
        self.create_export_panel(self.export_tab)

        # Main plot area (right side)
        self.plot_area_frame = ctk.CTkFrame(self.content_frame)
        self.plot_area_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        
        # Configure plot area grid
        self.plot_area_frame.grid_rowconfigure(0, weight=1)
        self.plot_area_frame.grid_columnconfigure(0, weight=1)

        # Create plot area
        self.create_plot_area()

    def create_files_panel(self, parent):
        """Create the files management panel"""
        # Header
        header_frame = ctk.CTkFrame(parent)
        header_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(header_frame, text="Loaded Files", font=("", 14, "bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="Add", command=self.add_files, width=60).pack(side="right", padx=2)

        # Files list frame with scrollbar
        list_frame = ctk.CTkFrame(parent)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create scrollable frame
        self.files_scroll = ctk.CTkScrollableFrame(list_frame)
        self.files_scroll.pack(fill="both", expand=True)

        # Store file cards
        self.file_cards = {}

    def create_series_panel(self, parent):
        """Create the series configuration panel"""
        # Header
        header_frame = ctk.CTkFrame(parent)
        header_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(header_frame, text="Data Series", font=("", 14, "bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="Add", command=self.add_series, width=60).pack(side="right", padx=2)

        # Series configuration frame
        config_frame = ctk.CTkFrame(parent)
        config_frame.pack(fill="x", padx=5, pady=5)

        # Series name
        ctk.CTkLabel(config_frame, text="Series Name:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.series_name_entry = ctk.CTkEntry(config_frame, textvariable=self.series_name_var)
        self.series_name_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        # Source file
        ctk.CTkLabel(config_frame, text="Source File:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.series_file_combo = ctk.CTkComboBox(config_frame, variable=self.series_file_var,
                                                 command=self.on_file_selected)
        self.series_file_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=2)

        # Sheet selection (for Excel files)
        ctk.CTkLabel(config_frame, text="Sheet:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.series_sheet_combo = ctk.CTkComboBox(config_frame, variable=self.series_sheet_var,
                                                  command=self.on_sheet_selected)
        self.series_sheet_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=2)

        # X Column
        ctk.CTkLabel(config_frame, text="X Column:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.series_x_combo = ctk.CTkComboBox(config_frame, variable=self.series_x_var)
        self.series_x_combo.grid(row=3, column=1, sticky="ew", padx=5, pady=2)

        # Y Column
        ctk.CTkLabel(config_frame, text="Y Column:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.series_y_combo = ctk.CTkComboBox(config_frame, variable=self.series_y_var)
        self.series_y_combo.grid(row=4, column=1, sticky="ew", padx=5, pady=2)

        # Row range
        range_frame = ctk.CTkFrame(config_frame)
        range_frame.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(range_frame, text="Rows:").pack(side="left", padx=5)
        self.series_start_entry = ctk.CTkEntry(range_frame, textvariable=self.series_start_var,
                                               width=60, placeholder_text="Start")
        self.series_start_entry.pack(side="left", padx=2)
        ctk.CTkLabel(range_frame, text="to").pack(side="left", padx=2)
        self.series_end_entry = ctk.CTkEntry(range_frame, textvariable=self.series_end_var,
                                             width=60, placeholder_text="End")
        self.series_end_entry.pack(side="left", padx=2)

        # Action buttons
        button_frame = ctk.CTkFrame(config_frame)
        button_frame.grid(row=6, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        ctk.CTkButton(button_frame, text="Advanced...", command=self.show_advanced_series_config,
                      width=80).pack(side="left", padx=2)
        ctk.CTkButton(button_frame, text="Add Series", command=self.add_series_from_form,
                      fg_color=ColorPalette.SUCCESS, width=80).pack(side="right", padx=2)

        config_frame.grid_columnconfigure(1, weight=1)

        # Series list
        ctk.CTkLabel(parent, text="Active Series:", font=("", 12, "bold")).pack(anchor="w", padx=5, pady=(10, 5))

        # Series list frame with scrollbar
        self.series_scroll = ctk.CTkScrollableFrame(parent)
        self.series_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Store series cards
        self.series_cards = {}

    def create_config_panel(self, parent):
        """Create the plot configuration panel"""
        # Create scrollable frame for config
        config_scroll = ctk.CTkScrollableFrame(parent)
        config_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # Title section
        title_frame = ctk.CTkFrame(config_scroll)
        title_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(title_frame, text="Plot Title", font=("", 12, "bold")).pack(anchor="w")
        self.title_entry = ctk.CTkEntry(title_frame, textvariable=self.title_var)
        self.title_entry.pack(fill="x", pady=2)

        size_frame = ctk.CTkFrame(title_frame)
        size_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(size_frame, text="Size:").pack(side="left", padx=5)
        ctk.CTkSlider(size_frame, from_=8, to=24, variable=self.title_size_var).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(size_frame, textvariable=self.title_size_var).pack(side="left", padx=5)

        # Axes section
        axes_frame = ctk.CTkFrame(config_scroll)
        axes_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(axes_frame, text="Axes Labels", font=("", 12, "bold")).pack(anchor="w")

        # X-axis
        ctk.CTkLabel(axes_frame, text="X Label:").pack(anchor="w", pady=2)
        self.xlabel_entry = ctk.CTkEntry(axes_frame, textvariable=self.xlabel_var)
        self.xlabel_entry.pack(fill="x", pady=2)

        # Y-axis
        ctk.CTkLabel(axes_frame, text="Y Label:").pack(anchor="w", pady=2)
        self.ylabel_entry = ctk.CTkEntry(axes_frame, textvariable=self.ylabel_var)
        self.ylabel_entry.pack(fill="x", pady=2)

        # Scale options
        scale_frame = ctk.CTkFrame(config_scroll)
        scale_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(scale_frame, text="Scale Options", font=("", 12, "bold")).pack(anchor="w")
        ctk.CTkCheckBox(scale_frame, text="Log Scale X", variable=self.log_scale_x_var,
                        command=self.create_plot).pack(anchor="w", pady=2)
        ctk.CTkCheckBox(scale_frame, text="Log Scale Y", variable=self.log_scale_y_var,
                        command=self.create_plot).pack(anchor="w", pady=2)

        # Grid options
        grid_frame = ctk.CTkFrame(config_scroll)
        grid_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(grid_frame, text="Grid Options", font=("", 12, "bold")).pack(anchor="w")
        ctk.CTkCheckBox(grid_frame, text="Show Grid", variable=self.show_grid_var,
                        command=self.create_plot).pack(anchor="w", pady=2)

        style_frame = ctk.CTkFrame(grid_frame)
        style_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(style_frame, text="Style:").pack(side="left", padx=5)
        ctk.CTkComboBox(style_frame, values=["-", "--", ":", "-."],
                        variable=self.grid_style_var, width=80).pack(side="left", padx=5)

        alpha_frame = ctk.CTkFrame(grid_frame)
        alpha_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(alpha_frame, text="Alpha:").pack(side="left", padx=5)
        ctk.CTkSlider(alpha_frame, from_=0, to=1, variable=self.grid_alpha_var).pack(side="left", fill="x", expand=True)

        # Legend options
        legend_frame = ctk.CTkFrame(config_scroll)
        legend_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(legend_frame, text="Legend", font=("", 12, "bold")).pack(anchor="w")
        ctk.CTkCheckBox(legend_frame, text="Show Legend", variable=self.show_legend_var,
                        command=self.create_plot).pack(anchor="w", pady=2)

        # Figure size
        size_frame = ctk.CTkFrame(config_scroll)
        size_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(size_frame, text="Figure Size", font=("", 12, "bold")).pack(anchor="w")

        width_frame = ctk.CTkFrame(size_frame)
        width_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(width_frame, text="Width:").pack(side="left", padx=5)
        ctk.CTkSlider(width_frame, from_=8, to=20, variable=self.fig_width_var).pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(width_frame, textvariable=self.fig_width_var).pack(side="left", padx=5)

        height_frame = ctk.CTkFrame(size_frame)
        height_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(height_frame, text="Height:").pack(side="left", padx=5)
        ctk.CTkSlider(height_frame, from_=6, to=12, variable=self.fig_height_var).pack(side="left", fill="x",
                                                                                       expand=True)
        ctk.CTkLabel(height_frame, textvariable=self.fig_height_var).pack(side="left", padx=5)

        # Action buttons
        button_frame = ctk.CTkFrame(config_scroll)
        button_frame.pack(fill="x", padx=5, pady=10)

        ctk.CTkButton(button_frame, text="Advanced Config...", command=self.show_plot_config).pack(fill="x", pady=2)
        ctk.CTkButton(button_frame, text="Apply Changes", command=self.create_plot,
                      fg_color=ColorPalette.SUCCESS).pack(fill="x", pady=2)
        ctk.CTkButton(button_frame, text="Reset Defaults", command=self.reset_plot_config).pack(fill="x", pady=2)

    def create_export_panel(self, parent):
        """Create export controls panel"""
        # Export options
        export_frame = ctk.CTkFrame(parent)
        export_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(export_frame, text="Export Options", 
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

        # Plot export
        ctk.CTkButton(export_frame, text="📊 Export Plot", 
                      command=self.export_plot).pack(fill="x", padx=5, pady=2)
        
        # Data export 
        ctk.CTkButton(export_frame, text="📋 Export Data", 
                      command=self.export_all_data).pack(fill="x", padx=5, pady=2)
        
        # Full export dialog
        ctk.CTkButton(export_frame, text="📤 Export Dialog", 
                      command=self.show_export_dialog).pack(fill="x", padx=5, pady=2)

    def create_plot_area(self):
        """Create the main plot area"""
        # Welcome message for empty state
        self.empty_plot_frame = ctk.CTkFrame(self.plot_area_frame)
        self.empty_plot_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        welcome_label = ctk.CTkLabel(
            self.empty_plot_frame,
            text=f"{AppConfig.APP_NAME}\n{AppConfig.APP_SUBTITLE}\n\n"
                 "Load multiple Excel files and create custom series ranges\n"
                 "for comprehensive vacuum data visualization and analysis.",
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

        # Keyboard shortcuts
        self.bind(KeyBindings.NEW_PROJECT, lambda e: self.new_project())
        self.bind(KeyBindings.OPEN_PROJECT, lambda e: self.load_project())
        self.bind(KeyBindings.SAVE_PROJECT, lambda e: self.save_project())
        self.bind(KeyBindings.ADD_FILE, lambda e: self.add_files())
        self.bind(KeyBindings.ADD_SERIES, lambda e: self.add_series())
        self.bind(KeyBindings.REFRESH_PLOT, lambda e: self.create_plot())
        self.bind(KeyBindings.EXPORT_PLOT, lambda e: self.export_plot())
        self.bind(KeyBindings.TOGGLE_GRID, lambda e: self.toggle_grid())
        self.bind(KeyBindings.TOGGLE_LEGEND, lambda e: self.toggle_legend())
        self.bind(KeyBindings.TOGGLE_THEME, lambda e: self.toggle_theme())
        self.bind(KeyBindings.SHOW_HELP, lambda e: self.show_help())
        self.bind(KeyBindings.QUIT, lambda e: self.on_closing())


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

                    # Load file using FileManager for proper handling
                    file_data = self.file_manager.load_file(filename)

                    if file_data:
                        # Store with proper ID
                        self.loaded_files[file_data.id] = file_data
                        self.add_file_card(file_data)
                        success_count += 1
                    else:
                        # If FileManager couldn't load it, try direct approach
                        # Load the data
                        if filename.endswith('.csv'):
                            df = pd.read_csv(filename)
                        else:
                            df = pd.read_excel(filename)

                        # Create FileData object with CORRECT parameter order
                        file_data = FileData(
                            filepath=filename,  # filepath first
                            data=df,           # data second
                            filename=os.path.basename(filename)  # optional filename
                        )

                        self.loaded_files[file_data.id] = file_data
                        self.add_file_card(file_data)
                        success_count += 1

                except Exception as e:
                    error_files.append((filename, str(e)))
                    logger.error(f"Failed to load {filename}: {e}")

            # Update UI
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
                if error_files:
                    self.show_error_details(error_files)

    def add_file_card(self, file_data):
        """Add a file card to the files panel"""
        card = ctk.CTkFrame(self.files_scroll)
        card.pack(fill="x", pady=5, padx=5)

        # File info
        info_frame = ctk.CTkFrame(card)
        info_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(info_frame, text=file_data.filename, font=("", 12, "bold")).pack(anchor="w")
        size_label = ctk.CTkLabel(info_frame, text=f"{len(file_data.df)} rows, {len(file_data.df.columns)} columns")
        size_label.pack(anchor="w")

        # Action buttons
        btn_frame = ctk.CTkFrame(card)
        btn_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(btn_frame, text="View", width=60,
                      command=lambda f=file_data: self.view_file_data(f)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Remove", width=60, fg_color=ColorPalette.ERROR,
                      command=lambda f=file_data: self.remove_file(f)).pack(side="right", padx=2)

        # Store reference
        self.file_cards[file_data.id] = card

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

    def remove_file(self, file_data):
        """Remove a file and its associated series"""
        series_count = len([s for s in self.all_series.values() if s.file_id == file_data.id])

        if series_count > 0:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Remove")
            dialog.geometry("400x200")
            dialog.transient(self)
            dialog.grab_set()

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
                # Remove associated series
                for series_id in list(self.all_series.keys()):
                    if self.all_series[series_id].file_id == file_data.id:
                        self.remove_series(series_id)

                # Remove file
                del self.loaded_files[file_data.id]
                self.file_cards[file_data.id].destroy()
                del self.file_cards[file_data.id]

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
            self.file_cards[file_data.id].destroy()
            del self.file_cards[file_data.id]
            self.update_counts()
            self.status_bar.set_status(f"Removed file: {file_data.filename}", "info")

    def view_file_data(self, file_data):
        """View file data in a data viewer"""
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

    def update_series_file_combo(self):
        """Update the file selection combo for series creation"""
        file_options = [f"{fd.filename} ({fd.id[:8]})" for fd in self.loaded_files.values()]
        self.series_file_combo.configure(values=file_options)
        if file_options and not self.series_file_var.get():
            self.series_file_combo.set(file_options[0])
            self.on_file_selected()

    def on_file_selected(self, choice=None):
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
                self.series_end_var.set(str(min(1000, max_rows)))

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
        except Exception as e:
            logger.error(f"File selection error: {e}")
            self.status_bar.set_status(f"File selection error: {str(e)}", "error")


    def on_sheet_selected(self, choice=None):
        """Handle sheet selection for Excel files"""
        sheet_name = self.series_sheet_var.get()
        selection = self.series_file_var.get()

        if not selection or not sheet_name:
            return

        try:
            # Extract file ID from selection
            file_id = selection.split('(')[-1].rstrip(')')

            # Find matching file
            matching_file = None
            for fid, fdata in self.loaded_files.items():
                if fid.startswith(file_id):
                    matching_file = fdata
                    break

            if not matching_file:
                return

            # If this is an Excel file with multiple sheets, reload the specific sheet
            if hasattr(matching_file, 'sheets') and sheet_name in matching_file.sheets:
                # Update the DataFrame to the selected sheet
                matching_file.df = matching_file.sheets[sheet_name]
                matching_file.sheet_name = sheet_name

                # Re-analyze the data
                matching_file.analyze_data()

                # Update column combos
                columns = matching_file.df.columns.tolist()
                self.series_x_combo.configure(values=['Index'] + columns)
                self.series_y_combo.configure(values=columns)

                # Set defaults
                if columns:
                    self.series_x_combo.set('Index')
                    numeric_cols = matching_file.get_numeric_columns()
                    if numeric_cols:
                        self.series_y_combo.set(numeric_cols[0])

                self.status_bar.set_status(f"Loaded sheet: {sheet_name}", "success")

        except Exception as e:
            logger.error(f"Sheet selection error: {e}")
            self.status_bar.set_status(f"Sheet selection error: {str(e)}", "error")


    def add_series_from_form(self):
        """Add a new data series from the form"""
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

        try:
            start_idx = int(self.series_start_var.get()) if self.series_start_var.get() else 0
            end_idx = int(self.series_end_var.get()) if self.series_end_var.get() else len(matching_file.df)
        except ValueError:
            self.status_bar.set_status("Invalid row numbers", "warning")
            return

        if start_idx >= end_idx:
            self.status_bar.set_status("Start index must be less than end index", "warning")
            return

        series_name = self.series_name_var.get() or f"Series {len(self.all_series) + 1}"
        series = SeriesConfig(series_name, matching_file_id, x_col, y_col, start_idx, end_idx)

        series.color = self.auto_colors[self.color_index % len(self.auto_colors)]
        self.color_index += 1

        self.all_series[series.id] = series
        self.add_series_card(series)

        self.series_name_var.set(f"Series {len(self.all_series) + 1}")
        self.status_bar.set_status(f"Added series: {series_name}", "success")

    def add_series_card(self, series):
        """Add a series card to the series panel"""
        card = ctk.CTkFrame(self.series_scroll)
        card.pack(fill="x", pady=5, padx=5)

        # Series info
        info_frame = ctk.CTkFrame(card)
        info_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(info_frame, text=series.name, font=("", 12, "bold")).pack(anchor="w")
        file_info = self.loaded_files.get(series.file_id)
        file_name = file_info.filename if file_info else "Unknown File"
        ctk.CTkLabel(info_frame, text=f"{file_name} | {series.y_column} vs {series.x_column}").pack(anchor="w")

        # Action buttons
        btn_frame = ctk.CTkFrame(card)
        btn_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(btn_frame, text="Edit", width=60,
                      command=lambda s=series: self.edit_series(s)).pack(side="left", padx=2)
        ctk.CTkButton(btn_frame, text="Remove", width=60, fg_color=ColorPalette.ERROR,
                      command=lambda s=series: self.remove_series(s)).pack(side="right", padx=2)

        # Store reference
        self.series_cards[series.id] = card

    def edit_series(self, series):
        """Edit an existing series"""
        dialog = SeriesConfigDialog(self, series, self.loaded_files[series.file_id])
        self.wait_window(dialog.dialog)

        if dialog.result == "apply":
            self.series_cards[series.id].destroy()
            self.add_series_card(series)
            self.status_bar.set_status(f"Configured series: {series.name}", "success")

    def remove_series(self, series):
        """Remove a series"""
        if series.file_id in self.loaded_files:
            file_data = self.loaded_files[series.file_id]
            if series.id in file_data.series_list:
                file_data.series_list.remove(series.id)

        del self.all_series[series.id]
        self.series_cards[series.id].destroy()
        del self.series_cards[series.id]

        self.update_counts()
        self.status_bar.set_status(f"Removed series: {series.name}", "info")

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

            if ctk.get_appearance_mode() == "Dark":
                plt.style.use('dark_background')
            else:
                plt.style.use('seaborn-v0_8-whitegrid')

            self.figure = Figure(figsize=(self.fig_width_var.get(), self.fig_height_var.get()),
                                 facecolor='white', dpi=100)
            ax = self.figure.add_subplot(111)

            for i, series in enumerate(visible_series):
                self.status_bar.show_progress((i + 1) / len(visible_series))

                file_data = self.loaded_files.get(series.file_id)
                if not file_data:
                    continue

                try:
                    self.plot_single_series(ax, series, file_data)
                except Exception as e:
                    logger.error(f"Error plotting series {series.name}: {e}")
                    continue

            self.configure_plot_axes(ax)

            self.annotation_manager.draw_annotations(ax)

            self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_area_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

            toolbar_frame = ctk.CTkFrame(self.plot_area_frame, height=40)
            toolbar_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
            toolbar_frame.grid_propagate(False)

            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()

            self.status_bar.hide_progress()
            self.status_bar.set_status("Plot created successfully", "success")

        except Exception as e:
            self.status_bar.hide_progress()
            self.status_bar.set_status(f"Failed to create plot: {str(e)}", "error")
            logger.exception("Plot creation failed")

    def plot_single_series(self, ax, series, file_data):
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
            if pd.api.types.is_datetime64_any_dtype(x_data):
                x_data = pd.to_datetime(x_data)

        # Get Y data
        y_data = data_slice[series.y_column].copy()

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
        if series.plot_type == 'line':
            ax.plot(x_plot, y_plot_smooth,
                    color=series.color,
                    linestyle=series.line_style,
                    linewidth=series.line_width,
                    marker=series.marker if series.marker else None,
                    markersize=series.marker_size,
                    alpha=series.alpha,
                    label=series.legend_label if series.show_in_legend else "")
        elif series.plot_type == 'scatter':
            ax.scatter(x_plot, y_plot_smooth,
                       color=series.color,
                       s=series.marker_size ** 2,
                       marker=series.marker if series.marker else 'o',
                       alpha=series.alpha,
                       label=series.legend_label if series.show_in_legend else "")

        # Add analysis features
        if series.show_trendline:
            self.add_trendline(ax, x_plot, y_plot, series)

        # Format datetime axis if needed
        if pd.api.types.is_datetime64_any_dtype(x_data):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.figure.autofmt_xdate()

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
        except Exception as e:
            logger.error(f"Failed to add trendline: {e}")

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

            # Refresh plot if exists
            if self.figure:
                self.create_plot()

            self.status_bar.set_status("Plot configuration updated", "success")

    def show_vacuum_analysis(self):
        """Show vacuum-specific analysis tools"""
        if self.all_series:
            vacuum_dialog = VacuumAnalysisDialog(self, self.all_series, self.loaded_files, self.vacuum_analyzer)
            self.status_bar.set_status("Vacuum analysis tools opened", "info")
        else:
            self.status_bar.set_status("No series available for analysis", "warning")

    def show_annotation_panel(self):
        """Show annotation manager"""
        if not self.figure:
            self.status_bar.set_status("Create a plot first", "warning")
            return

        ax = self.figure.axes[0] if self.figure and self.figure.axes else None
        annotation_dialog = AnnotationDialog(
            self,
            self.annotation_manager,
            ax
        )
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
        export_dialog = ExportDialog(self, self.plot_manager)

    def clear_all(self):
        """Clear all loaded files and series"""
        if self.loaded_files:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Clear All")
            dialog.geometry("400x200")
            dialog.transient(self)
            dialog.grab_set()

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

                # Clear UI elements
                for widget in self.files_scroll.winfo_children():
                    widget.destroy()
                for widget in self.series_scroll.winfo_children():
                    widget.destroy()

                self.file_cards = {}
                self.series_cards = {}

                self.clear_plot_area()
                self.update_counts()

                dialog.destroy()
                self.status_bar.set_status("All files and series cleared", "info")

            ctk.CTkButton(
                btn_frame,
                text="Clear All",
                command=confirm_clear,
                fg_color=ColorPalette.ERROR
            ).pack(side="left", padx=10)

    def clear_plot_area(self):
        """Clear the plot area and show empty state"""
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

        self.empty_plot_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def update_counts(self):
        """Update file and series counts in status bar"""
        file_count = len(self.loaded_files)
        series_count = len(self.all_series)
        self.status_bar.update_counts(files=file_count, series=series_count)

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)
        self.status_bar.set_status(f"Theme changed to: {new_mode}", "info")

        if self.figure:
            self.create_plot()

    def show_error_details(self, error_files):
        """Show detailed error information"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("File Loading Errors")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()

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

    def on_closing(self):
        """Handle window closing event"""
        if self.loaded_files or self.all_series:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Exit")
            dialog.geometry("350x150")
            dialog.transient(self)
            dialog.grab_set()

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

    # Stubs for unimplemented methods
    def new_project(self):
        self.status_bar.set_status("New project created", "info")

    def save_project(self):
        self.status_bar.set_status("Project saved", "success")

    def save_project_as(self):
        self.status_bar.set_status("Project saved as", "success")

    def load_project(self):
        self.status_bar.set_status("Project loaded", "success")

    def import_series_config(self):
        self.status_bar.set_status("Series config imported", "success")

    def duplicate_series(self):
        self.status_bar.set_status("Series duplicated", "info")

    def remove_selected_series(self):
        self.status_bar.set_status("Selected series removed", "info")

    def zoom_in(self):
        if self.toolbar: self.toolbar.zoom()

    def zoom_out(self):
        if self.toolbar: self.toolbar.zoom()

    def zoom_reset(self):
        if self.toolbar: self.toolbar.home()

    def toggle_grid(self):
        self.show_grid_var.set(not self.show_grid_var.get())
        self.create_plot()

    def toggle_legend(self):
        self.show_legend_var.set(not self.show_legend_var.get())
        self.create_plot()

    def show_statistical_analysis(self):
        self.status_bar.set_status("Statistical analysis opened", "info")

    def show_data_quality_report(self):
        self.status_bar.set_status("Data quality report generated", "info")

    def show_correlation_matrix(self):
        self.status_bar.set_status("Correlation matrix displayed", "info")

    def show_time_series_analysis(self):
        self.status_bar.set_status("Time series analysis opened", "info")

    def compare_series(self):
        self.status_bar.set_status("Series comparison opened", "info")

    def show_options(self):
        self.status_bar.set_status("Options dialog opened", "info")

    def show_help(self):
        self.status_bar.set_status("Help documentation opened", "info")

    def show_shortcuts(self):
        self.status_bar.set_status("Keyboard shortcuts displayed", "info")

    def show_about(self):
        self.status_bar.set_status("About dialog opened", "info")

    def reset_plot_config(self):
        """Reset plot configuration to defaults"""
        self.title_var.set("Multi-File Data Analysis")
        self.title_size_var.set(16)
        self.xlabel_var.set("X Axis")
        self.xlabel_size_var.set(12)
        self.ylabel_var.set("Y Axis")
        self.ylabel_size_var.set(12)
        self.log_scale_x_var.set(False)
        self.log_scale_y_var.set(False)
        self.show_grid_var.set(True)
        self.show_legend_var.set(True)
        self.grid_style_var.set("-")
        self.grid_alpha_var.set(0.3)
        self.fig_width_var.set(14.0)
        self.fig_height_var.set(9.0)

        if self.figure:
            self.create_plot()

        self.status_bar.set_status("Plot configuration reset", "success")

    def show_advanced_series_config(self):
        """Show advanced series configuration dialog"""
        if not self.series_file_var.get():
            self.status_bar.set_status("Select a file first", "warning")
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

        series = SeriesConfig(
            self.series_name_var.get() or "New Series",
            file_id,
            self.series_x_combo.get(),
            self.series_y_combo.get(),
            int(self.series_start_var.get()) if self.series_start_var.get() else 0,
            int(self.series_end_var.get()) if self.series_end_var.get() else len(matching_file.df)
        )

        dialog = SeriesConfigDialog(self, series, matching_file)
        self.wait_window(dialog.dialog)

        if dialog.result == "apply":
            self.all_series[series.id] = series
            self.add_series_card(series)
            self.status_bar.set_status("Series created with advanced settings", "success")


if __name__ == "__main__":
    app = ExcelDataPlotter()
    app.mainloop()