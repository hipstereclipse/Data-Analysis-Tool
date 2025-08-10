#!/usr/bin/env python3
"""
Enhanced Theme Manager for consistent dark mode styling
"""

import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.style as mstyle
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class EnhancedThemeManager:
    """Manages consistent theming across the application"""
    
    def __init__(self):
        self.current_theme = "dark"
        self.themes = {
            "dark": {
                "ctk_appearance": "dark",
                "ctk_color_theme": "dark-blue",
                "matplotlib_style": "dark_background",
                "colors": {
                    "bg_primary": "#1a1a1a",
                    "bg_secondary": "#2b2b2b", 
                    "bg_tertiary": "#3c3c3c",
                    "fg_primary": "#ffffff",
                    "fg_secondary": "#b0b0b0",
                    "fg_disabled": "#666666",
                    "accent": "#1f77b4",
                    "accent_hover": "#2e86c1",
                    "success": "#27ae60",
                    "warning": "#f39c12",
                    "error": "#e74c3c",
                    "border": "#555555",
                    "selection": "#4a4a4a"
                },
                "fonts": {
                    "default": ("Segoe UI", 11),
                    "heading": ("Segoe UI", 14, "bold"),
                    "subheading": ("Segoe UI", 12, "bold"),
                    "small": ("Segoe UI", 9),
                    "monospace": ("Consolas", 10)
                }
            },
            "light": {
                "ctk_appearance": "light",
                "ctk_color_theme": "blue",
                "matplotlib_style": "default",
                "colors": {
                    "bg_primary": "#ffffff",
                    "bg_secondary": "#f8f9fa",
                    "bg_tertiary": "#e9ecef",
                    "fg_primary": "#212529",
                    "fg_secondary": "#495057",
                    "fg_disabled": "#6c757d",
                    "accent": "#007bff",
                    "accent_hover": "#0056b3",
                    "success": "#28a745",
                    "warning": "#ffc107",
                    "error": "#dc3545",
                    "border": "#dee2e6",
                    "selection": "#e3f2fd"
                },
                "fonts": {
                    "default": ("Segoe UI", 11),
                    "heading": ("Segoe UI", 14, "bold"),
                    "subheading": ("Segoe UI", 12, "bold"),
                    "small": ("Segoe UI", 9),
                    "monospace": ("Consolas", 10)
                }
            }
        }
        
        # Apply initial theme
        self.apply_theme(self.current_theme)
        
    def apply_theme(self, theme_name: str):
        """Apply the specified theme"""
        if theme_name not in self.themes:
            logger.warning(f"Unknown theme: {theme_name}, using dark theme")
            theme_name = "dark"
            
        self.current_theme = theme_name
        theme = self.themes[theme_name]
        
        try:
            # Apply CustomTkinter theme
            ctk.set_appearance_mode(theme["ctk_appearance"])
            ctk.set_default_color_theme(theme["ctk_color_theme"])
            
            # Apply matplotlib style
            plt.style.use(theme["matplotlib_style"])
            
            # Configure matplotlib colors for consistency
            if theme_name == "dark":
                plt.rcParams.update({
                    'figure.facecolor': theme["colors"]["bg_primary"],
                    'figure.edgecolor': theme["colors"]["border"],
                    'axes.facecolor': theme["colors"]["bg_secondary"],
                    'axes.edgecolor': theme["colors"]["border"],
                    'axes.labelcolor': theme["colors"]["fg_primary"],
                    'axes.titlecolor': theme["colors"]["fg_primary"],
                    'xtick.color': theme["colors"]["fg_primary"],
                    'ytick.color': theme["colors"]["fg_primary"],
                    'text.color': theme["colors"]["fg_primary"],
                    'grid.color': theme["colors"]["fg_secondary"],
                    'grid.alpha': 0.3,
                    'legend.facecolor': theme["colors"]["bg_secondary"],
                    'legend.edgecolor': theme["colors"]["border"],
                    'savefig.facecolor': theme["colors"]["bg_primary"],
                    'savefig.edgecolor': theme["colors"]["border"]
                })
            else:
                # Reset to light defaults
                plt.rcParams.update({
                    'figure.facecolor': 'white',
                    'figure.edgecolor': 'white',
                    'axes.facecolor': 'white',
                    'axes.edgecolor': 'black',
                    'axes.labelcolor': 'black',
                    'axes.titlecolor': 'black',
                    'xtick.color': 'black',
                    'ytick.color': 'black',
                    'text.color': 'black',
                    'grid.color': 'gray',
                    'grid.alpha': 0.5,
                    'legend.facecolor': 'white',
                    'legend.edgecolor': 'black',
                    'savefig.facecolor': 'white',
                    'savefig.edgecolor': 'white'
                })
                
            logger.info(f"Applied theme: {theme_name}")
            
        except Exception as e:
            logger.error(f"Error applying theme {theme_name}: {e}")
            
    def get_color(self, color_name: str) -> str:
        """Get a color from the current theme"""
        theme = self.themes[self.current_theme]
        return theme["colors"].get(color_name, "#000000")
        
    def get_font(self, font_name: str) -> tuple:
        """Get a font from the current theme"""
        theme = self.themes[self.current_theme]
        return theme["fonts"].get(font_name, ("Segoe UI", 11))
        
    def configure_matplotlib_figure(self, fig, ax=None):
        """Configure matplotlib figure with current theme"""
        theme = self.themes[self.current_theme]
        colors = theme["colors"]
        
        # Configure figure
        fig.patch.set_facecolor(colors["bg_primary"])
        fig.patch.set_edgecolor(colors["border"])
        
        if ax is not None:
            # Configure axes
            ax.set_facecolor(colors["bg_secondary"])
            ax.tick_params(colors=colors["fg_primary"])
            ax.spines['bottom'].set_color(colors["border"])
            ax.spines['top'].set_color(colors["border"])
            ax.spines['left'].set_color(colors["border"])
            ax.spines['right'].set_color(colors["border"])
            ax.xaxis.label.set_color(colors["fg_primary"])
            ax.yaxis.label.set_color(colors["fg_primary"])
            ax.title.set_color(colors["fg_primary"])
            ax.grid(True, alpha=0.3, color=colors["fg_secondary"])
            
    def create_styled_button(self, parent, text: str, command=None, **kwargs) -> ctk.CTkButton:
        """Create a styled button with theme colors"""
        theme = self.themes[self.current_theme]
        colors = theme["colors"]
        
        default_kwargs = {
            "fg_color": colors["accent"],
            "hover_color": colors["accent_hover"],
            "text_color": colors["fg_primary"],
            "font": theme["fonts"]["default"]
        }
        default_kwargs.update(kwargs)
        
        return ctk.CTkButton(parent, text=text, command=command, **default_kwargs)
        
    def create_styled_entry(self, parent, **kwargs) -> ctk.CTkEntry:
        """Create a styled entry with theme colors"""
        theme = self.themes[self.current_theme]
        colors = theme["colors"]
        
        default_kwargs = {
            "text_color": colors["fg_primary"],
            "fg_color": colors["bg_secondary"],
            "border_color": colors["border"],
            "font": theme["fonts"]["default"]
        }
        default_kwargs.update(kwargs)
        
        return ctk.CTkEntry(parent, **default_kwargs)
        
    def create_styled_label(self, parent, text: str, style: str = "default", **kwargs) -> ctk.CTkLabel:
        """Create a styled label with theme colors"""
        theme = self.themes[self.current_theme]
        colors = theme["colors"]
        
        font_map = {
            "default": theme["fonts"]["default"],
            "heading": theme["fonts"]["heading"],
            "subheading": theme["fonts"]["subheading"],
            "small": theme["fonts"]["small"],
            "monospace": theme["fonts"]["monospace"]
        }
        
        default_kwargs = {
            "text_color": colors["fg_primary"],
            "font": font_map.get(style, theme["fonts"]["default"])
        }
        default_kwargs.update(kwargs)
        
        return ctk.CTkLabel(parent, text=text, **default_kwargs)
        
    def create_styled_frame(self, parent, **kwargs) -> ctk.CTkFrame:
        """Create a styled frame with theme colors"""
        theme = self.themes[self.current_theme]
        colors = theme["colors"]
        
        default_kwargs = {
            "fg_color": colors["bg_secondary"],
            "border_color": colors["border"]
        }
        default_kwargs.update(kwargs)
        
        return ctk.CTkFrame(parent, **default_kwargs)
        
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.apply_theme(new_theme)
        
    def get_series_colors(self, count: int) -> list:
        """Get a list of distinct colors for series"""
        base_colors = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
            "#aec7e8", "#ffbb78", "#98df8a", "#ff9896", "#c5b0d5",
            "#c49c94", "#f7b6d3", "#c7c7c7", "#dbdb8d", "#9edae5"
        ]
        
        # Cycle through colors if more series than colors
        colors = []
        for i in range(count):
            colors.append(base_colors[i % len(base_colors)])
            
        return colors
        
    def get_current_theme_info(self) -> Dict[str, Any]:
        """Get information about the current theme"""
        return {
            "name": self.current_theme,
            "colors": self.themes[self.current_theme]["colors"].copy(),
            "fonts": self.themes[self.current_theme]["fonts"].copy()
        }

# Global theme manager instance
theme_manager = EnhancedThemeManager()
