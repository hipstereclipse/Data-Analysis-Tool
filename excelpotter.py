#!/usr/bin/env python3
"""
Modern Professional Multi-File Excel Data Plotter v4.0 - FIXED VERSION
Complete UI Overhaul with Responsive Design and Modern Interface
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
from matplotlib.patches import Rectangle, Polygon
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

print("Starting Professional Multi-File Excel Plotter with Analysis Tools...")

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
        
        # Action buttons with icons
        self.actions = []
        
    def add_action(self, text, icon, command, tooltip=""):
        """Add an action button"""
        btn = ctk.CTkButton(
            self,
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
        
    def add_separator(self):
        """Add a vertical separator"""
        sep = ctk.CTkFrame(self, width=2, fg_color=("gray80", "gray30"))
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
                
            if artist:
                artists[artist] = ann_id
        
        return artists

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
        self.create_appearance_card()
        self.create_data_handling_card()
        self.create_analysis_card()
        self.create_display_options_card()
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
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
        
        # Highlighting options
        highlight_frame = ttk.LabelFrame(card, text="Auto-highlighting", padding=10)
        highlight_frame.pack(fill='x', pady=10)
        
        self.highlight_weekends_var = tk.BooleanVar(value=getattr(self.series, 'highlight_weekends', False))
        self.highlight_hours_var = tk.BooleanVar(value=getattr(self.series, 'highlight_business_hours', False))
        self.highlight_outliers_var = tk.BooleanVar(value=getattr(self.series, 'highlight_outliers', False))
        
        if hasattr(self.series, '_datetime_detected') and self.series._datetime_detected:
            ttk.Checkbutton(highlight_frame, text="Highlight weekends", 
                           variable=self.highlight_weekends_var).pack(anchor='w')
            ttk.Checkbutton(highlight_frame, text="Highlight business hours (9-5)", 
                           variable=self.highlight_hours_var).pack(anchor='w')
        
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
            self.series.show_trendline = self.show_trend_var.get()
            self.series.trend_type = self.trend_type_var.get()
            
            # Update trend parameters
            if self.series.trend_type == 'polynomial' and hasattr(self, 'poly_degree_var') and self.poly_degree_var:
                self.series.trend_params['degree'] = self.poly_degree_var.get()
            elif self.series.trend_type == 'moving_average' and hasattr(self, 'ma_window_var') and self.ma_window_var:
                self.series.trend_params['window'] = self.ma_window_var.get()
            
            self.series.show_peaks = self.show_peaks_var.get()
            self.series.peak_prominence = self.peak_prom_var.get()
            self.series.show_statistics = self.show_stats_var.get()
            
            # Display options
            self.series.visible = self.visible_var.get()
            self.series.show_in_legend = self.legend_var.get()
            self.series.legend_label = self.legend_label_var.get()
            self.series.y_axis = self.y_axis_var.get()
            
            # Highlighting
            self.series.highlight_weekends = self.highlight_weekends_var.get() if hasattr(self, 'highlight_weekends_var') else False
            self.series.highlight_business_hours = self.highlight_hours_var.get() if hasattr(self, 'highlight_hours_var') else False
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

class AnalysisDialog:
    """Dialog for data analysis tools"""
    def __init__(self, parent, series_data, all_series, loaded_files):
        self.parent = parent
        self.series_data = series_data
        self.all_series = all_series
        self.loaded_files = loaded_files
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Data Analysis Tools")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
    
    def create_widgets(self):
        # Create notebook for different analysis categories
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Statistics tab
        self.create_statistics_tab(notebook)
        
        # Peak detection tab
        self.create_peak_detection_tab(notebook)
        
        # Correlation analysis tab
        self.create_correlation_tab(notebook)
        
        # Regression analysis tab
        self.create_regression_tab(notebook)
        
        # Frequency analysis tab
        self.create_frequency_tab(notebook)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Close", command=self.close).pack(side='right', padx=5)
        ttk.Button(btn_frame, text="Export Results", command=self.export_results).pack(side='right', padx=5)
    
    def create_statistics_tab(self, notebook):
        """Create statistics analysis tab"""
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text='📊 Statistics')
        
        # Series selection
        select_frame = ttk.LabelFrame(stats_frame, text="Select Series", padding=10)
        select_frame.pack(fill='x', padx=5, pady=5)
        
        self.stats_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(select_frame, textvariable=self.stats_series_var, 
                    values=series_options, state='readonly', width=40).pack(pady=5)
        
        ttk.Button(select_frame, text="Calculate Statistics", 
                  command=self.calculate_statistics).pack(pady=5)
        
        # Results display
        results_frame = ttk.LabelFrame(stats_frame, text="Statistical Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create text widget for results
        self.stats_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10))
        stats_scroll = ttk.Scrollbar(results_frame, command=self.stats_text.yview)
        self.stats_text.config(yscrollcommand=stats_scroll.set)
        
        self.stats_text.pack(side='left', fill='both', expand=True)
        stats_scroll.pack(side='right', fill='y')
    
    def create_peak_detection_tab(self, notebook):
        """Create peak detection tab"""
        peak_frame = ttk.Frame(notebook)
        notebook.add(peak_frame, text='📈 Peak Detection')
        
        # Configuration
        config_frame = ttk.LabelFrame(peak_frame, text="Peak Detection Settings", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.peak_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.peak_series_var, 
                    values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Prominence setting
        ttk.Label(config_frame, text="Prominence:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.prominence_var = tk.DoubleVar(value=0.1)
        ttk.Scale(config_frame, from_=0.01, to=1.0, variable=self.prominence_var, 
                 orient='horizontal', length=200).grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(config_frame, textvariable=self.prominence_var).grid(row=1, column=2, padx=5, pady=5)
        
        ttk.Button(config_frame, text="Detect Peaks", 
                  command=self.detect_peaks).grid(row=2, column=1, pady=10)
        
        # Results
        results_frame = ttk.LabelFrame(peak_frame, text="Detection Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create treeview for peaks
        columns = ['Type', 'Index', 'X Value', 'Y Value']
        self.peaks_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.peaks_tree.heading(col, text=col)
            self.peaks_tree.column(col, width=100)
        
        peaks_scroll = ttk.Scrollbar(results_frame, orient='vertical', command=self.peaks_tree.yview)
        self.peaks_tree.configure(yscrollcommand=peaks_scroll.set)
        
        self.peaks_tree.pack(side='left', fill='both', expand=True)
        peaks_scroll.pack(side='right', fill='y')
        
        # Action buttons
        action_frame = ttk.Frame(peak_frame)
        action_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(action_frame, text="Mark Selected on Plot", 
                  command=self.mark_selected_peaks).pack(side='left', padx=5)
        ttk.Button(action_frame, text="Export Peak Data", 
                  command=self.export_peak_data).pack(side='left', padx=5)
    
    def create_correlation_tab(self, notebook):
        """Create correlation analysis tab"""
        corr_frame = ttk.Frame(notebook)
        notebook.add(corr_frame, text='🔗 Correlation')
        
        # Series selection
        select_frame = ttk.LabelFrame(corr_frame, text="Select Series for Correlation", padding=10)
        select_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(select_frame, text="Select multiple series to analyze correlation:").pack(pady=5)
        
        # Listbox for multiple selection
        self.corr_listbox = tk.Listbox(select_frame, selectmode='multiple', height=8)
        for series in self.all_series.values():
            self.corr_listbox.insert(tk.END, f"{series.name} - {series.y_column}")
        self.corr_listbox.pack(fill='x', pady=5)
        
        ttk.Button(select_frame, text="Calculate Correlation Matrix", 
                  command=self.calculate_correlation).pack(pady=5)
        
        # Results
        results_frame = ttk.LabelFrame(corr_frame, text="Correlation Matrix", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.corr_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10))
        corr_scroll = ttk.Scrollbar(results_frame, command=self.corr_text.yview)
        self.corr_text.config(yscrollcommand=corr_scroll.set)
        
        self.corr_text.pack(side='left', fill='both', expand=True)
        corr_scroll.pack(side='right', fill='y')
    
    def create_regression_tab(self, notebook):
        """Create regression analysis tab"""
        reg_frame = ttk.Frame(notebook)
        notebook.add(reg_frame, text='📉 Regression')
        
        # Configuration
        config_frame = ttk.LabelFrame(reg_frame, text="Regression Settings", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.reg_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.reg_series_var, 
                    values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Polynomial degree
        ttk.Label(config_frame, text="Polynomial Degree:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.poly_degree_var = tk.IntVar(value=1)
        ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.poly_degree_var, 
                   width=10).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        ttk.Button(config_frame, text="Perform Regression", 
                  command=self.perform_regression).grid(row=2, column=1, pady=10)
        
        # Results
        results_frame = ttk.LabelFrame(reg_frame, text="Regression Results", padding=10)
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.reg_text = tk.Text(results_frame, wrap='word', font=('Consolas', 10), height=10)
        reg_scroll = ttk.Scrollbar(results_frame, command=self.reg_text.yview)
        self.reg_text.config(yscrollcommand=reg_scroll.set)
        
        self.reg_text.pack(side='left', fill='both', expand=True)
        reg_scroll.pack(side='right', fill='y')
        
        # Residuals plot frame
        residual_frame = ttk.LabelFrame(reg_frame, text="Residual Plot", padding=10)
        residual_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.residual_fig = Figure(figsize=(6, 3), facecolor='white')
        self.residual_canvas = FigureCanvasTkAgg(self.residual_fig, master=residual_frame)
        self.residual_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def create_frequency_tab(self, notebook):
        """Create frequency analysis tab"""
        freq_frame = ttk.Frame(notebook)
        notebook.add(freq_frame, text='🌊 Frequency')
        
        # Configuration
        config_frame = ttk.LabelFrame(freq_frame, text="FFT Settings", padding=10)
        config_frame.pack(fill='x', padx=5, pady=5)
        
        # Series selection
        ttk.Label(config_frame, text="Series:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.fft_series_var = tk.StringVar()
        series_options = [f"{s.name} ({s.legend_label})" for s in self.all_series.values()]
        ttk.Combobox(config_frame, textvariable=self.fft_series_var, 
                    values=series_options, state='readonly', width=30).grid(row=0, column=1, padx=5, pady=5)
        
        # Sample rate
        ttk.Label(config_frame, text="Sample Rate:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.sample_rate_var = tk.DoubleVar(value=1.0)
        ttk.Entry(config_frame, textvariable=self.sample_rate_var, 
                 width=15).grid(row=1, column=1, sticky='w', padx=5, pady=5)
        
        ttk.Button(config_frame, text="Perform FFT", 
                  command=self.perform_fft).grid(row=2, column=1, pady=10)
        
        # Results plot
        plot_frame = ttk.LabelFrame(freq_frame, text="Frequency Spectrum", padding=10)
        plot_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.fft_fig = Figure(figsize=(8, 5), facecolor='white')
        self.fft_canvas = FigureCanvasTkAgg(self.fft_fig, master=plot_frame)
        self.fft_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def calculate_statistics(self):
        """Calculate and display statistics"""
        series_text = self.stats_series_var.get()
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
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, "No valid data in selected series")
            return
        
        # Calculate statistics
        stats_dict = DataAnalysisTools.calculate_statistics(y_data)
        
        # Display results
        result_text = f"STATISTICAL ANALYSIS\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"Column: {series.y_column}\n"
        result_text += f"{'='*50}\n\n"
        
        result_text += f"Descriptive Statistics:\n"
        result_text += f"  Count:        {stats_dict['count']:,}\n"
        result_text += f"  Mean:         {stats_dict['mean']:.6f}\n"
        result_text += f"  Median:       {stats_dict['median']:.6f}\n"
        result_text += f"  Std Dev:      {stats_dict['std']:.6f}\n"
        result_text += f"  Variance:     {stats_dict['var']:.6f}\n"
        result_text += f"  CV:           {stats_dict['cv']:.4f}\n\n"
        
        result_text += f"Range Statistics:\n"
        result_text += f"  Minimum:      {stats_dict['min']:.6f}\n"
        result_text += f"  Maximum:      {stats_dict['max']:.6f}\n"
        result_text += f"  Range:        {stats_dict['range']:.6f}\n\n"
        
        result_text += f"Quartile Statistics:\n"
        result_text += f"  Q1 (25%):     {stats_dict['q1']:.6f}\n"
        result_text += f"  Q3 (75%):     {stats_dict['q3']:.6f}\n"
        result_text += f"  IQR:          {stats_dict['iqr']:.6f}\n\n"
        
        result_text += f"Distribution Shape:\n"
        result_text += f"  Skewness:     {stats_dict['skewness']:.6f}\n"
        result_text += f"  Kurtosis:     {stats_dict['kurtosis']:.6f}\n"
        
        # Interpretation
        result_text += f"\n{'='*50}\n"
        result_text += f"INTERPRETATION:\n"
        
        if abs(stats_dict['skewness']) < 0.5:
            result_text += "• Distribution is approximately symmetric\n"
        elif stats_dict['skewness'] > 0:
            result_text += "• Distribution is right-skewed (positive skew)\n"
        else:
            result_text += "• Distribution is left-skewed (negative skew)\n"
        
        if stats_dict['kurtosis'] > 3:
            result_text += "• Distribution has heavy tails (leptokurtic)\n"
        elif stats_dict['kurtosis'] < 3:
            result_text += "• Distribution has light tails (platykurtic)\n"
        else:
            result_text += "• Distribution has normal tail weight (mesokurtic)\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, result_text)
    
    def detect_peaks(self):
        """Detect peaks and valleys"""
        series_text = self.peak_series_var.get()
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
            x_data = np.arange(start_idx, end_idx)
        else:
            x_data = data_slice[series.x_column].values
        
        y_data = data_slice[series.y_column].values
        
        # Remove NaN values
        valid_mask = ~(pd.isna(x_data) | pd.isna(y_data))
        x_data = x_data[valid_mask]
        y_data = y_data[valid_mask]
        
        if len(x_data) == 0:
            messagebox.showwarning("Warning", "No valid data in selected series")
            return
        
        # Calculate prominence based on data range
        data_range = np.max(y_data) - np.min(y_data)
        prominence = self.prominence_var.get() * data_range
        
        # Detect peaks and valleys
        peak_results = DataAnalysisTools.find_peaks_and_valleys(x_data, y_data, prominence)
        
        # Clear previous results
        for item in self.peaks_tree.get_children():
            self.peaks_tree.delete(item)
        
        # Display peaks
        for i, (x, y) in enumerate(zip(peak_results['peaks']['x_values'], 
                                       peak_results['peaks']['y_values'])):
            self.peaks_tree.insert('', 'end', values=['Peak', i, f"{x:.6f}", f"{y:.6f}"])
        
        # Display valleys
        for i, (x, y) in enumerate(zip(peak_results['valleys']['x_values'], 
                                       peak_results['valleys']['y_values'])):
            self.peaks_tree.insert('', 'end', values=['Valley', i, f"{x:.6f}", f"{y:.6f}"])
        
        # Store results for later use
        self.current_peak_results = peak_results
        self.current_peak_series = series
    
    def mark_selected_peaks(self):
        """Mark selected peaks on the main plot"""
        selection = self.peaks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select peaks/valleys to mark")
            return
        
        if not hasattr(self, 'current_peak_results'):
            return
        
        # Get parent's annotation manager
        if hasattr(self.parent, 'annotation_manager'):
            for item in selection:
                values = self.peaks_tree.item(item)['values']
                peak_type = values[0]
                x_val = float(values[2])
                y_val = float(values[3])
                
                # Add point marker
                color = 'red' if peak_type == 'Peak' else 'blue'
                marker = '^' if peak_type == 'Peak' else 'v'
                self.parent.annotation_manager.add_annotation(
                    'point',
                    x_pos=x_val,
                    y_pos=y_val,
                    label=f"{peak_type}: {y_val:.3f}",
                    marker=marker,
                    size=150,
                    color=color
                )
            
            messagebox.showinfo("Success", f"Added {len(selection)} markers to plot")
    
    def export_peak_data(self):
        """Export peak detection results"""
        if not hasattr(self, 'current_peak_results'):
            messagebox.showwarning("Warning", "No peak detection results to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Peak Data",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Prepare data for export
                peak_data = []
                
                # Add peaks
                for x, y in zip(self.current_peak_results['peaks']['x_values'],
                               self.current_peak_results['peaks']['y_values']):
                    peak_data.append({'Type': 'Peak', 'X': x, 'Y': y})
                
                # Add valleys
                for x, y in zip(self.current_peak_results['valleys']['x_values'],
                               self.current_peak_results['valleys']['y_values']):
                    peak_data.append({'Type': 'Valley', 'X': x, 'Y': y})
                
                # Create DataFrame and export
                df = pd.DataFrame(peak_data)
                df.to_csv(filename, index=False)
                
                messagebox.showinfo("Success", f"Peak data exported to:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export peak data:\n{str(e)}")
    
    def calculate_correlation(self):
        """Calculate correlation between selected series"""
        selection = self.corr_listbox.curselection()
        if len(selection) < 2:
            messagebox.showwarning("Warning", "Please select at least 2 series")
            return
        
        # Get selected series
        selected_series = []
        series_list = list(self.all_series.values())
        for idx in selection:
            selected_series.append(series_list[idx])
        
        # Prepare data for correlation
        correlation_data = {}
        min_length = float('inf')
        
        for series in selected_series:
            file_data = self.loaded_files[series.file_id]
            start_idx = series.start_index
            end_idx = series.end_index or len(file_data.df)
            y_data = file_data.df.iloc[start_idx:end_idx][series.y_column].values
            
            correlation_data[series.name] = y_data
            min_length = min(min_length, len(y_data))
        
        # Truncate all series to same length
        for key in correlation_data:
            correlation_data[key] = correlation_data[key][:min_length]
        
        # Calculate correlation matrix
        df_corr = pd.DataFrame(correlation_data)
        corr_matrix = df_corr.corr()
        
        # Display results
        result_text = f"CORRELATION ANALYSIS\n"
        result_text += f"{'='*50}\n"
        result_text += f"Number of series: {len(selected_series)}\n"
        result_text += f"Data points used: {min_length}\n\n"
        
        result_text += "Correlation Matrix:\n"
        result_text += corr_matrix.to_string(float_format=lambda x: f'{x:.4f}')
        
        result_text += f"\n\n{'='*50}\n"
        result_text += "INTERPRETATION:\n"
        
        # Find strong correlations
        strong_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    strong_corr.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_val))
        
        if strong_corr:
            result_text += "\nStrong correlations (|r| > 0.7):\n"
            for s1, s2, corr in strong_corr:
                result_text += f"• {s1} ↔ {s2}: {corr:.4f}\n"
        else:
            result_text += "\nNo strong correlations found (|r| > 0.7)\n"
        
        self.corr_text.delete(1.0, tk.END)
        self.corr_text.insert(1.0, result_text)
    
    def perform_regression(self):
        """Perform regression analysis"""
        series_text = self.reg_series_var.get()
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
            x_data = np.arange(start_idx, end_idx)
        else:
            x_data = data_slice[series.x_column].values
            # Convert to numeric if datetime
            if pd.api.types.is_datetime64_any_dtype(x_data):
                x_data = pd.to_numeric(x_data)
        
        y_data = data_slice[series.y_column].values
        
        # Remove NaN values
        valid_mask = ~(pd.isna(x_data) | pd.isna(y_data))
        x_data = x_data[valid_mask]
        y_data = y_data[valid_mask]
        
        if len(x_data) == 0:
            messagebox.showwarning("Warning", "No valid data in selected series")
            return
        
        # Perform regression
        degree = self.poly_degree_var.get()
        reg_results = DataAnalysisTools.perform_regression(x_data, y_data, degree)
        
        # Display results
        result_text = f"REGRESSION ANALYSIS\n"
        result_text += f"{'='*50}\n"
        result_text += f"Series: {series.name}\n"
        result_text += f"Polynomial Degree: {degree}\n"
        result_text += f"Data Points: {len(x_data)}\n\n"
        
        result_text += f"Model Performance:\n"
        result_text += f"  R-squared: {reg_results['r_squared']:.6f}\n"
        result_text += f"  RMSE: {np.sqrt(np.mean(reg_results['residuals']**2)):.6f}\n\n"
        
        result_text += f"Coefficients:\n"
        for i, coef in enumerate(reg_results['coefficients']):
            if degree == 1:
                if i == 0:
                    result_text += f"  Intercept: {coef:.6f}\n"
                else:
                    result_text += f"  Slope: {coef:.6f}\n"
            else:
                result_text += f"  x^{degree-i}: {coef:.6e}\n"
        
        # Equation
        result_text += f"\nRegression Equation:\n"
        if degree == 1:
            result_text += f"  y = {reg_results['coefficients'][1]:.6f}x + {reg_results['coefficients'][0]:.6f}\n"
        else:
            equation = "  y = "
            for i, coef in enumerate(reg_results['coefficients']):
                power = degree - i
                if i > 0:
                    equation += " + " if coef >= 0 else " - "
                    equation += f"{abs(coef):.3e}"
                else:
                    equation += f"{coef:.3e}"
                
                if power > 1:
                    equation += f"x^{power}"
                elif power == 1:
                    equation += "x"
            result_text += equation + "\n"
        
        self.reg_text.delete(1.0, tk.END)
        self.reg_text.insert(1.0, result_text)
        
        # Plot residuals
        self.residual_fig.clear()
        ax = self.residual_fig.add_subplot(111)
        
        ax.scatter(x_data, reg_results['residuals'], alpha=0.6, s=30)
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.8)
        ax.set_xlabel('X values')
        ax.set_ylabel('Residuals')
        ax.set_title('Residual Plot')
        ax.grid(True, alpha=0.3)
        
        self.residual_fig.tight_layout()
        self.residual_canvas.draw()
        
        # Store results for adding to main plot
        self.current_regression = {
            'x_data': x_data,
            'y_pred': reg_results['y_predicted'],
            'series': series,
            'degree': degree,
            'r_squared': reg_results['r_squared']
        }
    
    def perform_fft(self):
        """Perform FFT analysis"""
        series_text = self.fft_series_var.get()
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
        y_data = file_data.df.iloc[start_idx:end_idx][series.y_column].dropna().values
        
        if len(y_data) == 0:
            messagebox.showwarning("Warning", "No valid data in selected series")
            return
        
        # Perform FFT
        sample_rate = self.sample_rate_var.get()
        frequencies, amplitudes = DataAnalysisTools.perform_fft(y_data, sample_rate)
        
        # Plot results
        self.fft_fig.clear()
        ax = self.fft_fig.add_subplot(111)
        
        ax.plot(frequencies, amplitudes, 'b-', linewidth=1.5)
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Amplitude')
        ax.set_title(f'Frequency Spectrum - {series.name}')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, sample_rate/2)  # Nyquist frequency
        
        # Find dominant frequencies
        peak_indices = find_peaks(amplitudes, height=np.max(amplitudes)*0.1)[0]
        if len(peak_indices) > 0:
            peak_freqs = frequencies[peak_indices]
            peak_amps = amplitudes[peak_indices]
            
            # Mark dominant frequencies
            ax.scatter(peak_freqs, peak_amps, color='red', s=100, zorder=5)
            
            # Annotate top 3 frequencies
            sorted_indices = np.argsort(peak_amps)[::-1][:3]
            for idx in sorted_indices:
                ax.annotate(f'{peak_freqs[idx]:.2f} Hz', 
                           xy=(peak_freqs[idx], peak_amps[idx]),
                           xytext=(10, 10), textcoords='offset points',
                           fontsize=9, ha='left')
        
        self.fft_fig.tight_layout()
        self.fft_canvas.draw()
    
    def export_results(self):
        """Export all analysis results"""
        filename = filedialog.asksaveasfilename(
            title="Export Analysis Results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("DATA ANALYSIS RESULTS\n")
                    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("="*70 + "\n\n")
                    
                    # Statistics
                    if self.stats_text.get(1.0, tk.END).strip():
                        f.write("STATISTICS\n")
                        f.write("-"*70 + "\n")
                        f.write(self.stats_text.get(1.0, tk.END))
                        f.write("\n\n")
                    
                    # Correlation
                    if self.corr_text.get(1.0, tk.END).strip():
                        f.write("CORRELATION ANALYSIS\n")
                        f.write("-"*70 + "\n")
                        f.write(self.corr_text.get(1.0, tk.END))
                        f.write("\n\n")
                    
                    # Regression
                    if self.reg_text.get(1.0, tk.END).strip():
                        f.write("REGRESSION ANALYSIS\n")
                        f.write("-"*70 + "\n")
                        f.write(self.reg_text.get(1.0, tk.END))
                        f.write("\n\n")
                
                messagebox.showinfo("Success", f"Analysis results exported to:\n{filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export results:\n{str(e)}")
    
    def close(self):
        """Close the dialog"""
        self.dialog.destroy()

class ModernAnnotationDialog:
    """Modern annotation dialog with inline editing"""
    def __init__(self, parent, annotation_manager, figure=None, ax=None):
        self.parent = parent
        self.annotation_manager = annotation_manager
        self.figure = figure
        self.ax = ax
        self.selected_annotation = None
        
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
            ("→ Arrow", self.add_arrow),
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
        
        # Quick templates
        ttk.Separator(parent, orient='horizontal').pack(fill='x', pady=20)
        
        ttk.Label(parent, text="Quick Templates", 
                 font=('Segoe UI', 12, 'bold')).pack(pady=(0, 10))
        
        templates = [
            ("📊 Add Statistics Box", self.add_stats_box),
            ("📅 Mark Weekends", self.mark_weekends),
            ("⏰ Business Hours", self.mark_business_hours),
            ("🎯 Mark Extremes", self.mark_extremes),
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
            # Position
            pos_frame = ttk.Frame(parent)
            pos_frame.pack(fill='x', pady=2)
            
            pos_key = 'x_pos' if ann_type == 'vline' else 'y_pos'
            ttk.Label(pos_frame, text=f"{pos_key.replace('_', ' ').title()}:").pack(side='left')
            
            pos_var = tk.StringVar(value=str(annotation.get(pos_key, 0)))
            pos_entry = ttk.Entry(pos_frame, textvariable=pos_var, width=15)
            pos_entry.pack(side='left', padx=5)
            pos_entry.bind('<Return>', lambda e: self.update_property(ann_id, pos_key, float(pos_var.get())))
            
            # Color
            color_btn = tk.Button(pos_frame, text="Color", bg=annotation.get('color', 'red'),
                                 command=lambda: self.change_color(ann_id))
            color_btn.pack(side='left', padx=5)
            
        elif ann_type == 'region':
            # Start and end positions
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
        
        # Label (common to all)
        if ann_type != 'text':
            label_frame = ttk.Frame(parent)
            label_frame.pack(fill='x', pady=2)
            
            ttk.Label(label_frame, text="Label:").pack(side='left')
            label_var = tk.StringVar(value=annotation.get('label', ''))
            label_entry = ttk.Entry(label_frame, textvariable=label_var, width=25)
            label_entry.pack(side='left', padx=5)
            label_entry.bind('<Return>', lambda e: self.update_property(ann_id, 'label', label_var.get()))
    
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
    
    def add_arrow(self):
        """Add arrow annotation"""
        if self.ax:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            x_start = xlim[0] + (xlim[1] - xlim[0]) * 0.3
            y_start = ylim[0] + (ylim[1] - ylim[0]) * 0.7
            x_end = xlim[0] + (xlim[1] - xlim[0]) * 0.6
            y_end = ylim[0] + (ylim[1] - ylim[0]) * 0.4
        else:
            x_start, y_start, x_end, y_end = 0, 1, 1, 0
        
        ann_id = self.annotation_manager.add_annotation('arrow',
            x_start=x_start,
            y_start=y_start,
            x_end=x_end,
            y_end=y_end,
            style='->',
            color='#2c3e50',
            width=2)
        
        self.update_annotation_list()
        self.select_annotation(ann_id)
        self.refresh_plot()
    
    def add_stats_box(self):
        """Add statistics box template"""
        # This would analyze the current data and add a text box with statistics
        messagebox.showinfo("Info", "Statistics box feature coming soon!")
    
    def mark_weekends(self):
        """Mark weekends template"""
        messagebox.showinfo("Info", "Weekend marking feature coming soon!")
    
    def mark_business_hours(self):
        """Mark business hours template"""
        messagebox.showinfo("Info", "Business hours marking feature coming soon!")
    
    def mark_extremes(self):
        """Mark extreme values template"""
        messagebox.showinfo("Info", "Extreme values marking feature coming soon!")
    
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
    
    def setup_interactive_editing(self):
        """Set up interactive annotation editing on the plot"""
        self.selected_artist = None
        
        def on_pick(event):
            """Handle picking annotations on the plot"""
            if hasattr(event, 'artist'):
                # Find which annotation was picked
                for ann_id, annotation in self.annotation_manager.annotations.items():
                    # Match the picked artist to an annotation
                    # This would need to be implemented based on how artists are tracked
                    pass
        
        def on_motion(event):
            """Handle mouse motion for dragging annotations"""
            if self.selected_artist and event.inaxes:
                # Update annotation position based on mouse movement
                pass
        
        def on_release(event):
            """Handle mouse release after dragging"""
            self.selected_artist = None
        
        # Connect event handlers
        self.figure.canvas.mpl_connect('pick_event', on_pick)
        self.figure.canvas.mpl_connect('motion_notify_event', on_motion)
        self.figure.canvas.mpl_connect('button_release_event', on_release)
    
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

class DataQualityLayer:
    """Represents a visual layer for data quality issues"""
    
    def __init__(self, name, issue_type, visible=True):
        self.name = name
        self.issue_type = issue_type
        self.visible = visible
        self.color_map = {
            'missing': '#e74c3c',     # Red
            'outliers': '#f39c12',    # Orange
            'gaps': '#9b59b6',        # Purple
            'duplicates': '#3498db',  # Blue
            'noise': '#e67e22',       # Dark orange
            'anomalies': '#c0392b'    # Dark red
        }
        self.alpha = 0.6
        self.style = 'highlight'  # highlight, annotate, or filter
    
    def apply_to_plot(self, ax, x_data, y_data, issues):
        """Apply this quality layer to the plot"""
        if not self.visible:
            return
        
        issue_data = issues.get(self.issue_type, {})
        color = self.color_map.get(self.issue_type, '#e74c3c')
        
        if self.issue_type == 'missing':
            self._highlight_missing(ax, x_data, y_data, issue_data, color)
        elif self.issue_type == 'outliers':
            self._highlight_outliers(ax, x_data, y_data, issue_data, color)
        elif self.issue_type == 'gaps':
            self._highlight_gaps(ax, x_data, y_data, issue_data, color)
        elif self.issue_type == 'duplicates':
            self._highlight_duplicates(ax, x_data, y_data, issue_data, color)
        elif self.issue_type == 'noise':
            self._highlight_noise(ax, x_data, y_data, issue_data, color)
        elif self.issue_type == 'anomalies':
            self._highlight_anomalies(ax, x_data, y_data, issue_data, color)
    
    def _highlight_missing(self, ax, x_data, y_data, issue_data, color):
        """Highlight missing data regions"""
        for region in issue_data.get('regions', []):
            start, end = region['start'], region['end']
            
            if self.style == 'highlight':
                # Add shaded region
                if start > 0 and end < len(x_data) - 1:
                    x_start = x_data.iloc[start-1] if hasattr(x_data, 'iloc') else x_data[start-1]
                    x_end = x_data.iloc[end+1] if hasattr(x_data, 'iloc') else x_data[end+1]
                    ax.axvspan(x_start, x_end, alpha=self.alpha, color=color, 
                             label=f'Missing Data ({region["count"]} points)')
            
            elif self.style == 'annotate':
                # Add text annotation
                if region['severity'] == 'high':
                    mid_point = (start + end) // 2
                    if mid_point < len(x_data):
                        x_pos = x_data.iloc[mid_point] if hasattr(x_data, 'iloc') else x_data[mid_point]
                        ax.annotate(f'Missing\n{region["count"]} pts', 
                                  xy=(x_pos, ax.get_ylim()[1] * 0.95),
                                  xytext=(0, 10), textcoords='offset points',
                                  ha='center', fontsize=9,
                                  bbox=dict(boxstyle='round,pad=0.3', fc=color, alpha=0.7),
                                  arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
    
    def _highlight_outliers(self, ax, x_data, y_data, issue_data, color):
        """Highlight outlier points"""
        indices = issue_data.get('indices', [])
        if not indices:
            return
        
        outlier_x = [x_data.iloc[i] if hasattr(x_data, 'iloc') else x_data[i] for i in indices if i < len(x_data)]
        outlier_y = [y_data.iloc[i] if hasattr(y_data, 'iloc') else y_data[i] for i in indices if i < len(y_data)]
        
        if self.style == 'highlight':
            # Circle outliers
            ax.scatter(outlier_x, outlier_y, s=100, facecolors='none', 
                      edgecolors=color, linewidths=2, label='Outliers', zorder=10)
        
        elif self.style == 'annotate':
            # Annotate severe outliers
            severities = issue_data.get('severity', [])
            for i, (x, y, severity) in enumerate(zip(outlier_x, outlier_y, severities)):
                if severity == 'extreme':
                    ax.annotate('!', xy=(x, y), xytext=(5, 5), 
                              textcoords='offset points', fontsize=12,
                              color=color, fontweight='bold')
    
    def _highlight_gaps(self, ax, x_data, y_data, issue_data, color):
        """Highlight data gaps"""
        gaps = issue_data.get('gaps', [])
        
        for gap in gaps:
            if gap['severity'] == 'high':
                start_idx = gap['start_idx']
                end_idx = gap['end_idx']
                
                if start_idx < len(x_data) and end_idx < len(x_data):
                    x1 = x_data.iloc[start_idx] if hasattr(x_data, 'iloc') else x_data[start_idx]
                    x2 = x_data.iloc[end_idx] if hasattr(x_data, 'iloc') else x_data[end_idx]
                    
                    # Draw attention to gap
                    ax.axvspan(x1, x2, alpha=self.alpha * 0.5, color=color, 
                             linestyle='--', label='Data Gap')
    
    def _highlight_duplicates(self, ax, x_data, y_data, issue_data, color):
        """Highlight duplicate points"""
        groups = issue_data.get('groups', [])
        
        for group in groups:
            if group['count'] > 2:  # Only highlight significant duplicates
                indices = group['indices']
                x_val, y_val = group['value']
                
                # Add marker at duplicate location
                ax.plot(x_val, y_val, 'X', markersize=12, color=color, 
                       label=f'Duplicate ({group["count"]}x)', zorder=10)
    
    def _highlight_noise(self, ax, x_data, y_data, issue_data, color):
        """Highlight noisy regions"""
        regions = issue_data.get('regions', [])
        
        for region in regions:
            if region['severity'] == 'high':
                start, end = region['start'], region['end']
                
                if start < len(x_data) and end < len(x_data):
                    x_start = x_data.iloc[start] if hasattr(x_data, 'iloc') else x_data[start]
                    x_end = x_data.iloc[end] if hasattr(x_data, 'iloc') else x_data[end]
                    
                    # Add translucent overlay
                    ax.axvspan(x_start, x_end, alpha=self.alpha * 0.3, 
                             color=color, label='High Noise Region')
    
    def _highlight_anomalies(self, ax, x_data, y_data, issue_data, color):
        """Highlight anomalous points"""
        anomalies = issue_data.get('anomalies', [])
        
        if anomalies:
            anomaly_x = [a['x'] for a in anomalies]
            anomaly_y = [a['y'] for a in anomalies]
            
            # Star markers for anomalies
            ax.scatter(anomaly_x, anomaly_y, marker='*', s=200, 
                      color=color, edgecolor='black', linewidth=1,
                      label='Anomalies', zorder=11)

class LayerManager:
    """Manages multiple visual layers for data quality and annotations"""
    
    def __init__(self):
        self.layers = {}
        self.layer_order = []
    
    def add_quality_layer(self, name, issue_type, visible=True):
        """Add a data quality layer"""
        layer = DataQualityLayer(name, issue_type, visible)
        self.layers[name] = layer
        if name not in self.layer_order:
            self.layer_order.append(name)
        return layer
    
    def remove_layer(self, name):
        """Remove a layer"""
        if name in self.layers:
            del self.layers[name]
            self.layer_order.remove(name)
    
    def reorder_layers(self, new_order):
        """Reorder layers"""
        self.layer_order = [name for name in new_order if name in self.layers]
    
    def toggle_layer(self, name):
        """Toggle layer visibility"""
        if name in self.layers:
            self.layers[name].visible = not self.layers[name].visible
    
    def apply_layers(self, ax, x_data, y_data, series_name=""):
        """Apply all active layers to the plot"""
        # For now, just return without applying layers
        # Full implementation would analyze data quality here
        pass

class ModernLayerControlPanel:
    """Modern UI panel for controlling data quality layers"""
    
    def __init__(self, parent, layer_manager, update_callback):
        self.parent = parent
        self.layer_manager = layer_manager
        self.update_callback = update_callback
        
        # Create the panel and make it accessible
        self.panel = self.create_panel()
    
    def create_panel(self):
        """Create the layer control panel"""
        # Main frame with modern styling
        self.panel = tk.Frame(self.parent, bg='#2c3e50', relief='flat')
        self.panel.pack(fill='both', expand=True)
        
        # Header
        header = tk.Frame(self.panel, bg='#34495e', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="🎨 Data Quality Layers", 
                font=('Segoe UI', 12, 'bold'), 
                fg='white', bg='#34495e').pack(side='left', padx=10, pady=10)
        
        # Add layer button
        add_btn = tk.Button(header, text="+ Add Layer", 
                          command=self.add_layer_dialog,
                          bg='#3498db', fg='white',
                          font=('Segoe UI', 10),
                          relief='flat', cursor='hand2')
        add_btn.pack(side='right', padx=10, pady=5)
        
        # Layer list container
        self.layer_container = tk.Frame(self.panel, bg='#ecf0f1')
        self.layer_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Initialize with default layers
        self.initialize_default_layers()
        self.update_layer_display()

        return self.panel
    
    def initialize_default_layers(self):
        """Add default quality layers"""
        default_layers = [
            ("Missing Data", "missing"),
            ("Outliers", "outliers"),
            ("Data Gaps", "gaps"),
            ("Duplicates", "duplicates"),
            ("Noise Regions", "noise"),
            ("Anomalies", "anomalies")
        ]
        
        for name, issue_type in default_layers:
            self.layer_manager.add_quality_layer(name, issue_type, visible=False)
    
    def update_layer_display(self):
        """Update the layer list display"""
        # Clear existing
        for widget in self.layer_container.winfo_children():
            widget.destroy()
        
        # Add layer items
        for i, layer_name in enumerate(self.layer_manager.layer_order):
            layer = self.layer_manager.layers[layer_name]
            self.create_layer_item(i, layer_name, layer)
    
    def create_layer_item(self, index, name, layer):
        """Create a single layer control item"""
        # Layer item frame
        item = tk.Frame(self.layer_container, bg='white', relief='solid', 
                       borderwidth=1, height=60)
        item.pack(fill='x', pady=2)
        item.pack_propagate(False)
        
        # Drag handle
        handle = tk.Label(item, text="≡", font=('Segoe UI', 12), 
                         bg='#bdc3c7', width=3, cursor='hand2')
        handle.pack(side='left', fill='y')
        
        # Layer info
        info_frame = tk.Frame(item, bg='white')
        info_frame.pack(side='left', fill='both', expand=True, padx=10)
        
        # Layer name and type
        name_label = tk.Label(info_frame, text=name, 
                            font=('Segoe UI', 11, 'bold'), 
                            bg='white', anchor='w')
        name_label.pack(fill='x', pady=(5, 0))
        
        type_label = tk.Label(info_frame, text=f"Type: {layer.issue_type}", 
                            font=('Segoe UI', 9), 
                            fg='#7f8c8d', bg='white', anchor='w')
        type_label.pack(fill='x')
        
        # Controls
        control_frame = tk.Frame(item, bg='white')
        control_frame.pack(side='right', padx=10)
        
        # Visibility toggle
        vis_var = tk.BooleanVar(value=layer.visible)
        vis_check = tk.Checkbutton(control_frame, text="Visible", 
                                  variable=vis_var, 
                                  command=lambda: self.toggle_visibility(name, vis_var.get()),
                                  bg='white', font=('Segoe UI', 9))
        vis_check.pack(side='left', padx=5)
        
        # Style selector
        style_var = tk.StringVar(value=layer.style)
        style_menu = ttk.Combobox(control_frame, textvariable=style_var,
                                 values=['highlight', 'annotate', 'filter'],
                                 state='readonly', width=10)
        style_menu.pack(side='left', padx=5)
        style_menu.bind('<<ComboboxSelected>>', 
                       lambda e: self.change_style(name, style_var.get()))
        
        # Color button
        color_btn = tk.Button(control_frame, text="", 
                            bg=layer.color_map.get(layer.issue_type, '#e74c3c'),
                            width=3, relief='raised',
                            command=lambda: self.change_color(name))
        color_btn.pack(side='left', padx=5)
        
        # Delete button
        del_btn = tk.Button(control_frame, text="×", 
                          fg='#e74c3c', bg='white',
                          font=('Segoe UI', 12, 'bold'),
                          relief='flat', cursor='hand2',
                          command=lambda: self.delete_layer(name))
        del_btn.pack(side='left', padx=2)
    
    def toggle_visibility(self, layer_name, visible):
        """Toggle layer visibility"""
        self.layer_manager.layers[layer_name].visible = visible
        self.update_callback()
    
    def change_style(self, layer_name, style):
        """Change layer display style"""
        self.layer_manager.layers[layer_name].style = style
        self.update_callback()
    
    def change_color(self, layer_name):
        """Change layer color"""
        layer = self.layer_manager.layers[layer_name]
        current_color = layer.color_map.get(layer.issue_type, '#e74c3c')
        
        color = colorchooser.askcolor(initialcolor=current_color)
        if color[1]:
            layer.color_map[layer.issue_type] = color[1]
            self.update_layer_display()
            self.update_callback()
    
    def delete_layer(self, layer_name):
        """Delete a layer"""
        if messagebox.askyesno("Confirm", f"Delete layer '{layer_name}'?"):
            self.layer_manager.remove_layer(layer_name)
            self.update_layer_display()
            self.update_callback()
    
    def add_layer_dialog(self):
        """Show dialog to add new layer"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Quality Layer")
        dialog.geometry("400x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Layer name
        tk.Label(dialog, text="Layer Name:", font=('Segoe UI', 10)).pack(pady=10)
        name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=name_var, width=30).pack(pady=5)
        
        # Issue type
        tk.Label(dialog, text="Issue Type:", font=('Segoe UI', 10)).pack(pady=10)
        type_var = tk.StringVar()
        type_combo = ttk.Combobox(dialog, textvariable=type_var,
                                 values=['missing', 'outliers', 'gaps', 
                                        'duplicates', 'noise', 'anomalies'],
                                 state='readonly', width=30)
        type_combo.pack(pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="Add", 
                  command=lambda: self.add_layer(name_var.get(), type_var.get(), dialog)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Cancel", 
                  command=dialog.destroy).pack(side='left', padx=5)
    
    def add_layer(self, name, issue_type, dialog):
        """Add a new layer"""
        if name and issue_type:
            self.layer_manager.add_quality_layer(name, issue_type)
            self.update_layer_display()
            self.update_callback()
            dialog.destroy()
        else:
            messagebox.showerror("Error", "Please provide both name and type")

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
        self.title("Professional Multi-File Excel Data Plotter v4.0")
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
        self.layer_manager = LayerManager()
        self.annotation_manager = ModernAnnotationManager()
        self.analysis_tools = DataAnalysisTools()
        
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
        """Create the top action bar"""
        self.top_bar = QuickActionBar(self.main_container)
        self.top_bar.grid(row=0, column=0, sticky="ew")

        # File actions
        self.top_bar.add_action("Add Files", "📁", self.add_files, "Load Excel/CSV files")
        self.top_bar.add_action("Save Project", "💾", self.save_project, "Save current project")
        self.top_bar.add_separator()

        # Plot actions - Now the method exists before it's referenced
        self.top_bar.add_action("Generate Plot", "📊", self.create_plot, "Create plot from series")
        self.top_bar.add_action("Export", "📤", self.show_export_dialog, "Export plot or data")
        self.top_bar.add_separator()

        # Analysis actions
        self.top_bar.add_action("Analysis", "🔬", self.show_analysis_panel, "Data analysis tools")
        self.top_bar.add_action("Annotations", "📍", self.show_annotation_panel, "Manage annotations")
        self.top_bar.add_separator()

        # View actions
        self.top_bar.add_action("Theme", "🎨", self.toggle_theme, "Toggle dark/light theme")
        self.top_bar.add_action("Layout", "📐", self.cycle_layout, "Change layout mode")

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
        self.layer_tab = self.sidebar_tabs.add("Quality Layers")

        self.create_files_panel()
        self.create_series_panel()
        self.create_config_panel()
        self.create_export_panel()
        self.create_layer_panel()

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
        self.layer_tab = self.main_tabs.add("Layers")

        self.create_files_panel()
        self.create_series_panel()
        self.create_plot_area_compact()
        self.create_config_panel()
        self.create_export_panel()
        self.create_layer_panel()

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

        # Column selection
        ctk.CTkLabel(content, text="X Column:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.series_x_var = tk.StringVar()
        self.series_x_combo = ctk.CTkComboBox(content, variable=self.series_x_var, width=120)
        self.series_x_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ctk.CTkLabel(content, text="Y Column:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.series_y_var = tk.StringVar()
        self.series_y_combo = ctk.CTkComboBox(content, variable=self.series_y_var, width=120)
        self.series_y_combo.grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        # Range selection
        ctk.CTkLabel(content, text="Start:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.series_start_var = tk.IntVar(value=0)
        self.series_start_entry = ctk.CTkEntry(content, textvariable=self.series_start_var, width=80)
        self.series_start_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ctk.CTkLabel(content, text="End:").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        self.series_end_var = tk.IntVar(value=1000)
        self.series_end_entry = ctk.CTkEntry(content, textvariable=self.series_end_var, width=80)
        self.series_end_entry.grid(row=2, column=3, sticky="w", padx=5, pady=5)

        # Series name
        ctk.CTkLabel(content, text="Name:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.series_name_var = tk.StringVar(value="New Series")
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

    def create_layer_panel(self):
        """Create data quality layers panel"""
        self.layer_control = ModernLayerControlPanel(
            self.layer_tab, 
            self.layer_manager,
            self.refresh_plot
        )
        # Pack the panel instead of the controller
        self.layer_control.panel.pack(fill="both", expand=True, padx=10, pady=10)

    def create_plot_area(self):
        """Create the main plot area"""
        # Welcome message for empty state
        self.empty_plot_frame = ctk.CTkFrame(self.plot_frame)
        self.empty_plot_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        welcome_label = ctk.CTkLabel(
            self.empty_plot_frame,
            text="Professional Multi-File Excel Data Plotter\n\nLoad multiple Excel files and create custom series ranges\nfor comprehensive data visualization and analysis.",
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
                    'series': []
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
                        'missing_data_method': series.missing_data_method
                    })
                
                with open(filename, 'w') as f:
                    json.dump(project_data, f, indent=2)
                
                self.status_bar.set_status(f"Project saved to: {filename}", "success")
                
            except Exception as e:
                self.status_bar.set_status(f"Save failed: {str(e)}", "error")

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
        
        # Handle datetime formatting for x-axis
        if pd.api.types.is_datetime64_any_dtype(x_data):
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            self.figure.autofmt_xdate()

        # Apply quality layers
        self.layer_manager.apply_layers(ax, x_plot, y_plot, series.name)

    def handle_missing_data(self, y_data, method):
        """Handle missing data according to specified method"""
        if method == 'drop':
            # dropna() already returns a Series
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
            
            x_valid = x_numeric[valid].values.reshape(-1, 1)
            y_valid = y_numeric[valid].values
            
            # Perform linear regression
            reg = LinearRegression()
            reg.fit(x_valid, y_valid)
            
            # Create trendline
            x_trend = np.array([x_valid.min(), x_valid.max()]).reshape(-1, 1)
            y_trend = reg.predict(x_trend)
            
            # Plot trendline
            ax.plot(x_trend.flatten(), y_trend, 
                   color=series.color, 
                   linestyle='--', 
                   linewidth=series.line_width * 0.8,
                   alpha=series.alpha * 0.7,
                   label=f"{series.name} trend (R²={reg.score(x_valid, y_valid):.3f})")
            
        except Exception as e:
            print(f"Failed to add trendline: {e}")

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
            # Create analysis dialog with current data
            analysis_dialog = AnalysisDialog(self, None, self.all_series, self.loaded_files)
            self.status_bar.set_status("Analysis tools panel opened", "info")
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
        filetypes = [
            ("PNG files", "*.png"),
            ("PDF files", "*.pdf"),
            ("SVG files", "*.svg"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            parent=parent or self,
            title="Export Plot",
            defaultextension=".png",
            filetypes=filetypes
        )
        
        if filename:
            try:
                dpi = 300 if "png" in filename.lower() else 150
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
                        'missing_data_method': series.missing_data_method
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
        """Toggle between dark and light themes"""
        current = ctk.get_appearance_mode()
        new_mode = "light" if current == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.current_theme = new_mode
        self.status_bar.set_status(f"Theme changed to: {new_mode}", "info")
        self.refresh_plot()

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
        print("PROFESSIONAL MULTI-FILE EXCEL DATA PLOTTER v4.0")
        print("Enhanced Edition with Analysis Tools")
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