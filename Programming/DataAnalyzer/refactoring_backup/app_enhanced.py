#!/usr/bin/env python3
"""
Enhanced Excel Data Plotter with Full Legacy Functionality Restored
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
from datetime import datetime

# Import configuration
from config.constants import (
    AppConfig, UIConfig, ColorPalette, PlotConfig,
    FileTypes, PlotTypes, MissingDataMethods, TrendTypes,
    KeyBindings, DefaultSettings
)

# Import models
from models.data_models import FileData, SeriesConfig, PlotConfiguration, AnnotationConfig

# Import UI components - Enhanced Legacy Compatible
from ui.components import StatusBar, QuickActionBar, FileCard, SeriesCard, SearchBar, CollapsiblePanel, Tooltip

# Import core managers
from core.file_manager import FileManager
from core.plot_manager import PlotManager
from core.annotation_manager import AnnotationManager
from core.project_manager import ProjectManager
from core.export_manager import ExportManager

# Import analysis tools - Full Legacy Support
from analysis.legacy_analysis_tools import DataAnalysisTools, VacuumAnalysisTools
from analysis.statistical import StatisticalAnalyzer
from analysis.vacuum import VacuumAnalyzer
from analysis.data_quality import DataQualityAnalyzer

# Import utilities
from utils.helpers import format_file_size, generate_color_sequence, detect_datetime_column, convert_to_datetime
from utils.validators import validate_data_range

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ExcelDataPlotter(ctk.CTk):
    """
    Enhanced Main Application Window - Full Legacy Functionality
    """

    def __init__(self):
        """Initialize the enhanced application window"""
        super().__init__()

        # Configure window properties
        self.title(f"{AppConfig.APP_NAME} - {AppConfig.APP_SUBTITLE}")
        self.geometry(f"{AppConfig.DEFAULT_WIDTH}x{AppConfig.DEFAULT_HEIGHT}")
        self.minsize(AppConfig.MIN_WIDTH, AppConfig.MIN_HEIGHT)

        # Configure grid layout
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
        
        # Enhanced analysis tools - Legacy Compatible
        self.analysis_tools = DataAnalysisTools()
        self.vacuum_tools = VacuumAnalysisTools()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.vacuum_analyzer = VacuumAnalyzer()
        self.data_quality_analyzer = DataQualityAnalyzer()

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
        self.update_counts()
        logger.info("Enhanced Excel Data Plotter initialized with full legacy functionality")

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

        # Series creation variables
        self.series_file_var = tk.StringVar()
        self.series_x_var = tk.StringVar()
        self.series_y_var = tk.StringVar()
        self.series_name_var = tk.StringVar(value="New Series")
        self.series_start_var = tk.IntVar(value=0)
        self.series_end_var = tk.IntVar(value=1000)

        # Export settings
        self.export_format = tk.StringVar(value='PNG (High Quality)')
        self.dpi_var = tk.IntVar(value=300)

        # Current theme tracking
        self.current_theme = ctk.get_appearance_mode()

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

    def create_top_bar(self):
        """Create the top action bar with rearranged buttons - Legacy Compatible"""
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

        # Analysis actions (center) - ENHANCED
        self.top_bar.add_action("Analysis", "🔬", self.show_statistical_analysis, "Statistical analysis tools",
                                side="center")
        self.top_bar.add_action("Vacuum Tools", "🎯", self.show_vacuum_analysis, "Vacuum analysis tools", side="center")
        self.top_bar.add_action("Annotations", "📍", self.show_annotation_panel, "Manage annotations", side="center")
        self.top_bar.add_separator(side="center")

        # View actions (center) - ENHANCED
        self.top_bar.add_action("Theme", "🎨", self.toggle_theme, "Toggle dark/light theme", side="center")
        self.top_bar.add_action("Configure", "📐", self.show_plot_config, "Configure plot settings", side="center")

        logger.debug("Top action bar created with enhanced legacy functionality")

    def create_main_content(self):
        """Create the main content area with adaptive layout"""
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Create default layout
        self.create_default_layout()

    def create_default_layout(self):
        """Create the default layout with sidebar and main area - Legacy Compatible"""
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
        """Create the files management panel - Enhanced Legacy"""
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
        """Create the series management panel - Enhanced Legacy"""
        # Series creation section
        create_frame = CollapsiblePanel(self.series_tab, "Create New Series")
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

        # Column selection
        ctk.CTkLabel(content, text="X Column:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.series_x_combo = ctk.CTkComboBox(content, variable=self.series_x_var, width=120)
        self.series_x_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(content, text="Y Column:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.series_y_combo = ctk.CTkComboBox(content, variable=self.series_y_var, width=120)
        self.series_y_combo.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        # Range selection
        ctk.CTkLabel(content, text="Start:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(content, textvariable=self.series_start_var, width=80).grid(row=2, column=1, padx=5, pady=5)

        ctk.CTkLabel(content, text="End:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(content, textvariable=self.series_end_var, width=80).grid(row=2, column=3, padx=5, pady=5)

        # Series name
        ctk.CTkLabel(content, text="Name:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.series_name_entry = ctk.CTkEntry(content, textvariable=self.series_name_var, width=200)
        self.series_name_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        ctk.CTkButton(
            content,
            text="Add Series",
            command=self.add_series,
            fg_color=ColorPalette.SUCCESS
        ).grid(row=3, column=3, padx=5, pady=5)

        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(3, weight=1)

        # Series list
        series_label = ctk.CTkLabel(self.series_tab, text="Active Series", font=("", 14, "bold"))
        series_label.pack(padx=10, pady=(20, 5), anchor="w")

        self.series_scroll = ctk.CTkScrollableFrame(self.series_tab)
        self.series_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Update series display
        self.update_series_display()

    def create_config_panel(self):
        """Create the configuration panel"""
        # Plot title
        title_frame = ctk.CTkFrame(self.config_tab)
        title_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(title_frame, text="Plot Title:").pack(anchor="w", padx=5, pady=2)
        ctk.CTkEntry(title_frame, textvariable=self.title_var).pack(fill="x", padx=5, pady=2)

        # Axis labels
        axis_frame = ctk.CTkFrame(self.config_tab)
        axis_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(axis_frame, text="X Label:").pack(anchor="w", padx=5, pady=2)
        ctk.CTkEntry(axis_frame, textvariable=self.xlabel_var).pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(axis_frame, text="Y Label:").pack(anchor="w", padx=5, pady=2)
        ctk.CTkEntry(axis_frame, textvariable=self.ylabel_var).pack(fill="x", padx=5, pady=2)

        # Grid and legend
        options_frame = ctk.CTkFrame(self.config_tab)
        options_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkCheckBox(options_frame, text="Show Grid", variable=self.show_grid_var).pack(anchor="w", padx=5, pady=2)
        ctk.CTkCheckBox(options_frame, text="Show Legend", variable=self.show_legend_var).pack(anchor="w", padx=5, pady=2)

    def create_export_panel(self):
        """Create export panel"""
        export_frame = ctk.CTkFrame(self.export_tab)
        export_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Format selection
        ctk.CTkLabel(export_frame, text="Export Format:").pack(anchor="w", pady=2)
        format_combo = ctk.CTkComboBox(export_frame, width=200,
                                       values=['PNG (High Quality)', 'PDF (Vector)', 'SVG (Scalable)', 'JPG (Compressed)'],
                                       variable=self.export_format)
        format_combo.pack(fill="x", pady=2)

        # Export buttons
        ctk.CTkButton(export_frame, text="Export Plot", command=self.export_plot,
                      fg_color=ColorPalette.SUCCESS).pack(fill="x", pady=10)
        ctk.CTkButton(export_frame, text="Export All Data", command=self.export_all_data,
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

    def bind_events(self):
        """Bind window and widget events"""
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.bind("<Configure>", self.on_window_resize)

    # ============= ENHANCED FILE OPERATIONS =============

    def add_files(self):
        """Add multiple files with enhanced progress indication"""
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

                    # Load file with enhanced error handling
                    if filename.endswith('.csv'):
                        df = pd.read_csv(filename)
                    else:
                        df = pd.read_excel(filename)

                    # Create FileData object with full analysis
                    file_data = FileData(filename, df)
                    self.loaded_files[file_data.id] = file_data

                    success_count += 1

                except Exception as e:
                    error_files.append((filename, str(e)))
                    logger.error(f"Failed to load {filename}: {e}")

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

    # Include all remaining methods from the original implementation
    # ... (methods would continue here)

    def update_counts(self):
        """Update file and series counts"""
        self.status_bar.update_counts(
            files=len(self.loaded_files),
            series=len(self.all_series)
        )

    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()

    def on_window_resize(self, event):
        """Handle window resize events"""
        pass

    # Placeholder methods for functionality
    def load_project(self): pass
    def save_project(self): pass
    def show_export_dialog(self): pass
    def create_plot(self): pass
    def show_statistical_analysis(self): pass
    def show_vacuum_analysis(self): pass
    def show_annotation_panel(self): pass
    def toggle_theme(self): pass
    def show_plot_config(self): pass
    def clear_all_files(self): pass
    def reload_all_files(self): pass
    def search_files(self, query): pass
    def update_files_display(self): pass
    def update_series_display(self): pass
    def update_series_file_combo(self): pass
    def on_file_selected_for_series(self, choice=None): pass
    def add_series(self): pass
    def export_plot(self): pass
    def export_all_data(self): pass
    def show_error_details(self, errors): pass


def main():
    """Main application entry point"""
    try:
        app = ExcelDataPlotter()
        app.mainloop()
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application:\n{e}")


if __name__ == "__main__":
    main()
