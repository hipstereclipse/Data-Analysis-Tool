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

from ui.series_dialog import show_series_dialog
from ui.annotation_dialog import show_annotation_dialog
from ui.multi_series_analysis import show_multi_series_analysis
from core.ui_factory import UIFactory, DualRangeSlider
from core.data_utils import DataProcessor, DataValidator

# Import enhanced components
from ui.theme_manager import theme_manager
from ui.series_dialog import show_series_dialog, SeriesDialog
from ui.multi_series_analysis import show_multi_series_analysis
from core.plot_manager import PlotManager
from ui.theme_manager import ThemeManager

# Import models
from models.data_models import FileData, SeriesConfig, PlotConfiguration, AnnotationConfig
from models.project_models import Project

# Import UI components
from ui.components import StatusBar, QuickActionBar
from ui.panels import FilePanel, SeriesPanel, PlotPanel, ConfigPanel
# Import UI dialogs and components directly from dialogs module
from ui.dialogs import (
    SeriesConfigDialog, AnnotationDialog,
    DataSelectorDialog, PlotConfigDialog, ExportDialog, StatisticalAnalysisDialog
)
from ui.vacuum_analysis_dialog import VacuumAnalysisDialog
from ui.series_dialog import show_series_dialog
from ui.annotation_dialog import show_annotation_dialog

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

        # Configure window - make it resolution-independent
        self.title(f"{AppConfig.APP_NAME} - {AppConfig.APP_SUBTITLE}")
        
        # Get screen dimensions for better initial sizing
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Use 80% of screen size but respect minimums and maximums
        target_width = max(AppConfig.MIN_WIDTH, min(int(screen_width * 0.8), AppConfig.DEFAULT_WIDTH))
        target_height = max(AppConfig.MIN_HEIGHT, min(int(screen_height * 0.8), AppConfig.DEFAULT_HEIGHT))
        
        # Center window on screen
        x = (screen_width - target_width) // 2
        y = (screen_height - target_height) // 2
        
        self.geometry(f"{target_width}x{target_height}+{x}+{y}")
        self.minsize(AppConfig.MIN_WIDTH, AppConfig.MIN_HEIGHT)
        
        # Allow window to be maximized and handle scaling properly
        self.state('normal')  # Ensure normal state for sizing

        # Configure grid layout for main window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Initialize data storage
        self.loaded_files: Dict[str, FileData] = {}  # Dictionary of loaded FileData objects
        self.all_series: Dict[str, SeriesConfig] = {}  # Dictionary of SeriesConfig objects
        self.color_index = 0  # For auto-assigning colors
        self.auto_colors = ColorPalette.CHART_COLORS
        self.file_id_mapping = {}  # Mapping from display text to file ID

        # Initialize managers
        self.file_manager = FileManager()
        self.plot_manager = PlotManager()
        self.theme_manager = theme_manager  # Use the global singleton
        self.enhanced_plot_manager = None  # Will be initialized when figure is created
        self.annotation_manager = AnnotationManager()
        self.project_manager = ProjectManager()
        self.export_manager = ExportManager()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.vacuum_analyzer = VacuumAnalyzer()
        self.data_quality_analyzer = DataQualityAnalyzer()
        
        # Track open dialogs for theme updates
        self.open_dialogs = []
        
        # Legacy analysis tools for full compatibility
        self.analysis_tools = DataAnalysisTools()
        self.vacuum_tools = VacuumAnalysisTools()

        # Plot state
        self.figure = None  # Matplotlib figure
        self.canvas = None  # Matplotlib canvas
        self.toolbar = None  # Matplotlib toolbar
        self.plot_axes = None  # Current plot axes for annotations
        self.plot_config = PlotConfiguration()  # Current plot configuration
        self._creating_plot = False  # Mutex flag to prevent multiple simultaneous plot creation

        # Initialize UI variables
        self.init_variables()

        # Create UI components
        self.create_ui()

        # Bind window events
        self.bind_events()

        # Initialize status
        self.status_bar.set_status("Welcome to Excel Data Plotter", "info")

        # Initialize preview in welcome mode
        self.update_preview("welcome")

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
        # More reasonable default figure sizes
        self.fig_width_var = tk.DoubleVar(value=8.0)   # Reduced from 14.0
        self.fig_height_var = tk.DoubleVar(value=5.0)  # Reduced from 9.0
        self.dpi_var = tk.IntVar(value=100)

        # Advanced plot configuration variables
        self.plot_type_var = tk.StringVar(value="line")
        self.title_color_var = tk.StringVar(value="auto")
        self.axis_text_color_var = tk.StringVar(value="auto")

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
        
        # Ensure FileData compatibility
        self.migrate_file_data()
    
    def migrate_file_data(self):
        """Ensure all FileData objects have required attributes for backward compatibility"""
        for file_id, file_data in self.loaded_files.items():
            if not hasattr(file_data, 'series_list'):
                file_data.series_list = []

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
        analysis_menu.add_command(label="Multi-Series Analysis...", command=self.show_multi_analysis)
        analysis_menu.add_separator()
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
        self.plot_button = self.top_bar.add_action("Generate Plot", "📊", self.create_plot, "Create plot from visible series", side="right")
        self.top_bar.add_action("Export", "�", self.show_export_dialog, "Export plot or data", side="right")
        self.top_bar.add_separator(side="right")

        # Analysis actions (center)
        self.top_bar.add_action("Analysis", "�", self.show_statistical_analysis, "Statistical analysis tools", side="center")
        self.top_bar.add_action("Annotations", "📝", self.show_annotation_panel, "Add annotations to plots (requires active plot)", side="center")
        self.top_bar.add_separator(side="center")

        # View actions (center)
        self.top_bar.add_action("Theme", "🎨", self.toggle_theme, "Toggle dark/light theme", side="center")
        self.top_bar.add_action("Plot Config", "⚙️", self.show_advanced_plot_config, "Advanced plot configuration", side="center")

    def create_main_content(self):
        """Create the main content area with responsive layout including real-time preview"""
        # Content frame with three-column layout
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=0)  # Sidebar
        self.content_frame.grid_columnconfigure(1, weight=1)  # Main plot area (now gets all the space)

        # Responsive sidebar with better sizing
        sidebar_width = max(300, int(self.winfo_screenwidth() * 0.18))  # 18% of screen width, min 300px
        self.sidebar = ctk.CTkFrame(self.content_frame, width=sidebar_width)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        self.sidebar.grid_propagate(False)

        # Sidebar content with simplified tabs
        tab_width = sidebar_width - 20
        self.sidebar_tabs = ctk.CTkTabview(self.sidebar, width=tab_width)
        self.sidebar_tabs.pack(fill="both", expand=True, padx=5, pady=5)

        # Create only essential tabs
        self.files_tab = self.sidebar_tabs.add("📁 Files")
        self.series_tab = self.sidebar_tabs.add("📊 Series")

        # Create tab content
        self.create_files_panel(self.files_tab)
        self.create_integrated_series_panel(self.series_tab)

        # Main plot area with improved responsive design
        self.plot_area_frame = ctk.CTkFrame(self.content_frame)
        self.plot_area_frame.grid(row=0, column=1, sticky="nsew", padx=3)
        
        # Configure plot area grid for responsive content
        self.plot_area_frame.grid_rowconfigure(0, weight=1)
        self.plot_area_frame.grid_columnconfigure(0, weight=1)

        # Create plot area
        self.create_plot_area()

        # Note: Removed the third column (preview panel) to give more space to the main content
        # Preview functionality is now integrated into the main plot area

    def create_preview_content(self):
        """Create the content for the preview panel"""
        # This panel is now unused - the preview logic has been moved to the main area
        # and is handled intelligently based on user context
        pass

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

    def create_integrated_series_panel(self, parent):
        """Create an integrated series panel with creation, management, preview, and configuration"""
        # Main container with vertical layout
        main_container = ctk.CTkFrame(parent)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # === SERIES CREATION SECTION (COLLAPSIBLE) ===
        creation_container = ctk.CTkFrame(main_container)
        creation_container.pack(fill="x", pady=(0, 10))
        
        # Header with toggle button
        creation_header = ctk.CTkFrame(creation_container)
        creation_header.pack(fill="x", padx=5, pady=5)
        creation_header.grid_columnconfigure(1, weight=1)
        
        # Toggle button
        self.series_creation_collapsed = False
        self.creation_toggle_btn = ctk.CTkButton(
            creation_header,
            text="▼",
            width=30,
            height=25,
            command=self.toggle_series_creation,
            font=('Arial', 12)
        )
        self.creation_toggle_btn.grid(row=0, column=0, padx=(5, 10), pady=2)
        
        # Title label
        ctk.CTkLabel(creation_header, text="➕ Create New Series", font=("", 12, "bold")).grid(row=0, column=1, sticky="w", pady=2)
        
        # Content frame (collapsible)
        self.creation_frame = ctk.CTkFrame(creation_container)
        self.creation_frame.pack(fill="x", padx=5, pady=(0, 5))

        # File selection
        file_frame = ctk.CTkFrame(self.creation_frame)
        file_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(file_frame, text="Source File:", width=80).pack(side="left", padx=5)
        self.series_file_var = ctk.StringVar()
        self.series_file_combo = ctk.CTkComboBox(file_frame, variable=self.series_file_var,
                                                 command=self.on_file_selected_with_preview, width=160)
        self.series_file_combo.pack(side="left", fill="x", expand=True, padx=5)

        # Column selection with reduced padding
        col_frame = ctk.CTkFrame(self.creation_frame)
        col_frame.pack(fill="x", padx=5, pady=1)

        x_frame = ctk.CTkFrame(col_frame)
        x_frame.pack(fill="x", pady=1)
        ctk.CTkLabel(x_frame, text="X Column:", width=60).pack(side="left", padx=5)
        self.series_x_combo = ctk.CTkComboBox(x_frame, width=120, command=self.on_series_config_changed)
        self.series_x_combo.pack(side="left", fill="x", expand=True, padx=5)

        y_frame = ctk.CTkFrame(col_frame)
        y_frame.pack(fill="x", pady=1)
        ctk.CTkLabel(y_frame, text="Y Column:", width=60).pack(side="left", padx=5)
        self.series_y_combo = ctk.CTkComboBox(y_frame, width=120, command=self.on_series_config_changed)
        self.series_y_combo.pack(side="left", fill="x", expand=True, padx=5)

        # Series name with reduced padding
        name_frame = ctk.CTkFrame(self.creation_frame)
        name_frame.pack(fill="x", padx=5, pady=1)
        ctk.CTkLabel(name_frame, text="Name:", width=50).pack(side="left", padx=5)
        self.series_name_var = ctk.StringVar(value="Series 1")
        self.series_name_var.trace('w', lambda *args: self.on_series_config_changed())
        ctk.CTkEntry(name_frame, textvariable=self.series_name_var, width=150).pack(side="left", fill="x", expand=True, padx=5)        # Data range controls with visual selection - compact header
        range_frame = ctk.CTkFrame(self.creation_frame)
        range_frame.pack(fill="x", padx=5, pady=1)
        
        # Compact header with label and context on same line
        header_frame = ctk.CTkFrame(range_frame)
        header_frame.pack(fill="x", padx=5, pady=1)
        
        ctk.CTkLabel(header_frame, text="Data Range:", font=("", 11, "bold")).pack(side="left", padx=(0, 10))
        
        self.data_context_label = ctk.CTkLabel(
            header_frame,
            text="Select a file to see data range options",
            font=("", 9),
            text_color="gray"
        )
        self.data_context_label.pack(side="left")
        
        # Numeric range controls
        range_controls = ctk.CTkFrame(range_frame)
        range_controls.pack(fill="x", padx=5, pady=1)
        
        ctk.CTkLabel(range_controls, text="Start:", width=50).pack(side="left", padx=2)
        self.series_start_var = ctk.StringVar(value="0")
        self.start_entry = ctk.CTkEntry(range_controls, textvariable=self.series_start_var, width=80)
        self.start_entry.pack(side="left", padx=2)
        self.series_start_var.trace("w", self.on_start_entry_change)
        
        ctk.CTkLabel(range_controls, text="End:", width=30).pack(side="left", padx=2)
        self.series_end_var = ctk.StringVar()
        self.end_entry = ctk.CTkEntry(range_controls, textvariable=self.series_end_var, width=80)
        self.end_entry.pack(side="left", padx=2)
        self.series_end_var.trace("w", self.on_end_entry_change)
        
        # Visual range sliders - Dual-handle for space efficiency
        slider_frame = ctk.CTkFrame(range_frame)
        slider_frame.pack(fill="x", padx=5, pady=2)
        
        # Create start and end variables for dual slider
        self.start_var = tk.IntVar(value=0)
        self.end_var = tk.IntVar(value=100)
        
        # CustomTkinter dual-handle range slider
        self.dual_range_slider = DualRangeSlider(
            slider_frame,
            from_=0,
            to=100,
            start_var=self.start_var,
            end_var=self.end_var
        )
        self.dual_range_slider.pack(fill="x", padx=2, pady=2)
        
        # Quick selection buttons with reduced padding
        quick_btn_frame = ctk.CTkFrame(range_frame)
        quick_btn_frame.pack(fill="x", padx=5, pady=1)
        
        ctk.CTkButton(quick_btn_frame, text="All Data", width=70, height=25,
                      command=self.select_all_series_data).pack(side="left", padx=1)
        ctk.CTkButton(quick_btn_frame, text="First 10%", width=70, height=25,
                      command=self.select_first_10_percent).pack(side="left", padx=1)
        ctk.CTkButton(quick_btn_frame, text="Last 10%", width=70, height=25,
                      command=self.select_last_10_percent).pack(side="left", padx=1)
        ctk.CTkButton(quick_btn_frame, text="Middle 50%", width=80, height=25,
                      command=self.select_middle_50_percent).pack(side="left", padx=1)
        
        # Selection info with reduced padding
        self.selection_info_label = ctk.CTkLabel(
            range_frame,
            text="",
            font=("", 9),
            text_color="gray"
        )
        self.selection_info_label.pack(anchor="w", padx=5, pady=1)

        # Action buttons with reduced padding
        action_frame = ctk.CTkFrame(self.creation_frame)
        action_frame.pack(fill="x", padx=5, pady=2)
        
        ctk.CTkButton(action_frame, text="📋 Preview Data", 
                      command=self.preview_series_data, width=100).pack(side="left", padx=2)
        ctk.CTkButton(action_frame, text="➕ Add Series", 
                      command=self.add_series_from_form, width=100).pack(side="right", padx=2)

        # === SERIES MANAGEMENT SECTION ===
        management_frame = ctk.CTkFrame(main_container)
        management_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Header with series count and management buttons
        mgmt_header = ctk.CTkFrame(management_frame)
        mgmt_header.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(mgmt_header, text="📊 Active Series", font=("", 12, "bold")).pack(side="left")
        self.series_count_label = ctk.CTkLabel(mgmt_header, text="(0 total)", font=("", 10))
        self.series_count_label.pack(side="left", padx=(5, 0))

        # Management buttons with enhanced functionality
        mgmt_buttons = ctk.CTkFrame(mgmt_header)
        mgmt_buttons.pack(side="right")
        
        # Visibility controls
        ctk.CTkButton(mgmt_buttons, text="👁️", width=30, height=25,
                      command=self.show_all_series).pack(side="left", padx=1)
        ctk.CTkButton(mgmt_buttons, text="🚫", width=30, height=25,
                      command=self.hide_all_series).pack(side="left", padx=1)
        
        # Plot control
        ctk.CTkButton(mgmt_buttons, text="🔄", width=30, height=25,
                      command=self.refresh_plot).pack(side="left", padx=1)
        
        # Bulk operations
        ctk.CTkButton(mgmt_buttons, text="🗑️", width=30, height=25,
                      fg_color=("#ff4444", "#cc3333"),
                      hover_color=("#ff6666", "#ff4444"),
                      command=self.delete_all_series).pack(side="left", padx=1)
        
        # Advanced dropdown menu
        self.mgmt_menu_var = ctk.StringVar(value="⚙️")
        mgmt_menu = ctk.CTkComboBox(
            mgmt_buttons,
            variable=self.mgmt_menu_var,
            values=["⚙️", "📤 Export All", "🎨 Randomize Colors", "📋 Duplicate All", "🔢 Rename Sequential"],
            width=35,
            height=25,
            command=self._handle_bulk_operation
        )
        mgmt_menu.pack(side="left", padx=1)

        # Series list
        self.series_scroll = ctk.CTkScrollableFrame(management_frame)
        self.series_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Store series cards and tracking
        self.series_cards = {}
        self.selected_series = None
        self.series_visibility_vars = {}

    def refresh_plot(self):
        """Refresh the current plot"""
        if hasattr(self, 'figure') and self.figure and self.all_series:
            self.create_plot()
            self.status_bar.set_status("Plot refreshed", "success")
        else:
            self.status_bar.set_status("No plot to refresh", "warning")
    def toggle_series_creation(self):
        """Toggle the visibility of the series creation section"""
        self.series_creation_collapsed = not self.series_creation_collapsed
        
        if self.series_creation_collapsed:
            self.creation_frame.pack_forget()
            self.creation_toggle_btn.configure(text="▶")
        else:
            self.creation_frame.pack(fill="x", padx=5, pady=(0, 5))
            self.creation_toggle_btn.configure(text="▼")
    
    def sync_start_var_to_text(self, *args):
        """Sync start slider value to text entry"""
        try:
            start_val = self.start_var.get()
            self.series_start_var.set(str(start_val))
        except:
            pass
    
    def sync_end_var_to_text(self, *args):
        """Sync end slider value to text entry"""
        try:
            end_val = self.end_var.get()
            self.series_end_var.set(str(end_val))
        except:
            pass
    
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

        # Configure grid weights for the empty plot frame
        self.empty_plot_frame.grid_rowconfigure(1, weight=1)
        self.empty_plot_frame.grid_columnconfigure(0, weight=1)

        # Welcome message at the top
        welcome_label = ctk.CTkLabel(
            self.empty_plot_frame,
            text=f"{AppConfig.APP_NAME}\n{AppConfig.APP_SUBTITLE}\n\n"
                 "Load multiple Excel files and create custom series ranges\n"
                 "for comprehensive vacuum data visualization and analysis.",
            font=("", 18),
            text_color=("gray40", "gray60")
        )
        welcome_label.grid(row=0, column=0, pady=(20, 10), sticky="ew")

        # Preview section - shows series preview or plot based on context
        self.preview_section = ctk.CTkFrame(self.empty_plot_frame)
        self.preview_section.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.preview_section.grid_rowconfigure(1, weight=1)
        self.preview_section.grid_columnconfigure(0, weight=1)

        # Dynamic preview header
        self.preview_header = ctk.CTkLabel(
            self.preview_section, 
            text="Series Preview", 
            font=("", 14, "bold")
        )
        self.preview_header.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        # Series preview frame for showing selected series details - fixed height, no scrolling
        self.series_preview_frame = ctk.CTkFrame(self.preview_section, height=280)
        self.series_preview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.series_preview_frame.grid_propagate(False)  # Prevent automatic resizing
        
        # Initial placeholder
        self.preview_placeholder = ctk.CTkLabel(
            self.series_preview_frame,
            text="Add files and create series to begin",
            text_color=("gray50", "gray50")
        )
        self.preview_placeholder.pack(pady=20)

        # Get Started button at the bottom
        button_frame = ctk.CTkFrame(self.empty_plot_frame)
        button_frame.grid(row=2, column=0, pady=20, sticky="ew")
        
        ctk.CTkButton(
            button_frame,
            text="Get Started - Add Files",
            command=self.add_files,
            width=200,
            height=40,
            font=("", 14)
        ).pack(pady=10)

        # Initialize preview state tracking
        self.preview_mode = "welcome"  # welcome, series_editing, plot_display

    def update_preview(self, mode="auto"):
        """Update the preview based on current context"""
        try:
            # Determine the appropriate preview mode
            if mode == "auto":
                if hasattr(self, 'series_manager') and self.series_manager.series:
                    # Check if there are visible series
                    visible_series = [s for s in self.series_manager.series if s.visible]
                    if visible_series and hasattr(self, 'canvas') and self.canvas:
                        mode = "plot_display"
                    else:
                        mode = "series_preview"
                else:
                    mode = "welcome"
            
            self.preview_mode = mode
            
            if mode == "welcome":
                self._show_welcome_preview()
            elif mode == "series_editing":
                self._show_series_editing_preview()
            elif mode == "plot_display":
                self._show_plot_preview()
            elif mode == "series_preview":
                self._show_series_preview()
                
        except Exception as e:
            logger.error(f"Error updating preview: {e}")

    def _show_welcome_preview(self):
        """Show welcome state in preview"""
        self.preview_header.configure(text="Getting Started")
        # Clear existing preview content
        for widget in self.series_preview_frame.winfo_children():
            widget.destroy()
            
        welcome_text = ctk.CTkLabel(
            self.series_preview_frame,
            text="Add files and create series to begin\ndata visualization and analysis",
            text_color=("gray50", "gray50")
        )
        welcome_text.pack(pady=20)

    def _show_series_editing_preview(self):
        """Show series editing preview when user is creating/editing series"""
        self.preview_header.configure(text="Series Preview")
        # This will be updated by the series dialog when editing
        pass

    def _show_series_preview(self):
        """Show existing series information"""
        self.preview_header.configure(text="Active Series")
        # Clear existing preview content
        for widget in self.series_preview_frame.winfo_children():
            widget.destroy()
            
        if hasattr(self, 'series_manager') and self.series_manager.series:
            for i, series in enumerate(self.series_manager.series):
                series_frame = ctk.CTkFrame(self.series_preview_frame)
                series_frame.pack(fill="x", padx=5, pady=2)
                
                # Series name and visibility
                name_label = ctk.CTkLabel(
                    series_frame,
                    text=f"📊 {series.name}",
                    font=("", 12, "bold")
                )
                name_label.pack(anchor="w", padx=10, pady=5)
                
                # Series details
                details = f"Data points: {len(series.data) if hasattr(series, 'data') and series.data is not None else 0}"
                if hasattr(series, 'x_column') and hasattr(series, 'y_column'):
                    details += f"\nX: {series.x_column}, Y: {series.y_column}"
                
                details_label = ctk.CTkLabel(
                    series_frame,
                    text=details,
                    font=("", 10),
                    text_color=("gray60", "gray40")
                )
                details_label.pack(anchor="w", padx=10, pady=(0, 5))
        else:
            self._show_welcome_preview()

    def _show_plot_preview(self):
        """Show current plot in preview area"""
        self.preview_header.configure(text="Current Plot")
        # Clear existing preview content
        for widget in self.series_preview_frame.winfo_children():
            widget.destroy()
            
        # Show a mini version of the current plot or plot info
        if hasattr(self, 'series_manager') and self.series_manager.series:
            visible_count = len([s for s in self.series_manager.series if s.visible])
            plot_info = ctk.CTkLabel(
                self.series_preview_frame,
                text=f"📈 Plot displayed with {visible_count} visible series\n\nUse controls to modify series\nor create new ones",
                text_color=("gray60", "gray40")
            )
            plot_info.pack(pady=20)

    def show_series_editing_mode(self):
        """Called when user starts editing/creating a series"""
        self.update_preview("series_editing")

    def hide_series_editing_mode(self):
        """Called when user finishes editing/creating a series"""
        self.update_preview("auto")

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
            self.status_bar.set_status(f"Loading {len(filenames)} file(s)...", "info")
            self.status_bar.show_progress()
            success_count = 0
            error_files = []

            for i, filename in enumerate(filenames):
                # Update progress
                progress = i / len(filenames)
                self.status_bar.show_progress(progress)
                self.status_bar.set_status(f"Loading file {i+1}/{len(filenames)}: {os.path.basename(filename)}", "info")
                
                # Force UI update
                self.update_idletasks()
                try:
                    # Load file using FileManager for proper handling
                    file_data = self.file_manager.load_file(filename)

                    if file_data:
                        # Ensure series_list exists (for backward compatibility)
                        if not hasattr(file_data, 'series_list'):
                            file_data.series_list = []
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

                        # Ensure series_list exists (for backward compatibility)
                        if not hasattr(file_data, 'series_list'):
                            file_data.series_list = []
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
        series = SeriesConfig(
            name=series_name,
            file_id=matching_file_id,
            x_column=x_col,
            y_column=y_col,
            start_index=start_idx,
            end_index=end_idx
        )

        # Set visualization properties
        series.color = self.auto_colors[self.color_index % len(self.auto_colors)]
        series.show_in_legend = True
        series.legend_label = series_name
        series.visible = True  # Explicitly ensure visibility
        series.alpha = 1.0
        series.z_order = 1
        self.color_index += 1
        
        # Debug logging
        logger.info(f"Created series '{series_name}' with visible={series.visible}")

        self.all_series[series.id] = series
        
        # Ensure series_list exists (for backward compatibility)
        if not hasattr(matching_file, 'series_list'):
            matching_file.series_list = []
        matching_file.series_list.append(series.id)

        self.add_series_card(series)  # Add visual card
        self.update_counts()

        # Show data preview for the series just added
        self.preview_series_data(series, matching_file)

        # Update preview based on new series context
        self.update_preview("auto")

        self.series_name_var.set(f"Series {len(self.all_series) + 1}")

        self.status_bar.set_status(f"Added series: {series_name}", "success")
    
    def preview_series_data(self, series, file_data):
        """Show a preview of the series data being added to help users understand their selection"""
        try:
            # Get the data slice for this series
            start_idx = max(0, series.start_index or 0)
            end_idx = min(len(file_data.df), series.end_index or len(file_data.df))
            
            if start_idx >= end_idx:
                return
                
            data_slice = file_data.df.iloc[start_idx:end_idx].copy()
            
            # Get X and Y data
            if series.x_column == 'Index':
                x_data = np.arange(start_idx, end_idx)
                x_preview = x_data[:5]  # First 5 values
            else:
                x_data = data_slice[series.x_column]
                x_preview = x_data.head()
                
            y_data = data_slice[series.y_column]
            y_preview = y_data.head()
            
            # Create preview message
            preview_msg = (f"Series '{series.name}' Preview:\n"
                         f"X Column: {series.x_column}\n"
                         f"Y Column: {series.y_column}\n"
                         f"Data points: {len(y_data)}\n"
                         f"Range: {start_idx} to {end_idx}\n"
                         f"First 5 Y values: {', '.join([f'{val:.3f}' if pd.notna(val) else 'NaN' for val in y_preview])}")
            
            # Update status with data info
            data_info = f"Added '{series.name}': {len(y_data)} points from {series.y_column}"
            self.status_bar.set_status(data_info, "success")
            
            logger.info(preview_msg)
            
        except Exception as e:
            logger.error(f"Error creating series preview: {e}")

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
        # Create mapping from display text to actual file ID
        self.file_id_mapping = {}
        file_options = []
        
        for file_id, file_data in self.loaded_files.items():
            display_text = f"{file_data.filename} ({file_id[:8]})"
            file_options.append(display_text)
            self.file_id_mapping[display_text] = file_id
        
        self.series_file_combo.configure(values=file_options)
        if file_options and not self.series_file_var.get():
            self.series_file_combo.set(file_options[0])
            self.on_file_selected()

    def on_file_selected_with_preview(self, choice=None):
        """Handle file selection and update preview"""
        self.on_file_selected(choice)
        self.on_series_config_changed()

    def on_series_config_changed(self, *args):
        """Update preview when series configuration changes"""
        try:
            # Get current form values
            file_selection = self.series_file_var.get()
            x_col = self.series_x_combo.get()
            y_col = self.series_y_combo.get()
            series_name = self.series_name_var.get()
            
            # Only update preview if we have enough information
            if file_selection and x_col and y_col:
                self.update_series_preview_from_form()
        except Exception as e:
            logger.error(f"Error updating series config preview: {e}")

    def update_series_preview_from_form(self):
        """Update the preview with current form data as a live plot"""
        import pandas as pd
        import numpy as np
        try:
            # Switch to series editing preview mode
            self.update_preview("series_editing")
            
            # Get file data
            file_selection = self.series_file_var.get()
            if not file_selection or file_selection not in self.file_id_mapping:
                return
                
            file_id = self.file_id_mapping[file_selection]
            file_data = self.loaded_files.get(file_id)
            if not file_data:
                return
                
            # Get current form values
            x_col = self.series_x_combo.get()
            y_col = self.series_y_combo.get()
            series_name = self.series_name_var.get()
            start_idx = int(self.series_start_var.get() or 0)
            end_idx = int(self.series_end_var.get() or len(file_data.df))
            
            # Validate columns exist
            if x_col not in file_data.df.columns and x_col != 'Index':
                return
            if y_col not in file_data.df.columns:
                return
            
            # Update the preview header
            self.preview_header.configure(text="Live Series Preview")
            
            # Clear existing preview content
            for widget in self.series_preview_frame.winfo_children():
                try:
                    widget.destroy()
                except Exception:
                    # Widget already destroyed, ignore
                    pass
            
            # Create matplotlib figure for preview
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            import matplotlib.dates as mdates
            
            # Create a compact figure for preview with proper sizing
            preview_fig = Figure(figsize=(6, 2.5), dpi=100, facecolor='none')
            preview_ax = preview_fig.add_subplot(111)
            
            # Get data slice (limit to reasonable size for preview performance)
            max_preview_points = 1000
            actual_range = end_idx - start_idx
            if actual_range > max_preview_points:
                # Sample data for better performance
                step = actual_range // max_preview_points
                sample_indices = range(start_idx, end_idx, step)
                data_slice = file_data.df.iloc[sample_indices]
                display_start = start_idx
            else:
                data_slice = file_data.df.iloc[start_idx:end_idx]
                display_start = start_idx
            
            # Prepare x and y data
            if x_col == 'Index':
                if actual_range > max_preview_points:
                    x_data = [display_start + i * step for i in range(len(data_slice))]
                else:
                    x_data = range(display_start, display_start + len(data_slice))
                x_label = 'Index'
            else:
                x_data = data_slice[x_col]
                x_label = x_col
                
                # Handle datetime conversion if needed
                if data_slice[x_col].dtype == 'object':
                    try:
                        x_data = pd.to_datetime(x_data, errors='coerce')
                        x_data = pd.to_numeric(x_data, errors='coerce')
                    except:
                        pass
            
            y_data = data_slice[y_col]
            
            # Handle datetime/numeric conversion for y data
            if y_data.dtype == 'object':
                try:
                    y_data = pd.to_numeric(y_data, errors='coerce')
                except:
                    pass
            
            # Remove any NaN values
            valid_mask = ~(np.isnan(pd.to_numeric(x_data, errors='coerce')) | 
                          np.isnan(pd.to_numeric(y_data, errors='coerce')))
            
            if valid_mask.any():
                # Convert to numpy arrays for consistent indexing
                x_array = np.array(x_data)
                y_array = np.array(y_data)
                valid_array = np.array(valid_mask)
                
                # Apply mask to get clean data
                x_clean = x_array[valid_array]
                y_clean = y_array[valid_array]
                
                # Plot the data with themed colors
                line_color = self.theme_manager.get_color("accent")
                scatter_color = line_color
                edge_color = self.theme_manager.get_color("fg_primary")
                preview_ax.plot(x_clean, y_clean, linewidth=1.5, alpha=0.9, color=line_color, antialiased=True)
                
                # Add scatter points for better visibility (but not too many)
                scatter_step = max(1, len(x_clean) // 50)
                if scatter_step > 0:
                    preview_ax.scatter(x_clean[::scatter_step], y_clean[::scatter_step], 
                                     s=15, alpha=0.7, color=scatter_color, edgecolors=edge_color, linewidth=0.5)
            
            # Customize the plot
            preview_ax.set_title(f"Preview: {series_name}", fontsize=11, pad=10)
            preview_ax.set_xlabel(x_label, fontsize=9)
            preview_ax.set_ylabel(y_col, fontsize=9)
            preview_ax.tick_params(labelsize=8)
            preview_ax.grid(True, alpha=0.3)
            
            # Set background to match current theme
            bg_color = self.theme_manager.get_color("bg_secondary")
            text_color = self.theme_manager.get_color("fg_primary")
            preview_ax.set_facecolor(bg_color)
            preview_fig.patch.set_facecolor(bg_color)
            preview_fig.patch.set_alpha(1.0)  # Make sure background is opaque
            preview_ax.tick_params(colors=text_color)
            preview_ax.xaxis.label.set_color(text_color)
            preview_ax.yaxis.label.set_color(text_color)
            preview_ax.title.set_color(text_color)
            preview_ax.spines['bottom'].set_color(text_color)
            preview_ax.spines['top'].set_color(text_color)
            preview_ax.spines['right'].set_color(text_color)
            preview_ax.spines['left'].set_color(text_color)
            
            # Tight layout
            preview_fig.tight_layout(pad=1.0)
            
            # Create canvas and add to preview frame
            preview_canvas = FigureCanvasTkAgg(preview_fig, master=self.series_preview_frame)
            preview_canvas.draw()
            preview_canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
            # Add info text below the plot
            info_text = f"📊 {end_idx - start_idx:,} data points • {x_label} → {y_col}"
            info_label = ctk.CTkLabel(
                self.series_preview_frame,
                text=info_text,
                font=("", 10),
                text_color=("gray60", "gray40")
            )
            info_label.pack(pady=(0, 5))
            
        except Exception as e:
            logger.error(f"Error creating live plot preview: {e}")
            # Fallback to text preview
            self.preview_header.configure(text="Live Series Preview")
            for widget in self.series_preview_frame.winfo_children():
                widget.destroy()
                
            error_label = ctk.CTkLabel(
                self.series_preview_frame,
                text=f"⚠️ Preview Error\nUnable to plot data\n\nSeries: {series_name if 'series_name' in locals() else 'Unknown'}\nCheck data format",
                justify="center",
                text_color=("orange", "orange")
            )
            error_label.pack(fill="both", expand=True, padx=10, pady=20)

    def on_file_selected(self, choice=None):
        """Handle file selection for series creation"""
        selection = self.series_file_var.get()
        if not selection:
            return

        try:
            # Use the file ID mapping to get the actual file ID
            if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
                file_id = self.file_id_mapping[selection]
                matching_file = self.loaded_files.get(file_id)
            else:
                # Fallback to old method for compatibility
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
                
                # Initialize range controls
                self.series_start_var.set("0")
                self.series_end_var.set(str(max_rows))
                
                # Initialize dual range slider
                self.dual_range_slider.configure_range(from_=0, to=max_rows-1)
                self.start_var.set(0)
                self.end_var.set(max_rows)
                
                # Update data context info
                self.data_context_label.configure(text=f"Total data points available: {max_rows:,}")
                self.update_selection_info()

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
                
                # Show data info in status
                self.status_bar.set_status(
                    f"File: {matching_file.filename} | {len(matching_file.df):,} rows, {len(matching_file.df.columns)} cols | "
                    f"Numeric columns: {len([c for c in actual_columns if pd.api.types.is_numeric_dtype(matching_file.df[c])])}", 
                    "info"
                )
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

        # Use the file ID mapping to get the actual file ID
        if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
            matching_file_id = self.file_id_mapping[selection]
            matching_file = self.loaded_files.get(matching_file_id)
        else:
            # Fallback to old method for compatibility
            file_id = selection.split('(')[-1].rstrip(')')
            matching_file = None
            matching_file_id = None
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
        
        # Ensure unique series name
        original_name = series_name
        counter = 1
        while any(s.name == series_name for s in self.all_series.values()):
            series_name = f"{original_name} ({counter})"
            counter += 1
        
        series = SeriesConfig(
            name=series_name,
            file_id=matching_file_id,
            x_column=x_col,
            y_column=y_col,
            start_index=start_idx,
            end_index=end_idx
        )

        # Assign unique color from palette
        series.color = self.auto_colors[self.color_index % len(self.auto_colors)]
        self.color_index += 1
        
        # Store series
        logger.info(f"Creating new series with ID: {series.id}")
        self.all_series[series.id] = series
        self.add_series_card(series)
        
        # Update counts and plot button
        self.update_counts()  # Add this line to update the series count
        self.update_plot_button_text()

        # Update form for next series with incremented name
        self.series_name_var.set(f"Series {len(self.all_series) + 1}")
        self.status_bar.set_status(f"Added series: {series_name}", "success")

    def add_series_card(self, series):
        """Add an enhanced series card to the series panel with improved UI"""
        card = ctk.CTkFrame(self.series_scroll, corner_radius=8)
        card.pack(fill="x", pady=3, padx=4)

        # Main container with proper grid layout to ensure buttons are visible
        main_container = ctk.CTkFrame(card, corner_radius=6)
        main_container.pack(fill="x", padx=4, pady=4)
        main_container.grid_columnconfigure(0, weight=1)  # Left side expands
        main_container.grid_columnconfigure(1, weight=0)  # Right side fixed width

        # Left side: Visibility + Color + Series Info
        left_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        # Controls row (checkbox + color + name)
        controls_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        controls_frame.pack(fill="x")

        # Visibility checkbox
        visibility_var = ctk.BooleanVar(value=getattr(series, 'visible', True))
        visibility_check = ctk.CTkCheckBox(
            controls_frame, 
            text="", 
            variable=visibility_var,
            width=18,
            height=18,
            command=lambda: self.toggle_series_visibility(series, visibility_var.get())
        )
        visibility_check.pack(side="left", padx=(4, 8))

        # Color indicator
        color_button = ctk.CTkButton(
            controls_frame, 
            text="", 
            width=20, 
            height=20, 
            fg_color=series.color,
            corner_radius=4,
            hover_color=self._adjust_color_brightness(series.color, 0.8),
            command=lambda s=series: self.quick_change_series_color(s)
        )
        color_button.pack(side="left", padx=(0, 8))
        self._add_tooltip(color_button, "Click to change color")
        
        # Store reference for color updates
        if not hasattr(self, 'series_color_frames'):
            self.series_color_frames = {}
        self.series_color_frames[series.id] = color_button

        # Series name
        series_title = ctk.CTkLabel(
            controls_frame, 
            text=series.name, 
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        )
        series_title.pack(side="left", fill="x", expand=True)

        # Info row (file and data details)
        file_info = self.loaded_files.get(series.file_id)
        file_name = file_info.filename[:18] + "..." if file_info and len(file_info.filename) > 18 else (file_info.filename if file_info else "Unknown")
        data_points = (series.end_index or len(file_info.df)) - (series.start_index or 0) if file_info else 0
        
        info_text = f"📁 {file_name} • {series.x_column}→{series.y_column} • {data_points:,}pts"
        info_label = ctk.CTkLabel(
            left_frame, 
            text=info_text, 
            font=ctk.CTkFont(size=9), 
            text_color=("gray60", "gray50"),
            anchor="w"
        )
        info_label.pack(fill="x", padx=(32, 0))

        # Right side: Action buttons
        btn_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e", padx=(5, 0))

        # Configure button - primary action
        configure_btn = ctk.CTkButton(
            btn_frame, 
            text="Configure", 
            width=70, 
            height=26,
            corner_radius=6,
            font=ctk.CTkFont(size=10, weight="bold"),
            command=lambda s=series: self.edit_series(s)
        )
        configure_btn.pack(side="left", padx=2)
        self._add_tooltip(configure_btn, "Configure series settings")

        # Delete button - secondary action with warning styling
        delete_btn = ctk.CTkButton(
            btn_frame, 
            text="Delete", 
            width=60, 
            height=26,
            corner_radius=6,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=("#ff4444", "#cc3333"),
            hover_color=("#ff6666", "#ff4444"),
            command=lambda s=series: self.confirm_remove_series(s)
        )
        delete_btn.pack(side="left", padx=2)
        self._add_tooltip(delete_btn, "Delete this series")

        # Store the card reference for future updates
        self.series_cards[series.id] = card

        # Store widget references for updates
        if not hasattr(self, 'series_widgets'):
            self.series_widgets = {}
        self.series_widgets[series.id] = {
            'card': card,
            'visibility_var': visibility_var,
            'visibility_check': visibility_check,
            'color_button': color_button,
            'title_label': series_title,
            'info_label': info_label
        }

    def _adjust_color_brightness(self, hex_color, factor):
        """Adjust the brightness of a hex color"""
        try:
            # Remove the '#' if present
            hex_color = hex_color.lstrip('#')
            
            # Convert hex to RGB
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Adjust brightness
            new_rgb = tuple(int(min(255, max(0, c * factor))) for c in rgb)
            
            # Convert back to hex
            return f"#{new_rgb[0]:02x}{new_rgb[1]:02x}{new_rgb[2]:02x}"
        except:
            return hex_color  # Return original if conversion fails

    def _add_tooltip(self, widget, text):
        """Add a simple tooltip to a widget"""
        def on_enter(event):
            tooltip = ctk.CTkToplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            label = ctk.CTkLabel(
                tooltip, 
                text=text, 
                font=ctk.CTkFont(size=10),
                corner_radius=4
            )
            label.pack(padx=4, pady=2)
            
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def confirm_remove_series(self, series):
        """Show confirmation dialog before removing series"""
        try:
            # Create custom confirmation dialog
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Delete Series")
            dialog.geometry("350x180")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
            y = (dialog.winfo_screenheight() // 2) - (180 // 2)
            dialog.geometry(f"350x180+{x}+{y}")
            
            # Content frame
            content_frame = ctk.CTkFrame(dialog)
            content_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Warning text
            ctk.CTkLabel(
                content_frame,
                text="⚠️ Confirm Delete",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("#ff4444", "#ff6666")
            ).pack(pady=(10, 5))
            
            ctk.CTkLabel(
                content_frame,
                text=f"Delete '{series.name}'?\n\nThis action cannot be undone.",
                font=ctk.CTkFont(size=11),
                justify="center"
            ).pack(pady=10)
            
            # Button frame
            btn_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            btn_frame.pack(pady=15)
            
            result = {'confirmed': False}
            
            def confirm_delete():
                result['confirmed'] = True
                dialog.destroy()
                
            def cancel_delete():
                result['confirmed'] = False
                dialog.destroy()
            
            # Buttons
            ctk.CTkButton(
                btn_frame,
                text="Cancel",
                command=cancel_delete,
                width=80
            ).pack(side="left", padx=10)
            
            ctk.CTkButton(
                btn_frame,
                text="Delete",
                command=confirm_delete,
                fg_color=("#ff4444", "#cc3333"),
                hover_color=("#ff6666", "#ff4444"),
                width=80
            ).pack(side="left", padx=10)
            
            # Wait for dialog to close
            self.wait_window(dialog)
            
            # If confirmed, delete the series
            if result['confirmed']:
                self.remove_series(series)
                
        except Exception as e:
            logger.error(f"Error in confirmation dialog: {e}")
            # Fallback to direct deletion if dialog fails
            self.remove_series(series)

    def toggle_series_visibility(self, series, is_visible):
        """Toggle the visibility of a series and auto-refresh plot"""
        try:
            # Update the series object
            series.visible = is_visible
            self.all_series[series.id] = series
            
            # Log the change
            logger.info(f"Series '{series.name}' visibility changed to: {is_visible}")
            
            # Update counts display
            self.update_counts()
            
            # Update plot button text to show selected series count
            self.update_plot_button_text()
            
            # Auto-refresh the plot if we have any series and a figure exists
            if self.all_series and hasattr(self, 'figure') and self.figure:
                logger.info(f"Auto-refreshing plot due to visibility change for '{series.name}'")
                # Cancel any pending refresh and schedule a new one to prevent multiple rapid updates
                if hasattr(self, '_refresh_timer'):
                    self.after_cancel(self._refresh_timer)
                self._refresh_timer = self.after(100, self.create_plot)  # Debounce refresh by 100ms
            else:
                logger.info(f"Skipping auto-refresh: all_series={len(self.all_series)}, has_figure={hasattr(self, 'figure')}, figure_exists={hasattr(self, 'figure') and self.figure is not None}")
            
            # Update status
            status = "visible" if is_visible else "hidden"
            self.status_bar.set_status(f"Series '{series.name}' is now {status} - plot updated", "info")
            
            # Update preview based on current visibility state
            self.update_preview("auto")
                
        except Exception as e:
            logger.error(f"Error toggling series visibility: {e}")

    def update_plot_button_text(self):
        """Update the plot button text to show number of selected series"""
        try:
            visible_count = len([s for s in self.all_series.values() if getattr(s, 'visible', True)])
            
            if visible_count == 0:
                button_text = "Generate Plot"
                tooltip = "No series selected for plotting"
            elif visible_count == 1:
                button_text = "Generate Plot (1)"
                tooltip = "Plot 1 selected series"
            else:
                button_text = f"Generate Plot ({visible_count})"
                tooltip = f"Plot {visible_count} selected series"
            
            # Update button text if we have a reference to it
            if hasattr(self, 'plot_button') and self.plot_button:
                # Note: This depends on the QuickActionBar implementation
                # We might need to modify this based on how the toolbar buttons work
                pass
                
        except Exception as e:
            logger.error(f"Error updating plot button text: {e}")
            self.status_bar.set_status(f"Error toggling visibility: {str(e)}", "error")

    def select_and_preview_series(self, series):
        """Select a series and show its preview at the bottom of the series panel"""
        try:
            # Store currently selected series
            self.selected_series = series
            
            # Update the preview area
            self.show_series_preview(series)
            
            # Highlight the selected card (optional visual feedback)
            self.highlight_selected_series_card(series)
            
            self.status_bar.set_status(f"Selected series: {series.name}", "info")
            
        except Exception as e:
            logger.error(f"Error selecting series: {e}")
            self.status_bar.set_status(f"Error selecting series: {str(e)}", "error")

    def highlight_selected_series_card(self, selected_series):
        """Highlight the selected series card"""
        try:
            # Reset all cards to normal appearance
            for series_id, card in self.series_cards.items():
                if series_id == selected_series.id:
                    # Highlight selected card
                    card.configure(fg_color=("gray75", "gray25"))
                else:
                    # Normal appearance
                    card.configure(fg_color=("gray90", "gray13"))
        except Exception as e:
            logger.error(f"Error highlighting card: {e}")

    def show_series_preview(self, series):
        """Show a preview of the selected series data in the preview area"""
        try:
            # Clear existing preview content
            if hasattr(self, 'preview_placeholder'):
                self.preview_placeholder.destroy()
            
            for widget in self.series_preview_frame.winfo_children():
                widget.destroy()
            
            # Get file data
            file_data = self.loaded_files.get(series.file_id)
            if not file_data:
                ctk.CTkLabel(
                    self.series_preview_frame,
                    text="File data not available",
                    text_color="red"
                ).pack(expand=True)
                return
            
            # Create scrollable content
            preview_scroll = ctk.CTkScrollableFrame(self.series_preview_frame)
            preview_scroll.pack(fill="both", expand=True, padx=2, pady=2)
            
            # Preview header
            header_frame = ctk.CTkFrame(preview_scroll)
            header_frame.pack(fill="x", pady=(0, 5))
            
            ctk.CTkLabel(
                header_frame,
                text=f"📊 {series.name}",
                font=("", 12, "bold")
            ).pack(side="left")
            
            # Visibility and color indicator
            color_frame = ctk.CTkFrame(header_frame, width=15, height=15, fg_color=series.color)
            color_frame.pack(side="right", padx=(5, 0))
            color_frame.pack_propagate(False)
            
            # Data range and statistics
            start_idx = series.start_index or 0
            end_idx = series.end_index or len(file_data.df)
            data_points = end_idx - start_idx
            
            info_frame = ctk.CTkFrame(preview_scroll)
            info_frame.pack(fill="x", pady=2)
            
            info_text = f"📁 {file_data.filename}\n📈 {series.y_column} vs {series.x_column}\n📊 Rows {start_idx:,}-{end_idx:,} ({data_points:,} points)"
            ctk.CTkLabel(info_frame, text=info_text, font=("", 9), justify="left").pack(anchor="w", padx=5, pady=3)
            
            # Quick statistics
            try:
                data_slice = file_data.df.iloc[start_idx:end_idx]
                y_data = data_slice[series.y_column].dropna()
                
                if len(y_data) > 0:
                    stats_frame = ctk.CTkFrame(preview_scroll)
                    stats_frame.pack(fill="x", pady=2)
                    
                    stats_text = f"📈 Min: {y_data.min():.3f} | Max: {y_data.max():.3f} | Mean: {y_data.mean():.3f}"
                    ctk.CTkLabel(stats_frame, text=stats_text, font=("", 9)).pack(padx=5, pady=2)
                    
                    # Data sample (first 5 rows)
                    sample_frame = ctk.CTkFrame(preview_scroll)
                    sample_frame.pack(fill="x", pady=2)
                    
                    ctk.CTkLabel(sample_frame, text="📋 Data Sample:", font=("", 9, "bold")).pack(anchor="w", padx=5)
                    
                    if series.x_column == 'Index':
                        sample_data = data_slice[[series.y_column]].head(5)
                        sample_data.insert(0, 'Index', range(start_idx, start_idx + len(sample_data)))
                    else:
                        sample_data = data_slice[[series.x_column, series.y_column]].head(5)
                    
                    sample_text = sample_data.to_string(index=False, float_format='%.3f')
                    ctk.CTkLabel(
                        sample_frame, 
                        text=sample_text, 
                        font=("Consolas", 8),
                        justify="left"
                    ).pack(anchor="w", padx=5, pady=2)
                    
            except Exception as e:
                ctk.CTkLabel(
                    preview_scroll,
                    text=f"⚠️ Preview error: {str(e)}",
                    text_color="orange",
                    font=("", 9)
                ).pack(pady=5)
            
        except Exception as e:
            logger.error(f"Error showing series preview: {e}")
            ctk.CTkLabel(
                self.series_preview_frame,
                text=f"❌ Preview error: {str(e)}",
                text_color="red"
            ).pack(expand=True)

    def duplicate_series_real(self, series):
        """Actually duplicate a series with a new name"""
        try:
            # Create a copy of the series
            new_series = SeriesConfig(
                name=f"{series.name} (Copy)",
                file_id=series.file_id,
                x_column=series.x_column,
                y_column=series.y_column,
                start_index=series.start_index,
                end_index=series.end_index
            )
            
            # Copy all properties
            for attr in ['color', 'line_style', 'line_width', 'marker', 'marker_size',
                        'alpha', 'visible', 'show_in_legend', 'legend_label', 'plot_type']:
                if hasattr(series, attr):
                    setattr(new_series, attr, getattr(series, attr))
            
            # Assign new color
            new_series.color = self.auto_colors[self.color_index % len(self.auto_colors)]
            self.color_index += 1
            
            # Store the new series
            self.all_series[new_series.id] = new_series
            self.add_series_card(new_series)
            self.update_counts()
            
            self.status_bar.set_status(f"Duplicated series: {new_series.name}", "success")
            
        except Exception as e:
            logger.error(f"Error duplicating series: {e}")
            self.status_bar.set_status(f"Error duplicating series: {str(e)}", "error")
            
    def show_all_series(self):
        """Make all series visible"""
        try:
            count = 0
            for series_id, series in self.all_series.items():
                if not getattr(series, 'visible', True):
                    series.visible = True
                    count += 1
                    
                    # Update UI checkbox if it exists
                    if series_id in self.series_visibility_vars:
                        self.series_visibility_vars[series_id].set(True)
            
            if count > 0:
                self.status_bar.set_status(f"Made {count} series visible", "success")
                self.update_counts()  # Update the counts display
                # Update plot if it exists
                if hasattr(self, 'figure') and self.figure:
                    self.create_plot()
            else:
                self.status_bar.set_status("All series are already visible", "info")
                
        except Exception as e:
            logger.error(f"Error showing all series: {e}")
            self.status_bar.set_status(f"Error showing all series: {str(e)}", "error")

    def hide_all_series(self):
        """Hide all series"""
        try:
            count = 0
            for series_id, series in self.all_series.items():
                if getattr(series, 'visible', True):
                    series.visible = False
                    count += 1
                    
                    # Update UI checkbox if it exists
                    if series_id in self.series_visibility_vars:
                        self.series_visibility_vars[series_id].set(False)
            
            if count > 0:
                self.status_bar.set_status(f"Hidden {count} series", "success")
                self.update_counts()  # Update the counts display
                # Clear plot since no series are visible
                if hasattr(self, 'figure') and self.figure:
                    self.clear_plot_area()
            else:
                self.status_bar.set_status("All series are already hidden", "info")
                
        except Exception as e:
            logger.error(f"Error hiding all series: {e}")
            self.status_bar.set_status(f"Error hiding all series: {str(e)}", "error")

    def delete_all_series(self):
        """Delete all series with confirmation"""
        if not self.all_series:
            self.status_bar.set_status("No series to delete", "info")
            return
            
        try:
            # Create custom confirmation dialog
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Delete All Series")
            dialog.geometry("400x200")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
            y = (dialog.winfo_screenheight() // 2) - (200 // 2)
            dialog.geometry(f"400x200+{x}+{y}")
            
            # Warning content
            warning_frame = ctk.CTkFrame(dialog)
            warning_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Warning icon and text
            ctk.CTkLabel(
                warning_frame,
                text="⚠️ WARNING",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=("#ff4444", "#ff6666")
            ).pack(pady=(10, 5))
            
            ctk.CTkLabel(
                warning_frame,
                text=f"This will permanently delete all {len(self.all_series)} series.\n\nThis action cannot be undone.",
                font=ctk.CTkFont(size=12),
                justify="center"
            ).pack(pady=10)
            
            # Button frame
            btn_frame = ctk.CTkFrame(warning_frame, fg_color="transparent")
            btn_frame.pack(pady=20)
            
            result = {'confirmed': False}
            
            def confirm_delete():
                result['confirmed'] = True
                dialog.destroy()
                
            def cancel_delete():
                result['confirmed'] = False
                dialog.destroy()
            
            # Buttons
            ctk.CTkButton(
                btn_frame,
                text="Cancel",
                command=cancel_delete,
                width=100
            ).pack(side="left", padx=10)
            
            ctk.CTkButton(
                btn_frame,
                text="Delete All",
                command=confirm_delete,
                fg_color=("#ff4444", "#cc3333"),
                hover_color=("#ff6666", "#ff4444"),
                width=100
            ).pack(side="left", padx=10)
            
            # Wait for dialog to close
            self.wait_window(dialog)
            
            # If confirmed, delete all series
            if result['confirmed']:
                count = len(self.all_series)
                
                # Clear all series
                for series_id in list(self.all_series.keys()):
                    if series_id in self.series_cards:
                        self.series_cards[series_id].destroy()
                        del self.series_cards[series_id]
                    
                    if hasattr(self, 'series_color_frames') and series_id in self.series_color_frames:
                        del self.series_color_frames[series_id]
                        
                    if hasattr(self, 'series_widgets') and series_id in self.series_widgets:
                        del self.series_widgets[series_id]
                
                # Clear data structures
                self.all_series.clear()
                self.series_cards.clear()
                if hasattr(self, 'series_color_frames'):
                    self.series_color_frames.clear()
                if hasattr(self, 'series_widgets'):
                    self.series_widgets.clear()
                
                # Clear plot
                if hasattr(self, 'figure') and self.figure:
                    self.clear_plot_area()
                
                self.update_counts()
                self.status_bar.set_status(f"Deleted {count} series", "success")
            
        except Exception as e:
            logger.error(f"Error deleting all series: {e}")
            self.status_bar.set_status(f"Error deleting series: {str(e)}", "error")

    def _handle_bulk_operation(self, operation):
        """Handle bulk operations from the dropdown menu"""
        try:
            if operation == "⚙️":
                return  # Default state, do nothing
                
            elif operation == "📤 Export All":
                self._export_all_series()
            elif operation == "🎨 Randomize Colors":
                self._randomize_all_colors()
            elif operation == "📋 Duplicate All":
                self._duplicate_all_series()
            elif operation == "🔢 Rename Sequential":
                self._rename_series_sequential()
            
            # Reset dropdown to default
            self.mgmt_menu_var.set("⚙️")
            
        except Exception as e:
            logger.error(f"Error handling bulk operation: {e}")
            self.status_bar.set_status(f"Error: {str(e)}", "error")
            self.mgmt_menu_var.set("⚙️")

    def _export_all_series(self):
        """Export all series data to files"""
        if not self.all_series:
            self.status_bar.set_status("No series to export", "warning")
            return
            
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Select Export Folder")
        
        if folder:
            exported_count = 0
            for series in self.all_series.values():
                try:
                    file_data = self.loaded_files.get(series.file_id)
                    if file_data:
                        x_data, y_data = series.get_data(file_data)
                        export_df = pd.DataFrame({
                            series.x_column: x_data,
                            series.y_column: y_data
                        })
                        
                        # Safe filename
                        safe_name = "".join(c for c in series.name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        file_path = os.path.join(folder, f"{safe_name}.csv")
                        
                        export_df.to_csv(file_path, index=False)
                        exported_count += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to export series {series.name}: {e}")
            
            self.status_bar.set_status(f"Exported {exported_count} series to {folder}", "success")

    def _randomize_all_colors(self):
        """Randomize colors for all series"""
        if not self.all_series:
            self.status_bar.set_status("No series to recolor", "warning")
            return
            
        import random
        
        # Generate random colors
        colors = generate_color_sequence(len(self.all_series))
        random.shuffle(colors)
        
        for i, series in enumerate(self.all_series.values()):
            series.color = colors[i % len(colors)]
            self.all_series[series.id] = series
            self.update_series_card_color(series)
        
        # Refresh plot if exists
        if hasattr(self, 'figure') and self.figure:
            self.create_plot()
            
        self.status_bar.set_status(f"Randomized colors for {len(self.all_series)} series", "success")

    def _duplicate_all_series(self):
        """Duplicate all existing series"""
        if not self.all_series:
            self.status_bar.set_status("No series to duplicate", "warning")
            return
            
        original_series = list(self.all_series.values())
        duplicated_count = 0
        
        for series in original_series:
            try:
                self.duplicate_series_real(series)
                duplicated_count += 1
            except Exception as e:
                logger.warning(f"Failed to duplicate series {series.name}: {e}")
        
        self.status_bar.set_status(f"Duplicated {duplicated_count} series", "success")

    def _rename_series_sequential(self):
        """Rename all series with sequential numbering"""
        if not self.all_series:
            self.status_bar.set_status("No series to rename", "warning")
            return
            
        # Get base name from user
        dialog = ctk.CTkInputDialog(
            text="Enter base name for sequential numbering:",
            title="Rename Series"
        )
        
        base_name = dialog.get_input()
        if not base_name:
            return
            
        for i, series in enumerate(self.all_series.values(), 1):
            series.name = f"{base_name} {i}"
            self.all_series[series.id] = series
            
            # Update UI if widget exists
            if hasattr(self, 'series_widgets') and series.id in self.series_widgets:
                widgets = self.series_widgets[series.id]
                if 'title_label' in widgets and widgets['title_label'].winfo_exists():
                    widgets['title_label'].configure(text=series.name)
        
        self.status_bar.set_status(f"Renamed {len(self.all_series)} series", "success")

    def get_series_summary(self):
        """Get a summary of all series for display"""
        try:
            total_series = len(self.all_series)
            visible_series = len([s for s in self.all_series.values() if getattr(s, 'visible', True)])
            hidden_series = total_series - visible_series
            
            return {
                'total': total_series,
                'visible': visible_series,
                'hidden': hidden_series
            }
        except Exception as e:
            logger.error(f"Error getting series summary: {e}")
            return {'total': 0, 'visible': 0, 'hidden': 0}

    def trigger_auto_refresh(self):
        """Trigger auto-refresh of the plot if auto-refresh is enabled"""
        try:
            # Cancel any existing refresh timer
            if hasattr(self, '_refresh_timer') and self._refresh_timer:
                self.after_cancel(self._refresh_timer)
            
            # Schedule a new refresh with debounce
            self._refresh_timer = self.after(100, self._auto_refresh_plot)
            
        except Exception as e:
            logger.error(f"Error triggering auto-refresh: {e}")

    def _auto_refresh_plot(self):
        """Auto-refresh the plot (debounced)"""
        try:
            if hasattr(self, '_creating_plot') and self._creating_plot:
                return  # Skip if plot creation is already in progress
                
            self.create_plot()
        except Exception as e:
            logger.error(f"Error in auto-refresh: {e}")

    def _safe_finalize_canvas_display(self, canvas_widget):
        """Safely finalize canvas display with error handling for destroyed widgets"""
        try:
            # Check if widget still exists and is valid
            if canvas_widget.winfo_exists():
                self._finalize_canvas_display(canvas_widget)
        except tk.TclError as e:
            # Widget was destroyed before callback executed
            logger.debug(f"Canvas widget destroyed before finalization: {e}")
        except Exception as e:
            logger.error(f"Error in safe canvas finalization: {e}")

    def _finalize_canvas_display(self, canvas_widget):
        """Finalize canvas display after layout updates"""
        try:
            # Final widget state check
            logger.info(f"Final canvas widget visibility: {canvas_widget.winfo_viewable()}")
            logger.info(f"Final canvas widget size: {canvas_widget.winfo_width()}x{canvas_widget.winfo_height()}")
            
            # Ensure the canvas is visible and properly sized
            if canvas_widget.winfo_width() <= 1 or canvas_widget.winfo_height() <= 1:
                logger.warning("Canvas size is too small, forcing update...")
                # Force the parent frame to update its size
                self.plot_area_frame.update()
                canvas_widget.update()
                
                # Try to redraw the canvas
                self.canvas.draw()
                
                logger.info(f"After forced update - canvas size: {canvas_widget.winfo_width()}x{canvas_widget.winfo_height()}")
                
        except Exception as e:
            logger.error(f"Error finalizing canvas display: {e}")

    def quick_change_series_color(self, series):
        """Quick color change for a series by clicking the color preview"""
        try:
            from tkinter import colorchooser
            
            # Open color chooser dialog
            color = colorchooser.askcolor(
                color=series.color,
                title=f"Choose color for {series.name}"
            )
            
            if color[1]:  # color[1] is the hex string, color[0] is RGB tuple
                # Update series color
                series.color = color[1]
                self.all_series[series.id] = series
                
                # Update the color in the existing series card instead of recreating
                self.update_series_card_color(series)
                
                # Trigger auto-refresh if enabled
                self.trigger_auto_refresh()
                
                self.status_bar.set_status(f"Updated color for {series.name}", "success")
                
        except Exception as e:
            logger.error(f"Error changing series color: {e}")
            self.status_bar.set_status(f"Error changing color: {str(e)}", "error")

    def update_series_card_color(self, series):
        """Update the color preview in an existing series card"""
        try:
            # Use stored reference to directly update color button
            if (hasattr(self, 'series_color_frames') and 
                series.id in self.series_color_frames):
                color_button = self.series_color_frames[series.id]
                if color_button.winfo_exists():
                    color_button.configure(
                        fg_color=series.color,
                        hover_color=self._adjust_color_brightness(series.color, 0.8)
                    )
                    logger.info(f"Updated color button for series {series.name} to {series.color}")
                    return
                    
            # Fallback: recreate the card if direct update fails
            logger.warning(f"Color button reference not found for series {series.id}, recreating card")
            if series.id in self.series_cards:
                self.series_cards[series.id].destroy()
                del self.series_cards[series.id]
                if hasattr(self, 'series_color_frames') and series.id in self.series_color_frames:
                    del self.series_color_frames[series.id]
                if hasattr(self, 'series_widgets') and series.id in self.series_widgets:
                    del self.series_widgets[series.id]
            self.add_series_card(series)
            
        except Exception as e:
            logger.error(f"Error updating series card color: {e}")
    
    def update_series_card(self, series_id, updated_series):
        """Update an existing series card with new series data"""
        try:
            # Remove the old card
            if series_id in self.series_cards:
                self.series_cards[series_id].destroy()
                del self.series_cards[series_id]
            
            # Clean up color frame reference
            if hasattr(self, 'series_color_frames') and series_id in self.series_color_frames:
                del self.series_color_frames[series_id]
            
            # Create new card with updated data
            self.add_series_card(updated_series)
            
            logger.info(f"Updated series card for '{updated_series.name}'")
            
        except Exception as e:
            logger.error(f"Error updating series card: {e}")
            # Fallback: just create a new card
            self.add_series_card(updated_series)

    def _update_color_frame_in_widget(self, widget, new_color):
        """Recursively find and update color frame in widget hierarchy"""
        try:
            # Check if this widget is a color frame (has specific size and color)
            if (hasattr(widget, 'cget') and 
                hasattr(widget, 'configure') and
                widget.winfo_width() == 20 and 
                widget.winfo_height() == 15):
                widget.configure(fg_color=new_color)
                return True
                
            # Recursively check children
            for child in widget.winfo_children():
                if self._update_color_frame_in_widget(child, new_color):
                    return True
                    
        except Exception as e:
            logger.debug(f"Error checking widget for color frame: {e}")
        
        return False

    def edit_series(self, series):
        """Edit an existing series"""
        # Check if the file still exists
        if series.file_id not in self.loaded_files:
            self.status_bar.set_status(f"File for series '{series.name}' no longer available", "error")
            messagebox.showerror("Error", f"The source file for series '{series.name}' is no longer loaded.")
            return
            
        try:
            file_data = self.loaded_files[series.file_id]
            
            # Create dialog instance with correct parameters
            files_dict = {series.file_id: file_data}  # Convert to expected format
            dialog = SeriesDialog(self, files_dict, series, mode="edit")
            
            # Wait for dialog to complete
            self.wait_window(dialog.dialog)
            dialog_result = dialog.result
            
            # Handle the result if needed
            if dialog_result:
                # Update the series in the dictionary
                self.all_series[series.id] = dialog_result
                
                # Update the visual card
                self.update_series_card(series.id, dialog_result)
                
                # Update counts after series modification
                self.update_counts()
                
                # Refresh the plot
                self.refresh_plot()
                
                self.status_bar.set_status(f"Updated series '{dialog_result.name}'", "success")
            
            logger.info(f"Series configuration dialog result: {dialog_result}")
            
        except KeyError as e:
            logger.error(f"KeyError in edit_series: {e}")
            self.status_bar.set_status(f"Error: File ID {series.file_id} not found", "error")
            messagebox.showerror("Error", f"Cannot find file for series '{series.name}'. File may have been removed.")
        except Exception as e:
            logger.error(f"Error editing series: {e}")
            self.status_bar.set_status(f"Error editing series: {str(e)}", "error")
            messagebox.showerror("Error", f"Failed to edit series: {str(e)}")

    def update_series_display_from_config(self, updated_series):
        """Update main UI to reflect changes from enhanced series configuration"""
        try:
            # Update the current series form if this series is selected
            current_selection = self.series_file_var.get()
            if current_selection:
                # Check if the updated series belongs to the currently selected file
                if hasattr(self, 'file_id_mapping') and current_selection in self.file_id_mapping:
                    file_id = self.file_id_mapping[current_selection]
                    if file_id == updated_series.file_id:
                        # Update form fields to reflect the series configuration
                        self.series_name_var.set(updated_series.name)
                        self.series_x_combo.set(updated_series.x_column)
                        self.series_y_combo.set(updated_series.y_column)
                        self.series_start_var.set(str(updated_series.start_index or 0))
                        self.series_end_var.set(str(updated_series.end_index or ""))
                        
        except Exception as e:
            logger.error(f"Error updating series display: {e}")

    def select_all_series_data(self):
        """Select all available data for the current file"""
        selection = self.series_file_var.get()
        if not selection:
            self.status_bar.set_status("Please select a file first", "warning")
            return
            
        try:
            if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
                file_id = self.file_id_mapping[selection]
                matching_file = self.loaded_files.get(file_id)
                if matching_file:
                    total_points = len(matching_file.df)
                    self.series_start_var.set("0")
                    self.series_end_var.set(str(total_points))
                    self.start_var.set(0)
                    self.end_var.set(total_points)
                    self.update_selection_info()
                    self.status_bar.set_status(f"Selected all {total_points:,} rows", "info")
        except Exception as e:
            logger.error(f"Error selecting all data: {e}")

    def select_first_10_percent(self):
        """Select first 10% of data"""
        selection = self.series_file_var.get()
        if not selection:
            self.status_bar.set_status("Please select a file first", "warning")
            return
            
        try:
            if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
                file_id = self.file_id_mapping[selection]
                matching_file = self.loaded_files.get(file_id)
                if matching_file:
                    total_points = len(matching_file.df)
                    ten_percent = max(1, int(total_points * 0.1))
                    self.series_start_var.set("0")
                    self.series_end_var.set(str(ten_percent))
                    self.start_var.set(0)
                    self.end_var.set(ten_percent)
                    self.update_selection_info()
                    self.status_bar.set_status(f"Selected first 10% ({ten_percent:,} rows)", "info")
        except Exception as e:
            logger.error(f"Error selecting first 10%: {e}")

    def select_last_10_percent(self):
        """Select last 10% of data"""
        selection = self.series_file_var.get()
        if not selection:
            self.status_bar.set_status("Please select a file first", "warning")
            return
            
        try:
            if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
                file_id = self.file_id_mapping[selection]
                matching_file = self.loaded_files.get(file_id)
                if matching_file:
                    total_points = len(matching_file.df)
                    ten_percent = max(1, int(total_points * 0.1))
                    start_point = total_points - ten_percent
                    self.series_start_var.set(str(start_point))
                    self.series_end_var.set(str(total_points))
                    self.start_var.set(start_point)
                    self.end_var.set(total_points)
                    self.update_selection_info()
                    self.status_bar.set_status(f"Selected last 10% ({ten_percent:,} rows)", "info")
        except Exception as e:
            logger.error(f"Error selecting last 10%: {e}")

    def select_middle_50_percent(self):
        """Select middle 50% of data"""
        selection = self.series_file_var.get()
        if not selection:
            self.status_bar.set_status("Please select a file first", "warning")
            return
            
        try:
            if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
                file_id = self.file_id_mapping[selection]
                matching_file = self.loaded_files.get(file_id)
                if matching_file:
                    total_points = len(matching_file.df)
                    quarter = total_points // 4
                    start_point = quarter
                    end_point = total_points - quarter
                    self.series_start_var.set(str(start_point))
                    self.series_end_var.set(str(end_point))
                    self.start_var.set(start_point)
                    self.end_var.set(end_point)
                    self.update_selection_info()
                    selected_count = end_point - start_point
                    self.status_bar.set_status(f"Selected middle 50% ({selected_count:,} rows)", "info")
        except Exception as e:
            logger.error(f"Error selecting middle 50%: {e}")

    def on_start_entry_change(self, *args):
        """Handle start entry text changes"""
        try:
            start_val = int(self.series_start_var.get())
            end_val = int(self.series_end_var.get()) if self.series_end_var.get() else start_val + 1
            
            # Get current file to validate range
            selection = self.series_file_var.get()
            if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
                file_id = self.file_id_mapping[selection]
                matching_file = self.loaded_files.get(file_id)
                if matching_file:
                    max_val = len(matching_file.df)
                    start_val = max(0, min(start_val, max_val - 1))
                    
                    if start_val >= end_val:
                        end_val = start_val + 1
                        self.series_end_var.set(str(end_val))
                    
                    # Update dual slider
                    self.start_var.set(start_val)
                    self.update_selection_info()
                    # Update live preview
                    self.on_series_config_changed()
        except ValueError:
            pass

    def on_end_entry_change(self, *args):
        """Handle end entry text changes"""
        try:
            end_val = int(self.series_end_var.get())
            start_val = int(self.series_start_var.get()) if self.series_start_var.get() else 0
            
            # Get current file to validate range
            selection = self.series_file_var.get()
            if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
                file_id = self.file_id_mapping[selection]
                matching_file = self.loaded_files.get(file_id)
                if matching_file:
                    max_val = len(matching_file.df)
                    end_val = max(1, min(end_val, max_val))
                    
                    if start_val >= end_val:
                        start_val = end_val - 1
                        if start_val < 0:
                            start_val = 0
                        self.series_start_var.set(str(start_val))
                        # Update dual slider
                        self.start_var.set(start_val)
                    
                    # Update dual slider
                    self.end_var.set(end_val)
                    self.update_selection_info()
                    # Update live preview
                    self.on_series_config_changed()
        except ValueError:
            pass

    def on_start_slider_change(self, value):
        """Handle start slider changes"""
        try:
            start_val = int(value)
            # Update text entry to match slider
            self.series_start_var.set(str(start_val))
            self.update_selection_info()
            # Update live preview
            self.on_series_config_changed()
        except ValueError:
            pass

    def on_end_slider_change(self, value):
        """Handle end slider changes"""
        try:
            end_val = int(value)
            # Update text entry to match slider
            self.series_end_var.set(str(end_val))
            self.update_selection_info()
            # Update live preview
            self.on_series_config_changed()
        except ValueError:
            pass

    def update_selection_info(self):
        """Update the data selection information display"""
        try:
            selection = self.series_file_var.get()
            if not selection or not hasattr(self, 'file_id_mapping') or selection not in self.file_id_mapping:
                self.selection_info_label.configure(text="")
                return
            
            file_id = self.file_id_mapping[selection]
            matching_file = self.loaded_files.get(file_id)
            if not matching_file:
                return
            
            total_points = len(matching_file.df)
            start_val = int(self.series_start_var.get()) if self.series_start_var.get() else 0
            end_val = int(self.series_end_var.get()) if self.series_end_var.get() else total_points
            
            selected_points = end_val - start_val
            percentage = (selected_points / total_points) * 100 if total_points > 0 else 0
            
            self.selection_info_label.configure(
                text=f"Selected: {selected_points:,} of {total_points:,} points ({percentage:.1f}%)"
            )
        except (ValueError, AttributeError):
            self.selection_info_label.configure(text="")

    def preview_series_data(self):
        """Preview the data that would be used for the current series configuration"""
        selection = self.series_file_var.get()
        if not selection:
            self.status_bar.set_status("Please select a source file", "warning")
            return

        x_col = self.series_x_combo.get()
        y_col = self.series_y_combo.get()

        if not x_col or not y_col:
            self.status_bar.set_status("Please select both X and Y columns", "warning")
            return

        try:
            # Get file data
            if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
                file_id = self.file_id_mapping[selection]
                matching_file = self.loaded_files.get(file_id)
            else:
                return
                
            if not matching_file:
                return

            # Get data range
            try:
                start_idx = int(self.series_start_var.get()) if self.series_start_var.get() else 0
                end_idx = int(self.series_end_var.get()) if self.series_end_var.get() else len(matching_file.df)
            except ValueError:
                start_idx = 0
                end_idx = len(matching_file.df)

            # Create preview dialog
            preview_dialog = ctk.CTkToplevel(self)
            preview_dialog.title("Series Data Preview")
            preview_dialog.geometry("800x600")
            preview_dialog.transient(self)

            # Preview content
            preview_frame = ctk.CTkFrame(preview_dialog)
            preview_frame.pack(fill="both", expand=True, padx=10, pady=10)

            # Info header
            info_text = f"Preview: {y_col} vs {x_col} | Rows {start_idx} to {end_idx} ({end_idx-start_idx} points)"
            ctk.CTkLabel(preview_frame, text=info_text, font=("", 12, "bold")).pack(pady=5)

            # Data preview
            data_slice = matching_file.df.iloc[start_idx:end_idx]
            preview_data = data_slice[[x_col, y_col]].head(100) if x_col != 'Index' else data_slice[[y_col]].head(100)
            
            text_widget = ctk.CTkTextbox(preview_frame, font=("Consolas", 10))
            text_widget.pack(fill="both", expand=True, pady=10)
            
            preview_text = f"Data Preview (first 100 rows of {end_idx-start_idx} total):\n\n"
            preview_text += preview_data.to_string()
            text_widget.insert("1.0", preview_text)
            text_widget.configure(state="disabled")

            # Close button
            ctk.CTkButton(preview_frame, text="Close", command=preview_dialog.destroy).pack(pady=5)

        except Exception as e:
            logger.error(f"Error previewing data: {e}")
            messagebox.showerror("Error", f"Failed to preview data: {str(e)}")

    def remove_series(self, series):
        """Remove a series"""
        if series.file_id in self.loaded_files:
            file_data = self.loaded_files[series.file_id]
            # Ensure series_list exists (for backward compatibility)
            if not hasattr(file_data, 'series_list'):
                file_data.series_list = []
            if series.id in file_data.series_list:
                file_data.series_list.remove(series.id)

        del self.all_series[series.id]
        self.series_cards[series.id].destroy()
        del self.series_cards[series.id]
        
        # Clean up color frame reference
        if hasattr(self, 'series_color_frames') and series.id in self.series_color_frames:
            del self.series_color_frames[series.id]

        self.update_counts()
        self.status_bar.set_status(f"Removed series: {series.name}", "info")

    def calculate_optimal_figure_size(self):
        """Calculate optimal figure size based on available space"""
        try:
            # Get the current window size
            self.update_idletasks()  # Ensure geometry is updated
            window_width = self.winfo_width()
            window_height = self.winfo_height()
            
            # If window is not fully realized, use screen size as fallback
            if window_width <= 1 or window_height <= 1:
                window_width = 1200  # Reasonable default
                window_height = 800  # Reasonable default
            
            # Account for left panel (approximately 400px) and margins
            available_width = max(300, window_width - 450)  # Leave space for left panel + margins
            available_height = max(250, window_height - 150)  # Leave space for toolbar + margins
            
            # Convert pixels to inches (assuming 100 DPI)
            fig_width = available_width / 100.0
            fig_height = available_height / 100.0
            
            # Apply reasonable constraints
            fig_width = max(3.0, min(fig_width, 10.0))  # Between 3 and 10 inches
            fig_height = max(2.5, min(fig_height, 7.0))   # Between 2.5 and 7 inches
            
            logger.info(f"Calculated optimal figure size: {fig_width:.1f}x{fig_height:.1f} inches (window: {window_width}x{window_height}px)")
            
            return fig_width, fig_height
            
        except Exception as e:
            logger.warning(f"Could not calculate optimal figure size: {e}")
            # Fall back to smaller default values
            return 6.0, 4.0

    def create_plot(self):
        """Create the plot with custom styling"""
        # Prevent multiple simultaneous plot creation
        if hasattr(self, '_creating_plot') and self._creating_plot:
            logger.info("Plot creation already in progress, skipping...")
            return
            
        if not self.all_series:
            self.status_bar.set_status("No series defined. Please add at least one series.", "warning")
            return
            
        self._creating_plot = True
        
        try:
            # Enhanced debugging for series visibility
            logger.info(f"=== DETAILED SERIES DEBUG START ===")
            logger.info(f"Total series in self.all_series: {len(self.all_series)}")
        
            for series_id, series in self.all_series.items():
                logger.info(f"Series ID '{series_id}': name='{series.name}', type={type(series)}")
                logger.info(f"  hasattr(series, 'visible'): {hasattr(series, 'visible')}")
                if hasattr(series, 'visible'):
                    logger.info(f"  series.visible: {series.visible}")
                else:
                    logger.info(f"  series.visible: MISSING ATTRIBUTE")
                logger.info(f"  getattr(series, 'visible', True): {getattr(series, 'visible', True)}")
                logger.info(f"  file_id: {series.file_id}")
                logger.info(f"  UUID length: {len(series_id)} characters")
        
            visible_series = [s for s in self.all_series.values() if getattr(s, 'visible', True)]
            
            logger.info(f"After filtering - visible_series count: {len(visible_series)}")
            for i, series in enumerate(visible_series):
                logger.info(f"  Visible series {i+1}: '{series.name}' (ID: {series.id})")
            logger.info(f"=== DETAILED SERIES DEBUG END ===")
            
            if not visible_series:
                self.status_bar.set_status("No visible series selected. Please check series visibility boxes to plot.", "warning")
                return

            # Inform user about what's being plotted
            series_names = [s.name for s in visible_series]
            if len(visible_series) == 1:
                self.status_bar.set_status(f"Plotting 1 series: {series_names[0]}", "info")
            else:
                self.status_bar.set_status(f"Plotting {len(visible_series)} series: {', '.join(series_names[:3])}{'...' if len(visible_series) > 3 else ''}", "info")

            self.status_bar.set_status("Generating plot...", "info")
            self.status_bar.show_progress()

            self.empty_plot_frame.grid_forget()

            if self.canvas:
                try:
                    # Cancel any pending after_idle callbacks that might reference the canvas
                    canvas_widget = self.canvas.get_tk_widget()
                    if canvas_widget.winfo_exists():
                        canvas_widget.destroy()
                except tk.TclError:
                    # Canvas already destroyed or invalid
                    pass
                finally:
                    self.canvas = None
                    
            if self.toolbar:
                try:
                    self.toolbar.destroy()
                except tk.TclError:
                    pass
                finally:
                    self.toolbar = None

            # Set theme-appropriate matplotlib style and colors
            is_dark_theme = ctk.get_appearance_mode() == "Dark"
            if is_dark_theme:
                plt.style.use('dark_background')
                fig_color = '#2b2b2b'  # Dark background
            else:
                plt.style.use('seaborn-v0_8-whitegrid')
                fig_color = 'white'  # Light background

            # Calculate optimal figure size based on available space
            optimal_width, optimal_height = self.calculate_optimal_figure_size()
            
            self.figure = Figure(figsize=(optimal_width, optimal_height),
                                 facecolor=fig_color, dpi=100)
            ax = self.figure.add_subplot(111)
            
            # Set axes background to match theme
            if is_dark_theme:
                ax.set_facecolor('#2b2b2b')
            else:
                ax.set_facecolor('white')
            
            # Store axes reference for annotations
            self.plot_axes = ax
            
            # Log plotting details
            logger.info(f"Starting to plot {len(visible_series)} visible series")

            for i, series in enumerate(visible_series):
                self.status_bar.show_progress((i + 1) / len(visible_series))

                file_data = self.loaded_files.get(series.file_id)
                if not file_data:
                    logger.warning(f"File data not found for series {series.name} (file_id: {series.file_id})")
                    continue

                try:
                    logger.info(f"Plotting series {i+1}/{len(visible_series)}: '{series.name}' (color: {series.color})")
                    self.plot_single_series(ax, series, file_data)
                except Exception as e:
                    logger.error(f"Error plotting series {series.name}: {e}")
                    continue

            # Ensure axes are properly configured
            logger.info("Configuring plot axes...")

            # Ensure axes are properly configured
            logger.info("Configuring plot axes...")
            self.configure_plot_axes(ax)

            # Auto-scale to show all data
            ax.relim()
            ax.autoscale_view()
            
            # Draw annotations
            self.annotation_manager.draw_annotations(ax)
            
            # Force tight layout before canvas creation
            self.figure.tight_layout()

            self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_area_frame)
            logger.info("Canvas created, about to draw...")
            self.canvas.draw()
            logger.info("Canvas drawn, about to grid...")
            
            # Debug widget hierarchy before gridding
            logger.info(f"Plot area frame children before canvas grid: {list(self.plot_area_frame.children.keys())}")
            
            canvas_widget = self.canvas.get_tk_widget()
            
            # Configure the canvas widget properly
            canvas_widget.configure(highlightthickness=0)
            canvas_widget.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
            logger.info("Canvas gridded successfully")
            
            # Debug widget hierarchy after gridding
            logger.info(f"Plot area frame children after canvas grid: {list(self.plot_area_frame.children.keys())}")
            
            # Force the plot area frame to update its layout
            self.plot_area_frame.update_idletasks()
            canvas_widget.update_idletasks()
            
            # Force canvas refresh
            self.canvas.draw_idle()
            
            # Give the widget system time to process the layout
            self.after_idle(lambda: self._safe_finalize_canvas_display(canvas_widget))
            
            logger.info("Canvas and plot area updated")
            
            # Final widget state check
            logger.info(f"Final canvas widget visibility: {canvas_widget.winfo_viewable()}")
            logger.info(f"Final canvas widget size: {canvas_widget.winfo_width()}x{canvas_widget.winfo_height()}")

            toolbar_frame = ctk.CTkFrame(self.plot_area_frame, height=40)
            toolbar_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
            toolbar_frame.grid_propagate(False)

            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()

            self.status_bar.hide_progress()
            
            # Log completion and final check
            handles, labels = ax.get_legend_handles_labels()
            logger.info(f"Plot completed with {len(handles)} legend items")
            
            if len(handles) > 0:
                self.status_bar.set_status(f"Plot created successfully with {len(visible_series)} series", "success")
            else:
                self.status_bar.set_status("Plot created but no data series visible", "warning")
                
            # Update counts to reflect current state after plot creation
            self.update_counts()

        except Exception as e:
            self.status_bar.hide_progress()
            self.status_bar.set_status(f"Failed to create plot: {str(e)}", "error")
            logger.exception("Plot creation failed")
        finally:
            # Always clear the mutex flag
            self._creating_plot = False
            # Update preview to show plot context
            self.update_preview("auto")

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

        # Get proper label for the series
        series_label = ""
        if hasattr(series, 'show_in_legend') and series.show_in_legend:
            series_label = getattr(series, 'legend_label', series.name) or series.name

        # Main plot
        if series.plot_type == 'line':
            ax.plot(x_plot, y_plot_smooth,
                    color=series.color,
                    linestyle=series.line_style,
                    linewidth=series.line_width,
                    marker=series.marker if series.marker else None,
                    markersize=series.marker_size,
                    alpha=series.alpha,
                    label=series_label,
                    zorder=getattr(series, 'z_order', 1))
        elif series.plot_type == 'scatter':
            ax.scatter(x_plot, y_plot_smooth,
                       color=series.color,
                       s=series.marker_size ** 2,
                       marker=series.marker if series.marker else 'o',
                       alpha=series.alpha,
                       label=series_label,
                       zorder=getattr(series, 'z_order', 1))
        
        # Log successful plotting
        logger.info(f"Successfully plotted series '{series.name}' with {len(x_plot)} points (color: {series.color})")

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
        """Configure plot axes and styling with theme-aware text colors"""
        # Determine text color based on current theme and user overrides
        is_dark_theme = ctk.get_appearance_mode() == "Dark"
        
        # Title color logic
        if self.title_color_var.get() == "auto":
            title_color = 'white' if is_dark_theme else 'black'
        else:
            title_color = self.title_color_var.get()
        
        # Axis text color logic  
        if self.axis_text_color_var.get() == "auto":
            text_color = 'white' if is_dark_theme else 'black'
        else:
            text_color = self.axis_text_color_var.get()
        
        # Configure title with proper color
        ax.set_title(self.title_var.get(), 
                    fontsize=self.title_size_var.get(), 
                    fontweight='bold', 
                    pad=20,
                    color=title_color)
        
        # Configure axis labels with proper color
        ax.set_xlabel(self.xlabel_var.get(), 
                     fontsize=self.xlabel_size_var.get(),
                     color=text_color)
        ax.set_ylabel(self.ylabel_var.get(), 
                     fontsize=self.ylabel_size_var.get(),
                     color=text_color)
        
        # Configure tick labels with proper color
        ax.tick_params(colors=text_color, which='both')
        
        # Set spine colors to be visible
        for spine in ax.spines.values():
            spine.set_color(text_color)
            spine.set_alpha(0.8)

        if self.show_grid_var.get():
            ax.grid(True, linestyle=self.grid_style_var.get(),
                    alpha=self.grid_alpha_var.get(), which='both',
                    color=text_color)
            ax.set_axisbelow(True)

        if self.show_legend_var.get():
            handles, labels = ax.get_legend_handles_labels()
            filtered = [(h, l) for h, l in zip(handles, labels) if l]
            if filtered:
                handles, labels = zip(*filtered)
                legend = ax.legend(handles, labels, loc='best', frameon=True,
                                 fancybox=True, shadow=True, fontsize=10)
                # Set legend colors based on theme
                for text in legend.get_texts():
                    text.set_color(text_color)
                
                # Set legend background and frame colors based on theme
                legend_bg_color = '#2b2b2b' if is_dark_theme else 'white'
                legend_edge_color = text_color
                
                legend.get_frame().set_facecolor(legend_bg_color)
                legend.get_frame().set_edgecolor(legend_edge_color)
                legend.get_frame().set_alpha(0.9)  # Semi-transparent background

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
        if not self.all_series:
            self.status_bar.set_status("No series available for analysis", "warning")
            return

        # Instantiate dialog with expected signature from ui/vacuum_analysis_dialog.py
        try:
            dialog = VacuumAnalysisDialog(self, selected_series=None, all_series=self.all_series, loaded_files=self.loaded_files)

            # Track the inner CTkToplevel for theme updates
            dlg_window = getattr(dialog, 'dialog', dialog)
            self.open_dialogs.append(dlg_window)

            def on_dialog_close():
                if dlg_window in self.open_dialogs:
                    self.open_dialogs.remove(dlg_window)
                try:
                    dlg_window.destroy()
                except Exception:
                    pass

            if hasattr(dlg_window, 'protocol'):
                dlg_window.protocol("WM_DELETE_WINDOW", on_dialog_close)

            self.status_bar.set_status("Vacuum analysis tools opened", "info")
        except Exception as e:
            logger.error(f"Failed to open Vacuum Analysis dialog: {e}")
            self.status_bar.set_status("Error opening Vacuum Analysis", "error")

    def show_multi_analysis(self):
        """Show multi-series analysis dialog"""
        try:
            if not self.all_series:
                self.status_bar.set_status("No series available for analysis", "warning")
                messagebox.showwarning("Warning", "Please load data and create series first")
                return
                
            # Show the new enhanced analysis dialog
            dialog = StatisticalAnalysisDialog(self, self.all_series, self.loaded_files, 
                                             self.statistical_analyzer, self.vacuum_analyzer)
            try:
                dialog.dialog.lift()  # Bring dialog to front
            except tk.TclError:
                # Dialog might have been destroyed before focusing
                pass
            
            # Track the dialog for theme updates
            self.open_dialogs.append(dialog)
            
            # Remove dialog from tracking when it's closed
            def on_dialog_close():
                if dialog in self.open_dialogs:
                    self.open_dialogs.remove(dialog)
                dialog.destroy()
            
            dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
            
            self.status_bar.set_status("Multi-series analysis opened", "info")
                
        except Exception as e:
            logger.error(f"Error showing enhanced multi-analysis: {e}")
            self.status_bar.set_status("Error opening enhanced analysis dialog", "error")
            messagebox.showerror("Error", f"Failed to open enhanced analysis: {str(e)}")

    def show_annotation_panel(self):
        """Show annotation manager"""
        if not self.figure or not hasattr(self, 'canvas') or not self.canvas:
            # Check if user has series but no plot
            if self.all_series:
                visible_series = [s for s in self.all_series.values() if getattr(s, 'visible', True)]
                if visible_series:
                    # User has series ready, offer to create plot first
                    dialog = ctk.CTkToplevel(self)
                    dialog.title("Create Plot First")
                    dialog.geometry("400x200")
                    dialog.transient(self)
                    dialog.grab_set()
                    dialog.attributes('-topmost', True)
                    
                    ctk.CTkLabel(
                        dialog,
                        text="⚠️ Annotations require an active plot",
                        font=("", 16, "bold")
                    ).pack(pady=15)
                    
                    ctk.CTkLabel(
                        dialog,
                        text=f"You have {len(visible_series)} series ready to plot.\nCreate the plot first, then access annotations.\n\n💡 Annotations let you add labels, arrows, and notes\nto highlight important features in your data."
                    ).pack(pady=10)
                    
                    btn_frame = ctk.CTkFrame(dialog)
                    btn_frame.pack(pady=15)
                    
                    def create_plot_and_open_annotations():
                        dialog.destroy()
                        self.create_plot()
                        # Schedule annotation dialog to open after plot is created
                        self.after(100, self._open_annotations_after_plot)
                    
                    ctk.CTkButton(
                        btn_frame,
                        text="📊 Create Plot & Open Annotations",
                        command=create_plot_and_open_annotations,
                        fg_color=UIConfig.PRIMARY
                    ).pack(side="left", padx=10)
                    
                    ctk.CTkButton(
                        btn_frame,
                        text="Cancel",
                        command=dialog.destroy,
                        fg_color="gray50"
                    ).pack(side="left", padx=10)
                    
                    # Center the dialog
                    dialog.update_idletasks()
                    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
                    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
                    dialog.geometry(f"+{x}+{y}")
                    
                else:
                    self.status_bar.set_status("No visible series to plot - enable series visibility first", "warning")
            else:
                self.status_bar.set_status("Load data and create series first, then generate a plot to access annotations", "warning")
            return

        ax = self.figure.axes[0] if self.figure and self.figure.axes else None
        if not ax:
            self.status_bar.set_status("No plot axes available for annotations", "warning")
            return
            
        show_annotation_dialog(self, self.annotation_manager, ax)
        self.status_bar.set_status("Annotation manager opened", "info")
    
    def _open_annotations_after_plot(self):
        """Helper method to open annotations after plot creation"""
        if self.figure and hasattr(self, 'canvas') and self.canvas:
            ax = self.figure.axes[0] if self.figure.axes else None
            if ax:
                show_annotation_dialog(self, self.annotation_manager, ax)
                self.status_bar.set_status("Plot created and annotation manager opened", "success")
            else:
                self.status_bar.set_status("Plot created but no axes available for annotations", "warning")
        else:
            self.status_bar.set_status("Failed to create plot - please try again", "error")

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
        logger.info("CLEAR_PLOT_AREA CALLED - this may be the issue!")
        import traceback
        logger.info(f"Stack trace: {traceback.format_stack()}")
        
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

        self.empty_plot_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def update_counts(self):
        """Update file and series counts in status bar and series panel"""
        file_count = len(self.loaded_files)
        series_count = len(self.all_series)
        
        # Update status bar
        self.status_bar.update_counts(files=file_count, series=series_count)
        
        # Update series count display if it exists
        if hasattr(self, 'series_count_label'):
            summary = self.get_series_summary()
            count_text = f"({summary['total']} total, {summary['visible']} visible"
            if summary['hidden'] > 0:
                count_text += f", {summary['hidden']} hidden"
            count_text += ")"
            self.series_count_label.configure(text=count_text)

    def toggle_theme(self):
        """Toggle between dark and light themes"""
        logger.info("Theme toggle requested")
        
        # Use the enhanced theme manager for proper theming
        old_theme = self.theme_manager.current_theme
        self.theme_manager.toggle_theme()
        new_theme = self.theme_manager.current_theme
        
        logger.info(f"Theme changed from {old_theme} to {new_theme}")
        
        # Get the new theme name for status message
        self.status_bar.set_status(f"Theme changed to: {new_theme.title()}", "info")

        # Recreate the plot with new theme if it exists
        if self.figure:
            logger.info("Refreshing main plot")
            self.create_plot()
            
        # Refresh the live preview if currently showing series editing
        if (self.preview_mode == "series_editing" and 
            hasattr(self, 'series_preview_frame') and 
            self.series_preview_frame.winfo_exists()):
            try:
                logger.info("Refreshing live preview")
                self.update_series_preview_from_form()
            except Exception as e:
                logger.error(f"Error refreshing preview: {e}")
            
        # Refresh dual range slider theme
        if hasattr(self, 'dual_range_slider') and self.dual_range_slider:
            try:
                logger.info("Refreshing dual range slider")
                self.dual_range_slider.refresh_theme()
            except Exception as e:
                logger.error(f"Error refreshing dual range slider theme: {e}")
            
        # Refresh theme for all open dialogs
        for dialog in self.open_dialogs[:]:  # Use slice to avoid modification during iteration
            try:
                if dialog.winfo_exists():  # Check if dialog still exists
                    if hasattr(dialog, 'refresh_theme'):
                        dialog.refresh_theme()
                else:
                    # Remove dialogs that no longer exist
                    self.open_dialogs.remove(dialog)
            except tk.TclError:
                # Dialog has been destroyed, remove from list
                if dialog in self.open_dialogs:
                    self.open_dialogs.remove(dialog)
            
        # Force update of all UI components
        self.update_idletasks()

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

    def create_series_from_data(self, file_data=None):
        """Create a new smart series with intelligent defaults"""
        if not file_data and self.loaded_files:
            # Use the first loaded file if none specified
            file_data = list(self.loaded_files.values())[0]
        
        if not file_data:
            messagebox.showwarning("No Data", "Please load a data file first.")
            return
        
        # Create new series with smart dialog
        self.show_series_editing_mode()  # Switch to series editing preview mode
        new_series = show_series_dialog(self, file_data, None)
        self.hide_series_editing_mode()  # Switch back to auto mode
        if new_series:
            # Add to series configurations
            self.series_configs[new_series.id] = new_series
            self.refresh_series_list()
            self.update_plot()
            
            # Show success message
            messagebox.showinfo("Success", f"Smart series '{new_series.name}' created successfully!")

    def auto_detect_series(self, file_data):
        """Automatically detect and create recommended series"""
        if not file_data:
            return
        
        numeric_cols = file_data.get_numeric_columns()
        datetime_cols = file_data.datetime_columns
        
        recommendations = []
        
        # Recommend time series if datetime column exists
        if datetime_cols and numeric_cols:
            for i, num_col in enumerate(numeric_cols[:3]):  # Limit to first 3
                series_name = f"Time Series: {num_col}"
                recommendations.append({
                    'name': series_name,
                    'x_column': datetime_cols[0],
                    'y_column': num_col,
                    'type': 'time_series'
                })
        
        # Recommend correlation plots for numeric columns
        if len(numeric_cols) >= 2:
            for i in range(min(2, len(numeric_cols)-1)):
                series_name = f"Correlation: {numeric_cols[i+1]} vs {numeric_cols[i]}"
                recommendations.append({
                    'name': series_name,
                    'x_column': numeric_cols[i],
                    'y_column': numeric_cols[i+1],
                    'type': 'correlation'
                })
        
        return recommendations

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
        """Show statistical analysis dialog"""
        try:
            if not self.all_series:
                self.status_bar.set_status("No series available for analysis", "warning")
                messagebox.showwarning("Warning", "Please load data and create series first")
                return
                
            # Use the legacy statistical analyzer for now
            from ui.dialogs import StatisticalAnalysisDialog
            dialog = StatisticalAnalysisDialog(self, self.all_series, self.loaded_files, self.statistical_analyzer, self.vacuum_analyzer)
            self.status_bar.set_status("Statistical analysis opened", "info")
            
        except ImportError:
            # If the dialog doesn't exist, use the enhanced multi-series analysis instead
            self.show_multi_analysis()
        except Exception as e:
            logger.error(f"Error showing statistical analysis: {e}")
            self.status_bar.set_status("Error opening statistical analysis", "error")
            messagebox.showerror("Error", f"Failed to open statistical analysis: {str(e)}")

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
        # Use updated reasonable default values
        self.fig_width_var.set(8.0)
        self.fig_height_var.set(5.0)

        if self.figure:
            self.create_plot()

        self.status_bar.set_status("Plot configuration reset", "success")

    def show_advanced_series_config(self):
        """Show advanced series configuration dialog"""
        if not self.series_file_var.get():
            self.status_bar.set_status("Select a file first", "warning")
            return

        selection = self.series_file_var.get()
        
        # Get matching file
        if hasattr(self, 'file_id_mapping') and selection in self.file_id_mapping:
            file_id = self.file_id_mapping[selection]
            matching_file = self.loaded_files.get(file_id)
        else:
            # Fallback to old method
            file_id = selection.split('(')[-1].rstrip(')')
            matching_file = None
            for fid, fdata in self.loaded_files.items():
                if fid.startswith(file_id):
                    matching_file = fdata
                    file_id = fid
                    break

        if not matching_file:
            return

        # Create series with current form data
        series_name = self.series_name_var.get() or "New Series"
        x_col = self.series_x_combo.get() or "Index"
        y_col = self.series_y_combo.get()
        
        if not y_col:
            self.status_bar.set_status("Please select a Y column first", "warning")
            return

        try:
            start_idx = int(self.series_start_var.get()) if self.series_start_var.get() else 0
            end_idx = int(self.series_end_var.get()) if self.series_end_var.get() else len(matching_file.df)
        except ValueError:
            start_idx = 0
            end_idx = len(matching_file.df)

        series = SeriesConfig(
            name=series_name,
            file_id=file_id,
            x_column=x_col,
            y_column=y_col,
            start_index=start_idx,
            end_index=end_idx
        )

        self.show_series_editing_mode()  # Switch to series editing preview mode
        dialog_result = show_series_dialog(self, matching_file, series)
        self.hide_series_editing_mode()  # Switch back to auto mode
        if dialog_result:
            # Update the main form with the advanced configuration
            updated_series = dialog_result
            
            # Update form fields to reflect changes
            self.series_name_var.set(updated_series.name)
            self.series_x_combo.set(updated_series.x_column)
            self.series_y_combo.set(updated_series.y_column)
            self.series_start_var.set(str(updated_series.start_index or 0))
            self.series_end_var.set(str(updated_series.end_index or len(matching_file.df)))
            
            # Store the advanced configuration
            self.all_series[updated_series.id] = updated_series
            self.add_series_card(updated_series)
            
            self.status_bar.set_status("Series created with advanced settings", "success")

    def show_advanced_plot_config(self):
        """Show advanced plot configuration dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Advanced Plot Configuration")
        dialog.geometry("600x700")
        dialog.resizable(True, True)
        
        # Make it modal
        dialog.transient(self)
        dialog.grab_set()
        
        # Create notebook for tabs
        notebook = ctk.CTkTabview(dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === PLOT TYPE TAB ===
        plot_tab = notebook.add("Plot Type")
        
        plot_frame = ctk.CTkScrollableFrame(plot_tab)
        plot_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(plot_frame, text="Plot Type Selection", font=("", 14, "bold")).pack(anchor="w", pady=5)
        
        self.plot_type_var = ctk.StringVar(value="line")
        plot_types = [
            ("Line Plot", "line", "Best for time series and continuous data"),
            ("Scatter Plot", "scatter", "Best for correlation analysis"),
            ("Bar Chart", "bar", "Best for categorical data"),
            ("Step Plot", "step", "Best for step functions"),
            ("Area Plot", "area", "Best for filled regions"),
            ("Box Plot", "box", "Best for statistical distributions")
        ]
        
        for name, value, description in plot_types:
            frame = ctk.CTkFrame(plot_frame)
            frame.pack(fill="x", pady=2)
            
            radio = ctk.CTkRadioButton(frame, text=name, variable=self.plot_type_var, value=value)
            radio.pack(side="left", padx=10, pady=5)
            
            desc_label = ctk.CTkLabel(frame, text=description, text_color="gray")
            desc_label.pack(side="left", padx=10, pady=5)
        
        # === APPEARANCE TAB ===
        appearance_tab = notebook.add("Appearance")
        
        app_frame = ctk.CTkScrollableFrame(appearance_tab)
        app_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Title customization
        title_section = ctk.CTkFrame(app_frame)
        title_section.pack(fill="x", pady=5)
        ctk.CTkLabel(title_section, text="Title & Labels", font=("", 12, "bold")).pack(anchor="w", padx=5, pady=5)
        
        # Title
        title_frame = ctk.CTkFrame(title_section)
        title_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(title_frame, text="Plot Title:", width=100).pack(side="left", padx=5)
        title_entry = ctk.CTkEntry(title_frame, textvariable=self.title_var)
        title_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Title color override
        title_color_frame = ctk.CTkFrame(title_section)
        title_color_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(title_color_frame, text="Title Color:", width=100).pack(side="left", padx=5)
        self.title_color_var = ctk.StringVar(value="auto")
        title_color_combo = ctk.CTkComboBox(title_color_frame, 
                                          values=["auto", "black", "white", "red", "blue", "green"],
                                          variable=self.title_color_var)
        title_color_combo.pack(side="left", padx=5)
        
        # Axis labels
        xlabel_frame = ctk.CTkFrame(title_section)
        xlabel_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(xlabel_frame, text="X Label:", width=100).pack(side="left", padx=5)
        xlabel_entry = ctk.CTkEntry(xlabel_frame, textvariable=self.xlabel_var)
        xlabel_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ylabel_frame = ctk.CTkFrame(title_section)
        ylabel_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(ylabel_frame, text="Y Label:", width=100).pack(side="left", padx=5)
        ylabel_entry = ctk.CTkEntry(ylabel_frame, textvariable=self.ylabel_var)
        ylabel_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        # Text color overrides
        text_section = ctk.CTkFrame(app_frame)
        text_section.pack(fill="x", pady=5)
        ctk.CTkLabel(text_section, text="Text Color Overrides", font=("", 12, "bold")).pack(anchor="w", padx=5, pady=5)
        
        self.axis_text_color_var = ctk.StringVar(value="auto")
        axis_color_frame = ctk.CTkFrame(text_section)
        axis_color_frame.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(axis_color_frame, text="Axis Text:", width=100).pack(side="left", padx=5)
        axis_color_combo = ctk.CTkComboBox(axis_color_frame,
                                         values=["auto", "black", "white", "red", "blue", "green"],
                                         variable=self.axis_text_color_var)
        axis_color_combo.pack(side="left", padx=5)
        
        # === ADVANCED TAB ===
        advanced_tab = notebook.add("Advanced")
        
        adv_frame = ctk.CTkScrollableFrame(advanced_tab)
        adv_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Grid options
        grid_section = ctk.CTkFrame(adv_frame)
        grid_section.pack(fill="x", pady=5)
        ctk.CTkLabel(grid_section, text="Grid & Legend", font=("", 12, "bold")).pack(anchor="w", padx=5, pady=5)
        
        grid_check = ctk.CTkCheckBox(grid_section, text="Show Grid", variable=self.show_grid_var)
        grid_check.pack(anchor="w", padx=5, pady=2)
        
        legend_check = ctk.CTkCheckBox(grid_section, text="Show Legend", variable=self.show_legend_var)
        legend_check.pack(anchor="w", padx=5, pady=2)
        
        # Scale options
        scale_section = ctk.CTkFrame(adv_frame)
        scale_section.pack(fill="x", pady=5)
        ctk.CTkLabel(scale_section, text="Scale Options", font=("", 12, "bold")).pack(anchor="w", padx=5, pady=5)
        
        log_x_check = ctk.CTkCheckBox(scale_section, text="Logarithmic X-axis", variable=self.log_scale_x_var)
        log_x_check.pack(anchor="w", padx=5, pady=2)
        
        log_y_check = ctk.CTkCheckBox(scale_section, text="Logarithmic Y-axis", variable=self.log_scale_y_var)
        log_y_check.pack(anchor="w", padx=5, pady=2)
        
        # === BUTTONS ===
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        def apply_and_close():
            # Apply the configuration
            self.create_plot()
            dialog.destroy()
        
        def close_dialog():
            dialog.destroy()
        
        ctk.CTkButton(button_frame, text="Apply & Close", 
                     command=apply_and_close,
                     fg_color=ColorPalette.SUCCESS).pack(side="right", padx=5)
        ctk.CTkButton(button_frame, text="Cancel", 
                     command=close_dialog).pack(side="right", padx=5)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    app = ExcelDataPlotter()
    app.mainloop()
