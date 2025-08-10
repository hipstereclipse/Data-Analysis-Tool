#!/usr/bin/env python3
"""
UI Components for Excel Data Plotter - Complete Implementation
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Callable, Optional, List, Dict, Any
import pandas as pd
import os
from pathlib import Path


class FileCard(ctk.CTkFrame):
    """Card widget for displaying file information"""

    def __init__(self, parent, file_data, on_select=None, on_remove=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.file_data = file_data
        self.on_select = on_select
        self.on_remove = on_remove
        self.is_selected = False

        self.configure(height=80)

        # Main content frame
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # File name
        name_label = ctk.CTkLabel(
            content_frame,
            text=file_data.filename,
            font=("", 12, "bold"),
            anchor="w"
        )
        name_label.pack(fill="x", padx=5, pady=(5, 0))

        # File info
        info_text = f"{file_data.row_count:,} rows × {file_data.column_count} columns"
        if file_data.file_size:
            size_mb = file_data.file_size / (1024 * 1024)
            info_text += f" • {size_mb:.1f} MB"

        info_label = ctk.CTkLabel(
            content_frame,
            text=info_text,
            font=("", 10),
            anchor="w",
            text_color=("gray60", "gray40")
        )
        info_label.pack(fill="x", padx=5, pady=(0, 5))

        # Action buttons frame
        button_frame = ctk.CTkFrame(content_frame)
        button_frame.pack(fill="x", padx=5, pady=(0, 5))

        # Remove button
        if on_remove:
            remove_btn = ctk.CTkButton(
                button_frame,
                text="×",
                width=25,
                height=25,
                command=lambda: on_remove(file_data.file_id),
                fg_color="transparent",
                hover_color=("gray80", "gray30")
            )
            remove_btn.pack(side="right", padx=2)

        # Bind click event
        self.bind("<Button-1>", self._on_click)
        content_frame.bind("<Button-1>", self._on_click)
        name_label.bind("<Button-1>", self._on_click)
        info_label.bind("<Button-1>", self._on_click)

    def _on_click(self, event):
        """Handle click event"""
        if self.on_select:
            self.on_select(self.file_data.file_id)

    def set_selected(self, selected: bool):
        """Set selection state"""
        self.is_selected = selected
        if selected:
            self.configure(fg_color=("gray85", "gray25"))
        else:
            self.configure(fg_color=("gray95", "gray15"))


class SeriesCard(ctk.CTkFrame):
    """Card widget for displaying series information"""

    def __init__(self, parent, series_config, on_edit=None, on_remove=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.series_config = series_config
        self.on_edit = on_edit
        self.on_remove = on_remove

        self.configure(height=100)

        # Main content
        content_frame = ctk.CTkFrame(self)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Series name with color indicator
        header_frame = ctk.CTkFrame(content_frame)
        header_frame.pack(fill="x", padx=5, pady=(5, 0))

        # Color indicator
        color_label = ctk.CTkLabel(
            header_frame,
            text="●",
            font=("", 14),
            text_color=series_config.color,
            width=20
        )
        color_label.pack(side="left", padx=(0, 5))

        # Series name
        name_label = ctk.CTkLabel(
            header_frame,
            text=series_config.name,
            font=("", 12, "bold"),
            anchor="w"
        )
        name_label.pack(side="left", fill="x", expand=True)

        # Info
        info_text = f"{series_config.x_column} vs {series_config.y_column}"
        if series_config.start_index or series_config.end_index:
            info_text += f" [{series_config.start_index}:{series_config.end_index}]"

        info_label = ctk.CTkLabel(
            content_frame,
            text=info_text,
            font=("", 10),
            anchor="w",
            text_color=("gray60", "gray40")
        )
        info_label.pack(fill="x", padx=5, pady=(0, 5))

        # Action buttons
        button_frame = ctk.CTkFrame(content_frame)
        button_frame.pack(fill="x", padx=5, pady=(0, 5))

        if on_edit:
            edit_btn = ctk.CTkButton(
                button_frame,
                text="Edit",
                width=50,
                height=25,
                command=lambda: on_edit(series_config)
            )
            edit_btn.pack(side="left", padx=2)

        if on_remove:
            remove_btn = ctk.CTkButton(
                button_frame,
                text="Remove",
                width=60,
                height=25,
                command=lambda: on_remove(series_config.id),
                fg_color=("gray70", "gray30")
            )
            remove_btn.pack(side="left", padx=2)


class SearchBar(ctk.CTkFrame):
    """Search bar widget"""

    def __init__(self, parent, on_search=None, **kwargs):
        super().__init__(parent, **kwargs)

        self.on_search = on_search
        self.configure(height=35)

        # Search icon
        icon_label = ctk.CTkLabel(self, text="🔍", font=("", 14))
        icon_label.pack(side="left", padx=(10, 5))

        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self,
            textvariable=self.search_var,
            placeholder_text="Search..."
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Bind events
        self.search_var.trace('w', self._on_search)

    def _on_search(self, *args):
        """Handle search input"""
        if self.on_search:
            self.on_search(self.search_var.get())

    def get(self) -> str:
        """Get search text"""
        return self.search_var.get()

    def set(self, text: str):
        """Set search text"""
        self.search_var.set(text)


class CollapsiblePanel(ctk.CTkFrame):
    """Collapsible panel widget"""

    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, **kwargs)

        self.title = title
        self.is_collapsed = False

        # Header button
        self.header_btn = ctk.CTkButton(
            self,
            text=f"▼ {title}",
            command=self.toggle,
            anchor="w",
            fg_color="transparent",
            hover_color=("gray85", "gray25")
        )
        self.header_btn.pack(fill="x")

        # Content frame
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True)

    def toggle(self):
        """Toggle collapsed state"""
        if self.is_collapsed:
            self.expand()
        else:
            self.collapse()

    def collapse(self):
        """Collapse the panel"""
        self.content_frame.pack_forget()
        self.header_btn.configure(text=f"▶ {self.title}")
        self.is_collapsed = True

    def expand(self):
        """Expand the panel"""
        self.content_frame.pack(fill="both", expand=True)
        self.header_btn.configure(text=f"▼ {self.title}")
        self.is_collapsed = False

    def get_content_frame(self):
        """Get the content frame for adding widgets"""
        return self.content_frame


class ToolTip:
    """Tooltip widget for providing help text"""

    def __init__(self, widget, text="", delay=1000):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.show_timer = None

        # Bind events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<ButtonPress>", self._on_leave)

    def _on_enter(self, event=None):
        """Mouse enters widget"""
        self._schedule_show()

    def _on_leave(self, event=None):
        """Mouse leaves widget"""
        self._cancel_show()
        self._hide()

    def _schedule_show(self):
        """Schedule tooltip display"""
        self._cancel_show()
        self.show_timer = self.widget.after(self.delay, self._show)

    def _cancel_show(self):
        """Cancel scheduled display"""
        if self.show_timer:
            self.widget.after_cancel(self.show_timer)
            self.show_timer = None

    def _show(self):
        """Display tooltip"""
        if self.tooltip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        # Create tooltip window
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            background="#333333",
            foreground="white",
            relief="solid",
            borderwidth=1,
            font=("", 9)
        )
        label.pack()

    def _hide(self):
        """Hide tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def set_text(self, text: str):
        """Update tooltip text"""
        self.text = text


class Tooltip:
    """
    Creates hover tooltips for widgets - Legacy Compatible Version
    Shows helpful text when user hovers over a widget
    """

    def __init__(self, widget, text, delay=500):
        """
        Initialize tooltip for a widget

        Args:
            widget: The widget to attach tooltip to
            text (str): Text to display in tooltip
            delay (int): Milliseconds to wait before showing tooltip
        """
        self.widget = widget  # Store reference to parent widget
        self.text = text  # Tooltip text
        self.delay = delay  # Delay before showing
        self.tooltip = None  # Tooltip window (created on demand)
        self.after_id = None  # ID for delayed show operation

        # Bind mouse events to widget
        self.widget.bind("<Enter>", self.on_enter)  # Mouse enters widget
        self.widget.bind("<Leave>", self.on_leave)  # Mouse leaves widget
        self.widget.bind("<ButtonPress>", self.on_leave)  # Click hides tooltip

    def on_enter(self, event=None):
        """
        Handle mouse entering widget - schedule tooltip display

        Args:
            event: Mouse event (unused but required by tkinter)
        """
        # Schedule tooltip to appear after delay
        self.after_id = self.widget.after(self.delay, self.show_tooltip)

    def on_leave(self, event=None):
        """
        Handle mouse leaving widget - cancel/hide tooltip

        Args:
            event: Mouse event (unused but required by tkinter)
        """
        # Cancel scheduled show if tooltip hasn't appeared yet
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None
        # Hide tooltip if it's visible
        self.hide_tooltip()

    def show_tooltip(self):
        """Display the tooltip window"""
        # Don't create duplicate tooltips
        if self.tooltip or not self.text:
            return

        # Get position for tooltip (near widget)
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25  # Position to right of cursor
        y += self.widget.winfo_rooty() + 25  # Position below cursor

        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)  # Remove window decorations

        # Create label with tooltip text
        label = ctk.CTkLabel(
            self.tooltip,
            text=self.text,
            fg_color=("gray20", "gray80"),  # Background color
            corner_radius=6  # Rounded corners
        )
        label.pack()

        # Position tooltip window
        self.tooltip.wm_geometry(f"+{x}+{y}")

    def hide_tooltip(self):
        """Hide and destroy the tooltip window"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class FileCard(ctk.CTkFrame):
    """
    Card widget displaying file information - Legacy Compatible Version
    Shows file details with action buttons
    """

    def __init__(self, master, file_data, on_remove=None, on_view=None, **kwargs):
        """
        Initialize file card

        Args:
            master: Parent widget
            file_data: FileData object to display
            on_remove: Callback function for remove button
            on_view: Callback function for view button
            **kwargs: Additional frame arguments
        """
        super().__init__(master, **kwargs)

        # Store callbacks and data
        self.file_data = file_data
        self.on_remove = on_remove
        self.on_view = on_view

        # Main content container
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=3, pady=3)

        # Header with icon and filename
        self.header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # File icon
        self.icon_label = ctk.CTkLabel(
            self.header_frame,
            text="📄",
            font=("", 24)
        )
        self.icon_label.pack(side="left", padx=(0, 10))

        # File name
        self.name_label = ctk.CTkLabel(
            self.header_frame,
            text=os.path.basename(file_data.filename),
            font=("", 12, "bold"),
            anchor="w"
        )
        self.name_label.pack(side="left", fill="x", expand=True)

        # Statistics frame
        self.stats_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=10, pady=5)

        # Create statistics text
        stats_text = f"Rows: {len(file_data.data):,} | Columns: {len(file_data.data.columns)}"
        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text=stats_text,
            font=("", 10),
            text_color=("gray60", "gray40")
        )
        self.stats_label.pack(side="left")

        # Action buttons frame
        self.action_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=10, pady=(0, 10))

        # View button
        self.view_btn = ctk.CTkButton(
            self.action_frame,
            text="View",
            width=60,
            height=25,
            command=lambda: self.on_view(self.file_data) if self.on_view else None
        )
        self.view_btn.pack(side="left", padx=(0, 5))

        # Remove button
        self.remove_btn = ctk.CTkButton(
            self.action_frame,
            text="Remove",
            width=60,
            height=25,
            fg_color=("#DC2626", "#DC2626"),
            hover_color="#DC2626",
            command=lambda: self.on_remove(self.file_data) if self.on_remove else None
        )
        self.remove_btn.pack(side="left")

        # Add hover effect
        self.bind("<Enter>", lambda e: self.configure(fg_color=("gray85", "gray25")))
        self.bind("<Leave>", lambda e: self.configure(fg_color=("gray90", "gray20")))


class SeriesCard(ctk.CTkFrame):
    """
    Card widget displaying series information - Legacy Compatible Version
    Shows series details with configuration and action buttons
    """

    def __init__(self, master, series, file_data, on_configure=None, on_toggle=None, on_remove=None, **kwargs):
        """
        Initialize series card

        Args:
            master: Parent widget
            series: SeriesConfig object to display
            file_data: Associated FileData object
            on_configure: Callback for configure button
            on_toggle: Callback for visibility toggle
            on_remove: Callback for remove button
            **kwargs: Additional frame arguments
        """
        super().__init__(master, **kwargs)

        # Store data and callbacks
        self.series = series
        self.file_data = file_data
        self.on_configure = on_configure
        self.on_toggle = on_toggle
        self.on_remove = on_remove

        # Main content container
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=3, pady=3)

        # Header with color indicator and name
        self.header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Color indicator circle
        self.color_indicator = ctk.CTkFrame(
            self.header_frame,
            width=20,
            height=20,
            corner_radius=10,  # Makes it circular
            fg_color=series.color
        )
        self.color_indicator.pack(side="left", padx=(0, 10))

        # Series name
        self.name_label = ctk.CTkLabel(
            self.header_frame,
            text=series.name,
            font=("", 12, "bold"),
            anchor="w"
        )
        self.name_label.pack(side="left", fill="x", expand=True)

        # Visibility toggle switch
        self.visible_switch = ctk.CTkSwitch(
            self.header_frame,
            text="",
            width=40,
            height=20,
            command=lambda: self.on_toggle(self.series) if self.on_toggle else None
        )
        self.visible_switch.pack(side="right")

        # Set switch state based on series visibility
        if series.visible:
            self.visible_switch.select()
        else:
            self.visible_switch.deselect()

        # Info frame
        self.info_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=10, pady=5)

        # Create info text
        info_text = f"{series.x_column} vs {series.y_column} | Range: {series.start_index}-{series.end_index}"
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text=info_text,
            font=("", 10),
            text_color=("gray60", "gray40"),
            anchor="w"
        )
        self.info_label.pack(side="left", fill="x", expand=True)

        # Action buttons frame
        self.action_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Configure button
        self.configure_btn = ctk.CTkButton(
            self.action_frame,
            text="Configure",
            width=80,
            height=25,
            command=lambda: self.on_configure(self.series) if self.on_configure else None
        )
        self.configure_btn.pack(side="left", padx=(0, 5))

        # Remove button
        self.remove_btn = ctk.CTkButton(
            self.action_frame,
            text="Remove",
            width=60,
            height=25,
            fg_color=("#DC2626", "#DC2626"),
            hover_color="#DC2626",
            command=lambda: self.on_remove(self.series) if self.on_remove else None
        )
        self.remove_btn.pack(side="left")


class QuickActionBar(ctk.CTkFrame):
    """
    Toolbar with quick action buttons - Legacy Compatible Version
    Organizes buttons into left, center, and right sections
    """

    def __init__(self, master, **kwargs):
        """
        Initialize quick action bar

        Args:
            master: Parent widget
            **kwargs: Additional frame arguments
        """
        # Initialize with fixed height
        super().__init__(master, height=50, **kwargs)
        self.pack_propagate(False)  # Maintain fixed height

        # Left frame for left-aligned actions
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.pack(side="left", fill="y")

        # Right frame for right-aligned actions
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.pack(side="right", fill="y")

        # Center frame for center actions
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.pack(side="left", fill="both", expand=True)

        # List to track all action buttons
        self.actions = []

    def add_action(self, text, icon, command, tooltip="", side="left"):
        """
        Add an action button to the toolbar

        Args:
            text (str): Button text
            icon (str): Icon/emoji to display
            command: Function to call when clicked
            tooltip (str): Tooltip text to show on hover
            side (str): Which section to add to ('left', 'center', 'right')

        Returns:
            ctk.CTkButton: The created button widget
        """
        # Determine parent frame based on side
        if side == "left":
            parent = self.left_frame
        elif side == "right":
            parent = self.right_frame
        else:
            parent = self.center_frame

        # Create button with icon and text
        btn = ctk.CTkButton(
            parent,
            text=f"{icon} {text}",
            width=100,
            height=35,
            command=command
        )
        btn.pack(side="left", padx=5, pady=7)

        # Add tooltip if provided
        if tooltip:
            Tooltip(btn, tooltip)

        # Track button
        self.actions.append(btn)

        return btn

    def add_separator(self, side="left"):
        """
        Add a vertical separator line

        Args:
            side (str): Which section to add to ('left', 'center', 'right')
        """
        # Determine parent frame
        if side == "left":
            parent = self.left_frame
        elif side == "right":
            parent = self.right_frame
        else:
            parent = self.center_frame

        # Create vertical separator
        sep = ctk.CTkFrame(parent, width=2, fg_color=("gray80", "gray30"))
        sep.pack(side="left", fill="y", padx=10, pady=10)


class StatusBar(ctk.CTkFrame):
    """Enhanced status bar with centered progress and better visibility"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=35, **kwargs)

        # Configure grid for centering
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)  
        self.grid_columnconfigure(2, weight=1)

        # Left side - status text
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            anchor="w",
            font=("", 11)
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=5)

        # Center - progress bar (initially hidden)
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.grid_columnconfigure(0, weight=1)  # Progress bar gets most space
        self.progress_frame.grid_columnconfigure(1, weight=0)  # Label is fixed width
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=250)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=5)
        self.progress_bar.set(0)

        # Progress label to the right of the bar
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=("", 10),
            width=80  # Fixed width for consistent layout
        )
        self.progress_label.grid(row=0, column=1, sticky="w", padx=(5, 10), pady=5)

        # Right side - counts
        self.counts_label = ctk.CTkLabel(
            self,
            text="",
            anchor="e",
            font=("", 11)
        )
        self.counts_label.grid(row=0, column=2, sticky="e", padx=5)

        self.is_progress_visible = False

    def set_status(self, text: str, level: str = "info"):
        """Update status text"""
        color_map = {
            "info": ("gray10", "gray90"),
            "success": ("green", "green"),
            "warning": ("orange", "orange"),
            "error": ("red", "red")
        }

        self.status_label.configure(
            text=text,
            text_color=color_map.get(level, color_map["info"])
        )

    def update_counts(self, files: int = 0, series: int = 0):
        """Update file and series counts"""
        self.counts_label.configure(
            text=f"Files: {files} | Series: {series}"
        )

    def show_progress(self, value: float = 0):
        """Show progress bar centered at bottom with optional value (0-1)"""
        if not self.is_progress_visible:
            # Show progress frame in center column
            self.progress_frame.grid(row=0, column=1, sticky="ew", padx=20, pady=2)
            self.is_progress_visible = True

        # Update progress value
        if value > 0:
            self.progress_bar.set(value)
            percentage = int(value * 100)
            self.progress_label.configure(text=f"{percentage}%")
        else:
            self.progress_bar.set(0)
            self.progress_label.configure(text="Loading...")

    def hide_progress(self):
        """Hide progress bar and restore normal status layout"""
        if self.is_progress_visible:
            self.progress_frame.grid_forget()
            self.is_progress_visible = False

            # Reset progress
            self.progress_bar.set(0)
            self.progress_label.configure(text="")
            self.progress_label.configure(text="")

class CollapsibleFrame(ctk.CTkFrame):
    """Collapsible frame widget - Compatibility alias"""

    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, **kwargs)

        self.title = title
        self.is_collapsed = False

        # Header
        self.header = ctk.CTkButton(
            self,
            text=f"▼ {title}",
            command=self.toggle,
            anchor="w"
        )
        self.header.pack(fill="x")

        # Content frame
        self.content = ctk.CTkFrame(self)
        self.content.pack(fill="both", expand=True)

    def toggle(self):
        """Toggle collapsed state"""
        if self.is_collapsed:
            self.content.pack(fill="both", expand=True)
            self.header.configure(text=f"▼ {self.title}")
            self.is_collapsed = False
        else:
            self.content.pack_forget()
            self.header.configure(text=f"▶ {self.title}")
            self.is_collapsed = True
