#!/usr/bin/env python3
"""
Application constants and configuration
Complete implementation with all constants from original application
"""

from enum import Enum
from typing import List, Dict, Any, Tuple


class AppConfig:
    """Application configuration constants"""
    APP_NAME = "Professional Excel Data Plotter"
    APP_SUBTITLE = "Vacuum Analysis Edition"
    VERSION = "5.0.0"
    AUTHOR = "Professional Edition"

    # Window settings - responsive and DPI-aware defaults
    DEFAULT_WIDTH = 1200  # Reduced for better compatibility
    DEFAULT_HEIGHT = 750  # Reduced for better compatibility 
    MIN_WIDTH = 900       # Lowered minimum for smaller screens
    MIN_HEIGHT = 550      # Lowered minimum for smaller screens

    # File limits
    MAX_FILE_SIZE_MB = 500
    MAX_FILES = 50
    MAX_SERIES = 100

    # Performance
    CHUNK_SIZE = 10000
    PREVIEW_ROWS = 1000
    CACHE_SIZE = 100

    # Auto-save
    AUTOSAVE_INTERVAL = 300  # seconds
    BACKUP_COUNT = 5


class UIConfig:
    """UI configuration settings"""
    # Theme
    DEFAULT_THEME = "dark"

    # Colors - Using your original color scheme
    PRIMARY = "#3B82F6"
    SECONDARY = "#6366F1"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"

    # Panel sizes
    SIDE_PANEL_WIDTH = 350
    BOTTOM_PANEL_HEIGHT = 150

    # Fonts
    FONT_FAMILY = "Segoe UI"
    TITLE_FONT_SIZE = 16
    HEADING_FONT_SIZE = 14
    NORMAL_FONT_SIZE = 11
    SMALL_FONT_SIZE = 9


class ColorPalette:
    """Color palette for charts and UI elements"""
    # Chart colors - Professional palette
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
        "#84CC16",  # Lime
        "#06B6D4",  # Cyan
        "#A855F7",  # Violet
    ]

    # Status colors
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"
    SECONDARY = "#6B7280"

    # Data quality indicators
    GOOD_DATA = "#10B981"
    WARNING_DATA = "#F59E0B"
    BAD_DATA = "#EF4444"
    MISSING_DATA = "#9CA3AF"


class PlotConfig:
    """Default plot configuration"""
    FIGURE_WIDTH = 14
    FIGURE_HEIGHT = 9
    DPI = 100
    EXPORT_DPI = 300

    # Grid settings
    GRID_ALPHA = 0.3
    GRID_STYLE = "-"
    GRID_COLOR = "#E5E7EB"

    # Text sizes
    TITLE_SIZE = 16
    LABEL_SIZE = 12
    TICK_SIZE = 10
    LEGEND_SIZE = 10
    ANNOTATION_SIZE = 9

    # Margins (in inches)
    LEFT_MARGIN = 0.125
    RIGHT_MARGIN = 0.9
    TOP_MARGIN = 0.9
    BOTTOM_MARGIN = 0.125

    # Legend
    LEGEND_LOCATION = "best"
    LEGEND_FRAMEON = True
    LEGEND_FANCYBOX = True
    LEGEND_SHADOW = False
    LEGEND_NCOL = 1


class FileTypes(Enum):
    """Supported file types"""
    DATA = ("Data Files", ["*.xlsx", "*.xls", "*.xlsm", "*.xlsb", "*.csv", "*.tsv", "*.txt"])
    EXCEL = ("Excel Files", ["*.xlsx", "*.xls", "*.xlsm", "*.xlsb"])
    CSV = ("CSV Files", ["*.csv", "*.tsv", "*.txt"])
    PROJECT = ("Project Files", ["*.edp"])
    ALL = ("All Files", ["*.*"])

    @property
    def description(self) -> str:
        return self.value[0]

    @property
    def extensions(self) -> List[str]:
        return self.value[1]
    
    @property
    def filedialog_tuple(self) -> Tuple[str, str]:
        """Get tuple format for tkinter filedialog filetypes"""
        return (self.description, " ".join(self.extensions))


class PlotTypes(Enum):
    """Available plot types"""
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    AREA = "area"
    BOX = "box"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    STEP = "step"
    STEM = "stem"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """Get display names for UI"""
        return {
            cls.LINE.value: "Line Plot",
            cls.SCATTER.value: "Scatter Plot",
            cls.BAR.value: "Bar Chart",
            cls.AREA.value: "Area Plot",
            cls.BOX.value: "Box Plot",
            cls.HISTOGRAM.value: "Histogram",
            cls.HEATMAP.value: "Heat Map",
            cls.STEP.value: "Step Plot",
            cls.STEM.value: "Stem Plot"
        }


class MissingDataMethods(Enum):
    """Methods for handling missing data"""
    DROP = "drop"
    INTERPOLATE = "interpolate"
    FORWARD_FILL = "forward"
    BACKWARD_FILL = "backward"
    ZERO = "zero"
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """Get display names for UI"""
        return {
            cls.DROP.value: "Drop Missing",
            cls.INTERPOLATE.value: "Linear Interpolation",
            cls.FORWARD_FILL.value: "Forward Fill",
            cls.BACKWARD_FILL.value: "Backward Fill",
            cls.ZERO.value: "Fill with Zero",
            cls.MEAN.value: "Fill with Mean",
            cls.MEDIAN.value: "Fill with Median",
            cls.MODE.value: "Fill with Mode"
        }


class TrendTypes(Enum):
    """Trend line types for analysis"""
    LINEAR = "linear"
    POLYNOMIAL = "polynomial"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    POWER = "power"
    MOVING_AVERAGE = "moving_average"
    SAVGOL = "savitzky_golay"
    LOWESS = "lowess"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """Get display names for UI"""
        return {
            cls.LINEAR.value: "Linear Regression",
            cls.POLYNOMIAL.value: "Polynomial Fit",
            cls.EXPONENTIAL.value: "Exponential Fit",
            cls.LOGARITHMIC.value: "Logarithmic Fit",
            cls.POWER.value: "Power Law Fit",
            cls.MOVING_AVERAGE.value: "Moving Average",
            cls.SAVGOL.value: "Savitzky-Golay Filter",
            cls.LOWESS.value: "LOWESS Smoothing"
        }


class AnalysisTypes(Enum):
    """Types of analysis available"""
    BASIC_STATS = "basic_statistics"
    DISTRIBUTION = "distribution"
    CORRELATION = "correlation"
    REGRESSION = "regression"
    TIME_SERIES = "time_series"
    FREQUENCY = "frequency"
    OUTLIERS = "outliers"
    VACUUM = "vacuum_analysis"
    PEAKS = "peak_detection"
    NOISE = "noise_analysis"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """Get display names for UI"""
        return {
            cls.BASIC_STATS.value: "Basic Statistics",
            cls.DISTRIBUTION.value: "Distribution Analysis",
            cls.CORRELATION.value: "Correlation Analysis",
            cls.REGRESSION.value: "Regression Analysis",
            cls.TIME_SERIES.value: "Time Series Analysis",
            cls.FREQUENCY.value: "Frequency Analysis",
            cls.OUTLIERS.value: "Outlier Detection",
            cls.VACUUM.value: "Vacuum Analysis",
            cls.PEAKS.value: "Peak Detection",
            cls.NOISE.value: "Noise Analysis"
        }


class VacuumUnits(Enum):
    """Vacuum pressure units"""
    TORR = "Torr"
    MBAR = "mbar"
    PA = "Pa"
    PSI = "PSI"
    ATM = "atm"

    @classmethod
    def get_conversion_factors(cls) -> Dict[str, float]:
        """Get conversion factors to Torr"""
        return {
            cls.TORR.value: 1.0,
            cls.MBAR.value: 0.750062,
            cls.PA.value: 0.00750062,
            cls.PSI.value: 51.7149,
            cls.ATM.value: 760.0
        }


class ExportFormats(Enum):
    """Export format options"""
    PNG = ("PNG (High Quality)", "png", 300)
    PDF = ("PDF (Vector)", "pdf", None)
    SVG = ("SVG (Scalable)", "svg", None)
    JPG = ("JPG (Compressed)", "jpg", 150)
    TIFF = ("TIFF (Lossless)", "tiff", 300)
    EPS = ("EPS (PostScript)", "eps", None)

    @property
    def display_name(self) -> str:
        return self.value[0]

    @property
    def extension(self) -> str:
        return self.value[1]

    @property
    def default_dpi(self) -> int:
        return self.value[2]


class MarkerStyles(Enum):
    """Marker styles for plots"""
    NONE = ""
    POINT = "."
    CIRCLE = "o"
    SQUARE = "s"
    DIAMOND = "D"
    TRIANGLE_UP = "^"
    TRIANGLE_DOWN = "v"
    PLUS = "+"
    CROSS = "x"
    STAR = "*"

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """Get display names for UI"""
        return {
            cls.NONE.value: "None",
            cls.POINT.value: "Point",
            cls.CIRCLE.value: "Circle",
            cls.SQUARE.value: "Square",
            cls.DIAMOND.value: "Diamond",
            cls.TRIANGLE_UP.value: "Triangle Up",
            cls.TRIANGLE_DOWN.value: "Triangle Down",
            cls.PLUS.value: "Plus",
            cls.CROSS.value: "Cross",
            cls.STAR.value: "Star"
        }


class LineStyles(Enum):
    """Line styles for plots"""
    SOLID = "-"
    DASHED = "--"
    DOTTED = ":"
    DASHDOT = "-."
    NONE = ""

    @classmethod
    def get_display_names(cls) -> Dict[str, str]:
        """Get display names for UI"""
        return {
            cls.SOLID.value: "Solid",
            cls.DASHED.value: "Dashed",
            cls.DOTTED.value: "Dotted",
            cls.DASHDOT.value: "Dash-Dot",
            cls.NONE.value: "None"
        }


# Keyboard shortcuts
class KeyBindings:
    """Keyboard shortcuts for the application"""
    NEW_PROJECT = "<Control-n>"
    OPEN_PROJECT = "<Control-o>"
    SAVE_PROJECT = "<Control-s>"
    SAVE_AS = "<Control-Shift-S>"

    ADD_FILE = "<Control-Shift-O>"
    REMOVE_FILE = "<Delete>"

    ADD_SERIES = "<Control-Shift-N>"
    DUPLICATE_SERIES = "<Control-d>"

    REFRESH_PLOT = "<F5>"
    EXPORT_PLOT = "<Control-e>"

    UNDO = "<Control-z>"
    REDO = "<Control-y>"

    ZOOM_IN = "<Control-plus>"
    ZOOM_OUT = "<Control-minus>"
    ZOOM_RESET = "<Control-0>"

    TOGGLE_GRID = "<Control-g>"
    TOGGLE_LEGEND = "<Control-l>"
    TOGGLE_THEME = "<Control-t>"

    SHOW_HELP = "<F1>"
    QUIT = "<Control-q>"


# Default settings that can be saved/loaded
class DefaultSettings:
    """Default application settings"""
    RECENT_FILES_COUNT = 10
    AUTO_REFRESH = True
    CONFIRM_DELETE = True
    SHOW_TOOLTIPS = True
    SMOOTH_ANIMATIONS = True
    CHECK_UPDATES = True

    # Plot defaults
    DEFAULT_PLOT_TYPE = PlotTypes.LINE.value
    DEFAULT_MARKER = MarkerStyles.NONE.value
    DEFAULT_LINE_STYLE = LineStyles.SOLID.value
    DEFAULT_LINE_WIDTH = 1.5
    DEFAULT_MARKER_SIZE = 6

    # Data handling defaults
    DEFAULT_MISSING_METHOD = MissingDataMethods.INTERPOLATE.value
    DEFAULT_OUTLIER_METHOD = "zscore"
    DEFAULT_SMOOTHING = False
    DEFAULT_SMOOTH_FACTOR = 5

    # Export defaults
    DEFAULT_EXPORT_FORMAT = ExportFormats.PNG
    DEFAULT_EXPORT_DPI = 300
    DEFAULT_EXPORT_TRANSPARENT = False