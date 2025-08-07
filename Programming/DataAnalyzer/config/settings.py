#!/usr/bin/env python3
"""
Application settings management
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class UserSettings:
    """User preferences and settings"""

    # Appearance
    theme: str = "system"  # "light", "dark", "system"
    color_scheme: str = "blue"  # Color theme
    font_size: int = 12

    # Window
    window_maximized: bool = False
    window_width: int = 1600
    window_height: int = 900
    window_x: Optional[int] = None
    window_y: Optional[int] = None

    # Defaults
    default_plot_type: str = "line"
    default_export_format: str = "png"
    default_export_dpi: int = 300
    auto_save_enabled: bool = True
    auto_save_interval: int = 300  # seconds

    # Recent files
    recent_files: List[str] = field(default_factory=list)
    recent_projects: List[str] = field(default_factory=list)
    max_recent_items: int = 10

    # Advanced
    enable_gpu: bool = False
    cache_size_mb: int = 100
    max_undo_steps: int = 50
    show_tooltips: bool = True
    confirm_exit: bool = True

    # Data handling
    default_missing_data_method: str = "drop"
    default_smoothing_window: int = 5
    auto_detect_datetime: bool = True

    # Performance
    chunk_size: int = 10000
    preview_rows: int = 1000
    enable_threading: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        """Create from dictionary"""
        return cls(**data)


class SettingsManager:
    """Manages application settings"""

    def __init__(self, app_dir: Optional[Path] = None):
        """
        Initialize settings manager

        Args:
            app_dir: Application directory for settings storage
        """
        if app_dir:
            self.app_dir = app_dir
        else:
            self.app_dir = Path.home() / ".excel_data_plotter"

        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.app_dir / "settings.json"

        self.settings = self.load_settings()

    def load_settings(self) -> UserSettings:
        """Load settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    return UserSettings.from_dict(data)
            except Exception as e:
                logger.error(f"Failed to load settings: {e}")

        return UserSettings()

    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            logger.info("Settings saved")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value"""
        return getattr(self.settings, key, default)

    def set(self, key: str, value: Any):
        """Set setting value"""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save_settings()

    def add_recent_file(self, filepath: str):
        """Add file to recent files list"""
        filepath = str(filepath)

        # Remove if already in list
        if filepath in self.settings.recent_files:
            self.settings.recent_files.remove(filepath)

        # Add to beginning
        self.settings.recent_files.insert(0, filepath)

        # Trim to max size
        if len(self.settings.recent_files) > self.settings.max_recent_items:
            self.settings.recent_files = self.settings.recent_files[:self.settings.max_recent_items]

        self.save_settings()

    def add_recent_project(self, filepath: str):
        """Add project to recent projects list"""
        filepath = str(filepath)

        if filepath in self.settings.recent_projects:
            self.settings.recent_projects.remove(filepath)

        self.settings.recent_projects.insert(0, filepath)

        if len(self.settings.recent_projects) > self.settings.max_recent_items:
            self.settings.recent_projects = self.settings.recent_projects[:self.settings.max_recent_items]

        self.save_settings()

    def clear_recent_files(self):
        """Clear recent files list"""
        self.settings.recent_files.clear()
        self.save_settings()

    def clear_recent_projects(self):
        """Clear recent projects list"""
        self.settings.recent_projects.clear()
        self.save_settings()

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = UserSettings()
        self.save_settings()