#!/usr/bin/env python3
"""
Excel Data Plotter - Professional Edition
Main entry point for the application
"""

import sys
import logging
from pathlib import Path
import customtkinter as ctk
from app import ExcelDataPlotterApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)


def main():
    """Initialize and run the application"""
    try:
        # Set appearance mode and color theme
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        # Create and run application
        app = ExcelDataPlotterApp()
        app.mainloop()

    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()