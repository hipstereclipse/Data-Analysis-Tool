#!/usr/bin/env python3
"""
constants.py - Application-wide constants, color schemes, and styling configurations
This module centralizes all constants used throughout the application for easy maintenance
"""


class ColorPalette:
    """Defines color schemes for both light and dark modes"""

    # Light mode color definitions
    LIGHT_BG = "#F5F7FA"  # Light background color for main panels
    LIGHT_SURFACE = "#FFFFFF"  # White surface color for cards/panels
    LIGHT_SURFACE_2 = "#F8F9FA"  # Secondary surface color for nested elements
    LIGHT_BORDER = "#E1E4E8"  # Border color for light mode elements
    LIGHT_TEXT = "#2D3748"  # Primary text color in light mode
    LIGHT_TEXT_SECONDARY = "#718096"  # Secondary/muted text color in light mode

    # Dark mode color definitions
    DARK_BG = "#1A202C"  # Dark background color for main panels
    DARK_SURFACE = "#2D3748"  # Dark surface color for cards/panels
    DARK_SURFACE_2 = "#374151"  # Secondary dark surface color
    DARK_BORDER = "#4A5568"  # Border color for dark mode elements
    DARK_TEXT = "#F7FAFC"  # Primary text color in dark mode
    DARK_TEXT_SECONDARY = "#CBD5E0"  # Secondary/muted text color in dark mode

    # Accent colors (theme-independent)
    PRIMARY = "#3B82F6"  # Primary action color (blue)
    PRIMARY_HOVER = "#2563EB"  # Hover state for primary color
    SECONDARY = "#9C27B0"  # Secondary action color (purple)
    SECONDARY_HOVER = "#7B1FA2"  # Hover state for secondary color
    SUCCESS = "#10B981"  # Success/positive action color (green)
    WARNING = "#F59E0B"  # Warning/caution color (amber)
    ERROR = "#EF4444"  # Error/danger color (red)
    INFO = "#3B82F6"  # Information color (blue)

    # Chart color palette for data series
    CHART_COLORS = [
        "#3B82F6",  # Blue
        "#10B981",  # Green
        "#F59E0B",  # Amber
        "#EF4444",  # Red
        "#8B5CF6",  # Purple
        "#EC4899",  # Pink
        "#14B8A6",  # Teal
        "#F97316",  # Orange
        "#6366F1",  # Indigo
        "#84CC16"  # Lime
    ]


class Style:
    """Defines styling constants and helper methods"""

    # Color dictionary for easy access
    COLORS = {
        # Primary colors
        'primary': '#3B82F6',
        'primary_hover': '#2563EB',
        'primary_dark': '#1D4ED8',

        # Status colors
        'success': '#10B981',
        'warning': '#F59E0B',
        'error': '#EF4444',
        'info': '#3B82F6',

        # Neutral colors for light mode
        'bg_light': '#F9FAFB',
        'bg_dark': '#1F2937',
        'surface_light': '#FFFFFF',
        'surface_dark': '#374151',
        'border_light': '#E5E7EB',
        'border_dark': '#4B5563',
        'text_light': '#111827',
        'text_dark': '#F9FAFB',
        'text_secondary_light': '#6B7280',
        'text_secondary_dark': '#9CA3AF',
    }

    # Chart colors for data visualization
    CHART_COLORS = [
        '#3B82F6',  # Blue
        '#10B981',  # Green
        '#F59E0B',  # Amber
        '#EF4444',  # Red
        '#8B5CF6',  # Purple
        '#EC4899',  # Pink
        '#14B8A6',  # Teal
        '#F97316',  # Orange
        '#6366F1',  # Indigo
        '#84CC16'  # Lime
    ]

    @staticmethod
    def get_color(name, dark_mode=False):
        """
        Get color based on current theme mode

        Args:
            name (str): Color name to retrieve
            dark_mode (bool): Whether dark mode is active

        Returns:
            str: Hex color code
        """
        # Try to get theme-specific color first
        if dark_mode:
            # Look for dark mode specific color
            color = Style.COLORS.get(f'{name}_dark', Style.COLORS.get(name, '#FFFFFF'))
        else:
            # Look for light mode specific color
            color = Style.COLORS.get(f'{name}_light', Style.COLORS.get(name, '#000000'))
        return color


class AppConfig:
    """Application configuration constants"""

    # Application metadata
    APP_NAME = "Excel Data Plotter"
    APP_VERSION = "4.2"
    APP_SUBTITLE = "Vacuum Analysis Edition"

    # Window dimensions
    DEFAULT_WIDTH = 1600  # Default window width in pixels
    DEFAULT_HEIGHT = 900  # Default window height in pixels
    MIN_WIDTH = 1200  # Minimum window width
    MIN_HEIGHT = 700  # Minimum window height

    # Layout breakpoints for responsive design
    COMPACT_LAYOUT_WIDTH = 1400  # Width below which to use compact layout

    # File handling
    MAX_RECENT_FILES = 10  # Maximum number of recent files to remember
    AUTO_SAVE_INTERVAL = 300  # Auto-save interval in seconds (5 minutes)

    # Plotting defaults
    DEFAULT_FIG_WIDTH = 14.0  # Default figure width in inches
    DEFAULT_FIG_HEIGHT = 9.0  # Default figure height in inches
    DEFAULT_DPI = 100  # Default dots per inch for display
    EXPORT_DPI = 300  # DPI for exported images

    # Data handling
    DEFAULT_PREVIEW_ROWS = 10  # Number of rows to show in preview
    MAX_PREVIEW_ROWS = 1000  # Maximum rows for data preview
    SAMPLE_SIZE_FOR_LARGE_DATA = 500  # Sample size when data is too large

    # Animation and UI
    ANIMATION_SPEED = 10  # Animation speed in milliseconds
    ANIMATION_STEPS = 15  # Number of steps in animations
    TOOLTIP_DELAY = 500  # Delay before showing tooltips in milliseconds

    # Vacuum analysis defaults
    BASE_PRESSURE_WINDOW_MINUTES = 10  # Window size for base pressure calculation
    SPIKE_THRESHOLD_SIGMA = 3.0  # Standard deviations for spike detection
    DEFAULT_SAMPLE_RATE_HZ = 1.0  # Default sampling rate for vacuum data


class FileTypes:
    """Supported file types and their extensions"""

    # Excel file types
    EXCEL_EXTENSIONS = ["*.xlsx", "*.xls"]
    EXCEL_DESCRIPTION = "Excel files"

    # CSV file types
    CSV_EXTENSIONS = ["*.csv"]
    CSV_DESCRIPTION = "CSV files"

    # Project file types
    PROJECT_EXTENSIONS = ["*.json"]
    PROJECT_DESCRIPTION = "Project files"

    # Image export formats
    IMAGE_FORMATS = [
        ("PNG (High Quality)", "*.png"),
        ("PDF (Vector)", "*.pdf"),
        ("SVG (Scalable)", "*.svg"),
        ("JPG (Compressed)", "*.jpg")
    ]

    # All supported data formats
    ALL_DATA_FORMATS = [
        (EXCEL_DESCRIPTION, " ".join(EXCEL_EXTENSIONS)),
        (CSV_DESCRIPTION, " ".join(CSV_EXTENSIONS)),
        ("All files", "*.*")
    ]


class PlotTypes:
    """Available plot types and their configurations"""

    # Plot type identifiers
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    AREA = "area"
    BOX = "box"
    HEATMAP = "heatmap"

    # List of all available plot types
    ALL_TYPES = [LINE, SCATTER, BAR, AREA, BOX, HEATMAP]

    # Display names for plot types
    DISPLAY_NAMES = {
        LINE: "Line Plot",
        SCATTER: "Scatter Plot",
        BAR: "Bar Chart",
        AREA: "Area Chart",
        BOX: "Box Plot",
        HEATMAP: "Heat Map"
    }


class GridStyles:
    """Grid line styles for plots"""

    SOLID = "-"  # Solid line
    DASHED = "--"  # Dashed line
    DOTTED = ":"  # Dotted line
    DASHDOT = "-."  # Dash-dot line

    # All available styles
    ALL_STYLES = [SOLID, DASHED, DOTTED, DASHDOT]

    # Display names for styles
    DISPLAY_NAMES = {
        SOLID: "Solid",
        DASHED: "Dashed",
        DOTTED: "Dotted",
        DASHDOT: "Dash-Dot"
    }


class MissingDataMethods:
    """Methods for handling missing data in series"""

    INTERPOLATE = "interpolate"  # Interpolate missing values
    DROP = "drop"  # Remove missing values
    FILL_ZERO = "fill_zero"  # Replace with zero
    FORWARD_FILL = "forward_fill"  # Use previous valid value

    # All methods
    ALL_METHODS = [INTERPOLATE, DROP, FILL_ZERO, FORWARD_FILL]

    # Descriptions for UI
    DESCRIPTIONS = {
        INTERPOLATE: "Fill gaps with interpolated values",
        DROP: "Remove missing data points",
        FILL_ZERO: "Replace with zero",
        FORWARD_FILL: "Use previous valid value"
    }


class TrendTypes:
    """Types of trend lines available"""

    LINEAR = "linear"  # Linear regression
    POLYNOMIAL = "polynomial"  # Polynomial fit
    EXPONENTIAL = "exponential"  # Exponential fit
    MOVING_AVERAGE = "moving_average"  # Moving average

    # All trend types
    ALL_TYPES = [LINEAR, POLYNOMIAL, EXPONENTIAL, MOVING_AVERAGE]

    # Display names
    DISPLAY_NAMES = {
        LINEAR: "Linear",
        POLYNOMIAL: "Polynomial",
        EXPONENTIAL: "Exponential",
        MOVING_AVERAGE: "Moving Average"
    }


# Export DPI options for image export
EXPORT_DPI_OPTIONS = [150, 300, 600, 1200]

# Default margins for plots (as fractions of figure size)
DEFAULT_MARGINS = {
    'left': 0.1,
    'right': 0.05,
    'top': 0.1,
    'bottom': 0.1
}