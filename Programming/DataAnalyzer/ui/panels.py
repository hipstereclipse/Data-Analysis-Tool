#!/usr/bin/env python3
"""
UI Panels for Excel Data Plotter
Main panel components for the application interface
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Optional, Callable, Any
import pandas as pd

from config.constants import ColorPalette, PlotTypes, UIConfig
from models.data_models import FileData, SeriesConfig
from ui.components import FileCard, SeriesCard, SearchBar, CollapsiblePanel


class FilePanel(ctk.CTkFrame):
    """
    Panel for file management
    Displays loaded files and provides file operations
    """

    def __init__(self, parent, on_file_select: Callable = None,
                 on_file_remove: Callable = None, **kwargs):
        """
        Initialize file panel

        Args:
            parent: Parent widget
            on_file_select: Callback when file is selected
            on_file_remove: Callback when file is removed
        """
        super().__init__(parent, **kwargs)

        self.on_file_select = on_file_select
        self.on_file_remove = on_file_remove
        self.file_cards: Dict[str, FileCard] = {}
        self.selected_file_id: Optional[str] = None

        # Configure grid
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.create_header()

        # Search bar
        self.search_bar = SearchBar(self, on_search=self.filter_files)
        self.search_bar.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Scrollable frame for file cards
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # Info panel
        self.create_info_panel()

    def create_header(self):
        """Create panel header"""
        header_frame = ctk.CTkFrame(self, height=40)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(header_frame, text="Loaded Files",
                                   font=("", 14, "bold"))
        title_label.grid(row=0, column=0, sticky="w", padx=10)

        # Count label
        self.count_label = ctk.CTkLabel(header_frame, text="(0 files)",
                                        font=("", 11))
        self.count_label.grid(row=0, column=1, padx=10)

    def create_info_panel(self):
        """Create information panel at bottom"""
        info_frame = ctk.CTkFrame(self, height=100)
        info_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        # Info text
        self.info_text = ctk.CTkTextbox(info_frame, height=80)
        self.info_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.info_text.insert("1.0", "No file selected")

    def add_file(self, file_data: FileData):
        """
        Add a file to the panel

        Args:
            file_data: FileData object to add
        """
        # Create file card
        card = FileCard(self.scroll_frame, file_data,
                        on_remove=self.remove_file)
        card.pack(fill="x", padx=5, pady=2)

        # Bind click event
        card.bind("<Button-1>", lambda e: self.select_file(file_data.file_id))

        # Store reference
        self.file_cards[file_data.file_id] = card

        # Update count
        self.update_count()

    def remove_file(self, file_id: str):
        """Remove a file from the panel"""
        if file_id in self.file_cards:
            self.file_cards[file_id].destroy()
            del self.file_cards[file_id]

            if self.on_file_remove:
                self.on_file_remove(file_id)

            self.update_count()

    def select_file(self, file_id: str):
        """Select a file and show its information"""
        # Update selection state
        for fid, card in self.file_cards.items():
            card.set_selected(fid == file_id)

        self.selected_file_id = file_id

        # Update info panel
        if file_id in self.file_cards:
            file_data = self.file_cards[file_id].file_data
            info_text = f"File: {file_data.filename}\n"
            info_text += f"Path: {file_data.filepath}\n"
            info_text += f"Size: {file_data.file_size:,} bytes\n"
            info_text += f"Rows: {file_data.row_count:,}\n"
            info_text += f"Columns: {file_data.column_count}\n"
            info_text += f"Missing Data: {file_data.missing_data_percent:.2f}%\n"

            if file_data.datetime_columns:
                info_text += f"DateTime Columns: {', '.join(file_data.datetime_columns)}\n"
            if file_data.numeric_columns:
                info_text += f"Numeric Columns: {', '.join(file_data.numeric_columns[:5])}"
                if len(file_data.numeric_columns) > 5:
                    info_text += f" (+{len(file_data.numeric_columns) - 5} more)"

            self.info_text.delete("1.0", "end")
            self.info_text.insert("1.0", info_text)

        if self.on_file_select:
            self.on_file_select(file_id)

    def filter_files(self, search_text: str):
        """Filter displayed files based on search text"""
        for file_id, card in self.file_cards.items():
            if search_text.lower() in card.file_data.filename.lower():
                card.pack(fill="x", padx=5, pady=2)
            else:
                card.pack_forget()

    def update_count(self):
        """Update file count display"""
        count = len(self.file_cards)
        self.count_label.configure(text=f"({count} file{'s' if count != 1 else ''})")

    def clear(self):
        """Clear all files from panel"""
        for card in self.file_cards.values():
            card.destroy()
        self.file_cards.clear()
        self.selected_file_id = None
        self.update_count()

        self.info_text.delete("1.0", "end")
        self.info_text.insert("1.0", "No file selected")

    def get_selected_file(self) -> Optional[str]:
        """Get currently selected file ID"""
        return self.selected_file_id


class SeriesPanel(ctk.CTkFrame):
    """
    Panel for series configuration and management
    """

    def __init__(self, parent, on_series_edit: Callable = None,
                 on_series_remove: Callable = None,
                 on_series_toggle: Callable = None, **kwargs):
        """
        Initialize series panel

        Args:
            parent: Parent widget
            on_series_edit: Callback when series is edited
            on_series_remove: Callback when series is removed
            on_series_toggle: Callback when series visibility is toggled
        """
        super().__init__(parent, **kwargs)

        self.on_series_edit = on_series_edit
        self.on_series_remove = on_series_remove
        self.on_series_toggle = on_series_toggle
        self.series_cards: Dict[str, SeriesCard] = {}

        # Configure grid
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.create_header()

        # Controls
        self.create_controls()

        # Scrollable frame for series cards
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)

        # Empty state message
        self.empty_label = ctk.CTkLabel(self.scroll_frame,
                                        text="No series configured\n\nClick 'Add Series' to create a new data series",
                                        font=("", 12), text_color=("gray50", "gray60"))
        self.empty_label.pack(expand=True, pady=50)

    def create_header(self):
        """Create panel header"""
        header_frame = ctk.CTkFrame(self, height=40)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(header_frame, text="Data Series",
                                   font=("", 14, "bold"))
        title_label.grid(row=0, column=0, sticky="w", padx=10)

        # Count label
        self.count_label = ctk.CTkLabel(header_frame, text="(0 series)",
                                        font=("", 11))
        self.count_label.grid(row=0, column=1, padx=10)

    def create_controls(self):
        """Create control buttons"""
        control_frame = ctk.CTkFrame(self)
        control_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Visibility controls
        vis_frame = ctk.CTkFrame(control_frame)
        vis_frame.pack(side="left", padx=5)

        ctk.CTkButton(vis_frame, text="Show All", width=80,
                      command=lambda: self.set_all_visibility(True)).pack(side="left", padx=2)
        ctk.CTkButton(vis_frame, text="Hide All", width=80,
                      command=lambda: self.set_all_visibility(False)).pack(side="left", padx=2)

        # Action buttons
        action_frame = ctk.CTkFrame(control_frame)
        action_frame.pack(side="right", padx=5)

        ctk.CTkButton(action_frame, text="Clear All", width=80,
                      command=self.clear_all_series).pack(side="left", padx=2)

    def add_series(self, series_config: SeriesConfig):
        """
        Add a series to the panel

        Args:
            series_config: SeriesConfig object to add
        """
        # Hide empty message
        self.empty_label.pack_forget()

        # Create series card
        card = SeriesCard(self.scroll_frame, series_config,
                          on_edit=self.on_series_edit,
                          on_remove=self.remove_series,
                          on_toggle=self.on_series_toggle)
        card.pack(fill="x", padx=5, pady=2)

        # Store reference
        self.series_cards[series_config.series_id] = card

        # Update count
        self.update_count()

    def remove_series(self, series_id: str):
        """Remove a series from the panel"""
        if series_id in self.series_cards:
            self.series_cards[series_id].destroy()
            del self.series_cards[series_id]

            if self.on_series_remove:
                self.on_series_remove(series_id)

            self.update_count()

            # Show empty message if no series
            if not self.series_cards:
                self.empty_label.pack(expand=True, pady=50)

    def update_series(self, series_config: SeriesConfig):
        """Update an existing series"""
        if series_config.series_id in self.series_cards:
            self.series_cards[series_config.series_id].update_series(series_config)

    def set_all_visibility(self, visible: bool):
        """Set visibility for all series"""
        for card in self.series_cards.values():
            card.visible_var.set(visible)
            card.toggle_visibility()

    def clear_all_series(self):
        """Clear all series from panel"""
        if not self.series_cards:
            return

        from tkinter import messagebox
        if messagebox.askyesno("Clear All", "Remove all series?"):
            for series_id in list(self.series_cards.keys()):
                self.remove_series(series_id)

    def update_count(self):
        """Update series count display"""
        count = len(self.series_cards)
        visible = sum(1 for card in self.series_cards.values() if card.series.visible)
        self.count_label.configure(text=f"({visible}/{count} visible)")

    def clear(self):
        """Clear all series from panel"""
        for card in self.series_cards.values():
            card.destroy()
        self.series_cards.clear()
        self.update_count()
        self.empty_label.pack(expand=True, pady=50)

    def get_series_list(self) -> List[SeriesConfig]:
        """Get list of all series configurations"""
        return [card.series for card in self.series_cards.values()]

    def get_visible_series(self) -> List[SeriesConfig]:
        """Get list of visible series configurations"""
        return [card.series for card in self.series_cards.values() if card.series.visible]


class PlotPanel(ctk.CTkFrame):
    """
    Panel for plot display and interaction
    """

    def __init__(self, parent, **kwargs):
        """Initialize plot panel"""
        super().__init__(parent, **kwargs)

        self.figure = None
        self.canvas = None
        self.toolbar = None
        self.axes = None

        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create empty state
        self.create_empty_state()

    def create_empty_state(self):
        """Create empty state display"""
        self.empty_frame = ctk.CTkFrame(self)
        self.empty_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # Welcome message
        welcome_label = ctk.CTkLabel(
            self.empty_frame,
            text="Multi-File Excel Data Plotter\nVacuum Analysis Edition\n\n"
                 "Load files and configure series to begin plotting",
            font=("", 16),
            text_color=("gray40", "gray60")
        )
        welcome_label.pack(expand=True)

        # Tips
        tips_frame = ctk.CTkFrame(self.empty_frame)
        tips_frame.pack(pady=20)

        tips = [
            "📁 Add Excel or CSV files using the Files panel",
            "📊 Configure data series in the Series panel",
            "⚙️ Customize plot appearance in the Config panel",
            "🔬 Use Analysis menu for vacuum-specific tools"
        ]

        for tip in tips:
            tip_label = ctk.CTkLabel(tips_frame, text=tip, font=("", 11),
                                     text_color=("gray50", "gray60"))
            tip_label.pack(anchor="w", pady=2)

    def set_figure(self, figure, canvas, toolbar):
        """
        Set the matplotlib figure and canvas

        Args:
            figure: Matplotlib figure
            canvas: FigureCanvasTkAgg object
            toolbar: NavigationToolbar2Tk object
        """
        # Remove empty state
        self.empty_frame.grid_forget()

        # Remove old canvas if exists
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        if self.toolbar:
            self.toolbar.destroy()

        # Set new figure
        self.figure = figure
        self.canvas = canvas
        self.toolbar = toolbar
        self.axes = figure.axes[0] if figure.axes else None

        # Pack canvas
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Create toolbar frame
        toolbar_frame = ctk.CTkFrame(self)
        toolbar_frame.grid(row=1, column=0, sticky="ew")

        # Pack toolbar
        self.toolbar.pack(side="left", fill="x", expand=True)

    def clear_plot(self):
        """Clear the plot and show empty state"""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None
        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

        self.figure = None
        self.axes = None

        # Show empty state
        self.empty_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def get_axes(self):
        """Get the current axes object"""
        return self.axes


class ConfigPanel(ctk.CTkFrame):
    """
    Panel for plot configuration
    """

    def __init__(self, parent, on_config_change: Callable = None, **kwargs):
        """
        Initialize config panel

        Args:
            parent: Parent widget
            on_config_change: Callback when configuration changes
        """
        super().__init__(parent, **kwargs)

        self.on_config_change = on_config_change

        # Create scrollable frame
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Create configuration sections
        self.create_title_section()
        self.create_axes_section()
        self.create_scale_section()
        self.create_grid_section()
        self.create_legend_section()
        self.create_figure_section()
        self.create_action_buttons()

    def create_title_section(self):
        """Create title configuration section"""
        section = CollapsiblePanel(self.scroll_frame, "Title Settings", expanded=True)
        section.pack(fill="x", padx=5, pady=5)

        content = section.get_content_frame()

        # Title text
        ctk.CTkLabel(content, text="Plot Title:").pack(anchor="w", padx=5, pady=2)
        self.title_var = tk.StringVar(value="Data Analysis")
        title_entry = ctk.CTkEntry(content, textvariable=self.title_var)
        title_entry.pack(fill="x", padx=5, pady=2)

        # Title size
        size_frame = ctk.CTkFrame(content)
        size_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(size_frame, text="Size:").pack(side="left", padx=5)
        self.title_size_var = tk.IntVar(value=16)
        size_slider = ctk.CTkSlider(size_frame, from_=8, to=24,
                                    variable=self.title_size_var)
        size_slider.pack(side="left", fill="x", expand=True, padx=5)
        size_label = ctk.CTkLabel(size_frame, textvariable=self.title_size_var, width=30)
        size_label.pack(side="left", padx=5)

    def create_axes_section(self):
        """Create axes configuration section"""
        section = CollapsiblePanel(self.scroll_frame, "Axes Labels", expanded=True)
        section.pack(fill="x", padx=5, pady=5)

        content = section.get_content_frame()

        # X-axis label
        ctk.CTkLabel(content, text="X-Axis Label:").pack(anchor="w", padx=5, pady=2)
        self.xlabel_var = tk.StringVar(value="X Axis")
        xlabel_entry = ctk.CTkEntry(content, textvariable=self.xlabel_var)
        xlabel_entry.pack(fill="x", padx=5, pady=2)

        # Y-axis label
        ctk.CTkLabel(content, text="Y-Axis Label:").pack(anchor="w", padx=5, pady=2)
        self.ylabel_var = tk.StringVar(value="Y Axis")
        ylabel_entry = ctk.CTkEntry(content, textvariable=self.ylabel_var)
        ylabel_entry.pack(fill="x", padx=5, pady=2)

        # Label sizes
        size_frame = ctk.CTkFrame(content)
        size_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(size_frame, text="Label Size:").pack(side="left", padx=5)
        self.label_size_var = tk.IntVar(value=12)
        size_slider = ctk.CTkSlider(size_frame, from_=8, to=20,
                                    variable=self.label_size_var)
        size_slider.pack(side="left", fill="x", expand=True, padx=5)
        size_label = ctk.CTkLabel(size_frame, textvariable=self.label_size_var, width=30)
        size_label.pack(side="left", padx=5)

    def create_scale_section(self):
        """Create scale configuration section"""
        section = CollapsiblePanel(self.scroll_frame, "Scale Options", expanded=False)
        section.pack(fill="x", padx=5, pady=5)

        content = section.get_content_frame()

        # Log scale options
        self.log_scale_x_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(content, text="Logarithmic X-Axis",
                        variable=self.log_scale_x_var,
                        command=self.on_config_change).pack(anchor="w", padx=5, pady=5)

        self.log_scale_y_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(content, text="Logarithmic Y-Axis",
                        variable=self.log_scale_y_var,
                        command=self.on_config_change).pack(anchor="w", padx=5, pady=5)

        # Auto scale options
        self.auto_scale_x_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(content, text="Auto Scale X-Axis",
                        variable=self.auto_scale_x_var,
                        command=self.toggle_x_limits).pack(anchor="w", padx=5, pady=5)

        # X limits
        x_limit_frame = ctk.CTkFrame(content)
        x_limit_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(x_limit_frame, text="X Min:").pack(side="left", padx=5)
        self.x_min_var = tk.DoubleVar(value=0)
        self.x_min_entry = ctk.CTkEntry(x_limit_frame, textvariable=self.x_min_var, width=80)
        self.x_min_entry.pack(side="left", padx=5)

        ctk.CTkLabel(x_limit_frame, text="X Max:").pack(side="left", padx=10)
        self.x_max_var = tk.DoubleVar(value=100)
        self.x_max_entry = ctk.CTkEntry(x_limit_frame, textvariable=self.x_max_var, width=80)
        self.x_max_entry.pack(side="left", padx=5)

        self.auto_scale_y_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(content, text="Auto Scale Y-Axis",
                        variable=self.auto_scale_y_var,
                        command=self.toggle_y_limits).pack(anchor="w", padx=5, pady=5)

        # Y limits
        y_limit_frame = ctk.CTkFrame(content)
        y_limit_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(y_limit_frame, text="Y Min:").pack(side="left", padx=5)
        self.y_min_var = tk.DoubleVar(value=0)
        self.y_min_entry = ctk.CTkEntry(y_limit_frame, textvariable=self.y_min_var, width=80)
        self.y_min_entry.pack(side="left", padx=5)

        ctk.CTkLabel(y_limit_frame, text="Y Max:").pack(side="left", padx=10)
        self.y_max_var = tk.DoubleVar(value=100)
        self.y_max_entry = ctk.CTkEntry(y_limit_frame, textvariable=self.y_max_var, width=80)
        self.y_max_entry.pack(side="left", padx=5)

        # Initially disable limit entries
        self.toggle_x_limits()
        self.toggle_y_limits()

    def create_grid_section(self):
        """Create grid configuration section"""
        section = CollapsiblePanel(self.scroll_frame, "Grid Settings", expanded=False)
        section.pack(fill="x", padx=5, pady=5)

        content = section.get_content_frame()

        # Show grid
        self.show_grid_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(content, text="Show Grid",
                        variable=self.show_grid_var,
                        command=self.on_config_change).pack(anchor="w", padx=5, pady=5)

        # Grid style
        style_frame = ctk.CTkFrame(content)
        style_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(style_frame, text="Grid Style:").pack(side="left", padx=5)
        self.grid_style_var = tk.StringVar(value="-")
        style_combo = ctk.CTkComboBox(style_frame, values=["-", "--", ":", "-."],
                                      variable=self.grid_style_var, width=100)
        style_combo.pack(side="left", padx=5)

        # Grid alpha
        alpha_frame = ctk.CTkFrame(content)
        alpha_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(alpha_frame, text="Grid Alpha:").pack(side="left", padx=5)
        self.grid_alpha_var = tk.DoubleVar(value=0.3)
        alpha_slider = ctk.CTkSlider(alpha_frame, from_=0.1, to=1.0,
                                     variable=self.grid_alpha_var)
        alpha_slider.pack(side="left", fill="x", expand=True, padx=5)
        alpha_label = ctk.CTkLabel(alpha_frame, text="0.3", width=40)
        alpha_label.pack(side="left", padx=5)

        # Update label when slider changes
        def update_alpha_label(value):
            alpha_label.configure(text=f"{value:.2f}")
            if self.on_config_change:
                self.on_config_change()

        alpha_slider.configure(command=update_alpha_label)

    def create_legend_section(self):
        """Create legend configuration section"""
        section = CollapsiblePanel(self.scroll_frame, "Legend Settings", expanded=False)
        section.pack(fill="x", padx=5, pady=5)

        content = section.get_content_frame()

        # Show legend
        self.show_legend_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(content, text="Show Legend",
                        variable=self.show_legend_var,
                        command=self.on_config_change).pack(anchor="w", padx=5, pady=5)

        # Legend location
        loc_frame = ctk.CTkFrame(content)
        loc_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(loc_frame, text="Location:").pack(side="left", padx=5)
        self.legend_loc_var = tk.StringVar(value="best")
        loc_combo = ctk.CTkComboBox(loc_frame,
                                    values=["best", "upper right", "upper left",
                                            "lower right", "lower left", "center",
                                            "upper center", "lower center",
                                            "center left", "center right"],
                                    variable=self.legend_loc_var, width=150)
        loc_combo.pack(side="left", padx=5)

        # Legend options
        self.legend_frameon_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(content, text="Show Frame",
                        variable=self.legend_frameon_var,
                        command=self.on_config_change).pack(anchor="w", padx=5, pady=2)

        self.legend_fancybox_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(content, text="Fancy Box",
                        variable=self.legend_fancybox_var,
                        command=self.on_config_change).pack(anchor="w", padx=5, pady=2)

        self.legend_shadow_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(content, text="Shadow",
                        variable=self.legend_shadow_var,
                        command=self.on_config_change).pack(anchor="w", padx=5, pady=2)

    def create_figure_section(self):
        """Create figure size configuration section"""
        section = CollapsiblePanel(self.scroll_frame, "Figure Size", expanded=False)
        section.pack(fill="x", padx=5, pady=5)

        content = section.get_content_frame()

        # Width
        width_frame = ctk.CTkFrame(content)
        width_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(width_frame, text="Width:").pack(side="left", padx=5)
        self.fig_width_var = tk.DoubleVar(value=14)
        width_slider = ctk.CTkSlider(width_frame, from_=8, to=20,
                                     variable=self.fig_width_var)
        width_slider.pack(side="left", fill="x", expand=True, padx=5)
        width_label = ctk.CTkLabel(width_frame, text="14", width=40)
        width_label.pack(side="left", padx=5)

        # Height
        height_frame = ctk.CTkFrame(content)
        height_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(height_frame, text="Height:").pack(side="left", padx=5)
        self.fig_height_var = tk.DoubleVar(value=9)
        height_slider = ctk.CTkSlider(height_frame, from_=6, to=12,
                                      variable=self.fig_height_var)
        height_slider.pack(side="left", fill="x", expand=True, padx=5)
        height_label = ctk.CTkLabel(height_frame, text="9", width=40)
        height_label.pack(side="left", padx=5)

        # DPI
        dpi_frame = ctk.CTkFrame(content)
        dpi_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(dpi_frame, text="DPI:").pack(side="left", padx=5)
        self.dpi_var = tk.IntVar(value=100)
        dpi_slider = ctk.CTkSlider(dpi_frame, from_=50, to=200,
                                   variable=self.dpi_var)
        dpi_slider.pack(side="left", fill="x", expand=True, padx=5)
        dpi_label = ctk.CTkLabel(dpi_frame, text="100", width=40)
        dpi_label.pack(side="left", padx=5)

        # Update labels
        def update_width_label(value):
            width_label.configure(text=f"{value:.1f}")
            if self.on_config_change:
                self.on_config_change()

        def update_height_label(value):
            height_label.configure(text=f"{value:.1f}")
            if self.on_config_change:
                self.on_config_change()

        def update_dpi_label(value):
            dpi_label.configure(text=f"{int(value)}")
            if self.on_config_change:
                self.on_config_change()

        width_slider.configure(command=update_width_label)
        height_slider.configure(command=update_height_label)
        dpi_slider.configure(command=update_dpi_label)

    def create_action_buttons(self):
        """Create action buttons"""
        button_frame = ctk.CTkFrame(self.scroll_frame)
        button_frame.pack(fill="x", padx=5, pady=10)

        ctk.CTkButton(button_frame, text="Apply Changes",
                      command=self.apply_config,
                      fg_color=ColorPalette.SUCCESS).pack(fill="x", pady=2)

        ctk.CTkButton(button_frame, text="Reset Defaults",
                      command=self.reset_defaults).pack(fill="x", pady=2)

    def toggle_x_limits(self):
        """Enable/disable X limit entries based on auto scale"""
        state = "disabled" if self.auto_scale_x_var.get() else "normal"
        self.x_min_entry.configure(state=state)
        self.x_max_entry.configure(state=state)

    def toggle_y_limits(self):
        """Enable/disable Y limit entries based on auto scale"""
        state = "disabled" if self.auto_scale_y_var.get() else "normal"
        self.y_min_entry.configure(state=state)
        self.y_max_entry.configure(state=state)

    def apply_config(self):
        """Apply configuration changes"""
        if self.on_config_change:
            self.on_config_change()

    def reset_defaults(self):
        """Reset to default configuration"""
        self.title_var.set("Data Analysis")
        self.title_size_var.set(16)
        self.xlabel_var.set("X Axis")
        self.ylabel_var.set("Y Axis")
        self.label_size_var.set(12)

        self.log_scale_x_var.set(False)
        self.log_scale_y_var.set(False)
        self.auto_scale_x_var.set(True)
        self.auto_scale_y_var.set(True)

        self.show_grid_var.set(True)
        self.grid_style_var.set("-")
        self.grid_alpha_var.set(0.3)

        self.show_legend_var.set(True)
        self.legend_loc_var.set("best")
        self.legend_frameon_var.set(True)
        self.legend_fancybox_var.set(True)
        self.legend_shadow_var.set(False)

        self.fig_width_var.set(14)
        self.fig_height_var.set(9)
        self.dpi_var.set(100)

        self.toggle_x_limits()
        self.toggle_y_limits()

        if self.on_config_change:
            self.on_config_change()

    def get_plot_config(self) -> Dict[str, Any]:
        """Get current plot configuration as dictionary"""
        config = {
            'title': self.title_var.get(),
            'title_size': self.title_size_var.get(),
            'xlabel': self.xlabel_var.get(),
            'ylabel': self.ylabel_var.get(),
            'label_size': self.label_size_var.get(),

            'log_scale_x': self.log_scale_x_var.get(),
            'log_scale_y': self.log_scale_y_var.get(),
            'auto_scale_x': self.auto_scale_x_var.get(),
            'auto_scale_y': self.auto_scale_y_var.get(),

            'show_grid': self.show_grid_var.get(),
            'grid_style': self.grid_style_var.get(),
            'grid_alpha': self.grid_alpha_var.get(),

            'show_legend': self.show_legend_var.get(),
            'legend_loc': self.legend_loc_var.get(),
            'legend_frameon': self.legend_frameon_var.get(),
            'legend_fancybox': self.legend_fancybox_var.get(),
            'legend_shadow': self.legend_shadow_var.get(),

            'fig_width': self.fig_width_var.get(),
            'fig_height': self.fig_height_var.get(),
            'dpi': self.dpi_var.get()
        }

        if not self.auto_scale_x_var.get():
            config['x_min'] = self.x_min_var.get()
            config['x_max'] = self.x_max_var.get()

        if not self.auto_scale_y_var.get():
            config['y_min'] = self.y_min_var.get()
            config['y_max'] = self.y_max_var.get()

        return config

    def set_plot_config(self, config: Dict[str, Any]):
        """Set plot configuration from dictionary"""
        if 'title' in config:
            self.title_var.set(config['title'])
        if 'title_size' in config:
            self.title_size_var.set(config['title_size'])
        if 'xlabel' in config:
            self.xlabel_var.set(config['xlabel'])
        if 'ylabel' in config:
            self.ylabel_var.set(config['ylabel'])
        if 'label_size' in config:
            self.label_size_var.set(config['label_size'])

        if 'log_scale_x' in config:
            self.log_scale_x_var.set(config['log_scale_x'])
        if 'log_scale_y' in config:
            self.log_scale_y_var.set(config['log_scale_y'])
        if 'auto_scale_x' in config:
            self.auto_scale_x_var.set(config['auto_scale_x'])
        if 'auto_scale_y' in config:
            self.auto_scale_y_var.set(config['auto_scale_y'])

        if 'show_grid' in config:
            self.show_grid_var.set(config['show_grid'])
        if 'grid_style' in config:
            self.grid_style_var.set(config['grid_style'])
        if 'grid_alpha' in config:
            self.grid_alpha_var.set(config['grid_alpha'])

        if 'show_legend' in config:
            self.show_legend_var.set(config['show_legend'])
        if 'legend_loc' in config:
            self.legend_loc_var.set(config['legend_loc'])

        if 'fig_width' in config:
            self.fig_width_var.set(config['fig_width'])
        if 'fig_height' in config:
            self.fig_height_var.set(config['fig_height'])
        if 'dpi' in config:
            self.dpi_var.set(config['dpi'])

        if 'x_min' in config:
            self.x_min_var.set(config['x_min'])
        if 'x_max' in config:
            self.x_max_var.set(config['x_max'])
        if 'y_min' in config:
            self.y_min_var.set(config['y_min'])
        if 'y_max' in config:
            self.y_max_var.set(config['y_max'])

        self.toggle_x_limits()
        self.toggle_y_limits()