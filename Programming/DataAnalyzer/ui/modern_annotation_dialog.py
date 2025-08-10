#!/usr/bin/env python3
"""
Modern Annotation System - Professional Annotation Management
Advanced annotation system with intelligent tools and modern UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
import uuid

from models.data_models import AnnotationConfig
from core.annotation_manager import AnnotationManager

logger = logging.getLogger(__name__)


class ModernAnnotationDialog(ctk.CTkToplevel):
    """
    Modern Annotation Management Dialog
    Features:
    - Visual annotation creation and editing
    - Template-based quick annotations
    - Intelligent positioning
    - Professional styling
    - Export-ready annotations
    """

    def __init__(self, parent, annotation_manager: AnnotationManager, plot_axes=None):
        super().__init__(parent)
        
        self.parent = parent
        self.annotation_manager = annotation_manager
        self.plot_axes = plot_axes
        self.result = None
        
        # Dialog state
        self.current_annotation = None
        self.annotation_templates = self._create_templates()
        
        # Setup dialog
        self.setup_dialog()
        self.create_interface()
        self.refresh_annotation_list()
        
        # Center dialog
        self.center_window()

    def setup_dialog(self):
        """Setup dialog window properties"""
        self.title("🎯 Modern Annotation Manager")
        self.geometry("900x700")
        self.minsize(800, 600)
        self.transient(self.parent)
        self.grab_set()
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def create_interface(self):
        """Create the modern interface"""
        # Left panel - Annotation list and templates
        self.create_annotation_list_panel()
        
        # Right panel - Properties and preview
        self.create_properties_panel()
        
        # Bottom panel - Actions
        self.create_action_panel()

    def create_annotation_list_panel(self):
        """Create annotation list and template panel"""
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            list_frame,
            text="🎯 Annotations",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 15), sticky="w")
        
        # Quick templates section
        templates_frame = ctk.CTkFrame(list_frame)
        templates_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        templates_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkLabel(
            templates_frame,
            text="🚀 Quick Templates",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=3, pady=(10, 5), sticky="w")
        
        # Template buttons
        template_buttons = [
            ("📝 Text Note", "text"),
            ("📍 Data Point", "point"),
            ("➡️ Arrow", "arrow"),
            ("📏 Line", "line"),
            ("🔴 Circle", "circle"),
            ("📦 Rectangle", "rectangle")
        ]
        
        for i, (text, template_type) in enumerate(template_buttons):
            btn = ctk.CTkButton(
                templates_frame,
                text=text,
                width=120,
                height=35,
                command=lambda t=template_type: self.create_from_template(t)
            )
            btn.grid(row=1 + i // 3, column=i % 3, padx=2, pady=2, sticky="ew")
        
        # Existing annotations list
        list_label = ctk.CTkLabel(
            list_frame,
            text="📋 Current Annotations",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        list_label.grid(row=2, column=0, pady=(15, 5), sticky="w")
        
        # Annotation listbox with scrollbar
        listbox_frame = ctk.CTkFrame(list_frame)
        listbox_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        listbox_frame.grid_columnconfigure(0, weight=1)
        listbox_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_rowconfigure(3, weight=1)
        
        self.annotation_listbox = tk.Listbox(
            listbox_frame,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f538d",
            selectforeground="white",
            font=("Segoe UI", 10)
        )
        self.annotation_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.annotation_listbox.bind('<<ListboxSelect>>', self.on_select_annotation)
        
        # List control buttons
        list_controls = ctk.CTkFrame(list_frame)
        list_controls.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 10))
        list_controls.grid_columnconfigure((0, 1, 2), weight=1)
        
        ctk.CTkButton(
            list_controls,
            text="➕ Add",
            command=self.add_annotation,
            width=80
        ).grid(row=0, column=0, padx=2, pady=5)
        
        ctk.CTkButton(
            list_controls,
            text="📝 Edit",
            command=self.edit_annotation,
            width=80
        ).grid(row=0, column=1, padx=2, pady=5)
        
        ctk.CTkButton(
            list_controls,
            text="🗑️ Delete",
            command=self.delete_annotation,
            width=80
        ).grid(row=0, column=2, padx=2, pady=5)

    def create_properties_panel(self):
        """Create properties and preview panel"""
        properties_frame = ctk.CTkFrame(self)
        properties_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        properties_frame.grid_columnconfigure(0, weight=1)
        properties_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            properties_frame,
            text="⚙️ Properties",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(10, 15), sticky="w")
        
        # Properties scroll frame
        self.properties_scroll = ctk.CTkScrollableFrame(properties_frame)
        self.properties_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.properties_scroll.grid_columnconfigure(0, weight=1)
        
        # Initially show placeholder
        self.show_placeholder_properties()

    def create_action_panel(self):
        """Create action buttons panel"""
        action_frame = ctk.CTkFrame(self)
        action_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(action_frame)
        button_frame.pack(side="right", padx=10, pady=10)
        
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="❌ Cancel",
            command=self.cancel,
            width=100
        )
        self.cancel_button.pack(side="left", padx=(0, 5))
        
        self.apply_button = ctk.CTkButton(
            button_frame,
            text="✅ Apply",
            command=self.apply,
            width=100
        )
        self.apply_button.pack(side="left", padx=5)
        
        self.ok_button = ctk.CTkButton(
            button_frame,
            text="💾 OK",
            command=self.ok,
            width=100,
            fg_color="green"
        )
        self.ok_button.pack(side="left", padx=(5, 0))

    def _create_templates(self) -> Dict[str, Dict[str, Any]]:
        """Create annotation templates"""
        return {
            "text": {
                "annotation_type": "text",
                "text": "Sample Text",
                "font_size": 12.0,
                "color": "#000000",
                "background_color": "#FFFFFF",
                "alpha": 0.8
            },
            "point": {
                "annotation_type": "point",
                "text": "Data Point",
                "marker": "o",
                "color": "#FF0000",
                "marker_size": 8.0
            },
            "arrow": {
                "annotation_type": "arrow",
                "text": "Arrow",
                "arrow_style": "->",
                "color": "#0000FF",
                "arrow_width": 2.0
            },
            "line": {
                "annotation_type": "line",
                "text": "Reference Line",
                "line_style": "-",
                "color": "#008000",
                "line_width": 2.0
            },
            "circle": {
                "annotation_type": "circle",
                "text": "Circle",
                "color": "#FF00FF",
                "fill": False,
                "radius": 0.1
            },
            "rectangle": {
                "annotation_type": "rectangle",
                "text": "Rectangle",
                "color": "#FFA500",
                "fill": False,
                "width": 0.2,
                "height": 0.1
            }
        }

    def create_from_template(self, template_type: str):
        """Create annotation from template"""
        if template_type not in self.annotation_templates:
            return
        
        template = self.annotation_templates[template_type].copy()
        
        # Create new annotation with template defaults
        annotation = AnnotationConfig(**template)
        
        # Add to manager
        self.annotation_manager.add_annotation(annotation)
        self.refresh_annotation_list()
        
        # Select the new annotation
        annotations = self.annotation_manager.get_annotations()
        if annotations:
            index = len(annotations) - 1
            self.annotation_listbox.selection_clear(0, tk.END)
            self.annotation_listbox.selection_set(index)
            self.annotation_listbox.activate(index)
            self.on_select_annotation(None)

    def refresh_annotation_list(self):
        """Refresh the annotation list display"""
        self.annotation_listbox.delete(0, tk.END)
        
        annotations = self.annotation_manager.get_annotations()
        for annotation in annotations:
            display_text = self._get_annotation_display_text(annotation)
            self.annotation_listbox.insert(tk.END, display_text)

    def _get_annotation_display_text(self, annotation: AnnotationConfig) -> str:
        """Get display text for annotation"""
        type_icons = {
            "text": "📝",
            "point": "📍",
            "arrow": "➡️",
            "line": "📏",
            "circle": "🔴",
            "rectangle": "📦"
        }
        
        icon = type_icons.get(annotation.annotation_type, "📋")
        text = annotation.text[:20] + "..." if len(annotation.text) > 20 else annotation.text
        return f"{icon} {text}"

    def on_select_annotation(self, event):
        """Handle annotation selection"""
        selection = self.annotation_listbox.curselection()
        if not selection:
            self.show_placeholder_properties()
            return
        
        index = selection[0]
        annotations = self.annotation_manager.get_annotations()
        if index < len(annotations):
            self.current_annotation = annotations[index]
            self.show_annotation_properties(self.current_annotation)

    def show_placeholder_properties(self):
        """Show placeholder when no annotation is selected"""
        # Clear properties
        for widget in self.properties_scroll.winfo_children():
            widget.destroy()
        
        placeholder_label = ctk.CTkLabel(
            self.properties_scroll,
            text="👈 Select an annotation or create a new one\nto see properties here",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        placeholder_label.pack(pady=50)

    def show_annotation_properties(self, annotation: AnnotationConfig):
        """Show properties for selected annotation"""
        # Clear previous properties
        for widget in self.properties_scroll.winfo_children():
            widget.destroy()
        
        # Create property fields based on annotation type
        self.create_basic_properties(annotation)
        self.create_position_properties(annotation)
        self.create_style_properties(annotation)
        self.create_type_specific_properties(annotation)

    def create_basic_properties(self, annotation: AnnotationConfig):
        """Create basic annotation properties"""
        basic_frame = ctk.CTkFrame(self.properties_scroll)
        basic_frame.pack(fill="x", padx=5, pady=5)
        basic_frame.grid_columnconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(
            basic_frame,
            text="📋 Basic Properties",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Type
        ctk.CTkLabel(basic_frame, text="Type:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.type_var = tk.StringVar(value=annotation.annotation_type)
        self.type_combo = ctk.CTkComboBox(
            basic_frame,
            variable=self.type_var,
            values=["text", "point", "arrow", "line", "circle", "rectangle"],
            command=self.on_type_change,
            width=150
        )
        self.type_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Text
        ctk.CTkLabel(basic_frame, text="Text:", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.text_var = tk.StringVar(value=annotation.text)
        self.text_entry = ctk.CTkEntry(basic_frame, textvariable=self.text_var, width=200)
        self.text_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.text_entry.bind('<KeyRelease>', self.on_property_change)
        
        # Visibility
        self.visible_var = tk.BooleanVar(value=annotation.visible)
        self.visible_check = ctk.CTkCheckBox(
            basic_frame,
            text="Visible",
            variable=self.visible_var,
            command=self.on_property_change
        )
        self.visible_check.grid(row=3, column=1, sticky="w", padx=5, pady=5)

    def create_position_properties(self, annotation: AnnotationConfig):
        """Create position properties"""
        position_frame = ctk.CTkFrame(self.properties_scroll)
        position_frame.pack(fill="x", padx=5, pady=5)
        position_frame.grid_columnconfigure((1, 3), weight=1)
        
        # Header
        ctk.CTkLabel(
            position_frame,
            text="📍 Position",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=4, pady=(10, 15), sticky="w")
        
        # X position
        ctk.CTkLabel(position_frame, text="X:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.x_var = tk.DoubleVar(value=annotation.x)
        self.x_entry = ctk.CTkEntry(position_frame, textvariable=self.x_var, width=100)
        self.x_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.x_entry.bind('<KeyRelease>', self.on_property_change)
        
        # Y position
        ctk.CTkLabel(position_frame, text="Y:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=2, sticky="w", padx=5, pady=5
        )
        self.y_var = tk.DoubleVar(value=annotation.y)
        self.y_entry = ctk.CTkEntry(position_frame, textvariable=self.y_var, width=100)
        self.y_entry.grid(row=1, column=3, sticky="w", padx=5, pady=5)
        self.y_entry.bind('<KeyRelease>', self.on_property_change)
        
        # For arrows and lines, add end position
        if annotation.annotation_type in ["arrow", "line"]:
            # X2 position
            ctk.CTkLabel(position_frame, text="X2:", font=ctk.CTkFont(weight="bold")).grid(
                row=2, column=0, sticky="w", padx=5, pady=5
            )
            self.x2_var = tk.DoubleVar(value=annotation.x2)
            self.x2_entry = ctk.CTkEntry(position_frame, textvariable=self.x2_var, width=100)
            self.x2_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
            self.x2_entry.bind('<KeyRelease>', self.on_property_change)
            
            # Y2 position
            ctk.CTkLabel(position_frame, text="Y2:", font=ctk.CTkFont(weight="bold")).grid(
                row=2, column=2, sticky="w", padx=5, pady=5
            )
            self.y2_var = tk.DoubleVar(value=annotation.y2)
            self.y2_entry = ctk.CTkEntry(position_frame, textvariable=self.y2_var, width=100)
            self.y2_entry.grid(row=2, column=3, sticky="w", padx=5, pady=5)
            self.y2_entry.bind('<KeyRelease>', self.on_property_change)

    def create_style_properties(self, annotation: AnnotationConfig):
        """Create style properties"""
        style_frame = ctk.CTkFrame(self.properties_scroll)
        style_frame.pack(fill="x", padx=5, pady=5)
        style_frame.grid_columnconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(
            style_frame,
            text="🎨 Style",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Color
        ctk.CTkLabel(style_frame, text="Color:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        
        color_frame = ctk.CTkFrame(style_frame)
        color_frame.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        self.color_var = tk.StringVar(value=annotation.color)
        self.color_button = ctk.CTkButton(
            color_frame,
            text="🎨",
            command=self.choose_color,
            fg_color=annotation.color,
            width=40
        )
        self.color_button.grid(row=0, column=0, padx=2)
        
        self.color_entry = ctk.CTkEntry(color_frame, textvariable=self.color_var, width=80)
        self.color_entry.grid(row=0, column=1, padx=2)
        self.color_entry.bind('<KeyRelease>', self.on_color_change)
        
        # Alpha
        ctk.CTkLabel(style_frame, text="Opacity:", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, sticky="w", padx=5, pady=5
        )
        self.alpha_var = tk.DoubleVar(value=annotation.alpha)
        self.alpha_slider = ctk.CTkSlider(
            style_frame,
            from_=0.0,
            to=1.0,
            variable=self.alpha_var,
            command=self.on_property_change,
            width=150
        )
        self.alpha_slider.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    def create_type_specific_properties(self, annotation: AnnotationConfig):
        """Create properties specific to annotation type"""
        if annotation.annotation_type == "text":
            self.create_text_properties(annotation)
        elif annotation.annotation_type in ["circle", "rectangle"]:
            self.create_shape_properties(annotation)
        elif annotation.annotation_type in ["arrow", "line"]:
            self.create_line_properties(annotation)

    def create_text_properties(self, annotation: AnnotationConfig):
        """Create text-specific properties"""
        text_frame = ctk.CTkFrame(self.properties_scroll)
        text_frame.pack(fill="x", padx=5, pady=5)
        text_frame.grid_columnconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(
            text_frame,
            text="📝 Text Properties",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Font size
        ctk.CTkLabel(text_frame, text="Font Size:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.font_size_var = tk.DoubleVar(value=annotation.font_size)
        self.font_size_entry = ctk.CTkEntry(text_frame, textvariable=self.font_size_var, width=80)
        self.font_size_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.font_size_entry.bind('<KeyRelease>', self.on_property_change)

    def create_shape_properties(self, annotation: AnnotationConfig):
        """Create shape-specific properties"""
        shape_frame = ctk.CTkFrame(self.properties_scroll)
        shape_frame.pack(fill="x", padx=5, pady=5)
        shape_frame.grid_columnconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(
            shape_frame,
            text="🔶 Shape Properties",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Fill
        self.fill_var = tk.BooleanVar(value=annotation.fill)
        self.fill_check = ctk.CTkCheckBox(
            shape_frame,
            text="Fill Shape",
            variable=self.fill_var,
            command=self.on_property_change
        )
        self.fill_check.grid(row=1, column=1, sticky="w", padx=5, pady=5)

    def create_line_properties(self, annotation: AnnotationConfig):
        """Create line-specific properties"""
        line_frame = ctk.CTkFrame(self.properties_scroll)
        line_frame.pack(fill="x", padx=5, pady=5)
        line_frame.grid_columnconfigure(1, weight=1)
        
        # Header
        ctk.CTkLabel(
            line_frame,
            text="📏 Line Properties",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")
        
        # Line style
        ctk.CTkLabel(line_frame, text="Style:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        self.line_style_var = tk.StringVar(value=annotation.line_style)
        self.line_style_combo = ctk.CTkComboBox(
            line_frame,
            variable=self.line_style_var,
            values=["-", "--", "-.", ":"],
            command=self.on_property_change,
            width=100
        )
        self.line_style_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)

    # Event handlers
    def on_type_change(self, value=None):
        """Handle annotation type change"""
        if self.current_annotation:
            self.current_annotation.annotation_type = self.type_var.get()
            self.show_annotation_properties(self.current_annotation)
            self.refresh_annotation_list()

    def on_property_change(self, event=None):
        """Handle property changes"""
        if not self.current_annotation:
            return
        
        # Update annotation properties from UI with safe type conversion
        self.current_annotation.text = self.text_var.get()
        self.current_annotation.visible = self.visible_var.get()
        
        # Safely handle x and y values that might be datetime strings
        try:
            x_value = self.x_var.get()
            self.current_annotation.x = x_value
        except tk.TclError:
            # If numeric conversion fails, try to use the string value directly
            try:
                x_str = self.x_entry.get()
                # Try to parse as datetime first
                import pandas as pd
                dt = pd.to_datetime(x_str)
                self.current_annotation.x = dt.timestamp() if hasattr(dt, 'timestamp') else dt
            except:
                # If all else fails, keep the original value
                pass
        
        try:
            y_value = self.y_var.get()
            self.current_annotation.y = y_value
        except tk.TclError:
            # If numeric conversion fails, try to use the string value directly
            try:
                y_str = self.y_entry.get()
                self.current_annotation.y = float(y_str)
            except:
                # If all else fails, keep the original value
                pass
                
        self.current_annotation.alpha = self.alpha_var.get()
        
        # Update type-specific properties with safe conversion
        if hasattr(self, 'x2_var'):
            try:
                self.current_annotation.x2 = self.x2_var.get()
            except tk.TclError:
                try:
                    x2_value = self.x2_var._tk.globalgetvar(self.x2_var._name)
                    self.current_annotation.x2 = x2_value
                except:
                    pass
                    
        if hasattr(self, 'y2_var'):
            try:
                self.current_annotation.y2 = self.y2_var.get()
            except tk.TclError:
                try:
                    y2_value = self.y2_var._tk.globalgetvar(self.y2_var._name)
                    self.current_annotation.y2 = y2_value
                except:
                    pass
        if hasattr(self, 'font_size_var'):
            self.current_annotation.font_size = self.font_size_var.get()
        if hasattr(self, 'fill_var'):
            self.current_annotation.fill = self.fill_var.get()
        if hasattr(self, 'line_style_var'):
            self.current_annotation.line_style = self.line_style_var.get()
        
        self.refresh_annotation_list()

    def on_color_change(self, event=None):
        """Handle color changes"""
        if self.current_annotation:
            color = self.color_var.get()
            self.current_annotation.color = color
            self.color_button.configure(fg_color=color)

    def choose_color(self):
        """Open color chooser dialog"""
        color = colorchooser.askcolor(title="Choose annotation color", color=self.color_var.get())
        if color[1]:  # User didn't cancel
            self.color_var.set(color[1])
            self.on_color_change()

    def add_annotation(self):
        """Add new annotation"""
        self.create_from_template("text")

    def edit_annotation(self):
        """Edit selected annotation"""
        selection = self.annotation_listbox.curselection()
        if selection:
            # Properties are already shown when selected
            pass
        else:
            messagebox.showinfo("No Selection", "Please select an annotation to edit.")

    def delete_annotation(self):
        """Delete selected annotation"""
        selection = self.annotation_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an annotation to delete.")
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this annotation?"):
            index = selection[0]
            annotations = self.annotation_manager.get_annotations()
            if index < len(annotations):
                self.annotation_manager.remove_annotation(annotations[index])
                self.refresh_annotation_list()
                self.show_placeholder_properties()

    def center_window(self):
        """Center dialog on parent window"""
        self.update_idletasks()
        
        # Get window size
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        pos_x = parent_x + (parent_width - window_width) // 2
        pos_y = parent_y + (parent_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

    def apply(self):
        """Apply current changes"""
        # Changes are applied in real-time, so just update the plot
        if self.plot_axes:
            self.annotation_manager.set_data_context(self.plot_axes)
            self.annotation_manager.draw_all_annotations(self.plot_axes)

    def ok(self):
        """Apply and close dialog"""
        self.apply()
        self.result = True
        self.destroy()

    def cancel(self):
        """Cancel and close dialog"""
        self.result = False
        self.destroy()


def show_modern_annotation_dialog(parent, annotation_manager: AnnotationManager, plot_axes=None) -> bool:
    """
    Show the modern annotation management dialog
    
    Args:
        parent: Parent window
        annotation_manager: Annotation manager instance
        plot_axes: Optional matplotlib axes for preview
        
    Returns:
        True if changes were applied, False if cancelled
    """
    try:
        dialog = ModernAnnotationDialog(parent, annotation_manager, plot_axes)
        parent.wait_window(dialog)
        return dialog.result or False
    except Exception as e:
        logger.error(f"Error showing annotation dialog: {e}")
        messagebox.showerror("Error", f"Failed to open annotation manager: {e}")
        return False
