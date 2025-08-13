#!/usr/bin/env python3
"""
Test script for annotation manager preview functionality
"""

import tkinter as tk
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

from core.annotation_manager import AnnotationManager
from ui.annotation_dialog import AnnotationDialog

def test_preview_functionality():
    """Test the annotation preview functionality"""
    print("Testing annotation preview functionality...")
    
    # Create a test root window
    root = ctk.CTk()
    root.title("Test Annotation Preview")
    root.geometry("800x600")
    
    # Create a simple plot
    fig = Figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    
    # Generate test data
    x = np.linspace(0, 10, 100)
    y = np.sin(x) + 0.1 * np.random.randn(100)
    
    ax.plot(x, y, 'b-', label='Test Data')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Embed plot in tkinter
    canvas = FigureCanvasTkAgg(fig, root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)
    
    # Create annotation manager
    annotation_manager = AnnotationManager()
    annotation_manager.set_data_context(ax)
    
    # Test basic annotation methods
    try:
        # Test preview mode
        annotation_manager.start_preview_mode()
        print("✓ Preview mode started successfully")
        
        # Test adding a text annotation
        annotation_manager.add_text(5, 0.5, "Test Text", color="red")
        print("✓ Text annotation added successfully")
        
        # Test adding a line
        annotation_manager.add_line(2, 0, 8, 1, color="blue")
        print("✓ Line annotation added successfully")
        
        # Test adding an arrow
        annotation_manager.add_arrow(3, -0.5, 7, 0.5, color="green")
        print("✓ Arrow annotation added successfully")
        
        # Test clearing preview
        annotation_manager.clear_preview()
        print("✓ Preview cleared successfully")
        
        print("\n✓ All annotation manager tests passed!")
        
    except Exception as e:
        print(f"✗ Error testing annotation manager: {e}")
        return False
    
    # Test annotation dialog
    def test_dialog():
        try:
            dialog = AnnotationDialog(root, annotation_manager)
            print("✓ Annotation dialog created successfully")
            return True
        except Exception as e:
            print(f"✗ Error creating annotation dialog: {e}")
            return False
    
    # Add button to test dialog
    btn_frame = ctk.CTkFrame(root)
    btn_frame.pack(pady=10)
    
    ctk.CTkButton(
        btn_frame,
        text="Open Annotation Dialog",
        command=test_dialog
    ).pack(side="left", padx=5)
    
    ctk.CTkButton(
        btn_frame,
        text="Test Preview Mode",
        command=lambda: annotation_manager.start_preview_mode()
    ).pack(side="left", padx=5)
    
    ctk.CTkButton(
        btn_frame,
        text="Clear Preview",
        command=lambda: annotation_manager.clear_preview()
    ).pack(side="left", padx=5)
    
    print("\nAnnotation preview test window opened.")
    print("Use the buttons to test the functionality.")
    print("Close the window when done.")
    
    root.mainloop()
    return True

if __name__ == "__main__":
    test_preview_functionality()
