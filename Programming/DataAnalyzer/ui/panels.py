#!/usr/bin/env python3
"""
Specialized UI panels
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Dict, List, Optional, Any, Callable
import logging

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from ui.components import DataCard, SearchBar, CollapsibleFrame
from models.data_models import FileData, SeriesConfig
from config.constants import UIConfig

logger = logging.getLogger(__name__)


class FilePanel(ctk.CTkScrollableFrame):
    """Panel for managing loaded files"""

    def __init__(self, parent, app_ref, **kwargs):
        super().__init__(parent, **kwargs)

        self.app = app_ref
        self.file_cards: Dict[str, DataCard] = {}

        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        title = ctk.CTkLabel(
            header,
            text="📁 Loaded Files",
            font=("", 16, "bold")
        )
        title.pack(side="left")

        # Add button
        add_btn = ctk.CTkButton(
            header,
            text="+ Add Files",
            command=self.app.add_files,
            width=100
        )
        add_btn.pack(side="right")

        # Search bar
        self.search_bar = SearchBar(
            self,
            on_search=self._filter_files,
            placeholder="Search files..."
        )
        self.search_bar.pack(fill="x", padx=10, pady=(0, 10))

        # File container
        self.file_container = ctk.CTkFrame(self)
        self.file_container.pack(fill="both", expand=True, padx=10)

    def add_file_card(self, file_data: FileData):
        """Add a file card"""
        from utils.helpers import format_file_size

        # Create subtitle with file info
        subtitle = f"{file_data.metadata['rows']:,} rows × {file_data.metadata['columns']} columns"
        subtitle += f" | {format_file_size(file_data.metadata['memory_usage'])}"

        card = DataCard(
            self.file_container,
            title=file_data.filename,
            subtitle=subtitle,
            icon="📊" if file_data.metadata['has_numeric'] else "📄",
            on_click=lambda: self._show_file_preview(file_data),
            on_remove=lambda: self.app.remove_file(file_data.id)
        )
        card.pack(fill="x", pady=5)

        self.file_cards[file_data.id] = card

    def remove_file_card(self, file_id: str):
        """Remove a file card"""
        if file_id in self.file_cards:
            self.file_cards[file_id].destroy()
            del self.file_cards[file_id]

    def clear(self):
        """Clear all file cards"""
        for card in self.file_cards.values():
            card.destroy()
        self.file_cards.clear()

    def _filter_files(self, search_text: str):
        """Filter displayed files"""
        search_lower = search_text.lower()

        for file_id, card in self.file_cards.items():
            file_data = self.app.loaded_files.get(file_id)
            if file_data:
                match = (search_lower in file_data.filename.lower() or
                         any(search_lower in col.lower()
                             for col in file_data.dataframe.columns))

                if match:
                    card.pack(fill="x", pady=5)
                else:
                    card.pack_forget()

    def _show_file_preview(self, file_data: FileData):
        """Show file preview dialog"""
        from ui.dialogs import DataPreviewDialog
        DataPreviewDialog(self, file_data)


class SeriesPanel(ctk.CTkScrollableFrame):
    """Panel for managing data series"""

    def __init__(self, parent, app_ref, **kwargs):
        super().__init__(parent, **kwargs)

        self.app = app_ref
        self.series_cards: Dict[str, DataCard] = {}

        # Header
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=10, pady=10)

        title = ctk.CTkLabel(
            header,
            text="📈 Data Series",
            font=("", 16, "bold")
        )
        title.pack(side="left")

        # Add button
        add_btn = ctk.CTkButton(
            header,
            text="+ Create Series",
            command=self.app.create_series,
            width=100
        )
        add_btn.pack(side="right")

        # Series container
        self.series_container = ctk.CTkFrame(self)
        self.series_container.pack(fill="both", expand=True, padx=10)

    def add_series_card(self, series: SeriesConfig):
        """Add a series card"""
        # Get file name
        file_data = self.app.loaded_files.get(series.file_id)
        file_name = file_data.filename if file_data else "Unknown"

        # Create subtitle
        subtitle = f"{file_name} | {series.x_column} vs {series.y_column}"

        # Determine icon based on visibility
        icon = "👁" if series.visible else "👁‍🗨"

        card = DataCard(
            self.series_container,
            title=series.name,
            subtitle=subtitle,
            icon=icon,
            on_click=lambda: self.app.edit_series(series.id),
            on_remove=lambda: self.app.remove_series(series.id)
        )

        # Add color indicator
        if series.color:
            color_indicator = ctk.CTkLabel(
                card,
                text="●",
                text_color=series.color,
                font=("", 20)
            )
            color_indicator.place(relx=0.95, rely=0.5, anchor="e")

        card.pack(fill="x", pady=5)
        self.series_cards[series.id] = card

    def update_series_card(self, series_id: str):
        """Update a series card"""
        if series_id in self.series_cards:
            # Remove old card
            self.series_cards[series_id].destroy()

            # Add updated card
            series = self.app.series_configs.get(series_id)
            if series:
                self.add_series_card(series)

    def remove_series_card(self, series_id: str):
        """Remove a series card"""
        if series_id in self.series_cards:
            self.series_cards[series_id].destroy()
            del self.series_cards[series_id]

    def clear(self):
        """Clear all series cards"""
        for card in self.series_cards.values():
            card.destroy()
        self.series_cards.clear()


class PlotPanel(ctk.CTkFrame):
    """Panel for displaying plots"""

    def __init__(self, parent, app_ref, **kwargs):
        super().__init__(parent, **kwargs)

        self.app = app_ref
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasTkAgg] = None
        self.toolbar: Optional[NavigationToolbar2Tk] = None

        # Plot container
        self.plot_container = ctk.CTkFrame(self)
        self.plot_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Empty state
        self.empty_label = ctk.CTkLabel(
            self.plot_container,
            text="No plot generated\nClick 'Generate Plot' to create visualization",
            font=("", 14),
            text_color="gray"
        )
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def display_plot(self, figure: Figure):
        """Display a matplotlib figure"""
        # Clear previous plot
        self.clear_plot()

        # Hide empty state
        self.empty_label.place_forget()

        # Create canvas
        self.figure = figure
        self.canvas = FigureCanvasTkAgg(figure, master=self.plot_container)
        self.canvas.draw()

        # Pack canvas
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True)

        # Create toolbar
        toolbar_frame = ctk.CTkFrame(self.plot_container, height=40)
        toolbar_frame.pack(fill="x")
        toolbar_frame.pack_propagate(False)

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

    def clear_plot(self):
        """Clear current plot"""
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        if self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

        self.figure = None

        # Show empty state
        self.empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def has_plot(self) -> bool:
        """Check if plot exists"""
        return self.figure is not None

    def get_axes(self):
        """Get current axes"""
        if self.figure and self.figure.axes:
            return self.figure.axes[0]
        return None


class ConfigPanel(ctk.CTkScrollableFrame):
    """Panel for plot configuration"""

    def __init__(self, parent, app_ref, **kwargs):
        super().__init__(parent, **kwargs)

        self.app = app_ref
        self.config_vars = {}

        # Title
        title = ctk.CTkLabel(
            self,
            text="⚙️ Plot Configuration",
            font=("", 16, "bold")
        )
        title.pack(pady=10)

        # Create configuration sections
        self._create_general_section()
        self._create_axes_section()
        self._create_style_section()
        self._create_export_section()

    def _create_general_section(self):
        """Create general configuration section"""
        section = CollapsibleFrame(self, title="General Settings")
        section.pack(fill="x", padx=10, pady=5)

        content = section.get_content_frame()

        # Title
        self._add_config_field(
            content, "title", "Plot Title",
            default="Data Analysis", field_type="entry"
        )

        # Plot type
        self._add_config_field(
            content, "plot_type", "Plot Type",
            default="line", field_type="combo",
            values=["line", "scatter", "bar", "area"]
        )

        # Figure size
        size_frame = ctk.CTkFrame(content)
        size_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(size_frame, text="Figure Size:").pack(side="left", padx=5)

        self._add_config_field(
            size_frame, "fig_width", "Width",
            default=14, field_type="spinbox", from_=5, to=30
        )

        self._add_config_field(
            size_frame, "fig_height", "Height",
            default=9, field_type="spinbox", from_=3, to=20
        )

    def _create_axes_section(self):
        """Create axes configuration section"""
        section = CollapsibleFrame(self, title="Axes Settings", collapsed=True)
        section.pack(fill="x", padx=10, pady=5)

        content = section.get_content_frame()

        # X-axis
        self._add_config_field(
            content, "xlabel", "X Label",
            default="X Axis", field_type="entry"
        )

        self._add_config_field(
            content, "log_scale_x", "Log Scale X",
            default=False, field_type="checkbox"
        )

        # Y-axis
        self._add_config_field(
            content, "ylabel", "Y Label",
            default="Y Axis", field_type="entry"
        )

        self._add_config_field(
            content, "log_scale_y", "Log Scale Y",
            default=False, field_type="checkbox"
        )

    def _create_style_section(self):
        """Create style configuration section"""
        section = CollapsibleFrame(self, title="Style Settings", collapsed=True)
        section.pack(fill="x", padx=10, pady=5)

        content = section.get_content_frame()

        # Grid
        self._add_config_field(
            content, "show_grid", "Show Grid",
            default=True, field_type="checkbox"
        )

        self._add_config_field(
            content, "grid_alpha", "Grid Opacity",
            default=0.3, field_type="slider", from_=0, to=1
        )

        # Legend
        self._add_config_field(
            content, "show_legend", "Show Legend",
            default=True, field_type="checkbox"
        )

        # Theme
        self._add_config_field(
            content, "theme", "Plot Theme",
            default="default", field_type="combo",
            values=["default", "dark", "seaborn", "ggplot"]
        )

    def _create_export_section(self):
        """Create export configuration section"""
        section = CollapsibleFrame(self, title="Export Settings", collapsed=True)
        section.pack(fill="x", padx=10, pady=5)

        content = section.get_content_frame()

        self._add_config_field(
            content, "export_dpi", "Export DPI",
            default=300, field_type="spinbox", from_=72, to=600
        )

    def _add_config_field(
            self,
            parent,
            key: str,
            label: str,
            default: Any,
            field_type: str = "entry",
            **kwargs
    ):
        """Add a configuration field"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=5)

        # Label
        lbl = ctk.CTkLabel(frame, text=label, width=120, anchor="w")
        lbl.pack(side="left", padx=5)

        # Create appropriate widget
        if field_type == "entry":
            var = tk.StringVar(value=str(default))
            widget = ctk.CTkEntry(frame, textvariable=var, width=200)

        elif field_type == "spinbox":
            var = tk.IntVar(value=int(default))
            widget = ttk.Spinbox(
                frame,
                textvariable=var,
                from_=kwargs.get('from_', 0),
                to=kwargs.get('to', 100),
                width=10
            )

        elif field_type == "slider":
            var = tk.DoubleVar(value=float(default))
            widget = ctk.CTkSlider(
                frame,
                variable=var,
                from_=kwargs.get('from_', 0),
                to=kwargs.get('to', 1),
                width=200
            )

        elif field_type == "checkbox":
            var = tk.BooleanVar(value=bool(default))
            widget = ctk.CTkCheckBox(frame, text="", variable=var)

        elif field_type == "combo":
            var = tk.StringVar(value=str(default))
            widget = ctk.CTkComboBox(
                frame,
                variable=var,
                values=kwargs.get('values', []),
                width=200
            )
        else:
            return

        widget.pack(side="left", padx=5)
        self.config_vars[key] = var

    def get_plot_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        config = {}

        for key, var in self.config_vars.items():
            try:
                config[key] = var.get()
            except:
                pass

        return config

    def set_plot_config(self, config: Dict[str, Any]):
        """Set configuration values"""
        for key, value in config.items():
            if key in self.config_vars:
                try:
                    self.config_vars[key].set(value)
                except:
                    pass