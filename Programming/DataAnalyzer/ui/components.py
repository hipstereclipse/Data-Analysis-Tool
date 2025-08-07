#!/usr/bin/env python3
"""
Reusable UI components
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path

from config.constants import UIConfig


class StatusBar(ctk.CTkFrame):
    """Application status bar"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=30, **kwargs)
        self.grid_propagate(False)

        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, padx=10, sticky="w")

        # Progress bar
        self.progress = ctk.CTkProgressBar(self, width=200)
        self.progress.grid(row=0, column=1, padx=10)
        self.progress.set(0)
        self.progress.grid_remove()

        # Info labels
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=2, padx=10, sticky="e")

        self.file_count_label = ctk.CTkLabel(
            self.info_frame,
            text="Files: 0"
        )
        self.file_count_label.pack(side="left", padx=5)

        self.series_count_label = ctk.CTkLabel(
            self.info_frame,
            text="Series: 0"
        )
        self.series_count_label.pack(side="left", padx=5)

        # Configure grid weights
        self.grid_columnconfigure(0, weight=1)

    def set_status(self, text: str, status_type: str = "info"):
        """Update status text"""
        colors = {
            "info": UIConfig.INFO,
            "success": UIConfig.SUCCESS,
            "warning": UIConfig.WARNING,
            "error": UIConfig.ERROR
        }

        color = colors.get(status_type, UIConfig.INFO)
        self.status_label.configure(text=text, text_color=color)

    def show_progress(self, value: Optional[float] = None):
        """Show/update progress bar"""
        self.progress.grid()
        if value is not None:
            self.progress.set(value)

    def hide_progress(self):
        """Hide progress bar"""
        self.progress.grid_remove()
        self.progress.set(0)

    def update_counts(self, files: Optional[int] = None, series: Optional[int] = None):
        """Update file and series counts"""
        if files is not None:
            self.file_count_label.configure(text=f"Files: {files}")
        if series is not None:
            self.series_count_label.configure(text=f"Series: {series}")


class QuickActionBar(ctk.CTkFrame):
    """Quick action toolbar"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.buttons: List[ctk.CTkButton] = []
        self.current_column = 0

    def add_action(
            self,
            icon: str,
            command: Callable,
            tooltip: str = "",
            width: int = 40
    ):
        """Add action button"""
        btn = ctk.CTkButton(
            self,
            text=icon,
            command=command,
            width=width,
            height=32
        )
        btn.grid(row=0, column=self.current_column, padx=2, pady=2)

        if tooltip:
            self._add_tooltip(btn, tooltip)

        self.buttons.append(btn)
        self.current_column += 1

        return btn

    def add_separator(self):
        """Add visual separator"""
        sep = ttk.Separator(self, orient="vertical")
        sep.grid(row=0, column=self.current_column, sticky="ns", padx=5)
        self.current_column += 1

    def _add_tooltip(self, widget, text: str):
        """Add tooltip to widget"""
        ToolTip(widget, text)


class ToolTip:
    """Tooltip for widgets"""

    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tooltip = None

        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)

    def _on_enter(self, event=None):
        """Show tooltip"""
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background="#333333",
            foreground="white",
            relief="solid",
            borderwidth=1,
            font=("Arial", 10)
        )
        label.pack()

        self.tooltip.wm_geometry(f"+{x}+{y}")

    def _on_leave(self, event=None):
        """Hide tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


class CollapsibleFrame(ctk.CTkFrame):
    """Collapsible frame container"""

    def __init__(
            self,
            parent,
            title: str = "",
            collapsed: bool = False,
            **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.collapsed = collapsed

        # Header
        self.header = ctk.CTkFrame(self)
        self.header.pack(fill="x", padx=2, pady=2)

        # Toggle button
        self.toggle_btn = ctk.CTkButton(
            self.header,
            text="▼" if not collapsed else "▶",
            width=30,
            height=25,
            command=self.toggle
        )
        self.toggle_btn.pack(side="left", padx=5)

        # Title
        self.title_label = ctk.CTkLabel(
            self.header,
            text=title,
            font=("", 12, "bold")
        )
        self.title_label.pack(side="left", padx=5)

        # Content frame
        self.content = ctk.CTkFrame(self)
        if not collapsed:
            self.content.pack(fill="both", expand=True, padx=2, pady=2)

    def toggle(self):
        """Toggle collapsed state"""
        self.collapsed = not self.collapsed

        if self.collapsed:
            self.content.pack_forget()
            self.toggle_btn.configure(text="▶")
        else:
            self.content.pack(fill="both", expand=True, padx=2, pady=2)
            self.toggle_btn.configure(text="▼")

    def get_content_frame(self):
        """Get content frame for adding widgets"""
        return self.content


class DataCard(ctk.CTkFrame):
    """Card widget for displaying data items"""

    def __init__(
            self,
            parent,
            title: str,
            subtitle: str = "",
            icon: str = "📄",
            on_click: Optional[Callable] = None,
            on_remove: Optional[Callable] = None,
            **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.on_click = on_click
        self.on_remove = on_remove

        # Configure appearance
        self.configure(corner_radius=8)

        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=10)

        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")

        # Icon
        icon_label = ctk.CTkLabel(
            header,
            text=icon,
            font=("", 20)
        )
        icon_label.pack(side="left", padx=(0, 10))

        # Title
        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=("", 12, "bold"),
            anchor="w"
        )
        title_label.pack(side="left", fill="x", expand=True)

        # Remove button
        if on_remove:
            remove_btn = ctk.CTkButton(
                header,
                text="✕",
                width=25,
                height=25,
                fg_color=UIConfig.ERROR,
                command=on_remove
            )
            remove_btn.pack(side="right")

        # Subtitle
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                content,
                text=subtitle,
                font=("", 10),
                text_color="gray",
                anchor="w"
            )
            subtitle_label.pack(fill="x", pady=(5, 0))

        # Make clickable
        if on_click:
            self.bind("<Button-1>", lambda e: on_click())
            for child in self.winfo_children():
                child.bind("<Button-1>", lambda e: on_click())


class SearchBar(ctk.CTkFrame):
    """Search input with filter options"""

    def __init__(
            self,
            parent,
            on_search: Optional[Callable] = None,
            placeholder: str = "Search...",
            **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.on_search = on_search

        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_text_change)

        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.search_var,
            placeholder_text=placeholder,
            width=300
        )
        self.entry.pack(side="left", padx=5)

        # Clear button
        self.clear_btn = ctk.CTkButton(
            self,
            text="✕",
            width=30,
            command=self.clear
        )
        self.clear_btn.pack(side="left")

    def _on_text_change(self, *args):
        """Handle text change"""
        if self.on_search:
            self.on_search(self.search_var.get())

    def clear(self):
        """Clear search text"""
        self.search_var.set("")

    def get_text(self) -> str:
        """Get current search text"""
        return self.search_var.get()


class TabPanel(ctk.CTkTabview):
    """Enhanced tab panel"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.tabs: Dict[str, ctk.CTkFrame] = {}

    def add_tab(self, name: str, icon: str = "") -> ctk.CTkFrame:
        """Add a new tab"""
        display_name = f"{icon} {name}" if icon else name
        tab = self.add(display_name)
        self.tabs[name] = tab
        return tab

    def get_tab(self, name: str) -> Optional[ctk.CTkFrame]:
        """Get tab by name"""
        return self.tabs.get(name)

    def select_tab(self, name: str):
        """Select a tab by name"""
        if name in self.tabs:
            for tab_name in self._tab_dict:
                if name in tab_name:
                    self.set(tab_name)
                    break