#!/usr/bin/env python3
"""
Application constants and configuration
"""

from enum import Enum
from typing import List, Dict, Any


class AppConfig:
    """Application configuration"""
    APP_NAME = "Excel Data Plotter"
    VERSION = "5.0.0"
    AUTHOR = "Professional Edition"

    # File limits
    MAX_FILE_SIZE_MB = 500
    MAX_FILES = 50
    MAX_SERIES = 100

    # Performance
    CHUNK_SIZE = 10000
    PREVIEW_ROWS = 1000
    CACHE_SIZE = 100


class UIConfig:
    """UI configuration"""
    DEFAULT_WIDTH = 1600
    DEFAULT_HEIGHT = 900
    MIN_WIDTH = 1200
    MIN_HEIGHT = 700

    # Colors
    PRIMARY = "#3B82F6"
    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"

    # Chart colors
    CHART_COLORS = [
        "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
        "#8B5CF6", "#EC4899", "#14B8A6", "#F97316",
        "#6366F1", "#84CC16", "#06B6D4", "#A855F7"
    ]


class PlotConfig:
    """Default plot configuration"""
    FIGURE_WIDTH = 14
    FIGURE_HEIGHT = 9
    DPI = 100
    EXPORT_DPI = 300

    GRID_ALPHA = 0.3
    GRID_STYLE = "-"

    TITLE_SIZE = 16
    LABEL_SIZE = 12
    TICK_SIZE = 10
    LEGEND_SIZE = 10


class FileTypes(Enum):
    """Supported file types"""
    EXCEL = ("Excel Files", ["*.xlsx", "*.xls", "*.xlsm"])
    CSV = ("CSV Files", ["*.csv"])
    PROJECT = ("Project Files", ["*.edp"])

    @property
    def description(self) -> str:
        return self.value[0]

    @property
    def extensions(self) -> List[str]:
        return self.value[1]


class PlotTypes(Enum):
    """Available plot types"""
    LINE = "line"
    SCATTER = "scatter"
    BAR = "bar"
    AREA = "area"
    BOX = "box"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"


class MissingDataMethods(Enum):
    """Methods for handling missing data"""
    DROP = "drop"
    INTERPOLATE = "interpolate"
    FORWARD_FILL = "forward"
    BACKWARD_FILL = "backward"
    ZERO = "zero"
    MEAN = "mean"


class TrendTypes(Enum):
    """Trend line types"""
    LINEAR = "linear"
    POLYNOMIAL = "polynomial"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    POWER = "power"
    MOVING_AVERAGE = "moving_average"


class AnalysisTypes(Enum):
    """Analysis types"""
    BASIC_STATS = "basic_statistics"
    DISTRIBUTION = "distribution"
    CORRELATION = "correlation"
    REGRESSION = "regression"
    TIME_SERIES = "time_series"
    FREQUENCY = "frequency"
    OUTLIERS = "outliers"
    VACUUM = "vacuum"