#!/usr/bin/env python3
"""
Annotation Dialog - Unified implementation
Consolidated annotation management interface
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import customtkinter as ctk
from typing import Dict, List, Optional, Any
import logging

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
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Initialize variables
        self._init_variables()
        
        # Create widgets
        self._create_widgets()
        
        # Center dialog
        UIFactory.center_window(self.dialog, 900, 700)
        
        # Refresh annotation list
        self._refresh_annotation_list()
        
        # Bind coordinates to plot for slider ranges
        self._bind_coordinates_to_plot()
    
    def _init_variables(self):
        """Initialize dialog variables"""
        # Annotation properties
        self.text_var = tk.StringVar()
        self.x_pos_var = tk.DoubleVar()
        self.y_pos_var = tk.DoubleVar()
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
        self.background_alpha_var = tk.DoubleVar(value=0.8)
        self.border_thickness_var = tk.DoubleVar(value=1.0)
        
        # Annotation templates
        self.templates = self._create_templates()
    
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
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel - Tools
        tools_panel = ctk.CTkFrame(main_frame)
        tools_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        tools_panel.configure(width=350)
        
        # Right panel - Annotation list
        list_panel = ctk.CTkFrame(main_frame)
        list_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Create tool sections
        self._create_creation_tools(tools_panel)
        self._create_properties_panel(tools_panel)
        self._create_templates_panel(tools_panel)
        
        # Create annotation list
        self._create_annotation_list(list_panel)
        
        # Create button panel
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
        
        # Text input
        ctk.CTkLabel(content, text="Annotation Text:").pack(anchor="w", pady=(10, 2))
        text_entry = ctk.CTkEntry(content, textvariable=self.text_var, width=300)
        text_entry.pack(fill="x", pady=2)
        
        # Create button
        ctk.CTkButton(
            content,
            text="Create Annotation",
            command=self._create_annotation,
            width=200
        ).pack(pady=10)
    
    def _create_properties_panel(self, parent):
        """Create properties panel"""
        section = UIFactory.create_labeled_frame(parent, "Properties")
        section.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(section)
        content.pack(fill="x", padx=10, pady=5)
        
        # Color selection
        color_frame = ctk.CTkFrame(content)
        color_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(color_frame, text="Color:", width=80).pack(side="left")
        self.color_button = ctk.CTkButton(
            color_frame,
            text="",
            command=self._choose_color,
            width=50,
            fg_color=self.color_var.get()
        )
        self.color_button.pack(side="left", padx=5)
        
        # Font size
        font_frame = ctk.CTkFrame(content)
        font_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(font_frame, text="Font Size:", width=80).pack(side="left")
        ctk.CTkSlider(
            font_frame,
            from_=8,
            to=24,
            variable=self.font_size_var,
            width=150
        ).pack(side="left", padx=5)
        
        # Font weight
        weight_frame = ctk.CTkFrame(content)
        weight_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(weight_frame, text="Font Weight:", width=80).pack(side="left")
        ctk.CTkComboBox(
            weight_frame,
            variable=self.font_weight_var,
            values=["normal", "bold"],
            width=100
        ).pack(side="left", padx=5)
        
        # Options
        ctk.CTkCheckBox(content, text="Show Arrow", variable=self.arrow_var).pack(anchor="w", pady=2)
        
        # Arrow properties (only visible when arrow is enabled)
        arrow_frame = ctk.CTkFrame(content)
        arrow_frame.pack(fill="x", pady=5)
        
        # Arrow orientation
        orientation_frame = ctk.CTkFrame(arrow_frame)
        orientation_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(orientation_frame, text="Arrow Direction:", width=100).pack(side="left")
        ctk.CTkComboBox(
            orientation_frame,
            variable=self.arrow_orientation_var,
            values=["up", "down", "left", "right", "northeast", "northwest", "southeast", "southwest"],
            width=120
        ).pack(side="left", padx=5)
        
        # Arrow size
        arrow_size_frame = ctk.CTkFrame(arrow_frame)
        arrow_size_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(arrow_size_frame, text="Arrow Size:", width=100).pack(side="left")
        ctk.CTkSlider(
            arrow_size_frame,
            from_=5,
            to=30,
            variable=self.arrow_size_var,
            width=120
        ).pack(side="left", padx=5)
        
        # Line thickness
        line_thickness_frame = ctk.CTkFrame(content)
        line_thickness_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(line_thickness_frame, text="Line Thickness:", width=100).pack(side="left")
        ctk.CTkSlider(
            line_thickness_frame,
            from_=0.5,
            to=5.0,
            variable=self.line_thickness_var,
            width=150
        ).pack(side="left", padx=5)
        
        # Background and border options
        ctk.CTkCheckBox(content, text="Background", variable=self.background_var).pack(anchor="w", pady=2)
        
        # Background alpha (only visible when background is enabled)
        bg_alpha_frame = ctk.CTkFrame(content)
        bg_alpha_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(bg_alpha_frame, text="Background Alpha:", width=120).pack(side="left")
        ctk.CTkSlider(
            bg_alpha_frame,
            from_=0.1,
            to=1.0,
            variable=self.background_alpha_var,
            width=130
        ).pack(side="left", padx=5)
        
        ctk.CTkCheckBox(content, text="Border", variable=self.border_var).pack(anchor="w", pady=2)
        
        # Border thickness (only visible when border is enabled)
        border_thickness_frame = ctk.CTkFrame(content)
        border_thickness_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(border_thickness_frame, text="Border Thickness:", width=120).pack(side="left")
        ctk.CTkSlider(
            border_thickness_frame,
            from_=0.5,
            to=3.0,
            variable=self.border_thickness_var,
            width=130
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
        
        # Template buttons
        for template_name in self.templates.keys():
            btn = ctk.CTkButton(
                content,
                text=template_name,
                command=lambda name=template_name: self._apply_template(name),
                width=100
            )
            btn.pack(side="left", padx=2, pady=2)
    
    def _create_annotation_list(self, parent):
        """Create annotation list panel"""
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ctk.CTkLabel(parent, text="📝 Annotations", font=("", 16, "bold"))
        title.grid(row=0, column=0, pady=10)
        
        # List frame
        list_frame = ctk.CTkFrame(parent)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Annotation listbox
        self.annotation_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.SINGLE,
            font=("Consolas", 10)
        )
        self.annotation_listbox.grid(row=0, column=0, sticky="nsew")
        self.annotation_listbox.bind("<<ListboxSelect>>", self._on_select_annotation)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, command=self.annotation_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.annotation_listbox.config(yscrollcommand=scrollbar.set)
        
        # List controls
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        ctk.CTkButton(
            controls_frame,
            text="Delete Selected",
            command=self._delete_annotation,
            width=120
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            controls_frame,
            text="Clear All",
            command=self._clear_all_annotations,
            width=100
        ).pack(side="left", padx=5)
    
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
            self.x_pos_var.set(event.xdata)
            self.y_pos_var.set(event.ydata)
            
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
                
            except Exception as e:
                logger.warning(f"Could not bind coordinates to plot: {e}")
    
    def _create_annotation(self):
        """Create new annotation"""
        try:
            if not self.text_var.get().strip():
                messagebox.showerror("Error", "Please enter annotation text")
                return
            
            # Create annotation config
            annotation = AnnotationConfig(
                text=self.text_var.get().strip(),
                x_position=self.x_pos_var.get(),
                y_position=self.y_pos_var.get(),
                color=self.color_var.get(),
                font_size=self.font_size_var.get(),
                font_weight=self.font_weight_var.get(),
                show_arrow=self.arrow_var.get(),
                background=self.background_var.get(),
                border=self.border_var.get(),
                arrow_orientation=self.arrow_orientation_var.get(),
                line_thickness=self.line_thickness_var.get(),
                arrow_size=self.arrow_size_var.get(),
                background_alpha=self.background_alpha_var.get(),
                border_thickness=self.border_thickness_var.get()
            )
            
            # Add to manager
            self.annotation_manager.add_annotation(annotation)
            
            # Refresh list
            self._refresh_annotation_list()
            
            # Clear inputs
            self.text_var.set("")
            
            messagebox.showinfo("Success", "Annotation created successfully!")
            
        except Exception as e:
            logger.error(f"Error creating annotation: {e}")
            messagebox.showerror("Error", f"Failed to create annotation: {str(e)}")
    
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
        """Refresh the annotation list"""
        try:
            self.annotation_listbox.delete(0, tk.END)
            
            annotations = self.annotation_manager.get_annotations()
            for annotation in annotations:
                display_text = f"{annotation.text} ({annotation.x_position:.2f}, {annotation.y_position:.2f})"
                self.annotation_listbox.insert(tk.END, display_text)
                
        except Exception as e:
            logger.error(f"Error refreshing annotation list: {e}")
    
    def _on_select_annotation(self, event):
        """Handle annotation selection"""
        try:
            selection = self.annotation_listbox.curselection()
            if selection:
                index = selection[0]
                annotations = self.annotation_manager.get_annotations()
                
                if index < len(annotations):
                    self.current_annotation = annotations[index]
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
        self.result = 'close'
        self.dialog.destroy()


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
