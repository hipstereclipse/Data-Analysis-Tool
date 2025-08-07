#!/usr/bin/env python3
"""
Main application window and coordinator
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import logging
from typing import Dict, List, Optional
import json
from pathlib import Path

from config.constants import AppConfig, UIConfig
from models.data_models import FileData, SeriesConfig
from models.project_models import Project
from ui.components import StatusBar, QuickActionBar
from ui.panels import FilePanel, SeriesPanel, PlotPanel, ConfigPanel
from ui.dialogs import SeriesDialog, AnalysisDialog, AnnotationDialog
from core.file_manager import FileManager
from core.plot_manager import PlotManager
from core.annotation_manager import AnnotationManager
from core.project_manager import ProjectManager
from analysis.statistical import StatisticalAnalyzer
from analysis.vacuum import VacuumAnalyzer
from utils.helpers import format_file_size

logger = logging.getLogger(__name__)


class ExcelDataPlotterApp(ctk.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title(f"{AppConfig.APP_NAME} v{AppConfig.VERSION}")
        self.geometry(f"{UIConfig.DEFAULT_WIDTH}x{UIConfig.DEFAULT_HEIGHT}")
        self.minsize(UIConfig.MIN_WIDTH, UIConfig.MIN_HEIGHT)

        # Initialize managers
        self.file_manager = FileManager()
        self.plot_manager = PlotManager()
        self.annotation_manager = AnnotationManager()
        self.project_manager = ProjectManager()
        self.statistical_analyzer = StatisticalAnalyzer()
        self.vacuum_analyzer = VacuumAnalyzer()

        # Data storage
        self.loaded_files: Dict[str, FileData] = {}
        self.series_configs: Dict[str, SeriesConfig] = {}
        self.current_project: Optional[Project] = None

        # Build UI
        self._create_ui()
        self._bind_events()

        # Initialize
        self._initialize_state()

        logger.info("Application initialized successfully")

    def _create_ui(self):
        """Create the main UI layout"""
        # Configure grid weights
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Top action bar
        self.action_bar = QuickActionBar(self)
        self.action_bar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self._configure_action_bar()

        # Main content area with paned window
        self.paned_window = ctk.CTkTabview(self)
        self.paned_window.grid(row=1, column=0, sticky="nsew", padx=5, pady=0)

        # Create tabs
        self.files_tab = self.paned_window.add("Files")
        self.series_tab = self.paned_window.add("Series")
        self.plot_tab = self.paned_window.add("Plot")
        self.config_tab = self.paned_window.add("Configuration")

        # Initialize panels
        self.file_panel = FilePanel(self.files_tab, self)
        self.file_panel.pack(fill="both", expand=True)

        self.series_panel = SeriesPanel(self.series_tab, self)
        self.series_panel.pack(fill="both", expand=True)

        self.plot_panel = PlotPanel(self.plot_tab, self)
        self.plot_panel.pack(fill="both", expand=True)

        self.config_panel = ConfigPanel(self.config_tab, self)
        self.config_panel.pack(fill="both", expand=True)

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

    def _configure_action_bar(self):
        """Configure action bar buttons"""
        actions = [
            ("📁", "Add Files", self.add_files),
            ("💾", "Save Project", self.save_project),
            ("📂", "Load Project", self.load_project),
            ("📊", "Generate Plot", self.generate_plot),
            ("📤", "Export", self.export_plot),
            ("🔬", "Analysis", self.show_analysis),
            ("📍", "Annotations", self.show_annotations),
            ("🎨", "Theme", self.toggle_theme)
        ]

        for icon, tooltip, command in actions:
            self.action_bar.add_action(icon, command, tooltip)

    def _bind_events(self):
        """Bind keyboard and window events"""
        self.bind("<Control-o>", lambda e: self.add_files())
        self.bind("<Control-s>", lambda e: self.save_project())
        self.bind("<Control-p>", lambda e: self.generate_plot())
        self.bind("<F5>", lambda e: self.refresh_plot())
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _initialize_state(self):
        """Initialize application state"""
        self.status_bar.set_status("Ready", "info")
        self.update_counts()

    # File operations
    def add_files(self):
        """Add data files to the project"""
        files = self.file_manager.select_files()
        if not files:
            return

        success_count = 0
        errors = []

        self.status_bar.show_progress(0)

        for i, filepath in enumerate(files):
            try:
                self.status_bar.show_progress((i + 1) / len(files))
                file_data = self.file_manager.load_file(filepath)
                self.loaded_files[file_data.id] = file_data
                self.file_panel.add_file_card(file_data)
                success_count += 1

            except Exception as e:
                errors.append((filepath, str(e)))
                logger.error(f"Failed to load {filepath}: {e}")

        self.status_bar.hide_progress()

        if success_count > 0:
            self.status_bar.set_status(
                f"Loaded {success_count} file(s)", "success"
            )
            self.update_counts()

        if errors:
            self._show_error_report(errors)

    def remove_file(self, file_id: str):
        """Remove a file from the project"""
        if file_id in self.loaded_files:
            # Remove associated series
            series_to_remove = [
                sid for sid, series in self.series_configs.items()
                if series.file_id == file_id
            ]

            for series_id in series_to_remove:
                self.remove_series(series_id)

            # Remove file
            del self.loaded_files[file_id]
            self.file_panel.remove_file_card(file_id)
            self.update_counts()

            self.status_bar.set_status("File removed", "info")

    # Series operations
    def create_series(self):
        """Create a new data series"""
        if not self.loaded_files:
            messagebox.showwarning("No Files", "Please load data files first")
            return

        dialog = SeriesDialog(self, self.loaded_files, mode="create")
        self.wait_window(dialog.dialog)

        if dialog.result:
            series = dialog.result
            self.series_configs[series.id] = series
            self.series_panel.add_series_card(series)
            self.update_counts()
            self.status_bar.set_status("Series created", "success")

    def edit_series(self, series_id: str):
        """Edit an existing series"""
        if series_id not in self.series_configs:
            return

        series = self.series_configs[series_id]
        file_data = self.loaded_files.get(series.file_id)

        if not file_data:
            messagebox.showerror("Error", "Source file not found")
            return

        dialog = SeriesDialog(self, self.loaded_files, series, mode="edit")
        self.wait_window(dialog.dialog)

        if dialog.result:
            self.series_configs[series_id] = dialog.result
            self.series_panel.update_series_card(series_id)
            self.status_bar.set_status("Series updated", "success")

    def remove_series(self, series_id: str):
        """Remove a series"""
        if series_id in self.series_configs:
            del self.series_configs[series_id]
            self.series_panel.remove_series_card(series_id)
            self.update_counts()
            self.status_bar.set_status("Series removed", "info")

    # Plot operations
    def generate_plot(self):
        """Generate plot from configured series"""
        visible_series = [
            s for s in self.series_configs.values() if s.visible
        ]

        if not visible_series:
            messagebox.showwarning(
                "No Series",
                "Please create and enable at least one series"
            )
            return

        try:
            self.status_bar.set_status("Generating plot...", "info")

            # Get plot configuration
            config = self.config_panel.get_plot_config()

            # Generate plot
            figure = self.plot_manager.create_plot(
                visible_series,
                self.loaded_files,
                config
            )

            # Add annotations
            self.annotation_manager.apply_annotations(figure)

            # Display plot
            self.plot_panel.display_plot(figure)

            self.status_bar.set_status("Plot generated", "success")

        except Exception as e:
            logger.error(f"Plot generation failed: {e}")
            messagebox.showerror("Plot Error", str(e))
            self.status_bar.set_status("Plot generation failed", "error")

    def refresh_plot(self):
        """Refresh the current plot"""
        if self.plot_panel.has_plot():
            self.generate_plot()

    def export_plot(self):
        """Export plot or data"""
        if not self.plot_panel.has_plot():
            messagebox.showwarning("No Plot", "Please generate a plot first")
            return

        filepath = self.file_manager.save_file_dialog(
            title="Export Plot",
            filetypes=[
                ("PNG", "*.png"),
                ("PDF", "*.pdf"),
                ("SVG", "*.svg"),
                ("Excel", "*.xlsx"),
                ("CSV", "*.csv")
            ]
        )

        if filepath:
            try:
                ext = Path(filepath).suffix.lower()

                if ext in ['.png', '.pdf', '.svg']:
                    self.plot_manager.export_plot(filepath)
                elif ext in ['.xlsx', '.csv']:
                    self.export_data(filepath)

                self.status_bar.set_status(f"Exported to {filepath}", "success")

            except Exception as e:
                logger.error(f"Export failed: {e}")
                messagebox.showerror("Export Error", str(e))

    # Project operations
    def save_project(self):
        """Save current project"""
        filepath = self.file_manager.save_file_dialog(
            title="Save Project",
            filetypes=[("Project Files", "*.edp")]
        )

        if filepath:
            try:
                project = Project(
                    files=self.loaded_files,
                    series=self.series_configs,
                    annotations=self.annotation_manager.get_annotations(),
                    config=self.config_panel.get_plot_config()
                )

                self.project_manager.save_project(project, filepath)
                self.current_project = project
                self.status_bar.set_status("Project saved", "success")

            except Exception as e:
                logger.error(f"Save failed: {e}")
                messagebox.showerror("Save Error", str(e))

    def load_project(self):
        """Load a project file"""
        filepath = self.file_manager.open_file_dialog(
            title="Load Project",
            filetypes=[("Project Files", "*.edp")]
        )

        if filepath:
            try:
                project = self.project_manager.load_project(filepath)
                self._apply_project(project)
                self.current_project = project
                self.status_bar.set_status("Project loaded", "success")

            except Exception as e:
                logger.error(f"Load failed: {e}")
                messagebox.showerror("Load Error", str(e))

    # Analysis operations
    def show_analysis(self):
        """Show analysis dialog"""
        if not self.series_configs:
            messagebox.showwarning("No Series", "Please create series first")
            return

        dialog = AnalysisDialog(
            self,
            self.series_configs,
            self.loaded_files,
            self.statistical_analyzer,
            self.vacuum_analyzer
        )

    def show_annotations(self):
        """Show annotation manager"""
        dialog = AnnotationDialog(
            self,
            self.annotation_manager,
            self.plot_panel.get_axes()
        )
        self.wait_window(dialog.dialog)

        if dialog.changed:
            self.refresh_plot()

    # UI operations
    def toggle_theme(self):
        """Toggle between light and dark theme"""
        current = ctk.get_appearance_mode()
        new_mode = "dark" if current == "light" else "light"
        ctk.set_appearance_mode(new_mode)
        self.status_bar.set_status(f"Switched to {new_mode} mode", "info")

    def update_counts(self):
        """Update file and series counts"""
        self.status_bar.update_counts(
            files=len(self.loaded_files),
            series=len(self.series_configs)
        )

    def _show_error_report(self, errors: List[tuple]):
        """Show detailed error report"""
        report = "The following files failed to load:\n\n"
        for filepath, error in errors:
            report += f"• {Path(filepath).name}\n  {error}\n\n"

        messagebox.showerror("Load Errors", report)

    def _apply_project(self, project: Project):
        """Apply loaded project state"""
        # Clear current state
        self.loaded_files.clear()
        self.series_configs.clear()
        self.file_panel.clear()
        self.series_panel.clear()

        # Load project data
        self.loaded_files = project.files
        self.series_configs = project.series

        # Update UI
        for file_data in self.loaded_files.values():
            self.file_panel.add_file_card(file_data)

        for series in self.series_configs.values():
            self.series_panel.add_series_card(series)

        # Apply configuration
        self.config_panel.set_plot_config(project.config)

        # Apply annotations
        self.annotation_manager.set_annotations(project.annotations)

        self.update_counts()

    def export_data(self, filepath: str):
        """Export data to file"""
        # Implementation for data export
        pass

    def on_closing(self):
        """Handle window closing"""
        if self.loaded_files or self.series_configs:
            if messagebox.askokcancel("Quit", "Unsaved changes will be lost. Continue?"):
                self.destroy()
        else:
            self.destroy()