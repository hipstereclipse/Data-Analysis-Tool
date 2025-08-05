#!/usr/bin/env python3
"""
Modern Professional Multi-File Excel Data Plotter v4.1 - Vacuum Analysis Edition
Enhanced for vacuum pressure data analysis with improved data handling
Required packages: pip install pandas matplotlib openpyxl xlrd seaborn scipy scikit-learn customtkinter pillow
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import customtkinter as ctk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle, Polygon, FancyArrowPatch
from matplotlib.lines import Line2D
import numpy as np
import seaborn as sns
from scipy import stats
from scipy.interpolate import make_interp_spline
from scipy.signal import find_peaks, savgol_filter
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import os
import sys
from datetime import datetime, timedelta
import warnings
import uuid
import copy
import json
from PIL import Image, ImageTk
import threading
import queue
warnings.filterwarnings('ignore')

# Configure CustomTkinter
ctk.set_appearance_mode("system")  # Modes: "system", "dark", "light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

# Set matplotlib and seaborn styles
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

print("Starting Professional Multi-File Excel Plotter with Vacuum Analysis Tools...")

class ColorPalette:
    # Light mode colors
    LIGHT_BG = "#F5F7FA"
    LIGHT_SURFACE = "#FFFFFF"
    LIGHT_SURFACE_2 = "#F8F9FA"
    LIGHT_BORDER = "#E1E4E8"
    LIGHT_TEXT = "#2D3748"
    LIGHT_TEXT_SECONDARY = "#718096"
    
    # Dark mode colors
    DARK_BG = "#1A202C"
    DARK_SURFACE = "#2D3748"
    DARK_SURFACE_2 = "#374151"
    DARK_BORDER = "#4A5568"
    DARK_TEXT = "#F7FAFC"
    DARK_TEXT_SECONDARY = "#CBD5E0"
    
    # Accent colors
    PRIMARY = "#3B82F6"
    PRIMARY_HOVER = "#2563EB"
    SECONDARY = "#9C27B0"
    SECONDARY_HOVER = "#7B1FA2"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"
    
    # Chart colors
    CHART_COLORS = [
        "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
        "#EC4899", "#14B8A6", "#F97316", "#6366F1", "#84CC16"
    ]

class ModernStyle:
    """Modern color schemes and styling constants"""
    
    # Modern color palette
    COLORS = {
        # Primary colors
        'primary': '#3B82F6',
        'primary_hover': '#2563EB',
        'primary_dark': '#1D4ED8',
        
        # Status colors
        'success': '#10B981',
        'warning': '#F59E0B',
        'error': '#EF4444',
        'info': '#3B82F6',
        
        # Neutral colors
        'bg_light': '#F9FAFB',
        'bg_dark': '#1F2937',
        'surface_light': '#FFFFFF',
        'surface_dark': '#374151',
        'border_light': '#E5E7EB',
        'border_dark': '#4B5563',
        'text_light': '#111827',
        'text_dark': '#F9FAFB',
        'text_secondary_light': '#6B7280',
        'text_secondary_dark': '#9CA3AF',
    }
    
    # Chart colors
    CHART_COLORS = [
        '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
        '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16'
    ]
    
    @staticmethod
    def get_color(name, dark_mode=False):
        """Get color based on current theme"""
        if dark_mode:
            return ModernStyle.COLORS.get(f'{name}_dark', ModernStyle.COLORS.get(name, '#FFFFFF'))
        return ModernStyle.COLORS.get(f'{name}_light', ModernStyle.COLORS.get(name, '#000000'))

class ModernTooltip:
    """Modern tooltip implementation"""
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip = None
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.widget.bind("<ButtonPress>", self.on_leave)
        self.after_id = None
        
    def on_enter(self, event=None):
        self.after_id = self.widget.after(self.delay, self.show_tooltip)
        
    def on_leave(self, event=None):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
        self.hide_tooltip()
        
    def show_tooltip(self):
        if self.tooltip or not self.text:
            return
            
        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        
        label = ctk.CTkLabel(self.tooltip, text=self.text, 
                            fg_color=("gray20", "gray80"),
                            corner_radius=6)
        label.pack()
        
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class ModernStatusBar(ctk.CTkFrame):
    """Modern status bar with progress indicator"""
    def __init__(self, master, **kwargs):
        super().__init__(master, height=30, **kwargs)
        self.grid_propagate(False)
        
        # Status text
        self.status_label = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status_label.grid(row=0, column=0, padx=10, sticky="w")
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self, width=200)
        self.progress.grid(row=0, column=1, padx=10)
        self.progress.set(0)
        self.progress.grid_remove()
        
        # Info labels
        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=0, column=2, padx=10, sticky="e")
        
        self.files_label = ctk.CTkLabel(self.info_frame, text="Files: 0")
        self.files_label.pack(side="left", padx=5)
        
        self.series_label = ctk.CTkLabel(self.info_frame, text="Series: 0")
        self.series_label.pack(side="left", padx=5)
        
        self.grid_columnconfigure(0, weight=1)
        
    def set_status(self, text, status_type="info"):
        """Update status text with color coding"""
        colors = {
            "info": ("gray40", "gray60"),
            "success": ColorPalette.SUCCESS,
            "warning": ColorPalette.WARNING,
            "error": ColorPalette.ERROR
        }
        
        color = colors.get(status_type, ("gray40", "gray60"))
        self.status_label.configure(text=text, text_color=color)
        
    def show_progress(self, value=None):
        """Show or update progress bar"""
        self.progress.grid()
        if value is not None:
            self.progress.set(value)
            
    def hide_progress(self):
        """Hide progress bar"""
        self.progress.grid_remove()
        self.progress.set(0)
        
    def update_counts(self, files=None, series=None):
        """Update file and series counts"""
        if files is not None:
            self.files_label.configure(text=f"Files: {files}")
        if series is not None:
            self.series_label.configure(text=f"Series: {series}")

class ResponsiveFrame(ctk.CTkFrame):
    """A frame that adapts its layout based on available space"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.bind("<Configure>", self._on_configure)
        self._last_width = 0
        self._last_height = 0
        
    def _on_configure(self, event):
        if event.width != self._last_width or event.height != self._last_height:
            self._last_width = event.width
            self._last_height = event.height
            self.update_layout(event.width, event.height)
    
    def update_layout(self, width, height):
        """Override this method in subclasses to implement responsive behavior"""
        pass

class CollapsiblePanel(ctk.CTkFrame):
    """A collapsible panel with smooth animation"""
    def __init__(self, master, title="", start_collapsed=False, **kwargs):
        super().__init__(master, **kwargs)
        
        self.collapsed = start_collapsed
        self.animation_speed = 10
        self.animation_steps = 15
        
        # Header
        self.header = ctk.CTkFrame(self, height=40)
        self.header.pack(fill="x", padx=2, pady=2)
        self.header.pack_propagate(False)
        
        # Collapse button
        self.toggle_btn = ctk.CTkButton(
            self.header,
            text="▼" if not self.collapsed else "▶",
            width=30,
            height=30,
            command=self.toggle,
            fg_color="transparent",
            hover_color=("gray80", "gray30")
        )
        self.toggle_btn.pack(side="left", padx=5)
        
        # Title
        self.title_label = ctk.CTkLabel(self.header, text=title, font=("", 14, "bold"))
        self.title_label.pack(side="left", padx=5)
        
        # Content frame
        self.content_frame = ctk.CTkFrame(self)
        if not self.collapsed:
            self.content_frame.pack(fill="both", expand=True, padx=2, pady=(0, 2))
            
    def toggle(self):
        """Toggle collapsed state with animation"""
        self.collapsed = not self.collapsed
        self.toggle_btn.configure(text="▼" if not self.collapsed else "▶")
        
        if self.collapsed:
            self.content_frame.pack_forget()
        else:
            self.content_frame.pack(fill="both", expand=True, padx=2, pady=(0, 2))
            
    def get_content_frame(self):
        """Get the frame for adding content"""
        return self.content_frame

class ModernTabbedPanel(ctk.CTkTabview):
    """Modern tabbed panel with enhanced styling"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._segmented_button.configure(font=("", 12))

class FloatingPanel(ctk.CTkToplevel):
    """A floating panel that can be docked or undocked"""
    def __init__(self, master, title="", width=400, height=300, **kwargs):
        super().__init__(master, **kwargs)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(300, 200)
        
        # Make it float above main window
        self.transient(master)
        self.lift()
        
        # Header for dragging
        self.header = ctk.CTkFrame(self, height=30)
        self.header.pack(fill="x")
        
        self.title_label = ctk.CTkLabel(self.header, text=title, font=("", 12, "bold"))
        self.title_label.pack(side="left", padx=10)
        
        # Close button
        self.close_btn = ctk.CTkButton(
            self.header,
            text="✕",
            width=30,
            height=25,
            command=self.withdraw,
            fg_color="transparent",
            hover_color=ColorPalette.ERROR
        )
        self.close_btn.pack(side="right", padx=5)
        
        # Content frame
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Enable dragging
        self.header.bind("<Button-1>", self.start_drag)
        self.header.bind("<B1-Motion>", self.drag)
        self.title_label.bind("<Button-1>", self.start_drag)
        self.title_label.bind("<B1-Motion>", self.drag)
        
    def start_drag(self, event):
        self.x = event.x
        self.y = event.y
        
    def drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry(f"+{x}+{y}")

class ModernFileCard(ctk.CTkFrame):
    """Modern card widget for file display"""
    def __init__(self, master, file_data, on_remove=None, on_view=None, **kwargs):
        super().__init__(master, **kwargs)
        self.file_data = file_data
        self.on_remove = on_remove
        self.on_view = on_view
        
        # Main content
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=3, pady=3)
        
        # File icon and name
        self.header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.icon_label = ctk.CTkLabel(self.header_frame, text="📄", font=("", 24))
        self.icon_label.pack(side="left", padx=(0, 10))
        
        self.name_label = ctk.CTkLabel(
            self.header_frame,
            text=os.path.basename(file_data.filename),
            font=("", 12, "bold"),
            anchor="w"
        )
        self.name_label.pack(side="left", fill="x", expand=True)
        
        # Stats
        self.stats_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=10, pady=5)
        
        stats_text = f"Rows: {len(file_data.df):,} | Columns: {len(file_data.df.columns)}"
        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text=stats_text,
            font=("", 10),
            text_color=("gray60", "gray40")
        )
        self.stats_label.pack(side="left")
        
        # Actions
        self.action_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.view_btn = ctk.CTkButton(
            self.action_frame,
            text="View",
            width=60,
            height=25,
            command=lambda: self.on_view(self.file_data) if self.on_view else None
        )
        self.view_btn.pack(side="left", padx=(0, 5))
        
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
        
        # Hover effect
        self.bind("<Enter>", lambda e: self.configure(fg_color=("gray85", "gray25")))
        self.bind("<Leave>", lambda e: self.configure(fg_color=("gray90", "gray20")))

class ModernSeriesCard(ctk.CTkFrame):
    """Modern card widget for series display"""
    def __init__(self, master, series, file_data, on_configure=None, on_toggle=None, on_remove=None, **kwargs):
        super().__init__(master, **kwargs)
        self.series = series
        self.file_data = file_data
        self.on_configure = on_configure
        self.on_toggle = on_toggle
        self.on_remove = on_remove
        
        # Main content
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.pack(fill="both", expand=True, padx=3, pady=3)
        
        # Header with color indicator
        self.header_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # Color indicator
        self.color_indicator = ctk.CTkFrame(
            self.header_frame,
            width=20,
            height=20,
            corner_radius=10,
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
        
        # Visibility toggle
        self.visible_switch = ctk.CTkSwitch(
            self.header_frame,
            text="",
            width=40,
            height=20,
            command=lambda: self.on_toggle(self.series) if self.on_toggle else None
        )
        self.visible_switch.pack(side="right")
        self.visible_switch.select() if series.visible else self.visible_switch.deselect()
        
        # Info
        self.info_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.info_frame.pack(fill="x", padx=10, pady=5)
        
        info_text = f"{series.x_column} vs {series.y_column} | Range: {series.start_index}-{series.end_index}"
        self.info_label = ctk.CTkLabel(
            self.info_frame,
            text=info_text,
            font=("", 10),
            text_color=("gray60", "gray40"),
            anchor="w"
        )
        self.info_label.pack(side="left", fill="x", expand=True)
        
        # Actions
        self.action_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.action_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.configure_btn = ctk.CTkButton(
            self.action_frame,
            text="Configure",
            width=80,
            height=25,
            command=lambda: self.on_configure(self.series) if self.on_configure else None
        )
        self.configure_btn.pack(side="left", padx=(0, 5))
        
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

class QuickActionBar(ctk.CTkFrame):
    """Quick action toolbar with common functions"""
    def __init__(self, master, **kwargs):
        super().__init__(master, height=50, **kwargs)
        self.pack_propagate(False)
        
        # Left frame for file operations
        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.pack(side="left", fill="y")
        
        # Right frame for plot operations
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.pack(side="right", fill="y")
        
        # Center frame for other actions
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.center_frame.pack(side="left", fill="both", expand=True)
        
        self.actions = []
        
    def add_action(self, text, icon, command, tooltip="", side="left"):
        """Add an action button to specified side"""
        if side == "left":
            parent = self.left_frame
        elif side == "right":
            parent = self.right_frame
        else:
            parent = self.center_frame
            
        btn = ctk.CTkButton(
            parent,
            text=f"{icon} {text}",
            width=100,
            height=35,
            command=command
        )
        btn.pack(side="left", padx=5, pady=7)
        
        if tooltip:
            ModernTooltip(btn, tooltip)
            
        self.actions.append(btn)
        return btn
        
    def add_separator(self, side="left"):
        """Add a vertical separator"""
        if side == "left":
            parent = self.left_frame
        elif side == "right":
            parent = self.right_frame
        else:
            parent = self.center_frame
            
        sep = ctk.CTkFrame(parent, width=2, fg_color=("gray80", "gray30"))
        sep.pack(side="left", fill="y", padx=10, pady=10)

class ModernSearchBar(ctk.CTkFrame):
    """Modern search bar with filters"""
    def __init__(self, master, on_search=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_search = on_search
        
        # Search icon
        self.icon_label = ctk.CTkLabel(self, text="🔍", font=("", 16))
        self.icon_label.pack(side="left", padx=(10, 5))
        
        # Search entry
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Search...",
            width=300,
            height=35
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.perform_search())
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
        
        self.search_timer = None
        
    def on_type(self, event):
        """Handle typing with debounce"""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self.perform_search)
        
    def perform_search(self):
        """Execute search"""
        if self.on_search:
            self.on_search(self.search_entry.get())

class ModernAnnotationManager:
    """Enhanced annotation manager with editing capabilities"""
    def __init__(self):
        self.annotations = {}
        self.annotation_id_counter = 0
        self.selected_annotation = None
        
    def add_annotation(self, ann_type, **kwargs):
        """Add annotation with unique ID"""
        self.annotation_id_counter += 1
        ann_id = f"ann_{self.annotation_id_counter}"
        
        annotation = {
            'id': ann_id,
            'type': ann_type,
            'visible': True,
            'editable': True,
            **kwargs
        }
        
        self.annotations[ann_id] = annotation
        return ann_id
    
    def update_annotation(self, ann_id, **kwargs):
        """Update existing annotation"""
        if ann_id in self.annotations:
            self.annotations[ann_id].update(kwargs)
    
    def remove_annotation(self, ann_id):
        """Remove annotation by ID"""
        if ann_id in self.annotations:
            del self.annotations[ann_id]
            if self.selected_annotation == ann_id:
                self.selected_annotation = None
    
    def draw_annotations(self, ax, picker=True):
        """Draw all visible annotations with picker support"""
        artists = {}
        
        for ann_id, ann in self.annotations.items():
            if not ann.get('visible', True):
                continue
            
            artist = None
            
            if ann['type'] == 'vline':
                artist = ax.axvline(x=ann['x_pos'], 
                                   color=ann.get('color', 'red'),
                                   linestyle=ann.get('style', '--'),
                                   linewidth=ann.get('width', 2),
                                   alpha=ann.get('alpha', 0.8),
                                   label=ann.get('label'),
                                   picker=picker)
                
            elif ann['type'] == 'hline':
                artist = ax.axhline(y=ann['y_pos'],
                                   color=ann.get('color', 'blue'),
                                   linestyle=ann.get('style', '--'),
                                   linewidth=ann.get('width', 2),
                                   alpha=ann.get('alpha', 0.8),
                                   label=ann.get('label'),
                                   picker=picker)
                
            elif ann['type'] == 'region':
                artist = ax.axvspan(ann['x_start'], ann['x_end'],
                                   color=ann.get('color', 'yellow'),
                                   alpha=ann.get('alpha', 0.3),
                                   label=ann.get('label'),
                                   picker=picker)
                
            elif ann['type'] == 'point':
                artist = ax.scatter(ann['x_pos'], ann['y_pos'],
                                   marker=ann.get('marker', 'o'),
                                   s=ann.get('size', 100),
                                   color=ann.get('color', 'red'),
                                   edgecolors='black' if ann_id == self.selected_annotation else 'none',
                                   linewidths=2 if ann_id == self.selected_annotation else 0,
                                   zorder=10,
                                   label=ann.get('label'),
                                   picker=picker)
                
            elif ann['type'] == 'text':
                bbox_props = ann.get('bbox')
                if ann_id == self.selected_annotation and bbox_props:
                    bbox_props = dict(bbox_props)
                    bbox_props['edgecolor'] = 'blue'
                    bbox_props['linewidth'] = 2
                
                artist = ax.text(ann['x_pos'], ann['y_pos'], ann['text'],
                               fontsize=ann.get('fontsize', 12),
                               color=ann.get('color', 'black'),
                               bbox=bbox_props,
                               zorder=10,
                               picker=picker)
                
            elif ann['type'] == 'arrow':
                # Enhanced arrow annotation with better control
                arrow = FancyArrowPatch(
                    (ann['x_start'], ann['y_start']),
                    (ann['x_end'], ann['y_end']),
                    arrowstyle=ann.get('style', '->'),
                    color=ann.get('color', 'black'),
                    linewidth=ann.get('width', 2),
                    mutation_scale=20,
                    alpha=ann.get('alpha', 0.8)
                )
                ax.add_patch(arrow)
                artist = arrow
                
            if artist:
                artists[artist] = ann_id
        
        return artists

class VacuumAnalysisTools:
    """Specialized tools for vacuum pressure data analysis"""
    
    @staticmethod
    def calculate_base_pressure(pressure_data, window_minutes=10, sample_rate_hz=1):
        """Calculate base pressure using a moving window approach"""
        window_size = int(window_minutes * 60 * sample_rate_hz)
        
        # Calculate rolling minimum
        rolling_min = pd.Series(pressure_data).rolling(window=window_size, center=True).min()
        
        # Find the most stable region (lowest standard deviation)
        rolling_std = pd.Series(pressure_data).rolling(window=window_size, center=True).std()
        
        # Get base pressure from the most stable region
        if not rolling_std.isna().all():
            most_stable_idx = rolling_std.idxmin()
            base_pressure = rolling_min.iloc[most_stable_idx]
        else:
            base_pressure = np.min(pressure_data)
        
        return base_pressure, rolling_min, rolling_std
    
    @staticmethod
    def calculate_noise_metrics(pressure_data, sample_rate_hz=1):
        """Calculate noise metrics for vacuum pressure data"""
        # Remove trend using polynomial fit
        x = np.arange(len(pressure_data))
        coeffs = np.polyfit(x, pressure_data, 2)
        trend = np.polyval(coeffs, x)
        detrended = pressure_data - trend
        
        # Calculate noise metrics
        noise_rms = np.sqrt(np.mean(detrended**2))
        noise_peak_to_peak = np.max(detrended) - np.min(detrended)
        
        # Frequency analysis
        fft_values = np.fft.fft(detrended)
        frequencies = np.fft.fftfreq(len(detrended), 1/sample_rate_hz)
        power_spectrum = np.abs(fft_values)**2
        
        # Find dominant noise frequencies
        positive_freq_mask = frequencies > 0
        dominant_freq_idx = np.argmax(power_spectrum[positive_freq_mask])
        dominant_frequency = frequencies[positive_freq_mask][dominant_freq_idx]
        
        return {
            'noise_rms': noise_rms,
            'noise_p2p': noise_peak_to_peak,
            'dominant_freq': dominant_frequency,
            'power_spectrum': power_spectrum[positive_freq_mask],
            'frequencies': frequencies[positive_freq_mask],
            'detrended_signal': detrended
        }
    
    @staticmethod
    def detect_pressure_spikes(pressure_data, threshold_factor=3, min_spike_duration=1):
        """Detect pressure spikes in vacuum data"""
        # Calculate rolling statistics
        rolling_mean = pd.Series(pressure_data).rolling(window=100, center=True).mean()
        rolling_std = pd.Series(pressure_data).rolling(window=100, center=True).std()
        
        # Identify spikes
        threshold = rolling_mean + threshold_factor * rolling_std
        spike_mask = pressure_data > threshold
        
        # Group consecutive spikes
        spikes = []
        spike_start = None
        
        for i, is_spike in enumerate(spike_mask):
            if is_spike and spike_start is None:
                spike_start = i
            elif not is_spike and spike_start is not None:
                if i - spike_start >= min_spike_duration:
                    spikes.append({
                        'start': spike_start,
                        'end': i,
                        'duration': i - spike_start,
                        'max_pressure': np.max(pressure_data[spike_start:i]),
                        'severity': 'high' if np.max(pressure_data[spike_start:i]) > rolling_mean.iloc[spike_start] * 10 else 'medium'
                    })
                spike_start = None
        
        return spikes
    
    @staticmethod
    def calculate_leak_rate(pressure_data, time_data, start_pressure, end_pressure=None):
        """Calculate vacuum leak rate"""
        if end_pressure is None:
            end_pressure = pressure_data[-1]
        
        # Convert time to seconds if datetime
        if pd.api.types.is_datetime64_any_dtype(time_data):
            time_seconds = (time_data - time_data.iloc[0]).dt.total_seconds()
        else:
            time_seconds = time_data
        
        # Fit exponential or linear model
        log_pressure = np.log(pressure_data)
        coeffs = np.polyfit(time_seconds, log_pressure, 1)
        
        # Leak rate in mbar·L/s (approximate)
        leak_rate = coeffs[0] * np.mean(pressure_data)
        
        # Quality of fit
        fitted = np.exp(np.polyval(coeffs, time_seconds))
        r_squared = 1 - np.sum((pressure_data - fitted)**2) / np.sum((pressure_data - np.mean(pressure_data))**2)
        
        return {
            'leak_rate': leak_rate,
            'r_squared': r_squared,
            'fitted_curve': fitted,
            'time_constant': -1/coeffs[0] if coeffs[0] != 0 else np.inf
        }
    
    @staticmethod
    def analyze_pump_down_curve(pressure_data, time_data):
        """Analyze pump-down characteristics"""
        # Find key points
        initial_pressure = pressure_data[0]
        final_pressure = pressure_data[-1]
        
        # Time to reach certain pressure levels
        milestones = {}
        pressure_targets = [1e-3, 1e-4, 1e-5, 1e-6, 1e-7]
        
        for target in pressure_targets:
            if final_pressure <= target < initial_pressure:
                idx = np.where(pressure_data <= target)[0]
                if len(idx) > 0:
                    milestones[f"{target:.0e} mbar"] = time_data[idx[0]]
        
        # Calculate pumping speed changes
        log_pressure = np.log10(pressure_data)
        d_log_p_dt = np.gradient(log_pressure)
        
        return {
            'initial_pressure': initial_pressure,
            'final_pressure': final_pressure,
            'milestones': milestones,
            'pumping_speed_indicator': -d_log_p_dt
        }

class DataAnalysisTools:
    """Collection of data analysis methods"""
    
    @staticmethod
    def calculate_statistics(data):
        """Calculate comprehensive statistics for a data series"""
        stats_dict = {
            'count': len(data),
            'mean': np.mean(data),
            'median': np.median(data),
            'std': np.std(data),
            'var': np.var(data),
            'min': np.min(data),
            'max': np.max(data),
            'range': np.max(data) - np.min(data),
            'q1': np.percentile(data, 25),
            'q3': np.percentile(data, 75),
            'iqr': np.percentile(data, 75) - np.percentile(data, 25),
            'skewness': stats.skew(data),
            'kurtosis': stats.kurtosis(data),
            'cv': np.std(data) / np.mean(data) if np.mean(data) != 0 else np.nan
        }
        return stats_dict
    
    @staticmethod
    def find_peaks_and_valleys(x_data, y_data, prominence=None):
        """Find peaks and valleys in the data"""
        # Find peaks
        peaks, peak_props = find_peaks(y_data, prominence=prominence)
        
        # Find valleys (invert data)
        valleys, valley_props = find_peaks(-y_data, prominence=prominence)
        
        return {
            'peaks': {'indices': peaks, 'x_values': x_data[peaks], 'y_values': y_data[peaks]},
            'valleys': {'indices': valleys, 'x_values': x_data[valleys], 'y_values': y_data[valleys]}
        }
    
    @staticmethod
    def calculate_moving_average(data, window_size):
        """Calculate moving average"""
        return pd.Series(data).rolling(window=window_size, center=True).mean()
    
    @staticmethod
    def calculate_derivative(x_data, y_data):
        """Calculate numerical derivative"""
        return np.gradient(y_data, x_data)
    
    @staticmethod
    def perform_fft(data, sample_rate=1.0):
        """Perform Fast Fourier Transform"""
        fft_values = np.fft.fft(data)
        frequencies = np.fft.fftfreq(len(data), 1/sample_rate)
        
        # Return positive frequencies only
        positive_freq_idx = frequencies > 0
        return frequencies[positive_freq_idx], np.abs(fft_values[positive_freq_idx])
    
    @staticmethod
    def calculate_correlation_matrix(dataframe, columns):
        """Calculate correlation matrix for selected columns"""
        return dataframe[columns].corr()
    
    @staticmethod
    def perform_regression(x_data, y_data, degree=1):
        """Perform polynomial regression"""
        x_data = np.array(x_data).reshape(-1, 1)
        y_data = np.array(y_data)
        
        if degree == 1:
            model = LinearRegression()
            model.fit(x_data, y_data)
            y_pred = model.predict(x_data)
            r2 = model.score(x_data, y_data)
            coefficients = [model.intercept_, model.coef_[0]]
        else:
            coefficients = np.polyfit(x_data.flatten(), y_data, degree)
            poly = np.poly1d(coefficients)
            y_pred = poly(x_data.flatten())
            r2 = 1 - (np.sum((y_data - y_pred)**2) / np.sum((y_data - np.mean(y_data))**2))
        
        return {
            'coefficients': coefficients,
            'y_predicted': y_pred,
            'r_squared': r2,
            'residuals': y_data - y_pred
        }

class ModernSeriesConfig:
    """Enhanced series configuration with better defaults"""
    def __init__(self, name, file_id, x_col, y_col, start_idx=None, end_idx=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.file_id = file_id
        self.x_column = x_col
        self.y_column = y_col
        self.start_index = start_idx if start_idx is not None else 0
        self.end_index = end_idx
        
        # Modern visual defaults
        self.color = None  # Auto-assign
        self.line_style = '-'
        self.marker = ''  # No markers by default for cleaner look
        self.line_width = 2.5
        self.marker_size = 6
        self.alpha = 0.9
        self.fill_area = False
        self.gradient_fill = False
        
        # Enhanced data handling
        self.missing_data_method = 'interpolate'
        self.outlier_handling = 'keep'
        self.outlier_threshold = 3.0  # Standard deviations
        self.smoothing = False
        self.smooth_factor = 0  # 0-100, 0 = no smoothing
        
        # Date/time handling
        self.datetime_format = 'auto'  # auto, custom, or specific format
        self.custom_datetime_format = '%Y-%m-%d %H:%M:%S'
        self.timezone = None
        
        # Display options
        self.visible = True
        self.show_in_legend = True
        self.legend_label = name
        self.y_axis = 'left'  # 'left' or 'right'
        
        # Analysis features
        self.show_statistics = False
        self.show_trendline = False
        self.trend_type = 'linear'  # linear, polynomial, exponential, moving_average
        self.trend_params = {'degree': 1, 'window': 20}
        self.show_peaks = False
        self.peak_prominence = 0.1
        
        # Additional attributes
        self.missing_data_color = 'red'
        self.show_moving_average = False
        self.moving_average_window = 20
        self.show_confidence_interval = False
        self.confidence_level = 0.95

        # Initialize missing defaults
        self.highlight_weekends = False
        self.highlight_business_hours = False
        self.highlight_outliers = False
        self.outlier_method = 'keep'
        
        # Vacuum-specific defaults
        self.highlight_base_pressure = False
        self.highlight_spikes = False

class FileData:
    """Container for loaded file data"""
    def __init__(self, filepath, dataframe):
        self.id = str(uuid.uuid4())
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.df = dataframe
        self.original_df = dataframe.copy()
        self.load_time = datetime.now()
        self.series_list = []

class ImprovedDataSelector(ctk.CTkFrame):
    """Improved data selector for handling various Excel layouts"""
    def __init__(self, master, file_data, on_data_selected=None, **kwargs):
        super().__init__(master, **kwargs)
        self.file_data = file_data
        self.on_data_selected = on_data_selected
        self.preview_rows = 10
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create the data selector interface"""
        # Preview section
        preview_label = ctk.CTkLabel(self, text="Data Preview", font=("", 14, "bold"))
        preview_label.pack(pady=(10, 5))
        
        # Preview frame with scrollbars
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create text widget for preview
        self.preview_text = ctk.CTkTextbox(preview_frame, height=200)
        self.preview_text.pack(fill="both", expand=True)
        
        # Update preview
        self.update_preview()
        
        # Column detection section
        detect_frame = ctk.CTkFrame(self)
        detect_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(detect_frame, text="Header Row:").pack(side="left", padx=5)
        self.header_row_var = tk.IntVar(value=0)
        self.header_spin = ctk.CTkEntry(detect_frame, textvariable=self.header_row_var, width=60)
        self.header_spin.pack(side="left", padx=5)
        
        ctk.CTkButton(
            detect_frame,
            text="Auto-Detect Headers",
            command=self.auto_detect_headers,
            width=150
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            detect_frame,
            text="Update Preview",
            command=self.update_preview,
            width=100
        ).pack(side="left", padx=5)
        
        # Data range selection
        range_frame = ctk.CTkFrame(self)
        range_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(range_frame, text="Data Range:").grid(row=0, column=0, sticky="w", padx=5)
        
        ctk.CTkLabel(range_frame, text="Start Row:").grid(row=0, column=1, padx=5)
        self.start_row_var = tk.IntVar(value=1)
        ctk.CTkEntry(range_frame, textvariable=self.start_row_var, width=80).grid(row=0, column=2, padx=5)
        
        ctk.CTkLabel(range_frame, text="End Row:").grid(row=0, column=3, padx=5)
        self.end_row_var = tk.IntVar(value=len(self.file_data.df))
        ctk.CTkEntry(range_frame, textvariable=self.end_row_var, width=80).grid(row=0, column=4, padx=5)
        
        # Column selection
        col_frame = ctk.CTkFrame(self)
        col_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(col_frame, text="Select Columns:").pack(anchor="w", pady=5)
        
        # Column listbox with scrollbar
        list_frame = ctk.CTkFrame(col_frame)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ctk.CTkScrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.column_listbox = tk.Listbox(
            list_frame,
            selectmode="multiple",
            height=8,
            yscrollcommand=scrollbar.set
        )
        self.column_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=self.column_listbox.yview)
        
        # Populate columns
        self.update_column_list()
        
        # Apply button
        ctk.CTkButton(
            self,
            text="Apply Selection",
            command=self.apply_selection,
            fg_color=ColorPalette.SUCCESS
        ).pack(pady=10)
    
    def auto_detect_headers(self):
        """Auto-detect header row"""
        # Simple heuristic: find row with most non-numeric values
        max_non_numeric = 0
        best_row = 0
        
        for i in range(min(20, len(self.file_data.df))):
            row = self.file_data.df.iloc[i]
            non_numeric_count = sum(1 for val in row if not self.is_numeric(val))
            
            if non_numeric_count > max_non_numeric:
                max_non_numeric = non_numeric_count
                best_row = i
        
        self.header_row_var.set(best_row)
        self.update_preview()
    
    def is_numeric(self, value):
        """Check if value is numeric"""
        try:
            float(value)
            return True
        except:
            return False
    
    def update_preview(self):
        """Update data preview"""
        try:
            header_row = self.header_row_var.get()
            
            # Show preview with potential headers
            preview_text = "Preview (first 10 rows):\n\n"
            
            if header_row > 0:
                preview_text += "Detected Headers:\n"
                headers = self.file_data.df.iloc[header_row].values
                preview_text += ", ".join(str(h) for h in headers) + "\n\n"
            
            # Show data rows
            start = max(0, header_row + 1)
            end = min(start + self.preview_rows, len(self.file_data.df))
            
            preview_df = self.file_data.df.iloc[start:end]
            preview_text += preview_df.to_string()
            
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", preview_text)
            
            # Update column list
            self.update_column_list()
            
        except Exception as e:
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert("1.0", f"Error updating preview: {str(e)}")
    
    def update_column_list(self):
        """Update column selection list"""
        self.column_listbox.delete(0, tk.END)
        
        header_row = self.header_row_var.get()
        
        if header_row >= 0 and header_row < len(self.file_data.df):
            # Use specified row as headers
            columns = self.file_data.df.iloc[header_row].values
            for i, col in enumerate(columns):
                self.column_listbox.insert(tk.END, f"Column {i}: {col}")
        else:
            # Use default column names
            for col in self.file_data.df.columns:
                self.column_listbox.insert(tk.END, str(col))
    
    def apply_selection(self):
        """Apply the data selection"""
        if self.on_data_selected:
            selection_info = {
                'header_row': self.header_row_var.get(),
                'start_row': self.start_row_var.get(),
                'end_row': self.end_row_var.get(),
                'selected_columns': [self.column_listbox.get(i) for i in self.column_listbox.curselection()]
            }
            self.on_data_selected(selection_info)

class ModernSeriesConfigDialog:
    """Modern, intuitive series configuration dialog"""
    def __init__(self, parent, series_config, file_data):
        self.parent = parent
        self.series = series_config
        self.file_data = file_data
        self.result = None
        
        # Analyze data for smart defaults
        self.analyze_data()
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Configure: {series_config.name}")
        self.dialog.geometry("1050x750")
        self.dialog.configure(bg='#f0f0f0')
        
        # Modern styling
        self.setup_styles()
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Store dialog as 'top' for compatibility
        self.top = self.dialog
        
        self.create_widgets()
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
    
    def setup_styles(self):
        """Setup modern styles"""
        style = ttk.Style()
        
        # Configure modern notebook style
        style.configure('Modern.TNotebook', tabposition='n', borderwidth=0)
        style.configure('Modern.TNotebook.Tab', padding=[20, 10], font=('Segoe UI', 10))
        
        # Modern frames
        style.configure('Card.TFrame', relief='flat', borderwidth=1)
        style.configure('Header.TLabel', font=('Segoe UI', 11, 'bold'))
        style.configure('Modern.TButton', font=('Segoe UI', 10))
    
    def analyze_data(self):
        """Analyze data to provide smart defaults"""
        try:
            start_idx = self.series.start_index
            end_idx = self.series.end_index or len(self.file_data.df)
            data_slice = self.file_data.df.iloc[start_idx:end_idx]
            
            # Check if X column is datetime
            self.series._datetime_detected = False
            if self.series.x_column != 'Index':
                x_data = data_slice[self.series.x_column]
                self.series._datetime_detected = self.is_datetime_data(x_data)
            
            # Initialize as empty dict
            self.series._data_stats = {}
            
            # Calculate Y data statistics
            if self.series.y_column in data_slice.columns:
                y_data = data_slice[self.series.y_column].dropna()
                if len(y_data) > 0:
                    self.series._data_stats = {
                        'min': y_data.min(),
                        'max': y_data.max(),
                        'mean': y_data.mean(),
                        'std': y_data.std(),
                        'count': len(y_data),
                        'missing': len(data_slice) - len(y_data)
                    }
        except Exception as e:
            print(f"Data analysis error: {e}")
            self.series._datetime_detected = False
            self.series._data_stats = {}
    
    def is_datetime_data(self, data):
        """Check if data is datetime"""
        if pd.api.types.is_datetime64_any_dtype(data):
            return True
        
        # Try to detect datetime strings
        try:
            sample = data.dropna().head(10)
            if len(sample) > 0:
                pd.to_datetime(sample, infer_datetime_format=True)
                return True
        except:
            pass
        
        return False
    
    def create_widgets(self):
        # Header with series info
        self.create_header()
        
        # Main content area with cards
        main_frame = ttk.Frame(self.dialog, style='Card.TFrame')
        main_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        # Create two columns
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', padx=(10, 0))
        
        # Create card-based layout in left column
        self.create_card_layout(left_frame)
        
        # Add preview panel in right column
        self.create_preview_panel(right_frame)
        
        # Action buttons
        self.create_action_buttons()

    def create_preview_panel(self, parent):
        """Create live preview panel"""
        preview_frame = ttk.LabelFrame(parent, text="Live Preview", padding=10)
        preview_frame.pack(fill='both', expand=True)
        
        self.preview_panel = LivePreviewPanel(preview_frame, width=400, height=500)
        
        # Update preview on changes
        self.update_preview()

    def update_preview(self):
        """Update the live preview"""
        try:
            # Get sample data
            start_idx = self.series.start_index
            end_idx = min(self.series.end_index or len(self.file_data.df), start_idx + 1000)
            data_slice = self.file_data.df.iloc[start_idx:end_idx]
            
            if self.series.x_column == 'Index':
                x_data = np.arange(len(data_slice))
            else:
                x_data = data_slice[self.series.x_column]
            
            y_data = data_slice[self.series.y_column]
            
            # Get current settings
            settings = {
                'color': self.color_var.get(),
                'line_style': self.series.line_style,
                'line_width': self.width_var.get(),
                'alpha': self.alpha_var.get(),
                'fill_area': self.fill_var.get()
            }

            # Update preview
            self.preview_panel.update_preview(x_data, y_data, settings)
        except Exception as e:
            print(f"Preview update error: {e}")
        
    def create_header(self):
        """Create modern header with series info"""
        header_frame = tk.Frame(self.dialog, bg='#2c3e50', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Series name and file info
        info_frame = tk.Frame(header_frame, bg='#2c3e50')
        info_frame.pack(expand=True)
        
        tk.Label(info_frame, text=self.series.name, 
                font=('Segoe UI', 16, 'bold'), 
                fg='white', bg='#2c3e50').pack(pady=(15, 5))
        
        tk.Label(info_frame, 
                text=f"{self.file_data.filename} | {self.series.x_column} vs {self.series.y_column}",
                font=('Segoe UI', 10), 
                fg='#ecf0f1', bg='#2c3e50').pack()
        
        if hasattr(self.series, '_data_stats') and self.series._data_stats:
            stats = self.series._data_stats
            tk.Label(info_frame, 
                    text=f"{stats['count']:,} points | {stats['missing']} missing | Range: {stats['min']:.2f} to {stats['max']:.2f}",
                    font=('Segoe UI', 9), 
                    fg='#bdc3c7', bg='#2c3e50').pack()
    
    def create_card_layout(self, parent):
        """Create card-based layout for settings"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create cards
        self.create_data_range_card()  # New card for data range
        self.create_appearance_card()
        self.create_data_handling_card()
        self.create_analysis_card()
        self.create_display_options_card()
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_data_range_card(self):
        """Create data range selection card"""
        card = self.create_card(self.scrollable_frame, "📊 Data Range", expanded=True)
        
        # Current data info
        info_frame = ttk.Frame(card)
        info_frame.pack(fill='x', pady=5)
        
        # Get actual data bounds
        max_rows = len(self.file_data.df)
        
        ttk.Label(info_frame, text=f"Total rows in file: {max_rows:,}", 
                 font=('Segoe UI', 10)).pack(anchor='w')
        
        # Range selection
        range_frame = ttk.Frame(card)
        range_frame.pack(fill='x', pady=10)
        
        ttk.Label(range_frame, text="Start Index:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.start_var = tk.IntVar(value=self.series.start_index)
        self.start_spin = ttk.Spinbox(range_frame, from_=0, to=max_rows-1, 
                                     textvariable=self.start_var, width=15,
                                     command=self.on_range_changed)
        self.start_spin.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(range_frame, text="End Index:").grid(row=0, column=2, sticky='w', padx=(20, 5), pady=5)
        self.end_var = tk.IntVar(value=self.series.end_index or max_rows)
        self.end_spin = ttk.Spinbox(range_frame, from_=1, to=max_rows, 
                                   textvariable=self.end_var, width=15,
                                   command=self.on_range_changed)
        self.end_spin.grid(row=0, column=3, padx=5, pady=5)
        
        # Quick range buttons
        quick_frame = ttk.Frame(card)
        quick_frame.pack(fill='x', pady=5)
        
        ttk.Label(quick_frame, text="Quick Select:").pack(side='left', padx=5)
        
        ttk.Button(quick_frame, text="First 100", 
                  command=lambda: self.set_range(0, 100)).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="First 1000", 
                  command=lambda: self.set_range(0, 1000)).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="Last 100", 
                  command=lambda: self.set_range(max_rows-100, max_rows)).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="Last 1000", 
                  command=lambda: self.set_range(max_rows-1000, max_rows)).pack(side='left', padx=2)
        ttk.Button(quick_frame, text="All Data", 
                  command=lambda: self.set_range(0, max_rows)).pack(side='left', padx=2)
        
        # Selected range info
        self.range_info_label = ttk.Label(card, text="", font=('Segoe UI', 9))
        self.range_info_label.pack(pady=5)
        self.update_range_info()
    
    def set_range(self, start, end):
        """Set data range"""
        max_rows = len(self.file_data.df)
        self.start_var.set(max(0, start))
        self.end_var.set(min(max_rows, end))
        self.on_range_changed()
    
    def on_range_changed(self):
        """Handle range change"""
        self.update_range_info()
        self.update_preview()
    
    def update_range_info(self):
        """Update range information display"""
        start = self.start_var.get()
        end = self.end_var.get()
        count = end - start
        self.range_info_label.config(text=f"Selected: {count:,} rows (indices {start} to {end-1})")
    
    def create_appearance_card(self):
        """Create appearance settings card"""
        card = self.create_card(self.scrollable_frame, "🎨 Appearance", expanded=True)
        
        # Color selection with preview
        color_frame = ttk.Frame(card)
        color_frame.pack(fill='x', pady=5)
        
        ttk.Label(color_frame, text="Color:", style='Header.TLabel').pack(side='left', padx=(0, 10))
        
        self.color_var = tk.StringVar(value=self.series.color or '#3498db')
        self.color_preview = tk.Frame(color_frame, bg=self.color_var.get(), 
                                     width=30, height=30, relief='solid', borderwidth=1)
        self.color_preview.pack(side='left', padx=5)
        
        ttk.Button(color_frame, text="Choose", 
                  command=self.choose_color, width=10).pack(side='left', padx=5)
        
        # Quick color palette
        palette_frame = ttk.Frame(card)
        palette_frame.pack(fill='x', pady=5)
        
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', 
                 '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#d35400']
        
        for color in colors:
            btn = tk.Frame(palette_frame, bg=color, width=25, height=25, 
                          relief='raised', borderwidth=1, cursor='hand2')
            btn.pack(side='left', padx=2)
            btn.bind("<Button-1>", lambda e, c=color: self.set_color(c))
        
        # Line style with preview
        style_frame = ttk.Frame(card)
        style_frame.pack(fill='x', pady=10)
        
        ttk.Label(style_frame, text="Style:", style='Header.TLabel').grid(row=0, column=0, sticky='w')
        
        # Style options with visual representation
        self.style_var = tk.StringVar(value=self.series.line_style)
        styles = [
            ('-', 'Solid ——————'),
            ('--', 'Dashed — — — —'),
            (':', 'Dotted · · · · ·'),
            ('-.', 'Dash-dot — · — ·')
        ]
        
        style_combo = ttk.Combobox(style_frame, textvariable=self.style_var, 
                                  values=[desc for _, desc in styles], 
                                  state='readonly', width=20)
        style_combo.set(dict(styles).get(self.series.line_style, styles[0][1]))
        style_combo.grid(row=0, column=1, padx=10)
        
        # Bind change event to update preview
        style_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # Size controls with live preview
        size_frame = ttk.Frame(card)
        size_frame.pack(fill='x', pady=5)
        
        # Line width
        ttk.Label(size_frame, text="Line Width:").grid(row=0, column=0, sticky='w', pady=5)
        self.width_var = tk.DoubleVar(value=self.series.line_width)
        width_scale = ttk.Scale(size_frame, from_=0.5, to=6, variable=self.width_var,
                               orient='horizontal', length=200,
                               command=lambda v: self.on_width_change())
        width_scale.grid(row=0, column=1, padx=10, pady=5)
        self.width_label = ttk.Label(size_frame, text=f"{self.width_var.get():.1f}")
        self.width_label.grid(row=0, column=2, pady=5)
        
        # Transparency
        ttk.Label(size_frame, text="Transparency:").grid(row=1, column=0, sticky='w', pady=5)
        self.alpha_var = tk.DoubleVar(value=self.series.alpha)
        alpha_scale = ttk.Scale(size_frame, from_=0.1, to=1.0, variable=self.alpha_var,
                               orient='horizontal', length=200,
                               command=lambda v: self.on_alpha_change())
        alpha_scale.grid(row=1, column=1, padx=10, pady=5)
        self.alpha_label = ttk.Label(size_frame, text=f"{int(self.alpha_var.get()*100)}%")
        self.alpha_label.grid(row=1, column=2, pady=5)
        
        # Advanced options
        adv_frame = ttk.LabelFrame(card, text="Advanced Style", padding=10)
        adv_frame.pack(fill='x', pady=10)
        
        self.fill_var = tk.BooleanVar(value=self.series.fill_area)
        fill_check = ttk.Checkbutton(adv_frame, text="Fill area under curve", 
                                    variable=self.fill_var,
                                    command=self.update_preview)
        fill_check.pack(anchor='w')
        
        self.gradient_var = tk.BooleanVar(value=getattr(self.series, 'gradient_fill', False))
        ttk.Checkbutton(adv_frame, text="Use gradient fill", 
                       variable=self.gradient_var).pack(anchor='w')
    
    def on_width_change(self):
        """Handle width change"""
        self.width_label.config(text=f"{self.width_var.get():.1f}")
        self.update_preview()
    
    def on_alpha_change(self):
        """Handle alpha change"""
        self.alpha_label.config(text=f"{int(self.alpha_var.get()*100)}%")
        self.update_preview()
    
    def create_data_handling_card(self):
        """Create data handling settings card"""
        card = self.create_card(self.scrollable_frame, "📊 Data Handling", expanded=True)
        
        # Missing data handling
        missing_frame = ttk.LabelFrame(card, text="Missing Data", padding=10)
        missing_frame.pack(fill='x', pady=5)
        
        self.missing_var = tk.StringVar(value=self.series.missing_data_method)
        methods = [
            ('interpolate', 'Interpolate', 'Fill gaps with interpolated values'),
            ('drop', 'Remove', 'Remove missing data points'),
            ('fill_zero', 'Zero', 'Replace with zero'),
            ('forward_fill', 'Forward Fill', 'Use previous valid value')
        ]
        
        for value, text, tooltip in methods:
            rb = ttk.Radiobutton(missing_frame, text=text, variable=self.missing_var, value=value)
            rb.pack(anchor='w', pady=2)
            self.create_tooltip(rb, tooltip)
        
        # Date/Time handling (if applicable)
        if hasattr(self.series, '_datetime_detected') and self.series._datetime_detected:
            dt_frame = ttk.LabelFrame(card, text="Date/Time Format", padding=10)
            dt_frame.pack(fill='x', pady=5)
            
            self.dt_format_var = tk.StringVar(value=self.series.datetime_format)
            
            ttk.Radiobutton(dt_frame, text="Auto-detect format", 
                           variable=self.dt_format_var, value='auto').pack(anchor='w')
            
            common_formats = [
                ('%Y-%m-%d', 'Date only (2024-03-15)'),
                ('%Y-%m-%d %H:%M:%S', 'Date & Time (2024-03-15 14:30:00)'),
                ('%d/%m/%Y', 'DD/MM/YYYY (15/03/2024)'),
                ('%m/%d/%Y', 'MM/DD/YYYY (03/15/2024)'),
                ('%Y-%m-%d %H:%M', 'Date & Time without seconds')
            ]
            
            for fmt, desc in common_formats:
                ttk.Radiobutton(dt_frame, text=desc, 
                               variable=self.dt_format_var, value=fmt).pack(anchor='w')
            
            # Custom format
            custom_frame = ttk.Frame(dt_frame)
            custom_frame.pack(fill='x', pady=5)
            
            ttk.Radiobutton(custom_frame, text="Custom:", 
                           variable=self.dt_format_var, value='custom').pack(side='left')
            
            self.custom_dt_var = tk.StringVar(value=self.series.custom_datetime_format)
            ttk.Entry(custom_frame, textvariable=self.custom_dt_var, width=25).pack(side='left', padx=5)
        
        # Outlier handling
        outlier_frame = ttk.LabelFrame(card, text="Outlier Detection", padding=10)
        outlier_frame.pack(fill='x', pady=5)
        
        self.outlier_var = tk.StringVar(value=self.series.outlier_method)
        
        ttk.Radiobutton(outlier_frame, text="Keep all data", 
                       variable=self.outlier_var, value='keep').pack(anchor='w')
        ttk.Radiobutton(outlier_frame, text="Remove outliers", 
                       variable=self.outlier_var, value='remove').pack(anchor='w')
        ttk.Radiobutton(outlier_frame, text="Cap outliers", 
                       variable=self.outlier_var, value='cap').pack(anchor='w')
        
        # Threshold setting
        threshold_frame = ttk.Frame(outlier_frame)
        threshold_frame.pack(fill='x', pady=5)
        
        ttk.Label(threshold_frame, text="Threshold (std dev):").pack(side='left')
        self.threshold_var = tk.DoubleVar(value=self.series.outlier_threshold)
        ttk.Spinbox(threshold_frame, from_=1, to=5, increment=0.5, 
                   textvariable=self.threshold_var, width=10).pack(side='left', padx=5)
        
        # Smoothing
        smooth_frame = ttk.LabelFrame(card, text="Data Smoothing", padding=10)
        smooth_frame.pack(fill='x', pady=5)
        
        ttk.Label(smooth_frame, text="Smoothing Level:").pack(anchor='w')
        
        self.smooth_var = tk.IntVar(value=self.series.smooth_factor)
        smooth_scale = ttk.Scale(smooth_frame, from_=0, to=100, variable=self.smooth_var,
                                orient='horizontal', length=300)
        smooth_scale.pack(fill='x', pady=5)
        
        # Labels for smoothing scale
        label_frame = ttk.Frame(smooth_frame)
        label_frame.pack(fill='x')
        ttk.Label(label_frame, text="None", font=('Segoe UI', 8)).pack(side='left')
        ttk.Label(label_frame, text="Heavy", font=('Segoe UI', 8)).pack(side='right')
    
    def create_analysis_card(self):
        """Create analysis settings card"""
        card = self.create_card(self.scrollable_frame, "📈 Analysis", expanded=False)
        
        # Initialize trend-related variables
        self.poly_degree_var = None
        self.ma_window_var = None
        
        # Trend analysis
        trend_frame = ttk.LabelFrame(card, text="Trend Analysis", padding=10)
        trend_frame.pack(fill='x', pady=5)
        
        self.show_trend_var = tk.BooleanVar(value=self.series.show_trendline)
        ttk.Checkbutton(trend_frame, text="Show trend line", 
                       variable=self.show_trend_var,
                       command=self.toggle_trend_options).pack(anchor='w')
        
        self.trend_options_frame = ttk.Frame(trend_frame)
        self.trend_options_frame.pack(fill='x', pady=5)
        
        ttk.Label(self.trend_options_frame, text="Type:").grid(row=0, column=0, sticky='w', padx=5)
        self.trend_type_var = tk.StringVar(value=self.series.trend_type)
        trend_combo = ttk.Combobox(self.trend_options_frame, textvariable=self.trend_type_var,
                                  values=['linear', 'polynomial', 'exponential', 'moving_average'],
                                  state='readonly', width=15)
        trend_combo.grid(row=0, column=1, padx=5)
        trend_combo.bind('<<ComboboxSelected>>', self.on_trend_type_changed)
        
        # Dynamic parameters based on trend type
        self.trend_param_frame = ttk.Frame(self.trend_options_frame)
        self.trend_param_frame.grid(row=1, column=0, columnspan=2, pady=5)
        
        self.update_trend_params()
        self.toggle_trend_options()
        
        # Peak detection
        peak_frame = ttk.LabelFrame(card, text="Peak Detection", padding=10)
        peak_frame.pack(fill='x', pady=5)
        
        self.show_peaks_var = tk.BooleanVar(value=self.series.show_peaks)
        ttk.Checkbutton(peak_frame, text="Mark peaks and valleys", 
                       variable=self.show_peaks_var).pack(anchor='w')
        
        prom_frame = ttk.Frame(peak_frame)
        prom_frame.pack(fill='x', pady=5)
        
        ttk.Label(prom_frame, text="Sensitivity:").pack(side='left')
        self.peak_prom_var = tk.DoubleVar(value=self.series.peak_prominence)
        prom_scale = ttk.Scale(prom_frame, from_=0.01, to=0.5, variable=self.peak_prom_var,
                              orient='horizontal', length=200)
        prom_scale.pack(side='left', padx=10)
        
        # Statistics overlay
        stats_frame = ttk.LabelFrame(card, text="Statistics Display", padding=10)
        stats_frame.pack(fill='x', pady=5)
        
        self.show_stats_var = tk.BooleanVar(value=self.series.show_statistics)
        ttk.Checkbutton(stats_frame, text="Show statistics box on plot", 
                       variable=self.show_stats_var).pack(anchor='w')
    
    def create_display_options_card(self):
        """Create display options card"""
        card = self.create_card(self.scrollable_frame, "👁️ Display Options", expanded=False)
        
        # Basic visibility
        basic_frame = ttk.Frame(card)
        basic_frame.pack(fill='x', pady=5)
        
        self.visible_var = tk.BooleanVar(value=self.series.visible)
        ttk.Checkbutton(basic_frame, text="Visible", variable=self.visible_var,
                       style='Modern.TCheckbutton').pack(side='left', padx=10)
        
        self.legend_var = tk.BooleanVar(value=self.series.show_in_legend)
        ttk.Checkbutton(basic_frame, text="Show in legend", variable=self.legend_var,
                       style='Modern.TCheckbutton').pack(side='left', padx=10)
        
        # Legend customization
        legend_frame = ttk.Frame(card)
        legend_frame.pack(fill='x', pady=5)
        
        ttk.Label(legend_frame, text="Legend label:").pack(side='left', padx=5)
        self.legend_label_var = tk.StringVar(value=self.series.legend_label)
        ttk.Entry(legend_frame, textvariable=self.legend_label_var, width=30).pack(side='left', padx=5)
        
        # Y-axis selection
        axis_frame = ttk.Frame(card)
        axis_frame.pack(fill='x', pady=5)
        
        ttk.Label(axis_frame, text="Y-axis:").pack(side='left', padx=5)
        self.y_axis_var = tk.StringVar(value=self.series.y_axis)
        ttk.Radiobutton(axis_frame, text="Left", variable=self.y_axis_var, 
                       value='left').pack(side='left', padx=5)
        ttk.Radiobutton(axis_frame, text="Right", variable=self.y_axis_var, 
                       value='right').pack(side='left', padx=5)
        
        # Vacuum-specific highlighting options
        highlight_frame = ttk.LabelFrame(card, text="Auto-highlighting", padding=10)
        highlight_frame.pack(fill='x', pady=10)
        
        self.highlight_base_var = tk.BooleanVar(value=getattr(self.series, 'highlight_base_pressure', False))
        self.highlight_spikes_var = tk.BooleanVar(value=getattr(self.series, 'highlight_spikes', False))
        self.highlight_outliers_var = tk.BooleanVar(value=getattr(self.series, 'highlight_outliers', False))
        
        ttk.Checkbutton(highlight_frame, text="Highlight base pressure level", 
                       variable=self.highlight_base_var).pack(anchor='w')
        ttk.Checkbutton(highlight_frame, text="Highlight pressure spikes", 
                       variable=self.highlight_spikes_var).pack(anchor='w')
        ttk.Checkbutton(highlight_frame, text="Highlight outliers", 
                       variable=self.highlight_outliers_var).pack(anchor='w')
    
    def create_card(self, parent, title, expanded=True):
        """Create a modern card UI element"""
        # Card container
        card_container = ttk.Frame(parent)
        card_container.pack(fill='x', pady=5)
        
        # Card frame with shadow effect
        card = tk.Frame(card_container, bg='white', relief='solid', borderwidth=1)
        card.pack(fill='x', padx=5, pady=2)
        
        # Header
        header = tk.Frame(card, bg='#ecf0f1', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Title with expand/collapse button
        title_frame = tk.Frame(header, bg='#ecf0f1')
        title_frame.pack(side='left', fill='both', expand=True)
        
        self.expand_icon = tk.Label(title_frame, text='▼' if expanded else '▶', 
                                   font=('Segoe UI', 10), bg='#ecf0f1', cursor='hand2')
        self.expand_icon.pack(side='left', padx=(10, 5), pady=10)
        
        tk.Label(title_frame, text=title, font=('Segoe UI', 12, 'bold'), 
                bg='#ecf0f1').pack(side='left', pady=10)
        
        # Content frame
        content = ttk.Frame(card)
        if expanded:
            content.pack(fill='x', padx=15, pady=15)
        
        # Bind expand/collapse
        def toggle_expand(event=None):
            if content.winfo_viewable():
                content.pack_forget()
                self.expand_icon.config(text='▶')
            else:
                content.pack(fill='x', padx=15, pady=15)
                self.expand_icon.config(text='▼')
        
        header.bind("<Button-1>", toggle_expand)
        self.expand_icon.bind("<Button-1>", toggle_expand)
        
        return content
    
    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, background="#333333", 
                           foreground="white", relief='solid', borderwidth=1,
                           font=('Segoe UI', 9))
            label.pack()
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def create_action_buttons(self):
        """Create modern action buttons"""
        btn_frame = tk.Frame(self.dialog, bg='#ecf0f1')
        btn_frame.pack(fill='x', pady=10)
        
        # Apply button
        apply_btn = tk.Button(btn_frame, text="Apply Changes", 
                            command=self.apply_changes,
                            bg='#3498db', fg='white', 
                            font=('Segoe UI', 11, 'bold'),
                            padx=20, pady=8, 
                            relief='flat', cursor='hand2')
        apply_btn.pack(side='right', padx=10)
        
        # Cancel button
        cancel_btn = tk.Button(btn_frame, text="Cancel", 
                             command=self.cancel,
                             bg='#95a5a6', fg='white', 
                             font=('Segoe UI', 11),
                             padx=20, pady=8, 
                             relief='flat', cursor='hand2')
        cancel_btn.pack(side='right', padx=5)
        
        # Reset button
        reset_btn = tk.Button(btn_frame, text="Reset to Defaults", 
                            command=self.reset_defaults,
                            bg='#e74c3c', fg='white', 
                            font=('Segoe UI', 10),
                            padx=15, pady=8, 
                            relief='flat', cursor='hand2')
        reset_btn.pack(side='left', padx=10)
    
    def choose_color(self):
        """Choose color with modern color picker"""
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
            self.set_color(color[1])
    
    def set_color(self, color):
        """Set the selected color"""
        self.color_var.set(color)
        self.color_preview.config(bg=color)
        self.update_preview()
    
    def toggle_trend_options(self):
        """Toggle trend options visibility"""
        if self.show_trend_var.get():
            self.trend_options_frame.pack(fill='x', pady=5)
        else:
            self.trend_options_frame.pack_forget()
    
    def on_trend_type_changed(self, event=None):
        """Update trend parameters based on type"""
        self.update_trend_params()
    
    def update_trend_params(self):
        """Update trend parameter inputs based on selected type"""
        # Clear existing parameters
        for widget in self.trend_param_frame.winfo_children():
            widget.destroy()
        
        trend_type = self.trend_type_var.get()
        
        if trend_type == 'polynomial':
            ttk.Label(self.trend_param_frame, text="Degree:").pack(side='left', padx=5)
            self.poly_degree_var = tk.IntVar(value=self.series.trend_params.get('degree', 2))
            ttk.Spinbox(self.trend_param_frame, from_=1, to=10, 
                       textvariable=self.poly_degree_var, width=10).pack(side='left')
            
        elif trend_type == 'moving_average':
            ttk.Label(self.trend_param_frame, text="Window:").pack(side='left', padx=5)
            self.ma_window_var = tk.IntVar(value=self.series.trend_params.get('window', 20))
            ttk.Spinbox(self.trend_param_frame, from_=5, to=100, 
                       textvariable=self.ma_window_var, width=10).pack(side='left')
    
    def apply_changes(self):
        """Apply all changes to series configuration"""
        try:
            # Data range
            self.series.start_index = self.start_var.get()
            self.series.end_index = self.end_var.get()
            
            # Basic settings
            self.series.color = self.color_var.get()
            
            # Parse line style
            style_map = {
                'Solid ——————': '-',
                'Dashed — — — —': '--',
                'Dotted · · · · ·': ':',
                'Dash-dot — · — ·': '-.'
            }
            self.series.line_style = style_map.get(self.style_var.get(), '-')
            
            # Appearance
            self.series.line_width = self.width_var.get()
            self.series.alpha = self.alpha_var.get()
            self.series.fill_area = self.fill_var.get()
            self.series.gradient_fill = self.gradient_var.get()
            
            # Data handling
            self.series.missing_data_method = self.missing_var.get()
            self.series.outlier_method = self.outlier_var.get()
            self.series.outlier_threshold = self.threshold_var.get()
            self.series.smooth_factor = self.smooth_var.get()
            
            # DateTime handling
            if hasattr(self, 'dt_format_var'):
                self.series.datetime_format = self.dt_format_var.get()
                if self.series.datetime_format == 'custom':
                    self.series.custom_datetime_format = self.custom_dt_var.get()
            
            # Analysis
            self.series.show_peaks = self.show_peaks_var.get()
            self.series.peak_prominence = self.peak_prom_var.get()
            self.series.show_statistics = self.show_stats_var.get()
            
            # Display options
            self.series.visible = self.visible_var.get()
            self.series.show_in_legend = self.legend_var.get()
            self.series.legend_label = self.legend_label_var.get()
            self.series.y_axis = self.y_axis_var.get()
            
            # Vacuum-specific highlighting
            self.series.highlight_base_pressure = self.highlight_base_var.get() if hasattr(self, 'highlight_base_var') else False
            self.series.highlight_spikes = self.highlight_spikes_var.get() if hasattr(self, 'highlight_spikes_var') else False
            self.series.highlight_outliers = self.highlight_outliers_var.get() if hasattr(self, 'highlight_outliers_var') else False
            
            self.result = 'apply'
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply changes:\n{str(e)}")
    
    def cancel(self):
        """Cancel without applying changes"""
        self.result = 'cancel'
        self.dialog.destroy()
    
    def reset_defaults(self):
        """Reset to default values"""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to defaults?"):
            # Reset all variables to defaults
            self.color_var.set('#3498db')
            self.set_color('#3498db')
            self.style_var.set('Solid ——————')
            self.width_var.set(2.5)
            self.alpha_var.set(0.9)
            self.fill_var.set(False)
            self.gradient_var.set(False)
            
            self.missing_var.set('interpolate')
            self.outlier_var.set('keep')
            self.threshold_var.set(3.0)
            self.smooth_var.set(0)
            
            self.show_trend_var.set(False)
            self.show_peaks_var.set(False)
            self.show_stats_var.set(False)
            
            self.visible_var.set(True)
            self.legend_var.set(True)
            self.y_axis_var.set('left')
            
            self.update_preview()

class VacuumAnalysisDialog:
    """Dialog for vacuum-specific data analysis tools"""
    def __init__(self, parent, series_data, all_series, loaded_files):
        self.parent = parent
        self.series_data = series_data
        self.all_series = all_series
        self.loaded_files = loaded_files
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Vacuum Data Analysis Tools")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
    
    def create_widgets(self):
        # Create notebook for different analysis categories
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Base pressure analysis tab
        self.create_base_pressure_tab(notebook)
        
        # Noise analysis tab
        self.create_noise_analysis_tab(notebook)
        
        # Spike detection tab
        self.create_spike_detection_tab(notebook)
        
        # Leak rate analysis tab
        self.create_leak_rate_tab(notebook)
        
        # Pump-down analysis tab
        self.create_pumpdown_tab(notebook)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Close", command=self.close).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Export Results", command=self.export_results).pack(side='right', padx=5)
    
    def create_base_pressure_tab(self, notebook):
        """Create base pressure analysis tab"""
        base_frame = ttk.Frame(notebook)
        notebook.add(base_frame, text='🎯 Base Pressure')
        
        # Series selection
        select_frame = ttk.LabelFrame(base_frame, text="Select Series", padding=10)
        select_frame.pack(fill='x', padx=5, pady=5)
        
        self.base_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(select_frame, textvariable=self.base_series_var, 
                    values=series_options, state='readonly', width=40).pack(pady=5)
        
        # Window size setting
        window_frame = ttk.Frame(select_frame)
        window_frame.pack(fill='x', pady=5)
        
        ttk.Label(window_frame, text="Window Size (minutes):").pack(side='left', padx=5)
        self.window_size_var = tk.IntVar(value=10)
        ttk.Spinbox(window_frame, from_=1, to=60, textvariable=self.window_size_var, width=10).pack(side='left', padx=5)
        
        ttk.Button(select_frame, text="Calculate Base Pressure", 
                  command=self.calculate_base_pressure).pack(pady=5)
        
        # Results display
        results_frame = ttk.LabelFrame(base_frame, text="Analysis Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create text widget for results
        self.base_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10))
        base_scroll = ttk.Scrollbar(results_frame, command=self.base_text.yview)
        self.base_text.config(yscrollcommand=base_scroll.set)
        
        self.base_text.pack(side='left', fill='both', expand=True)
        base_scroll.pack(side='right', fill='y')
        
        # Visualization frame
        viz_frame = ttk.LabelFrame(base_frame, text="Visualization", padding=10)
        viz_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(viz_frame, text="Add Base Pressure Line to Plot", 
                  command=self.add_base_pressure_line).pack(pady=5)
    
    def create_noise_analysis_tab(self, notebook):
        """Create noise analysis tab"""
        noise_frame = ttk.Frame(notebook)
        notebook.add(noise_frame, text='📊 Noise Analysis')
        
        # Configuration
        config_frame = ttk.LabelFrame(noise_frame, text="Noise Analysis Settings", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.noise_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.noise_series_var, 
                    values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Sample rate
        ttk.Label(config_frame, text="Sample Rate (Hz):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.sample_rate_var = tk.DoubleVar(value=1.0)
        ttk.Entry(config_frame, textvariable=self.sample_rate_var, width=15).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        ttk.Button(config_frame, text="Analyze Noise", 
                  command=self.analyze_noise).grid(row=2, column=1, pady=10)
        
        # Results
        results_frame = ttk.LabelFrame(noise_frame, text="Noise Metrics", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.noise_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10), height=10)
        noise_scroll = ttk.Scrollbar(results_frame, command=self.noise_text.yview)
        self.noise_text.config(yscrollcommand=noise_scroll.set)
        
        self.noise_text.pack(side='left', fill='both', expand=True)
        noise_scroll.pack(side='right', fill='y')
        
        # Spectrum plot frame
        spectrum_frame = ttk.LabelFrame(noise_frame, text="Frequency Spectrum", padding=10)
        spectrum_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.noise_fig = Figure(figsize=(6, 3), facecolor='white')
        self.noise_canvas = FigureCanvasTkAgg(self.noise_fig, master=spectrum_frame)
        self.noise_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def create_spike_detection_tab(self, notebook):
        """Create spike detection tab"""
        spike_frame = ttk.Frame(notebook)
        notebook.add(spike_frame, text='⚡ Spike Detection')
        
        # Configuration
        config_frame = ttk.LabelFrame(spike_frame, text="Spike Detection Settings", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.spike_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.spike_series_var, 
                    values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Threshold setting
        ttk.Label(config_frame, text="Threshold (σ):").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.spike_threshold_var = tk.DoubleVar(value=3.0)
        ttk.Scale(config_frame, from_=1.0, to=5.0, variable=self.spike_threshold_var, 
                 orient='horizontal', length=200).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(config_frame, textvariable=self.spike_threshold_var).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Button(config_frame, text="Detect Spikes", 
                  command=self.detect_spikes).grid(row=2, column=1, pady=10)
        
        # Results
        results_frame = ttk.LabelFrame(spike_frame, text="Detected Spikes", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for spikes
        columns = ['Index', 'Start Time', 'Duration', 'Max Pressure', 'Severity']
        self.spikes_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.spikes_tree.heading(col, text=col)
            self.spikes_tree.column(col, width=100)
        
        spikes_scroll = ttk.Scrollbar(results_frame, orient='vertical', command=self.spikes_tree.yview)
        self.spikes_tree.configure(yscrollcommand=spikes_scroll.set)
        
        self.spikes_tree.pack(side='left', fill='both', expand=True)
        spikes_scroll.pack(side='right', fill='y')
        
        # Action buttons
        action_frame = ttk.Frame(spike_frame)
        action_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(action_frame, text="Mark Spikes on Plot", 
                  command=self.mark_spikes_on_plot).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Export Spike Data", 
                  command=self.export_spike_data).pack(side='left', padx=5)
    
    def create_leak_rate_tab(self, notebook):
        """Create leak rate analysis tab"""
        leak_frame = ttk.Frame(notebook)
        notebook.add(leak_frame, text='💨 Leak Rate')
        
        # Configuration
        config_frame = ttk.LabelFrame(leak_frame, text="Leak Rate Analysis", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.leak_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.leak_series_var, 
                    values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(config_frame, text="Calculate Leak Rate", 
                  command=self.calculate_leak_rate).grid(row=1, column=1, pady=10)
        
        # Results
        results_frame = ttk.LabelFrame(leak_frame, text="Leak Rate Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.leak_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10), height=10)
        leak_scroll = ttk.Scrollbar(results_frame, command=self.leak_text.yview)
        self.leak_text.config(yscrollcommand=leak_scroll.set)
        
        self.leak_text.pack(side='left', fill='both', expand=True)
        leak_scroll.pack(side='right', fill='y')
        
        # Fit plot frame
        fit_frame = ttk.LabelFrame(leak_frame, text="Leak Rate Fit", padding=10)
        fit_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.leak_fig = Figure(figsize=(6, 3), facecolor='white')
        self.leak_canvas = FigureCanvasTkAgg(self.leak_fig, master=fit_frame)
        self.leak_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def create_pumpdown_tab(self, notebook):
        """Create pump-down analysis tab"""
        pump_frame = ttk.Frame(notebook)
        notebook.add(pump_frame, text='📉 Pump-down')
        
        # Configuration
        config_frame = ttk.LabelFrame(pump_frame, text="Pump-down Analysis", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.pump_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.pump_series_var, 
                    values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(config_frame, text="Analyze Pump-down", 
                  command=self.analyze_pumpdown).grid(row=1, column=1, pady=10)
        
        # Results
        results_frame = ttk.LabelFrame(pump_frame, text="Pump-down Characteristics", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.pump_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10))
        pump_scroll = ttk.Scrollbar(results_frame, command=self.pump_text.yview)
        self.pump_text.config(yscrollcommand=pump_scroll.set)
        
        self.pump_text.pack(side='left', fill='both', expand=True)
        pump_scroll.pack(side='right', fill='y')
    
    def calculate_base_pressure(self):
        """Calculate base pressure for selected series"""
        series_text = self.base_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return
        
        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break
        
        if not series:
            return
        
        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)
        
        y_data = file_data.df.iloc[start_idx:end_idx][series.y_column].dropna()
        
        if len(y_data) == 0:
            self.base_text.delete(1.0, tk.END)
            self.base_text.insert(1.0, "No valid data in selected series")
            return
        
        # Calculate base pressure
        window_minutes = self.window_size_var.get()
        base_pressure, rolling_min, rolling_std = VacuumAnalysisTools.calculate_base_pressure(
            y_data.values, window_minutes=window_minutes
        )
        
        # Display results
        result_text = f"BASE PRESSURE ANALYSIS\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"Window Size: {window_minutes} minutes\n"
        result_text += f"{'='*50}\n\n"
        
        result_text += f"Base Pressure: {base_pressure:.2e} mbar\n\n"
        
        result_text += f"Additional Statistics:\n"
        result_text += f"  Current Pressure: {y_data.iloc[-1]:.2e} mbar\n"
        result_text += f"  Average Pressure: {y_data.mean():.2e} mbar\n"
        result_text += f"  Minimum Pressure: {y_data.min():.2e} mbar\n"
        result_text += f"  Stability (min std): {rolling_std.min():.2e} mbar\n"
        
        # Store results for plotting
        self.current_base_pressure = base_pressure
        self.current_base_series = series
        
        self.base_text.delete(1.0, tk.END)
        self.base_text.insert(1.0, result_text)
    
    def add_base_pressure_line(self):
        """Add base pressure line to main plot"""
        if not hasattr(self, 'current_base_pressure'):
            messagebox.showwarning("Warning", "Please calculate base pressure first")
            return
        
        # Add annotation to parent's annotation manager
        if hasattr(self.parent, 'annotation_manager'):
            self.parent.annotation_manager.add_annotation(
                'hline',
                y_pos=self.current_base_pressure,
                label=f"Base Pressure: {self.current_base_pressure:.2e} mbar",
                color='green',
                style='--',
                width=2
            )
            messagebox.showinfo("Success", "Base pressure line added to plot")
    
    def analyze_noise(self):
        """Analyze noise in pressure data"""
        series_text = self.noise_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return
        
        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break
        
        if not series:
            return
        
        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)
        
        y_data = file_data.df.iloc[start_idx:end_idx][series.y_column].dropna()
        
        if len(y_data) == 0:
            return
        
        # Analyze noise
        sample_rate = self.sample_rate_var.get()
        noise_metrics = VacuumAnalysisTools.calculate_noise_metrics(y_data.values, sample_rate)
        
        # Display results
        result_text = f"NOISE ANALYSIS\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"Sample Rate: {sample_rate} Hz\n"
        result_text += f"{'='*50}\n\n"
        
        result_text += f"Noise Metrics:\n"
        result_text += f"  RMS Noise: {noise_metrics['noise_rms']:.2e} mbar\n"
        result_text += f"  Peak-to-Peak: {noise_metrics['noise_p2p']:.2e} mbar\n"
        result_text += f"  Dominant Frequency: {noise_metrics['dominant_freq']:.3f} Hz\n"
        result_text += f"  SNR: {20*np.log10(y_data.mean()/noise_metrics['noise_rms']):.1f} dB\n"
        
        self.noise_text.delete(1.0, tk.END)
        self.noise_text.insert(1.0, result_text)
        
        # Plot frequency spectrum
        self.noise_fig.clear()
        ax = self.noise_fig.add_subplot(111)
        
        ax.semilogy(noise_metrics['frequencies'], noise_metrics['power_spectrum'])
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Power Spectral Density')
        ax.set_title('Noise Frequency Spectrum')
        ax.grid(True, alpha=0.3)
        
        self.noise_fig.tight_layout()
        self.noise_canvas.draw()
    
    def detect_spikes(self):
        """Detect pressure spikes"""
        series_text = self.spike_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return
        
        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break
        
        if not series:
            return
        
        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)
        data_slice = file_data.df.iloc[start_idx:end_idx]
        
        y_data = data_slice[series.y_column].values
        
        # Detect spikes
        threshold_factor = self.spike_threshold_var.get()
        spikes = VacuumAnalysisTools.detect_pressure_spikes(y_data, threshold_factor)
        
        # Clear previous results
        for item in self.spikes_tree.get_children():
            self.spikes_tree.delete(item)
        
        # Display spikes
        for i, spike in enumerate(spikes):
            # Get time if available
            if series.x_column != 'Index':
                try:
                    start_time = data_slice.iloc[spike['start']][series.x_column]
                except:
                    start_time = spike['start']
            else:
                start_time = spike['start']
            
            self.spikes_tree.insert('', 'end', values=[
                i,
                str(start_time),
                spike['duration'],
                f"{spike['max_pressure']:.2e}",
                spike['severity']
            ])
        
        # Store results
        self.current_spikes = spikes
        self.current_spike_series = series
    
    def mark_spikes_on_plot(self):
        """Mark detected spikes on the main plot"""
        if not hasattr(self, 'current_spikes'):
            messagebox.showwarning("Warning", "Please detect spikes first")
            return
        
        # Add annotations for spikes
        if hasattr(self.parent, 'annotation_manager'):
            for spike in self.current_spikes:
                # Add region for spike
                self.parent.annotation_manager.add_annotation(
                    'region',
                    x_start=spike['start'],
                    x_end=spike['end'],
                    label=f"Spike: {spike['max_pressure']:.2e} mbar",
                    color='red' if spike['severity'] == 'high' else 'orange',
                    alpha=0.3
                )
            
            messagebox.showinfo("Success", f"Added {len(self.current_spikes)} spike markers to plot")
    
    def export_spike_data(self):
        """Export spike detection results"""
        if not hasattr(self, 'current_spikes'):
            messagebox.showwarning("Warning", "No spike data to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Spike Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                spike_df = pd.DataFrame(self.current_spikes)
                spike_df.to_csv(filename, index=False)
                messagebox.showinfo("Success", f"Spike data exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export spike data:\n{str(e)}")
    
    def calculate_leak_rate(self):
        """Calculate vacuum leak rate"""
        series_text = self.leak_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return
        
        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break
        
        if not series:
            return
        
        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)
        data_slice = file_data.df.iloc[start_idx:end_idx]
        
        # Prepare data
        if series.x_column == 'Index':
            x_data = np.arange(len(data_slice))
        else:
            x_data = data_slice[series.x_column]
        
        y_data = data_slice[series.y_column]
        
        # Remove NaN values
        valid_mask = ~(pd.isna(y_data))
        x_data = x_data[valid_mask]
        y_data = y_data[valid_mask]
        
        if len(x_data) == 0:
            return
        
        # Calculate leak rate
        start_pressure = y_data.iloc[0]
        leak_results = VacuumAnalysisTools.calculate_leak_rate(y_data, x_data, start_pressure)
        
        # Display results
        result_text = f"LEAK RATE ANALYSIS\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"{'='*50}\n\n"
        
        result_text += f"Initial Pressure: {start_pressure:.2e} mbar\n"
        result_text += f"Final Pressure: {y_data.iloc[-1]:.2e} mbar\n\n"
        
        result_text += f"Leak Rate: {leak_results['leak_rate']:.2e} mbar·L/s\n"
        result_text += f"Time Constant: {leak_results['time_constant']:.1f} s\n"
        result_text += f"R-squared: {leak_results['r_squared']:.4f}\n"
        
        self.leak_text.delete(1.0, tk.END)
        self.leak_text.insert(1.0, result_text)
        
        # Plot fit
        self.leak_fig.clear()
        ax = self.leak_fig.add_subplot(111)
        
        ax.semilogy(x_data, y_data, 'o', alpha=0.5, label='Data')
        ax.semilogy(x_data, leak_results['fitted_curve'], 'r-', label='Fit')
        ax.set_xlabel('Time')
        ax.set_ylabel('Pressure (mbar)')
        ax.set_title('Leak Rate Fit')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        self.leak_fig.tight_layout()
        self.leak_canvas.draw()
    
    def analyze_pumpdown(self):
        """Analyze pump-down characteristics"""
        series_text = self.pump_series_var.get()
        if not series_text:
            messagebox.showwarning("Warning", "Please select a series")
            return
        
        # Find the series
        series = None
        for s in self.all_series.values():
            if f"{s.name} ({s.legend_label})" == series_text:
                series = s
                break
        
        if not series:
            return
        
        # Get data
        file_data = self.loaded_files[series.file_id]
        start_idx = series.start_index
        end_idx = series.end_index or len(file_data.df)
        data_slice = file_data.df.iloc[start_idx:end_idx]
        
        # Prepare data
        if series.x_column == 'Index':
            x_data = np.arange(len(data_slice))
        else:
            x_data = data_slice[series.x_column]
        
        y_data = data_slice[series.y_column]
        
        # Remove NaN values
        valid_mask = ~(pd.isna(y_data))
        x_data = x_data[valid_mask]
        y_data = y_data[valid_mask]
        
        if len(x_data) == 0:
            return
        
        # Analyze pump-down
        pump_results = VacuumAnalysisTools.analyze_pump_down_curve(y_data.values, x_data)
        
        # Display results
        result_text = f"PUMP-DOWN ANALYSIS\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"{'='*50}\n\n"
        
        result_text += f"Pressure Range:\n"
        result_text += f"  Initial: {pump_results['initial_pressure']:.2e} mbar\n"
        result_text += f"  Final: {pump_results['final_pressure']:.2e} mbar\n"
        result_text += f"  Reduction: {pump_results['initial_pressure']/pump_results['final_pressure']:.1f}x\n\n"
        
        result_text += f"Milestones:\n"
        for pressure, time in pump_results['milestones'].items():
            result_text += f"  {pressure}: reached at {time}\n"
        
        self.pump_text.delete(1.0, tk.END)
        self.pump_text.insert(1.0, result_text)
    
    def export_results(self):
        """Export all analysis results"""
        filename = filedialog.asksaveasfilename(
            title="Export Vacuum Analysis Results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("VACUUM DATA ANALYSIS RESULTS\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*70 + "\n\n")
                    
                    # Base pressure
                    if self.base_text.get(1.0, tk.END).strip():
                        f.write("BASE PRESSURE ANALYSIS\n")
                        f.write("-"*70 + "\n")
                        f.write(self.base_text.get(1.0, tk.END))
                        f.write("\n\n")
                    
                    # Noise analysis
                    if self.noise_text.get(1.0, tk.END).strip():
                        f.write("NOISE ANALYSIS\n")
                        f.write("-"*70 + "\n")
                        f.write(self.noise_text.get(1.0, tk.END))
                        f.write("\n\n")
                    
                    # Leak rate
                    if self.leak_text.get(1.0, tk.END).strip():
                        f.write("LEAK RATE ANALYSIS\n")
                        f.write("-"*70 + "\n")
                        f.write(self.leak_text.get(1.0, tk.END))
                        f.write("\n\n")
                    
                    # Pump-down
                    if self.pump_text.get(1.0, tk.END).strip():
                        f.write("PUMP-DOWN ANALYSIS\n")
                        f.write("-"*70 + "\n")
                        f.write(self.pump_text.get(1.0, tk.END))
                        f.write("\n\n")
                
                messagebox.showinfo("Success", f"Analysis results exported to:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results:\n{str(e)}")
    
    def close(self):
        """Close the dialog"""
        self.dialog.destroy()

class ModernAnnotationDialog:
    """Modern annotation dialog with inline editing and vacuum templates"""
    def __init__(self, parent, annotation_manager, figure=None, ax=None):
        self.parent = parent
        self.annotation_manager = annotation_manager
        self.figure = figure
        self.ax = ax
        self.selected_annotation = None
        self.dragging = False
        self.drag_data = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Annotations")
        self.dialog.geometry("900x700")
        self.dialog.configure(bg='#f5f5f5')
        
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        
        # If figure is provided, set up interactive editing
        if self.figure and self.ax:
            self.setup_interactive_editing()
        
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
    
    def create_widgets(self):
        """Create modern annotation interface"""
        # Header
        header = tk.Frame(self.dialog, bg='#34495e', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="📍 Plot Annotations", 
                font=('Segoe UI', 16, 'bold'), 
                fg='white', bg='#34495e').pack(pady=15)
        
        # Main container
        main_container = ttk.Frame(self.dialog)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - annotation types
        left_panel = ttk.Frame(main_container, width=250)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self.create_annotation_types_panel(left_panel)
        
        # Right panel - annotation list and properties
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side='left', fill='both', expand=True)
        
        self.create_annotation_list_panel(right_panel)
    
    def create_annotation_types_panel(self, parent):
        """Create panel with annotation type buttons"""
        ttk.Label(parent, text="Add Annotation", 
                 font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))
        
        # Annotation type buttons with icons
        buttons = [
            ("➖ Horizontal Line", self.add_horizontal_line),
            ("│ Vertical Line", self.add_vertical_line),
            ("▭ Shaded Region", self.add_region),
            ("● Point Marker", self.add_point),
            ("T Text Label", self.add_text),
            ("→ Enhanced Arrow", self.add_enhanced_arrow),
        ]
        
        for text, command in buttons:
            btn = tk.Button(parent, text=text, command=command,
                          bg='#3498db', fg='white',
                          font=('Segoe UI', 10),
                          padx=15, pady=10,
                          relief='flat', cursor='hand2',
                          anchor='w')
            btn.pack(fill='x', pady=3)
            
            # Hover effect
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#2980b9'))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#3498db'))
        
        # Quick templates for vacuum analysis
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=20)
        
        ttk.Label(parent, text="Vacuum Templates", 
                 font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))
        
        templates = [
            ("🎯 Base Pressure Line", self.add_base_pressure_template),
            ("📊 Noise Region", self.add_noise_region_template),
            ("⚡ Spike Markers", self.add_spike_marker_template),
            ("📉 Pressure Targets", self.add_pressure_targets_template),
        ]
        
        for text, command in templates:
            btn = tk.Button(parent, text=text, command=command,
                          bg='#27ae60', fg='white',
                          font=('Segoe UI', 9),
                          padx=10, pady=8,
                          relief='flat', cursor='hand2',
                          anchor='w')
            btn.pack(fill='x', pady=2)
            
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#229954'))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#27ae60'))
    
    def create_annotation_list_panel(self, parent):
        """Create panel showing all annotations with inline editing"""
        # List header
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(header_frame, text="Current Annotations", 
                 font=('Segoe UI', 12, 'bold')).pack(side='left')
        
        # Action buttons
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side='right')
        
        ttk.Button(btn_frame, text="Clear All", 
                  command=self.clear_all).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Export", 
                  command=self.export_annotations).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="Import", 
                  command=self.import_annotations).pack(side='left', padx=2)
        
        # Annotation list with custom styling
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill='both', expand=True)
        
        # Create canvas for scrollable list
        self.canvas = tk.Canvas(list_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Update list
        self.update_annotation_list()
        
        # Bottom action bar
        action_bar = ttk.Frame(parent)
        action_bar.pack(fill='x', pady=10)
        
        ttk.Button(action_bar, text="Apply & Close", 
                  command=self.apply_and_close,
                  style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(action_bar, text="Cancel", 
                  command=self.cancel).pack(side='right')
    
    def update_annotation_list(self):
        """Update the annotation list display"""
        # Clear existing items
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Add annotation items
        for ann_id, annotation in self.annotation_manager.annotations.items():
            self.create_annotation_item(ann_id, annotation)
    
    def create_annotation_item(self, ann_id, annotation):
        """Create a single annotation item with inline controls"""
        # Container frame
        item_frame = tk.Frame(self.scrollable_frame, bg='white', relief='solid', 
                             borderwidth=1, padx=10, pady=10)
        item_frame.pack(fill='x', pady=5, padx=5)
        
        # Selection highlight
        if ann_id == self.annotation_manager.selected_annotation:
            item_frame.config(borderwidth=2, relief='solid', highlightbackground='#3498db')
        
        # Header row
        header_row = ttk.Frame(item_frame)
        header_row.pack(fill='x')
        
        # Type icon and label
        type_icons = {
            'vline': '│',
            'hline': '─',
            'region': '▭',
            'point': '●',
            'text': 'T',
            'arrow': '→'
        }
        
        icon = type_icons.get(annotation['type'], '?')
        ttk.Label(header_row, text=f"{icon} {annotation['type'].title()}", 
                 font=('Segoe UI', 10, 'bold')).pack(side='left')
        
        # Visibility toggle
        vis_var = tk.BooleanVar(value=annotation.get('visible', True))
        vis_check = ttk.Checkbutton(header_row, text="", variable=vis_var,
                                   command=lambda: self.toggle_visibility(ann_id, vis_var.get()))
        vis_check.pack(side='right', padx=5)
        ttk.Label(header_row, text="Visible").pack(side='right')
        
        # Delete button
        del_btn = tk.Button(header_row, text="🗑", fg='#e74c3c', 
                           font=('Segoe UI', 10), relief='flat', cursor='hand2',
                           command=lambda: self.delete_annotation(ann_id))
        del_btn.pack(side='right', padx=5)
        
        # Properties based on type
        props_frame = ttk.Frame(item_frame)
        props_frame.pack(fill='x', pady=(10, 0))
        
        self.create_annotation_properties(props_frame, ann_id, annotation)
        
        # Click to select
        item_frame.bind("<Button-1>", lambda e: self.select_annotation(ann_id))
    
    def create_annotation_properties(self, parent, ann_id, annotation):
        """Create property controls for annotation"""
        ann_type = annotation['type']
        
        if ann_type in ['vline', 'hline']:
            # Position with better precision controls
            pos_frame = ttk.Frame(parent)
            pos_frame.pack(fill='x', pady=2)
            
            pos_key = 'x_pos' if ann_type == 'vline' else 'y_pos'
            ttk.Label(pos_frame, text=f"{pos_key.replace('_', ' ').title()}:").pack(side='left')
            
            pos_var = tk.StringVar(value=str(annotation.get(pos_key, 0)))
            pos_entry = ttk.Entry(pos_frame, textvariable=pos_var, width=15)
            pos_entry.pack(side='left', padx=5)
            pos_entry.bind('<Return>', lambda e: self.update_property(ann_id, pos_key, float(pos_var.get())))
            
            # Fine adjustment buttons
            ttk.Button(pos_frame, text="-", width=3,
                      command=lambda: self.adjust_position(ann_id, pos_key, -0.1)).pack(side='left', padx=1)
            ttk.Button(pos_frame, text="+", width=3,
                      command=lambda: self.adjust_position(ann_id, pos_key, 0.1)).pack(side='left', padx=1)
            
            # Color
            color_btn = tk.Button(pos_frame, text="Color", bg=annotation.get('color', 'red'),
                                 command=lambda: self.change_color(ann_id))
            color_btn.pack(side='left', padx=5)
            
        elif ann_type == 'region':
            # Start and end positions with better controls
            pos_frame = ttk.Frame(parent)
            pos_frame.pack(fill='x', pady=2)
            
            ttk.Label(pos_frame, text="From:").pack(side='left')
            start_var = tk.StringVar(value=str(annotation.get('x_start', 0)))
            start_entry = ttk.Entry(pos_frame, textvariable=start_var, width=10)
            start_entry.pack(side='left', padx=5)
            
            ttk.Label(pos_frame, text="To:").pack(side='left', padx=(10, 0))
            end_var = tk.StringVar(value=str(annotation.get('x_end', 1)))
            end_entry = ttk.Entry(pos_frame, textvariable=end_var, width=10)
            end_entry.pack(side='left', padx=5)
            
            def update_region():
                self.annotation_manager.update_annotation(ann_id, 
                    x_start=float(start_var.get()), 
                    x_end=float(end_var.get()))
                self.refresh_plot()
            
            start_entry.bind('<Return>', lambda e: update_region())
            end_entry.bind('<Return>', lambda e: update_region())
            
        elif ann_type == 'text':
            # Text content
            text_frame = ttk.Frame(parent)
            text_frame.pack(fill='x', pady=2)
            
            ttk.Label(text_frame, text="Text:").pack(side='left')
            text_var = tk.StringVar(value=annotation.get('text', ''))
            text_entry = ttk.Entry(text_frame, textvariable=text_var, width=30)
            text_entry.pack(side='left', padx=5)
            text_entry.bind('<Return>', lambda e: self.update_property(ann_id, 'text', text_var.get()))
            
        elif ann_type == 'arrow':
            # Enhanced arrow controls
            arrow_frame = ttk.Frame(parent)
            arrow_frame.pack(fill='x', pady=2)
            
            # Start position
            ttk.Label(arrow_frame, text="Start:").grid(row=0, column=0, sticky='w')
            start_x_var = tk.StringVar(value=str(annotation.get('x_start', 0)))
            start_y_var = tk.StringVar(value=str(annotation.get('y_start', 0)))
            
            ttk.Entry(arrow_frame, textvariable=start_x_var, width=10).grid(row=0, column=1, padx=2)
            ttk.Entry(arrow_frame, textvariable=start_y_var, width=10).grid(row=0, column=2, padx=2)
            
            # End position
            ttk.Label(arrow_frame, text="End:").grid(row=1, column=0, sticky='w')
            end_x_var = tk.StringVar(value=str(annotation.get('x_end', 1)))
            end_y_var = tk.StringVar(value=str(annotation.get('y_end', 1)))
            
            ttk.Entry(arrow_frame, textvariable=end_x_var, width=10).grid(row=1, column=1, padx=2)
            ttk.Entry(arrow_frame, textvariable=end_y_var, width=10).grid(row=1, column=2, padx=2)
            
            def update_arrow():
                self.annotation_manager.update_annotation(ann_id,
                    x_start=float(start_x_var.get()),
                    y_start=float(start_y_var.get()),
                    x_end=float(end_x_var.get()),
                    y_end=float(end_y_var.get()))
                self.refresh_plot()
            
            ttk.Button(arrow_frame, text="Update", command=update_arrow).grid(row=2, column=1, columnspan=2, pady=5)
        
        # Label (common to all)
        if ann_type != 'text':
            label_frame = ttk.Frame(parent)
            label_frame.pack(fill='x', pady=2)
            
            ttk.Label(label_frame, text="Label:").pack(side='left')
            label_var = tk.StringVar(value=annotation.get('label', ''))
            label_entry = ttk.Entry(label_frame, textvariable=label_var, width=25)
            label_entry.pack(side='left', padx=5)
            label_entry.bind('<Return>', lambda e: self.update_property(ann_id, 'label', label_var.get()))
    
    def adjust_position(self, ann_id, pos_key, delta):
        """Fine adjust position"""
        annotation = self.annotation_manager.annotations.get(ann_id)
        if annotation:
            current_pos = annotation.get(pos_key, 0)
            self.annotation_manager.update_annotation(ann_id, **{pos_key: current_pos + delta})
            self.update_annotation_list()
            self.refresh_plot()
    
    def select_annotation(self, ann_id):
        """Select an annotation"""
        self.annotation_manager.selected_annotation = ann_id
        self.update_annotation_list()
        self.refresh_plot()
    
    def toggle_visibility(self, ann_id, visible):
        """Toggle annotation visibility"""
        self.annotation_manager.update_annotation(ann_id, visible=visible)
        self.refresh_plot()
    
    def update_property(self, ann_id, prop, value):
        """Update annotation property"""
        self.annotation_manager.update_annotation(ann_id, **{prop: value})
        self.refresh_plot()
    
    def change_color(self, ann_id):
        """Change annotation color"""
        annotation = self.annotation_manager.annotations.get(ann_id)
        if annotation:
            color = colorchooser.askcolor(initialcolor=annotation.get('color', 'red'))
            if color[1]:
                self.annotation_manager.update_annotation(ann_id, color=color[1])
                self.update_annotation_list()
                self.refresh_plot()
    
    def delete_annotation(self, ann_id):
        """Delete annotation"""
        if messagebox.askyesno("Confirm", "Delete this annotation?"):
            self.annotation_manager.remove_annotation(ann_id)
            self.update_annotation_list()
            self.refresh_plot()
    
    def add_horizontal_line(self):
        """Add horizontal line annotation"""
        # Get current y-axis limits or default
        y_pos = 0
        if self.ax:
            ylim = self.ax.get_ylim()
            y_pos = (ylim[0] + ylim[1]) / 2
        
        ann_id = self.annotation_manager.add_annotation('hline', 
            y_pos=y_pos, 
            label="Horizontal Line",
            color='#3498db',
            style='--',
            width=2)
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
    
    def add_vertical_line(self):
        """Add vertical line annotation"""
        x_pos = 0
        if self.ax:
            xlim = self.ax.get_xlim()
            x_pos = (xlim[0] + xlim[1]) / 2
        
        ann_id = self.annotation_manager.add_annotation('vline',
            x_pos=x_pos,
            label="Vertical Line",
            color='#e74c3c',
            style='--',
            width=2)
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
    
    def add_region(self):
        """Add shaded region annotation"""
        x_start, x_end = 0, 1
        if self.ax:
            xlim = self.ax.get_xlim()
            span = xlim[1] - xlim[0]
            x_start = xlim[0] + span * 0.3
            x_end = xlim[0] + span * 0.7
        
        ann_id = self.annotation_manager.add_annotation('region',
            x_start=x_start,
            x_end=x_end,
            label="Region",
            color='#f39c12',
            alpha=0.3)
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
    
    def add_point(self):
        """Add point marker annotation"""
        x_pos, y_pos = 0, 0
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            x_pos = (xlim[0] + xlim[1]) / 2
            y_pos = (ylim[0] + ylim[1]) / 2
        
        ann_id = self.annotation_manager.add_annotation('point',
            x_pos=x_pos,
            y_pos=y_pos,
            label="Point",
            marker='o',
            size=100,
            color='#e74c3c')
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
    
    def add_text(self):
        """Add text annotation"""
        x_pos, y_pos = 0, 0
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            x_pos = xlim[0] + (xlim[1] - xlim[0]) * 0.1
            y_pos = ylim[1] - (ylim[1] - ylim[0]) * 0.1
        
        ann_id = self.annotation_manager.add_annotation('text',
            x_pos=x_pos,
            y_pos=y_pos,
            text="Annotation",
            fontsize=12,
            color='black',
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
    
    def add_enhanced_arrow(self):
        """Add enhanced arrow annotation with better defaults"""
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # Create arrow pointing from upper left to center
            x_start = xlim[0] + (xlim[1] - xlim[0]) * 0.2
            y_start = ylim[0] + (ylim[1] - ylim[0]) * 0.8
            x_end = xlim[0] + (xlim[1] - xlim[0]) * 0.5
            y_end = ylim[0] + (ylim[1] - ylim[0]) * 0.5
        else:
            x_start, y_start, x_end, y_end = 0, 1, 1, 0
        
        ann_id = self.annotation_manager.add_annotation('arrow',
            x_start=x_start,
            y_start=y_start,
            x_end=x_end,
            y_end=y_end,
            style='->',
            color='#2c3e50',
            width=2,
            label="Arrow")
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
    
    # Vacuum-specific templates
    def add_base_pressure_template(self):
        """Add base pressure line template"""
        if self.ax:
            ylim = self.ax.get_ylim()
            # Estimate base pressure as lower 10% of range
            base_pressure = ylim[0] + (ylim[1] - ylim[0]) * 0.1
        else:
            base_pressure = 1e-6
        
        ann_id = self.annotation_manager.add_annotation('hline',
            y_pos=base_pressure,
            label=f"Base Pressure: {base_pressure:.2e} mbar",
            color='green',
            style='--',
            width=2,
            alpha=0.8)
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
        
        messagebox.showinfo("Template Added", 
                          "Base pressure line added. Adjust the position to match your measured base pressure.")
    
    def add_noise_region_template(self):
        """Add noise analysis region template"""
        if self.ax:
            xlim = self.ax.get_xlim()
            # Create region in middle third
            span = xlim[1] - xlim[0]
            x_start = xlim[0] + span * 0.33
            x_end = xlim[0] + span * 0.67
        else:
            x_start, x_end = 100, 200
        
        ann_id = self.annotation_manager.add_annotation('region',
            x_start=x_start,
            x_end=x_end,
            label="Noise Analysis Region",
            color='purple',
            alpha=0.2)
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
        
        messagebox.showinfo("Template Added", 
                          "Noise analysis region added. Adjust to cover a stable pressure region.")
    
    def add_spike_marker_template(self):
        """Add spike marker template"""
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            x_pos = xlim[0] + (xlim[1] - xlim[0]) * 0.5
            y_pos = ylim[0] + (ylim[1] - ylim[0]) * 0.9
        else:
            x_pos, y_pos = 50, 1e-3
        
        ann_id = self.annotation_manager.add_annotation('point',
            x_pos=x_pos,
            y_pos=y_pos,
            label="Pressure Spike",
            marker='^',
            size=150,
            color='red')
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
        
        messagebox.showinfo("Template Added", 
                          "Spike marker added. Move to actual spike locations.")
    
    def add_pressure_targets_template(self):
        """Add common vacuum pressure target lines"""
        targets = [
            (1e-3, "High Vacuum", 'blue'),
            (1e-6, "Ultra-High Vacuum", 'green'),
            (1e-9, "Extreme High Vacuum", 'purple')
        ]
        
        added_count = 0
        for pressure, label, color in targets:
            # Only add if within current plot range
            if self.ax:
                ylim = self.ax.get_ylim()
                if ylim[0] <= pressure <= ylim[1]:
                    self.annotation_manager.add_annotation('hline',
                        y_pos=pressure,
                        label=f"{label}: {pressure:.0e} mbar",
                        color=color,
                        style=':',
                        width=1.5,
                        alpha=0.6)
                    added_count += 1
            else:
                self.annotation_manager.add_annotation('hline',
                    y_pos=pressure,
                    label=f"{label}: {pressure:.0e} mbar",
                    color=color,
                    style=':',
                    width=1.5,
                    alpha=0.6)
                added_count += 1
        
        self.update_annotation_list()
        self.refresh_plot()
        
        messagebox.showinfo("Template Added", 
                          f"Added {added_count} pressure target lines.")
    
    def setup_interactive_editing(self):
        """Set up interactive annotation editing on the plot"""
        self.selected_artist = None
        self.drag_start = None
        
        def on_pick(event):
            """Handle picking annotations on the plot"""
            if hasattr(event, 'artist') and self.figure:
                self.selected_artist = event.artist
                # Store original position for dragging
                if hasattr(event.artist, 'get_xydata'):
                    self.drag_start = event.artist.get_xydata()
                elif hasattr(event.artist, 'get_offsets'):
                    self.drag_start = event.artist.get_offsets()
        
        def on_motion(event):
            """Handle mouse motion for dragging annotations"""
            if self.selected_artist and event.inaxes and self.dragging:
                # Update annotation position based on type
                # This would need to be implemented based on annotation type
                pass
        
        def on_press(event):
            """Handle mouse press"""
            if self.selected_artist and event.inaxes:
                self.dragging = True
                self.drag_data = {'start_x': event.xdata, 'start_y': event.ydata}
        
        def on_release(event):
            """Handle mouse release after dragging"""
            self.dragging = False
            self.selected_artist = None
            self.drag_data = None
        
        # Connect event handlers
        if self.figure:
            self.figure.canvas.mpl_connect('pick_event', on_pick)
            self.figure.canvas.mpl_connect('motion_notify_event', on_motion)
            self.figure.canvas.mpl_connect('button_press_event', on_press)
            self.figure.canvas.mpl_connect('button_release_event', on_release)
    
    def clear_all(self):
        """Clear all annotations"""
        if self.annotation_manager.annotations:
            if messagebox.askyesno("Confirm", "Remove all annotations?"):
                self.annotation_manager.annotations.clear()
                self.update_annotation_list()
                self.refresh_plot()
    
    def export_annotations(self):
        """Export annotations to file"""
        filename = filedialog.asksaveasfilename(
            title="Export Annotations",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.annotation_manager.annotations, f, indent=2)
                messagebox.showinfo("Success", "Annotations exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def import_annotations(self):
        """Import annotations from file"""
        filename = filedialog.askopenfilename(
            title="Import Annotations",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    imported = json.load(f)
                
                # Merge with existing annotations
                for ann_id, annotation in imported.items():
                    if 'id' in annotation:
                        del annotation['id']
                    new_id = self.annotation_manager.add_annotation(
                        annotation['type'], **annotation)
                
                self.update_annotation_list()
                self.refresh_plot()
                messagebox.showinfo("Success", f"Imported {len(imported)} annotations!")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import: {str(e)}")
    
    def refresh_plot(self):
        """Refresh the plot with updated annotations"""
        if hasattr(self.parent, 'refresh_plot'):
            self.parent.refresh_plot()
    
    def apply_and_close(self):
        """Apply changes and close dialog"""
        self.refresh_plot()
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel and close dialog"""
        self.dialog.destroy()

class LivePreviewPanel:
    """Panel showing live preview of changes"""
    
    def __init__(self, parent, width=400, height=250):
        self.parent = parent
        self.width = width
        self.height = height
        
        self.create_panel()
    
    def create_panel(self):
        """Create the preview panel"""
        # Frame with border
        self.panel = tk.Frame(self.parent, bg='#ecf0f1', 
                            relief='solid', borderwidth=1)
        self.panel.pack(fill='both', expand=True)
        
        # Header
        header = tk.Frame(self.panel, bg='#34495e', height=30)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="Preview", font=('Segoe UI', 10, 'bold'),
                fg='white', bg='#34495e').pack(pady=5)
        
        # Canvas for preview
        self.fig = Figure(figsize=(self.width/100, self.height/100), 
                         facecolor='white', tight_layout=True)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.panel)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Status bar
        self.status_bar = tk.Label(self.panel, text="Ready", 
                                 font=('Segoe UI', 9), 
                                 bg='#bdc3c7', anchor='w')
        self.status_bar.pack(fill='x')
    
    def update_preview(self, x_data, y_data, settings=None, layers=None):
        """Update the preview with new data and settings"""
        self.ax.clear()
        
        # Basic plot
        if len(x_data) > 0 and len(y_data) > 0:
            # Sample data if too large
            if len(x_data) > 500:
                step = len(x_data) // 500
                x_sample = x_data[::step]
                y_sample = y_data[::step]
            else:
                x_sample = x_data
                y_sample = y_data
            
            # Apply settings if provided
            if settings:
                self.ax.plot(x_sample, y_sample, 
                           color=settings.get('color', '#3498db'),
                           linestyle=settings.get('line_style', '-'),
                           linewidth=settings.get('line_width', 2),
                           alpha=settings.get('alpha', 0.9))
                
                if settings.get('fill_area'):
                    self.ax.fill_between(x_sample, y_sample, 
                                       alpha=settings.get('alpha', 0.9) * 0.3,
                                       color=settings.get('color', '#3498db'))
            else:
                self.ax.plot(x_sample, y_sample)
            
            # Apply quality layers if provided
            if layers:
                for layer in layers:
                    if layer.visible:
                        # Simplified layer application for preview
                        if layer.issue_type == 'outliers':
                            # Show sample outliers
                            outlier_indices = np.random.choice(len(x_sample), 
                                                             size=min(5, len(x_sample)//20), 
                                                             replace=False)
                            self.ax.scatter(x_sample[outlier_indices], 
                                          y_sample[outlier_indices],
                                          s=80, facecolors='none', 
                                          edgecolors=layer.color_map['outliers'],
                                          linewidths=2)
            
            # Style
            self.ax.set_xlabel('X', fontsize=9)
            self.ax.set_ylabel('Y', fontsize=9)
            self.ax.tick_params(labelsize=8)
            self.ax.grid(True, alpha=0.3)
            
            # Update status
            self.status_bar.config(text=f"Preview: {len(x_sample)} points")
        else:
            self.ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                       transform=self.ax.transAxes, fontsize=12, color='gray')
            self.status_bar.config(text="No data to preview")
        
        self.canvas.draw()

class ProfessionalMultiFileExcelPlotter(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize modern UI settings
        self.title("Professional Multi-File Excel Data Plotter v4.2")
        self.geometry("1600x900")
        self.minsize(1200, 700)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Initialize variables
        self.loaded_files = {}
        self.all_series = {}
        self.figure = None
        self.canvas = None
        self.toolbar = None
        self.color_index = 0
        self.current_theme = ctk.get_appearance_mode()
        self.auto_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                           '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        # Initialize managers
        self.annotation_manager = ModernAnnotationManager()
        self.analysis_tools = DataAnalysisTools()
        self.vacuum_tools = VacuumAnalysisTools()
        
        # Initialize plot configuration variables
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
        self.margin_left_var = tk.DoubleVar(value=0.1)
        self.margin_right_var = tk.DoubleVar(value=0.05)
        self.margin_top_var = tk.DoubleVar(value=0.1)
        self.margin_bottom_var = tk.DoubleVar(value=0.1)
        self.plot_type_var = tk.StringVar(value="line")
        self.x_auto_scale = tk.BooleanVar(value=True)
        self.y_auto_scale = tk.BooleanVar(value=True)
        self.x_min_var = tk.StringVar(value="")
        self.x_max_var = tk.StringVar(value="")
        self.y_min_var = tk.StringVar(value="")
        self.y_max_var = tk.StringVar(value="")
        
        # Create UI
        self.create_ui()
        
        # Bind window events
        self.bind("<Configure>", self.on_window_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize status
        self.status_bar.set_status("Welcome to Professional Excel Data Plotter", "info")

    def create_ui(self):
        """Create the modern responsive UI"""
        # Main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_rowconfigure(1, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Top bar with quick actions
        self.create_top_bar()

        # Main content area with adaptive layout
        self.create_main_content()

        # Status bar
        self.status_bar = ModernStatusBar(self.main_container)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        # Floating panels (initially hidden)
        self.create_floating_panels()

    def create_top_bar(self):
        """Create the top action bar with rearranged buttons"""
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

        # Analysis actions (center)
        self.top_bar.add_action("Analysis", "🔬", self.show_analysis_panel, "Data analysis tools", side="center")
        self.top_bar.add_action("Vacuum Tools", "🎯", self.show_vacuum_analysis, "Vacuum analysis tools", side="center")
        self.top_bar.add_action("Annotations", "📍", self.show_annotation_panel, "Manage annotations", side="center")
        self.top_bar.add_separator(side="center")

        # View actions (center)
        self.top_bar.add_action("Theme", "🎨", self.toggle_theme, "Toggle dark/light theme", side="center")
        self.top_bar.add_action("Layout", "📐", self.cycle_layout, "Change layout mode", side="center")

    def create_main_content(self):
        """Create the main content area with adaptive layout"""
        self.content_frame = ctk.CTkFrame(self.main_container)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Determine initial layout based on window size
        self.current_layout = "default"  # default, compact, expanded
        self.create_default_layout()

    def create_default_layout(self):
        """Create the default layout with sidebar and main area"""
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
        self.sidebar_tabs = ModernTabbedPanel(self.sidebar, width=390, height=800)
        self.sidebar_tabs.pack(fill="both", expand=True)

        # Create tabs - Professional features
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

    def create_compact_layout(self):
        """Create compact layout for smaller screens"""
        # Clear existing widgets
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        # Single tabbed interface
        self.main_tabs = ModernTabbedPanel(self.content_frame)
        self.main_tabs.grid(row=0, column=0, sticky="nsew")

        # Create tabs
        self.files_tab = self.main_tabs.add("Files")
        self.series_tab = self.main_tabs.add("Series")
        self.plot_tab = self.main_tabs.add("Plot")
        self.config_tab = self.main_tabs.add("Config")
        self.export_tab = self.main_tabs.add("Export")

        self.create_files_panel()
        self.create_series_panel()
        self.create_plot_area_compact()
        self.create_config_panel()
        self.create_export_panel()

    def create_files_panel(self):
        """Create the files management panel"""
        # Search bar
        self.file_search = ModernSearchBar(
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
        """Create the series management panel with professional features"""
        # Series creation section
        create_frame = CollapsiblePanel(self.series_tab, "Create New Series", start_collapsed=False)
        create_frame.pack(fill="x", padx=10, pady=(10, 5))

        content = create_frame.get_content_frame()

        # File selection
        ctk.CTkLabel(content, text="Source File:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.series_file_var = tk.StringVar()
        self.series_file_combo = ctk.CTkComboBox(
            content,
            variable=self.series_file_var,
            command=self.on_file_selected_for_series,
            width=200
        )
        self.series_file_combo.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        # Advanced data selection button
        self.data_select_btn = ctk.CTkButton(
            content,
            text="Advanced Selection",
            command=self.show_advanced_data_selector,
            width=120
        )
        self.data_select_btn.grid(row=0, column=3, padx=5, pady=5)

        # Column selection
        ctk.CTkLabel(content, text="X Column:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.series_x_var = tk.StringVar()
        self.series_x_combo = ctk.CTkComboBox(content, variable=self.series_x_var, width=120,
                                             command=lambda x: self.update_series_range_limits())
        self.series_x_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(content, text="Y Column:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.series_y_var = tk.StringVar()
        self.series_y_combo = ctk.CTkComboBox(content, variable=self.series_y_var, width=120,
                                             command=lambda x: self.update_series_range_limits())
        self.series_y_combo.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        # Range selection with dynamic limits
        ctk.CTkLabel(content, text="Start:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.series_start_var = tk.IntVar(value=0)
        self.series_start_entry = ctk.CTkEntry(content, textvariable=self.series_start_var, width=80)
        self.series_start_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(content, text="End:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.series_end_var = tk.IntVar(value=1000)
        self.series_end_entry = ctk.CTkEntry(content, textvariable=self.series_end_var, width=80)
        self.series_end_entry.grid(row=2, column=3, sticky="w", padx=5, pady=5)

        # Range info label
        self.range_info_label = ctk.CTkLabel(content, text="", text_color=("gray60", "gray40"))
        self.range_info_label.grid(row=3, column=0, columnspan=4, pady=5)

        # Series name
        ctk.CTkLabel(content, text="Name:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.series_name_var = tk.StringVar(value="New Series")
        self.series_name_entry = ctk.CTkEntry(content, textvariable=self.series_name_var, width=200)
        self.series_name_entry.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        ctk.CTkButton(
            content,
            text="Add Series",
            command=self.add_series,
            fg_color=ColorPalette.SUCCESS
        ).grid(row=4, column=3, padx=5, pady=5)

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
        """Create the configuration panel with professional features"""
        # Plot configuration sections
        sections = [
            ("Plot Settings", self.create_plot_settings),
            ("Axis Configuration", self.create_axis_config),
            ("Visual Style", self.create_visual_style),
            ("Advanced Options", self.create_advanced_options)
        ]

        for title, create_func in sections:
            panel = CollapsiblePanel(self.config_tab, title, start_collapsed=True)
            panel.pack(fill="x", padx=10, pady=5)
            create_func(panel.get_content_frame())

    def create_plot_settings(self, parent):
        """Create plot settings controls with professional options"""
        # Plot type
        ctk.CTkLabel(parent, text="Plot Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        plot_types = ["line", "scatter", "bar", "area", "box", "heatmap"]

        plot_type_frame = ctk.CTkFrame(parent, fg_color="transparent")
        plot_type_frame.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        
        for i, ptype in enumerate(plot_types):
            ctk.CTkRadioButton(
                plot_type_frame,
                text=ptype.capitalize(),
                variable=self.plot_type_var,
                value=ptype
            ).pack(side="left", padx=5, pady=5)

        # Figure size
        ctk.CTkLabel(parent, text="Figure Size:").grid(row=1, column=0, sticky="w", padx=5, pady=5)

        size_frame = ctk.CTkFrame(parent, fg_color="transparent")
        size_frame.grid(row=1, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(size_frame, text="W:").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(size_frame, textvariable=self.fig_width_var, width=60).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(size_frame, text="H:").pack(side="left", padx=(0, 5))
        ctk.CTkEntry(size_frame, textvariable=self.fig_height_var, width=60).pack(side="left")

        # Margins
        ctk.CTkLabel(parent, text="Margins:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        margin_frame = ctk.CTkFrame(parent, fg_color="transparent")
        margin_frame.grid(row=2, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        
        ctk.CTkLabel(margin_frame, text="Left:").pack(side="left", padx=2)
        ctk.CTkSlider(margin_frame, from_=0.05, to=0.3, variable=self.margin_left_var, 
                     width=80).pack(side="left", padx=2)
        
        ctk.CTkLabel(margin_frame, text="Right:").pack(side="left", padx=2)
        ctk.CTkSlider(margin_frame, from_=0.02, to=0.2, variable=self.margin_right_var, 
                     width=80).pack(side="left", padx=2)
        
        ctk.CTkLabel(margin_frame, text="Top:").pack(side="left", padx=2)
        ctk.CTkSlider(margin_frame, from_=0.05, to=0.25, variable=self.margin_top_var, 
                     width=80).pack(side="left", padx=2)
        
        ctk.CTkLabel(margin_frame, text="Bottom:").pack(side="left", padx=2)
        ctk.CTkSlider(margin_frame, from_=0.05, to=0.25, variable=self.margin_bottom_var, 
                     width=80).pack(side="left", padx=2)

    def create_axis_config(self, parent):
        """Create axis configuration controls with professional features"""
        # Title
        ctk.CTkLabel(parent, text="Title:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.title_var, width=300).grid(row=0, column=1, columnspan=3, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(parent, text="Title Size:").grid(row=0, column=4, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.title_size_var, width=60).grid(row=0, column=5, padx=5, pady=5)

        # X-axis
        ctk.CTkLabel(parent, text="X Label:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.xlabel_var, width=140).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(parent, text="X Label Size:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.xlabel_size_var, width=60).grid(row=1, column=3, padx=5, pady=5)

        ctk.CTkCheckBox(parent, text="Log Scale", variable=self.log_scale_x_var).grid(row=1, column=4, padx=5, pady=5)

        # Y-axis
        ctk.CTkLabel(parent, text="Y Label:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.ylabel_var, width=140).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(parent, text="Y Label Size:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkEntry(parent, textvariable=self.ylabel_size_var, width=60).grid(row=2, column=3, padx=5, pady=5)

        ctk.CTkCheckBox(parent, text="Log Scale", variable=self.log_scale_y_var).grid(row=2, column=4, padx=5, pady=5)

        parent.grid_columnconfigure(1, weight=1)

    def create_visual_style(self, parent):
        """Create visual style controls with professional options"""
        # Grid style
        ctk.CTkLabel(parent, text="Grid Style:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.grid_style_combo = ctk.CTkComboBox(
            parent,
            variable=self.grid_style_var,
            values=["-", "--", ":", "-."],
            width=100
        )
        self.grid_style_combo.grid(row=0, column=1, padx=5, pady=5)

        # Grid alpha
        ctk.CTkLabel(parent, text="Grid Alpha:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ctk.CTkSlider(
            parent,
            from_=0.1,
            to=1.0,
            variable=self.grid_alpha_var,
            width=150
        ).grid(row=0, column=3, padx=5, pady=5)

        # Show grid
        ctk.CTkCheckBox(parent, text="Show Grid", variable=self.show_grid_var).grid(row=1, column=0, sticky="w", padx=5, pady=5)

        # Show legend
        ctk.CTkCheckBox(parent, text="Show Legend", variable=self.show_legend_var).grid(row=1, column=1, sticky="w", padx=5, pady=5)

    def create_advanced_options(self, parent):
        """Create advanced options section"""
        # X-axis auto scale
        ctk.CTkCheckBox(parent, text="Auto X Scale", variable=self.x_auto_scale,
                       command=self.toggle_x_manual_limits).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # X-axis manual limits
        ctk.CTkLabel(parent, text="X Min:").grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.x_min_entry = ctk.CTkEntry(parent, textvariable=self.x_min_var, width=80, state="disabled")
        self.x_min_entry.grid(row=0, column=2, padx=5, pady=5)

        ctk.CTkLabel(parent, text="X Max:").grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.x_max_entry = ctk.CTkEntry(parent, textvariable=self.x_max_var, width=80, state="disabled")
        self.x_max_entry.grid(row=0, column=4, padx=5, pady=5)

        # Y-axis auto scale
        ctk.CTkCheckBox(parent, text="Auto Y Scale", variable=self.y_auto_scale,
                       command=self.toggle_y_manual_limits).grid(row=1, column=0, sticky="w", padx=5, pady=5)

        # Y-axis manual limits
        ctk.CTkLabel(parent, text="Y Min:").grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.y_min_entry = ctk.CTkEntry(parent, textvariable=self.y_min_var, width=80, state="disabled")
        self.y_min_entry.grid(row=1, column=2, padx=5, pady=5)

        ctk.CTkLabel(parent, text="Y Max:").grid(row=1, column=3, sticky="w", padx=5, pady=5)
        self.y_max_entry = ctk.CTkEntry(parent, textvariable=self.y_max_var, width=80, state="disabled")
        self.y_max_entry.grid(row=1, column=4, padx=5, pady=5)

    def toggle_x_manual_limits(self):
        """Toggle X-axis manual limit entry fields"""
        state = "normal" if not self.x_auto_scale.get() else "disabled"
        self.x_min_entry.configure(state=state)
        self.x_max_entry.configure(state=state)

    def toggle_y_manual_limits(self):
        """Toggle Y-axis manual limit entry fields"""
        state = "normal" if not self.y_auto_scale.get() else "disabled"
        self.y_min_entry.configure(state=state)
        self.y_max_entry.configure(state=state)

    def create_export_panel(self):
        """Create export panel with professional options"""
        # Export options
        export_frame = ctk.CTkFrame(self.export_tab)
        export_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Image format
        ctk.CTkLabel(export_frame, text="Image Format:").pack(anchor="w", pady=2)
        self.export_format = ctk.CTkComboBox(export_frame, width=200,
                                           values=['PNG (High Quality)', 'PDF (Vector)', 'SVG (Scalable)', 'JPG (Compressed)'])
        self.export_format.set('PNG (High Quality)')
        self.export_format.pack(fill="x", pady=2)

        # Resolution
        ctk.CTkLabel(export_frame, text="Resolution (DPI):").pack(anchor="w", pady=2)
        
        dpi_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        dpi_frame.pack(fill="x", pady=2)
        
        self.dpi_var = tk.IntVar(value=300)
        for dpi in [150, 300, 600, 1200]:
            ctk.CTkRadioButton(dpi_frame, text=str(dpi), variable=self.dpi_var, 
                             value=dpi).pack(side="left", padx=10)

        # Export buttons
        ctk.CTkButton(export_frame, text="Export Plot", command=self.export_plot,
                     fg_color=ColorPalette.SUCCESS).pack(fill="x", pady=10)
        ctk.CTkButton(export_frame, text="Export All Data", command=self.export_all_data,
                     fg_color=ColorPalette.SECONDARY).pack(fill="x", pady=2)
        ctk.CTkButton(export_frame, text="Export Series Config", command=self.export_series_config,
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

    def create_plot_area_compact(self):
        """Create plot area for compact layout"""
        self.plot_container = ctk.CTkFrame(self.plot_tab)
        self.plot_container.pack(fill="both", expand=True, padx=10, pady=10)

    def create_floating_panels(self):
        """Create floating panels for analysis and annotations"""
        # Analysis panel
        self.analysis_panel = FloatingPanel(self, "Data Analysis", 600, 700)
        self.analysis_panel.withdraw()

        # Annotation panel
        self.annotation_panel = FloatingPanel(self, "Annotations", 500, 600)
        self.annotation_panel.withdraw()

    # ====================== Professional Methods ======================

    def show_advanced_data_selector(self):
        """Show advanced data selector for non-standard Excel layouts"""
        if not self.series_file_var.get():
            self.status_bar.set_status("Please select a source file first", "warning")
            return
        
        # Find the selected file
        selection = self.series_file_var.get()
        file_id = selection.split('(')[-1].rstrip(')')
        matching_file = None
        for fid, fdata in self.loaded_files.items():
            if fid.startswith(file_id):
                matching_file = fdata
                break
        
        if not matching_file:
            return
        
        # Create selector dialog
        selector_dialog = ctk.CTkToplevel(self)
        selector_dialog.title("Advanced Data Selection")
        selector_dialog.geometry("800x600")
        selector_dialog.transient(self)
        selector_dialog.grab_set()
        
        # Create the selector
        selector = ImprovedDataSelector(
            selector_dialog, 
            matching_file,
            on_data_selected=lambda info: self.apply_advanced_selection(info, selector_dialog)
        )
        selector.pack(fill="both", expand=True)

    def apply_advanced_selection(self, selection_info, dialog):
        """Apply the advanced data selection"""
        try:
            # Update column combos based on selection
            header_row = selection_info['header_row']
            selected_columns = selection_info['selected_columns']
            
            # Update the series configuration
            self.series_start_var.set(selection_info['start_row'])
            self.series_end_var.set(selection_info['end_row'])
            
            # Close dialog
            dialog.destroy()
            
            self.status_bar.set_status("Advanced selection applied", "success")
            
        except Exception as e:
            self.status_bar.set_status(f"Selection error: {str(e)}", "error")

    def update_series_range_limits(self):
        """Update the range limits based on selected columns"""
        selection = self.series_file_var.get()
        if not selection:
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
            
            if matching_file:
                # Get selected columns
                x_col = self.series_x_combo.get()
                y_col = self.series_y_combo.get()
                
                if x_col and y_col:
                    # Determine valid data range
                    df = matching_file.df
                    max_rows = len(df)
                    
                    # Check for non-null data in selected columns
                    if x_col != 'Index' and x_col in df.columns:
                        x_valid = df[x_col].notna()
                    else:
                        x_valid = pd.Series([True] * len(df))
                    
                    if y_col in df.columns:
                        y_valid = df[y_col].notna()
                    else:
                        y_valid = pd.Series([True] * len(df))
                    
                    # Find first and last valid indices
                    valid_mask = x_valid & y_valid
                    if valid_mask.any():
                        valid_indices = valid_mask[valid_mask].index
                        first_valid = valid_indices[0]
                        last_valid = valid_indices[-1]
                        
                        # Update range info
                        self.range_info_label.configure(
                            text=f"Valid data range: {first_valid} to {last_valid} ({len(valid_indices)} points)"
                        )
                        
                        # Set default range to include all valid data
                        if self.series_start_var.get() == 0 or self.series_start_var.get() > last_valid:
                            self.series_start_var.set(first_valid)
                        if self.series_end_var.get() > last_valid or self.series_end_var.get() < first_valid:
                            self.series_end_var.set(min(last_valid + 1, max_rows))
                    else:
                        self.range_info_label.configure(text="No valid data in selected columns")
                else:
                    self.range_info_label.configure(text="Select both X and Y columns")
                    
        except Exception as e:
            print(f"Range update error: {e}")
            self.range_info_label.configure(text="")

    def detect_datetime_column(self, data_series):
        """Detect if a data series could be datetime without converting it"""
        try:
            # Skip if already datetime
            if pd.api.types.is_datetime64_any_dtype(data_series):
                return True
                
            # Sample a few rows to test
            sample = data_series.dropna().head(20)
            if len(sample) == 0:
                return False
                
            # Try to convert sample to datetime
            converted = pd.to_datetime(sample, errors='coerce', infer_datetime_format=True)
            
            # If most values converted successfully, it's likely datetime
            success_rate = converted.notna().sum() / len(sample)
            return success_rate > 0.8
            
        except Exception:
            return False

    def convert_to_datetime_for_plotting(self, data_series):
        """Convert data series to datetime only for plotting purposes"""
        try:
            if pd.api.types.is_datetime64_any_dtype(data_series):
                return data_series
                
            # Try to convert to datetime
            converted = pd.to_datetime(data_series, errors='coerce', infer_datetime_format=True)
            
            # Return converted if successful, otherwise return original
            if converted.notna().sum() / len(data_series.dropna()) > 0.8:
                return converted
            else:
                return data_series
                
        except Exception:
            return data_series

    def reload_all_files(self):
        """Reload all loaded files"""
        if not self.loaded_files:
            self.status_bar.set_status("No files to reload", "warning")
            return
        
        # Create confirmation dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Reload")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 200) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Message
        ctk.CTkLabel(
            dialog,
            text="Reload all files?",
            font=("", 16, "bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            dialog,
            text="This will reset any unsaved changes.",
            text_color=ColorPalette.WARNING
        ).pack(pady=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            fg_color="gray50"
        ).pack(side="left", padx=10)
        
        def confirm_reload():
            file_paths = [file_data.filepath for file_data in self.loaded_files.values()]
            self.clear_all_files()
            
            # Reload files
            success_count = 0
            for filepath in file_paths:
                try:
                    if filepath.endswith('.csv'):
                        df = pd.read_csv(filepath)
                    else:
                        df = pd.read_excel(filepath)
                    
                    file_data = FileData(filepath, df)
                    self.loaded_files[file_data.id] = file_data
                    success_count += 1
                except Exception as e:
                    print(f"Error reloading {filepath}: {e}")
            
            self.update_files_display()
            self.update_series_file_combo()
            self.update_counts()
            dialog.destroy()
            
            if success_count > 0:
                self.status_bar.set_status(f"Reloaded {success_count} files", "success")
            else:
                self.status_bar.set_status("Failed to reload any files", "error")
        
        ctk.CTkButton(
            btn_frame,
            text="Reload",
            command=confirm_reload,
            fg_color=ColorPalette.PRIMARY
        ).pack(side="left", padx=10)

    def update_counts(self):
        """Update file and series counts in status bar"""
        file_count = len(self.loaded_files)
        series_count = len(self.all_series)
        self.status_bar.update_counts(files=file_count, series=series_count)

    def save_project(self):
        """Save the current project state"""
        filename = filedialog.asksaveasfilename(
            title="Save Project",
            defaultextension=".json",
            filetypes=[("Project files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                project_data = {
                    'version': '1.0',
                    'creation_date': datetime.now().isoformat(),
                    'files': [],
                    'series': [],
                    'plot_config': {
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
                        'fig_height': self.fig_height_var.get(),
                        'plot_type': self.plot_type_var.get()
                    }
                }
                
                # Save file references
                for file_id, file_data in self.loaded_files.items():
                    project_data['files'].append({
                        'id': file_id,
                        'filepath': file_data.filepath,
                        'filename': file_data.filename
                    })
                
                # Save series configurations
                for series_id, series in self.all_series.items():
                    project_data['series'].append({
                        'id': series_id,
                        'name': series.name,
                        'file_id': series.file_id,
                        'x_column': series.x_column,
                        'y_column': series.y_column,
                        'start_index': series.start_index,
                        'end_index': series.end_index,
                        'color': series.color,
                        'line_style': series.line_style,
                        'marker': series.marker,
                        'line_width': series.line_width,
                        'marker_size': series.marker_size,
                        'alpha': series.alpha,
                        'fill_area': series.fill_area,
                        'visible': series.visible,
                        'legend_label': series.legend_label,
                        'missing_data_method': series.missing_data_method,
                        'show_trendline': series.show_trendline,
                        'trend_type': series.trend_type,
                        'trend_params': series.trend_params
                    })
                
                with open(filename, 'w') as f:
                    json.dump(project_data, f, indent=2)
                
                self.status_bar.set_status(f"Project saved to: {filename}", "success")
                
            except Exception as e:
                self.status_bar.set_status(f"Save failed: {str(e)}", "error")

    def load_project(self):
        """Load a saved project"""
        filename = filedialog.askopenfilename(
            title="Load Project",
            filetypes=[("Project files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    project_data = json.load(f)
                
                # Clear existing data
                self.clear_all_files()
                
                # Load files
                file_mapping = {}  # Map old IDs to new IDs
                for file_info in project_data['files']:
                    try:
                        filepath = file_info['filepath']
                        if os.path.exists(filepath):
                            if filepath.endswith('.csv'):
                                df = pd.read_csv(filepath)
                            else:
                                df = pd.read_excel(filepath)
                            
                            file_data = FileData(filepath, df)
                            self.loaded_files[file_data.id] = file_data
                            file_mapping[file_info['id']] = file_data.id
                        else:
                            self.status_bar.set_status(f"File not found: {filepath}", "warning")
                    except Exception as e:
                        print(f"Error loading file {filepath}: {e}")
                
                # Load series
                for series_info in project_data['series']:
                    try:
                        # Map old file ID to new one
                        old_file_id = series_info['file_id']
                        if old_file_id in file_mapping:
                            new_file_id = file_mapping[old_file_id]
                            
                            # Create series
                            series = ModernSeriesConfig(
                                series_info['name'],
                                new_file_id,
                                series_info['x_column'],
                                series_info['y_column'],
                                series_info['start_index'],
                                series_info['end_index']
                            )
                            
                            # Apply saved properties
                            for prop in ['color', 'line_style', 'marker', 'line_width', 
                                        'marker_size', 'alpha', 'fill_area', 'visible', 
                                        'legend_label', 'missing_data_method', 'show_trendline',
                                        'trend_type', 'trend_params']:
                                if prop in series_info:
                                    setattr(series, prop, series_info[prop])
                            
                            self.all_series[series.id] = series
                            self.loaded_files[new_file_id].series_list.append(series.id)
                            
                    except Exception as e:
                        print(f"Error loading series: {e}")
                
                # Load plot configuration
                if 'plot_config' in project_data:
                    config = project_data['plot_config']
                    self.title_var.set(config.get('title', 'Multi-File Data Analysis'))
                    self.title_size_var.set(config.get('title_size', 16))
                    self.xlabel_var.set(config.get('xlabel', 'X Axis'))
                    self.xlabel_size_var.set(config.get('xlabel_size', 12))
                    self.ylabel_var.set(config.get('ylabel', 'Y Axis'))
                    self.ylabel_size_var.set(config.get('ylabel_size', 12))
                    self.log_scale_x_var.set(config.get('log_scale_x', False))
                    self.log_scale_y_var.set(config.get('log_scale_y', False))
                    self.show_grid_var.set(config.get('show_grid', True))
                    self.show_legend_var.set(config.get('show_legend', True))
                    self.grid_style_var.set(config.get('grid_style', '-'))
                    self.grid_alpha_var.set(config.get('grid_alpha', 0.3))
                    self.fig_width_var.set(config.get('fig_width', 14.0))
                    self.fig_height_var.set(config.get('fig_height', 9.0))
                    self.plot_type_var.set(config.get('plot_type', 'line'))
                
                # Update displays
                self.update_files_display()
                self.update_series_display()
                self.update_series_file_combo()
                self.update_counts()
                
                self.status_bar.set_status(f"Project loaded from: {filename}", "success")
                
            except Exception as e:
                self.status_bar.set_status(f"Load failed: {str(e)}", "error")

    def show_vacuum_analysis(self):
        """Show vacuum-specific analysis tools"""
        if self.all_series:
            # Create vacuum analysis dialog
            vacuum_dialog = VacuumAnalysisDialog(self, None, self.all_series, self.loaded_files)
            self.status_bar.set_status("Vacuum analysis tools opened", "info")
        else:
            self.status_bar.set_status("No series available for analysis", "warning")

    # ====================== Combined Methods ======================
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
                    # Update progress
                    progress = (i + 1) / len(filenames)
                    self.status_bar.show_progress(progress)
                    self.status_bar.set_status(f"Loading: {os.path.basename(filename)}", "info")

                    # Load file
                    if filename.endswith('.csv'):
                        df = pd.read_csv(filename)
                    else:
                        df = pd.read_excel(filename)

                    # Create FileData object
                    file_data = FileData(filename, df)
                    self.loaded_files[file_data.id] = file_data

                    success_count += 1

                except Exception as e:
                    error_files.append((filename, str(e)))

            # Update UI
            self.update_files_display()
            self.update_series_file_combo()
            self.status_bar.hide_progress()

            # Update counts
            self.update_counts()

            # Show results
            if success_count > 0:
                self.status_bar.set_status(f"Successfully loaded {success_count} file(s)", "success")
                if error_files:
                    self.show_error_details(error_files)
            else:
                self.status_bar.set_status("Failed to load any files", "error")

    def clear_all_files(self):
        """Clear all loaded files and series"""
        if self.loaded_files:
            # Create confirmation dialog
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Clear All")
            dialog.geometry("400x200")
            dialog.transient(self)
            dialog.grab_set()

            # Center the dialog
            dialog.update()
            x = (dialog.winfo_screenwidth() - 400) // 2
            y = (dialog.winfo_screenheight() - 200) // 2
            dialog.geometry(f"+{x}+{y}")

            # Message
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

            # Buttons
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

                self.update_files_display()
                self.update_series_display()
                self.update_series_file_combo()
                self.clear_plot_area()

                self.update_counts()
                self.status_bar.set_status("All files and series cleared", "info")

                dialog.destroy()

            ctk.CTkButton(
                btn_frame,
                text="Clear All",
                command=confirm_clear,
                fg_color=ColorPalette.ERROR
            ).pack(side="left", padx=10)

    def search_files(self, query):
        """Search files by name"""
        query = query.lower()
        for widget in self.files_scroll.winfo_children():
            if isinstance(widget, ModernFileCard):
                if query in widget.file_data.filename.lower():
                    widget.pack(fill="x", pady=5)
                else:
                    widget.pack_forget()

    def update_files_display(self):
        """Update the files display with modern cards"""
        # Clear existing widgets
        for widget in self.files_scroll.winfo_children():
            widget.destroy()

        # Add file cards
        for file_data in self.loaded_files.values():
            card = ModernFileCard(
                self.files_scroll,
                file_data,
                on_remove=self.remove_file,
                on_view=self.view_file_data
            )
            card.pack(fill="x", pady=5)

    def remove_file(self, file_data):
        """Remove a file and its associated series"""
        # Check for associated series
        series_count = len(file_data.series_list)

        if series_count > 0:
            # Show confirmation dialog
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Remove")
            dialog.geometry("400x200")
            dialog.transient(self)
            dialog.grab_set()

            # Center the dialog
            x = (self.winfo_screenwidth() - 400) // 2
            y = (self.winfo_screenheight() - 200) // 2
            dialog.geometry(f"+{x}+{y}")

            # Message
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

            # Buttons
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
                for series_id in file_data.series_list.copy():
                    if series_id in self.all_series:
                        del self.all_series[series_id]

                # Remove file
                del self.loaded_files[file_data.id]

                # Update displays
                self.update_files_display()
                self.update_series_display()
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
            # No series associated, just remove
            del self.loaded_files[file_data.id]
            self.update_files_display()
            self.update_counts()
            self.status_bar.set_status(f"Removed file: {file_data.filename}", "info")

    def view_file_data(self, file_data):
        """View file data in a modern data viewer"""
        viewer = ctk.CTkToplevel(self)
        viewer.title(f"Data Viewer - {file_data.filename}")
        viewer.geometry("900x600")
        viewer.transient(self)

        # Create viewer content
        viewer_frame = ctk.CTkFrame(viewer)
        viewer_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Info bar
        info_frame = ctk.CTkFrame(viewer_frame)
        info_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            info_frame,
            text=f"Rows: {len(file_data.df):,} | Columns: {len(file_data.df.columns)}",
            font=("", 12)
        ).pack(side="left", padx=10)

        # Export button
        ctk.CTkButton(
            info_frame,
            text="Export Data",
            command=lambda: self.export_dataframe(file_data.df, file_data.filename),
            width=100
        ).pack(side="right", padx=10)

        # Create text widget for data display
        text_frame = ctk.CTkFrame(viewer_frame)
        text_frame.pack(fill="both", expand=True)

        text_widget = ctk.CTkTextbox(text_frame, font=("Consolas", 10))
        
        # Display data (first 1000 rows)
        display_df = file_data.df.head(1000)
        text_widget.insert("1.0", display_df.to_string())
        text_widget.configure(state="disabled")
        
        text_widget.pack(fill="both", expand=True)

        # Status
        status_label = ctk.CTkLabel(
            viewer_frame,
            text=f"Showing first {min(1000, len(file_data.df))} rows",
            text_color=("gray60", "gray40")
        )
        status_label.pack(pady=5)

    def update_series_file_combo(self):
        """Update the file selection combo for series creation"""
        file_options = [f"{fd.filename} ({fd.id[:8]})" for fd in self.loaded_files.values()]

        if hasattr(self, 'series_file_combo'):
            self.series_file_combo.configure(values=file_options)
            if file_options and not self.series_file_var.get():
                self.series_file_combo.set(file_options[0])
                self.on_file_selected_for_series()

    def on_file_selected_for_series(self, choice=None):
        """Handle file selection for series creation"""
        selection = self.series_file_var.get()
        if not selection:
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

            if matching_file:
                # Get actual column names and convert to strings
                actual_columns = matching_file.df.columns.tolist()
                columns = [str(col) for col in actual_columns]

                # Update column combos
                self.series_x_combo.configure(values=['Index'] + columns)
                self.series_y_combo.configure(values=columns)

                # Update range limits
                max_rows = len(matching_file.df)
                self.series_end_var.set(min(1000, max_rows))

                # Auto-select columns
                if columns:
                    self.series_x_combo.set('Index')
                    # Select first numeric column for Y
                    numeric_cols = []
                    for col in actual_columns:
                        try:
                            if pd.api.types.is_numeric_dtype(matching_file.df[col]):
                                numeric_cols.append(str(col))
                        except:
                            pass
                    
                    if numeric_cols:
                        self.series_y_combo.set(numeric_cols[0])
                
                # Update range limits
                self.update_series_range_limits()
        
        except Exception as e:
            print(f"File selection error: {e}")
            self.status_bar.set_status(f"File selection error: {str(e)}", "error")

    def add_series(self):
        """Add a new data series"""
        # Validate inputs
        selection = self.series_file_var.get()
        if not selection:
            self.status_bar.set_status("Please select a source file", "warning")
            return

        x_col = self.series_x_combo.get()
        y_col = self.series_y_combo.get()

        if not x_col or not y_col:
            self.status_bar.set_status("Please select both X and Y columns", "warning")
            return

        # Find file
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

        # Get range
        start_idx = self.series_start_var.get()
        end_idx = self.series_end_var.get()

        if start_idx >= end_idx:
            self.status_bar.set_status("Start index must be less than end index", "warning")
            return

        # Create series
        series_name = self.series_name_var.get()
        series = ModernSeriesConfig(series_name, matching_file_id, x_col, y_col, start_idx, end_idx)

        # Auto-assign color
        series.color = self.auto_colors[self.color_index % len(self.auto_colors)]
        self.color_index += 1

        # Add to collections
        self.all_series[series.id] = series
        matching_file.series_list.append(series.id)

        # Update displays
        self.update_series_display()
        self.update_counts()

        # Generate next series name
        self.series_name_var.set(f"Series {len(self.all_series) + 1}")

        self.status_bar.set_status(f"Added series: {series_name}", "success")

    def update_series_display(self):
        """Update the series display with modern cards"""
        # Clear existing widgets
        for widget in self.series_scroll.winfo_children():
            widget.destroy()

        # Add series cards
        for series in self.all_series.values():
            file_data = self.loaded_files.get(series.file_id)
            if file_data:
                card = ModernSeriesCard(
                    self.series_scroll,
                    series,
                    file_data,
                    on_configure=self.configure_series,
                    on_toggle=self.toggle_series_visibility,
                    on_remove=self.remove_series
                )
                card.pack(fill="x", pady=5)

    def configure_series(self, series):
        """Open series configuration dialog"""
        # Create modern configuration dialog
        dialog = ModernSeriesConfigDialog(self, series, self.loaded_files[series.file_id])
        self.wait_window(dialog.top)
        
        if dialog.result == "apply":
            self.update_series_display()
            self.status_bar.set_status(f"Configured series: {series.name}", "success")

    def toggle_series_visibility(self, series):
        """Toggle series visibility"""
        series.visible = not series.visible
        self.status_bar.set_status(f"Series '{series.name}' {'shown' if series.visible else 'hidden'}", "info")

    def remove_series(self, series):
        """Remove a series"""
        # Remove from file's series list
        if series.file_id in self.loaded_files:
            file_data = self.loaded_files[series.file_id]
            if series.id in file_data.series_list:
                file_data.series_list.remove(series.id)

        # Remove from main collection
        del self.all_series[series.id]

        # Update displays
        self.update_series_display()
        self.update_counts()
        self.status_bar.set_status(f"Removed series: {series.name}", "info")

    def clear_plot_area(self):
        """Clear the plot area and show empty state"""
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        if hasattr(self, 'toolbar') and self.toolbar:
            self.toolbar.destroy()
            self.toolbar = None

        self.empty_plot_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

    def create_plot(self):
        """Create the plot with modern styling and professional features"""
        if not self.all_series:
            self.status_bar.set_status("No series defined. Please add at least one series.", "warning")
            return

        # Filter visible series
        visible_series = [s for s in self.all_series.values() if s.visible]
        if not visible_series:
            self.status_bar.set_status("No visible series. Please make at least one series visible.", "warning")
            return

        try:
            self.status_bar.set_status("Generating plot...", "info")
            self.status_bar.show_progress()

            # Remove empty state
            self.empty_plot_frame.grid_forget()

            # Clear previous plot
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            if self.toolbar:
                self.toolbar.destroy()

            # Create figure with modern styling
            fig_width = self.fig_width_var.get()
            fig_height = self.fig_height_var.get()

            # Apply appropriate style based on theme
            if self.current_theme == "dark":
                plt.style.use('dark_background')
            else:
                plt.style.use('seaborn-v0_8-whitegrid')

            self.figure = Figure(figsize=(fig_width, fig_height), facecolor='white', dpi=100)
            ax = self.figure.add_subplot(111)

            plot_type = self.plot_type_var.get()

            # Plot each visible series
            for i, series in enumerate(visible_series):
                self.status_bar.show_progress((i + 1) / len(visible_series))

                file_data = self.loaded_files.get(series.file_id)
                if not file_data:
                    continue

                try:
                    self.plot_single_series(ax, series, file_data, plot_type)
                except Exception as e:
                    print(f"Error plotting series {series.name}: {e}")
                    continue

            # Configure axes and styling
            self.configure_plot_axes(ax)

            # Draw annotations
            self.annotation_manager.draw_annotations(ax)

            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

            # Create toolbar frame
            toolbar_frame = ctk.CTkFrame(self.plot_frame, height=40)
            toolbar_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
            toolbar_frame.grid_propagate(False)

            # Add matplotlib toolbar
            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()

            self.status_bar.hide_progress()
            self.status_bar.set_status("Plot created successfully", "success")

        except Exception as e:
            self.status_bar.hide_progress()
            self.status_bar.set_status(f"Failed to create plot: {str(e)}", "error")
            import traceback
            traceback.print_exc()

    def plot_single_series(self, ax, series, file_data, plot_type):
        """Plot a single data series with professional features"""
        # Get data range
        start_idx = max(0, series.start_index)
        end_idx = min(len(file_data.df), series.end_index or len(file_data.df))
        
        if start_idx >= end_idx:
            return
            
        # Extract data
        data_slice = file_data.df.iloc[start_idx:end_idx].copy()
        
        # Prepare X data
        if series.x_column == 'Index':
            x_data = np.arange(start_idx, end_idx)
            x_label = "Index"
        else:
            x_data = data_slice[series.x_column]
            x_label = series.x_column
            # Convert to datetime for plotting if it looks like datetime
            if self.detect_datetime_column(x_data):
                x_data = self.convert_to_datetime_for_plotting(x_data)
        
        # Prepare Y data
        y_data = data_slice[series.y_column].copy()
        
        # Handle missing data according to series configuration
        y_data = self.handle_missing_data(y_data, series.missing_data_method)
        
        # Create valid data mask
        if isinstance(x_data, pd.Series):
            valid_mask = ~(x_data.isna() | y_data.isna())
            x_plot = x_data[valid_mask]
            y_plot = y_data[valid_mask]
        else:
            valid_mask = ~y_data.isna()
            x_plot = x_data[valid_mask] if hasattr(x_data, '__getitem__') else [x for x, v in zip(x_data, valid_mask) if v]
            y_plot = y_data[valid_mask]
        
        if len(x_plot) == 0:
            return
        
        # Apply smoothing if requested
        if series.smooth_factor > 0 and len(y_plot) > 5:
            window_size = max(5, int(len(y_plot) * series.smooth_factor / 100))
            if window_size % 2 == 0:
                window_size += 1
            try:
                y_plot = savgol_filter(y_plot, window_size, 3)
            except:
                pass
        
        # Plot based on type
        if plot_type == 'line':
            line = ax.plot(x_plot, y_plot, 
                          color=series.color,
                          linestyle=series.line_style,
                          linewidth=series.line_width,
                          marker=series.marker if series.marker else None,
                          markersize=series.marker_size,
                          alpha=series.alpha,
                          label=series.legend_label if series.show_in_legend else "")
            
            # Fill area if requested
            if series.fill_area:
                ax.fill_between(x_plot, y_plot, alpha=series.alpha * 0.3, color=series.color)
                
        elif plot_type == 'scatter':
            ax.scatter(x_plot, y_plot,
                      color=series.color,
                      s=series.marker_size**2,
                      marker=series.marker if series.marker else 'o',
                      alpha=series.alpha,
                      label=series.legend_label if series.show_in_legend else "")
        
        elif plot_type == 'bar':
            ax.bar(x_plot, y_plot,
                   color=series.color,
                   alpha=series.alpha,
                   label=series.legend_label if series.show_in_legend else "")
        
        elif plot_type == 'area':
            ax.fill_between(x_plot, y_plot,
                           color=series.color,
                           alpha=series.alpha,
                           label=series.legend_label if series.show_in_legend else "")
        
        # Add trendline if requested
        if series.show_trendline and plot_type in ['scatter', 'line']:
            self.add_trendline(ax, x_plot, y_plot, series)
        
        # Add peaks if requested
        if series.show_peaks:
            self.mark_peaks(ax, x_plot, y_plot, series)
        
        # Add statistics box if requested
        if series.show_statistics:
            self.add_statistics_box(ax, y_plot, series)
        
        # Vacuum-specific features
        if series.highlight_base_pressure:
            base_pressure, _, _ = VacuumAnalysisTools.calculate_base_pressure(y_plot)
            ax.axhline(y=base_pressure, color='green', linestyle='--', alpha=0.5, 
                      label=f'Base: {base_pressure:.2e}')
        
        if series.highlight_spikes:
            spikes = VacuumAnalysisTools.detect_pressure_spikes(y_plot)
            for spike in spikes:
                if spike['severity'] == 'high':
                    ax.axvspan(x_plot.iloc[spike['start']], x_plot.iloc[spike['end']], 
                              color='red', alpha=0.2)
        
        # Handle datetime formatting for x-axis
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
            # Convert to numeric if needed
            if pd.api.types.is_datetime64_any_dtype(x_data):
                x_numeric = pd.to_numeric(x_data)
            else:
                x_numeric = pd.to_numeric(x_data, errors='coerce')
            
            y_numeric = pd.to_numeric(y_data, errors='coerce')
            
            # Remove NaN values
            valid = ~(x_numeric.isna() | y_numeric.isna())
            if valid.sum() < 2:
                return
            
            x_valid = x_numeric[valid].values
            y_valid = y_numeric[valid].values
            
            if series.trend_type == 'linear':
                # Linear regression
                x_valid_2d = x_valid.reshape(-1, 1)
                reg = LinearRegression()
                reg.fit(x_valid_2d, y_valid)
                
                # Create trendline
                x_trend = np.array([x_valid.min(), x_valid.max()]).reshape(-1, 1)
                y_trend = reg.predict(x_trend)
                
                # Plot trendline
                ax.plot(x_trend.flatten(), y_trend, 
                       color=series.color, 
                       linestyle='--', 
                       linewidth=series.line_width * 0.8,
                       alpha=series.alpha * 0.7,
                       label=f"{series.name} trend (R²={reg.score(x_valid_2d, y_valid):.3f})")
                       
            elif series.trend_type == 'polynomial':
                degree = series.trend_params.get('degree', 2)
                coeffs = np.polyfit(x_valid, y_valid, degree)
                poly = np.poly1d(coeffs)
                
                x_trend = np.linspace(x_valid.min(), x_valid.max(), 100)
                y_trend = poly(x_trend)
                
                ax.plot(x_trend, y_trend,
                       color=series.color,
                       linestyle='--',
                       linewidth=series.line_width * 0.8,
                       alpha=series.alpha * 0.7,
                       label=f"{series.name} poly{degree}")
                       
            elif series.trend_type == 'moving_average':
                window = series.trend_params.get('window', 20)
                ma = pd.Series(y_valid).rolling(window=window, center=True).mean()
                
                ax.plot(x_valid, ma,
                       color=series.color,
                       linestyle='--',
                       linewidth=series.line_width * 0.8,
                       alpha=series.alpha * 0.7,
                       label=f"{series.name} MA({window})")
            
        except Exception as e:
            print(f"Failed to add trendline: {e}")

    def mark_peaks(self, ax, x_data, y_data, series):
        """Mark peaks and valleys on the plot"""
        try:
            # Calculate prominence based on data range
            data_range = np.max(y_data) - np.min(y_data)
            prominence = series.peak_prominence * data_range
            
            # Find peaks and valleys
            peak_results = DataAnalysisTools.find_peaks_and_valleys(
                np.array(x_data), np.array(y_data), prominence
            )
            
            # Mark peaks
            if len(peak_results['peaks']['indices']) > 0:
                ax.scatter(peak_results['peaks']['x_values'], 
                          peak_results['peaks']['y_values'],
                          marker='^', s=100, color='red', zorder=5,
                          label=f'{series.name} peaks')
            
            # Mark valleys
            if len(peak_results['valleys']['indices']) > 0:
                ax.scatter(peak_results['valleys']['x_values'], 
                          peak_results['valleys']['y_values'],
                          marker='v', s=100, color='blue', zorder=5,
                          label=f'{series.name} valleys')
                          
        except Exception as e:
            print(f"Failed to mark peaks: {e}")

    def add_statistics_box(self, ax, y_data, series):
        """Add statistics box to plot"""
        try:
            stats = DataAnalysisTools.calculate_statistics(y_data)
            
            # Create text for statistics box
            stats_text = f"{series.name}\n"
            stats_text += f"Mean: {stats['mean']:.3e}\n"
            stats_text += f"Std: {stats['std']:.3e}\n"
            stats_text += f"Min: {stats['min']:.3e}\n"
            stats_text += f"Max: {stats['max']:.3e}"
            
            # Add text box to plot
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', bbox=props)
                   
        except Exception as e:
            print(f"Failed to add statistics: {e}")

    def configure_plot_axes(self, ax):
        """Configure plot axes and styling"""
        # Set title and labels
        ax.set_title(self.title_var.get(), fontsize=self.title_size_var.get(), fontweight='bold', pad=20)
        ax.set_xlabel(self.xlabel_var.get(), fontsize=self.xlabel_size_var.get())
        ax.set_ylabel(self.ylabel_var.get(), fontsize=self.ylabel_size_var.get())
        
        # Grid settings
        if self.show_grid_var.get():
            ax.grid(True, linestyle=self.grid_style_var.get(), 
                   alpha=self.grid_alpha_var.get(), which='both')
            ax.set_axisbelow(True)
        
        # Legend
        if self.show_legend_var.get():
            handles, labels = ax.get_legend_handles_labels()
            # Remove empty labels
            filtered = [(h, l) for h, l in zip(handles, labels) if l]
            if filtered:
                handles, labels = zip(*filtered)
                ax.legend(handles, labels, loc='best', frameon=True, 
                         fancybox=True, shadow=True, fontsize=10)
        
        # Log scales
        if self.log_scale_x_var.get():
            ax.set_xscale('log')
        if self.log_scale_y_var.get():
            ax.set_yscale('log')
        
        # Manual axis limits
        if not self.x_auto_scale.get():
            try:
                x_min = float(self.x_min_var.get())
                x_max = float(self.x_max_var.get())
                ax.set_xlim(x_min, x_max)
            except ValueError:
                pass
        
        if not self.y_auto_scale.get():
            try:
                y_min = float(self.y_min_var.get())
                y_max = float(self.y_max_var.get())
                ax.set_ylim(y_min, y_max)
            except ValueError:
                pass

    def show_analysis_panel(self):
        """Show the analysis tools panel"""
        if self.all_series:
            # Simple implementation without external AnalysisDialog
            self.status_bar.set_status("Analysis tools not available in this version", "info")
            # You could implement a basic analysis dialog here or use vacuum analysis
            self.show_vacuum_analysis()
        else:
            self.status_bar.set_status("No series available for analysis", "warning")

    def show_annotation_panel(self):
        """Show the annotation manager panel"""
        # Get current axes if plot exists
        ax = self.figure.axes[0] if self.figure and self.figure.axes else None
        annotation_dialog = ModernAnnotationDialog(self, self.annotation_manager, self.figure, ax)
        self.status_bar.set_status("Annotation manager opened", "info")

    def refresh_plot(self):
        """Refresh the current plot"""
        if self.all_series:
            self.create_plot()
            self.status_bar.set_status("Plot refreshed", "success")
        else:
            self.status_bar.set_status("No series to plot", "warning")

    def show_export_dialog(self):
        """Show export options"""
        # Create export dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Export Options")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 300) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        content = ctk.CTkFrame(dialog)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(content, text="Select Export Type:", font=("", 14)).pack(pady=10)
        
        # Export buttons
        ctk.CTkButton(
            content,
            text="Export Plot",
            command=lambda: self.export_plot(dialog),
            width=200,
            height=40
        ).pack(pady=10)
        
        ctk.CTkButton(
            content,
            text="Export All Data",
            command=lambda: self.export_all_data(dialog),
            width=200,
            height=40
        ).pack(pady=10)
        
        ctk.CTkButton(
            content,
            text="Export Series Config",
            command=lambda: self.export_series_config(dialog),
            width=200,
            height=40
        ).pack(pady=10)

    def export_plot(self, parent=None):
        """Export the current plot"""
        if not self.figure:
            self.status_bar.set_status("No plot to export", "warning")
            return
            
        # Create save dialog
        format_map = {
            'PNG (High Quality)': '.png',
            'PDF (Vector)': '.pdf',
            'SVG (Scalable)': '.svg',
            'JPG (Compressed)': '.jpg'
        }
        
        selected_format = self.export_format.get() if hasattr(self, 'export_format') else 'PNG (High Quality)'
        default_ext = format_map.get(selected_format, '.png')
        
        filetypes = [
            ("PNG files", "*.png"),
            ("PDF files", "*.pdf"),
            ("SVG files", "*.svg"),
            ("JPG files", "*.jpg"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            parent=parent or self,
            title="Export Plot",
            defaultextension=default_ext,
            filetypes=filetypes
        )
        
        if filename:
            try:
                dpi = self.dpi_var.get() if hasattr(self, 'dpi_var') else 300
                self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')
                self.status_bar.set_status(f"Plot exported to: {filename}", "success")
                if parent:
                    parent.destroy()
            except Exception as e:
                self.status_bar.set_status(f"Export failed: {str(e)}", "error")

    def export_all_data(self, parent=None):
        """Export all series data to a single Excel file"""
        if not self.all_series:
            self.status_bar.set_status("No series to export", "warning")
            return
            
        filename = filedialog.asksaveasfilename(
            parent=parent or self,
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
                        
                        # Get data range
                        start_idx = max(0, series.start_index)
                        end_idx = min(len(file_data.df), series.end_index or len(file_data.df))
                        data_slice = file_data.df.iloc[start_idx:end_idx]
                        
                        # Select relevant columns
                        if series.x_column == 'Index':
                            export_df = data_slice[[series.y_column]].copy()
                            export_df.insert(0, 'Index', range(start_idx, end_idx))
                        else:
                            cols = [series.x_column, series.y_column]
                            export_df = data_slice[cols].copy()
                        
                        # Create sheet name (max 31 chars for Excel)
                        sheet_name = series.name[:31]
                        
                        # Write to Excel
                        export_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                self.status_bar.set_status(f"Data exported to: {filename}", "success")
                if parent:
                    parent.destroy()
                
            except Exception as e:
                self.status_bar.set_status(f"Export failed: {str(e)}", "error")

    def export_series_config(self, parent=None):
        """Export series configuration for later import"""
        if not self.all_series:
            self.status_bar.set_status("No series configuration to export", "warning")
            return
            
        filename = filedialog.asksaveasfilename(
            parent=parent or self,
            title="Export Series Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                config = {
                    'version': '1.0',
                    'export_date': datetime.now().isoformat(),
                    'series': []
                }
                
                for series in self.all_series.values():
                    series_dict = {
                        'name': series.name,
                        'file': self.loaded_files[series.file_id].filepath,
                        'x_column': series.x_column,
                        'y_column': series.y_column,
                        'start_index': series.start_index,
                        'end_index': series.end_index,
                        'color': series.color,
                        'line_style': series.line_style,
                        'marker': series.marker,
                        'line_width': series.line_width,
                        'marker_size': series.marker_size,
                        'alpha': series.alpha,
                        'fill_area': series.fill_area,
                        'visible': series.visible,
                        'legend_label': series.legend_label,
                        'missing_data_method': series.missing_data_method,
                        'show_trendline': series.show_trendline,
                        'trend_type': series.trend_type,
                        'trend_params': series.trend_params
                    }
                    config['series'].append(series_dict)
                
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                
                self.status_bar.set_status(f"Configuration exported to: {filename}", "success")
                if parent:
                    parent.destroy()
                
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

    def show_error_details(self, error_files):
        """Show detailed error information"""
        # Create error dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("File Loading Errors")
        dialog.geometry("600x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        x = (self.winfo_screenwidth() - 600) // 2
        y = (self.winfo_screenheight() - 400) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        content = ctk.CTkFrame(dialog)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            content,
            text=f"{len(error_files)} files failed to load:",
            font=("", 14, "bold")
        ).pack(pady=5)
        
        # Scrollable error list
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
        
        # Close button
        ctk.CTkButton(
            content,
            text="Close",
            command=dialog.destroy,
            width=100
        ).pack(pady=10)

    def on_window_resize(self, event=None):
        """Handle window resize events"""
        if event and event.widget == self:
            width = self.winfo_width()
            height = self.winfo_height()

            # Determine appropriate layout
            if width < 1400:
                if self.current_layout != "compact":
                    self.current_layout = "compact"
                    self.create_compact_layout()
            else:
                if self.current_layout != "default":
                    self.current_layout = "default"
                    self.create_default_layout()

    def cycle_layout(self):
        """Cycle through layout modes"""
        layouts = ["default", "compact"]
        current_idx = layouts.index(self.current_layout)
        next_idx = (current_idx + 1) % len(layouts)
        self.current_layout = layouts[next_idx]

        if self.current_layout == "default":
            self.create_default_layout()
        else:
            self.create_compact_layout()

        self.status_bar.set_status(f"Layout changed to: {self.current_layout}", "info")

    def toggle_theme(self):
        """Toggle between dark and light themes - FIXED"""
        current = ctk.get_appearance_mode().lower()
        new_mode = "light" if current == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.current_theme = new_mode
        
        # Update plot style if plot exists
        if hasattr(self, 'figure') and self.figure:
            # Refresh plot with new theme
            self.refresh_plot()
        
        self.status_bar.set_status(f"Theme changed to: {new_mode}", "info")

    def on_closing(self):
        """Handle window closing event"""
        if self.loaded_files or self.all_series:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Exit")
            dialog.geometry("350x150")
            dialog.transient(self)
            dialog.grab_set()
            
            # Center dialog
            x = (self.winfo_screenwidth() - 350) // 2
            y = (self.winfo_screenheight() - 150) // 2
            dialog.geometry(f"+{x}+{y}")
            
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




# Main execution
if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("PROFESSIONAL MULTI-FILE EXCEL DATA PLOTTER v4.1")
        print("Vacuum Analysis Edition")
        print("="*60 + "\n")
        
        app = ProfessionalMultiFileExcelPlotter()
        
        # Set window icon if available
        try:
            app.wm_iconbitmap('icon.ico')
        except:
            pass
        
        app.mainloop()
        
    except Exception as e:
        print(f"\nCritical error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")