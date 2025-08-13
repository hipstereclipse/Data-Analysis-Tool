#!/usr/bin/env python3
"""
Annotation Dialog - Unified implementation
Consolidated annotation management interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import customtkinter as ctk
from typing import Dict, List, Optional, Any
import logging
import json
import numpy as np

from models.data_models import AnnotationConfig
from core.annotation_manager import AnnotationManager
from core.ui_factory import UIFactory

logger = logging.getLogger(__name__)


class AnnotationDialog:
    """Unified annotation management dialog"""
    
    def __init__(self, parent, annotation_manager: AnnotationManager, axes):
        self.parent = parent
        self.annotation_manager = annotation_manager
        self.axes = axes
        self.result = None
        
        # Current annotation being edited
        self.current_annotation = None
        
        # Create dialog
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Annotation Manager")
        self.dialog.geometry("1000x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog resizable
        self.dialog.resizable(True, True)
        self.dialog.minsize(800, 500)
        
        # Initialize variables
        self._init_variables()
        
        # Create widgets
        self._create_widgets()
        
        # Center dialog
        UIFactory.center_window(self.dialog, 1000, 600)
        
        # Refresh annotation list
        self._refresh_annotation_list()
        
        # Bind coordinates to plot for slider ranges
        self._bind_coordinates_to_plot()
        
        # Enable preview mode
        self.annotation_manager.start_preview_mode()
    
    def _init_variables(self):
        """Initialize dialog variables"""
        # Annotation properties
        self.text_var = tk.StringVar()
        self.x_pos_var = tk.DoubleVar()
        self.y_pos_var = tk.DoubleVar()
        # Secondary coordinates for lines/arrows
        self.x2_pos_var = tk.DoubleVar()
        self.y2_pos_var = tk.DoubleVar()
        self.color_var = tk.StringVar(value="#000000")
        self.font_size_var = tk.IntVar(value=12)
        self.font_weight_var = tk.StringVar(value="normal")
        self.arrow_var = tk.BooleanVar(value=False)
        self.background_var = tk.BooleanVar(value=False)
        self.border_var = tk.BooleanVar(value=False)

        # Enhanced annotation properties
        self.arrow_orientation_var = tk.StringVar(value="up")
        self.line_thickness_var = tk.DoubleVar(value=1.0)
        self.arrow_size_var = tk.DoubleVar(value=10.0)
        self.arrow_head_size_var = tk.DoubleVar(value=12.0)
        self.arrow_style_var = tk.StringVar(value="->")
        self.background_alpha_var = tk.DoubleVar(value=0.8)
        self.border_thickness_var = tk.DoubleVar(value=1.0)

        # Annotation templates
        self.templates = self._create_templates()

        # Real-time preview mode
        self.preview_enabled = tk.BooleanVar(value=True)
        self.line_creation_mode = tk.StringVar(value="manual")  # "manual", "pick_both"

        # Data-driven tools state
        self.snap_to_points_var = tk.BooleanVar(value=True)
        self.selected_series_var = tk.StringVar(value="")
        self.top_peaks_n_var = tk.IntVar(value=3)
        self.std_k_var = tk.DoubleVar(value=1.0)
        self.threshold_var = tk.DoubleVar(value=0.0)
        self._data_sources = []
    
    def _create_templates(self) -> Dict[str, Dict[str, Any]]:
        """Create annotation templates"""
        return {
            "Peak": {
                "text": "Peak",
                "color": "#FF0000",
                "font_size": 10,
                "arrow": True,
                "background": True
            },
            "Valley": {
                "text": "Valley",
                "color": "#0000FF",
                "font_size": 10,
                "arrow": True,
                "background": True
            },
            "Threshold": {
                "text": "Threshold",
                "color": "#FF8000",
                "font_size": 12,
                "arrow": False,
                "background": True
            },
            "Note": {
                "text": "Note",
                "color": "#008000",
                "font_size": 10,
                "arrow": False,
                "background": False
            },
            "Warning": {
                "text": "⚠ Warning",
                "color": "#FF0000",
                "font_size": 12,
                "arrow": True,
                "background": True,
                "border": True
            }
        }
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Left panel - Tools in tabs (reduces vertical clutter)
        tools_tab = ctk.CTkTabview(main_frame)
        tools_tab.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        tools_tab.add("Create")
        tools_tab.add("Properties")
        tools_tab.add("Data")
        tools_tab.add("Templates")

        # Create scrollable content areas for each tab
        create_tab = ctk.CTkScrollableFrame(tools_tab.tab("Create"))
        create_tab.pack(fill="both", expand=True, padx=8, pady=8)
        props_tab = ctk.CTkScrollableFrame(tools_tab.tab("Properties"))
        props_tab.pack(fill="both", expand=True, padx=8, pady=8)
        data_tab = ctk.CTkScrollableFrame(tools_tab.tab("Data"))
        data_tab.pack(fill="both", expand=True, padx=8, pady=8)
        templates_tab = ctk.CTkScrollableFrame(tools_tab.tab("Templates"))
        templates_tab.pack(fill="both", expand=True, padx=8, pady=8)

        # Populate tabs
        self._create_creation_tools(create_tab)
        self._create_properties_panel(props_tab)
        self._create_data_tools(data_tab)
        self._create_templates_panel(templates_tab)

        # Right panel - Annotation list
        list_panel = ctk.CTkFrame(main_frame)
        list_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Create annotation list
        self._create_annotation_list(list_panel)
        # Populate available data sources after UI is ready
        self._populate_data_sources()

        # Bottom dialog buttons
        self._create_button_panel()
    
    def _create_creation_tools(self, parent):
        """Create annotation creation tools"""
        section = UIFactory.create_labeled_frame(parent, "Create Annotation")
        section.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)
        
        # Position selection with slider-based positioning
        pos_frame = ctk.CTkFrame(content)
        pos_frame.pack(fill="x", pady=5)
        
        # X Position Slider
        x_pos_frame = ctk.CTkFrame(pos_frame)
        x_pos_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(x_pos_frame, text="X Position:", width=80).pack(side="left")
        self.x_pos_slider = ctk.CTkSlider(
            x_pos_frame,
            from_=0,
            to=100,
            variable=self.x_pos_var,
            command=self._update_position_from_slider,
            width=150
        )
        self.x_pos_slider.pack(side="left", padx=5, fill="x", expand=True)
        self.x_pos_label = ctk.CTkLabel(x_pos_frame, text="0.0", width=50)
        self.x_pos_label.pack(side="right", padx=5)
        
        # Y Position Slider
        y_pos_frame = ctk.CTkFrame(pos_frame)
        y_pos_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(y_pos_frame, text="Y Position:", width=80).pack(side="left")
        self.y_pos_slider = ctk.CTkSlider(
            y_pos_frame,
            from_=0,
            to=100,
            variable=self.y_pos_var,
            command=self._update_position_from_slider,
            width=150
        )
        self.y_pos_slider.pack(side="left", padx=5, fill="x", expand=True)
        self.y_pos_label = ctk.CTkLabel(y_pos_frame, text="0.0", width=50)
        self.y_pos_label.pack(side="right", padx=5)

        # Secondary coordinates for Line/Arrow
        sec_frame = ctk.CTkFrame(content)
        sec_frame.pack(fill="x", pady=(8, 2))
        ctk.CTkLabel(sec_frame, text="X2:", width=40).pack(side="left")
        self.x2_entry = ctk.CTkEntry(sec_frame, width=90)
        self.x2_entry.pack(side="left", padx=(5, 10))
        ctk.CTkLabel(sec_frame, text="Y2:", width=40).pack(side="left")
        self.y2_entry = ctk.CTkEntry(sec_frame, width=90)
        self.y2_entry.pack(side="left", padx=(5, 10))
        
        # Text input
        ctk.CTkLabel(content, text="Annotation Text:").pack(anchor="w", pady=(10, 2))
        text_entry = ctk.CTkEntry(content, textvariable=self.text_var, width=300)
        text_entry.pack(fill="x", pady=2)
        
        # Creation buttons - organized in 2 rows
        buttons_row1 = ctk.CTkFrame(content)
        buttons_row1.pack(fill="x", pady=5)
        ctk.CTkButton(
            buttons_row1,
            text="Add Text",
            command=self._create_text_annotation,
            width=80
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            buttons_row1,
            text="Add Line",
            command=self._create_line_annotation,
            width=80
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            buttons_row1,
            text="Add Arrow",
            command=self._create_arrow_annotation,
            width=80
        ).pack(side="left", padx=2)
        
        buttons_row2 = ctk.CTkFrame(content)
        buttons_row2.pack(fill="x", pady=2)
        ctk.CTkButton(
            buttons_row2,
            text="Add Rect",
            command=self._create_rect_annotation,
            width=80
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            buttons_row2,
            text="Add Circle",
            command=self._create_circle_annotation,
            width=80
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            buttons_row2,
            text="Add Point",
            command=self._create_point_annotation,
            width=80
        ).pack(side="left", padx=2)

        # Pick end point on plot for line/arrow
        pick_row = ctk.CTkFrame(content)
        pick_row.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(
            pick_row,
            text="Pick End on Plot",
            command=self._pick_end_on_plot,
            width=150
        ).pack(side="left", padx=4)
        
        # Real-time preview toggle
        ctk.CTkCheckBox(
            pick_row,
            text="Live Preview",
            variable=self.preview_enabled,
            command=self._toggle_preview
        ).pack(side="right", padx=4)
        
        # Line creation mode
        mode_frame = ctk.CTkFrame(content)
        mode_frame.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(mode_frame, text="Line/Arrow Mode:").pack(side="left", padx=4)
        ctk.CTkRadioButton(mode_frame, text="Manual", variable=self.line_creation_mode, value="manual").pack(side="left", padx=4)
        ctk.CTkRadioButton(mode_frame, text="Pick Both Points", variable=self.line_creation_mode, value="pick_both").pack(side="left", padx=4)
        
        # Bind preview updates to control changes
        self._bind_preview_updates()
    
    def _create_properties_panel(self, parent):
        """Create properties panel"""
        section = UIFactory.create_labeled_frame(parent, "Properties")
        section.pack(fill="x", pady=5)
        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)
        
        # Color selection
        color_frame = ctk.CTkFrame(content)
        color_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(color_frame, text="Color:", width=60).pack(side="left")
        self.color_button = ctk.CTkButton(
            color_frame,
            text="",
            command=self._choose_color,
            width=40,
            fg_color=self.color_var.get()
        )
        self.color_button.pack(side="left", padx=5)
        
        # Font size
        font_frame = ctk.CTkFrame(content)
        font_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(font_frame, text="Font Size:", width=60).pack(side="left")
        ctk.CTkSlider(
            font_frame,
            from_=8,
            to=24,
            variable=self.font_size_var,
            width=120
        ).pack(side="left", padx=5)
        
        # Font weight
        weight_frame = ctk.CTkFrame(content)
        weight_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(weight_frame, text="Weight:", width=60).pack(side="left")
        ctk.CTkComboBox(
            weight_frame,
            variable=self.font_weight_var,
            values=["normal", "bold"],
            width=80
        ).pack(side="left", padx=5)

        # Options
        ctk.CTkCheckBox(content, text="Show Arrow", variable=self.arrow_var).pack(anchor="w", pady=1)
        
        # Arrow properties (only visible when arrow is enabled)
        arrow_frame = ctk.CTkFrame(content)
        arrow_frame.pack(fill="x", pady=2)
        
        # Arrow head/style row
        style_frame = ctk.CTkFrame(arrow_frame)
        style_frame.pack(fill="x", pady=1)
        ctk.CTkLabel(style_frame, text="Style:", width=50).pack(side="left")
        ctk.CTkComboBox(
            style_frame,
            variable=self.arrow_style_var,
            values=["->", "-|>", "<-", "<->", "fancy", "simple", "wedge"],
            width=90
        ).pack(side="left", padx=4)
        ctk.CTkLabel(style_frame, text="Head:", width=40).pack(side="left")
        ctk.CTkSlider(
            style_frame,
            from_=6,
            to=30,
            variable=self.arrow_head_size_var,
            width=100
        ).pack(side="left", padx=4)
        
        # Arrow/line width
        arrow_size_frame = ctk.CTkFrame(arrow_frame)
        arrow_size_frame.pack(fill="x", pady=1)
        ctk.CTkLabel(arrow_size_frame, text="Width:", width=50).pack(side="left")
        ctk.CTkSlider(
            arrow_size_frame,
            from_=0.5,
            to=6.0,
            variable=self.arrow_size_var,
            width=120
        ).pack(side="left", padx=5)
        
        # Line thickness
        line_thickness_frame = ctk.CTkFrame(content)
        line_thickness_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(line_thickness_frame, text="Line Thickness:", width=90).pack(side="left")
        ctk.CTkSlider(
            line_thickness_frame,
            from_=0.5,
            to=5.0,
            variable=self.line_thickness_var,
            width=120
        ).pack(side="left", padx=5)
        
        # Background and border options
        ctk.CTkCheckBox(content, text="Background", variable=self.background_var).pack(anchor="w", pady=1)
        
        # Background alpha (only visible when background is enabled)
        bg_alpha_frame = ctk.CTkFrame(content)
        bg_alpha_frame.pack(fill="x", pady=1)
        ctk.CTkLabel(bg_alpha_frame, text="BG Alpha:", width=70).pack(side="left")
        ctk.CTkSlider(
            bg_alpha_frame,
            from_=0.1,
            to=1.0,
            variable=self.background_alpha_var,
            width=100
        ).pack(side="left", padx=5)
        
        ctk.CTkCheckBox(content, text="Border", variable=self.border_var).pack(anchor="w", pady=1)
        
        # Border thickness (only visible when border is enabled)
        border_thickness_frame = ctk.CTkFrame(content)
        border_thickness_frame.pack(fill="x", pady=1)
        ctk.CTkLabel(border_thickness_frame, text="Border:", width=70).pack(side="left")
        ctk.CTkSlider(
            border_thickness_frame,
            from_=0.5,
            to=3.0,
            variable=self.border_thickness_var,
            width=100
        ).pack(side="left", padx=5)
        
        # Update button
        ctk.CTkButton(
            content,
            text="Update Selected",
            command=self._update_annotation,
            width=150
        ).pack(pady=10)
    
    def _create_templates_panel(self, parent):
        """Create templates panel"""
        section = UIFactory.create_labeled_frame(parent, "Quick Templates")
        section.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)
        
        # Template buttons - organized in rows
        row1 = ctk.CTkFrame(content)
        row1.pack(fill="x", pady=2)
        row2 = ctk.CTkFrame(content)
        row2.pack(fill="x", pady=2)
        
        template_names = list(self.templates.keys())
        for i, template_name in enumerate(template_names):
            target_row = row1 if i < 3 else row2
            btn = ctk.CTkButton(
                target_row,
                text=template_name,
                command=lambda name=template_name: self._apply_template(name),
                width=80
            )
            btn.pack(side="left", padx=2, pady=2)
    
    def _create_annotation_list(self, parent):
        """Create annotation list panel with a top toolbar"""
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Header with toolbar
        header = ctk.CTkFrame(parent)
        header.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="📝 Annotations", font=("", 16, "bold")).grid(row=0, column=0, sticky="w")

        toolbar = ctk.CTkFrame(parent)
        toolbar.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        for child in [
            ("Delete", self._delete_annotation, 80),
            ("Clear All", self._clear_all_annotations, 80),
            ("Duplicate", self._duplicate_selected, 80),
            ("Move ↑", self._move_selected_up, 60),
            ("Move ↓", self._move_selected_down, 60),
            ("Toggle Vis", self._toggle_selected_visibility, 90),
            ("Export", self._export_annotations, 70),
            ("Import", self._import_annotations, 70),
        ]:
            ctk.CTkButton(toolbar, text=child[0], command=child[1], width=child[2]).pack(side="left", padx=3)

        # List frame
        list_frame = ctk.CTkFrame(parent)
        list_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # Annotation tree with columns
        columns = ("type", "text", "color", "visible")
        self.annotation_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        for col, w in [("type", 70), ("text", 220), ("color", 80), ("visible", 60)]:
            self.annotation_tree.heading(col, text=col.capitalize())
            self.annotation_tree.column(col, width=w, anchor="w")
        self.annotation_tree.grid(row=0, column=0, sticky="nsew")
        self.annotation_tree.bind("<<TreeviewSelect>>", self._on_select_annotation)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, command=self.annotation_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.annotation_tree.config(yscrollcommand=scrollbar.set)

    def _create_data_tools(self, parent):
        """Create data-driven tools section"""
        section = UIFactory.create_labeled_frame(parent, "Data Tools")
        section.pack(fill="x", pady=5)

        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)

        # Data source selection
        src_row = ctk.CTkFrame(content)
        src_row.pack(fill="x", pady=2)
        ctk.CTkLabel(src_row, text="Series:", width=50).pack(side="left")
        self.series_combo = ctk.CTkComboBox(
            src_row,
            variable=self.selected_series_var,
            values=[""],
            width=120
        )
        self.series_combo.pack(side="left", padx=2)
        ctk.CTkButton(src_row, text="↻", width=30, command=self._populate_data_sources).pack(side="left", padx=2)

        # Snap to points
        ctk.CTkCheckBox(content, text="Snap to data points", variable=self.snap_to_points_var).pack(anchor="w", pady=2)

        # Stats row 1: Mean / Median
        row1 = ctk.CTkFrame(content)
        row1.pack(fill="x", pady=2)
        ctk.CTkButton(row1, text="Mean", width=80, command=lambda: self._add_horizontal_stat("mean")).pack(side="left", padx=2)
        ctk.CTkButton(row1, text="Median", width=80, command=lambda: self._add_horizontal_stat("median")).pack(side="left", padx=2)
        ctk.CTkButton(row1, text="Min/Max", width=80, command=self._annotate_min_max).pack(side="left", padx=2)

        # Std band with k
        row2 = ctk.CTkFrame(content)
        row2.pack(fill="x", pady=2)
        ctk.CTkLabel(row2, text="k:", width=20).pack(side="left")
        k_entry = ctk.CTkEntry(row2, width=40)
        k_entry.insert(0, str(self.std_k_var.get()))
        k_entry.pack(side="left", padx=2)
        def _set_k_from_entry():
            try:
                self.std_k_var.set(float(k_entry.get()))
            except Exception:
                pass
        ctk.CTkButton(row2, text="Std Band", width=70, command=lambda: (_set_k_from_entry(), self._add_std_band())).pack(side="left", padx=2)
        
        # Peaks
        ctk.CTkLabel(row2, text="N:", width=20).pack(side="left", padx=(10,0))
        n_entry = ctk.CTkEntry(row2, width=40)
        n_entry.insert(0, str(self.top_peaks_n_var.get()))
        n_entry.pack(side="left", padx=2)
        def _set_n_from_entry():
            try:
                self.top_peaks_n_var.set(int(n_entry.get()))
            except Exception:
                pass
        ctk.CTkButton(row2, text="Peaks", width=60, command=lambda: (_set_n_from_entry(), self._annotate_top_peaks())).pack(side="left", padx=2)

        # Threshold crossings and Trendline
        row3 = ctk.CTkFrame(content)
        row3.pack(fill="x", pady=2)
        ctk.CTkLabel(row3, text="Threshold:", width=70).pack(side="left")
        thr_entry = ctk.CTkEntry(row3, width=60)
        thr_entry.insert(0, str(self.threshold_var.get()))
        thr_entry.pack(side="left", padx=2)
        def _set_thr_from_entry():
            try:
                self.threshold_var.set(float(thr_entry.get()))
            except Exception:
                pass
        ctk.CTkButton(row3, text="Crossings", width=80, command=lambda: (_set_thr_from_entry(), self._annotate_threshold_crossings())).pack(side="left", padx=2)
        ctk.CTkButton(row3, text="Trendline", width=80, command=self._annotate_trendline).pack(side="left", padx=2)
    
    def _create_button_panel(self):
        """Create dialog buttons"""
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(fill="x", pady=10)
        
        # Close button
        ctk.CTkButton(
            button_frame,
            text="Close",
            command=self._close_dialog,
            width=100
        ).pack(side="right", padx=5)
        
        # Apply button
        ctk.CTkButton(
            button_frame,
            text="Apply Changes",
            command=self._apply_changes,
            width=120
        ).pack(side="right", padx=5)
    
    def _start_click_placement(self):
        """Start click-to-place mode"""
        messagebox.showinfo("Click to Place", 
                           "Click on the plot to position the annotation.\n"
                           "The dialog will be temporarily hidden.")
        
        # Hide dialog temporarily
        self.dialog.withdraw()
        
        # Connect click event
        self._click_cid = self.axes.figure.canvas.mpl_connect('button_press_event', self._on_plot_click)
    
    def _on_plot_click(self, event):
        """Handle plot click for annotation placement"""
        if event.inaxes == self.axes:
            # Disconnect event
            self.axes.figure.canvas.mpl_disconnect(self._click_cid)
            
            # Set position
            x, y = event.xdata, event.ydata
            if self.snap_to_points_var.get():
                sx, sy = self._snap_to_data(x, y)
                if sx is not None:
                    x, y = sx, sy
            self.x_pos_var.set(x)
            self.y_pos_var.set(y)
            
            # Show dialog again
            self.dialog.deiconify()
            
            messagebox.showinfo("Position Set", 
                               f"Position set to ({event.xdata:.3f}, {event.ydata:.3f})")
    
    def _choose_color(self):
        """Choose annotation color"""
        color = colorchooser.askcolor(initialcolor=self.color_var.get())
        if color[1]:
            self.color_var.set(color[1])
            self.color_button.configure(fg_color=color[1])
    
    def _apply_template(self, template_name: str):
        """Apply annotation template"""
        template = self.templates[template_name]
        
        self.text_var.set(template["text"])
        self.color_var.set(template["color"])
        self.color_button.configure(fg_color=template["color"])
        self.font_size_var.set(template["font_size"])
        self.arrow_var.set(template.get("arrow", False))
        self.background_var.set(template.get("background", False))
        self.border_var.set(template.get("border", False))
    
    def _update_position_from_slider(self, value):
        """Update position labels when sliders change"""
        # Update the position labels with current slider values
        if hasattr(self, 'x_pos_label'):
            self.x_pos_label.configure(text=f"{self.x_pos_var.get():.1f}")
        if hasattr(self, 'y_pos_label'):
            self.y_pos_label.configure(text=f"{self.y_pos_var.get():.1f}")
    
    def _bind_coordinates_to_plot(self):
        """Bind slider coordinates to plot axes for real-time preview"""
        if self.axes and hasattr(self.axes, 'get_xlim') and hasattr(self.axes, 'get_ylim'):
            try:
                # Get current plot limits
                x_min, x_max = self.axes.get_xlim()
                y_min, y_max = self.axes.get_ylim()
                
                # Update slider ranges to match plot coordinates
                if hasattr(self, 'x_pos_slider'):
                    self.x_pos_slider.configure(from_=x_min, to=x_max)
                if hasattr(self, 'y_pos_slider'):
                    self.y_pos_slider.configure(from_=y_min, to=y_max)
                    
                # Set initial positions to center of plot
                self.x_pos_var.set((x_min + x_max) / 2)
                self.y_pos_var.set((y_min + y_max) / 2)

                # Initialize secondary coordinates a bit offset for convenience
                self.x2_pos_var.set(self.x_pos_var.get() + (x_max - x_min) * 0.1)
                self.y2_pos_var.set(self.y_pos_var.get())
                if hasattr(self, 'x2_entry'):
                    self.x2_entry.delete(0, tk.END)
                    self.x2_entry.insert(0, f"{self.x2_pos_var.get():.3f}")
                if hasattr(self, 'y2_entry'):
                    self.y2_entry.delete(0, tk.END)
                    self.y2_entry.insert(0, f"{self.y2_pos_var.get():.3f}")
                
            except Exception as e:
                logger.warning(f"Could not bind coordinates to plot: {e}")
    
    def _create_text_annotation(self):
        """Create a text annotation using manager helper"""
        try:
            text = self.text_var.get().strip()
            if not text:
                messagebox.showerror("Error", "Please enter annotation text")
                return
            self.annotation_manager.add_text(
                text=text,
                x=self.x_pos_var.get(),
                y=self.y_pos_var.get(),
                color=self.color_var.get(),
                font_size=float(self.font_size_var.get()),
                background_color=self.color_var.get() if self.background_var.get() else None,
                border_color=self.color_var.get() if self.border_var.get() else None,
                alpha=float(self.background_alpha_var.get()),
            )
            self.annotation_manager.refresh_plot_annotations()
            self._refresh_annotation_list()
            self.text_var.set("")
            messagebox.showinfo("Success", "Text annotation added!")
        except Exception as e:
            logger.error(f"Error creating text annotation: {e}")
            messagebox.showerror("Error", f"Failed to add text annotation: {str(e)}")

    def _parse_x2y2(self) -> tuple:
        """Parse X2/Y2 fields, falling back to default vars if entries are empty."""
        def _parse(entry, fallback):
            try:
                s = entry.get().strip()
                return float(s) if s else float(fallback.get())
            except Exception:
                return float(fallback.get())
        return _parse(self.x2_entry, self.x2_pos_var), _parse(self.y2_entry, self.y2_pos_var)

    def _create_line_annotation(self):
        """Create a line annotation using manager helper"""
        try:
            if self.line_creation_mode.get() == "pick_both":
                self._create_line_with_pick_both()
                return
                
            x2, y2 = self._parse_x2y2()
            self.annotation_manager.add_line(
                x1=float(self.x_pos_var.get()),
                y1=float(self.y_pos_var.get()),
                x2=float(x2),
                y2=float(y2),
                color=self.color_var.get(),
                line_style='-',
                width=float(self.line_thickness_var.get()),
                alpha=float(self.background_alpha_var.get()),
            )
            self.annotation_manager.refresh_plot_annotations()
            self._refresh_annotation_list()
            messagebox.showinfo("Success", "Line annotation added!")
        except Exception as e:
            logger.error(f"Error creating line annotation: {e}")
            messagebox.showerror("Error", f"Failed to add line annotation: {str(e)}")

    def _create_arrow_annotation(self):
        """Create an arrow annotation using manager helper"""
        try:
            if self.line_creation_mode.get() == "pick_both":
                self._create_arrow_with_pick_both()
                return
                
            x2, y2 = self._parse_x2y2()
            self.annotation_manager.add_arrow(
                x_from=float(self.x_pos_var.get()),
                y_from=float(self.y_pos_var.get()),
                x_to=float(x2),
                y_to=float(y2),
                text=self.text_var.get().strip(),
                color=self.color_var.get(),
                width=float(self.arrow_size_var.get()),
                style=self.arrow_style_var.get() or '->',
                alpha=float(self.background_alpha_var.get()),
            )
            # Apply head size to last arrow (update config then redraw)
            anns = self.annotation_manager.get_annotations()
            if anns:
                last = anns[-1]
                try:
                    last.arrow_mutation_scale = float(self.arrow_head_size_var.get())
                    self.annotation_manager.update_annotation(last)
                except Exception:
                    pass
            self.annotation_manager.refresh_plot_annotations()
            self._refresh_annotation_list()
            self.text_var.set("")
            messagebox.showinfo("Success", "Arrow annotation added!")
        except Exception as e:
            logger.error(f"Error creating arrow annotation: {e}")
            messagebox.showerror("Error", f"Failed to add arrow annotation: {str(e)}")
    
    def _create_arrow_with_pick_both(self):
        """Create arrow by picking both start and end points"""
        messagebox.showinfo("Pick Arrow Points", "Click two points on the plot to create an arrow.")
        self.dialog.withdraw()
        
        self.picked_points = []
        
        def _on_click(event):
            if event.inaxes == self.axes and len(self.picked_points) < 2:
                self.picked_points.append((event.xdata, event.ydata))
                
                if len(self.picked_points) == 1:
                    # First point picked, update position
                    self.x_pos_var.set(event.xdata)
                    self.y_pos_var.set(event.ydata)
                elif len(self.picked_points) == 2:
                    # Second point picked, create arrow
                    x1, y1 = self.picked_points[0]
                    x2, y2 = self.picked_points[1]
                    
                    # Create the arrow
                    ann = self.annotation_manager.add_arrow(x1, y1, x2, y2, 
                                                    text=self.text_var.get().strip(),
                                                    color=self.color_var.get(),
                                                    width=float(self.arrow_size_var.get()),
                                                    style=self.arrow_style_var.get() or '->',
                                                    alpha=float(self.background_alpha_var.get()))
                    try:
                        ann.arrow_mutation_scale = float(self.arrow_head_size_var.get())
                        self.annotation_manager.update_annotation(ann)
                    except Exception:
                        pass
                    self.annotation_manager.refresh_plot_annotations()
                    self._refresh_annotation_list()
                    self.text_var.set("")
                    
                    # Cleanup
                    self.axes.figure.canvas.mpl_disconnect(cid)
                    self.dialog.deiconify()
                    messagebox.showinfo("Success", "Arrow created!")
        
        cid = self.axes.figure.canvas.mpl_connect('button_press_event', _on_click)

    def _create_rect_annotation(self):
        """Create a rectangle annotation using manager helper.
        Uses (x,y) as lower-left, and infers width/height from X2/Y2 if provided, else defaults.
        """
        try:
            # Infer width/height from X2/Y2 entries if present
            x = float(self.x_pos_var.get())
            y = float(self.y_pos_var.get())
            x2_txt = self.x2_entry.get().strip() if hasattr(self, 'x2_entry') else ''
            y2_txt = self.y2_entry.get().strip() if hasattr(self, 'y2_entry') else ''
            if x2_txt and y2_txt:
                width = float(x2_txt) - x
                height = float(y2_txt) - y
            else:
                # Default rectangle size ~10% of axis span
                x_min, x_max = self.axes.get_xlim()
                y_min, y_max = self.axes.get_ylim()
                width = (x_max - x_min) * 0.1
                height = (y_max - y_min) * 0.1
            self.annotation_manager.add_rectangle(
                x=x,
                y=y,
                width=width,
                height=height,
                color=self.color_var.get(),
                fill=self.background_var.get(),
                alpha=float(self.background_alpha_var.get()),
                border_color=self.color_var.get() if self.border_var.get() else None,
                border_width=float(self.border_thickness_var.get()),
            )
            self.annotation_manager.refresh_plot_annotations()
            self._refresh_annotation_list()
            messagebox.showinfo("Success", "Rectangle annotation added!")
        except Exception as e:
            logger.error(f"Error creating rectangle annotation: {e}")
            messagebox.showerror("Error", f"Failed to add rectangle annotation: {str(e)}")

    def _create_circle_annotation(self):
        """Create a circle annotation using manager helper.
        Uses radius from |X2 - X| (or default if empty).
        """
        try:
            x = float(self.x_pos_var.get())
            y = float(self.y_pos_var.get())
            x2_txt = self.x2_entry.get().strip() if hasattr(self, 'x2_entry') else ''
            if x2_txt:
                radius = abs(float(x2_txt) - x)
            else:
                x_min, x_max = self.axes.get_xlim()
                radius = (x_max - x_min) * 0.05
            self.annotation_manager.add_circle(
                x=x,
                y=y,
                radius=radius,
                color=self.color_var.get(),
                fill=self.background_var.get(),
                alpha=float(self.background_alpha_var.get()),
                border_color=self.color_var.get() if self.border_var.get() else None,
                border_width=float(self.border_thickness_var.get()),
            )
            self.annotation_manager.refresh_plot_annotations()
            self._refresh_annotation_list()
            messagebox.showinfo("Success", "Circle annotation added!")
        except Exception as e:
            logger.error(f"Error creating circle annotation: {e}")
            messagebox.showerror("Error", f"Failed to add circle annotation: {str(e)}")

    def _create_point_annotation(self):
        """Create a labeled point annotation using manager helper."""
        try:
            self.annotation_manager.add_point(
                x=float(self.x_pos_var.get()),
                y=float(self.y_pos_var.get()),
                text=self.text_var.get().strip(),
                color=self.color_var.get(),
                marker='o',
                marker_size=8.0,
                alpha=float(self.background_alpha_var.get()),
            )
            self.annotation_manager.refresh_plot_annotations()
            self._refresh_annotation_list()
            self.text_var.set("")
            messagebox.showinfo("Success", "Point annotation added!")
        except Exception as e:
            logger.error(f"Error creating point annotation: {e}")
            messagebox.showerror("Error", f"Failed to add point annotation: {str(e)}")

    def _pick_end_on_plot(self):
        """Enable picking an end point on the plot to populate X2/Y2 for line/arrow."""
        try:
            messagebox.showinfo("Pick End Point", "Click on the plot to set X2/Y2 for line/arrow.")
            self.dialog.withdraw()
            def _on_click(event):
                try:
                    if event.inaxes == self.axes:
                        x, y = event.xdata, event.ydata
                        if self.snap_to_points_var.get():
                            sx, sy = self._snap_to_data(x, y)
                            if sx is not None:
                                x, y = sx, sy
                        if hasattr(self, 'x2_entry') and hasattr(self, 'y2_entry'):
                            self.x2_entry.delete(0, tk.END)
                            self.x2_entry.insert(0, f"{x:.3f}")
                            self.y2_entry.delete(0, tk.END)
                            self.y2_entry.insert(0, f"{y:.3f}")
                        # Also update backing vars
                        self.x2_pos_var.set(float(x))
                        self.y2_pos_var.set(float(y))
                finally:
                    self.axes.figure.canvas.mpl_disconnect(cid)
                    self.dialog.deiconify()
            cid = self.axes.figure.canvas.mpl_connect('button_press_event', _on_click)
        except Exception as e:
            logger.error(f"Error picking end point: {e}")
            messagebox.showerror("Error", f"Failed to pick end point: {str(e)}")
    
    def _update_annotation(self):
        """Update selected annotation"""
        try:
            if not self.current_annotation:
                messagebox.showwarning("Warning", "Please select an annotation to update")
                return
            
            # Update annotation properties
            self.current_annotation.text = self.text_var.get().strip()
            self.current_annotation.x_position = self.x_pos_var.get()
            self.current_annotation.y_position = self.y_pos_var.get()
            self.current_annotation.color = self.color_var.get()
            self.current_annotation.font_size = self.font_size_var.get()
            self.current_annotation.font_weight = self.font_weight_var.get()
            self.current_annotation.show_arrow = self.arrow_var.get()
            self.current_annotation.background = self.background_var.get()
            self.current_annotation.border = self.border_var.get()
            self.current_annotation.arrow_orientation = self.arrow_orientation_var.get()
            self.current_annotation.line_thickness = self.line_thickness_var.get()
            self.current_annotation.arrow_size = self.arrow_size_var.get()
            # Extended arrow controls
            try:
                self.current_annotation.arrow_style = self.arrow_style_var.get() or '->'
                self.current_annotation.arrow_mutation_scale = float(self.arrow_head_size_var.get())
            except Exception:
                pass
            self.current_annotation.background_alpha = self.background_alpha_var.get()
            self.current_annotation.border_thickness = self.border_thickness_var.get()
            
            # Update in manager
            self.annotation_manager.update_annotation(self.current_annotation)
            
            # Refresh list
            self._refresh_annotation_list()
            
            messagebox.showinfo("Success", "Annotation updated successfully!")
            
        except Exception as e:
            logger.error(f"Error updating annotation: {e}")
            messagebox.showerror("Error", f"Failed to update annotation: {str(e)}")
    
    def _delete_annotation(self):
        """Delete selected annotation"""
        try:
            if not self.current_annotation:
                messagebox.showwarning("Warning", "Please select an annotation to delete")
                return
            
            if messagebox.askyesno("Confirm Delete", 
                                  f"Delete annotation '{self.current_annotation.text}'?"):
                
                self.annotation_manager.remove_annotation(self.current_annotation.annotation_id)
                self.current_annotation = None
                
                # Clear inputs
                self._clear_inputs()
                
                # Refresh list
                self._refresh_annotation_list()
                
        except Exception as e:
            logger.error(f"Error deleting annotation: {e}")
            messagebox.showerror("Error", f"Failed to delete annotation: {str(e)}")
    
    def _clear_all_annotations(self):
        """Clear all annotations"""
        try:
            if self.annotation_manager.get_annotations():
                if messagebox.askyesno("Confirm Clear", "Delete all annotations?"):
                    self.annotation_manager.clear_annotations()
                    self.current_annotation = None
                    self._clear_inputs()
                    self._refresh_annotation_list()
            else:
                messagebox.showinfo("Info", "No annotations to clear")
                
        except Exception as e:
            logger.error(f"Error clearing annotations: {e}")
            messagebox.showerror("Error", f"Failed to clear annotations: {str(e)}")
    
    def _refresh_annotation_list(self):
        """Refresh the annotation tree list with rich columns"""
        try:
            # Clear tree
            if hasattr(self, 'annotation_tree'):
                for item in self.annotation_tree.get_children():
                    self.annotation_tree.delete(item)

                annotations = self.annotation_manager.get_annotations()
                for ann in annotations:
                    row = (
                        ann.annotation_type,
                        (ann.text or '').strip() or '(no text)',
                        ann.color,
                        'Yes' if getattr(ann, 'visible', True) else 'No'
                    )
                    self.annotation_tree.insert('', 'end', iid=ann.annotation_id, values=row)
                
        except Exception as e:
            logger.error(f"Error refreshing annotation list: {e}")
    
    def _on_select_annotation(self, event):
        """Handle annotation selection"""
        try:
            if hasattr(self, 'annotation_tree'):
                sel = self.annotation_tree.selection()
                if not sel:
                    return
                ann_id = sel[0]
                for ann in self.annotation_manager.get_annotations():
                    if ann.annotation_id == ann_id:
                        self.current_annotation = ann
                        break
                if self.current_annotation:
                    self._load_annotation_properties()
                    
        except Exception as e:
            logger.error(f"Error selecting annotation: {e}")
    
    def _load_annotation_properties(self):
        """Load selected annotation properties into inputs"""
        if not self.current_annotation:
            return
        
        try:
            self.text_var.set(self.current_annotation.text)
            self.x_pos_var.set(self.current_annotation.x_position)
            self.y_pos_var.set(self.current_annotation.y_position)
            self.color_var.set(self.current_annotation.color)
            self.color_button.configure(fg_color=self.current_annotation.color)
            self.font_size_var.set(self.current_annotation.font_size)
            self.font_weight_var.set(self.current_annotation.font_weight)
            self.arrow_var.set(self.current_annotation.show_arrow)
            self.background_var.set(self.current_annotation.background)
            self.border_var.set(self.current_annotation.border)
            # Load extended arrow props when applicable
            try:
                self.arrow_style_var.set(getattr(self.current_annotation, 'arrow_style', '->') or '->')
                self.arrow_head_size_var.set(float(getattr(self.current_annotation, 'arrow_mutation_scale', 12.0)))
                self.arrow_size_var.set(float(getattr(self.current_annotation, 'arrow_width', 1.0)))
                self.line_thickness_var.set(float(getattr(self.current_annotation, 'border_width', 1.0)))
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"Error loading annotation properties: {e}")
    
    def _clear_inputs(self):
        """Clear all input fields"""
        self.text_var.set("")
        self.x_pos_var.set(0.0)
        self.y_pos_var.set(0.0)
        self.color_var.set("#000000")
        self.color_button.configure(fg_color="#000000")
        self.font_size_var.set(12)
        self.font_weight_var.set("normal")
        self.arrow_var.set(False)
        self.background_var.set(False)
        self.border_var.set(False)
        self.arrow_style_var.set('->')
        self.arrow_head_size_var.set(12.0)
        self.arrow_size_var.set(1.0)
        self.line_thickness_var.set(1.0)
    
    def _apply_changes(self):
        """Apply all changes"""
        try:
            # Refresh plot annotations
            self.annotation_manager.refresh_plot_annotations()
            messagebox.showinfo("Success", "Changes applied successfully!")
            
        except Exception as e:
            logger.error(f"Error applying changes: {e}")
            messagebox.showerror("Error", f"Failed to apply changes: {str(e)}")
    
    def _close_dialog(self):
        """Close the dialog"""
        # Disable preview mode
        self.annotation_manager.stop_preview_mode()
        self.result = 'close'
        self.dialog.destroy()
    
    def _bind_preview_updates(self):
        """Bind preview updates to control changes"""
        def update_preview(*args):
            if self.preview_enabled.get():
                self._update_live_preview()

        # Bind to all relevant variables
        self.x_pos_var.trace('w', update_preview)
        self.y_pos_var.trace('w', update_preview)
        self.text_var.trace('w', update_preview)
        self.color_var.trace('w', update_preview)
        self.font_size_var.trace('w', update_preview)
        self.background_var.trace('w', update_preview)
        self.border_var.trace('w', update_preview)
        self.background_alpha_var.trace('w', update_preview)
        self.line_thickness_var.trace('w', update_preview)
        self.arrow_size_var.trace('w', update_preview)
        self.arrow_style_var.trace('w', update_preview)
        self.arrow_head_size_var.trace('w', update_preview)
    
    def _update_live_preview(self):
        """Update the live preview annotation"""
        if not self.preview_enabled.get():
            return
            
        try:
            # Create preview annotation config
            if self.arrow_var.get():
                # Show an arrow preview if arrow option is on and X2/Y2 present
                x2, y2 = self._parse_x2y2()
                preview_config = AnnotationConfig(
                    annotation_type="arrow",
                    text=self.text_var.get().strip(),
                    x=self.x_pos_var.get(),
                    y=self.y_pos_var.get(),
                    x2=float(x2),
                    y2=float(y2),
                    color=self.color_var.get(),
                    font_size=float(self.font_size_var.get()),
                    arrow_style=self.arrow_style_var.get() or '->',
                    arrow_width=float(self.arrow_size_var.get()),
                    arrow_mutation_scale=float(self.arrow_head_size_var.get()),
                    alpha=float(self.background_alpha_var.get()),
                )
            else:
                preview_config = AnnotationConfig(
                    annotation_type="text",
                    text=self.text_var.get() or "Preview",
                    x=self.x_pos_var.get(),
                    y=self.y_pos_var.get(),
                    color=self.color_var.get(),
                    font_size=float(self.font_size_var.get()),
                    background_color=self.color_var.get() if self.background_var.get() else None,
                    border_color=self.color_var.get() if self.border_var.get() else None,
                    alpha=float(self.background_alpha_var.get()),
                )
            
            # Update preview
            self.annotation_manager.update_preview(preview_config)
        except Exception as e:
            logger.debug(f"Preview update failed: {e}")
    
    def _toggle_preview(self):
        """Toggle preview mode on/off"""
        if self.preview_enabled.get():
            self.annotation_manager.start_preview_mode()
            self._update_live_preview()
        else:
            self.annotation_manager.stop_preview_mode()
    
    def _create_line_with_pick_both(self):
        """Create line by picking both start and end points"""
        messagebox.showinfo("Pick Line Points", "Click two points on the plot to create a line.")
        self.dialog.withdraw()
        
        self.picked_points = []
        
        def _on_click(event):
            if event.inaxes == self.axes and len(self.picked_points) < 2:
                self.picked_points.append((event.xdata, event.ydata))
                
                if len(self.picked_points) == 1:
                    # First point picked, update position
                    self.x_pos_var.set(event.xdata)
                    self.y_pos_var.set(event.ydata)
                elif len(self.picked_points) == 2:
                    # Second point picked, create line
                    x1, y1 = self.picked_points[0]
                    x2, y2 = self.picked_points[1]
                    
                    # Update X2/Y2 entries
                    if hasattr(self, 'x2_entry'):
                        self.x2_entry.delete(0, tk.END)
                        self.x2_entry.insert(0, f"{x2:.3f}")
                    if hasattr(self, 'y2_entry'):
                        self.y2_entry.delete(0, tk.END)
                        self.y2_entry.insert(0, f"{y2:.3f}")
                    
                    # Create the line
                    self.annotation_manager.add_line(x1, y1, x2, y2, 
                                                   color=self.color_var.get(),
                                                   width=float(self.line_thickness_var.get()),
                                                   alpha=float(self.background_alpha_var.get()))
                    self.annotation_manager.refresh_plot_annotations()
                    self._refresh_annotation_list()
                    
                    # Cleanup
                    self.axes.figure.canvas.mpl_disconnect(cid)
                    self.dialog.deiconify()
                    messagebox.showinfo("Success", "Line created!")
        
        cid = self.axes.figure.canvas.mpl_connect('button_press_event', _on_click)

    # -------- Data tools helpers --------
    def _populate_data_sources(self):
        """Populate series combo with line labels from axes."""
        try:
            labels = []
            if hasattr(self.axes, 'get_lines'):
                for line in self.axes.get_lines():
                    label = line.get_label() or ""
                    # Skip matplotlib internal labels like _line0
                    if not label or label.startswith("_"):
                        # Use a fallback name with index
                        idx = len(labels)
                        label = f"Series {idx+1}"
                    labels.append(label)
            if not labels:
                labels = [""]
            self._data_sources = labels
            if hasattr(self, 'series_combo'):
                self.series_combo.configure(values=labels)
                # Keep current if present, else set to first
                current = self.selected_series_var.get()
                if current not in labels:
                    self.selected_series_var.set(labels[0])
        except Exception as e:
            logger.debug(f"Failed to populate data sources: {e}")

    def _get_selected_series_data(self):
        """Return x,y numpy arrays for the selected line series."""
        try:
            if not hasattr(self.axes, 'get_lines'):
                return None
            lines = list(self.axes.get_lines())
            if not lines:
                return None
            # Try to match by label
            target_label = self.selected_series_var.get()
            for line in lines:
                lbl = line.get_label() or ""
                if lbl == target_label or (not target_label and not lbl):
                    xdata = np.asarray(line.get_xdata(), dtype=float)
                    ydata = np.asarray(line.get_ydata(), dtype=float)
                    return xdata, ydata
            # Fallback to first line
            line = lines[0]
            xdata = np.asarray(line.get_xdata(), dtype=float)
            ydata = np.asarray(line.get_ydata(), dtype=float)
            return xdata, ydata
        except Exception as e:
            logger.debug(f"No series data available: {e}")
            return None

    def _snap_to_data(self, x, y):
        """Snap (x,y) to nearest data point on selected series."""
        series = self._get_selected_series_data()
        if not series:
            return (x, y)
        xdata, ydata = series
        if xdata.size == 0:
            return (x, y)
        try:
            idx = int(np.argmin(np.abs(xdata - x)))
            return (float(xdata[idx]), float(ydata[idx]))
        except Exception:
            return (x, y)

    def _add_horizontal_stat(self, kind: str):
        series = self._get_selected_series_data()
        if not series:
            messagebox.showwarning("No Data", "No series data available.")
            return
        x, y = series
        if y.size == 0:
            return
        if kind == "mean":
            yv = float(np.nanmean(y))
            label = "Mean"
            color = "#2E86AB"
        else:
            yv = float(np.nanmedian(y))
            label = "Median"
            color = "#8E44AD"
        xlim = self.axes.get_xlim()
        self.annotation_manager.add_line(
            x1=xlim[0], y1=yv, x2=xlim[1], y2=yv,
            color=color, line_style='--', width=1.5, alpha=0.6
        )
        self.annotation_manager.add_text(
            text=f"{label}: {yv:.3g}", x=xlim[1], y=yv,
            color=color, font_size=10, background_color="#FFFFFF", alpha=0.7
        )
        self.annotation_manager.refresh_plot_annotations()
        self._refresh_annotation_list()

    def _add_std_band(self):
        series = self._get_selected_series_data()
        if not series:
            messagebox.showwarning("No Data", "No series data available.")
            return
        x, y = series
        if y.size == 0:
            return
        k = float(self.std_k_var.get())
        mu = float(np.nanmean(y))
        sigma = float(np.nanstd(y))
        y_low, y_high = mu - k * sigma, mu + k * sigma
        x0, x1 = self.axes.get_xlim()
        # Add a semi-transparent rectangle spanning the band
        self.annotation_manager.add_rectangle(
            x=x0, y=min(y_low, y_high),
            width=(x1 - x0), height=abs(y_high - y_low),
            color="#3498DB", fill=True, alpha=0.15,
            border_color="#2980B9", border_width=0.5
        )
        # Add lines at the bounds
        self.annotation_manager.add_line(x0, y_low, x1, y_low, color="#2980B9", line_style=":", width=1.0, alpha=0.5)
        self.annotation_manager.add_line(x0, y_high, x1, y_high, color="#2980B9", line_style=":", width=1.0, alpha=0.5)
        self.annotation_manager.refresh_plot_annotations()
        self._refresh_annotation_list()

    def _annotate_min_max(self):
        series = self._get_selected_series_data()
        if not series:
            messagebox.showwarning("No Data", "No series data available.")
            return
        x, y = series
        if y.size == 0:
            return
        imin = int(np.nanargmin(y))
        imax = int(np.nanargmax(y))
        self.annotation_manager.add_point(x=float(x[imin]), y=float(y[imin]), text="Min", color="#16A085", marker='v', marker_size=8.0, alpha=0.9)
        self.annotation_manager.add_point(x=float(x[imax]), y=float(y[imax]), text="Max", color="#C0392B", marker='^', marker_size=8.0, alpha=0.9)
        self.annotation_manager.refresh_plot_annotations()
        self._refresh_annotation_list()

    def _annotate_top_peaks(self):
        series = self._get_selected_series_data()
        if not series:
            messagebox.showwarning("No Data", "No series data available.")
            return
        x, y = series
        if y.size < 3:
            return
        # Simple local maxima detection
        peaks = []
        for i in range(1, len(y) - 1):
            if y[i] > y[i-1] and y[i] > y[i+1]:
                peaks.append((i, y[i]))
        if not peaks:
            return
        peaks.sort(key=lambda t: t[1], reverse=True)
        n = max(1, int(self.top_peaks_n_var.get()))
        for i, _ in peaks[:n]:
            self.annotation_manager.add_point(x=float(x[i]), y=float(y[i]), text="Peak", color="#E67E22", marker='^', marker_size=8.0, alpha=0.9)
        self.annotation_manager.refresh_plot_annotations()
        self._refresh_annotation_list()

    def _annotate_threshold_crossings(self):
        series = self._get_selected_series_data()
        if not series:
            messagebox.showwarning("No Data", "No series data available.")
            return
        x, y = series
        if y.size < 2:
            return
        thr = float(self.threshold_var.get())
        s = y - thr
        crossings = []
        for i in range(1, len(y)):
            if np.isnan(s[i]) or np.isnan(s[i-1]):
                continue
            if (s[i] == 0) or (s[i-1] == 0) or (s[i] > 0) != (s[i-1] > 0):
                # Linear interpolation for x at crossing
                try:
                    x0, x1 = x[i-1], x[i]
                    y0, y1 = y[i-1], y[i]
                    if y1 != y0:
                        xc = float(x0 + (thr - y0) * (x1 - x0) / (y1 - y0))
                    else:
                        xc = float(x[i])
                    crossings.append(xc)
                except Exception:
                    pass
        for xc in crossings:
            self.annotation_manager.add_point(x=xc, y=thr, text="Cross", color="#34495E", marker='x', marker_size=8.0, alpha=0.9)
        self.annotation_manager.refresh_plot_annotations()
        self._refresh_annotation_list()

    def _annotate_trendline(self):
        series = self._get_selected_series_data()
        if not series:
            messagebox.showwarning("No Data", "No series data available.")
            return
        x, y = series
        if x.size < 2:
            return
        try:
            coeffs = np.polyfit(x, y, 1)
            m, b = float(coeffs[0]), float(coeffs[1])
            x0, x1 = self.axes.get_xlim()
            y0, y1 = m * x0 + b, m * x1 + b
            self.annotation_manager.add_line(x0, y0, x1, y1, color="#9B59B6", line_style="-.", width=1.5, alpha=0.7)
            self.annotation_manager.add_text(text=f"Slope: {m:.3g}", x=x1, y=y1, color="#9B59B6", font_size=10, background_color="#FFFFFF", alpha=0.7)
            self.annotation_manager.refresh_plot_annotations()
            self._refresh_annotation_list()
        except Exception as e:
            logger.debug(f"Trendline fit failed: {e}")

    # -------- Management helpers --------
    def _get_selected_id(self) -> Optional[str]:
        if hasattr(self, 'annotation_tree'):
            sel = self.annotation_tree.selection()
            if not sel:
                return None
            return sel[0]
        return None

    def _move_selected_up(self):
        ann_id = self._get_selected_id()
        anns = self.annotation_manager.get_annotations()
        if not ann_id:
            return
        # Find index
        idx = next((i for i,a in enumerate(anns) if a.annotation_id == ann_id), None)
        if idx is None or idx <= 0:
            return
        anns[idx-1], anns[idx] = anns[idx], anns[idx-1]
        self.annotation_manager.set_annotations(anns)
        self._refresh_annotation_list()
        try:
            self.annotation_tree.selection_set(anns[idx-1].annotation_id)
        except Exception:
            pass

    def _move_selected_down(self):
        ann_id = self._get_selected_id()
        anns = self.annotation_manager.get_annotations()
        if not ann_id:
            return
        idx = next((i for i,a in enumerate(anns) if a.annotation_id == ann_id), None)
        if idx is None or idx >= len(anns) - 1:
            return
        anns[idx+1], anns[idx] = anns[idx], anns[idx+1]
        self.annotation_manager.set_annotations(anns)
        self._refresh_annotation_list()
        try:
            self.annotation_tree.selection_set(anns[idx+1].annotation_id)
        except Exception:
            pass

    def _toggle_selected_visibility(self):
        ann_id = self._get_selected_id()
        if not ann_id:
            return
        anns = self.annotation_manager.get_annotations()
        ann = next((a for a in anns if a.annotation_id == ann_id), None)
        if not ann:
            return
        ann.visible = not getattr(ann, 'visible', True)
        self.annotation_manager.update_annotation(ann)
        self._refresh_annotation_list()

    def _duplicate_selected(self):
        ann_id = self._get_selected_id()
        if not ann_id:
            return
        anns = self.annotation_manager.get_annotations()
        ann = next((a for a in anns if a.annotation_id == ann_id), None)
        if not ann:
            return
        try:
            data = ann.to_dict() if hasattr(ann, 'to_dict') else ann.__dict__
            # Remove id to create a new one by manager
            data.pop('annotation_id', None)
            dup = AnnotationConfig(**data)
            self.annotation_manager.add_annotation(dup)
            self.annotation_manager.refresh_plot_annotations()
            self._refresh_annotation_list()
        except Exception as e:
            logger.error(f"Failed to duplicate annotation: {e}")

    def _export_annotations(self):
        try:
            anns = self.annotation_manager.get_annotations()
            payload = [a.to_dict() if hasattr(a, 'to_dict') else a.__dict__ for a in anns]
            path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
            if not path:
                return
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2)
            messagebox.showinfo("Exported", f"Saved {len(payload)} annotations.")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def _import_annotations(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All Files", "*.*")])
            if not path:
                return
            with open(path, 'r', encoding='utf-8') as f:
                payload = json.load(f)
            anns: List[AnnotationConfig] = []
            for item in payload:
                try:
                    # Accept dicts with possible extra/legacy fields
                    anns.append(AnnotationConfig(**item))
                except Exception:
                    # Best-effort fallback
                    a = AnnotationConfig(annotation_type=item.get('annotation_type', 'text'), x=item.get('x', 0.0), y=item.get('y', 0.0))
                    for k, v in item.items():
                        if hasattr(a, k):
                            setattr(a, k, v)
                    anns.append(a)
            self.annotation_manager.set_annotations(anns)
            self.annotation_manager.refresh_plot_annotations()
            self._refresh_annotation_list()
            messagebox.showinfo("Imported", f"Loaded {len(anns)} annotations.")
        except Exception as e:
            messagebox.showerror("Import Failed", str(e))


def show_annotation_dialog(parent, annotation_manager: AnnotationManager, axes) -> str:
    """Show the annotation dialog
    
    Args:
        parent: Parent widget
        annotation_manager: Annotation manager instance
        axes: Plot axes
        
    Returns:
        Dialog result
    """
    dialog = AnnotationDialog(parent, annotation_manager, axes)
    parent.wait_window(dialog.dialog)
    return dialog.result
