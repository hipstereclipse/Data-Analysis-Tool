#!/usr/bin/env python3
"""
Base class for themed dialogs
Provides common functionality and theming support for dialog windows
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from ui.theme_manager import theme_manager


class ThemedDialogBase:
    """Base class for themed dialogs with common functionality"""
    
    def __init__(self, parent, title: str, size: tuple = (800, 600)):
        """
        Initialize themed dialog base
        
        Args:
            parent: Parent window
            title: Dialog title
            size: Dialog size as (width, height) tuple
        """
        self.parent = parent
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{size[0]}x{size[1]}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Configure grid weights
        self.dialog.grid_columnconfigure(0, weight=1)
        self.dialog.grid_rowconfigure(0, weight=1)
        
        # Use the global theme manager instance
        self.theme_manager = theme_manager
        
        # Apply initial theme
        self.apply_theme()
        
        # Center dialog on parent
        self.center_dialog()
        
    def apply_theme(self):
        """Apply current theme to dialog"""
        try:
            # Use theme manager to get current theme colors
            theme_info = self.theme_manager.get_current_theme_info()
            colors = theme_info['colors']
            
            # Set dialog background based on current theme
            self.dialog.configure(bg=colors['bg_primary'])
            
        except Exception:
            # If theme manager fails, use default
            self.dialog.configure(bg='#f0f0f0')
    
    def center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        
        # Get parent position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_w = self.parent.winfo_width()
        parent_h = self.parent.winfo_height()
        
        # Get dialog size
        dialog_w = self.dialog.winfo_width()
        dialog_h = self.dialog.winfo_height()
        
        # Calculate centered position
        x = parent_x + (parent_w // 2) - (dialog_w // 2)
        y = parent_y + (parent_h // 2) - (dialog_h // 2)
        
        # Ensure dialog stays on screen
        x = max(0, x)
        y = max(0, y)
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def destroy(self):
        """Destroy the dialog"""
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.destroy()
    
    def close(self):
        """Close the dialog (alias for destroy)"""
        self.destroy()
    
    def show(self):
        """Show the dialog and wait for user input"""
        self.dialog.wait_window()
    
    def hide(self):
        """Hide the dialog"""
        if hasattr(self, 'dialog') and self.dialog:
            self.dialog.withdraw()
    
    def configure_styles(self):
        """Configure ttk styles for the dialog"""
        try:
            style = ttk.Style()
            theme_info = self.theme_manager.get_current_theme_info()
            colors = theme_info['colors']
            
            # Configure modern styles based on current theme
            style.configure('Dialog.TFrame', background=colors['bg_secondary'])
            style.configure('Dialog.TLabel', background=colors['bg_secondary'], foreground=colors['fg_primary'])
            style.configure('Dialog.TButton', background=colors['bg_tertiary'], foreground=colors['fg_primary'])
            style.configure('Heading.TLabel', font=theme_info['fonts']['heading'])
            style.configure('Title.TLabel', font=theme_info['fonts']['heading'])
            
        except Exception:
            # If styling fails, continue without custom styles
            pass
