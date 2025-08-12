#!/usr/bin/env python3
"""
UI Factory - Reusable UI component creation utilities
Consolidates common UI patterns and widgets
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional, Callable, List, Dict, Any

from ui.theme_manager import theme_manager


class UIFactory:
    """Factory class for creating standardized UI components"""
    
    @staticmethod
    def create_labeled_frame(parent, title: str, **kwargs) -> ctk.CTkFrame:
        """Create a frame with a title label"""
        container = ctk.CTkFrame(parent, **kwargs)
        
        title_label = ctk.CTkLabel(
            container,
            text=title,
            font=theme_manager.get_font("subheading")
        )
        title_label.pack(anchor="w", pady=(5, 10), padx=10)
        
        return container
    
    @staticmethod
    def create_scrollable_text(parent, **kwargs) -> tk.Text:
        """Create a scrollable text widget with theme-appropriate styling"""
        text_widget = tk.Text(
            parent,
            wrap="word",
            font=theme_manager.get_font("monospace"),
            bg=theme_manager.get_color("bg_secondary"),
            fg=theme_manager.get_color("fg_primary"),
            insertbackground=theme_manager.get_color("fg_primary"),
            **kwargs
        )
        
        scrollbar = ttk.Scrollbar(parent, command=text_widget.yview)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return text_widget
    
    @staticmethod
    def create_matplotlib_canvas(parent, figure: Figure) -> FigureCanvasTkAgg:
        """Create a matplotlib canvas with navigation toolbar"""
        canvas = FigureCanvasTkAgg(figure, parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Apply theme to figure
        theme_manager.configure_matplotlib_figure(figure)
        
        return canvas
    
    @staticmethod
    def create_button_panel(parent, buttons: List[Dict[str, Any]]) -> ctk.CTkFrame:
        """Create a horizontal button panel
        
        Args:
            parent: Parent widget
            buttons: List of button configs with keys: text, command, width (optional)
        """
        button_frame = ctk.CTkFrame(parent)
        
        for button_config in buttons:
            btn = ctk.CTkButton(
                button_frame,
                text=button_config["text"],
                command=button_config["command"],
                width=button_config.get("width", 100)
            )
            btn.pack(side="right", padx=5)
            
        return button_frame
    
    @staticmethod
    def create_option_checkboxes(parent, options: List[tuple], 
                                variables: Dict[str, tk.BooleanVar]) -> ctk.CTkFrame:
        """Create a set of option checkboxes
        
        Args:
            parent: Parent widget
            options: List of (key, display_text) tuples
            variables: Dict to store BooleanVar references
        """
        options_frame = ctk.CTkFrame(parent)
        
        for option_key, option_text in options:
            var = tk.BooleanVar(value=True)
            variables[option_key] = var
            
            checkbox = ctk.CTkCheckBox(
                options_frame,
                text=option_text,
                variable=var
            )
            checkbox.pack(anchor="w", pady=2)
            
        return options_frame
    
    @staticmethod
    def create_parameter_grid(parent, parameters: List[Dict[str, Any]]) -> ctk.CTkFrame:
        """Create a grid of parameter inputs
        
        Args:
            parent: Parent widget
            parameters: List of parameter configs with keys: label, variable, width (optional)
        """
        param_frame = ctk.CTkFrame(parent)
        param_frame.grid_columnconfigure(1, weight=1)
        
        for i, param_config in enumerate(parameters):
            label = ctk.CTkLabel(param_frame, text=param_config["label"])
            label.grid(row=i, column=0, sticky="w", padx=5, pady=2)
            
            entry = ctk.CTkEntry(
                param_frame,
                textvariable=param_config["variable"],
                width=param_config.get("width", 100)
            )
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            
        return param_frame
    
    @staticmethod
    def center_window(window, width: int = None, height: int = None):
        """Center a window on the screen"""
        window.update_idletasks()
        
        if width is None:
            width = window.winfo_width()
        if height is None:
            height = window.winfo_height()
            
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        window.geometry(f"{width}x{height}+{x}+{y}")


class DualRangeSlider(ctk.CTkFrame):
    """Reusable dual-handle range slider component"""
    
    def __init__(self, parent, from_=0, to=100, start_var=None, end_var=None, 
                 start_command=None, end_command=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.from_ = from_
        self.to = to
        self.start_var = start_var or tk.IntVar()
        self.end_var = end_var or tk.IntVar()
        self.start_command = start_command
        self.end_command = end_command
        
        # Track which handle is being dragged
        self.dragging = None
        
        # Configure layout
        self.grid_columnconfigure(0, weight=1)
        
        # Create header with labels
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        self.start_label = ctk.CTkLabel(header_frame, text=f"Start: {self.start_var.get()}")
        self.start_label.grid(row=0, column=0, sticky="w", padx=5)
        
        self.end_label = ctk.CTkLabel(header_frame, text=f"End: {self.end_var.get()}")
        self.end_label.grid(row=0, column=2, sticky="e", padx=5)
        
        # Create canvas for slider with theme colors - use the global theme_manager import
        canvas_bg = theme_manager.get_color("bg_secondary")
        self.canvas = ctk.CTkCanvas(self, height=40, highlightthickness=0, bg=canvas_bg)
        self.canvas.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Bind events
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Initialize display
        self.after(10, self._draw_slider)
        
        # Bind variable changes to update display
        self.start_var.trace("w", self._on_var_change)
        self.end_var.trace("w", self._on_var_change)
        
    def _on_canvas_configure(self, event):
        """Handle canvas resize"""
        self._draw_slider()
        
    def _draw_slider(self):
        """Draw the slider track and handles"""
        try:
            if not hasattr(self, 'canvas') or not self.canvas.winfo_exists():
                return
                
            self.canvas.delete("all")
            
            # Get canvas dimensions
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            if width <= 1:  # Canvas not ready yet
                self.after(10, self._draw_slider)
                return
        except Exception:
            # Canvas might be destroyed, skip drawing
            return
            
        # Calculate positions
        margin = 20
        track_y = height // 2
        track_start = margin
        track_end = width - margin
        track_width = track_end - track_start
        
        # Calculate handle positions
        start_ratio = (self.start_var.get() - self.from_) / (self.to - self.from_)
        end_ratio = (self.end_var.get() - self.from_) / (self.to - self.from_)
        
        start_x = track_start + start_ratio * track_width
        end_x = track_start + end_ratio * track_width
        
        # Get theme-appropriate colors - use the global theme_manager import
        track_color = theme_manager.get_color("bg_tertiary")
        range_color = theme_manager.get_color("accent")
        handle_color = theme_manager.get_color("fg_primary")
        
        # Draw track
        self.canvas.create_line(track_start, track_y, track_end, track_y, 
                               width=4, fill=track_color, capstyle="round")
        
        # Draw selected range
        self.canvas.create_line(start_x, track_y, end_x, track_y, 
                               width=6, fill=range_color, capstyle="round")
        
        # Draw handles
        handle_fill = theme_manager.get_color("accent")
        handle_outline = theme_manager.get_color("fg_primary")
        
        # Start handle
        self.start_handle = self.canvas.create_oval(
            start_x - 8, track_y - 8, start_x + 8, track_y + 8,
            fill=handle_fill, outline=handle_outline, width=2, tags="start_handle"
        )
        
        # End handle  
        self.end_handle = self.canvas.create_oval(
            end_x - 8, track_y - 8, end_x + 8, track_y + 8,
            fill=handle_fill, outline=handle_outline, width=2, tags="end_handle"
        )
        
        # Update labels
        self.start_label.configure(text=f"Start: {self.start_var.get()}")
        self.end_label.configure(text=f"End: {self.end_var.get()}")
        
    def _on_click(self, event):
        """Handle mouse click"""
        # Find which handle was clicked
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        
        if "start_handle" in tags:
            self.dragging = "start"
        elif "end_handle" in tags:
            self.dragging = "end"
        else:
            # Click on track - move nearest handle
            start_x = self._get_handle_x("start")
            end_x = self._get_handle_x("end")
            
            if abs(event.x - start_x) < abs(event.x - end_x):
                self.dragging = "start"
                self._update_value_from_position(event.x, "start")
            else:
                self.dragging = "end"
                self._update_value_from_position(event.x, "end")
                
    def _on_drag(self, event):
        """Handle mouse drag"""
        if self.dragging:
            self._update_value_from_position(event.x, self.dragging)
            
    def _on_release(self, event):
        """Handle mouse release"""
        self.dragging = None
        
    def _get_handle_x(self, handle):
        """Get the x position of a handle"""
        width = self.canvas.winfo_width()
        margin = 20
        track_width = width - 2 * margin
        
        if handle == "start":
            ratio = (self.start_var.get() - self.from_) / (self.to - self.from_)
        else:
            ratio = (self.end_var.get() - self.from_) / (self.to - self.from_)
            
        return margin + ratio * track_width
        
    def _update_value_from_position(self, x, handle):
        """Update value based on mouse position"""
        width = self.canvas.winfo_width()
        margin = 20
        track_width = width - 2 * margin
        
        # Calculate ratio from position
        ratio = max(0, min(1, (x - margin) / track_width))
        value = int(self.from_ + ratio * (self.to - self.from_))
        
        if handle == "start":
            # Ensure start < end
            if value >= self.end_var.get():
                value = self.end_var.get() - 1
            self.start_var.set(max(self.from_, value))
            if self.start_command:
                self.start_command(value)
        else:
            # Ensure end > start
            if value <= self.start_var.get():
                value = self.start_var.get() + 1
            self.end_var.set(min(self.to, value))
            if self.end_command:
                self.end_command(value)
                
        self._draw_slider()
        
    def _on_var_change(self, *args):
        """Handle variable changes from external sources"""
        try:
            self._draw_slider()
        except Exception:
            # Widget might be destroyed, ignore
            pass
        
    def configure_range(self, from_=None, to=None):
        """Configure the range of the slider"""
        if from_ is not None:
            self.from_ = from_
        if to is not None:
            self.to = to
        
        # Ensure current values are within new range
        current_start = self.start_var.get()
        current_end = self.end_var.get()
        
        self.start_var.set(max(self.from_, min(self.to, current_start)))
        self.end_var.set(max(self.from_, min(self.to, current_end)))
        
        # Redraw the slider
        self._draw_slider()
    
    def refresh_theme(self):
        """Refresh the slider appearance for theme changes"""
        try:
            # Update canvas background - use the global theme_manager import
            canvas_bg = theme_manager.get_color("bg_secondary")
            
            if self.canvas.winfo_exists():
                self.canvas.configure(bg=canvas_bg)
                # Redraw with new colors
                self._draw_slider()
        except Exception as e:
            # Ignore errors if widget no longer exists
            pass
