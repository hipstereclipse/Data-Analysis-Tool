#!/usr/bin/env python3
"""
Quick validation script for the modernized annotation dialog
Tests the new data-driven features and UI improvements
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import customtkinter as ctk

from core.annotation_manager import AnnotationManager
from ui.annotation_dialog import AnnotationDialog
from models.data_models import AnnotationConfig

def test_annotation_ui():
    """Test the modernized annotation UI"""
    print("Creating test UI for annotation dialog...")
    
    # Create test data
    x = np.linspace(0, 10, 100)
    y = np.sin(x) + 0.1 * np.random.randn(100)
    
    # Create root window
    root = ctk.CTk()
    root.title("Annotation Dialog Test")
    root.geometry("800x600")
    
    # Create matplotlib figure
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(x, y, label="Test Data", color="#3B82F6")
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.set_title("Test Plot for Annotation Dialog")
    ax.grid(True)
    ax.legend()
    
    # Create canvas
    canvas = FigureCanvasTkAgg(fig, root)
    canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # Create annotation manager
    annotation_manager = AnnotationManager()
    annotation_manager.set_data_context(ax)
    
    def open_annotation_dialog():
        """Open the modernized annotation dialog"""
        try:
            dialog = AnnotationDialog(root, annotation_manager, ax)
            root.wait_window(dialog.dialog)
            print(f"Dialog closed. Total annotations: {len(annotation_manager.get_annotations())}")
        except Exception as e:
            print(f"Error opening annotation dialog: {e}")
            import traceback
            traceback.print_exc()
    
    # Add test button
    button_frame = ctk.CTkFrame(root)
    button_frame.pack(fill="x", padx=10, pady=5)
    
    open_btn = ctk.CTkButton(
        button_frame,
        text="Open Annotation Dialog",
        command=open_annotation_dialog,
        font=("Arial", 14, "bold")
    )
    open_btn.pack(side="left", padx=5)
    
    info_label = ctk.CTkLabel(
        button_frame,
        text="Test the modernized annotation system with real-time preview, data tools, and management features!",
        font=("Arial", 12)
    )
    info_label.pack(side="left", padx=10)
    
    print("UI created successfully!")
    print("\nFeatures to test:")
    print("1. Creation Tools: Text, Line, Arrow, Rect, Circle, Point")
    print("2. Live Preview: Toggle and watch real-time updates")
    print("3. On-plot Picking: 'Pick End on Plot' and 'Pick Both Points' modes")
    print("4. Data Tools: Mean/Median, Std Band, Min/Max, Peaks, Crossings, Trendline")
    print("5. Snap-to-Data: Enable to snap picks to nearest data points")
    print("6. Management: Move Up/Down, Toggle Visibility, Duplicate, Export/Import")
    print("\nClick 'Open Annotation Dialog' to start testing!")
    
    # Start GUI
    root.mainloop()

if __name__ == "__main__":
    test_annotation_ui()
