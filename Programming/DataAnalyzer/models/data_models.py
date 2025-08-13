#!/usr/bin/env python3
"""
Data models for Excel Data Plotter - COMPLETE FIXED VERSION
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import uuid
import warnings
from pathlib import Path


@dataclass
class FileData:
    """Complete FileData class with all required attributes"""
    filepath: str
    data: pd.DataFrame
    filename: Optional[str] = None

    # Use 'id' to match tests
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Metadata
    file_size: int = 0
    load_time: datetime = field(default_factory=datetime.now)
    sheet_name: Optional[str] = None

    # Data properties
    columns: List[str] = field(default_factory=list)
    dtypes: Dict[str, str] = field(default_factory=dict)
    shape: Tuple[int, int] = (0, 0)

    # Analysis metadata
    numeric_columns: List[str] = field(default_factory=list)
    datetime_columns: List[str] = field(default_factory=list)
    text_columns: List[str] = field(default_factory=list)

    # Quality metrics
    missing_values: Dict[str, int] = field(default_factory=dict)
    quality_score: float = 100.0

    # User metadata
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Series tracking
    series_list: List[str] = field(default_factory=list)  # Track associated series IDs

    def __post_init__(self):
        """Initialize computed properties"""
        # Sync id and file_id
        if not self.id:
            self.id = self.file_id
        else:
            self.file_id = self.id

        # If filename not provided, extract from filepath
        if self.filename is None:
            self.filename = Path(self.filepath).name

        if self.data is not None:
            self.analyze_data()

    @property
    def df(self) -> pd.DataFrame:
        """Return dataframe for backward compatibility"""
        return self.data

    @property
    def row_count(self) -> int:
        """Return number of rows"""
        return len(self.data) if self.data is not None else 0

    @property
    def column_count(self) -> int:
        """Return number of columns"""
        return len(self.data.columns) if self.data is not None else 0

    @property
    def metadata(self) -> Dict[str, Any]:
        """Return metadata dictionary for compatibility"""
        return {
            'rows': self.row_count,
            'columns': self.column_count,
            'shape': self.shape,
            'numeric_columns': len(self.numeric_columns),
            'datetime_columns': len(self.datetime_columns),
            'text_columns': len(self.text_columns),
            'missing_values': sum(self.missing_values.values()),
            'quality_score': self.quality_score,
            'file_size': self.file_size,
            'has_numeric': len(self.numeric_columns) > 0,  # Added this line
            'has_datetime': len(self.datetime_columns) > 0,  # Added for completeness
            'memory_usage': self.data.memory_usage(deep=True).sum() if self.data is not None else 0,
            'dtypes': self.dtypes
        }

    def analyze_data(self):
        """Analyze the loaded data"""
        if self.data is None:
            return

        # Basic properties
        self.shape = self.data.shape
        # Ensure all column names are strings
        self.columns = [str(col) for col in self.data.columns.tolist()]
        self.dtypes = {str(col): str(dtype) for col, dtype in self.data.dtypes.items()}

        # Clear existing categorizations
        self.numeric_columns = []
        self.datetime_columns = []
        self.text_columns = []

        # Categorize columns and attempt data type conversion
        for col in self.columns:
            dtype = self.data[col].dtype
            
            # Try to convert string columns that look like numbers
            if dtype == 'object':
                # Try to convert to numeric
                numeric_series = pd.to_numeric(self.data[col], errors='coerce')
                if not numeric_series.isna().all() and numeric_series.notna().sum() > 0:
                    # If most values can be converted to numeric, use that
                    self.data[col] = numeric_series
                    dtype = numeric_series.dtype
                else:
                    # Try to convert to datetime
                    try:
                        # Try to infer datetime format automatically, suppressing warnings
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            datetime_series = pd.to_datetime(self.data[col], errors='coerce', infer_datetime_format=True)
                        if not datetime_series.isna().all() and datetime_series.notna().sum() > 0:
                            self.data[col] = datetime_series
                            dtype = datetime_series.dtype
                    except:
                        pass
            
            # Categorize based on final dtype
            if pd.api.types.is_numeric_dtype(dtype):
                self.numeric_columns.append(col)
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                self.datetime_columns.append(col)
            else:
                self.text_columns.append(col)

        # Update dtypes after conversion
        self.dtypes = {col: str(dtype) for col, dtype in self.data.dtypes.items()}

        # Calculate missing values
        self.missing_values = self.data.isnull().sum().to_dict()

        # Calculate quality score
        total_cells = self.data.size
        missing_cells = self.data.isnull().sum().sum()
        self.quality_score = 100 * (1 - missing_cells / total_cells) if total_cells > 0 else 100

    def get_numeric_columns(self) -> List[str]:
        """Get list of numeric columns"""
        return self.numeric_columns.copy()

    def get_column_stats(self, column: str) -> Dict[str, Any]:
        """Get statistics for a column"""
        if column not in self.columns:
            return {}

        col_data = self.data[column]
        stats = {
            'dtype': str(col_data.dtype),
            'count': int(col_data.count()),
            'missing': int(col_data.isnull().sum()),
            'unique': int(col_data.nunique())
        }

        if column in self.numeric_columns:
            stats.update({
                'mean': float(col_data.mean()),
                'std': float(col_data.std()),
                'min': float(col_data.min()),
                'max': float(col_data.max()),
                'q25': float(col_data.quantile(0.25)),
                'q50': float(col_data.quantile(0.50)),
                'q75': float(col_data.quantile(0.75))
            })

        return stats

    def get_preview(self, rows: int = 10) -> pd.DataFrame:
        """Get preview of data"""
        return self.data.head(rows)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'filename': self.filename,
            'filepath': self.filepath,
            'file_size': self.file_size,
            'load_time': self.load_time.isoformat(),
            'sheet_name': self.sheet_name,
            'shape': self.shape,
            'columns': self.columns,
            'numeric_columns': self.numeric_columns,
            'datetime_columns': self.datetime_columns,
            'quality_score': self.quality_score,
            'notes': self.notes,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], df: pd.DataFrame = None) -> 'FileData':
        """Create FileData from dictionary"""
        file_data = cls(
            filepath=data.get('filepath', ''),
            data=df,
            filename=data.get('filename', 'unknown')
        )

        # Set ID
        if 'id' in data:
            file_data.id = data['id']
            file_data.file_id = data['id']
        elif 'file_id' in data:
            file_data.id = data['file_id']
            file_data.file_id = data['file_id']

        # Set additional properties
        for key in ['file_size', 'sheet_name', 'notes', 'tags']:
            if key in data:
                setattr(file_data, key, data[key])

        if 'load_time' in data:
            file_data.load_time = datetime.fromisoformat(data['load_time'])

        return file_data


@dataclass
class SeriesConfig:
    """Configuration for a data series"""
    name: str
    file_id: str
    x_column: str
    y_column: str

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sheet_name: Optional[str] = None
    start_index: Optional[int] = 0
    end_index: Optional[int] = None

    # Display settings - Enhanced
    color: str = "#3B82F6"
    line_style: str = "-"  # '-', '--', '-.', ':', 'none'
    line_width: float = 1.5
    marker: Optional[str] = None  # 'o', 's', '^', 'v', '<', '>', 'D', 'none'
    marker_size: float = 6.0
    marker_edge_color: str = "auto"  # "auto" uses line color
    marker_edge_width: float = 0.8
    alpha: float = 1.0
    visible: bool = True
    show_in_legend: bool = True
    legend_label: str = ""
    plot_type: str = "line"  # "line", "scatter", "bar", "step"
    missing_data_method: str = "skip"  # Options: "skip", "interpolate", "zero", "highlight"
    
    # Advanced styling options
    fill_between: bool = False
    fill_color: str = "auto"  # "auto" uses line color with reduced alpha
    fill_alpha: float = 0.2
    error_bars: bool = False
    error_color: str = "auto"
    error_alpha: float = 0.6
    smooth_line: bool = False  # Apply smoothing filter
    smooth_window: int = 5
    z_order: int = 1  # Drawing order (higher = on top)
    
    # Data handling options
    outlier_handling: str = "keep"  # "keep", "remove", "highlight", "clamp"
    outlier_threshold: float = 3.0  # Standard deviations for outlier detection
    outlier_color: str = "red"
    data_decimation: bool = False  # Reduce data points for performance
    decimation_factor: int = 1
    
    # Additional display settings
    show_trendline: bool = False
    show_trend: bool = False  # Legacy compatibility alias
    smooth_factor: float = 0.0
    
    # Data range settings (backward compatibility)
    start_row: Optional[int] = None
    end_row: Optional[int] = None
    
    # Legacy compatibility attributes
    smoothing: bool = False
    y_axis: str = "left"
    z_order: int = 1
    marker_style: Optional[str] = None
    fill_area: bool = False
    gradient_fill: bool = False
    outlier_handling: str = 'keep'
    outlier_threshold: float = 3.0
    datetime_format: str = 'auto'
    custom_datetime_format: str = '%Y-%m-%d %H:%M:%S'
    timezone: Optional[str] = None
    show_statistics: bool = False
    trend_type: str = "linear"
    trend_params: Dict[str, Any] = field(default_factory=lambda: {'degree': 1, 'window': 20})
    trend_color: Optional[str] = None
    trend_style: str = "--"
    trend_width: float = 1.0
    show_mean: bool = False
    show_std: bool = False
    show_peaks: bool = False
    peak_prominence: float = 0.1
    missing_data_color: str = 'red'
    show_moving_average: bool = False
    moving_average_window: int = 20
    show_confidence_interval: bool = False
    confidence_level: float = 0.95
    highlight_weekends: bool = False
    highlight_business_hours: bool = False
    highlight_outliers: bool = False
    outlier_method: str = 'keep'
    highlight_base_pressure: bool = False
    highlight_spikes: bool = False
    
    def __post_init__(self):
        """Initialize computed properties for backward compatibility"""
        # Set default legend label if not provided
        if not self.legend_label:
            self.legend_label = self.name
            
        # Map start_index/end_index to start_row/end_row for compatibility
        if self.start_row is None and self.start_index is not None:
            self.start_row = self.start_index
        if self.end_row is None and self.end_index is not None:
            self.end_row = self.end_index
            
        # Map start_row/end_row back to start_index/end_index
        if self.start_index is None and self.start_row is not None:
            self.start_index = self.start_row
        if self.end_index is None and self.end_row is not None:
            self.end_index = self.end_row

    # Compatibility properties
    @property
    def series_id(self) -> str:
        """Alias for id"""
        return self.id

    def get_data(self, file_data: FileData) -> Tuple[np.ndarray, np.ndarray]:
        """Extract data from FileData"""
        if file_data is None or file_data.data is None:
            return np.array([]), np.array([])

        df = file_data.data

        # Apply range limits
        start = self.start_index or 0
        end = self.end_index or len(df)
        df = df.iloc[start:end]

        # Extract columns
        if self.x_column in df.columns and self.y_column in df.columns:
            x_data = df[self.x_column]
            y_data = df[self.y_column]
            
            # Convert to numeric if needed
            if x_data.dtype == 'object':
                x_data = pd.to_numeric(x_data, errors='coerce')
            if y_data.dtype == 'object':
                y_data = pd.to_numeric(y_data, errors='coerce')
            
            # Convert to numpy arrays
            x_values = x_data.values
            y_values = y_data.values

            # Remove NaN values
            mask = ~(pd.isna(x_values) | pd.isna(y_values))
            return x_values[mask], y_values[mask]

        return np.array([]), np.array([])

    def copy(self) -> 'SeriesConfig':
        """Create a copy of this SeriesConfig"""
        return SeriesConfig.from_dict(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SeriesConfig':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class PlotConfiguration:
    """Plot configuration settings"""
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    grid: bool = True
    legend: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class AnnotationConfig:
    """Annotation configuration"""
    annotation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    annotation_type: str = "text"
    text: str = ""
    x: float = 0.0
    y: float = 0.0
    x2: float = 0.0  # For lines, arrows
    y2: float = 0.0  # For lines, arrows
    
    # Visual properties
    visible: bool = True
    color: str = "#000000"
    alpha: float = 1.0
    
    # Text properties
    font_size: float = 12.0
    font_family: str = "sans-serif"
    font_weight: str = "normal"
    font_style: str = "normal"
    horizontal_alignment: str = "center"
    vertical_alignment: str = "center"
    rotation: float = 0.0
    
    # Background and border
    background_color: Optional[str] = None
    border_color: Optional[str] = None
    border_width: float = 1.0
    
    # Shape properties
    width: float = 0.1
    height: float = 0.1
    radius: float = 0.05
    fill: bool = False
    
    # Arrow properties
    arrow_style: str = "->"
    arrow_width: float = 1.0
    arrow_mutation_scale: float = 12.0
    line_style: str = "-"
    
    # Point/marker properties
    marker: Optional[str] = None
    marker_size: float = 6.0
    
    # Legacy compatibility for dialogs that use different parameter names
    label: str = ""
    x_data: float = 0.0
    x_end: float = 0.0
    y_data: float = 0.0
    y_end: float = 0.0
    
    def __post_init__(self):
        """Handle legacy parameter mapping"""
        # If x_data was provided, map to x
        if hasattr(self, '_x_data_set') and self._x_data_set:
            self.x = self.x_data
        # If x_end was provided, map to x2
        if hasattr(self, '_x_end_set') and self._x_end_set:
            self.x2 = self.x_end
        # If y_data was provided, map to y
        if hasattr(self, '_y_data_set') and self._y_data_set:
            self.y = self.y_data
        # If y_end was provided, map to y2
        if hasattr(self, '_y_end_set') and self._y_end_set:
            self.y2 = self.y_end
        # If label was provided and text is empty, use label as text
        if self.label and not self.text:
            self.text = self.label
    
    def __init__(self, **kwargs):
        """Custom constructor to handle legacy parameter mappings and set defaults"""
        # Handle legacy 'type' parameter
        if 'type' in kwargs:
            kwargs['annotation_type'] = kwargs.pop('type')

        # Map various alternate parameter names used by older dialogs
        if 'x_position' in kwargs:
            kwargs['x'] = kwargs.pop('x_position')
        if 'y_position' in kwargs:
            kwargs['y'] = kwargs.pop('y_position')
        if 'show_arrow' in kwargs:
            kwargs['arrow_style'] = '->' if kwargs.pop('show_arrow') else ''
        if 'background' in kwargs:
            bg_enabled = kwargs.pop('background')
            if bg_enabled and 'color' in kwargs:
                kwargs['background_color'] = kwargs['color']
        if 'border' in kwargs:
            border_enabled = kwargs.pop('border')
            if border_enabled and 'color' in kwargs:
                kwargs['border_color'] = kwargs['color']
        if 'arrow_orientation' in kwargs:
            orientation = kwargs.pop('arrow_orientation')
            orientation_map = {
                'up': '^', 'down': 'v', 'left': '<', 'right': '>',
                'northeast': '^>', 'northwest': '<^', 'southeast': 'v>', 'southwest': '<v'
            }
            kwargs['arrow_style'] = orientation_map.get(orientation, '->')
        if 'line_thickness' in kwargs:
            kwargs['arrow_width'] = kwargs.pop('line_thickness')
        if 'arrow_size' in kwargs:
            kwargs['arrow_width'] = kwargs.pop('arrow_size')
        if 'background_alpha' in kwargs:
            kwargs['alpha'] = kwargs.pop('background_alpha')
        if 'border_thickness' in kwargs:
            kwargs['border_width'] = kwargs.pop('border_thickness')

        # Set defaults
        self.annotation_id = kwargs.get('annotation_id', str(uuid.uuid4()))
        self.annotation_type = kwargs.get('annotation_type', 'text')
        self.text = kwargs.get('text', '')
        self.x = kwargs.get('x', 0.0)
        self.y = kwargs.get('y', 0.0)
        self.x2 = kwargs.get('x2', 0.0)
        self.y2 = kwargs.get('y2', 0.0)

        # Visual properties
        self.visible = kwargs.get('visible', True)
        self.color = kwargs.get('color', '#000000')
        self.alpha = kwargs.get('alpha', 1.0)

        # Text properties
        self.font_size = kwargs.get('font_size', 12.0)
        self.font_family = kwargs.get('font_family', 'sans-serif')
        self.font_weight = kwargs.get('font_weight', 'normal')
        self.font_style = kwargs.get('font_style', 'normal')
        self.horizontal_alignment = kwargs.get('horizontal_alignment', 'center')
        self.vertical_alignment = kwargs.get('vertical_alignment', 'center')
        self.rotation = kwargs.get('rotation', 0.0)

        # Background and border
        self.background_color = kwargs.get('background_color')
        self.border_color = kwargs.get('border_color')
        self.border_width = kwargs.get('border_width', 1.0)

        # Shape properties
        self.width = kwargs.get('width', 0.1)
        self.height = kwargs.get('height', 0.1)
        self.radius = kwargs.get('radius', 0.05)
        self.fill = kwargs.get('fill', False)

        # Arrow/line properties
        self.arrow_style = kwargs.get('arrow_style', '->')
        self.arrow_width = kwargs.get('arrow_width', 1.0)
        # Map head_size or mutation_scale to arrow_mutation_scale
        if 'head_size' in kwargs:
            self.arrow_mutation_scale = kwargs.get('head_size', 12.0)
        else:
            self.arrow_mutation_scale = kwargs.get('arrow_mutation_scale', 12.0)
        self.line_style = kwargs.get('line_style', '-')

        # Point/marker properties
        self.marker = kwargs.get('marker')
        self.marker_size = kwargs.get('marker_size', 6.0)

        # Legacy compatibility
        self.label = kwargs.get('label', '')
        self.x_data = kwargs.get('x_data', 0.0)
        self.x_end = kwargs.get('x_end', 0.0)
        self.y_data = kwargs.get('y_data', 0.0)
        self.y_end = kwargs.get('y_end', 0.0)

        # Handle legacy mappings
        if 'x_data' in kwargs:
            self.x = kwargs['x_data']
        if 'x_end' in kwargs:
            self.x2 = kwargs['x_end']
        if 'y_data' in kwargs:
            self.y = kwargs['y_data']
        if 'y_end' in kwargs:
            self.y2 = kwargs['y_end']
        if self.label and not self.text:
            self.text = self.label
    
    # Backward compatibility
    @property
    def id(self) -> str:
        return self.annotation_id
    
    @property
    def type(self) -> str:
        return self.annotation_type
    
    # Annotation dialog compatibility properties
    @property
    def x_position(self) -> float:
        return self.x
    
    @x_position.setter
    def x_position(self, value: float):
        self.x = value
    
    @property
    def y_position(self) -> float:
        return self.y
    
    @y_position.setter
    def y_position(self, value: float):
        self.y = value
    
    @property
    def show_arrow(self) -> bool:
        return bool(self.arrow_style and self.arrow_style != '')
    
    @show_arrow.setter
    def show_arrow(self, value: bool):
        if value:
            self.arrow_style = '->' if not self.arrow_style else self.arrow_style
        else:
            self.arrow_style = ''
    
    @property
    def background(self) -> bool:
        return bool(self.background_color)
    
    @background.setter
    def background(self, value: bool):
        if value and not self.background_color:
            self.background_color = self.color
        elif not value:
            self.background_color = None
    
    @property
    def border(self) -> bool:
        return bool(self.border_color)
    
    @border.setter
    def border(self, value: bool):
        if value and not self.border_color:
            self.border_color = self.color
        elif not value:
            self.border_color = None
    
    @property
    def arrow_orientation(self) -> str:
        """Get arrow orientation from arrow_style"""
        style_map = {
            '^': 'up',
            'v': 'down',
            '<': 'left',
            '>': 'right',
            '^>': 'northeast',
            '<^': 'northwest',
            'v>': 'southeast',
            '<v': 'southwest'
        }
        return style_map.get(self.arrow_style, 'up')
    
    @arrow_orientation.setter
    def arrow_orientation(self, value: str):
        orientation_map = {
            'up': '^',
            'down': 'v', 
            'left': '<',
            'right': '>',
            'northeast': '^>',
            'northwest': '<^',
            'southeast': 'v>',
            'southwest': '<v'
        }
        self.arrow_style = orientation_map.get(value, '->')
    
    @property
    def line_thickness(self) -> float:
        return self.arrow_width
    
    @line_thickness.setter
    def line_thickness(self, value: float):
        self.arrow_width = value
    
    @property
    def arrow_size(self) -> float:
        return self.arrow_width
    
    @arrow_size.setter
    def arrow_size(self, value: float):
        self.arrow_width = value
    
    @property
    def background_alpha(self) -> float:
        return self.alpha
    
    @background_alpha.setter
    def background_alpha(self, value: float):
        self.alpha = value
    
    @property
    def border_thickness(self) -> float:
        return self.border_width
    
    @border_thickness.setter
    def border_thickness(self, value: float):
        self.border_width = value

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()
