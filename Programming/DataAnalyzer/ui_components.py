#!/usr/bin/env python3
"""
ui_components.py - Reusable UI components for the Excel Data Plotter
Contains generic UI widgets that can be used throughout the application
"""

import tkinter as tk  # Standard Python GUI library
from tkinter import ttk  # Themed widgets for tkinter
import customtkinter as ctk  # Modern-looking tkinter widgets
from constants import ColorPalette, Style, AppConfig  # Import constants
import os  # For file operations


class Tooltip:
    """
    Creates hover tooltips for widgets
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


class StatusBar(ctk.CTkFrame):
    """
    Status bar widget showing application state and progress
    Displays at bottom of window with status text and optional progress bar
    """

    def __init__(self, master, **kwargs):
        """
        Initialize status bar

        Args:
            master: Parent widget
            **kwargs: Additional frame arguments
        """
        # Initialize frame with fixed height
        super().__init__(master, height=30, **kwargs)
        self.grid_propagate(False)  # Maintain fixed height

        # Status text label (left side)
        self.status_label = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status_label.grid(row=0, column=0, padx=10, sticky="w")

        # Progress bar (center, hidden by default)
        self.progress = ctk.CTkProgressBar(self, width=200)
        self.progress.grid(row=0, column=1, padx=10)
        self.progress.set(0)  # Initialize at 0%
        self.progress.grid_remove()  # Hide initially

        # Info frame (right side)
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=2, padx=10, sticky="e")

        # File count label
        self.files_label = ctk.CTkLabel(self.info_frame, text="Files: 0")
        self.files_label.pack(side="left", padx=5)

        # Series count label
        self.series_label = ctk.CTkLabel(self.info_frame, text="Series: 0")
        self.series_label.pack(side="left", padx=5)

        # Make status label column expandable
        self.grid_columnconfigure(0, weight=1)

    def set_status(self, text, status_type="info"):
        """
        Update status text with color coding

        Args:
            text (str): Status message to display
            status_type (str): Type of status ('info', 'success', 'warning', 'error')
        """
        # Define colors for different status types
        colors = {
            "info": ("gray40", "gray60"),
            "success": ColorPalette.SUCCESS,
            "warning": ColorPalette.WARNING,
            "error": ColorPalette.ERROR
        }

        # Get color for status type
        color = colors.get(status_type, ("gray40", "gray60"))

        # Update label text and color
        self.status_label.configure(text=text, text_color=color)

    def show_progress(self, value=None):
        """
        Show or update progress bar

        Args:
            value (float, optional): Progress value (0.0 to 1.0)
        """
        # Make progress bar visible
        self.progress.grid()

        # Update value if provided
        if value is not None:
            self.progress.set(value)

    def hide_progress(self):
        """Hide progress bar and reset to 0"""
        self.progress.grid_remove()  # Hide widget
        self.progress.set(0)  # Reset value

    def update_counts(self, files=None, series=None):
        """
        Update file and series count displays

        Args:
            files (int, optional): Number of loaded files
            series (int, optional): Number of defined series
        """
        # Update file count if provided
        if files is not None:
            self.files_label.configure(text=f"Files: {files}")

        # Update series count if provided
        if series is not None:
            self.series_label.configure(text=f"Series: {series}")


class CollapsiblePanel(ctk.CTkFrame):
    """
    A panel that can be collapsed/expanded by clicking header
    Useful for organizing UI into sections that can be hidden
    """

    def __init__(self, master, title="", start_collapsed=False, **kwargs):
        """
        Initialize collapsible panel

        Args:
            master: Parent widget
            title (str): Panel title text
            start_collapsed (bool): Whether to start in collapsed state
            **kwargs: Additional frame arguments
        """
        super().__init__(master, **kwargs)

        # State tracking
        self.collapsed = start_collapsed

        # Create header frame
        self.header = ctk.CTkFrame(self, height=40)
        self.header.pack(fill="x", padx=2, pady=2)
        self.header.pack_propagate(False)  # Maintain fixed height

        # Collapse/expand button
        self.toggle_btn = ctk.CTkButton(
            self.header,
            text="▼" if not self.collapsed else "▶",  # Arrow indicates state
            width=30,
            height=30,
            command=self.toggle,
            fg_color="transparent",
            hover_color=("gray80", "gray30")
        )
        self.toggle_btn.pack(side="left", padx=5)

        # Title label
        self.title_label = ctk.CTkLabel(
            self.header,
            text=title,
            font=("", 14, "bold")
        )
        self.title_label.pack(side="left", padx=5)

        # Content frame (collapsible part)
        self.content_frame = ctk.CTkFrame(self)

        # Show/hide content based on initial state
        if not self.collapsed:
            self.content_frame.pack(fill="both", expand=True, padx=2, pady=(0, 2))

    def toggle(self):
        """Toggle between collapsed and expanded states"""
        # Flip state
        self.collapsed = not self.collapsed

        # Update button arrow
        self.toggle_btn.configure(text="▼" if not self.collapsed else "▶")

        # Show or hide content
        if self.collapsed:
            self.content_frame.pack_forget()  # Hide content
        else:
            self.content_frame.pack(fill="both", expand=True, padx=2, pady=(0, 2))  # Show content

    def get_content_frame(self):
        """
        Get the content frame for adding widgets

        Returns:
            ctk.CTkFrame: Frame to add content to
        """
        return self.content_frame


class FileCard(ctk.CTkFrame):
    """
    Card widget displaying file information
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
        stats_text = f"Rows: {len(file_data.df):,} | Columns: {len(file_data.df.columns)}"
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
            fg_color=ColorPalette.ERROR,
            hover_color="#DC2626",
            command=lambda: self.on_remove(self.file_data) if self.on_remove else None
        )
        self.remove_btn.pack(side="left")

        # Add hover effect
        self.bind("<Enter>", lambda e: self.configure(fg_color=("gray85", "gray25")))
        self.bind("<Leave>", lambda e: self.configure(fg_color=("gray90", "gray20")))


class SeriesCard(ctk.CTkFrame):
    """
    Card widget displaying series information
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
            fg_color=ColorPalette.ERROR,
            hover_color="#DC2626",
            command=lambda: self.on_remove(self.series) if self.on_remove else None
        )
        self.remove_btn.pack(side="left")


class SearchBar(ctk.CTkFrame):
    """
    Search bar widget with live search capability
    Includes search input field and search button
    """

    def __init__(self, master, on_search=None, **kwargs):
        """
        Initialize search bar

        Args:
            master: Parent widget
            on_search: Callback function when search is performed
            **kwargs: Additional frame arguments
        """
        super().__init__(master, **kwargs)

        # Store callback
        self.on_search = on_search

        # Search icon
        self.icon_label = ctk.CTkLabel(self, text="🔍", font=("", 16))
        self.icon_label.pack(side="left", padx=(10, 5))

        # Search entry field
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Search...",
            width=300,
            height=35
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Bind Enter key to perform search
        self.search_entry.bind("<Return>", lambda e: self.perform_search())

        # Bind key release for live search
        self.search_entry.bind("<KeyRelease>", self.on_type)

        # Search button
        self.search_btn = ctk.CTkButton(
            self,
            text="Search",
            width=80,
            height=35,
            command=self.perform_search
        )
        self.search_btn.pack(side="left", padx=(5, 10))

        # Timer for debouncing live search
        self.search_timer = None

    def on_type(self, event):
        """
        Handle typing with debounce for live search
        Waits for user to stop typing before searching

        Args:
            event: Key event from tkinter
        """
        # Cancel previous timer if exists
        if self.search_timer:
            self.after_cancel(self.search_timer)

        # Start new timer (300ms delay)
        self.search_timer = self.after(300, self.perform_search)

    def perform_search(self):
        """Execute search callback with current search text"""
        if self.on_search:
            # Get search text and call callback
            self.on_search(self.search_entry.get())


class QuickActionBar(ctk.CTkFrame):
    """
    Toolbar with quick action buttons
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


class FloatingPanel(ctk.CTkToplevel):
    """
    A floating window panel that can be moved around
    Used for tool windows and dialogs
    """

    def __init__(self, master, title="", width=400, height=300, **kwargs):
        """
        Initialize floating panel

        Args:
            master: Parent window
            title (str): Panel title
            width (int): Panel width in pixels
            height (int): Panel height in pixels
            **kwargs: Additional toplevel arguments
        """
        super().__init__(master, **kwargs)

        # Configure window
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(300, 200)  # Minimum size

        # Make it float above main window
        self.transient(master)  # Associate with parent
        self.lift()  # Bring to front

        # Header frame for title and controls
        self.header = ctk.CTkFrame(self, height=30)
        self.header.pack(fill="x")

        # Title label
        self.title_label = ctk.CTkLabel(
            self.header,
            text=title,
            font=("", 12, "bold")
        )
        self.title_label.pack(side="left", padx=10)

        # Close button
        self.close_btn = ctk.CTkButton(
            self.header,
            text="✕",
            width=30,
            height=25,
            command=self.withdraw,  # Hide window
            fg_color="transparent",
            hover_color=ColorPalette.ERROR
        )
        self.close_btn.pack(side="right", padx=5)

        # Content frame for panel content
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Enable window dragging by header
        self.header.bind("<Button-1>", self.start_drag)
        self.header.bind("<B1-Motion>", self.drag)
        self.title_label.bind("<Button-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.drag)

        # Variables for drag tracking
        self.x = 0
        self.y = 0

    def start_drag(self, event):
        """
        Start dragging operation

        Args:
            event: Mouse event with coordinates
        """
        # Store initial mouse position
        self.x = event.x
        self.y = event.y

    def drag(self, event):
        """
        Handle dragging motion

        Args:
            event: Mouse event with current coordinates
        """
        # Calculate movement delta
        deltax = event.x - self.x
        deltay = event.y - self.y

        # Calculate new window position
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay

        # Move window
        self.geometry(f"+{x}+{y}")