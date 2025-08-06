#!/usr/bin/env python3
"""
models.py - Data models and structures for the Excel Data Plotter
Contains classes that represent the core data structures used throughout the application
"""

import uuid  # For generating unique identifiers
import os  # For file path operations
from datetime import datetime  # For timestamp tracking
import pandas as pd  # For data manipulation
import numpy as np  # For numerical operations
from constants import MissingDataMethods, TrendTypes  # Import constants


class FileData:
    """
    Container for loaded file data and metadata
    Represents a single Excel or CSV file loaded into the application
    """

    def __init__(self, filepath, dataframe):
        """
        Initialize a FileData object

        Args:
            filepath (str): Full path to the file
            dataframe (pd.DataFrame): Pandas DataFrame containing the file data
        """
        # Generate unique identifier for this file
        self.id = str(uuid.uuid4())

        # Store file path and extract filename
        self.filepath = filepath
        self.filename = os.path.basename(filepath)

        # Store the dataframe and keep original copy for reset functionality
        self.df = dataframe
        self.original_df = dataframe.copy()

        # Track when file was loaded
        self.load_time = datetime.now()

        # List of series IDs that use this file
        self.series_list = []


class SeriesConfig:
    """
    Configuration for a data series to be plotted
    Contains all settings for how a series should be displayed and processed
    """

    def __init__(self, name, file_id, x_col, y_col, start_idx=None, end_idx=None):
        """
        Initialize a series configuration

        Args:
            name (str): Display name for the series
            file_id (str): ID of the FileData this series uses
            x_col (str): Column name for X axis data
            y_col (str): Column name for Y axis data
            start_idx (int, optional): Starting row index
            end_idx (int, optional): Ending row index
        """
        # Unique identifier for this series
        self.id = str(uuid.uuid4())

        # Basic identification
        self.name = name  # User-friendly name
        self.file_id = file_id  # Reference to source file

        # Data columns
        self.x_column = x_col  # X-axis data column
        self.y_column = y_col  # Y-axis data column

        # Data range (row indices)
        self.start_index = start_idx if start_idx is not None else 0
        self.end_index = end_idx  # None means use all data

        # Visual appearance settings
        self.color = None  # Plot color (auto-assigned if None)
        self.line_style = '-'  # Line style: '-', '--', ':', '-.'
        self.marker = ''  # Marker style (empty = no markers)
        self.line_width = 2.5  # Line thickness
        self.marker_size = 6  # Size of data point markers
        self.alpha = 0.9  # Transparency (0=transparent, 1=opaque)
        self.fill_area = False  # Whether to fill area under curve
        self.gradient_fill = False  # Use gradient for area fill

        # Data processing settings
        self.missing_data_method = MissingDataMethods.INTERPOLATE  # How to handle NaN values
        self.outlier_handling = 'keep'  # How to handle outliers: 'keep', 'remove', 'cap'
        self.outlier_threshold = 3.0  # Standard deviations for outlier detection
        self.smoothing = False  # Whether to apply smoothing
        self.smooth_factor = 0  # Smoothing strength (0-100)

        # Date/time handling
        self.datetime_format = 'auto'  # Format for parsing datetime columns
        self.custom_datetime_format = '%Y-%m-%d %H:%M:%S'  # Custom format string
        self.timezone = None  # Timezone for datetime data

        # Display options
        self.visible = True  # Whether series is shown on plot
        self.show_in_legend = True  # Whether to include in legend
        self.legend_label = name  # Text shown in legend
        self.y_axis = 'left'  # Which Y-axis to use: 'left' or 'right'

        # Analysis features
        self.show_statistics = False  # Show statistics box on plot
        self.show_trendline = False  # Display trend line
        self.trend_type = TrendTypes.LINEAR  # Type of trend line
        self.trend_params = {'degree': 1, 'window': 20}  # Parameters for trend calculation
        self.show_peaks = False  # Mark peaks and valleys
        self.peak_prominence = 0.1  # Sensitivity for peak detection

        # Additional display options
        self.missing_data_color = 'red'  # Color for highlighting missing data
        self.show_moving_average = False  # Display moving average line
        self.moving_average_window = 20  # Window size for moving average
        self.show_confidence_interval = False  # Show confidence bands
        self.confidence_level = 0.95  # Confidence level for bands

        # Time-based highlighting
        self.highlight_weekends = False  # Highlight weekend periods
        self.highlight_business_hours = False  # Highlight business hours

        # Data quality indicators
        self.highlight_outliers = False  # Mark outlier points
        self.outlier_method = 'keep'  # Method for outlier handling

        # Vacuum-specific features
        self.highlight_base_pressure = False  # Show base pressure line
        self.highlight_spikes = False  # Mark pressure spikes


class AnnotationConfig:
    """
    Configuration for plot annotations
    Represents text, lines, shapes, and other markers on the plot
    """

    def __init__(self, ann_type, **kwargs):
        """
        Initialize an annotation configuration

        Args:
            ann_type (str): Type of annotation ('vline', 'hline', 'region', 'text', 'point', 'arrow')
            **kwargs: Additional parameters specific to annotation type
        """
        # Unique identifier
        self.id = str(uuid.uuid4())

        # Annotation type
        self.type = ann_type

        # Common properties
        self.visible = kwargs.get('visible', True)  # Whether annotation is shown
        self.editable = kwargs.get('editable', True)  # Whether user can edit
        self.label = kwargs.get('label', '')  # Text label for annotation

        # Visual properties
        self.color = kwargs.get('color', 'red')  # Annotation color
        self.alpha = kwargs.get('alpha', 0.8)  # Transparency
        self.line_width = kwargs.get('width', 2)  # Line thickness
        self.line_style = kwargs.get('style', '-')  # Line style

        # Position properties (varies by type)
        if ann_type == 'vline':
            self.x_pos = kwargs.get('x_pos', 0)  # X position for vertical line
        elif ann_type == 'hline':
            self.y_pos = kwargs.get('y_pos', 0)  # Y position for horizontal line
        elif ann_type == 'region':
            self.x_start = kwargs.get('x_start', 0)  # Start X for region
            self.x_end = kwargs.get('x_end', 1)  # End X for region
        elif ann_type == 'text':
            self.x_pos = kwargs.get('x_pos', 0)  # X position for text
            self.y_pos = kwargs.get('y_pos', 0)  # Y position for text
            self.text = kwargs.get('text', 'Annotation')  # Text content
            self.fontsize = kwargs.get('fontsize', 12)  # Font size
            self.bbox = kwargs.get('bbox', None)  # Background box properties
        elif ann_type == 'point':
            self.x_pos = kwargs.get('x_pos', 0)  # X position for point
            self.y_pos = kwargs.get('y_pos', 0)  # Y position for point
            self.marker = kwargs.get('marker', 'o')  # Marker style
            self.size = kwargs.get('size', 100)  # Marker size
        elif ann_type == 'arrow':
            self.x_start = kwargs.get('x_start', 0)  # Arrow start X
            self.y_start = kwargs.get('y_start', 0)  # Arrow start Y
            self.x_end = kwargs.get('x_end', 1)  # Arrow end X
            self.y_end = kwargs.get('y_end', 1)  # Arrow end Y
            self.arrow_style = kwargs.get('arrow_style', '->')  # Arrow head style


class ProjectData:
    """
    Container for entire project state
    Used for saving and loading project configurations
    """

    def __init__(self):
        """Initialize empty project data"""
        # Project metadata
        self.version = '1.0'  # Project file format version
        self.creation_date = datetime.now().isoformat()  # When project was created
        self.last_modified = datetime.now().isoformat()  # Last modification time

        # Project content
        self.files = []  # List of file references
        self.series = []  # List of series configurations
        self.annotations = []  # List of annotations

        # Plot configuration
        self.plot_config = {
            'title': 'Multi-File Data Analysis',
            'title_size': 16,
            'xlabel': 'X Axis',
            'xlabel_size': 12,
            'ylabel': 'Y Axis',
            'ylabel_size': 12,
            'log_scale_x': False,
            'log_scale_y': False,
            'show_grid': True,
            'show_legend': True,
            'grid_style': '-',
            'grid_alpha': 0.3,
            'fig_width': 14.0,
            'fig_height': 9.0,
            'plot_type': 'line'
        }

        # Window state
        self.window_state = {
            'width': 1600,
            'height': 900,
            'x_pos': None,  # Window X position
            'y_pos': None,  # Window Y position
            'maximized': False,
            'current_layout': 'default'
        }

    def add_file(self, file_data):
        """
        Add a file reference to the project

        Args:
            file_data (FileData): File data object to add
        """
        file_info = {
            'id': file_data.id,
            'filepath': file_data.filepath,
            'filename': file_data.filename,
            'load_time': file_data.load_time.isoformat()
        }
        self.files.append(file_info)

    def add_series(self, series):
        """
        Add a series configuration to the project

        Args:
            series (SeriesConfig): Series configuration to add
        """
        series_info = {
            'id': series.id,
            'name': series.name,
            'file_id': series.file_id,
            'x_column': series.x_column,
            'y_column': series.y_column,
            'start_index': series.start_index,
            'end_index': series.end_index,
            'color': series.color,
            'line_style': series.line_style,
            'marker': series.marker,
            'line_width': series.line_width,
            'marker_size': series.marker_size,
            'alpha': series.alpha,
            'fill_area': series.fill_area,
            'visible': series.visible,
            'legend_label': series.legend_label,
            'missing_data_method': series.missing_data_method,
            'show_trendline': series.show_trendline,
            'trend_type': series.trend_type,
            'trend_params': series.trend_params
        }
        self.series.append(series_info)


class AnalysisResult:
    """
    Container for analysis results
    Stores results from various analysis operations
    """

    def __init__(self, analysis_type):
        """
        Initialize analysis result container

        Args:
            analysis_type (str): Type of analysis performed
        """
        self.type = analysis_type  # Type of analysis
        self.timestamp = datetime.now()  # When analysis was performed
        self.series_id = None  # ID of series analyzed
        self.series_name = None  # Name of series analyzed
        self.results = {}  # Dictionary of result values
        self.metadata = {}  # Additional metadata

    def add_result(self, key, value, unit=None):
        """
        Add a result value

        Args:
            key (str): Result name
            value: Result value
            unit (str, optional): Unit of measurement
        """
        self.results[key] = {
            'value': value,
            'unit': unit
        }

    def get_summary(self):
        """
        Get a text summary of the analysis results

        Returns:
            str: Formatted summary text
        """
        summary = f"Analysis Type: {self.type}\n"
        summary += f"Series: {self.series_name}\n"
        summary += f"Performed: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += "-" * 50 + "\n"

        for key, data in self.results.items():
            value = data['value']
            unit = data['unit'] or ''
            summary += f"{key}: {value} {unit}\n"

        return summary