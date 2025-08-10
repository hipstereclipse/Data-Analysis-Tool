# Enhanced Series Configuration Dialog
# Professional Excel Data Plotter - Vacuum Analysis Edition

import logging
import warnings
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
from typing import Optional, Callable, List, Dict, Any

from models.data_models import FileData, SeriesConfig

logger = logging.getLogger(__name__)


class DualHandleRangeSlider(ctk.CTkFrame):
    """Custom dual-handle range slider with two handles on a single track for space-efficient range selection"""
    
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
        
        # Create canvas for slider
        self.canvas = ctk.CTkCanvas(self, height=40, highlightthickness=0)
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
        if not self.canvas.winfo_exists():
            return
            
        self.canvas.delete("all")
        
        # Get canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1:  # Canvas not ready yet
            self.after(10, self._draw_slider)
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
        
        # Draw track
        track_color = "#565B5E" if ctk.get_appearance_mode() == "Dark" else "#D0D0D0"
        self.canvas.create_line(track_start, track_y, track_end, track_y, 
                               width=4, fill=track_color, capstyle="round")
        
        # Draw selected range
        range_color = "#1F6AA5" if ctk.get_appearance_mode() == "Dark" else "#3B82F6"
        self.canvas.create_line(start_x, track_y, end_x, track_y, 
                               width=6, fill=range_color, capstyle="round")
        
        # Draw handles
        handle_color = "#FFFFFF" if ctk.get_appearance_mode() == "Dark" else "#000000"
        handle_outline = "#000000" if ctk.get_appearance_mode() == "Dark" else "#FFFFFF"
        
        # Start handle
        self.start_handle = self.canvas.create_oval(
            start_x - 8, track_y - 8, start_x + 8, track_y + 8,
            fill=handle_color, outline=handle_outline, width=2, tags="start_handle"
        )
        
        # End handle  
        self.end_handle = self.canvas.create_oval(
            end_x - 8, track_y - 8, end_x + 8, track_y + 8,
            fill=handle_color, outline=handle_outline, width=2, tags="end_handle"
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
        self._draw_slider()


class EnhancedSeriesDialog:
    """Enhanced series configuration dialog with advanced styling and data handling"""
    
    def __init__(self, parent, file_data: FileData, series_config: Optional[SeriesConfig] = None, 
                 on_series_configured: Optional[Callable] = None):
        self.parent = parent
        self.file_data = file_data
        # ... rest of constructor will be copied from original file
